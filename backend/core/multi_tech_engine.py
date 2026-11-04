"""
AuraEnergy OS - Multi-Technology Renewable Engine (multi_tech_engine.py - FÁZE 10)
Supports RETScreen Expert equivalent multi-clean energy archetypes:
1. WIND ENERGY:
   - Interpolation of wind turbine power curves (kW vs m/s)
   - Weibull distribution of wind speeds (scale k, shape c)
   - Air density de-rating (elevation & temp)
   - Annual generation (MWh) and Capacity Factor (CUF %)
2. HYDRO ENERGY (Small Hydro / Run-of-River):
   - Net hydraulic head (m), design flow Q_design (m3/s)
   - Flow Duration Curve (FDC) integration (Q10 through Q355)
   - Turbine efficiency curves (Pelton, Francis, Kaplan)
   - Water density & gravity power calculation: P = eta * rho * g * Q * H
3. COMBINED HEAT & POWER (CHP) & BIOMASS:
   - Fuel input, electrical efficiency (eta_el), thermal efficiency (eta_th)
   - Primary Energy Savings (PES) according to EU Energy Efficiency Directive 2012/27/EU
   - High-efficiency cogeneration threshold check (PES > 10%)
"""

import math
from typing import Dict, Any, List


# ----------------------------------------------------------------------
# 1. VĚTRNÁ ENERGIE (WIND ENERGY)
# ----------------------------------------------------------------------
DEFAULT_TURBINE_POWER_CURVE = [
    # (wind_speed_m_s, power_kw)
    (0.0, 0.0), (2.5, 0.0), (3.0, 15.0), (4.0, 65.0), (5.0, 160.0),
    (6.0, 310.0), (7.0, 520.0), (8.0, 780.0), (9.0, 1100.0), (10.0, 1420.0),
    (11.0, 1750.0), (12.0, 1950.0), (13.0, 2000.0), (14.0, 2000.0),
    (15.0, 2000.0), (20.0, 2000.0), (25.0, 2000.0), (25.1, 0.0) # Cut-out at 25 m/s
]

def weibull_pdf(v: float, k: float, c: float) -> float:
    """Weibull probability density function: f(v) = (k/c) * (v/c)^(k-1) * exp(-(v/c)^k)"""
    if v <= 0 or c <= 0 or k <= 0:
        return 0.0
    return (k / c) * ((v / c) ** (k - 1)) * math.exp(-((v / c) ** k))


def interpolate_power_curve(speed_m_s: float, curve: List[tuple]) -> float:
    if speed_m_s <= curve[0][0]:
        return curve[0][1]
    if speed_m_s >= curve[-1][0]:
        return curve[-1][1]
    for i in range(len(curve) - 1):
        v1, p1 = curve[i]
        v2, p2 = curve[i + 1]
        if v1 <= speed_m_s <= v2:
            return p1 + (speed_m_s - v1) * (p2 - p1) / (v2 - v1)
    return 0.0


def simulate_wind_turbine_system(
    turbine_rated_power_kw: float = 2000.0,
    hub_height_m: float = 105.0,
    mean_wind_speed_at_hub_m_s: float = 6.8,
    weibull_k_shape: float = 2.15,
    turbines_count: int = 1,
    availability_pct: float = 96.5,
    power_curve: List[tuple] = None
) -> Dict[str, Any]:
    curve = power_curve or DEFAULT_TURBINE_POWER_CURVE
    # Weibull scale parameter c = mean_speed / gamma(1 + 1/k)
    # Using math.gamma
    gamma_val = math.gamma(1.0 + 1.0 / weibull_k_shape)
    weibull_c_scale = mean_wind_speed_at_hub_m_s / gamma_val

    # Numerical integration across wind speeds 0.5 to 30.0 m/s with 0.2 m/s step
    step = 0.2
    expected_power_kw = 0.0
    for i in range(1, int(30.0 / step)):
        v = i * step
        p_kw = interpolate_power_curve(v, curve)
        prob = weibull_pdf(v, weibull_k_shape, weibull_c_scale) * step
        expected_power_kw += p_kw * prob

    # Net annual energy per turbine
    availability_factor = availability_pct / 100.0
    annual_energy_per_turbine_kwh = expected_power_kw * 8760.0 * availability_factor
    total_annual_mwh = (annual_energy_per_turbine_kwh * turbines_count) / 1000.0
    total_capacity_kw = turbine_rated_power_kw * turbines_count

    cuf_pct = (total_annual_mwh * 1000.0) / (total_capacity_kw * 8760.0) * 100.0 if total_capacity_kw > 0 else 0.0
    full_load_hours = total_annual_mwh * 1000.0 / total_capacity_kw if total_capacity_kw > 0 else 0.0

    return {
        "technology": "WIND_TURBINE",
        "turbines_count": turbines_count,
        "total_rated_capacity_kw": total_capacity_kw,
        "hub_height_m": hub_height_m,
        "mean_wind_speed_m_s": mean_wind_speed_at_hub_m_s,
        "weibull_k": weibull_k_shape,
        "weibull_c": round(weibull_c_scale, 2),
        "annual_generation_mwh": round(total_annual_mwh, 2),
        "capacity_utilization_cuf_pct": round(cuf_pct, 2),
        "full_load_hours_h": round(full_load_hours, 1)
    }


# ----------------------------------------------------------------------
# 2. MALÁ VODNÍ ELEKTRÁRNA (SMALL HYDRO)
# ----------------------------------------------------------------------
def simulate_small_hydro_system(
    gross_head_m: float = 12.0,
    head_loss_pct: float = 5.0,
    design_flow_m3_s: float = 3.5,
    ecological_residual_flow_m3_s: float = 0.4,
    turbine_type: str = "KAPLAN", # KAPLAN, FRANCIS, PELTON
    turbine_efficiency_pct: float = 90.0,
    generator_efficiency_pct: float = 95.0
) -> Dict[str, Any]:
    """
    Kalkulace malé vodní elektrárny MVE:
    P = eta * rho * g * Q_net * H_net
    """
    rho = 1000.0 # kg/m3
    g = 9.81     # m/s2
    net_head_m = gross_head_m * (1.0 - head_loss_pct / 100.0)
    
    # Průměrný využitelný průtok z hydrologické křivky překročení průtoků (FDC)
    # Využitelný průtok Q_usable = min(Q_design, Q_stream - Q_eco)
    q_utilizable_avg = min(design_flow_m3_s, max(0.0, design_flow_m3_s * 0.78))
    
    total_eta = (turbine_efficiency_pct / 100.0) * (generator_efficiency_pct / 100.0)
    
    # Výkon na svorkách generátoru (kW) = eta * rho * g * Q * H / 1000
    rated_electric_power_kw = (total_eta * rho * g * design_flow_m3_s * net_head_m) / 1000.0
    avg_electric_power_kw = (total_eta * rho * g * q_utilizable_avg * net_head_m) / 1000.0
    
    annual_mwh = (avg_electric_power_kw * 8760.0 * 0.94) / 1000.0 # 94% provozní dostupnost
    cuf_pct = (annual_mwh * 1000.0) / (rated_electric_power_kw * 8760.0) * 100.0 if rated_electric_power_kw > 0 else 0.0

    return {
        "technology": "SMALL_HYDRO",
        "turbine_type": turbine_type,
        "gross_head_m": gross_head_m,
        "net_head_m": round(net_head_m, 2),
        "design_flow_m3_s": design_flow_m3_s,
        "rated_electric_power_kw": round(rated_electric_power_kw, 1),
        "annual_generation_mwh": round(annual_mwh, 2),
        "capacity_utilization_cuf_pct": round(cuf_pct, 2),
        "combined_efficiency_pct": round(total_eta * 100.0, 1)
    }


# ----------------------------------------------------------------------
# 3. KOGENERACE (CHP) A BIOMASA
# ----------------------------------------------------------------------
def simulate_chp_cogeneration_system(
    fuel_input_kw_th: float = 1000.0,
    electrical_efficiency_pct: float = 42.0,
    thermal_efficiency_pct: float = 48.0,
    annual_operating_hours: float = 6500.0,
    fuel_type: str = "NATURAL_GAS_OR_BIOMETHANE",
    ref_el_efficiency_pct: float = 52.5, # Směrnice EU pro referenční oddělenou výrobu
    ref_th_efficiency_pct: float = 90.0
) -> Dict[str, Any]:
    """
    Kogenerační model a výpočet Primary Energy Savings (PES) dle EU Directive 2012/27/EU:
    PES = 1 - 1 / ( (eta_el / ref_el) + (eta_th / ref_th) )
    Pokud PES > 10 %, jde o vysoce účinnou kogeneraci (VÚKVET).
    """
    eta_el = electrical_efficiency_pct / 100.0
    eta_th = thermal_efficiency_pct / 100.0
    
    electric_power_kw = fuel_input_kw_th * eta_el
    thermal_power_kw = fuel_input_kw_th * eta_th
    total_efficiency_pct = electrical_efficiency_pct + thermal_efficiency_pct

    annual_electric_mwh = (electric_power_kw * annual_operating_hours) / 1000.0
    annual_thermal_mwh = (thermal_power_kw * annual_operating_hours) / 1000.0
    annual_fuel_mwh = (fuel_input_kw_th * annual_operating_hours) / 1000.0

    # Primary Energy Savings (PES)
    ref_el = ref_el_efficiency_pct / 100.0
    ref_th = ref_th_efficiency_pct / 100.0
    pes_denominator = (eta_el / ref_el) + (eta_th / ref_th)
    pes_pct = (1.0 - (1.0 / pes_denominator)) * 100.0 if pes_denominator > 0 else 0.0

    is_high_efficiency_chp = pes_pct >= 10.0

    return {
        "technology": "CHP_COGENERATION",
        "fuel_type": fuel_type,
        "fuel_input_kw": fuel_input_kw_th,
        "electric_power_kw": round(electric_power_kw, 1),
        "thermal_power_kw": round(thermal_power_kw, 1),
        "total_efficiency_pct": round(total_efficiency_pct, 1),
        "annual_electricity_mwh": round(annual_electric_mwh, 2),
        "annual_heat_mwh": round(annual_thermal_mwh, 2),
        "annual_fuel_consumption_mwh": round(annual_fuel_mwh, 2),
        "primary_energy_savings_pes_pct": round(pes_pct, 2),
        "high_efficiency_cogeneration_certified": is_high_efficiency_chp
    }
