"""
AI Day-Ahead Model Predictive Control (MPC) & Virtual Power Plant (VPP) Dispatch Engine
(vpp_mpc_engine.py - FÁZE 11)

Capabilities:
 1. 24h Day-Ahead MPC Battery Dispatch:
    - Formulates Linear Programming / Constrained Optimization using scipy.optimize.linprog
    - Decision variables: P_charge(t), P_discharge(t), SoC(t)
    - Objective: Maximize arbitrage profit + minimize peak demand charges subject to:
        * 0 <= P_charge <= P_bat_max
        * 0 <= P_discharge <= P_bat_max
        * SoC_min <= SoC(t) <= SoC_max
        * SoC(t+1) = SoC(t) + eta_ch * P_charge - (1/eta_dis) * P_discharge
 2. Virtual Power Plant (VPP) ČEPS Ancillary Services (SVR):
    - aFRR+ / aFRR- (Automatická regulace frekvence - sekundární regulace)
    - Merit Order activation based on activation price and capacity reservation
"""

import numpy as np
from scipy.optimize import linprog
from typing import Dict, Any, List


def optimize_24h_day_ahead_mpc(
    battery_capacity_kwh: float = 100.0,
    battery_power_kw: float = 50.0,
    roundtrip_efficiency_pct: float = 90.0,
    initial_soc_pct: float = 30.0,
    min_soc_pct: float = 15.0,
    max_soc_pct: float = 95.0,
    pv_forecast_kw: List[float] = None,
    load_forecast_kw: List[float] = None,
    spot_prices_eur_mwh: List[float] = None
) -> Dict[str, Any]:
    """
    Day-Ahead 24h MPC optimization using Scipy Linprog.
    Variables for 24 hours (N=24):
    x = [P_ch(0..23), P_dis(0..23)] -> 48 variables.
    """
    N = 24
    eta = np.sqrt(roundtrip_efficiency_pct / 100.0)
    e_max = battery_capacity_kwh
    p_max = battery_power_kw

    # Fallback profiles if not provided
    if spot_prices_eur_mwh is None or len(spot_prices_eur_mwh) != N:
        spot_prices_eur_mwh = [
            55.0, 48.0, 45.0, 42.0, 46.0, 68.0,
            110.0, 135.0, 125.0, 95.0, 60.0, 35.0,
            25.0, 22.0, 32.0, 65.0, 90.0, 140.0,
            170.0, 160.0, 130.0, 100.0, 78.0, 62.0
        ]

    # Convert prices to EUR/kWh
    prices_kwh = np.array(spot_prices_eur_mwh) / 1000.0

    # Objective: Minimize Cost = sum(P_ch * price - P_dis * price)
    # Linprog minimizes c^T * x
    # c = [price_0, ..., price_23, -price_0, ..., -price_23]
    c = np.concatenate([prices_kwh, -prices_kwh])

    # Constraints on SoC at each hour t (1..N):
    # SoC(t) = SoC_0 + sum_{i=0}^{t-1} (P_ch[i] * eta - P_dis[i] / eta)
    # SoC_min <= SoC(t) <= SoC_max
    # Matrix A_ub * x <= b_ub
    A_ub = []
    b_ub = []

    soc_0_kwh = e_max * (initial_soc_pct / 100.0)
    soc_min_kwh = e_max * (min_soc_pct / 100.0)
    soc_max_kwh = e_max * (max_soc_pct / 100.0)

    for t in range(1, N + 1):
        # Upper bound: sum(eta * P_ch - (1/eta) * P_dis) <= soc_max - soc_0
        row_max = np.zeros(2 * N)
        row_max[:t] = eta
        row_max[N:N + t] = -1.0 / eta
        A_ub.append(row_max)
        b_ub.append(soc_max_kwh - soc_0_kwh)

        # Lower bound: -sum(eta * P_ch - (1/eta) * P_dis) <= soc_0 - soc_min
        row_min = np.zeros(2 * N)
        row_min[:t] = -eta
        row_min[N:N + t] = 1.0 / eta
        A_ub.append(row_min)
        b_ub.append(soc_0_kwh - soc_min_kwh)

    A_ub = np.array(A_ub)
    b_ub = np.array(b_ub)

    # Variable bounds: 0 <= P_ch <= p_max, 0 <= P_dis <= p_max
    bounds = [(0, p_max)] * (2 * N)

    res = linprog(c, A_ub=A_ub, b_ub=b_ub, bounds=bounds, method='highs')

    if not res.success:
        # Fallback heuristic
        p_ch_opt = np.zeros(N)
        p_dis_opt = np.zeros(N)
    else:
        p_ch_opt = res.x[:N]
        p_dis_opt = res.x[N:]

    # Calculate resulting SoC trajectory & net profit
    soc_trajectory = [initial_soc_pct]
    current_e = soc_0_kwh
    hourly_net_power = []
    hourly_arbitrage_profit_eur = []

    for t in range(N):
        ch = float(p_ch_opt[t])
        dis = float(p_dis_opt[t])
        current_e += (ch * eta) - (dis / eta)
        current_e = max(soc_min_kwh, min(soc_max_kwh, current_e))
        soc_trajectory.append(round((current_e / e_max) * 100.0, 1))

        net_p = dis - ch
        hourly_net_power.append(round(net_p, 1))
        profit = (dis * prices_kwh[t]) - (ch * prices_kwh[t])
        hourly_arbitrage_profit_eur.append(round(profit, 2))

    total_profit_day_eur = float(np.sum(hourly_arbitrage_profit_eur))

    return {
        "status": "OPTIMAL" if res.success else "FALLBACK",
        "battery_capacity_kwh": battery_capacity_kwh,
        "battery_power_kw": battery_power_kw,
        "total_day_arbitrage_profit_eur": round(total_profit_day_eur, 2),
        "annual_projected_profit_eur": round(total_profit_day_eur * 365.0, 2),
        "schedule": {
            "hours": [f"{h:02d}:00" for h in range(N)],
            "charge_power_kw": [round(float(p), 1) for p in p_ch_opt],
            "discharge_power_kw": [round(float(p), 1) for p in p_dis_opt],
            "net_battery_power_kw": hourly_net_power,
            "soc_trajectory_pct": soc_trajectory[1:],
            "spot_prices_eur_mwh": spot_prices_eur_mwh
        }
    }


def simulate_ceps_vpp_ancillary_services(
    available_flexibility_kw: float = 100.0,
    service_type: str = "aFRR", # aFRR+ / aFRR- (Automatická regulace frekvence)
    reservation_price_czk_mw_h: float = 780.0, # Cena za rezervovanou kapacitu na trhu SVR
    activation_probability_pct: float = 12.0,
    activation_spread_czk_mwh: float = 3500.0
) -> Dict[str, Any]:
    """
    Virtuální elektrárna (VPP) dispečink a ocenění podpůrných služeb (ČEPS SVR dle Merit Order).
    """
    flex_mw = available_flexibility_kw / 1000.0
    annual_hours = 8760.0

    # 1. Výnos z rezervace kapacity (Pohotovost k regulaci)
    annual_capacity_revenue_czk = flex_mw * reservation_price_czk_mw_h * annual_hours

    # 2. Výnos z aktivované regulační energie (ČEPS aktivace dle odchylky soustavy)
    activated_hours = annual_hours * (activation_probability_pct / 100.0)
    annual_activated_energy_mwh = flex_mw * activated_hours
    annual_energy_revenue_czk = annual_activated_energy_mwh * activation_spread_czk_mwh

    total_vpp_revenue_czk = annual_capacity_revenue_czk + annual_energy_revenue_czk

    return {
        "vpp_service": f"ČEPS {service_type} (SVR)",
        "available_flexibility_kw": available_flexibility_kw,
        "reservation_price_czk_mw_h": reservation_price_czk_mw_h,
        "annual_capacity_reservation_revenue_czk": round(annual_capacity_revenue_czk, 0),
        "annual_activated_energy_revenue_czk": round(annual_energy_revenue_czk, 0),
        "total_annual_vpp_revenue_czk": round(total_vpp_revenue_czk, 0),
        "specific_flexibility_yield_czk_per_kw_year": round(total_vpp_revenue_czk / available_flexibility_kw, 0)
    }
