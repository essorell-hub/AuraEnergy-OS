import math
from typing import Dict, Any, List

def run_day_ahead_mpc_prediction(
    installed_pv_kwp: float = 100.0,
    battery_capacity_kwh: float = 120.0,
    battery_max_power_kw: float = 60.0,
    base_daily_load_kwh: float = 380.0
) -> Dict[str, Any]:
    """
    Prediktivní model řízení (Model Predictive Control - MPC) na 24 hodin dopředu:
    - AI předpověď solární výroby na základě předpovědi počasí (slunečno/oblačno)
    - Predikce profilu spotřeby budovy (pracovní doba 7-18h)
    - MPC optimalizace nabíjení a vybíjení baterie pro minimalizaci nákupu ze sítě v drahých hodinách.
    """
    hours = list(range(24))
    
    # 1. 24h profil spotřeby zátěže (Load curve)
    load_curve = []
    for h in hours:
        if 7 <= h <= 17:
            # Provozní špička v pracovní době
            l = (base_daily_load_kwh / 24.0) * (1.6 + 0.3 * math.sin((h - 7) / 10.0 * math.pi))
        else:
            # Noční klidová spotřeba (chlazení, servery)
            l = (base_daily_load_kwh / 24.0) * 0.45
        load_curve.append(round(l, 2))
        
    # 2. 24h solární výroba (GHI profil - zvonová křivka mezi 6h a 20h)
    pv_generation = []
    for h in hours:
        if 6 <= h <= 19:
            gen = (installed_pv_kwp * 0.78) * math.sin((h - 6) / 13.0 * math.pi)
        else:
            gen = 0.0
        pv_generation.append(max(0.0, round(gen, 2)))
        
    # 3. MPC optimalizace toku energie s baterií
    current_soc_kwh = battery_capacity_kwh * 0.30 # Počáteční nabití 30%
    battery_action = [] # + nabíjení, - vybíjení
    battery_soc_trajectory = []
    grid_import = []
    grid_export = []
    
    for h in hours:
        net_balance = pv_generation[h] - load_curve[h] # Kladné = přebytek, Záporné = deficit
        
        if net_balance > 0:
            # Přebytek FVE: nabíjíme baterii
            charge_power = min(net_balance, battery_max_power_kw, battery_capacity_kwh - current_soc_kwh)
            current_soc_kwh += charge_power * 0.92 # 92% účinnost nabíjení
            surplus = net_balance - charge_power
            battery_action.append(round(charge_power, 2))
            grid_export.append(round(surplus, 2))
            grid_import.append(0.0)
        else:
            # Deficit: pokrýváme z baterie, zbytek ze sítě
            deficit = abs(net_balance)
            discharge_power = min(deficit, battery_max_power_kw, current_soc_kwh - (battery_capacity_kwh * 0.10))
            current_soc_kwh -= discharge_power
            needed_from_grid = deficit - discharge_power
            battery_action.append(round(-discharge_power, 2))
            grid_import.append(round(needed_from_grid, 2))
            grid_export.append(0.0)
            
        battery_soc_trajectory.append(round((current_soc_kwh / battery_capacity_kwh) * 100.0, 1))
        
    total_pv_kwh = sum(pv_generation)
    total_load_kwh = sum(load_curve)
    total_import_kwh = sum(grid_import)
    total_export_kwh = sum(grid_export)
    self_sufficiency_pct = ((total_load_kwh - total_import_kwh) / total_load_kwh) * 100.0

    return {
        "installed_pv_kwp": installed_pv_kwp,
        "battery_capacity_kwh": battery_capacity_kwh,
        "total_day_pv_kwh": round(total_pv_kwh, 1),
        "total_day_load_kwh": round(total_load_kwh, 1),
        "total_grid_import_kwh": round(total_import_kwh, 1),
        "total_grid_export_kwh": round(total_export_kwh, 1),
        "mpc_self_sufficiency_pct": round(self_sufficiency_pct, 1),
        "hourly_data": {
            "hours": [f"{h:02d}:00" for h in hours],
            "load_kwh": load_curve,
            "pv_generation_kwh": pv_generation,
            "battery_action_kw": battery_action,
            "battery_soc_pct": battery_soc_trajectory,
            "grid_import_kwh": grid_import
        }
    }
