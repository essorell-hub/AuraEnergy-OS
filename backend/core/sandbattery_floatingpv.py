from typing import Dict, Any, List

def calculate_thermal_sand_battery(
    sand_mass_tonnes: float = 250.0,
    charge_temp_c: float = 550.0, # Teplota nahřátí tavené soli / křemičitého písku
    discharge_temp_c: float = 120.0, # Minimální využitelná teplota pro procesní páru
    surplus_pv_input_kw: float = 350.0, # Příkon z přebytků OZE
    heat_loss_rate_pct_day: float = 1.2 # Výborná tepelná izolace (<1.5% ztrát za 24h)
) -> Dict[str, Any]:
    """
    Model vysokoteplotní pískové / solné baterie (High-Temperature Thermal Energy Storage - TES >500 °C):
    Ukládá víkendové a polední přebytky elektřiny z FVE/Větru do tepla (500-600 °C)
    a následně dodává stabilní procesní páru (120-180 °C) pro průmysl.
    """
    # Měrná tepelná kapacita křemičitého písku cp ~ 0.83 kJ/kg.K = 0.23 kWh / tuna.K
    delta_t = charge_temp_c - discharge_temp_c
    specific_heat_kwh_per_tonne_k = 0.231
    
    # Celková tepelná kapacita baterie v MWh
    thermal_capacity_mwh = (sand_mass_tonnes * specific_heat_kwh_per_tonne_k * delta_t) / 1000.0
    
    # Čas potřebný k plnému nabití z přebytků FVE
    hours_to_full_charge = (thermal_capacity_mwh * 1000.0) / surplus_pv_input_kw if surplus_pv_input_kw > 0 else 0.0
    
    # Roční cyklování: cca 140 plných cyklů přebytků
    annual_heat_discharged_mwh = thermal_capacity_mwh * 140.0 * 0.94 # 94% účinnost cyklu
    annual_gas_cost_offset_eur = annual_heat_discharged_mwh * 85.0 # Úspora za zemní plyn
    co2_saved_tonnes = annual_heat_discharged_mwh * 0.202
    
    capex_eur = sand_mass_tonnes * 240.0 # ~240 EUR na tunu kapacity včetně výměníků
    payback_years = capex_eur / annual_gas_cost_offset_eur if annual_gas_cost_offset_eur > 0 else 0.0

    return {
        "sand_mass_tonnes": sand_mass_tonnes,
        "max_temperature_c": charge_temp_c,
        "thermal_storage_capacity_mwh": round(thermal_capacity_mwh, 2),
        "hours_to_full_charge": round(hours_to_full_charge, 1),
        "annual_heat_discharged_mwh": round(annual_heat_discharged_mwh, 1),
        "annual_gas_offset_eur": round(annual_gas_cost_offset_eur, 2),
        "estimated_capex_eur": round(capex_eur, 2),
        "simple_payback_years": round(payback_years, 1),
        "annual_co2_saved_tonnes": round(co2_saved_tonnes, 1)
    }

def calculate_floating_pv_and_cuzk(
    water_surface_area_m2: float = 15000.0,
    coverage_ratio_pct: float = 65.0,
    water_cooling_temp_drop_c: float = 8.5,
    water_evaporation_reduction_pct: float = 70.0,
    cadastral_parcel_number: str = "1425/8"
) -> Dict[str, Any]:
    """
    Model plovoucí fotovoltaiky (Floating PV - FPV) na vodních nádržích a pískovnách:
    - Vyšší účinnost díky přirozenému ochlazování vodou (+8 až 12 %)
    - Zamezení odparu vody o 70 % (klíčové pro zavlažovací nádrže a sucho)
    - Katastrální ověření parcel a nezabírání zemědělského půdního fondu (ZPF).
    """
    active_pv_area_m2 = water_surface_area_m2 * (coverage_ratio_pct / 100.0)
    # 1 kWp vyžaduje cca 5 m2 moderních panelů
    capacity_kwp = active_pv_area_m2 / 5.0
    
    # Zisk z chlazení vodou: cca -0.4% / °C u křemíkových panelů
    cooling_efficiency_gain_pct = water_cooling_temp_drop_c * 0.40 # ~3.4%
    albedo_gain_pct = 4.2 # Odraz od vodní hladiny
    total_boost_pct = cooling_efficiency_gain_pct + albedo_gain_pct
    
    base_annual_kwh_kwp = 1080.0
    effective_kwh_kwp = base_annual_kwh_kwp * (1.0 + total_boost_pct / 100.0)
    annual_generation_mwh = (capacity_kwp * effective_kwh_kwp) / 1000.0
    
    # Ušetřená odpařená voda (průměrný roční odpar cca 800 mm = 0.8 m3/m2)
    evaporated_water_saved_m3 = active_pv_area_m2 * 0.80 * (water_evaporation_reduction_pct / 100.0)

    return {
        "cadastral_parcel": cadastral_parcel_number,
        "water_surface_area_m2": water_surface_area_m2,
        "floating_pv_capacity_kwp": round(capacity_kwp, 1),
        "water_cooling_boost_pct": round(total_boost_pct, 1),
        "annual_generation_mwh": round(annual_generation_mwh, 1),
        "evaporated_water_saved_m3_year": round(evaporated_water_saved_m3, 0),
        "agricultural_land_saved_m2": round(active_pv_area_m2, 0),
        "cuzk_zpf_exemption": "NENÍ VYŽADOVÁNO VYJMUTÍ ZE ZPF (Vodní plocha)",
        "environmental_impact": "Ochrana před sinicemi a přehříváním vodní nádrže"
    }
