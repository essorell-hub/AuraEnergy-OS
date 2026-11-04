"""
retscreen_climate_stations.py
=============================
Čte 11 242 oficiálních klimatických stanic z:
 C:\Program Files\RETScreen\RETScreen Expert\Data\climateStations.xml
a umožňuje okamžité vyhledávání stanice dle názvu města nebo státu.
"""

import xml.etree.ElementTree as ET
import os
from typing import List, Dict, Any

STATIONS_XML = r"C:\Program Files\RETScreen\RETScreen Expert\Data\climateStations.xml"

_CACHED_STATIONS: List[Dict[str, Any]] = []


def get_all_retscreen_stations() -> List[Dict[str, Any]]:
    global _CACHED_STATIONS
    if _CACHED_STATIONS:
        return _CACHED_STATIONS

    if not os.path.exists(STATIONS_XML):
        return []

    try:
        tree = ET.parse(STATIONS_XML)
        root = tree.getroot()
        all_s = root.findall('.//s')
        
        results = []
        for s in all_s:
            attrib = s.attrib
            results.append({
                "id": attrib.get("id"),
                "name": attrib.get("name", "Unknown Station"),
                "country_code": attrib.get("c", ""),
                "lat": float(attrib.get("lat", 0.0)),
                "lon": float(attrib.get("lon", 0.0))
            })
        _CACHED_STATIONS = results
        return results
    except Exception as e:
        print("[Stations] Chyba čtení XML:", e)
        return []


def search_climate_stations(query: str, limit: int = 15) -> List[Dict[str, Any]]:
    """Vyhledá stanici podle názvu."""
    stations = get_all_retscreen_stations()
    q = query.lower().strip()
    matches = [s for s in stations if q in s["name"].lower()]
    return matches[:limit]


if __name__ == "__main__":
    st = get_all_retscreen_stations()
    print(f"Načteno celkem {len(st)} stanic.")
    czech = [s for s in st if "prague" in s["name"].lower() or "praha" in s["name"].lower() or "brno" in s["name"].lower()]
    print("Vzorek v ČR:", czech[:5])
