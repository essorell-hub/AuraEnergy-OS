"""
sector_coupling_h2_p2h.py
=========================
FÁZE 34 & 35: Sektorové provázání (Sector Coupling) - Zelený vodík a Power-to-Heat (P2H).
Poskytuje výpočet pro:
 1. Elektrolýzu vody (PEM / Alkalický elektrolyzér):
    - Specifická spotřeba (kWh/kg H2, obvykle 50–55 kWh/kg).
    - Tlakové skladování a LCOH (Levelized Cost of Hydrogen v EUR/kg a Kč/kg).
    - Teplotní bilance a rekuperace odpadního tepla z elektrolyzéru (až 75 °C).
 2. Průmyslová vysokoteplotní tepelná čerpadla a elektrokotle (Power-to-Heat):
    - Přeměna přebytků OZE na horkou vodu a páru (nahrazení zemního plynu).
    - Roční úspora emisí z plynu a finanční návratnost.
"""

from typing import Dict, Any


def simulate_green_hydrogen_production(
    surplus_power_kwh_annual: float = 250_000.0,
    electrolyzer_capacity_kw: float = 100.0,
    electrolyzer_tech: str = "PEM", # "PEM" nebo "ALKALINE"
    capex_eur_per_kw: float = 1200.0,
    operating_hours_annual: float = 2500.0,
    electricity_cost_eur_mwh: float = 45.0
) -> Dict[str, Any]:
    """
    Kalkulace výroby zeleného vodíku (H2) a nákladů LCOH.
    """
    # Specifická spotřeba elektřiny na 1 kg H2 (LHV vodíku je cca 33.33 kWh/kg)
    efficiency_kwh_per_kg = 54.0 if electrolyzer_tech.upper() == "PEM" else 50.0

    # Roční výroba vodíku z dostupných přebytků
    total_h2_kg_annual = surplus_power_kwh_annual / efficiency_kwh_per_kg
    daily_h2_production_kg = total_h2_kg_annual / 365.0

    # Rekuperace odpadního tepla (cca 25-30 % příkonu se přemění na teplo)
    waste_heat_thermal_mwh_yr = (surplus_power_kwh_annual * 0.28) / 1000.0

    # Finanční model LCOH (Levelized Cost of Hydrogen)
    system_capex_eur = electrolyzer_capacity_kw * capex_eur_per_kw
    annual_amortization_eur = system_capex_eur / 15.0 # 15 let životnost stacku
    annual_electricity_cost_eur = (surplus_power_kwh_annual / 1000.0) * electricity_cost_eur_mwh
    annual_om_cost_eur = system_capex_eur * 0.03 # 3 % na servis a vodu

    total_annual_cost_eur = annual_amortization_eur + annual_electricity_cost_eur + annual_om_cost_eur
    lcoh_eur_per_kg = total_annual_cost_eur / max(1.0, total_h2_kg_annual)
    eur_to_czk = 25.20
    lcoh_czk_per_kg = lcoh_eur_per_kg * eur_to_czk

    # Tržní benchmark (šedý vodík z parního reformingu zemního plynu je cca 60-90 Kč/kg, nafta ekvivalent cca 120-150 Kč/kg)
    diesel_parity_czk_kg = 145.0
    commercial_viable = lcoh_czk_per_kg <= diesel_parity_czk_kg

    return {
        "status": "CALCULATED",
        "technology": f"{electrolyzer_tech.upper()} Elektrolyzér",
        "electrolyzer_capacity_kw": electrolyzer_capacity_kw,
        "efficiency_kwh_per_kg_h2": efficiency_kwh_per_kg,
        "annual_production_kg_h2": round(total_h2_kg_annual, 1),
        "daily_average_kg_h2": round(daily_h2_production_kg, 2),
        "waste_heat_recovery_mwh_yr": round(waste_heat_thermal_mwh_yr, 2),
        "economics": {
            "system_capex_eur": round(system_capex_eur, 0),
            "system_capex_czk": round(system_capex_eur * eur_to_czk, 0),
            "annual_operating_cost_eur": round(annual_om_cost_eur + annual_electricity_cost_eur, 0),
            "lcoh_eur_per_kg": round(lcoh_eur_per_kg, 2),
            "lcoh_czk_per_kg": round(lcoh_czk_per_kg, 1),
            "diesel_parity_threshold_czk": diesel_parity_czk_kg,
            "economically_competitive_against_diesel": commercial_viable
        }
    }


def simulate_power_to_heat_steam(
    surplus_power_kwh_annual: float = 300_000.0,
    heat_pump_cop: float = 3.2,
    natural_gas_price_czk_kwh: float = 2.10,
    boiler_efficiency: float = 0.90
) -> Dict[str, Any]:
    """
    Simulace využití přebytků OZE pro vysokoteplotní tepelné čerpadlo nebo elektrodový kotel
    nahrazující průmyslový plynový kotel.
    """
    # Vyrobené teplo
    thermal_energy_kwh_yr = surplus_power_kwh_annual * heat_pump_cop
    # Uspořený zemní plyn v kWh
    saved_gas_kwh_yr = thermal_energy_kwh_yr / boiler_efficiency
    # Finanční úspora na plynu
    annual_gas_savings_czk = saved_gas_kwh_yr * natural_gas_price_czk_kwh

    # Emisní úspora (zemní plyn má cca 0.202 kg CO2 / kWh)
    co2_saved_tons_yr = (saved_gas_kwh_yr * 0.202) / 1000.0

    return {
        "status": "CALCULATED",
        "power_input_kwh_yr": round(surplus_power_kwh_annual, 1),
        "heat_pump_cop": heat_pump_cop,
        "thermal_output_kwh_yr": round(thermal_energy_kwh_yr, 1),
        "saved_natural_gas_kwh_yr": round(saved_gas_kwh_yr, 1),
        "annual_gas_cost_savings_czk": round(annual_gas_savings_czk, 0),
        "annual_co2_avoided_tons": round(co2_saved_tons_yr, 2)
    }
