import math
from typing import Dict, Any, List

def calculate_wind_yield(
    turbine_rated_power_kw: float = 2000.0, # 2 MW
    hub_height_m: float = 100.0,
    annual_average_wind_speed_m_s: float = 6.5,
    weibull_k: float = 2.0, # Typický tvar Weibullovy distribuce
    cut_in_speed_m_s: float = 3.0,
    rated_speed_m_s: float = 12.0,
    cut_out_speed_m_s: float = 25.0,
    air_density_kg_m3: float = 1.225,
    losses_pct: float = 12.0 # Wake ztráty, dostupnost sítě, námraza
) -> Dict[str, Any]:
    """
    Modelování větrné turbíny s využitím Rayleighovy / Weibullovy distribuce větru
    a syntetické výkonové křivky (Power Curve).
    Ekvivalent Wind modulu RETScreen Expert.
    """
    # 8760 hodin ročně, simulace integrace po 0.5 m/s krocích větru
    wind_steps = [v * 0.5 for v in range(1, 61)] # 0.5 až 30 m/s
    total_annual_mwh = 0.0
    power_curve = []
    
    # Škálovací parametr c pro Weibulla
    # Pro k=2 (Rayleigh): mean = c * Gamma(1 + 1/2) = c * sqrt(pi)/2 => c = mean / 0.8862
    c = annual_average_wind_speed_m_s / math.gamma(1.0 + 1.0 / weibull_k)
    
    for v in wind_steps:
        # Weibull probability density: f(v) = (k/c) * (v/c)^(k-1) * exp(-(v/c)^k)
        prob_density = (weibull_k / c) * ((v / c) ** (weibull_k - 1)) * math.exp(-((v / c) ** weibull_k))
        prob_in_interval = prob_density * 0.5 # šířka kroku 0.5 m/s
        hours_per_year = prob_in_interval * 8760.0
        
        # Výkonová křivka P(v)
        if v < cut_in_speed_m_s or v > cut_out_speed_m_s:
            power_kw = 0.0
        elif v >= rated_speed_m_s:
            power_kw = turbine_rated_power_kw
        else:
            # Kubická náběhová část křivky mezi cut-in a rated
            ratio = (v - cut_in_speed_m_s) / (rated_speed_m_s - cut_in_speed_m_s)
            power_kw = turbine_rated_power_kw * (ratio ** 3)
            
        energy_mwh_bin = (power_kw * hours_per_year) / 1000.0
        total_annual_mwh += energy_mwh_bin
        
        if int(v * 10) % 20 == 0: # Uložit po 2 m/s pro graf
            power_curve.append({"wind_speed_m_s": v, "power_kw": round(power_kw, 1)})
            
    # Zohlednění ztrát
    net_annual_mwh = total_annual_mwh * (1.0 - losses_pct / 100.0)
    capacity_factor_pct = (net_annual_mwh * 1000.0) / (turbine_rated_power_kw * 8760.0) * 100.0
    
    return {
        "rated_power_kw": turbine_rated_power_kw,
        "hub_height_m": hub_height_m,
        "annual_average_wind_speed_m_s": annual_average_wind_speed_m_s,
        "gross_generation_mwh": round(total_annual_mwh, 1),
        "net_generation_mwh": round(net_annual_mwh, 1),
        "capacity_factor_pct": round(capacity_factor_pct, 1),
        "full_load_hours": round((net_annual_mwh * 1000.0) / turbine_rated_power_kw, 0),
        "power_curve_sample": power_curve
    }
