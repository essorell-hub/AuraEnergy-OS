"""
retscreen_dynamic_wbs_engine.py
===============================
FÁZE 3.2: Dynamický rozpočtový modul WBS (Work Breakdown Structure) dle RETScreen Cost.xml.
Podporuje neomezený počet rozpočtových položek ve struktuře:
 1. Feasibility Study (Předinvestiční příprava a audity)
 2. Development & Engineering (Projektová dokumentace, EIA, posudky)
 3. Equipment (Hlavní technologie OZE, HVAC, rozvaděče)
 4. Balance of System (Kabelové trasy, potrubí, armatury, měření)
 5. Installation & Construction (Stavební práce, montáž, oživení)
 6. Contingencies (Rezerva na nepředvídané výdaje v % nebo fixní částce)
Umožňuje kalkulaci DPH, jednotkových nákladů a generování položkového výkazu výměr.
"""

from typing import List, Dict, Any


DEFAULT_RETSCREEN_WBS_TEMPLATES: List[Dict[str, Any]] = [
    # 1. Feasibility
    {"wbs": "1.1", "category": "Feasibility", "description": "Energetický audit dle Vyhlášky 141/2021 Sb.", "unit": "ks", "qty": 1, "unit_cost_eur": 3500.0},
    {"wbs": "1.2", "category": "Feasibility", "description": "Měření kvality sítě a impedance PCC", "unit": "ks", "qty": 1, "unit_cost_eur": 1800.0},
    # 2. Development
    {"wbs": "2.1", "category": "Development", "description": "Projektová dokumentace pro stavební povolení (DSP)", "unit": "ks", "qty": 1, "unit_cost_eur": 6200.0},
    {"wbs": "2.2", "category": "Development", "description": "Inženýring, vyjádření DOSS a připojovací smlouva", "unit": "ks", "qty": 1, "unit_cost_eur": 2400.0},
    # 3. Equipment
    {"wbs": "3.1", "category": "Equipment", "description": "Fotovoltaické panely Tier-1 TOPCon 580W", "unit": "kWp", "qty": 250, "unit_cost_eur": 210.0},
    {"wbs": "3.2", "category": "Equipment", "description": "Průmyslové střídače 100 kW s AFCI ochranou", "unit": "ks", "qty": 2, "unit_cost_eur": 4200.0},
    {"wbs": "3.3", "category": "Equipment", "description": "Bateriové úložiště BESS LFP 300 kWh", "unit": "kWh", "qty": 300, "unit_cost_eur": 290.0},
    # 4. BoS
    {"wbs": "4.1", "category": "Balance of System", "description": "Kabelové trasy AYKY/CYKY a perforované žlaby MARS", "unit": "m", "qty": 450, "unit_cost_eur": 38.0},
    {"wbs": "4.2", "category": "Balance of System", "description": "Rozvaděč RH nn s motorovými jističi a SPD I+II", "unit": "ks", "qty": 1, "unit_cost_eur": 8500.0},
    # 5. Labor
    {"wbs": "5.1", "category": "Installation", "description": "Montáž nosných konstrukcí a panelů", "unit": "kWp", "qty": 250, "unit_cost_eur": 45.0},
    {"wbs": "5.2", "category": "Installation", "description": "Elektromontáž, zapojení a výchozí revize dle ČSN 33 1500", "unit": "hod", "qty": 160, "unit_cost_eur": 42.0}
]


def calculate_dynamic_wbs_budget(
    items: List[Dict[str, Any]] = None,
    contingency_pct: float = 5.0,
    vat_tax_pct: float = 21.0
) -> Dict[str, Any]:
    """Kalkuluje celkový rozpočet projektu WBS dle kategorií."""
    if not items:
        items = DEFAULT_RETSCREEN_WBS_TEMPLATES

    category_totals: Dict[str, float] = {
        "Feasibility": 0.0,
        "Development": 0.0,
        "Equipment": 0.0,
        "Balance of System": 0.0,
        "Installation": 0.0
    }

    processed_lines = []
    subtotal = 0.0

    for item in items:
        qty = float(item.get("qty", 1))
        cost = float(item.get("unit_cost_eur", 0.0))
        total_line = qty * cost
        subtotal += total_line

        cat = item.get("category", "Equipment")
        if cat in category_totals:
            category_totals[cat] += total_line
        else:
            category_totals[cat] = total_line

        processed_lines.append({
            "wbs": item.get("wbs", "-"),
            "category": cat,
            "description": item.get("description", "Položka"),
            "unit": item.get("unit", "ks"),
            "qty": qty,
            "unit_cost_eur": round(cost, 2),
            "total_eur": round(total_line, 2)
        })

    contingency_amount = subtotal * (contingency_pct / 100.0)
    total_initial_capex_net = subtotal + contingency_amount
    vat_amount = total_initial_capex_net * (vat_tax_pct / 100.0)
    total_with_vat = total_initial_capex_net + vat_amount

    return {
        "status": "BUDGET_CALCULATED",
        "currency": "EUR",
        "subtotal_net_eur": round(subtotal, 2),
        "contingency_pct": contingency_pct,
        "contingency_eur": round(contingency_amount, 2),
        "total_initial_capex_net_eur": round(total_initial_capex_net, 2),
        "vat_tax_pct": vat_tax_pct,
        "vat_amount_eur": round(vat_amount, 2),
        "total_capex_with_vat_eur": round(total_with_vat, 2),
        "category_totals": {k: round(v, 2) for k, v in category_totals.items()},
        "line_items": processed_lines
    }
