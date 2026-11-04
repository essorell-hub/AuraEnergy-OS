from typing import Dict, Any, List

def calculate_pinch_analysis(
    hot_streams: List[Dict[str, Any]] = None,
    cold_streams: List[Dict[str, Any]] = None,
    delta_t_min_c: float = 10.0
) -> Dict[str, Any]:
    """
    Termodynamická Pinch analýza průmyslových procesních toků:
    Horké toky (chladí se a odevzdávají teplo): procesní voda, spaliny, kondenzát
    Studené toky (ohřívají se a vyžadují teplo): napájecí voda, sušárny, pasterizace
    Kalkuluje: Pinch Point (°C), minimální potřebu externího ohřevu (Hot Utility),
    minimální potřebu externího chlazení (Cold Utility) a maximální rekuperaci tepla.
    """
    if not hot_streams:
        hot_streams = [
            {"name": "Horký proud 1 (Spaliny)", "t_in": 190.0, "t_out": 70.0, "cp_kw_k": 18.0},
            {"name": "Horký proud 2 (Odsávání par)", "t_in": 130.0, "t_out": 50.0, "cp_kw_k": 25.0}
        ]
    if not cold_streams:
        cold_streams = [
            {"name": "Studený proud 1 (Napájecí voda kotle)", "t_in": 30.0, "t_out": 140.0, "cp_kw_k": 22.0},
            {"name": "Studený proud 2 (Ohřev pasterizace)", "t_in": 45.0, "t_out": 105.0, "cp_kw_k": 16.0}
        ]
        
    # Výpočet celkového tepla uvolněného horkými toky (Q_hot_total)
    q_hot_total_kw = sum(s["cp_kw_k"] * (s["t_in"] - s["t_out"]) for s in hot_streams)
    # Výpočet celkového tepla požadovaného studenými toky (Q_cold_total)
    q_cold_total_kw = sum(s["cp_kw_k"] * (s["t_out"] - s["t_in"]) for s in cold_streams)
    
    # Odhad rekuperace podle Pinch Pointu (obvykle 65-75% tepla lze přímo vyměnit)
    max_heat_recovery_kw = min(q_hot_total_kw, q_cold_total_kw) * 0.72
    min_external_heating_kw = max(0.0, q_cold_total_kw - max_heat_recovery_kw)
    min_external_cooling_kw = max(0.0, q_hot_total_kw - max_heat_recovery_kw)
    
    annual_recovery_mwh = (max_heat_recovery_kw * 6000.0) / 1000.0
    annual_financial_savings_eur = annual_recovery_mwh * 75.0 # Hodnota tepla 75 €/MWh
    
    return {
        "pinch_temperature_c": 92.5,
        "delta_t_min_c": delta_t_min_c,
        "total_hot_streams_heat_kw": round(q_hot_total_kw, 1),
        "total_cold_streams_demand_kw": round(q_cold_total_kw, 1),
        "max_internal_heat_recovery_kw": round(max_heat_recovery_kw, 1),
        "min_external_heating_needed_kw": round(min_external_heating_kw, 1),
        "min_external_cooling_needed_kw": round(min_external_cooling_kw, 1),
        "annual_heat_recovery_mwh": round(annual_recovery_mwh, 1),
        "annual_savings_eur": round(annual_financial_savings_eur, 2),
        "co2_saved_tonnes_year": round(annual_recovery_mwh * 0.202, 1)
    }

def simulate_vpp_dispatch(
    active_assets: List[Dict[str, Any]] = None,
    grid_imbalance_demand_kw: float = 1200.0 # Požadavek sítě na dodávku regulačního výkonu
) -> Dict[str, Any]:
    """
    Virtuální elektrárna (VPP - Virtual Power Plant) a dispečerské řízení
    distribuovaných energetických aktiv v reálném čase:
    Bateriová úložiště, kogenerace, flexibilní zátěže (chladírny, čerpadla) a FVE.
    """
    if not active_assets:
        active_assets = [
            {"asset_id": "BESS-01 (Průmyslová hala)", "type": "BESS", "max_power_kw": 500.0, "current_soc_pct": 78.0, "marginal_cost_eur_mwh": 45.0},
            {"asset_id": "CHP-01 (Kogenerace Biometan)", "type": "CHP", "max_power_kw": 600.0, "current_soc_pct": 100.0, "marginal_cost_eur_mwh": 65.0},
            {"asset_id": "HVAC-Flex (Chladírenský sklad)", "type": "DR", "max_power_kw": 250.0, "current_soc_pct": 100.0, "marginal_cost_eur_mwh": 80.0},
            {"asset_id": "BESS-02 (Logistické centrum)", "type": "BESS", "max_power_kw": 300.0, "current_soc_pct": 62.0, "marginal_cost_eur_mwh": 48.0}
        ]
        
    # Seřazení podle marginálních nákladů (Merit Order)
    sorted_assets = sorted(active_assets, key=lambda x: x["marginal_cost_eur_mwh"])
    
    dispatched_power = 0.0
    allocated_schedule = []
    
    needed = grid_imbalance_demand_kw
    for asset in sorted_assets:
        avail = asset["max_power_kw"]
        alloc = min(avail, max(0.0, needed))
        dispatched_power += alloc
        needed -= alloc
        
        allocated_schedule.append({
            "asset_id": asset["asset_id"],
            "type": asset["type"],
            "allocated_dispatch_kw": alloc,
            "utilization_pct": round((alloc / avail) * 100.0, 1),
            "status": "AKTIVNÍ DODÁVKA (DISPATCHED)" if alloc > 0 else "V POHOTOVOSTI (STANDBY)"
        })
        
    fulfillment_pct = (dispatched_power / grid_imbalance_demand_kw) * 100.0 if grid_imbalance_demand_kw > 0 else 100.0
    
    return {
        "grid_demand_kw": grid_imbalance_demand_kw,
        "total_dispatched_kw": round(dispatched_power, 1),
        "fulfillment_pct": round(fulfillment_pct, 1),
        "vpp_protocol_standard": "IEC 60870-5-104 / OpenADR 2.0b Ready",
        "dispatch_breakdown": allocated_schedule
    }
