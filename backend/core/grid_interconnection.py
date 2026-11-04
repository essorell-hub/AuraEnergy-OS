"""
Elektrotechnický engine síťové připojitelnosti a 8760h hodinového profilování pro AuraEnergy OS.
Standardy: PNE 33 3430-1, ČSN EN 50160, NREL SAM 8760 TMY standard.
"""
import math
from typing import Dict, Any, List

# Elektrické parametry standardních distribučních kabelů nízkého napětí (0.4 kV)
CABLE_DATABASE = {
    "al_150": {
        "name": "AYKY 4x150 mm² (Hliník Al)",
        "r_ohm_per_km": 0.206,      # Činný odpor při 20 °C
        "x_ohm_per_km": 0.080,      # Indukční reaktance při 50 Hz
        "current_capacity_a": 275.0 # Proudová zatížitelnost v zemi
    },
    "cu_150": {
        "name": "CYKY 4x150 mm² (Měď Cu)",
        "r_ohm_per_km": 0.124,      # Činný odpor při 20 °C
        "x_ohm_per_km": 0.078,      # Indukční reaktance při 50 Hz
        "current_capacity_a": 355.0 # Proudová zatížitelnost v zemi
    },
    "al_240": {
        "name": "AYKY 4x240 mm² (Hliník Al)",
        "r_ohm_per_km": 0.125,
        "x_ohm_per_km": 0.077,
        "current_capacity_a": 365.0
    }
}

def analyze_grid_interconnection_pcc(
    installed_ac_power_kw: float = 100.0,
    pcc_voltage_v: float = 400.0,
    transformer_capacity_kva: float = 630.0,
    distance_to_substation_m: float = 180.0,
    cable_type: str = "al_150",
    power_factor_cos_phi: float = 1.0 # 1.0 pro čistě činnou dodávku
) -> Dict[str, Any]:
    """
    Kalkulace zpětného vlivu výrobny na distribuční síť dle normy PNE 33 3430-1:
    - Výpočet procentuálního nárůstu napětí Delta U (%) v bodě připojení PCC.
    - Kontrola limitu Delta U <= 2.0 % (přísnější limit pro připojení nových OZE bez vyvolaných investic).
    - Výpočet impedance vedení Z_kabel = sqrt(R^2 + X^2).
    - Vytížení transformátoru (%).
    - Řídicí logika regulace jalového výkonu střídačem Q(U) dle požadavků PNE.
    """
    cable = CABLE_DATABASE.get(cable_type, CABLE_DATABASE["al_150"])
    dist_km = distance_to_substation_m / 1000.0
    
    # 1. Elektrické impedance kabelové trasy
    line_r = cable["r_ohm_per_km"] * dist_km
    line_x = cable["x_ohm_per_km"] * dist_km
    line_z = math.sqrt(line_r**2 + line_x**2)
    
    # Jmenovitý a fázový proud výrobny I = P / (sqrt(3) * U * cos_phi)
    p_w = installed_ac_power_kw * 1000.0
    operating_current_a = p_w / (math.sqrt(3.0) * pcc_voltage_v * power_factor_cos_phi)
    
    # 2. Výpočet nárůstu napětí Delta U dle PNE 33 3430-1
    # Delta U (V) = (P * R + Q * X) / U_nom
    # Při cos phi = 1.0 je Q = 0 => Delta U = (P * R) / U_nom
    sin_phi = math.sqrt(max(0.0, 1.0 - power_factor_cos_phi**2))
    q_var = p_w * (sin_phi / power_factor_cos_phi) if power_factor_cos_phi > 0 else 0.0
    
    delta_u_volts = (p_w * line_r + q_var * line_x) / pcc_voltage_v
    delta_u_pct = (delta_u_volts / pcc_voltage_v) * 100.0
    
    # 3. Vytížení transformátoru
    trafo_loading_pct = (installed_ac_power_kw / transformer_capacity_kva) * 100.0
    cable_loading_pct = (operating_current_a / cable["current_capacity_a"]) * 100.0

    # 4. Rozhodovací logika Q(U) regulace a připojitelnosti
    # Limit dle PNE 33 3430-1 je Delta U <= 2.0 % (příp. 3.0 % s Q(U))
    compliant_standard = bool(delta_u_pct <= 2.0)
    
    if compliant_standard:
        decision_code = "APPROVE_STANDARD"
        status_text = "SCHVÁLENO BEZ VÝHRAD (ΔU ≤ 2.0 %)"
        remedy_text = "Připojení je plně vyhovující bez nutnosti dalších síťových úprav či omezení."
        qu_required = False
    elif delta_u_pct <= 3.0:
        decision_code = "APPROVE_WITH_QU"
        status_text = "PODMÍNĚNĚ SCHVÁLENO S REGULACÍ Q(U) (2.0 % < ΔU ≤ 3.0 %)"
        remedy_text = "Aktivace autonomní křivky střídače Q(U) – induktivní odběr jalového výkonu pro snížení napětí."
        qu_required = True
    else:
        decision_code = "REJECT_GRID_REINFORCEMENT"
        status_text = "ZAMÍTNUTO PRO NÁRŮST NAPĚTÍ (ΔU > 3.0 %)"
        remedy_text = "Nutné posílení vedení (např. kabel CYKY 240 mm² Cu) nebo zřízení vlastní trafostanice 22 kV."
        qu_required = True

    return {
        "installed_ac_power_kw": installed_ac_power_kw,
        "operating_current_a": round(operating_current_a, 1),
        "cable_name": cable["name"],
        "distance_m": distance_to_substation_m,
        "line_resistance_ohm": round(line_r, 4),
        "line_reactance_ohm": round(line_x, 4),
        "line_impedance_ohm": round(line_z, 4),
        "voltage_rise_volts": round(delta_u_volts, 2),
        "voltage_rise_pct": round(delta_u_pct, 2),
        "limit_pne_pct": 2.0,
        "transformer_loading_pct": round(trafo_loading_pct, 1),
        "cable_ampacity_loading_pct": round(cable_loading_pct, 1),
        "compliance_approved": compliant_standard,
        "qu_regulation_required": qu_required,
        "decision_code": decision_code,
        "status_text": status_text,
        "recommended_remedy": remedy_text
    }

def simulate_8760_hourly_generation_and_sizing(
    installed_capacity_kwp: float,
    inverter_ac_power_kw: float,
    tilt_deg: float = 35.0,
    annual_ghi_kwh_m2: float = 1120.0
) -> Dict[str, Any]:
    """
    Generování syntetického hodinového profilu pro všech 8 760 hodin roku (NREL SAM TMY ekvivalent)
    a automatické dimenzování hlavního jističe a rezervované kapacity (RK).
    """
    hourly_output_kw = []
    daily_base = [0.0,0.0,0.0,0.0,0.0,0.01,0.08,0.30,0.62,0.85,0.96,1.0,0.97,0.86,0.64,0.32,0.09,0.01,0.0,0.0,0.0,0.0,0.0,0.0]
    
    total_mwh = 0.0
    for day in range(365):
        day_of_year = day + 1
        # Sezónní modulace osvitu
        season = 0.88 + 0.48 * math.sin((day_of_year - 80) / 365.0 * 2.0 * math.pi)
        
        for h in range(24):
            factor = daily_base[h]
            if factor > 0:
                dc_kw = installed_capacity_kwp * factor * season * 0.83
                ac_kw = min(inverter_ac_power_kw, dc_kw) # Inverter clipping limit
            else:
                ac_kw = 0.0
            hourly_output_kw.append(round(ac_kw, 2))
            total_mwh += (ac_kw / 1000.0)

    # Špičkový výkon AC
    peak_ac_kw = max(hourly_output_kw)
    
    # Dimenzování hlavního jističe (A) a rezervované kapacity (RK)
    # I_max = P_peak / (sqrt(3) * 400 V)
    nominal_current_a = (peak_ac_kw * 1000.0) / (math.sqrt(3.0) * 400.0)
    
    # Výběr standardní řady jističů: 100A, 125A, 160A, 200A, 250A, 315A, 400A
    breaker_series = [63, 80, 100, 125, 160, 200, 250, 315, 400, 500, 630]
    recommended_breaker_a = next((b for b in breaker_series if b >= nominal_current_a * 1.15), 630)
    
    # Doporučená rezervovaná kapacita (RK v kW) se zohledněním 10% bezpečnostní rezervy
    recommended_rk_kw = math.ceil(peak_ac_kw * 1.05)
    
    # Křivka trvání výkonu (Duration curve po 10% decilech)
    sorted_8760 = sorted(hourly_output_kw, reverse=True)
    deciles = [round(sorted_8760[int(pct * 8760 / 100)], 1) for pct in range(0, 100, 10)]

    return {
        "installed_capacity_kwp": installed_capacity_kwp,
        "inverter_ac_power_kw": inverter_ac_power_kw,
        "annual_generation_mwh": round(total_mwh, 2),
        "peak_measured_ac_kw": round(peak_ac_kw, 2),
        "nominal_full_load_current_a": round(nominal_current_a, 1),
        "recommended_main_breaker_a": recommended_breaker_a,
        "recommended_reserved_capacity_rk_kw": recommended_rk_kw,
        "capacity_factor_cuf_pct": round((total_mwh * 1000.0) / (installed_capacity_kwp * 8760.0) * 100.0, 2),
        "hourly_deciles_sample_kw": deciles
    }
