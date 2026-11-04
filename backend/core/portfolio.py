from typing import List, Dict, Any

def analyze_portfolio_net_zero(
    facilities: List[Dict[str, Any]],
    target_year: int = 2035,
    discount_rate: float = 0.06
) -> Dict[str, Any]:
    """
    Agregace více budov a projektů v rámci portfolia.
    Modelování Net-Zero trajektorie, celkových CAPEX investic,
    kumulativních ročních úspor a dekarbonizace celého portfolia.
    """
    total_baseline_energy_mwh = sum(f.get("baseline_energy_mwh", 0.0) for f in facilities)
    total_baseline_co2_tonnes = sum(f.get("baseline_co2_tonnes", 0.0) for f in facilities)
    total_capex = sum(f.get("capex", 0.0) for f in facilities)
    total_annual_savings_eur = sum(f.get("annual_savings_eur", 0.0) for f in facilities)
    total_annual_co2_saved = sum(f.get("co2_saved_tonnes", 0.0) for f in facilities)
    
    remaining_co2 = max(0.0, total_baseline_co2_tonnes - total_annual_co2_saved)
    decarbonization_pct = (total_annual_co2_saved / total_baseline_co2_tonnes * 100.0) if total_baseline_co2_tonnes > 0 else 100.0
    
    # Roční trajektorie dekarbonizace do roku target_year (např. 2026 -> 2035)
    current_year = 2026
    years_count = max(1, target_year - current_year + 1)
    trajectory = []
    
    yearly_co2_reduction_step = total_annual_co2_saved / (years_count - 1) if years_count > 1 else total_annual_co2_saved
    
    current_co2 = total_baseline_co2_tonnes
    for y in range(current_year, target_year + 1):
        trajectory.append({
            "year": y,
            "portfolio_co2_tonnes": round(current_co2, 1),
            "target_net_zero": 0.0
        })
        current_co2 = max(0.0, current_co2 - yearly_co2_reduction_step)
        
    # Portfolio NPV
    simple_payback = (total_capex / total_annual_savings_eur) if total_annual_savings_eur > 0 else 0.0
    
    return {
        "facility_count": len(facilities),
        "total_capex_eur": round(total_capex, 2),
        "total_annual_savings_eur": round(total_annual_savings_eur, 2),
        "simple_payback_years": round(simple_payback, 1),
        "baseline_co2_tonnes": round(total_baseline_co2_tonnes, 1),
        "remaining_co2_tonnes": round(remaining_co2, 1),
        "portfolio_decarbonization_pct": round(decarbonization_pct, 1),
        "trajectory": trajectory,
        "facilities_summary": facilities
    }
