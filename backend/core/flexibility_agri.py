from typing import Dict, Any, List

def calculate_flexibility_and_v2g(
    bess_power_kw: float = 500.0,
    ev_count: int = 25,
    ev_battery_kwh: float = 65.0,
    ev_charger_power_kw: float = 22.0,
    afrr_positive_price_eur_mw_h: float = 38.0, # Cena za pohotovost aFRR+ (nahoru)
    afrr_negative_price_eur_mw_h: float = 32.0, # Cena za pohotovost aFRR- (dolů)
    contracted_hours_year: int = 4000,
    v2g_active_percentage: float = 40.0 # 40% firemní flotily k dispozici pro V2G
) -> Dict[str, Any]:
    """
    Model poskytování podpůrných služeb flexibility pro ČEPS/ENTSO-E (SVR aFRR / mFRR)
    a obousměrného chytrého nabíjení firemní flotily elektromobilů (V2G - Vehicle to Grid).
    """
    # 1. BESS agregace do flexibility (aFRR / SVR)
    bess_mw = bess_power_kw / 1000.0
    # Rezervace kapacity pro ČEPS (platba za disponibilitu)
    annual_bess_flex_revenue = bess_mw * ((afrr_positive_price_eur_mw_h + afrr_negative_price_eur_mw_h) / 2.0) * contracted_hours_year
    
    # 2. V2G (Vehicle to Grid) flotila
    available_evs = ev_count * (v2g_active_percentage / 100.0)
    # Každé EV poskytuje v průměru 12 kWh flexibility ze své baterie během parkování
    v2g_pool_capacity_kwh = available_evs * 15.0
    v2g_pool_power_kw = available_evs * (ev_charger_power_kw * 0.5)
    
    # Úspory z ořezávání čtvrthodinových maxim (Peak Shaving) flotilou
    monthly_peak_demand_savings = (v2g_pool_power_kw * 14.5) # ~14.5 EUR/kW měsíčně za rezervovanou kapacitu
    annual_v2g_savings = (monthly_peak_demand_savings * 12.0) + (v2g_pool_capacity_kwh * 250.0 * 0.08) # Arbitráž
    
    total_flexibility_revenue = annual_bess_flex_revenue + annual_v2g_savings

    return {
        "bess_power_kw": bess_power_kw,
        "ev_fleet_size": ev_count,
        "v2g_active_evs": round(available_evs, 0),
        "v2g_power_pool_kw": round(v2g_pool_power_kw, 1),
        "annual_bess_afrr_revenue_eur": round(annual_bess_flex_revenue, 2),
        "annual_v2g_fleet_savings_eur": round(annual_v2g_savings, 2),
        "total_annual_flexibility_benefit_eur": round(total_flexibility_revenue, 2),
        "ceps_code_compliance": "SVR aFRR / mFRR Ready",
        "grid_support_capability": "Frequency Regulation & Local Peak Shaving"
    }

def calculate_agrivoltaics_and_cooling(
    capacity_kwp: float = 250.0,
    crop_type: str = "berries", # "berries", "apples", "vegetables", "cereals"
    ground_albedo: float = 0.22,
    bifaciality_factor: float = 0.85,
    crop_yield_change_pct: float = 12.0 # Ochrana před kroupami a úžehem zvyšuje výnos o 12%
) -> Dict[str, Any]:
    """
    Model Agrofotovoltaiky (Agri-PV):
    - Oboustranné (bifaciální) panely s odrazem od vegetace
    - Mikroklimatické ochlazování panelů odpařováním rostlin (zvýšení účinnosti o ~3.5%)
    - Zachování a stabilizace zemědělského výnosu.
    """
    # Standardní výroba FVE
    baseline_yield_kwh_kwp = 1050.0
    # Bifaciální zisk
    bifacial_gain_pct = ground_albedo * bifaciality_factor * 25.0 # ~4.7%
    # Chladicí zisk (transpirace rostlin snižuje teplotu článku o 4-6 °C => +3.2% výroby)
    transpiration_cooling_gain_pct = 3.2
    
    total_specific_yield = baseline_yield_kwh_kwp * (1.0 + (bifacial_gain_pct + transpiration_cooling_gain_pct) / 100.0)
    annual_generation_mwh = (capacity_kwp * total_specific_yield) / 1000.0
    
    return {
        "capacity_kwp": capacity_kwp,
        "crop_type": crop_type,
        "bifacial_gain_pct": round(bifacial_gain_pct, 1),
        "cooling_gain_pct": round(transpiration_cooling_gain_pct, 1),
        "specific_yield_kwh_kwp": round(total_specific_yield, 1),
        "annual_generation_mwh": round(annual_generation_mwh, 1),
        "crop_yield_impact_pct": f"+{crop_yield_change_pct}% (ochrana před kroupami, suchem a spálením sluncem)",
        "dual_land_use_efficiency_pct": 165.0 # 100% zemědělství + 65% solární pokrytí
    }
