"""
retscreen_master_sync.py
========================
Automatický synchronizační modul, který přímo čte oficiální databázi
RETScreen Expert z lokální instalace:
 "C:\Program Files\RETScreen\RETScreen Expert\Data\product.sqlite"
a importuje přes 5 500 certifikovaných fotovoltaických panelů (monoSi, polySi),
1 385 větrných turbín a přes 3 200 tepelných čerpadel do naší lokální databáze AuraEnergy OS.
"""

import sqlite3
import os
import json

RETSCREEN_DB = r"C:\Program Files\RETScreen\RETScreen Expert\Data\product.sqlite"
LOCAL_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "projects.db")


def sync_from_official_retscreen():
    if not os.path.exists(RETSCREEN_DB):
        print(f"[RETScreen Sync] Databáze na cestě {RETSCREEN_DB} nebyla nalezena.")
        return False

    print("[RETScreen Sync] Připojuji se k oficiální RETScreen Expert databázi...")
    ret_conn = sqlite3.connect(RETSCREEN_DB)
    ret_cursor = ret_conn.cursor()

    local_conn = sqlite3.connect(LOCAL_DB)
    local_cursor = local_conn.cursor()

    local_cursor.execute("""
    CREATE TABLE IF NOT EXISTS retscreen_official_products (
        product_id INTEGER PRIMARY KEY,
        category TEXT NOT NULL,
        manufacturer TEXT NOT NULL,
        model_name TEXT NOT NULL,
        capacity_val REAL,
        capacity_unit TEXT,
        imported_at TEXT DEFAULT (datetime('now'))
    )
    """)

    # 1. Fotovoltaické panely (Kategorie 81 = monoSi, 82 = polySi)
    ret_cursor.execute("""
    SELECT p.ProductID, pc.Caption, m.ManufacturerName, p.ProductCaption, p.CapacityValue, p.CapacityUnit
    FROM Product p
    JOIN ProductCategory pc ON pc.ProductCategoryID = p.ProductCategoryID
    JOIN ProductManufacturer m ON m.ManufacturerID = p.ManufacturerID
    WHERE p.ProductCategoryID IN (81, 82)
    """)
    pv_rows = ret_cursor.fetchall()

    for r in pv_rows:
        pid, cat_raw, mfg, model, cap, unit = r
        cat = "PV_MODULE_MONO" if "mono" in cat_raw.lower() else "PV_MODULE_POLY"
        clean_model = model.replace("{{monoSi}} - ", "").replace("{{polySi}} - ", "").replace("{{xWattSymbol}}", "W").strip()
        local_cursor.execute("""
        INSERT OR REPLACE INTO retscreen_official_products
        (product_id, category, manufacturer, model_name, capacity_val, capacity_unit, imported_at)
        VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
        """, (pid, cat, mfg, clean_model, cap, "W"))

    # 2. Větrné turbíny (Kategorie 88)
    ret_cursor.execute("""
    SELECT p.ProductID, m.ManufacturerName, p.ProductCaption, p.CapacityValue, p.CapacityUnit
    FROM Product p
    JOIN ProductManufacturer m ON m.ManufacturerID = p.ManufacturerID
    WHERE p.ProductCategoryID = 88
    """)
    wind_rows = ret_cursor.fetchall()

    for r in wind_rows:
        pid, mfg, model, cap, unit = r
        clean_model = model.replace("{{xMetreSymbol}}", "m").replace("{{xKiloWattSymbol}}", "kW").strip()
        local_cursor.execute("""
        INSERT OR REPLACE INTO retscreen_official_products
        (product_id, category, manufacturer, model_name, capacity_val, capacity_unit, imported_at)
        VALUES (?, 'WIND_TURBINE', ?, ?, ?, ?, datetime('now'))
        """, (pid, mfg, clean_model, cap, "kW"))

    # 3. Tepelná čerpadla (Kategorie 50, 13, 49, 12)
    ret_cursor.execute("""
    SELECT p.ProductID, pc.Caption, m.ManufacturerName, p.ProductCaption, p.CapacityValue, p.CapacityUnit
    FROM Product p
    JOIN ProductCategory pc ON pc.ProductCategoryID = p.ProductCategoryID
    JOIN ProductManufacturer m ON m.ManufacturerID = p.ManufacturerID
    WHERE p.ProductCategoryID IN (50, 13, 49, 12)
    """)
    hp_rows = ret_cursor.fetchall()

    for r in hp_rows:
        pid, cat_raw, mfg, model, cap, unit = r
        cat = "HEAT_PUMP_GROUND" if "ground" in cat_raw.lower() else "HEAT_PUMP_AIR"
        local_cursor.execute("""
        INSERT OR REPLACE INTO retscreen_official_products
        (product_id, category, manufacturer, model_name, capacity_val, capacity_unit, imported_at)
        VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
        """, (pid, cat, mfg, model, cap, "kW"))

    local_conn.commit()
    ret_conn.close()
    local_conn.close()

    total_imported = len(pv_rows) + len(wind_rows) + len(hp_rows)
    print(f"[RETScreen Sync] Hotovo! Úspěšně importováno {total_imported} originálních certifikovaných produktů:")
    print(f" - Fotovoltaické panely: {len(pv_rows)} modelů")
    print(f" - Větrné turbíny: {len(wind_rows)} modelů")
    print(f" - Tepelná čerpadla: {len(hp_rows)} modelů")
    return True


if __name__ == "__main__":
    sync_from_official_retscreen()
