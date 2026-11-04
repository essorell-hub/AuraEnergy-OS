import math
from typing import Dict, Any, List

def calculate_solar_pv_yield(
    capacity_kwp: float,
    tilt_deg: float = 35.0,
    azimuth_deg: float = 180.0, # 180 = Jih
    system_losses_pct: float = 14.0, # Ztráty kabeláže, měnič, špína
    latitude: float = 50.08, # Např. Praha
    annual_ghi_kwh_m2: float = 1100.0, # Typický globální horizontální osvit pro ČR
    inverter_efficiency_pct: float = 97.0
) -> Dict[str, Any]:
    """
    Simulace výroby solární FVE elektrárny.
    Přepočet GHI na skloněnou plochu panelu (GTI) a kalkulace měsíční i roční výroby (MWh).
    """
    # Faktor korekce sklonu a orientace (zjednodušený Hay-Daviesův / Perezův aproximační model)
    # Optimální sklon v ČR/SR je cca 35° na jih (azimuth 180°)
    optimum_tilt = max(15.0, latitude * 0.76 + 3.1)
    tilt_diff = abs(tilt_deg - optimum_tilt)
    azimuth_diff = abs(azimuth_deg - 180.0)
    
    # Koeficient orientace (1.0 = ideální jih a optimální sklon)
    tilt_factor = math.cos(math.radians(tilt_diff * 0.8))
    azimuth_factor = math.cos(math.radians(azimuth_diff * 0.7))
    plane_of_array_factor = max(0.65, min(1.22, 1.15 * tilt_factor * azimuth_factor))
    
    effective_poa_kwh_m2 = annual_ghi_kwh_m2 * plane_of_array_factor
    
    # Celkové ztráty
    total_derate = (1.0 - system_losses_pct / 100.0) * (inverter_efficiency_pct / 100.0)
    
    # Specifická výroba kWh/kWp
    specific_yield_kwh_kwp = effective_poa_kwh_m2 * total_derate
    
    # Celková roční výroba
    annual_generation_kwh = capacity_kwp * specific_yield_kwh_kwp
    annual_generation_mwh = annual_generation_kwh / 1000.0
    
    # Typická měsíční křivka rozdělení osvitu v mírném pásmu
    # Součet vah = 1.0
    monthly_weights = [0.03, 0.05, 0.08, 0.11, 0.14, 0.14, 0.15, 0.13, 0.09, 0.05, 0.02, 0.01]
    
    monthly_kwh = [round(annual_generation_kwh * w, 1) for w in monthly_weights]
    
    return {
        "capacity_kwp": capacity_kwp,
        "tilt_deg": tilt_deg,
        "azimuth_deg": azimuth_deg,
        "specific_yield_kwh_kwp": round(specific_yield_kwh_kwp, 1),
        "annual_generation_mwh": round(annual_generation_mwh, 3),
        "annual_generation_kwh": round(annual_generation_kwh, 1),
        "monthly_generation_kwh": monthly_kwh,
        "performance_ratio_pct": round(total_derate * 100.0, 1),
        "plane_of_array_irradiance_kwh_m2": round(effective_poa_kwh_m2, 1)
    }

def calculate_battery_storage(
    pv_annual_kwh: float,
    building_annual_consumption_kwh: float,
    battery_capacity_kwh: float,
    battery_efficiency_pct: float = 90.0,
    dod_pct: float = 90.0 # Depth of discharge
) -> Dict[str, Any]:
    """
    Modelování vlivu bateriového úložiště (BESS) na vlastní spotřebu (self-consumption).
    """
    # Bez baterie je přímá spotřeba FVE obvykle 25-35 % (pro komerční/rezidenční profil)
    baseline_self_consumption_pct = 30.0
    
    usable_storage = battery_capacity_kwh * (dod_pct / 100.0)
    # Odhad dodatečného využití přes denní cykly (cca 280 ekvivalentních cyklů ročně)
    stored_and_discharged_annual_kwh = usable_storage * 280.0 * (battery_efficiency_pct / 100.0)
    
    direct_consumption_kwh = pv_annual_kwh * (baseline_self_consumption_pct / 100.0)
    total_self_consumption_kwh = min(
        building_annual_consumption_kwh,
        direct_consumption_kwh + stored_and_discharged_annual_kwh,
        pv_annual_kwh
    )
    
    grid_feed_in_kwh = max(0.0, pv_annual_kwh - total_self_consumption_kwh)
    grid_import_kwh = max(0.0, building_annual_consumption_kwh - total_self_consumption_kwh)
    
    self_sufficiency_pct = (total_self_consumption_kwh / building_annual_consumption_kwh * 100.0) if building_annual_consumption_kwh > 0 else 0.0
    self_consumption_pct = (total_self_consumption_kwh / pv_annual_kwh * 100.0) if pv_annual_kwh > 0 else 0.0
    
    return {
        "battery_capacity_kwh": battery_capacity_kwh,
        "total_self_consumed_kwh": round(total_self_consumption_kwh, 1),
        "grid_feed_in_kwh": round(grid_feed_in_kwh, 1),
        "grid_import_kwh": round(grid_import_kwh, 1),
        "self_sufficiency_pct": round(self_sufficiency_pct, 1),
        "self_consumption_pct": round(self_consumption_pct, 1)
    }
