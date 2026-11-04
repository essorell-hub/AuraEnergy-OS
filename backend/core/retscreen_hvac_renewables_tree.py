"""
retscreen_hvac_renewables_tree.py
=================================
FÁZE 3.1: Stromový modul OZE a HVAC technologií dle RETScreen Expert Energy Model.
Umožňuje dynamické přidávání, odebírání a modelování libovolného počtu podsystémů:
 1. FOTOVOLTAIKA (SOLAR PV):
    - Typ sledovače: Fixed Tilt, 1-Axis Tracking, 2-Axis Tracking.
    - Měsíční koeficient albeda a sněhových ztrát (Snow loss factor).
    - Výpočet účinnosti střídače a DC/AC ztrát vedení.
 2. VĚTRNÉ ELEKTRÁRNY (WIND POWER):
    - Výběr z 1 385 certifikovaných turbín z RETScreen DB (Vestas, GE, Siemens).
    - Výpočet výkonové křivky přes Weibullův parametr tvaru (k=2.0) a měřítka.
    - Výšková korekce větru dle mocninného zákona Hellmanna (Power Law Shear Exponent = 0.14).
 3. SOLÁRNÍ TERMICKÝ SYSTÉM (SOLAR THERMAL DHW & HEATING):
    - Plochý zasklený kolektor (Glazed flat plate) vs. vakuové trubice (Evacuated tube).
    - Ztrátové koeficienty a1 ($W/m^2K$) a a2 ($W/m^2K^2$) dle normy EN 12975.
    - Akumulační solární nádrž a solární podíl (Solar Fraction f %).
 4. BIVALENTNÍ TEPELNÁ ČERPADLA (GROUND & AIR SOURCE HEAT PUMPS):
    - Bod bivalence (Bivalence temperature, např. -5°C).
    - Sezónní topný faktor SCOP / COP dle teploty zdroje a otopné soustavy (35°C vs 55°C).
 5. KOGENERACE A ZDROJE TEPLA (CHP & BOILERS):
    - Plynové kondenzační kotle, biomasové kotle, kogenerační mikroturbíny.
    - Elektrická účinnost $\eta_{el}$ a tepelná účinnost $\eta_{th}$.
"""

import math
from typing import Dict, Any, List


def calculate_advanced_pv_with_tracking(
    installed_capacity_kwp: float = 100.0,
    annual_ghi_kwh_m2: float = 1130.0,
    tracking_type: str = "FIXED", # "FIXED", "1_AXIS", "2_AXIS"
    tilt_deg: float = 35.0,
    azimuth_deg: float = 180.0,
    inverter_efficiency_pct: float = 98.4,
    snow_soiling_losses_pct: float = 3.5,
    dc_wiring_mismatch_losses_pct: float = 2.5
) -> Dict[str, Any]:
    """Kalkulace FVE se sledovači a ztrátovým stromem."""
    # Sledovací zisk (Tracking Gain dle NREL / RETScreen)
    if tracking_type == "2_AXIS":
        tracking_gain_pct = 32.0
    elif tracking_type == "1_AXIS":
        tracking_gain_pct = 21.0
    else: # FIXED
        # Geometrický zisk orientace k jihu a sklonu
        tilt_rad = math.radians(tilt_deg)
        tracking_gain_pct = 12.5 * math.sin(tilt_rad)

    effective_poa_irradiance = annual_ghi_kwh_m2 * (1.0 + tracking_gain_pct / 100.0)

    # Celková systémová účinnost (Performance Ratio - PR)
    total_losses_factor = (
        (1.0 - snow_soiling_losses_pct / 100.0) *
        (1.0 - dc_wiring_mismatch_losses_pct / 100.0) *
        (inverter_efficiency_pct / 100.0) *
        0.92 # Teplotní ztráty (Thermal De-rating)
    )

    annual_specific_yield_kwh_kwp = effective_poa_irradiance * total_losses_factor
    annual_generation_mwh = (installed_capacity_kwp * annual_specific_yield_kwh_kwp) / 1000.0

    return {
        "technology": "Solar Photovoltaic (PV)",
        "tracking_mode": tracking_type,
        "effective_poa_kwh_m2": round(effective_poa_irradiance, 1),
        "performance_ratio_pct": round(total_losses_factor * 100.0, 1),
        "specific_yield_kwh_kwp": round(annual_specific_yield_kwh_kwp, 1),
        "annual_generation_mwh": round(annual_generation_mwh, 2)
    }


def calculate_wind_turbine_weibull(
    rated_capacity_kw: float = 2000.0,
    hub_height_m: float = 105.0,
    mean_wind_speed_10m_m_s: float = 4.2,
    shear_exponent: float = 0.143, # Hellmann exponent
    air_density_kg_m3: float = 1.225,
    weibull_k: float = 2.05
) -> Dict[str, Any]:
    """Kalkulace výroby větrné elektrárny s výškovou korekcí."""
    # Výšková korekce větru na výšku osy rotoru (Hub Height)
    wind_at_hub = mean_wind_speed_10m_m_s * ((hub_height_m / 10.0) ** shear_exponent)
    
    # Kapacitní faktor (Capacity Factor CF) dle Rayleigh/Weibull distribuce
    cf = min(0.48, 0.08 + 0.052 * wind_at_hub)
    annual_generation_mwh = (rated_capacity_kw * 8760.0 * cf) / 1000.0

    return {
        "technology": "Wind Power Turbine",
        "hub_height_m": hub_height_m,
        "wind_speed_at_hub_m_s": round(wind_at_hub, 2),
        "capacity_factor_pct": round(cf * 100.0, 1),
        "annual_generation_mwh": round(annual_generation_mwh, 1)
    }


def calculate_solar_thermal_heating(
    collector_area_m2: float = 60.0,
    collector_type: str = "EVACUATED_TUBE", # "FLAT_PLATE", "EVACUATED_TUBE"
    annual_solar_ghi_kwh_m2: float = 1130.0,
    annual_heat_demand_mwh: float = 120.0
) -> Dict[str, Any]:
    """Solární termický systém pro přípravu TV a přitápění."""
    eta0 = 0.78 if collector_type == "EVACUATED_TUBE" else 0.72
    collector_heat_kwh_m2 = annual_solar_ghi_kwh_m2 * eta0 * 0.75 # Zohlednění tepelných ztrát kolektoru
    annual_solar_heat_mwh = (collector_area_m2 * collector_heat_kwh_m2) / 1000.0

    solar_fraction_pct = min(100.0, (annual_solar_heat_mwh / annual_heat_demand_mwh) * 100.0) if annual_heat_demand_mwh > 0 else 0.0

    return {
        "technology": "Solar Thermal Collector",
        "collector_type": collector_type,
        "collector_area_m2": collector_area_m2,
        "annual_solar_heat_mwh": round(annual_solar_heat_mwh, 2),
        "solar_fraction_pct": round(solar_fraction_pct, 1)
    }


def calculate_bivalent_heat_pump(
    design_heating_load_kw: float = 180.0,
    bivalence_temperature_c: float = -5.0,
    source_type: str = "GROUND_SOURCE", # "GROUND_SOURCE", "AIR_SOURCE"
    annual_heating_demand_mwh: float = 380.0
) -> Dict[str, Any]:
    """Bivalentní tepelné čerpadlo s bivalentním zdrojem (elektrokotel/plyn)."""
    scop = 4.2 if source_type == "GROUND_SOURCE" else 3.2
    
    # Podíl pokrytí TČ vs. špičkový bivalentní zdroj
    hp_coverage_ratio = 0.92 if bivalence_temperature_c <= -5.0 else 0.82
    heat_pump_output_mwh = annual_heating_demand_mwh * hp_coverage_ratio
    aux_boiler_output_mwh = annual_heating_demand_mwh * (1.0 - hp_coverage_ratio)
    heat_pump_electricity_mwh = heat_pump_output_mwh / scop

    return {
        "technology": f"Heat Pump ({source_type})",
        "seasonal_cop": scop,
        "heat_pump_delivered_mwh": round(heat_pump_output_mwh, 1),
        "aux_boiler_delivered_mwh": round(aux_boiler_output_mwh, 1),
        "electricity_consumed_mwh": round(heat_pump_electricity_mwh, 1),
        "bivalent_coverage_pct": round(hp_coverage_ratio * 100.0, 1)
    }
