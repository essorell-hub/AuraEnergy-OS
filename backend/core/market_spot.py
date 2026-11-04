import random
from typing import Dict, Any, List

def get_live_market_spot_data() -> Dict[str, Any]:
    """
    Simulace reálných 24hodinových spotových cen elektřiny (OTE ČR / EPEX SPOT Day-Ahead).
    Generuje profil s poledním solárním propadem (Duck Curve) a ranní/večerní špičkou.
    """
    # 24 hodin: noční nízké ceny, ranní špička (7-9h), polední solární propad (12-14h), večerní špička (18-21h)
    base_profile = [
        65.0, 55.0, 50.0, 48.0, 52.0, 75.0,
        115.0, 142.0, 138.0, 105.0, 75.0, 42.0,
        28.0, 25.0, 38.0, 70.0, 95.0, 135.0,
        168.0, 155.0, 130.0, 105.0, 85.0, 70.0
    ]
    
    # Lehké náhodné variace pro živý dojem
    hourly_prices = [round(p + random.uniform(-4.0, 4.0), 2) for p in base_profile]
    
    min_price = min(hourly_prices)
    max_price = max(hourly_prices)
    avg_price = sum(hourly_prices) / len(hourly_prices)
    spread = max_price - min_price
    
    # Arbitrážní doporučení pro BESS
    charge_hours = [i for i, p in enumerate(hourly_prices) if p <= min_price + 10.0]
    discharge_hours = [i for i, p in enumerate(hourly_prices) if p >= max_price - 15.0]

    return {
        "market": "OTE / EPEX SPOT Day-Ahead",
        "currency": "EUR/MWh",
        "hourly_prices": hourly_prices,
        "metrics": {
            "min_price_eur_mwh": round(min_price, 2),
            "max_price_eur_mwh": round(max_price, 2),
            "avg_price_eur_mwh": round(avg_price, 2),
            "max_spread_eur_mwh": round(spread, 2)
        },
        "optimal_bess_schedule": {
            "charge_hours": [f"{h:02d}:00" for h in charge_hours],
            "discharge_hours": [f"{h:02d}:00" for h in discharge_hours]
        }
    }
