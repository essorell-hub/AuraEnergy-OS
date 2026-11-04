import numpy as np
from typing import Dict, Any, List, Optional

def calculate_advanced_project_finance(
    capex: float,
    annual_revenue: float,
    annual_om_cost: float,
    subsidy_grant_pct: float = 30.0, # Dotační příspěvek v %
    debt_ratio_pct: float = 60.0, # Dluh z částky po odečtení dotace
    loan_interest_rate_pct: float = 4.5,
    loan_term_years: int = 15,
    project_lifetime_years: int = 25,
    discount_rate_pct: float = 6.0,
    inflation_rate_pct: float = 2.0,
    electricity_escalation_pct: float = 3.0,
    degradation_pct: float = 0.5,
    corporate_tax_rate_pct: float = 21.0,
    depreciation_years: int = 5 # Odpisová skupina (např. ČR skupina 2 = 5 let)
) -> Dict[str, Any]:
    """
    Komplexní bankovní model projektového financování:
    - Dotace a granty (snížení nutného kapitálu)
    - Prioritní bankovní úvěr (Senior Debt) a anuitní splácení
    - Daňový štít (úroky a odpisy jako daňově uznatelný náklad)
    - Bankovní metriky krytí dluhu: DSCR (Debt Service Coverage Ratio)
    - Equity IRR vs. Project IRR
    """
    subsidy_amount = capex * (subsidy_grant_pct / 100.0)
    net_investment = capex - subsidy_amount
    
    debt_amount = net_investment * (debt_ratio_pct / 100.0)
    equity_amount = net_investment - debt_amount
    
    r_loan = loan_interest_rate_pct / 100.0
    r_disc = discount_rate_pct / 100.0
    tax_rate = corporate_tax_rate_pct / 100.0
    
    # Roční anuita úvěru
    if debt_amount > 0 and r_loan > 0 and loan_term_years > 0:
        annual_debt_service = debt_amount * (r_loan / (1.0 - (1.0 + r_loan) ** (-loan_term_years)))
    elif debt_amount > 0:
        annual_debt_service = debt_amount / loan_term_years
    else:
        annual_debt_service = 0.0

    remaining_debt = debt_amount
    annual_depreciation = net_investment / depreciation_years if depreciation_years > 0 else 0.0

    project_cash_flows = [-capex]
    equity_cash_flows = [-equity_amount]
    dscr_list = []
    yearly_breakdown = []
    
    cum_equity_cf = -equity_amount

    for y in range(1, project_lifetime_years + 1):
        # Příjmy a degradace
        deg_factor = (1.0 - degradation_pct / 100.0) ** (y - 1)
        esc_factor = (1.0 + electricity_escalation_pct / 100.0) ** (y - 1)
        rev = annual_revenue * deg_factor * esc_factor
        
        # OPEX s inflací
        om = annual_om_cost * ((1.0 + inflation_rate_pct / 100.0) ** (y - 1))
        ebitda = rev - om
        
        # Dluhová služba a úroky
        if y <= loan_term_years and remaining_debt > 0:
            interest_payment = remaining_debt * r_loan
            principal_payment = annual_debt_service - interest_payment
            debt_service = annual_debt_service
            remaining_debt = max(0.0, remaining_debt - principal_payment)
            dscr = ebitda / debt_service if debt_service > 0 else 99.0
            dscr_list.append(round(dscr, 2))
        else:
            interest_payment = 0.0
            principal_payment = 0.0
            debt_service = 0.0
            
        # Odpisy pro daňový základ
        depr = annual_depreciation if y <= depreciation_years else 0.0
        taxable_income = ebitda - interest_payment - depr
        tax = max(0.0, taxable_income * tax_rate)
        
        # Peněžní toky
        proj_cf = ebitda - (max(0.0, (ebitda - depr) * tax_rate))
        eq_cf = ebitda - debt_service - tax
        
        project_cash_flows.append(proj_cf)
        equity_cash_flows.append(eq_cf)
        cum_equity_cf += eq_cf
        
        yearly_breakdown.append({
            "year": y,
            "revenue": round(rev, 2),
            "ebitda": round(ebitda, 2),
            "debt_service": round(debt_service, 2),
            "tax": round(tax, 2),
            "equity_cash_flow": round(eq_cf, 2),
            "cumulative_equity_cf": round(cum_equity_cf, 2)
        })

    # Výpočet IRR pro Equity i Projekt
    import scipy.optimize as opt
    def calc_irr(cfs):
        try:
            return float(opt.brentq(lambda r: sum(c / ((1.0 + r) ** i) for i, c in enumerate(cfs)), -0.9, 10.0)) * 100.0
        except Exception:
            return None

    equity_irr = calc_irr(equity_cash_flows)
    project_irr = calc_irr(project_cash_flows)
    
    # NPV vlastního kapitálu
    equity_npv = sum(c / ((1.0 + r_disc) ** i) for i, c in enumerate(equity_cash_flows))
    min_dscr = min(dscr_list) if dscr_list else None
    avg_dscr = float(np.mean(dscr_list)) if dscr_list else None
    
    # Návratnost vlastního kapitálu
    equity_payback = None
    cum = -equity_amount
    for y in range(1, project_lifetime_years + 1):
        cum += equity_cash_flows[y]
        if cum >= 0:
            equity_payback = y
            break

    return {
        "capex_total": capex,
        "subsidy_amount": round(subsidy_amount, 2),
        "debt_amount": round(debt_amount, 2),
        "equity_amount": round(equity_amount, 2),
        "annual_debt_service": round(annual_debt_service, 2),
        "equity_npv": round(equity_npv, 2),
        "equity_irr_pct": round(equity_irr, 2) if equity_irr else None,
        "project_irr_pct": round(project_irr, 2) if project_irr else None,
        "equity_payback_years": equity_payback,
        "min_dscr": min_dscr,
        "avg_dscr": round(avg_dscr, 2) if avg_dscr else None,
        "bankability_status": "BANKABLE (DSCR >= 1.25)" if min_dscr and min_dscr >= 1.25 else "HIGH RISK (DSCR < 1.25)",
        "yearly_breakdown": yearly_breakdown
    }
