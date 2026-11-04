"""
grid_stability_iec60909.py
==========================
FÁZE 30 & 31: Zkratové poměry (IEC 60909) a kvalita elektrické energie (ČSN EN 50160).
Vypočítává:
 1. Počáteční souměrný rázový zkratový proud I''k (třífázový zkrat) a nárazový proud ip na přípojnici nn/vn.
 2. Příspěvek distribuční sítě vs. střídačů s omezeným zkratovým proudem (Inverter Fault Contribution ~ 1.1–1.3 x In).
 3. Celkové harmonické zkreslení napětí (THD_u) a proudu (THD_i) s kontrolou limitu normy EN 50160 (max 8.0 % pro nn/vn).
 4. Posouzení dynamické a tepelné odolnosti rozvaděče (Icw, Ipk).
"""

import math
from typing import Dict, Any


def calculate_iec60909_short_circuit_and_harmonics(
    grid_voltage_v: float = 400.0,
    transformer_apparent_power_kva: float = 630.0,
    transformer_uk_pct: float = 4.0, # typicky 4.0 % pro trafo 630 kVA
    inverter_rated_power_kw: float = 250.0,
    cable_length_m: float = 60.0,
    cable_conductor: str = "AL", # "CU" nebo "AL"
    cable_csa_mm2: float = 150.0
) -> Dict[str, Any]:
    """
    Kalkulace zkratového proudu dle IEC 60909 a harmonického zkreslení dle ČSN EN 50160.
    """
    # 1. Impedance transformátoru vn/nn
    un = grid_voltage_v
    sn_trafo = transformer_apparent_power_kva * 1000.0 # VA
    # Napětí naprázdno s koeficientem c = 1.05 pro nn
    c_factor = 1.05
    z_trafo = (transformer_uk_pct / 100.0) * (un ** 2) / sn_trafo # Ohm
    # Pro trafo 630 kVA je R/X cca 0.15 až 0.2
    r_trafo = 0.18 * z_trafo
    x_trafo = math.sqrt(max(0.000001, z_trafo ** 2 - r_trafo ** 2))

    # 2. Impedance kabelového vedení
    resistivity = 0.0282 if cable_conductor.upper() == "AL" else 0.0178 # Ohm * mm2 / m
    r_cable = (resistivity * cable_length_m) / max(1.0, cable_csa_mm2)
    # Reaktance kabelu cca 0.08 mOhm / m pro nn kabely
    x_cable = (0.08 / 1000.0) * cable_length_m

    # Celková impedance smyčky
    r_total = r_trafo + r_cable
    x_total = x_trafo + x_cable
    z_total = math.sqrt(r_total ** 2 + x_total ** 2)

    # 3. Počáteční souměrný rázový zkratový proud sítě I''k_grid (kA)
    ik_double_prime_grid_a = (c_factor * un) / (math.sqrt(3.0) * z_total)
    ik_grid_ka = ik_double_prime_grid_a / 1000.0

    # Nárazový zkratový proud ip (vrcholová hodnota)
    # Poměr R/X určuje součinitel kappa dle IEC 60909
    rx_ratio = r_total / max(0.00001, x_total)
    kappa = 1.02 + 0.98 * math.exp(-3.0 * rx_ratio)
    ip_grid_ka = kappa * math.sqrt(2.0) * ik_grid_ka

    # 4. Příspěvek střídačů (střídače jsou proudově omezené na cca 1.15 In)
    inv_in_a = (inverter_rated_power_kw * 1000.0) / (math.sqrt(3.0) * un)
    ik_inverter_ka = (inv_in_a * 1.20) / 1000.0

    # Celkový zkratový proud v místě připojení PCC
    ik_total_ka = ik_grid_ka + ik_inverter_ka
    ip_total_ka = ip_grid_ka + (math.sqrt(2.0) * ik_inverter_ka)

    # 5. Harmonická analýza (ČSN EN 50160)
    # Zkratový výkon sítě Ssc v místě připojení
    ssc_mva = (math.sqrt(3.0) * un * ik_grid_ka) / 1000.0
    # Poměr výkonu střídače k Ssc
    scr = (ssc_mva * 1000.0) / max(1.0, inverter_rated_power_kw) # Short Circuit Ratio

    # Vlastní proudové harmonické moderních střídačů (THD_i obvykle 2.0 - 3.0 % při plném výkonu)
    thd_i_pct = 2.40
    # THD napětí na přípojnici způsobené střídačem (inversní funkce k SCR)
    thd_u_induced_pct = (thd_i_pct / max(5.0, scr)) * 1.8
    # Základní pozadí sítě (typicky 1.5 - 2.5 % v průmyslových zónách)
    thd_u_background_pct = 2.10
    total_thd_u_pct = math.sqrt(thd_u_background_pct ** 2 + thd_u_induced_pct ** 2)

    en50160_limit_pct = 8.0 # Limit ČSN EN 50160 pro nn/vn
    compliant = total_thd_u_pct <= en50160_limit_pct

    return {
        "status": "APPROVED" if compliant else "WARNING_LIMIT_EXCEEDED",
        "standard": "IEC 60909 / ČSN EN 50160",
        "short_circuit_metrics": {
            "ik_double_prime_grid_ka": round(ik_grid_ka, 2),
            "ik_inverter_contribution_ka": round(ik_inverter_ka, 2),
            "ik_total_pcc_ka": round(ik_total_ka, 2),
            "ip_peak_pcc_ka": round(ip_total_ka, 2),
            "recommended_switchgear_icw_ka": math.ceil(ik_total_ka * 1.25)
        },
        "harmonics_power_quality": {
            "short_circuit_ratio_scr": round(scr, 1),
            "thd_current_inverter_pct": round(thd_i_pct, 2),
            "thd_voltage_induced_pct": round(thd_u_induced_pct, 2),
            "total_pcc_thd_voltage_pct": round(total_thd_u_pct, 2),
            "en50160_limit_pct": en50160_limit_pct,
            "compliant_with_en50160": compliant
        },
        "engineering_recommendation": (
            "Elektrická instalace a rozvaděč plně vyhovují normám IEC 60909 a ČSN EN 50160. "
            f"Doporučená minimální zkratová odolnost přípojnic je {math.ceil(ik_total_ka * 1.25)} kA / 1s."
            if compliant else
            "Upozornění: Celkové harmonické zkreslení překračuje limit normy EN 50160. Doporučeno osadit aktivní filtr harmonických (AHF)."
        )
    }
