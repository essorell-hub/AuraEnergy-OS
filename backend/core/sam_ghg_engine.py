"""
GHG Emission Analysis Module (RETScreen & GHG Protocol compliant).
Calculates:
- Baseline Grid Electricity Emissions (Scope 2)
- Proposed Clean Energy System Emissions (Lifecycle embodied carbon)
- Net GHG emission reduction in tCO2e/year & 25-year lifetime
- Equivalent metrics (passenger vehicles removed, trees planted, barrels of oil avoided).
"""
from typing import Dict, Any

def calculate_ghg_lifecycle_analysis(
    annual_clean_generation_mwh: float,
    grid_emission_factor_t_per_mwh: float = 0.420, # Typical Czech / Central European grid intensity
    pv_lifecycle_emission_factor_t_per_mwh: float = 0.041, # IPCC median life cycle PV emissions (41 g CO2/kWh)
    system_lifetime_years: int = 25,
    transmission_loss_factor_pct: float = 6.5
) -> Dict[str, Any]:
    """
    Computes comparative GHG emission reductions versus baseline grid mix.
    """
    # Grid baseline emissions (including transmission & distribution losses)
    effective_grid_factor = grid_emission_factor_t_per_mwh / (1.0 - transmission_loss_factor_pct / 100.0)
    annual_baseline_grid_co2_tonnes = annual_clean_generation_mwh * effective_grid_factor
    
    # Proposed clean system lifecycle emissions (Scope 3 embodied in PV manufacturing)
    annual_clean_system_co2_tonnes = annual_clean_generation_mwh * pv_lifecycle_emission_factor_t_per_mwh
    
    # Net annual and lifetime reduction
    annual_net_reduction_tco2 = max(0.0, annual_baseline_grid_co2_tonnes - annual_clean_system_co2_tonnes)
    lifetime_reduction_tco2 = annual_net_reduction_tco2 * system_lifetime_years
    
    # Environmental equivalence metrics (EPA Greenhouse Gas Equivalencies Calculator standards)
    passenger_vehicles_off_road = annual_net_reduction_tco2 / 2.2 # ~2.2 tonnes CO2 per vehicle per year
    tree_seedlings_grown_10y = annual_net_reduction_tco2 * 16.5
    barrels_of_oil_avoided = annual_net_reduction_tco2 * 2.32
    smartphones_charged_millions = (annual_net_reduction_tco2 * 1000.0) / 7.84 / 1000.0

    return {
        "annual_clean_generation_mwh": round(annual_clean_generation_mwh, 2),
        "grid_emission_intensity_t_mwh": round(effective_grid_factor, 3),
        "annual_baseline_emissions_tco2": round(annual_baseline_grid_co2_tonnes, 2),
        "annual_clean_lifecycle_emissions_tco2": round(annual_clean_system_co2_tonnes, 2),
        "annual_net_reduction_tco2": round(annual_net_reduction_tco2, 2),
        "lifetime_net_reduction_tco2": round(lifetime_reduction_tco2, 1),
        "equivalencies": {
            "passenger_vehicles_off_road_per_year": round(passenger_vehicles_off_road, 1),
            "tree_seedlings_grown_for_10_years": int(round(tree_seedlings_grown_10y)),
            "barrels_of_oil_avoided": int(round(barrels_of_oil_avoided)),
            "smartphones_charged_millions": round(smartphones_charged_millions, 2)
        }
    }
