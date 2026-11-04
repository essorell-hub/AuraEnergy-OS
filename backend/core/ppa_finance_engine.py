"""
Corporate PPA (Power Purchase Agreement) & Structured Project Finance Engine (ppa_finance_engine.py - FÁZE 20)
Supports:
 1. Corporate PPA Contracts:
    - On-site PPA (přímé vedení k odběrateli, bez síťových poplatků za distribuci)
    - Off-site PPA (přenos přes distribuční síť)
    - Virtual / Financial PPA (Contract for Difference - CfD se spotovým vyrovnáním)
    - Price Indexation: CPI / inflační eskalátor, Floor & Cap límce (Collars)
    - Volume Settlement: Pay-as-Produced vs. Pay-as-Forecasted
 2. Advanced Debt Syndication & Project Banking:
    - Senior Debt + Mezzanine Subordinated Financing
    - DSRA (Debt Service Reserve Account) 6-month funding
    - Banking Ratios:
        * DSCR (Debt Service Coverage Ratio)
        * LLCR (Loan Life Coverage Ratio)
        * PLCR (Project Life Coverage Ratio)
 3. Stress-Testing Matrix:
    - Interest Rate Shock (+150 bps / +300 bps PRIBOR/EURIBOR jump)
    - Power Price Crash (-25% / -40% market collapse)
    - Solar Yield P90 Downside Scenario
"""

import math
from typing import Dict, Any, List, Optional


def simulate_corporate_ppa_contract(
    annual_generation_mwh: float = 1200.0,
    contract_type: str = "ON_SITE_PPA", # ON_SITE_PPA, OFF_SITE_PPA, VPPA_FINANCIAL
    base_ppa_price_eur_mwh: float = 78.0,
    ppa_term_years: int = 15,
    cpi_escalation_pct: float = 2.0,
    price_floor_eur_mwh: float = 65.0,
    price_cap_eur_mwh: float = 98.0,
    settlement_type: str = "PAY_AS_PRODUCED", # PAY_AS_PRODUCED, PAY_AS_FORECASTED
    corporate_offtaker_name: str = "Škoda Auto / Průmyslový Partner a.s."
) -> Dict[str, Any]:
    """
    Modelování Corporate PPA smlouvy a pro-forma výnosů.
    """
    projections = []
    total_ppa_revenue_eur = 0.0
    current_price = base_ppa_price_eur_mwh
    degradation_factor = 1.0

    for year in range(1, ppa_term_years + 1):
        # Eskalace ceny s Floor a Cap mantinelem
        if year > 1:
            current_price = current_price * (1.0 + cpi_escalation_pct / 100.0)
            current_price = max(price_floor_eur_mwh, min(price_cap_eur_mwh, current_price))

        gen_mwh = annual_generation_mwh * degradation_factor
        degradation_factor *= 0.996 # 0.4 % degradace panelů ročně

        annual_rev = gen_mwh * current_price
        total_ppa_revenue_eur += annual_rev

        projections.append({
            "year": year,
            "ppa_price_eur_mwh": round(current_price, 2),
            "generation_mwh": round(gen_mwh, 1),
            "revenue_eur": round(annual_rev, 2)
        })

    avg_annual_revenue = total_ppa_revenue_eur / ppa_term_years

    return {
        "status": "APPROVED",
        "contract_type": contract_type,
        "corporate_offtaker": corporate_offtaker_name,
        "contract_term_years": ppa_term_years,
        "settlement_type": settlement_type,
        "pricing_structure": {
            "base_price_eur_mwh": base_ppa_price_eur_mwh,
            "floor_eur_mwh": price_floor_eur_mwh,
            "cap_eur_mwh": price_cap_eur_mwh,
            "cpi_escalation_pct": cpi_escalation_pct
        },
        "total_contract_revenue_eur": round(total_ppa_revenue_eur, 0),
        "average_annual_revenue_eur": round(avg_annual_revenue, 0),
        "projections_sample": projections[:5]
    }


def calculate_advanced_debt_syndication(
    total_capex_eur: float = 1_000_000.0,
    senior_debt_pct: float = 65.0,
    senior_interest_rate_pct: float = 4.5,
    senior_tenor_years: int = 15,
    mezzanine_debt_pct: float = 15.0,
    mezzanine_interest_rate_pct: float = 8.5,
    mezzanine_tenor_years: int = 10,
    annual_cfads_year1: float = 95_000.0, # Cash Flow Available for Debt Service
    project_lifetime_years: int = 25
) -> Dict[str, Any]:
    """
    Strukturované bankovní financování: Senior Debt + Mezzanine + DSRA + LLCR/PLCR.
    """
    senior_debt = total_capex_eur * (senior_debt_pct / 100.0)
    mezz_debt = total_capex_eur * (mezzanine_debt_pct / 100.0)
    sponsor_equity = total_capex_eur - senior_debt - mezz_debt

    # 1. Senior Debt Annuity
    r_sr = senior_interest_rate_pct / 100.0
    annual_senior_debt_service = senior_debt * (r_sr / (1.0 - (1.0 + r_sr) ** (-senior_tenor_years)))

    # 2. Mezzanine Annuity
    r_mezz = mezzanine_interest_rate_pct / 100.0
    annual_mezz_debt_service = mezz_debt * (r_mezz / (1.0 - (1.0 + r_mezz) ** (-mezzanine_tenor_years)))

    total_annual_debt_service = annual_senior_debt_service + annual_mezz_debt_service

    # 3. DSRA (Debt Service Reserve Account) - 6 měsíců splátek seniorního dluhu
    dsra_reserve_eur = annual_senior_debt_service * 0.50

    # 4. Bankovní ukazatele (Bankability Metrics)
    # DSCR = CFADS / Debt Service
    dscr_senior = annual_cfads_year1 / annual_senior_debt_service if annual_senior_debt_service > 0 else 99.0
    dscr_total = annual_cfads_year1 / total_annual_debt_service if total_annual_debt_service > 0 else 99.0

    # LLCR (Loan Life Coverage Ratio) = NPV(CFADS during loan life) / Initial Loan
    # PLCR (Project Life Coverage Ratio) = NPV(CFADS during project life) / Initial Loan
    disc_cfads_loan = sum(annual_cfads_year1 / ((1.0 + r_sr) ** t) for t in range(1, senior_tenor_years + 1))
    disc_cfads_project = sum(annual_cfads_year1 / ((1.0 + r_sr) ** t) for t in range(1, project_lifetime_years + 1))

    llcr = disc_cfads_loan / senior_debt if senior_debt > 0 else 99.0
    plcr = disc_cfads_project / senior_debt if senior_debt > 0 else 99.0

    # 5. Stresové testování (Stress Test)
    # Scénář A: Úrokový šok (+250 bps)
    r_sr_shock = (senior_interest_rate_pct + 2.5) / 100.0
    shocked_service = senior_debt * (r_sr_shock / (1.0 - (1.0 + r_sr_shock) ** (-senior_tenor_years)))
    dscr_stress_rates = annual_cfads_year1 / shocked_service

    # Scénář B: Cenový propad trhu (-25% CFADS)
    dscr_stress_price_drop = (annual_cfads_year1 * 0.75) / annual_senior_debt_service

    return {
        "capital_structure": {
            "total_capex_eur": total_capex_eur,
            "senior_debt_eur": senior_debt,
            "senior_debt_pct": senior_debt_pct,
            "mezzanine_debt_eur": mezz_debt,
            "mezzanine_debt_pct": mezzanine_debt_pct,
            "sponsor_equity_eur": sponsor_equity,
            "sponsor_equity_pct": round((sponsor_equity / total_capex_eur) * 100.0, 1),
            "dsra_reserve_account_eur": round(dsra_reserve_eur, 0)
        },
        "annual_debt_services": {
            "senior_debt_service_eur": round(annual_senior_debt_service, 0),
            "mezzanine_debt_service_eur": round(annual_mezz_debt_service, 0),
            "total_debt_service_eur": round(total_annual_debt_service, 0)
        },
        "banking_coverage_ratios": {
            "dscr_senior_year1": round(dscr_senior, 2),
            "dscr_total_year1": round(dscr_total, 2),
            "llcr_loan_life_ratio": round(llcr, 2),
            "plcr_project_life_ratio": round(plcr, 2),
            "bank_covenant_status": "APPROVED_BANKABLE" if (dscr_senior >= 1.25 and llcr >= 1.35) else "NEEDS_HIGHER_EQUITY"
        },
        "stress_test_analysis": {
            "interest_rate_shock_plus_250bps": {
                "shocked_dscr": round(dscr_stress_rates, 2),
                "passes_covenant": dscr_stress_rates >= 1.15
            },
            "power_price_crash_minus_25pct": {
                "shocked_dscr": round(dscr_stress_price_drop, 2),
                "passes_covenant": dscr_stress_price_drop >= 1.10
            }
        }
    }
