from typing import Dict, Any

def calculate_heat_pump_savings(
    current_fuel_type: str, # "natural_gas", "heating_oil", "coal", "direct_electric"
    annual_heat_demand_mwh: float,
    heat_pump_scop: float = 3.8, # Sezónní topný faktor např. vzduch-voda 3.5-4.2
    electricity_price_mwh: float = 180.0, # EUR/MWh
    existing_fuel_price_mwh: float = 85.0, # EUR/MWh pro stávající palivo
    existing_boiler_efficiency: float = 0.88
) -> Dict[str, Any]:
    """
    Modelování náhrady stávajícího vytápění tepelným čerpadlem a úspory provozních nákladů.
    """
    # Stávající spotřeba primární energie
    baseline_fuel_mwh = annual_heat_demand_mwh / existing_boiler_efficiency
    baseline_cost = baseline_fuel_mwh * existing_fuel_price_mwh
    
    # Nová spotřeba elektřiny pro TČ
    hp_electricity_demand_mwh = annual_heat_demand_mwh / heat_pump_scop
    hp_cost = hp_electricity_demand_mwh * electricity_price_mwh
    
    annual_cost_savings = baseline_cost - hp_cost
    energy_savings_mwh = baseline_fuel_mwh - hp_electricity_demand_mwh
    
    return {
        "annual_heat_demand_mwh": annual_heat_demand_mwh,
        "baseline_fuel_demand_mwh": round(baseline_fuel_mwh, 2),
        "baseline_annual_cost": round(baseline_cost, 2),
        "heat_pump_electricity_mwh": round(hp_electricity_demand_mwh, 2),
        "heat_pump_annual_cost": round(hp_cost, 2),
        "annual_cost_savings": round(annual_cost_savings, 2),
        "primary_energy_savings_mwh": round(energy_savings_mwh, 2),
        "seasonal_cop": heat_pump_scop
    }

def calculate_ghg_emissions(
    electricity_saved_mwh: float = 0.0,
    gas_saved_mwh: float = 0.0,
    coal_saved_mwh: float = 0.0,
    grid_emission_factor_t_per_mwh: float = 0.40, # Průměrný emisní faktor sítě ČR ~0.40 t CO2/MWh
    gas_emission_factor_t_per_mwh: float = 0.202,
    coal_emission_factor_t_per_mwh: float = 0.354
) -> Dict[str, Any]:
    """
    Kalkulace úspor emisí skleníkových plynů (GHG - CO2 ekvivalent).
    Ekvivalent GHG modulu RETScreen.
    """
    co2_saved_electricity = electricity_saved_mwh * grid_emission_factor_t_per_mwh
    co2_saved_gas = gas_saved_mwh * gas_emission_factor_t_per_mwh
    co2_saved_coal = coal_saved_mwh * coal_emission_factor_t_per_mwh
    
    total_co2_saved_tonnes = co2_saved_electricity + co2_saved_gas + co2_saved_coal
    
    # Ekvivalenty pro pochopení veřejností (stejně jako v RETScreen)
    cars_off_road_equivalent = total_co2_saved_tonnes / 2.3 # ~2.3 t CO2 na auto ročně
    trees_planted_equivalent = total_co2_saved_tonnes * 16.5 # ~16.5 stromů pohltí 1 t CO2 za 10 let
    
    return {
        "total_co2_saved_tonnes_per_year": round(total_co2_saved_tonnes, 2),
        "electricity_co2_tonnes": round(co2_saved_electricity, 2),
        "fuel_co2_tonnes": round(co2_saved_gas + co2_saved_coal, 2),
        "cars_off_road_equivalent": round(cars_off_road_equivalent, 1),
        "trees_planted_equivalent": int(round(trees_planted_equivalent))
    }
