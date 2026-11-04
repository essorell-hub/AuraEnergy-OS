"""
bess_physics_degradation.py
===========================
FÁZE 26: Elektrochemický a poloempirický model degradace lithiových akumulátorů (LFP / NMC).
Modeluje úbytek kapacity (Capacity Fade) a nárůst vnitřního odporu (Resistance Increase)
na základě:
 1. Kalendářního stárnutí (Calendar Aging): Arrheniův vztah, vliv teploty (°C) a průměrného stavu nabití (State of Charge - SoC).
 2. Cyklického stárnutí (Cycle Aging): Hloubka vybití (Depth of Discharge - DoD), rychlost nabíjení/vybíjení (C-rate) a tvorba SEI vrstvy (Solid Electrolyte Interphase).
 3. Predikce životnosti (End of Life - EOL obvykle 80 % nebo 70 % původní kapacity).
 4. Termodynamická bilance chlazení kontejneru (HVAC parasitic load).
"""

import math
from typing import Dict, Any, List


def simulate_bess_electrochemical_degradation(
    nominal_capacity_kwh: float = 100.0,
    chemistry: str = "LFP", # "LFP" (LiFePO4) nebo "NMC" (LiNiMnCoO2)
    daily_cycles: float = 1.2,
    avg_soc_pct: float = 55.0,
    avg_dod_pct: float = 80.0,
    avg_c_rate: float = 0.5,
    ambient_cell_temp_c: float = 25.0,
    project_lifetime_years: int = 20,
    eol_capacity_pct: float = 70.0
) -> Dict[str, Any]:
    """
    Simuluje degradaci bateriového úložiště rok po roce s rozpadem na kalendářní a cyklickou složku.
    """
    # Koeficienty pro chemii článku
    if chemistry.upper() == "LFP":
        # LFP je odolnější vůči vysokému SoC a cyklování, citlivé na podchlazení
        cal_ref_rate = 0.012  # 1.2 % za rok při 25°C a 50% SoC
        cycle_ref_coeff = 0.000045 # fade na ekvivalentní plný cyklus (EFC)
        act_energy_j_mol = 28000.0 # Aktivační energie Arrhenius
    else: # NMC
        cal_ref_rate = 0.019  # 1.9 % za rok při 25°C
        cycle_ref_coeff = 0.000085
        act_energy_j_mol = 34000.0

    R = 8.314 # Plynová konstanta J/(mol*K)
    temp_k = ambient_cell_temp_c + 273.15
    ref_temp_k = 25.0 + 273.15

    # Arrheniův teplotní faktor
    arrhenius_factor = math.exp((act_energy_j_mol / R) * (1.0 / ref_temp_k - 1.0 / temp_k))
    # Vliv SoC (vyšší SoC akceleruje kalendářní degradaci, zejména nad 70 %)
    soc_stress_factor = 1.0 + 0.8 * max(0.0, (avg_soc_pct - 50.0) / 50.0)
    # Vliv C-rate (vyšší C-rate = vyšší mechanické namáhání katody a SEI)
    c_rate_factor = (avg_c_rate / 0.5) ** 0.6
    # Vliv DoD (Wöhlerova křivka baterií)
    dod_factor = (avg_dod_pct / 80.0) ** 1.3

    annual_calendar_fade = cal_ref_rate * arrhenius_factor * soc_stress_factor
    efc_per_year = daily_cycles * (avg_dod_pct / 100.0) * 365.0
    annual_cycle_fade = efc_per_year * cycle_ref_coeff * c_rate_factor * dod_factor

    yearly_profiles = []
    remaining_capacity_pct = 100.0
    eol_year = None
    cell_internal_resistance_mohm = 0.60 # Počáteční vnitřní odpor nového článku

    for yr in range(1, project_lifetime_years + 1):
        # Nelineární průběh v čase (odmocnina z času pro SEI růst na počátku, poté lineární)
        time_factor = (yr ** 0.65 - (yr - 1) ** 0.65)
        yr_fade = (annual_calendar_fade * time_factor * 100.0) + (annual_cycle_fade * 100.0)
        
        remaining_capacity_pct = max(0.0, remaining_capacity_pct - yr_fade)
        cell_internal_resistance_mohm *= (1.0 + (yr_fade / 100.0) * 0.8) # Odpor roste s degradací

        if remaining_capacity_pct <= eol_capacity_pct and eol_year is None:
            eol_year = yr

        yearly_profiles.append({
            "year": yr,
            "remaining_capacity_pct": round(remaining_capacity_pct, 2),
            "usable_capacity_kwh": round(nominal_capacity_kwh * (remaining_capacity_pct / 100.0), 2),
            "annual_fade_pct": round(yr_fade, 3),
            "internal_resistance_mohm": round(cell_internal_resistance_mohm, 3)
        })

    # Parazitní spotřeba HVAC na chlazení kontejneru (cca 3-6 % ročního průchodu energie)
    annual_throughput_mwh = (nominal_capacity_kwh * efc_per_year * 2.0) / 1000.0
    hvac_cooling_load_mwh_yr = annual_throughput_mwh * (0.035 if ambient_cell_temp_c <= 25 else 0.055)

    return {
        "status": "CALCULATED",
        "battery_chemistry": chemistry.upper(),
        "nominal_capacity_kwh": nominal_capacity_kwh,
        "eol_capacity_target_pct": eol_capacity_pct,
        "predicted_eol_year": eol_year if eol_year else f">{project_lifetime_years}",
        "equivalent_full_cycles_per_year": round(efc_per_year, 1),
        "total_20yr_efc": round(efc_per_year * project_lifetime_years, 0),
        "annual_cooling_parasitic_mwh": round(hvac_cooling_load_mwh_yr, 2),
        "degradation_stress_factors": {
            "arrhenius_thermal_factor": round(arrhenius_factor, 3),
            "soc_stress_factor": round(soc_stress_factor, 3),
            "c_rate_factor": round(c_rate_factor, 3),
            "dod_stress_factor": round(dod_factor, 3)
        },
        "yearly_forecast": yearly_profiles
    }
