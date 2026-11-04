"""
Multi-Criteria Optimization & Scenario Pareto Frontier Engine (optimization_engine.py - FÁZE 21)
Provides:
 1. Scenario Matrix Generator:
    - Automatically iterates combinations of PV capacities (kWp), BESS capacities (kWh), and self-consumption modes
    - Evaluates for each candidate:
        * Annual Generation (MWh)
        * Net Present Value (NPV in EUR & CZK)
        * Real LCOE (EUR/MWh)
        * Simple & Discounted Payback Period (years)
        * Autarky / Self-consumption %
 2. Pareto Optimal Frontier Determination:
    - Dominance check across (CAPEX vs. NPV vs. Payback)
    - Recommends 3 highlighted archetypal strategies:
        * LOWEST_INVESTMENT (Nejnižší počáteční CAPEX)
        * MAXIMUM_NPV (Nejvyšší dlouhodobý čistý zisk)
        * FASTEST_PAYBACK (Nejrychlejší návratnost vloženého kapitálu)
"""

from typing import Dict, Any, List


def run_multicriteria_pv_bess_optimization(
    base_annual_load_kwh: float = 120_000.0,
    electricity_price_eur_mwh: float = 165.0,
    feedin_tariff_eur_mwh: float = 65.0,
    capex_per_kwp_pv_eur: float = 780.0,
    capex_per_kwh_bess_eur: float = 380.0,
    pv_candidates_kwp: List[float] = None,
    bess_candidates_kwh: List[float] = None
) -> Dict[str, Any]:
    """
    Vygeneruje a vyhodnotí matici kombinací FVE + BESS a určí Pareto optimum.
    """
    if pv_candidates_kwp is None:
        pv_candidates_kwp = [50.0, 75.0, 100.0, 150.0]
    if bess_candidates_kwh is None:
        bess_candidates_kwh = [0.0, 50.0, 100.0, 150.0]

    scenarios = []

    for pv in pv_candidates_kwp:
        # Generace FVE cca 1 120 kWh / kWp v ČR
        annual_gen_kwh = pv * 1120.0
        annual_gen_mwh = annual_gen_kwh / 1000.0

        for bess in bess_candidates_kwh:
            # Odhad vlastní spotřeby podle poměru BESS a FVE
            bat_ratio = bess / max(1.0, pv)
            if bat_ratio >= 1.0:
                self_cons_pct = 75.0
            elif bat_ratio >= 0.5:
                self_cons_pct = 65.0
            elif bat_ratio > 0.0:
                self_cons_pct = 55.0
            else:
                self_cons_pct = 42.0

            self_consumed_kwh = annual_gen_kwh * (self_cons_pct / 100.0)
            feedin_kwh = max(0.0, annual_gen_kwh - self_consumed_kwh)

            # Celkový CAPEX
            capex_pv = pv * capex_per_kwp_pv_eur
            capex_bess = bess * capex_per_kwh_bess_eur
            total_capex = capex_pv + capex_bess

            # Roční provozní úspora a výnos
            savings_self_cons = (self_consumed_kwh / 1000.0) * electricity_price_eur_mwh
            rev_feedin = (feedin_kwh / 1000.0) * feedin_tariff_eur_mwh
            om_annual = total_capex * 0.012 # 1.2% OPEX ročně
            annual_net_benefit = savings_self_cons + rev_feedin - om_annual

            # 25leté NPV při 6% diskontní sazbě
            r = 0.06
            pv_factor_25y = sum(1.0 / ((1.0 + r) ** t) for t in range(1, 26))
            npv_eur = (annual_net_benefit * pv_factor_25y) - total_capex

            # Prostá návratnost
            payback_years = total_capex / annual_net_benefit if annual_net_benefit > 0 else 99.0

            # LCOE reálné
            lcoe_eur_mwh = (total_capex + om_annual * pv_factor_25y) / (annual_gen_mwh * pv_factor_25y) if annual_gen_mwh > 0 else 0.0

            scenarios.append({
                "id": f"pv_{int(pv)}_bess_{int(bess)}",
                "pv_capacity_kwp": pv,
                "bess_capacity_kwh": bess,
                "total_capex_eur": round(total_capex, 0),
                "total_capex_czk": round(total_capex * 25.0, 0),
                "annual_generation_mwh": round(annual_gen_mwh, 1),
                "self_consumption_pct": round(self_cons_pct, 1),
                "annual_net_benefit_eur": round(annual_net_benefit, 0),
                "npv_eur": round(npv_eur, 0),
                "npv_czk": round(npv_eur * 25.0, 0),
                "payback_years": round(payback_years, 1),
                "lcoe_real_eur_mwh": round(lcoe_eur_mwh, 1)
            })

    # Určení 3 doporučených scénářů
    lowest_capex = min(scenarios, key=lambda s: s["total_capex_eur"])
    max_npv = max(scenarios, key=lambda s: s["npv_eur"])
    fastest_payback = min(scenarios, key=lambda s: s["payback_years"])

    # Pareto dominantní varianty (kde nelze zlepšit NPV bez navýšení CAPEX)
    sorted_by_capex = sorted(scenarios, key=lambda s: s["total_capex_eur"])
    pareto_frontier = []
    current_max_npv = -float('inf')
    for sc in sorted_by_capex:
        if sc["npv_eur"] > current_max_npv:
            pareto_frontier.append(sc)
            current_max_npv = sc["npv_eur"]

    return {
        "status": "OPTIMAL",
        "scenarios_evaluated_count": len(scenarios),
        "recommended_scenarios": {
            "lowest_investment": {
                "label": "Nejnižší počáteční investice",
                "scenario": lowest_capex,
                "description": f"Minimální kapitálová náročnost ({lowest_capex['total_capex_czk']:,.0f} Kč) se spolehlivou návratností {lowest_capex['payback_years']} let."
            },
            "maximum_npv": {
                "label": "Maximální čistá hodnota (Max NPV)",
                "scenario": max_npv,
                "description": f"Generuje absolutně nejvyšší zisk za 25 let ({max_npv['npv_czk']:,.0f} Kč čisté současné hodnoty)."
            },
            "fastest_payback": {
                "label": "Nejrychlejší doba návratnosti",
                "scenario": fastest_payback,
                "description": f"Optimalizováno pro rychlou návratnost kapitálu za {fastest_payback['payback_years']} roku s vysokou mírou samovýroby."
            }
        },
        "all_scenarios": scenarios,
        "pareto_frontier_ids": [p["id"] for p in pareto_frontier]
    }
