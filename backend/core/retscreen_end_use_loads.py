"""
retscreen_end_use_loads.py
==========================
Rozšířený modul energetických zátěží dle RETScreen Expert Energy Model:
 1. Vytápění (Space Heating) - výpočet přes HDD a prostup tepla obálky budovy ($U_{mean} \times A$).
 2. Chlazení (Space Cooling) - výpočet přes CDD, chladicí zátěž a EER/SEER chladičů.
 3. Osvětlení (Lighting Loads) - Lighting Power Density (LPD ve $W/m^2$) s tepelnou interakcí na chlazení a vytápění.
 4. Technologická a kancelářská zařízení (Plug Loads / Equipment) ve $W/m^2$.
 5. Příprava teplé užitkové vody (Domestic Hot Water - DHW) v litrech na osobu/den.
 6. Kumulativní 25letý graf peněžních toků (Cumulative Cash Flows Graph) s vyznačením bodu zlomu (Equity Payback).
"""

from typing import Dict, Any, List


def calculate_detailed_end_use_loads(
    floor_area_m2: float = 4500.0,
    occupancy_persons: int = 180,
    
    # 1. Lighting
    lighting_power_density_w_m2: float = 10.5, # W/m2 dle ASHRAE 90.1
    lighting_operating_hours_yr: float = 2800.0,
    lighting_led_retrofit_savings_pct: float = 55.0, # přechod na LED

    # 2. Equipment / Plug Loads
    equipment_power_density_w_m2: float = 12.0, # W/m2
    equipment_operating_hours_yr: float = 3000.0,

    # 3. Heating & Envelope
    envelope_u_value_w_m2k: float = 0.85, # průměrné U obálky
    heating_design_indoor_temp_c: float = 21.0,
    heating_degree_days: float = 3100.0,
    heating_system_efficiency: float = 0.88, # stávající plynový kotel

    # 4. Cooling
    cooling_degree_days: float = 180.0,
    cooling_chiller_seer: float = 3.4,

    # 5. Domestic Hot Water (DHW)
    dhw_liters_per_person_day: float = 25.0, # l/osoba/den
    dhw_supply_temp_c: float = 55.0,
    dhw_cold_water_temp_c: float = 10.0
) -> Dict[str, Any]:
    """
    Kalkulace spotřeby energie rozdělené do 5 koncových užití (End-Use Breakdown).
    """
    # 1. Osvětlení (Lighting)
    base_lighting_kwh_yr = (floor_area_m2 * lighting_power_density_w_m2 * lighting_operating_hours_yr) / 1000.0
    proposed_lighting_kwh_yr = base_lighting_kwh_yr * (1.0 - lighting_led_retrofit_savings_pct / 100.0)
    saved_lighting_kwh_yr = base_lighting_kwh_yr - proposed_lighting_kwh_yr

    # 2. Zařízení (Plug Loads)
    equipment_kwh_yr = (floor_area_m2 * equipment_power_density_w_m2 * equipment_operating_hours_yr) / 1000.0

    # 3. Vytápění (Space Heating)
    # Tepelná ztráta obálkou budovy kWh/rok = (U * A * HDD * 24) / 1000
    base_heating_thermal_kwh_yr = (envelope_u_value_w_m2k * floor_area_m2 * 2.2 * heating_degree_days * 24.0) / 1000.0
    base_heating_fuel_kwh_yr = base_heating_thermal_kwh_yr / heating_system_efficiency

    # Tepelný zisk ze snížení osvětlení (Tepelná interakce: méně odpadního tepla z LED = mírně vyšší topná potřeba cca 15%)
    thermal_interaction_heating_penalty = saved_lighting_kwh_yr * 0.15
    proposed_heating_fuel_kwh_yr = (base_heating_thermal_kwh_yr + thermal_interaction_heating_penalty) * 0.70 / 3.2 # Náhrada TČ s COP 3.2 a zateplením (-30%)

    # 4. Chlazení (Space Cooling)
    # Chlazení těží ze snížení vnitřních zisků z LED (o 30 % méně tepla na chlazení)
    base_cooling_thermal_kwh_yr = (floor_area_m2 * 25.0 * (cooling_degree_days / 180.0))
    base_cooling_elec_kwh_yr = base_cooling_thermal_kwh_yr / cooling_chiller_seer
    proposed_cooling_elec_kwh_yr = (base_cooling_thermal_kwh_yr - saved_lighting_kwh_yr * 0.30) / (cooling_chiller_seer * 1.35)

    # 5. Teplá užitková voda (DHW)
    # E = m * c * delta_T (c = 4.186 kJ/kg/K = 0.001163 kWh/kg/K)
    annual_dhw_liters = occupancy_persons * dhw_liters_per_person_day * 260.0 # 260 pracovních dní
    dhw_thermal_kwh_yr = annual_dhw_liters * (dhw_supply_temp_c - dhw_cold_water_temp_c) * 0.001163
    dhw_fuel_kwh_yr = dhw_thermal_kwh_yr / 0.85 # stávající účinnost

    # Souhrny
    base_total_kwh_yr = base_lighting_kwh_yr + equipment_kwh_yr + base_heating_fuel_kwh_yr + base_cooling_elec_kwh_yr + dhw_fuel_kwh_yr
    proposed_total_kwh_yr = proposed_lighting_kwh_yr + equipment_kwh_yr + proposed_heating_fuel_kwh_yr + proposed_cooling_elec_kwh_yr + (dhw_thermal_kwh_yr / 2.8)

    net_energy_savings_kwh_yr = base_total_kwh_yr - proposed_total_kwh_yr
    net_savings_pct = (net_energy_savings_kwh_yr / base_total_kwh_yr) * 100.0

    return {
        "status": "LOADS_CALCULATED",
        "standard": "RETScreen Expert Energy Model End-Use Breakdown",
        "breakdown": {
            "lighting": {
                "base_kwh_yr": round(base_lighting_kwh_yr, 0),
                "proposed_kwh_yr": round(proposed_lighting_kwh_yr, 0),
                "savings_kwh_yr": round(saved_lighting_kwh_yr, 0)
            },
            "equipment_plug_loads": {
                "base_kwh_yr": round(equipment_kwh_yr, 0),
                "proposed_kwh_yr": round(equipment_kwh_yr, 0),
                "savings_kwh_yr": 0.0
            },
            "space_heating": {
                "base_kwh_yr": round(base_heating_fuel_kwh_yr, 0),
                "proposed_kwh_yr": round(proposed_heating_fuel_kwh_yr, 0),
                "savings_kwh_yr": round(base_heating_fuel_kwh_yr - proposed_heating_fuel_kwh_yr, 0)
            },
            "space_cooling": {
                "base_kwh_yr": round(base_cooling_elec_kwh_yr, 0),
                "proposed_kwh_yr": round(proposed_cooling_elec_kwh_yr, 0),
                "savings_kwh_yr": round(base_cooling_elec_kwh_yr - proposed_cooling_elec_kwh_yr, 0)
            },
            "domestic_hot_water_dhw": {
                "base_kwh_yr": round(dhw_fuel_kwh_yr, 0),
                "proposed_kwh_yr": round(dhw_thermal_kwh_yr / 2.8, 0),
                "savings_kwh_yr": round(dhw_fuel_kwh_yr - (dhw_thermal_kwh_yr / 2.8), 0)
            }
        },
        "summary": {
            "base_total_annual_mwh": round(base_total_kwh_yr / 1000.0, 1),
            "proposed_total_annual_mwh": round(proposed_total_kwh_yr / 1000.0, 1),
            "annual_energy_savings_mwh": round(net_energy_savings_kwh_yr / 1000.0, 1),
            "total_savings_pct": round(net_savings_pct, 1)
        }
    }


def generate_cumulative_cash_flow_series(
    initial_equity_eur: float = 35000.0,
    year1_net_savings_eur: float = 14500.0,
    annual_om_eur: float = 1200.0,
    debt_payment_eur: float = 5800.0,
    debt_term_years: int = 15,
    inflation_rate_pct: float = 2.5,
    energy_escalation_pct: float = 3.5,
    evaluation_years: int = 25
) -> Dict[str, Any]:
    """
    Generuje křivku Cumulative Cash Flows Graph pro zobrazení bodu návratnosti (Break-even).
    """
    cumulative = -initial_equity_eur
    series = [{"year": 0, "annual_net_cash_eur": -round(initial_equity_eur, 0), "cumulative_cash_eur": round(cumulative, 0)}]
    break_even_year = None

    for yr in range(1, evaluation_years + 1):
        esc_savings = year1_net_savings_eur * ((1.0 + energy_escalation_pct / 100.0)**yr)
        esc_om = annual_om_eur * ((1.0 + inflation_rate_pct / 100.0)**yr)
        debt = debt_payment_eur if yr <= debt_term_years else 0.0

        net_flow = esc_savings - esc_om - debt
        cumulative += net_flow

        if cumulative >= 0 and break_even_year is None:
            # Lineární interpolace přesného bodu v roce
            prev = series[-1]["cumulative_cash_eur"]
            fraction = abs(prev) / max(1.0, net_flow)
            break_even_year = round((yr - 1) + fraction, 1)

        series.append({
            "year": yr,
            "annual_net_cash_eur": round(net_flow, 0),
            "cumulative_cash_eur": round(cumulative, 0)
        })

    return {
        "status": "GENERATED",
        "equity_payback_years": break_even_year if break_even_year else f">{evaluation_years}",
        "25yr_cumulative_wealth_eur": round(cumulative, 0),
        "cash_flow_series": series
    }
