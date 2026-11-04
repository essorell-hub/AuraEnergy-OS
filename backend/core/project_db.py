"""
Project Management and Database persistence module for AuraEnergy OS (KROK 7).
Uses lightweight SQLite for local project storage, loading, and versioning.
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "projects.db")


def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                location TEXT NOT NULL,
                facility_type TEXT,
                system_size_kw REAL NOT NULL,
                capex_total_czk REAL NOT NULL,
                params_json TEXT NOT NULL,
                results_json TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        conn.commit()


def list_projects() -> List[Dict[str, Any]]:
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, location, facility_type, system_size_kw, capex_total_czk, created_at, updated_at FROM projects ORDER BY updated_at DESC")
        rows = cursor.fetchall()
        return [dict(r) for r in rows]


def get_project(project_id: str) -> Optional[Dict[str, Any]]:
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
        row = cursor.fetchone()
        if not row:
            return None
        d = dict(row)
        d["params"] = json.loads(d["params_json"]) if d["params_json"] else {}
        d["results"] = json.loads(d["results_json"]) if d["results_json"] else None
        return d


def save_project(project_data: Dict[str, Any]) -> Dict[str, Any]:
    init_db()
    pid = project_data.get("id") or f"proj_{int(datetime.now().timestamp())}"
    name = project_data.get("name", "Nový FVE Projekt")
    location = project_data.get("location", "Praha, ČR")
    facility_type = project_data.get("facility_type", "COMMERCIAL_ROOFTOP")
    system_size_kw = float(project_data.get("system_size_kw", 100.0))
    capex_czk = float(project_data.get("capex_total_czk", 2200000.0))
    params = project_data.get("params", project_data)
    results = project_data.get("results", {})
    now_str = datetime.now().isoformat()

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO projects (id, name, location, facility_type, system_size_kw, capex_total_czk, params_json, results_json, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                name=excluded.name,
                location=excluded.location,
                facility_type=excluded.facility_type,
                system_size_kw=excluded.system_size_kw,
                capex_total_czk=excluded.capex_total_czk,
                params_json=excluded.params_json,
                results_json=excluded.results_json,
                updated_at=excluded.updated_at
        """, (
            pid, name, location, facility_type, system_size_kw, capex_czk,
            json.dumps(params, ensure_ascii=False),
            json.dumps(results, ensure_ascii=False) if results else None,
            project_data.get("created_at", now_str),
            now_str
        ))
        conn.commit()

    return {"status": "saved", "id": pid, "updated_at": now_str}


def delete_project(project_id: str) -> bool:
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM projects WHERE id = ?", (project_id,))
        conn.commit()
        return cursor.rowcount > 0
