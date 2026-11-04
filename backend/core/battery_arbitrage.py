from typing import Dict, Any, List

def calculate_bess_arbitrage_and_degradation(
    battery_capacity_kwh: float,
    battery_power_kw: float,
    efficiency_roundtrip_pct: float = 88.0,
    daily_cycles: float = 1.0,
    avg_price_spread_eur_mwh: float = 95.0, # Rozpětí mezi ranní špičkou a levnou noční/polední elektřinou
    peak_shaving_monthly_savings_eur: float = 350.0, # Úspora na rezervované kapacitě
    battery_capex_per_kwh: float = 400.0,
    project_years: int = 15
) -> Dict[str, Any]:
    """
    Spotová arbitráž bateriových úložišť (BESS), ořezávání špiček (Peak Shaving)
    a model cyklického i kalendářního stárnutí článků (State of Health - SoH).
    """
    battery_capex = battery_capacity_kwh * battery_capex_per_kwh
    
    # Roční výnos z arbitráže: kapacita * cykly * 365 dní * účinnost * spread
    daily_throughput_kwh = battery_capacity_kwh * daily_cycles
    annual_throughput_mwh = (daily_throughput_kwh * 365.0) / 1000.0
    annual_arbitrage_rev = annual_throughput_mwh * avg_price_spread_eur_mwh * (efficiency_roundtrip_pct / 100.0)
    annual_peak_shaving_rev = peak_shaving_monthly_savings_eur * 12.0
    
    total_annual_revenue = annual_arbitrage_rev + annual_peak_shaving_rev
    
    # Model degradace SoH (State of Health): ~2.2% ročně kalendářní + zátěžové stárnutí
    soh_curve = []
    current_soh = 100.0
    yearly_revenue_adjusted = []
    
    for y in range(1, project_years + 1):
        soh_curve.append({"year": y, "soh_pct": round(current_soh, 1)})
        yearly_revenue_adjusted.append(round(total_annual_revenue * (current_soh / 100.0), 2))
        current_soh = max(60.0, current_soh - 2.4) # Po 10-12 letech pokles pod 75%
        
    simple_payback = round(battery_capex / total_annual_revenue, 1) if total_annual_revenue > 0 else 0.0
    
    return {
        "battery_capacity_kwh": battery_capacity_kwh,
        "battery_power_kw": battery_power_kw,
        "battery_capex_eur": round(battery_capex, 2),
        "annual_arbitrage_revenue_eur": round(annual_arbitrage_rev, 2),
        "annual_peak_shaving_revenue_eur": round(annual_peak_shaving_rev, 2),
        "total_annual_revenue_year1_eur": round(total_annual_revenue, 2),
        "simple_payback_years": simple_payback,
        "soh_trajectory": soh_curve,
        "yearly_revenue_adjusted": yearly_revenue_adjusted
    }
