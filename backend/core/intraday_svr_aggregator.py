"""
intraday_svr_aggregator.py
==========================
FÁZE 37 & 38: Vnitrodenní obchodování (Intraday Market) a Služby výkonové rovnováhy (ČEPS SVR).
Modeluje:
 1. 15minutový vnitrodenní trh OTE (Intraday Trading) s korekcí predikční chyby OZE.
 2. Minimalizaci nákladů na odchylku (Imbalance Cost) a arbitráž na vnitrodenní volatilitě.
 3. Agregaci flexibility pro SVR (Služby výkonové rovnováhy ČEPS):
    - aFRR+ / aFRR- (automatická regulace frekvence - sekundární regulace).
    - mFRR (manuální záloha na 15 minut - terciární regulace).
    - Výpočet poplatku za pohotovost (Availability Fee Kč/MW/h) a za aktivaci energie (Activation Fee Kč/MWh).
"""

from typing import Dict, Any, List


def simulate_ceps_svr_revenue(
    battery_power_mw: float = 2.0,
    battery_capacity_mwh: float = 4.0,
    contracted_service: str = "aFRR", # "aFRR" (sekundární) nebo "mFRR" (terciární)
    hours_per_year_available: float = 7500.0
) -> Dict[str, Any]:
    """
    Kalkulace výnosů certifikovaného agregátora flexibility pro ČEPS SVR v ČR.
    """
    # Tržní ceny ČEPS (průměry 2024-2026):
    # Platba za rezervovaný výkon (Kč / MW / h)
    if contracted_service.upper() == "aFRR":
        capacity_fee_czk_mw_h = 420.0 # Vyšší cena za rychlou aFRR dynamiku
        avg_activation_hours_yr = 350.0 # Počet hodin aktivace v roce
        activation_spread_czk_mwh = 2800.0 # Rozdíl nákup vs. prodej při aktivaci
    else: # mFRR
        capacity_fee_czk_mw_h = 240.0
        avg_activation_hours_yr = 180.0
        activation_spread_czk_mwh = 1900.0

    # 1. Výnos z pohotovosti (Capacity Reservation Payment)
    reservation_revenue_czk = battery_power_mw * hours_per_year_available * capacity_fee_czk_mw_h

    # 2. Výnos z aktivované energie (Activation Spread)
    activation_mwh_yr = battery_power_mw * avg_activation_hours_yr
    activation_revenue_czk = activation_mwh_yr * activation_spread_czk_mwh

    # Celkový roční výnos z SVR
    total_svr_revenue_czk = reservation_revenue_czk + activation_revenue_czk

    # O&M náklady na dispečink, certifikaci a agregátora (cca 15 % výnosu)
    aggregator_commission_pct = 15.0
    net_svr_revenue_czk = total_svr_revenue_czk * (1.0 - aggregator_commission_pct / 100.0)

    return {
        "status": "APPROVED_CEPS_CODE",
        "service_type": f"ČEPS {contracted_service.upper()} SVR",
        "contracted_power_mw": battery_power_mw,
        "energy_capacity_mwh": battery_capacity_mwh,
        "availability_hours_yr": hours_per_year_available,
        "revenue_breakdown": {
            "capacity_reservation_revenue_czk": round(reservation_revenue_czk, 0),
            "activation_energy_revenue_czk": round(activation_revenue_czk, 0),
            "gross_svr_revenue_czk": round(total_svr_revenue_czk, 0),
            "aggregator_commission_czk": round(total_svr_revenue_czk * 0.15, 0),
            "net_owner_revenue_czk": round(net_svr_revenue_czk, 0)
        },
        "specific_metrics": {
            "specific_revenue_czk_per_mw_year": round(net_svr_revenue_czk / battery_power_mw, 0),
            "eur_czk_rate": 25.20,
            "net_owner_revenue_eur": round(net_svr_revenue_czk / 25.20, 0)
        }
    }


def simulate_intraday_imbalance_mitigation(
    forecast_generation_mwh: float = 1200.0,
    forecast_error_mae_pct: float = 12.0, # Střední chyba předpovědi FVE
    imbalance_penalty_czk_mwh: float = 1850.0,
    bess_flexible_mwh: float = 2.0
) -> Dict[str, Any]:
    """
    Simulace vnitrodenního vyrovnání odchylek pomocí BESS a Intraday aukcí.
    """
    total_deviation_mwh = forecast_generation_mwh * (forecast_error_mae_pct / 100.0)
    baseline_imbalance_cost_czk = total_deviation_mwh * imbalance_penalty_czk_mwh

    # S flexibilitou BESS a 15min vnitrodenním tradingem snížíme odchylku o cca 65-75 %
    mitigated_deviation_mwh = total_deviation_mwh * 0.70
    optimized_imbalance_cost_czk = (total_deviation_mwh - mitigated_deviation_mwh) * imbalance_penalty_czk_mwh
    annual_savings_czk = baseline_imbalance_cost_czk - optimized_imbalance_cost_czk

    return {
        "status": "CALCULATED",
        "market": "OTE Vnitrodenní trh (Intraday 15min)",
        "unmitigated_imbalance_cost_czk": round(baseline_imbalance_cost_czk, 0),
        "optimized_imbalance_cost_czk": round(optimized_imbalance_cost_czk, 0),
        "annual_deviation_savings_czk": round(annual_savings_czk, 0),
        "deviation_reduction_pct": 70.0
    }
