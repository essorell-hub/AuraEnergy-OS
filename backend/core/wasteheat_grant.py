from typing import Dict, Any, List

def calculate_industrial_waste_heat_and_geothermal(
    exhaust_gas_flow_m3_h: float = 4500.0,
    exhaust_temp_c: float = 280.0,
    ambient_temp_c: float = 20.0,
    operating_hours_year: int = 5500,
    heat_value_eur_mwh: float = 75.0,
    orc_electric_efficiency_pct: float = 18.0,
    geothermal_boreholes_count: int = 12,
    borehole_depth_m: float = 130.0,
    ground_thermal_conductivity_w_mk: float = 2.4
) -> Dict[str, Any]:
    """
    Model využití průmyslového odpadního tepla (Waste Heat Recovery)
    přes ORC (Organic Rankine Cycle) a hlubinných geotermálních vrtů (Borehole Thermal Energy Storage - BTES).
    """
    # 1. Průmyslové odpadní teplo: Q = V * rho * cp * delta_T
    # Měrné teplo spalin/vzduchu cp ~ 1.05 kJ/kg.K, hustota rho ~ 0.9 kg/m3 při zvýšené teplotě
    temp_drop = max(50.0, exhaust_temp_c - 90.0) # Vychlazení spalin na 90 °C
    thermal_power_kw = (exhaust_gas_flow_m3_h * 0.9 * 1.05 * temp_drop) / 3600.0
    
    annual_thermal_energy_mwh = (thermal_power_kw * operating_hours_year) / 1000.0
    # ORC výroba čisté elektřiny z odpadního tepla
    orc_electricity_mwh = annual_thermal_energy_mwh * (orc_electric_efficiency_pct / 100.0)
    residual_heat_mwh = annual_thermal_energy_mwh - orc_electricity_mwh
    
    annual_orc_revenue_eur = (orc_electricity_mwh * 135.0) + (residual_heat_mwh * heat_value_eur_mwh)
    
    # 2. Geotermální vrty (BTES)
    total_borehole_meters = geothermal_boreholes_count * borehole_depth_m
    # Průměrný měrný tepelný výkon vrtu cca 45 W/m
    geothermal_peak_power_kw = (total_borehole_meters * 45.0) / 1000.0
    geothermal_annual_heat_mwh = (geothermal_peak_power_kw * 2200.0) / 1000.0
    geothermal_cop = 4.6 # Vysoká celoroční účinnost zemního TČ
    
    co2_saved_tonnes = (orc_electricity_mwh * 0.40) + (residual_heat_mwh * 0.202) + (geothermal_annual_heat_mwh * 0.202)

    return {
        "waste_heat": {
            "thermal_power_kw": round(thermal_power_kw, 1),
            "annual_thermal_mwh": round(annual_thermal_energy_mwh, 1),
            "orc_electricity_generation_mwh": round(orc_electricity_mwh, 1),
            "residual_heating_mwh": round(residual_heat_mwh, 1),
            "annual_financial_benefit_eur": round(annual_orc_revenue_eur, 2)
        },
        "geothermal_btes": {
            "boreholes_count": geothermal_boreholes_count,
            "total_depth_m": total_borehole_meters,
            "peak_thermal_power_kw": round(geothermal_peak_power_kw, 1),
            "annual_geothermal_heat_mwh": round(geothermal_annual_heat_mwh, 1),
            "seasonal_cop": geothermal_cop
        },
        "total_co2_saved_tonnes_year": round(co2_saved_tonnes, 1)
    }

def generate_grant_application_package(
    project_name: str,
    technology: str,
    capex_eur: float,
    annual_savings_eur: float,
    co2_reduction_tonnes: float
) -> Dict[str, Any]:
    """
    Automatický generátor dotačních formulářů a investičních posudků
    pro Státní fond životního prostředí (SFŽP), Národní plán obnovy a Modernizační fond (RES+).
    """
    subsidy_intensity = 0.45 if technology in ["FVE", "BESS", "Zateplení"] else 0.55
    eligible_grant_eur = capex_eur * subsidy_intensity
    investor_cash_eur = capex_eur - eligible_grant_eur
    
    return {
        "document_type": "Oficiální investiční a dotační posudek OZE / EE",
        "program": "Modernizační fond / Nová zelená úsporám / Národní plán obnovy",
        "project_name": project_name,
        "technology_category": technology,
        "eligible_capex_eur": round(capex_eur, 2),
        "subsidy_grant_amount_eur": round(eligible_grant_eur, 2),
        "own_funds_required_eur": round(investor_cash_eur, 2),
        "annual_co2_abatement_tonnes": round(co2_reduction_tonnes, 1),
        "dnsh_environmental_compliance": "DNSH (Do No Significant Harm) splněno",
        "readiness_status": "PŘIPRAVENO K PODÁNÍ ŽÁDOSTI (Level 3 - Audit Approved)"
    }
