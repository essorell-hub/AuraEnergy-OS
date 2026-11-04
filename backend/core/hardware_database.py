"""
Extensive Tier-1 Global & European Hardware Database (hardware_database.py - FÁZE 16)
Includes:
 - PV Modules: JinkoSolar, LONGi, Trina Solar, Canadian Solar, JA Solar, SunPower/Maxeon, Huasun HJT
 - Inverters: GoodWe, Victron Energy, Fronius, Huawei, SMA, SolarEdge, Wattsonic
 - Batteries (BESS): BYD, Pylontech, GoodWe Lynx, Huawei LUNA2000, Victron Energy Lithium
 - Custom Component Creation & JSON/CSV Import API
"""

import sqlite3
import json
import os
from typing import Dict, Any, List, Optional

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "projects.db")


# -------------------------------------------------------------
# Tier-1 Pre-populated Master Hardware Catalogs
# -------------------------------------------------------------
TIER1_PV_MODULES = [
    {
        "id": "jinko-tiger-neo-580",
        "manufacturer": "JinkoSolar",
        "model_name": "Tiger Neo 72HL4-BDV 580W Bifacial",
        "cell_technology": "N-Type TOPCon",
        "rated_power_w": 580.0,
        "efficiency_pct": 22.45,
        "bifaciality_factor": 0.80,
        "temp_coeff_pmax": -0.30,
        "noct_c": 45.0,
        "product_warranty_years": 15,
        "performance_warranty_years": 30,
        "annual_degradation_pct": 0.40
    },
    {
        "id": "longi-himo-x6-440",
        "manufacturer": "LONGi Solar",
        "model_name": "Hi-MO X6 Explorer 440W HPBC",
        "cell_technology": "HPBC Back-Contact",
        "rated_power_w": 440.0,
        "efficiency_pct": 22.50,
        "bifaciality_factor": 0.0,
        "temp_coeff_pmax": -0.29,
        "noct_c": 45.0,
        "product_warranty_years": 15,
        "performance_warranty_years": 25,
        "annual_degradation_pct": 0.40
    },
    {
        "id": "trina-vertex-s-435",
        "manufacturer": "Trina Solar",
        "model_name": "Vertex S+ TSM-NEG9R.28 435W",
        "cell_technology": "N-Type i-TOPCon Double-Glass",
        "rated_power_w": 435.0,
        "efficiency_pct": 21.80,
        "bifaciality_factor": 0.0,
        "temp_coeff_pmax": -0.30,
        "noct_c": 43.0,
        "product_warranty_years": 25,
        "performance_warranty_years": 30,
        "annual_degradation_pct": 0.40
    },
    {
        "id": "canadian-topbihiku-690",
        "manufacturer": "Canadian Solar",
        "model_name": "TOPBiHiKu7 690W Bifacial",
        "cell_technology": "N-Type TOPCon",
        "rated_power_w": 690.0,
        "efficiency_pct": 22.20,
        "bifaciality_factor": 0.85,
        "temp_coeff_pmax": -0.29,
        "noct_c": 42.0,
        "product_warranty_years": 12,
        "performance_warranty_years": 30,
        "annual_degradation_pct": 0.35
    },
    {
        "id": "ja-solar-deepblue-575",
        "manufacturer": "JA Solar",
        "model_name": "DeepBlue 4.0 Pro 575W",
        "cell_technology": "N-Type Bycium+",
        "rated_power_w": 575.0,
        "efficiency_pct": 22.30,
        "bifaciality_factor": 0.80,
        "temp_coeff_pmax": -0.30,
        "noct_c": 45.0,
        "product_warranty_years": 12,
        "performance_warranty_years": 30,
        "annual_degradation_pct": 0.40
    },
    {
        "id": "maxeon-6-440",
        "manufacturer": "SunPower / Maxeon",
        "model_name": "Maxeon 6 AC 440W Ultra-Premium",
        "cell_technology": "IBC Maxeon Gen 6",
        "rated_power_w": 440.0,
        "efficiency_pct": 22.80,
        "bifaciality_factor": 0.0,
        "temp_coeff_pmax": -0.29,
        "noct_c": 42.0,
        "product_warranty_years": 40,
        "performance_warranty_years": 40,
        "annual_degradation_pct": 0.25
    },
    {
        "id": "huasun-himalaya-700",
        "manufacturer": "Huasun Energy",
        "model_name": "Himalaya G12-132 700W HJT",
        "cell_technology": "Heterojunction (HJT)",
        "rated_power_w": 700.0,
        "efficiency_pct": 22.53,
        "bifaciality_factor": 0.88,
        "temp_coeff_pmax": -0.26,
        "noct_c": 44.0,
        "product_warranty_years": 15,
        "performance_warranty_years": 30,
        "annual_degradation_pct": 0.35
    }
]

TIER1_INVERTERS = [
    {
        "id": "goodwe-et-10k",
        "manufacturer": "GoodWe",
        "model_name": "ET Plus Series GW10K-ET (10 kW)",
        "phases": 3,
        "inverter_type": "HYBRID",
        "rated_ac_power_kw": 10.0,
        "max_pv_input_kw": 15.0,
        "max_efficiency_pct": 98.2,
        "mppt_channels": 2,
        "mppt_voltage_range_v": "200 - 850 V",
        "cooling": "Pasivní (tiché chlazení)",
        "warranty_years": 5
    },
    {
        "id": "fronius-symo-gen24-10",
        "manufacturer": "Fronius",
        "model_name": "Symo GEN24 10.0 Plus (10 kW)",
        "phases": 3,
        "inverter_type": "HYBRID",
        "rated_ac_power_kw": 10.0,
        "max_pv_input_kw": 15.0,
        "max_efficiency_pct": 98.2,
        "mppt_channels": 2,
        "mppt_voltage_range_v": "80 - 1000 V",
        "cooling": "Aktivní ventilované",
        "warranty_years": 5
    },
    {
        "id": "huawei-sun2000-10ktl-m1",
        "manufacturer": "Huawei",
        "model_name": "SUN2000-10KTL-M1 High-Current",
        "phases": 3,
        "inverter_type": "HYBRID",
        "rated_ac_power_kw": 10.0,
        "max_pv_input_kw": 15.0,
        "max_efficiency_pct": 98.6,
        "mppt_channels": 2,
        "mppt_voltage_range_v": "140 - 980 V",
        "cooling": "Pasivní",
        "warranty_years": 10
    },
    {
        "id": "victron-multiplus-ii-5k",
        "manufacturer": "Victron Energy",
        "model_name": "MultiPlus-II 48/5000/70-50",
        "phases": 1,
        "inverter_type": "OFF_GRID_HYBRID",
        "rated_ac_power_kw": 4.0,
        "max_pv_input_kw": 6.0,
        "max_efficiency_pct": 95.0,
        "mppt_channels": 1,
        "mppt_voltage_range_v": "48 V DC Bus",
        "cooling": "Aktivní",
        "warranty_years": 5
    },
    {
        "id": "solaredge-se10k-rw",
        "manufacturer": "SolarEdge",
        "model_name": "SE10K Home Hub Inverter",
        "phases": 3,
        "inverter_type": "HYBRID_OPTIMIZED",
        "rated_ac_power_kw": 10.0,
        "max_pv_input_kw": 20.0,
        "max_efficiency_pct": 98.0,
        "mppt_channels": 1, # Direct optimizer bus
        "mppt_voltage_range_v": "750 V Fixed Bus",
        "cooling": "Pasivní",
        "warranty_years": 12
    },
    {
        "id": "huawei-sun2000-100ktl-m2",
        "manufacturer": "Huawei",
        "model_name": "SUN2000-100KTL-M2 Commercial",
        "phases": 3,
        "inverter_type": "STRING_GRID_TIED",
        "rated_ac_power_kw": 100.0,
        "max_pv_input_kw": 150.0,
        "max_efficiency_pct": 98.8,
        "mppt_channels": 10,
        "mppt_voltage_range_v": "200 - 1000 V",
        "cooling": "Smart Air Cooling",
        "warranty_years": 5
    }
]

TIER1_BATTERIES = [
    {
        "id": "byd-hvs-10-2",
        "manufacturer": "BYD",
        "model_name": "Battery-Box Premium HVS 10.2 kWh",
        "chemistry": "LFP (Lithium Iron Phosphate)",
        "voltage_type": "HIGH_VOLTAGE (400V)",
        "nominal_capacity_kwh": 10.24,
        "usable_capacity_kwh": 10.24,
        "dod_pct": 100.0,
        "roundtrip_efficiency_pct": 96.0,
        "c_rate": 1.0,
        "cycle_life": 6000,
        "warranty_years": 10
    },
    {
        "id": "pylontech-force-h2-14",
        "manufacturer": "Pylontech",
        "model_name": "Force-H2 14.21 kWh HV System",
        "chemistry": "LFP",
        "voltage_type": "HIGH_VOLTAGE (384V)",
        "nominal_capacity_kwh": 14.21,
        "usable_capacity_kwh": 13.50,
        "dod_pct": 95.0,
        "roundtrip_efficiency_pct": 95.0,
        "c_rate": 0.8,
        "cycle_life": 6000,
        "warranty_years": 10
    },
    {
        "id": "huawei-luna2000-15-s0",
        "manufacturer": "Huawei",
        "model_name": "LUNA2000-15-S0 Modular 15 kWh",
        "chemistry": "LFP",
        "voltage_type": "HIGH_VOLTAGE (600V)",
        "nominal_capacity_kwh": 15.0,
        "usable_capacity_kwh": 15.0,
        "dod_pct": 100.0,
        "roundtrip_efficiency_pct": 95.5,
        "c_rate": 0.5,
        "cycle_life": 6500,
        "warranty_years": 10
    },
    {
        "id": "goodwe-lynx-home-f-9-8",
        "manufacturer": "GoodWe",
        "model_name": "Lynx Home F Series LX F9.8-H",
        "chemistry": "LFP",
        "voltage_type": "HIGH_VOLTAGE (307V)",
        "nominal_capacity_kwh": 9.83,
        "usable_capacity_kwh": 9.83,
        "dod_pct": 100.0,
        "roundtrip_efficiency_pct": 96.0,
        "c_rate": 0.8,
        "cycle_life": 6000,
        "warranty_years": 10
    },
    {
        "id": "victron-smart-lithium-200",
        "manufacturer": "Victron Energy",
        "model_name": "Lithium SuperPack 25.6V 200Ah (5.12 kWh)",
        "chemistry": "LFP",
        "voltage_type": "LOW_VOLTAGE (48V/24V)",
        "nominal_capacity_kwh": 5.12,
        "usable_capacity_kwh": 4.60,
        "dod_pct": 90.0,
        "roundtrip_efficiency_pct": 92.0,
        "c_rate": 0.5,
        "cycle_life": 4000,
        "warranty_years": 5
    }
]


def init_hardware_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS hardware_components (
                id TEXT PRIMARY KEY,
                category TEXT NOT NULL, -- MODULE, INVERTER, BATTERY
                manufacturer TEXT NOT NULL,
                model_name TEXT NOT NULL,
                params_json TEXT NOT NULL,
                is_custom INTEGER DEFAULT 0,
                created_at TEXT NOT NULL
            )
        """)
        
        # Seed if empty
        cursor.execute("SELECT COUNT(*) FROM hardware_components")
        if cursor.fetchone()[0] == 0:
            for m in TIER1_PV_MODULES:
                cursor.execute("INSERT OR REPLACE INTO hardware_components VALUES (?, 'MODULE', ?, ?, ?, 0, datetime('now'))", 
                               (m["id"], m["manufacturer"], m["model_name"], json.dumps(m, ensure_ascii=False)))
            for i in TIER1_INVERTERS:
                cursor.execute("INSERT OR REPLACE INTO hardware_components VALUES (?, 'INVERTER', ?, ?, ?, 0, datetime('now'))", 
                               (i["id"], i["manufacturer"], i["model_name"], json.dumps(i, ensure_ascii=False)))
            for b in TIER1_BATTERIES:
                cursor.execute("INSERT OR REPLACE INTO hardware_components VALUES (?, 'BATTERY', ?, ?, ?, 0, datetime('now'))", 
                               (b["id"], b["manufacturer"], b["model_name"], json.dumps(b, ensure_ascii=False)))
            conn.commit()


def get_all_hardware(category: Optional[str] = None) -> List[Dict[str, Any]]:
    init_hardware_db()
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        if category:
            cursor.execute("SELECT * FROM hardware_components WHERE category = ? ORDER BY manufacturer, model_name", (category,))
        else:
            cursor.execute("SELECT * FROM hardware_components ORDER BY category, manufacturer")
        rows = cursor.fetchall()
        result = []
        for r in rows:
            d = dict(r)
            d["details"] = json.loads(d["params_json"])
            result.append(d)
        return result


def add_custom_component(category: str, manufacturer: str, model_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
    init_hardware_db()
    cid = f"custom_{category.lower()}_{int(sqlite3.time.time())}"
    params["id"] = cid
    params["manufacturer"] = manufacturer
    params["model_name"] = model_name

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO hardware_components (id, category, manufacturer, model_name, params_json, is_custom, created_at)
            VALUES (?, ?, ?, ?, ?, 1, datetime('now'))
        """, (cid, category.upper(), manufacturer, model_name, json.dumps(params, ensure_ascii=False)))
        conn.commit()

    return {"status": "created", "id": cid, "manufacturer": manufacturer, "model_name": model_name}
