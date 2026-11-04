"""
bifacial_optics_engine.py
=========================
FÁZE 27: Optický model oboustranných (bifaciálních) fotovoltaických modulů.
Využívá 2D View-Factor geometrii pro výpočet:
 1. Zadního difúzního i přímého ozáření odrazem od podkladu (Ground Albedo).
 2. Výšky instalace nad terénem (Clearance Height $H$) a rozteče řad (Pitch $W$).
 3. Koeficientu bifaciality panelu ($\phi_{\text{bifacial}}$, obvykle 70 % až 85 % pro n-type TOPCon a HJT).
 4. Výsledného oboustranného zisku (Bifacial Gain %) a specifického ročního výnosu (kWh/kWp).
"""

import math
from typing import Dict, Any


def simulate_bifacial_gain(
    pv_capacity_kwp: float = 100.0,
    front_annual_generation_mwh: float = 110.0,
    albedo_type: str = "GRASS", # "GRASS" (0.20), "WHITE_GRAVEL" (0.50), "CONCRETE" (0.30), "SNOW" (0.75), "AGRI_SOIL" (0.18)
    bifaciality_factor: float = 0.80, # 80 % pro moderní TOPCon články
    clearance_height_m: float = 1.2, # Výška spodní hrany panelu nad zemí
    collector_width_m: float = 2.3, # Šířka/výška skloněné plochy stolu
    row_pitch_m: float = 6.0, # Osová vzdálenost řad
    tilt_deg: float = 25.0
) -> Dict[str, Any]:
    """
    Kalkulace oboustranného zisku (Bifacial Gain) metodou View-Factor.
    """
    albedo_map = {
        "GRASS": 0.20,
        "WHITE_GRAVEL": 0.50,
        "CONCRETE": 0.30,
        "SNOW": 0.75,
        "AGRI_SOIL": 0.18,
        "WHITE_MEMBRANE": 0.65
    }
    albedo = albedo_map.get(albedo_type.upper(), 0.22)

    # 1. Geometrický pozorovací faktor země na zadní stranu panelu (View Factor F_sky_ground)
    # Vyšší světlá výška (clearance) zmenšuje stín vržený konstrukcí na zem pod modulem
    height_ratio = clearance_height_m / max(0.5, collector_width_m)
    ground_illumination_uniformity = min(0.95, 0.40 + 0.35 * math.atan(height_ratio))

    # Geometrický faktor viditelnosti zadní strany k ozářené ploše terénu
    tilt_rad = math.radians(tilt_deg)
    # Čím strmější sklon, tím větší část osvětleného podkladu vidí zadní strana
    vf_rear_ground = 0.5 * (1.0 - math.cos(tilt_rad)) * (1.0 - math.exp(-row_pitch_m / (2.0 * collector_width_m)))

    # 2. Efektivní zadní ozáření (Rear Irradiance Fraction)
    rear_irradiance_fraction = albedo * vf_rear_ground * ground_illumination_uniformity

    # 3. Bifaciální zisk (Bifacial Gain v %)
    # G_rear = G_front * rear_irradiance_fraction
    # P_rear = P_front * rear_irradiance_fraction * bifaciality_factor
    bifacial_gain_pct = rear_irradiance_fraction * bifaciality_factor * 100.0

    rear_generation_mwh = front_annual_generation_mwh * (bifacial_gain_pct / 100.0)
    total_bifacial_generation_mwh = front_annual_generation_mwh + rear_generation_mwh
    bifacial_specific_yield_kwh_kwp = (total_bifacial_generation_mwh * 1000.0) / pv_capacity_kwp

    return {
        "status": "CALCULATED",
        "albedo_surface": albedo_type.upper(),
        "albedo_reflectance": albedo,
        "bifaciality_factor": bifaciality_factor,
        "geometric_parameters": {
            "clearance_height_m": clearance_height_m,
            "collector_width_m": collector_width_m,
            "row_pitch_m": row_pitch_m,
            "tilt_deg": tilt_deg,
            "view_factor_rear": round(vf_rear_ground, 3)
        },
        "front_annual_generation_mwh": round(front_annual_generation_mwh, 2),
        "rear_annual_generation_mwh": round(rear_generation_mwh, 2),
        "total_bifacial_generation_mwh": round(total_bifacial_generation_mwh, 2),
        "bifacial_gain_pct": round(bifacial_gain_pct, 2),
        "specific_yield_kwh_kwp": round(bifacial_specific_yield_kwh_kwp, 1)
    }
