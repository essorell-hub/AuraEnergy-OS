"""
Residential Clean Energy & Subsidies (NZÚ) Simulation Engine (residential_engine.py - FÁZE 15)
Provides:
 1. Hourly Standardized Load Profiles (TDD - Typové Diagramy Dodávky) for Residential Homes:
    - Base household baseload (appliances, cooking, electronics)
    - Domestic Hot Water (TUV / Boiler) thermal storage integration
    - Heat Pump (Tepelné čerpadlo) dynamic heating/cooling load driven by Heating Degree Days (HDD)
    - Electric Vehicle (EV) Smart Wallbox charging (configurable charging windows)
 2. Economics & Government Subsidies:
    - Nová zelená úsporám (NZÚ) grant deduction (e.g. up to 160,000 - 200,000 CZK for PV + BESS + Wallbox)
    - Grid feed-in modes: Fixed Tariff, Spot Market (OTE ČR), or Zero Export (Mikrozdroj bez přetoků)
    - Energy Community & Peer-to-Peer (P2P) local energy sharing
 3. Self-Consumption (Vlastní spotřeba) & Autarky (Soběstačnost) ratios
"""

import math
from typing import Dict, Any, List, Optional


def generate_residential_8760_load_profile(
    annual_base_electricity_kwh: float = 3500.0,
    has_heat_pump: bool = True,
    annual_heat_demand_kwh: float = 8000.0,
    cop_heat_pump: float = 3.2,
    has_electric_hot_water_boiler: bool = True,
    boiler_volume_liters: float = 200.0,
    has_ev_wallbox: bool = True,
    annual_ev_mileage_km: float = 15000.0,
    ev_consumption_kwh_100km: float = 18.0
) -> Dict[str, Any]:
    """
    Generuje 8 760hodinový realistický profil spotřeby rodinného domu (TDD).
    """
    # 1. Základní denní křivka spotřebičů (ranní a večerní špička)
    base_hourly_weights = [
        0.025, 0.020, 0.018, 0.018, 0.022, 0.035, # 00-06h: noční útlum
        0.060, 0.075, 0.055, 0.040, 0.038, 0.045, # 06-12h: ranní špička a dopoledne
        0.048, 0.040, 0.035, 0.038, 0.045, 0.065, # 12-18h: odpoledne
        0.085, 0.090, 0.075, 0.060, 0.045, 0.030  # 18-24h: večerní rodinná špička
    ]
    norm_weight = sum(base_hourly_weights)

    # 2. Ohřev TUV (bojler 200 l): cca 4.2 kWh/den
    daily_tuv_kwh = (boiler_volume_liters * 4.186 * 35.0) / 3600.0 if has_electric_hot_water_boiler else 0.0
    annual_tuv_kwh = daily_tuv_kwh * 365.0

    # 3. Tepelné čerpadlo: roční spotřeba elektřiny = teplo / COP
    annual_hp_electric_kwh = (annual_heat_demand_kwh / cop_heat_pump) if has_heat_pump else 0.0

    # 4. EV Wallbox: roční spotřeba elektřiny
    annual_ev_kwh = (annual_ev_mileage_km / 100.0) * ev_consumption_kwh_100km if has_ev_wallbox else 0.0

    total_annual_load_kwh = annual_base_electricity_kwh + annual_tuv_kwh + annual_hp_electric_kwh + annual_ev_kwh

    # Syntéza hodinového profilu
    hourly_loads = []
    daily_base_kwh = annual_base_electricity_kwh / 365.0
    daily_ev_kwh = annual_ev_kwh / 365.0

    for day in range(365):
        day_of_year = day + 1
        # Sezónní faktor pro vytápění (maximum v lednu/prosinci, nula v létě)
        # Topení aktivní cca od 1. října do 30. dubna
        is_heating_season = (day_of_year < 120 or day_of_year > 275)
        seasonal_heat_factor = max(0.0, math.cos((day_of_year - 15) / 365.0 * 2.0 * math.pi)) if is_heating_season else 0.0
        daily_hp_kwh = (annual_hp_electric_kwh / 200.0) * seasonal_heat_factor

        for h in range(24):
            # Základní spotřeba
            load = daily_base_kwh * (base_hourly_weights[h] / norm_weight)
            
            # Bojler: ohřev kolem 13-15h (optimalizováno na FVE) nebo 22-01h
            if has_electric_hot_water_boiler and h in [12, 13, 14]:
                load += (daily_tuv_kwh / 3.0)
            
            # Tepelné čerpadlo: plynule rozloženo v chladných hodinách
            if has_heat_pump and daily_hp_kwh > 0:
                hp_weight = 1.2 if (h < 7 or h > 20) else 0.8
                load += (daily_hp_kwh / 24.0) * hp_weight

            # EV Wallbox: nabíjení večer/v noci (19-23h)
            if has_ev_wallbox and h in [19, 20, 21, 22]:
                load += (daily_ev_kwh / 4.0)

            hourly_loads.append(round(load, 3))

    peak_load_kw = max(hourly_loads)
    avg_load_kw = sum(hourly_loads) / len(hourly_loads)

    return {
        "annual_total_electricity_kwh": round(total_annual_load_kwh, 1),
        "breakdown_kwh": {
            "base_household_kwh": round(annual_base_electricity_kwh, 1),
            "domestic_hot_water_tuv_kwh": round(annual_tuv_kwh, 1),
            "heat_pump_electricity_kwh": round(annual_hp_electric_kwh, 1),
            "ev_wallbox_charging_kwh": round(annual_ev_kwh, 1)
        },
        "peak_hourly_load_kw": round(peak_load_kw, 2),
        "average_hourly_load_kw": round(avg_load_kw, 2),
        "hourly_load_sample_24h": hourly_loads[120*24 : 120*24 + 24] # Vzorek jednoho jarního dne
    }


def calculate_residential_nzu_subsidy(
    pv_system_kwp: float,
    battery_capacity_kwh: float = 0.0,
    has_ev_wallbox: bool = False,
    is_disadvantaged_region: bool = False, # Např. Ústecký, Moravskoslezský, Karlovarský kraj (+10%)
    has_combination_bonus: bool = True
) -> Dict[str, Any]:
    """
    Výpočet státní dotace z programu Nová zelená úsporám (NZÚ 2024/2026):
    - Základní podpora FVE: 35 000 Kč + 8 000 Kč / kWp (nebo 10 000 Kč / kWh akumulace)
    - Maximální limit podpory na FVE s baterií: 160 000 Kč (resp. 200 000 Kč)
    - Podpora Wallbox (Ecomobility): 15 000 Kč na nabíjecí bod
    - Kombinační bonus: 10 000 Kč při spojení FVE + zateplení/ohřev TUV/Wallbox
    - Zvýhodněné kraje: bonus +10 %
    """
    # 1. Dotace na FVE
    base_fve_grant = 35000.0
    kwp_grant = min(10.0, pv_system_kwp) * 8000.0
    bat_grant = min(20.0, battery_capacity_kwh) * 8000.0
    
    calc_pv_grant = base_fve_grant + kwp_grant + bat_grant
    # Strop na samotnou FVE dle metodiky NZÚ
    max_pv_cap = 160000.0 if battery_capacity_kwh > 0 else 90000.0
    final_pv_grant = min(max_pv_cap, calc_pv_grant)

    # 2. Wallbox dotace
    wallbox_grant = 15000.0 if has_ev_wallbox else 0.0

    # 3. Kombinační bonus
    combo_bonus = 10000.0 if (has_combination_bonus and has_ev_wallbox) else 0.0

    subtotal_grant = final_pv_grant + wallbox_grant + combo_bonus

    # 4. Regionální zvýhodnění (+10 %)
    regional_bonus = subtotal_grant * 0.10 if is_disadvantaged_region else 0.0
    total_nzu_grant = subtotal_grant + regional_bonus

    return {
        "program_name": "Nová zelená úsporám (NZÚ)",
        "pv_system_kwp": pv_system_kwp,
        "battery_capacity_kwh": battery_capacity_kwh,
        "items": {
            "pv_and_battery_grant_czk": round(final_pv_grant, 0),
            "ev_wallbox_grant_czk": round(wallbox_grant, 0),
            "combination_bonus_czk": round(combo_bonus, 0),
            "regional_bonus_10pct_czk": round(regional_bonus, 0)
        },
        "total_grant_czk": round(total_nzu_grant, 0),
        "grant_share_of_typical_capex_pct": round(min(50.0, (total_nzu_grant / max(100000.0, pv_system_kwp * 45000.0 + battery_capacity_kwh * 15000.0)) * 100.0), 1)
    }


def simulate_residential_pv_economics(
    system_kwp: float,
    battery_kwh: float,
    gross_capex_czk: float,
    annual_generation_kwh: float,
    residential_load_kwh: float,
    elec_retail_price_czk_kwh: float = 5.80, # Maloobchodní cena elektřiny vč. distribuce a DPH
    feedin_tariff_czk_kwh: float = 1.50,    # Výkupní cena za přetok
    feedin_mode: str = "SPOT_OR_FIXED",     # SPOT_OR_FIXED, ZERO_EXPORT, COMMUNITY_P2P
    community_sharing_tariff_czk_kwh: float = 3.80,
    has_ev_wallbox: bool = True
) -> Dict[str, Any]:
    """
    Kompletní ekonomická bilance rodinného domu s FVE, baterií a dotací NZÚ.
    """
    nzu = calculate_residential_nzu_subsidy(pv_system_kwp=system_kwp, battery_capacity_kwh=battery_kwh, has_ev_wallbox=has_ev_wallbox)
    grant_czk = nzu["total_grant_czk"]
    net_capex_czk = max(0.0, gross_capex_czk - grant_czk)

    # Odhad vlastní spotřeby (Self-consumption) s baterií
    # Bez baterie: ~30-40 %, s odpovídající baterií (1:1.2): ~65-80 %
    bat_ratio = battery_kwh / max(1.0, system_kwp)
    if bat_ratio >= 1.5:
        self_consumption_pct = 78.0
    elif bat_ratio >= 1.0:
        self_consumption_pct = 70.0
    elif bat_ratio >= 0.5:
        self_consumption_pct = 55.0
    else:
        self_consumption_pct = 38.0

    self_consumed_kwh = annual_generation_kwh * (self_consumption_pct / 100.0)
    grid_feedin_kwh = max(0.0, annual_generation_kwh - self_consumed_kwh)

    # Finanční úspory z vlastní spotřeby
    annual_savings_self_cons_czk = self_consumed_kwh * elec_retail_price_czk_kwh

    # Výnosy z přetoků
    if feedin_mode == "ZERO_EXPORT":
        annual_feedin_rev_czk = 0.0
        grid_feedin_kwh = 0.0
    elif feedin_mode == "COMMUNITY_P2P":
        annual_feedin_rev_czk = grid_feedin_kwh * community_sharing_tariff_czk_kwh
    else: # SPOT_OR_FIXED
        annual_feedin_rev_czk = grid_feedin_kwh * feedin_tariff_czk_kwh

    total_annual_benefit_czk = annual_savings_self_cons_czk + annual_feedin_rev_czk
    
    # Návratnost
    payback_gross_years = gross_capex_czk / total_annual_benefit_czk if total_annual_benefit_czk > 0 else 0.0
    payback_net_years = net_capex_czk / total_annual_benefit_czk if total_annual_benefit_czk > 0 else 0.0

    autarky_pct = (self_consumed_kwh / max(1.0, residential_load_kwh)) * 100.0

    return {
        "gross_capex_czk": round(gross_capex_czk, 0),
        "nzu_subsidy_grant_czk": round(grant_czk, 0),
        "net_capex_czk": round(net_capex_czk, 0),
        "annual_generation_kwh": round(annual_generation_kwh, 1),
        "self_consumption_pct": round(self_consumption_pct, 1),
        "self_consumed_kwh": round(self_consumed_kwh, 1),
        "grid_feedin_kwh": round(grid_feedin_kwh, 1),
        "autarky_sobystacnost_pct": round(min(100.0, autarky_pct), 1),
        "annual_benefits": {
            "electricity_cost_savings_czk": round(annual_savings_self_cons_czk, 0),
            "feedin_or_community_revenue_czk": round(annual_feedin_rev_czk, 0),
            "total_annual_benefit_czk": round(total_annual_benefit_czk, 0)
        },
        "payback_period": {
            "gross_without_subsidy_years": round(payback_gross_years, 1),
            "net_with_nzu_subsidy_years": round(payback_net_years, 1)
        },
        "nzu_detail": nzu
    }
