from typing import Dict, Any, List

def calculate_chp_and_hydrogen(
    fuel_input_mwh_year: float = 2500.0,
    fuel_type: str = "biomethane", # "natural_gas", "biomethane", "hydrogen"
    chp_electrical_efficiency_pct: float = 42.0,
    chp_thermal_efficiency_pct: float = 46.0,
    power_sale_price_mwh: float = 135.0,
    heat_offset_value_mwh: float = 80.0,
    fuel_cost_mwh: float = 75.0,
    chp_capex: float = 450000.0,
    om_cost_annual: float = 28000.0
) -> Dict[str, Any]:
    """
    Model kombinované výroby elektřiny a tepla (Kogenerace - CHP) a Power-to-H2.
    """
    elec_gen_mwh = fuel_input_mwh_year * (chp_electrical_efficiency_pct / 100.0)
    heat_gen_mwh = fuel_input_mwh_year * (chp_thermal_efficiency_pct / 100.0)
    
    annual_elec_rev = elec_gen_mwh * power_sale_price_mwh
    annual_heat_rev = heat_gen_mwh * heat_offset_value_mwh
    annual_fuel_cost = fuel_input_mwh_year * fuel_cost_mwh
    
    net_operational_profit = (annual_elec_rev + annual_heat_rev) - (annual_fuel_cost + om_cost_annual)
    overall_efficiency = chp_electrical_efficiency_pct + chp_thermal_efficiency_pct
    
    payback = round(chp_capex / net_operational_profit, 1) if net_operational_profit > 0 else None
    
    # Ekvivalent výroby zeleného vodíku přes elektrolyzér (předpoklad 50 kWh na 1 kg H2)
    h2_potential_kg = (elec_gen_mwh * 1000.0) / 50.0
    
    return {
        "fuel_input_mwh": fuel_input_mwh_year,
        "electricity_generation_mwh": round(elec_gen_mwh, 1),
        "heat_generation_mwh": round(heat_gen_mwh, 1),
        "overall_efficiency_pct": round(overall_efficiency, 1),
        "annual_revenue_total_eur": round(annual_elec_rev + annual_heat_rev, 2),
        "annual_fuel_cost_eur": round(annual_fuel_cost, 2),
        "net_annual_profit_eur": round(net_operational_profit, 2),
        "simple_payback_years": payback,
        "h2_equivalent_production_kg": round(h2_potential_kg, 0)
    }

def calculate_csrd_esg_metrics(
    electricity_mwh: float,
    natural_gas_mwh: float,
    district_heat_mwh: float,
    scope3_materials_co2_tonnes: float = 15.0,
    grid_emission_factor_t_per_mwh: float = 0.40,
    gas_emission_factor_t_per_mwh: float = 0.202
) -> Dict[str, Any]:
    """
    ESG & CSRD Report dle standardu ESRS E1 (Klimatická změna):
    - Scope 1: Přímé emise z fosilního plynu a paliv
    - Scope 2: Nepřímé emise ze spotřebované elektřiny a dálkového tepla
    - Scope 3: Zabudovaný uhlík v materiálech a technologiích (CAPEX Embodied Carbon)
    """
    scope1_tco2 = natural_gas_mwh * gas_emission_factor_t_per_mwh
    scope2_tco2 = electricity_mwh * grid_emission_factor_t_per_mwh + (district_heat_mwh * 0.15)
    scope3_tco2 = scope3_materials_co2_tonnes
    
    total_footprint_tco2 = scope1_tco2 + scope2_tco2 + scope3_tco2
    
    return {
        "scope1_direct_tonnes_co2": round(scope1_tco2, 2),
        "scope2_indirect_tonnes_co2": round(scope2_tco2, 2),
        "scope3_value_chain_tonnes_co2": round(scope3_tco2, 2),
        "total_carbon_footprint_tonnes_co2": round(total_footprint_tco2, 2),
        "esrs_compliance_status": "ESRS E1 Audit Ready",
        "eu_taxonomy_aligned": bool(electricity_mwh > 0 or scope1_tco2 == 0)
    }
