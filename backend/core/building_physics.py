from typing import Dict, Any, List

def calculate_building_envelope_and_hvac_losses(
    floor_area_m2: float = 850.0,
    wall_area_m2: float = 1200.0,
    roof_area_m2: float = 850.0,
    window_area_m2: float = 280.0,
    u_wall_existing: float = 1.25, # W/m2K (starší nezateplená cihla/panel)
    u_roof_existing: float = 0.95,
    u_window_existing: float = 2.70, # Stará dvojskla
    u_wall_renovated: float = 0.18, # Moderní zateplení 16-20 cm EPS/vata
    u_roof_renovated: float = 0.14,
    u_window_renovated: float = 0.85, # Moderní trojskla
    air_exchange_rate_ach: float = 0.5, # Výměna vzduchu za hodinu
    internal_temperature_c: float = 20.0,
    annual_heating_degree_days: float = 3150.0, # Např. ČR 3150 HDD
    heat_cost_eur_mwh: float = 95.0,
    facade_renovation_capex: float = 75000.0,
    roof_renovation_capex: float = 42000.0,
    windows_renovation_capex: float = 38000.0
) -> Dict[str, Any]:
    """
    Simulace tepelných ztrát budov dle ČSN EN ISO 52016-1 / DIN V 18599.
    Kalkuluje měrnou tepelnou ztrátu H_T (W/K), potřebu tepla na vytápění
    před a po renovaci, úspory v MWh a finanční návratnost zateplení.
    """
    # 1. Stávající stav
    h_trans_existing = (wall_area_m2 * u_wall_existing) + (roof_area_m2 * u_roof_existing) + (window_area_m2 * u_window_existing)
    # Větrací ztráty (výška stropu cca 3m)
    volume_m3 = floor_area_m2 * 3.0
    h_vent = 0.34 * air_exchange_rate_ach * volume_m3
    
    total_h_existing = h_trans_existing + h_vent
    # Roční spotřeba v kWh = H * HDD * 24 h / 1000
    annual_heat_demand_existing_mwh = (total_h_existing * annual_heating_degree_days * 24.0) / 1000000.0
    
    # 2. Stav po komplexní renovaci obálky
    h_trans_renovated = (wall_area_m2 * u_wall_renovated) + (roof_area_m2 * u_roof_renovated) + (window_area_m2 * u_window_renovated)
    total_h_renovated = h_trans_renovated + h_vent # Bez nuceného větrání s rekuperací
    annual_heat_demand_renovated_mwh = (total_h_renovated * annual_heating_degree_days * 24.0) / 1000000.0
    
    # 3. Přínos rekuperace (pokud by se přidala rekuperace s účinností 80%)
    h_vent_recup = h_vent * (1.0 - 0.80)
    annual_heat_with_recup_mwh = ((h_trans_renovated + h_vent_recup) * annual_heating_degree_days * 24.0) / 1000000.0

    # Úspory
    heat_saved_mwh = annual_heat_demand_existing_mwh - annual_heat_demand_renovated_mwh
    annual_cost_savings = heat_saved_mwh * heat_cost_eur_mwh
    total_capex = facade_renovation_capex + roof_renovation_capex + windows_renovation_capex
    simple_payback = total_capex / annual_cost_savings if annual_cost_savings > 0 else 0.0
    
    # Snížení emisí (předpoklad vytápění plynem 0.202 t CO2/MWh)
    co2_saved_tonnes = heat_saved_mwh * 0.202

    return {
        "existing_heat_demand_mwh": round(annual_heat_demand_existing_mwh, 1),
        "renovated_heat_demand_mwh": round(annual_heat_demand_renovated_mwh, 1),
        "heat_demand_with_recuperation_mwh": round(annual_heat_with_recup_mwh, 1),
        "annual_heat_saved_mwh": round(heat_saved_mwh, 1),
        "energy_reduction_pct": round((heat_saved_mwh / annual_heat_demand_existing_mwh * 100.0), 1),
        "annual_cost_savings_eur": round(annual_cost_savings, 2),
        "total_renovation_capex_eur": round(total_capex, 2),
        "simple_payback_years": round(simple_payback, 1),
        "co2_saved_tonnes_year": round(co2_saved_tonnes, 1),
        "u_values_comparison": {
            "walls": {"before": u_wall_existing, "after": u_wall_renovated},
            "roof": {"before": u_roof_existing, "after": u_roof_renovated},
            "windows": {"before": u_window_existing, "after": u_window_renovated}
        }
    }
