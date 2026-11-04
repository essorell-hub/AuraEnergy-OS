import numpy as np
from typing import List, Dict, Any, Optional

def calculate_cash_flow(
    capex: float,
    annual_savings: float,
    annual_om_cost: float,
    project_lifetime_years: int = 25,
    discount_rate: float = 0.06,
    inflation_rate: float = 0.02,
    fuel_escalation_rate: float = 0.03,
    debt_ratio: float = 0.0,
    debt_interest_rate: float = 0.05,
    debt_term_years: int = 15,
    degradation_rate: float = 0.005,
    tax_rate: float = 0.0
) -> Dict[str, Any]:
    """
    Kalkulace finančních toků, NPV, IRR, LCOE a doby návratnosti.
    Ekvivalent finančního modulu RETScreen.
    """
    equity = capex * (1.0 - debt_ratio)
    debt = capex * debt_ratio
    
    # Roční splátka úvěru (anuita)
    if debt > 0 and debt_interest_rate > 0 and debt_term_years > 0:
        annual_debt_payment = debt * (debt_interest_rate / (1 - (1 + debt_interest_rate) ** (-debt_term_years)))
    elif debt > 0 and debt_term_years > 0:
        annual_debt_payment = debt / debt_term_years
    else:
        annual_debt_payment = 0.0

    years = list(range(project_lifetime_years + 1))
    cash_flows = [-equity] # Rok 0: pouze vlastní kapitál
    discounted_cash_flows = [-equity]
    cumulative_cash_flows = [-equity]
    
    yearly_details = []
    
    for y in range(1, project_lifetime_years + 1):
        # Úspora energie s degradací účinnosti a eskalací cen energie
        production_factor = (1.0 - degradation_rate) ** (y - 1)
        savings = annual_savings * production_factor * ((1.0 + fuel_escalation_rate) ** (y - 1))
        
        # O&M náklady s inflací
        om = annual_om_cost * ((1.0 + inflation_rate) ** (y - 1))
        
        # Dluhová služba
        debt_payment = annual_debt_payment if y <= debt_term_years else 0.0
        
        # Zdanění (zjednodušený model)
        pre_tax = savings - om - debt_payment
        tax = max(0.0, pre_tax * tax_rate)
        net_cf = pre_tax - tax
        
        disc_cf = net_cf / ((1.0 + discount_rate) ** y)
        cum_cf = cumulative_cash_flows[-1] + net_cf
        
        cash_flows.append(net_cf)
        discounted_cash_flows.append(disc_cf)
        cumulative_cash_flows.append(cum_cf)
        
        yearly_details.append({
            "year": y,
            "savings": round(savings, 2),
            "om_cost": round(om, 2),
            "debt_payment": round(debt_payment, 2),
            "net_cash_flow": round(net_cf, 2),
            "discounted_cash_flow": round(disc_cf, 2),
            "cumulative_cash_flow": round(cum_cf, 2)
        })

    # NPV
    npv = float(sum(discounted_cash_flows))
    
    # IRR (Vnitřní výnosové procento)
    try:
        irr_val = np.irr(cash_flows) if hasattr(np, 'irr') else None
    except Exception:
        irr_val = None
        
    if irr_val is None or np.isnan(irr_val):
        # Numerické řešení pro IRR
        import scipy.optimize as opt
        def npv_func(r):
            return sum(cf / ((1.0 + r) ** i) for i, cf in enumerate(cash_flows))
        try:
            root = opt.brentq(npv_func, -0.9, 5.0)
            irr_val = float(root)
        except Exception:
            irr_val = None

    # Prostá návratnost (Simple Payback)
    simple_payback = None
    cum = -capex
    annual_net_simple = annual_savings - annual_om_cost
    if annual_net_simple > 0:
        simple_payback = capex / annual_net_simple

    # Diskontovaná doba návratnosti
    discounted_payback = None
    disc_cum = -equity
    for y in range(1, project_lifetime_years + 1):
        disc_cum += discounted_cash_flows[y]
        if disc_cum >= 0:
            discounted_payback = y - (disc_cum - discounted_cash_flows[y]) / discounted_cash_flows[y] if discounted_cash_flows[y] != 0 else y
            break

    return {
        "npv": round(npv, 2),
        "irr": round(irr_val * 100, 2) if irr_val is not None else None,
        "simple_payback_years": round(simple_payback, 2) if simple_payback else None,
        "discounted_payback_years": round(discounted_payback, 2) if discounted_payback else None,
        "cash_flows": [round(c, 2) for c in cash_flows],
        "discounted_cash_flows": [round(c, 2) for c in discounted_cash_flows],
        "cumulative_cash_flows": [round(c, 2) for c in cumulative_cash_flows],
        "yearly_details": yearly_details
    }

def calculate_lcoe(
    capex: float,
    annual_om_cost: float,
    annual_generation_mwh: float,
    project_lifetime_years: int = 25,
    discount_rate: float = 0.06,
    degradation_rate: float = 0.005,
    inflation_rate: float = 0.02
) -> float:
    """
    Levelized Cost of Electricity (LCOE) v měně / MWh.
    """
    total_disc_costs = capex
    total_disc_energy = 0.0
    
    for y in range(1, project_lifetime_years + 1):
        om = annual_om_cost * ((1.0 + inflation_rate) ** (y - 1))
        disc_cost = om / ((1.0 + discount_rate) ** y)
        total_disc_costs += disc_cost
        
        gen = annual_generation_mwh * ((1.0 - degradation_rate) ** (y - 1))
        disc_gen = gen / ((1.0 + discount_rate) ** y)
        total_disc_energy += disc_gen
        
    if total_disc_energy <= 0:
        return 0.0
    return round(total_disc_costs / total_disc_energy, 2)

def run_monte_carlo(
    capex: float,
    annual_savings: float,
    annual_om_cost: float,
    capex_std_pct: float = 0.10,
    savings_std_pct: float = 0.15,
    iterations: int = 2000,
    project_lifetime_years: int = 25,
    discount_rate: float = 0.06
) -> Dict[str, Any]:
    """
    Monte Carlo riziková analýza pro NPV a IRR s náhodnými odchylkami vstupů.
    """
    npv_results = []
    
    np.random.seed(42)
    rand_capex = np.random.normal(capex, capex * capex_std_pct, iterations)
    rand_savings = np.random.normal(annual_savings, annual_savings * savings_std_pct, iterations)
    
    for i in range(iterations):
        c = max(100.0, float(rand_capex[i]))
        s = max(0.0, float(rand_savings[i]))
        res = calculate_cash_flow(
            capex=c,
            annual_savings=s,
            annual_om_cost=annual_om_cost,
            project_lifetime_years=project_lifetime_years,
            discount_rate=discount_rate
        )
        npv_results.append(res["npv"])
        
    npv_arr = np.array(npv_results)
    p10 = float(np.percentile(npv_arr, 10))
    p50 = float(np.percentile(npv_arr, 50))
    p90 = float(np.percentile(npv_arr, 90))
    prob_positive_npv = float(np.sum(npv_arr > 0) / iterations * 100.0)
    
    # Histogram distribution (20 bins)
    hist, bin_edges = np.histogram(npv_arr, bins=20)
    
    return {
        "p10_npv": round(p10, 2),
        "p50_npv": round(p50, 2),
        "p90_npv": round(p90, 2),
        "mean_npv": round(float(np.mean(npv_arr)), 2),
        "prob_positive_npv_pct": round(prob_positive_npv, 1),
        "histogram": {
            "counts": [int(x) for x in hist],
            "bins": [round(float(b), 1) for b in bin_edges]
        }
    }
