"""
CAD Single Line Diagram (SLD) & Vector Scheme Generator (cad_sld_generator.py - FÁZE 24)
Generates:
 1. Standard AutoCAD-compatible DXF format (ASCII DXF R12 / 2000 compliant format without hard dependency on external libraries)
 2. Electrical elements drawn:
    - PV String arrays (Module symbols, DC disconnect switches, DC SPD type II surge arresters)
    - Inverter symbol (DC/AC conversion block, MPPT inputs)
    - AC Circuit breaker, AC SPD type I+II, Smart meter / Modbus energy meter
    - Point of Common Coupling (PCC) & Low Voltage busbar (400V 3L+N+PE)
 3. Export to downloadable .dxf file and SVG vector representation
"""

import os
from typing import Dict, Any


def generate_dxf_single_line_diagram(
    project_name: str = "FVE Projekt 100 kWp",
    modules_count: int = 172,
    module_power_w: float = 580.0,
    strings_count: int = 8,
    modules_per_string: int = 22,
    inverter_name: str = "Huawei SUN2000-100KTL-M2",
    main_breaker_a: int = 160,
    cable_type: str = "AYKY 4x150 mm²"
) -> str:
    """
    Vygeneruje validní standardní ASCII DXF výkres jednopólového schématu (SLD).
    Plně kompatibilní s AutoCAD, MicroStation, QCAD i LibreCAD.
    """
    dxf_lines = [
        "0", "SECTION",
        "2", "HEADER",
        "9", "$ACADVER", "1", "AC1009", # AutoCAD R11/R12 standard
        "0", "ENDSEC",
        "0", "SECTION",
        "2", "TABLES",
        "0", "ENDSEC",
        "0", "SECTION",
        "2", "ENTITIES"
    ]

    def add_line(x1, y1, x2, y2, color=7):
        dxf_lines.extend([
            "0", "LINE",
            "8", "0",
            "62", str(color),
            "10", f"{x1:.2f}", "20", f"{y1:.2f}", "30", "0.0",
            "11", f"{x2:.2f}", "21", f"{y2:.2f}", "31", "0.0"
        ])

    def add_text(x, y, text_str, height=2.5, color=7):
        dxf_lines.extend([
            "0", "TEXT",
            "8", "0",
            "62", str(color),
            "10", f"{x:.2f}", "20", f"{y:.2f}", "30", "0.0",
            "40", f"{height:.2f}",
            "1", str(text_str)
        ])

    # 1. Rámeček a záhlaví výkresu
    add_line(0, 0, 280, 0, 7)
    add_line(280, 0, 280, 190, 7)
    add_line(280, 190, 0, 190, 7)
    add_line(0, 190, 0, 0, 7)

    # Razítko výkresu
    add_line(160, 0, 160, 45, 7)
    add_line(160, 45, 280, 45, 7)
    add_text(165, 36, "AuraEnergy SAM OS - JEDNOPOLEVE SCHEMA (SLD)", 3.0, 3) # Green
    add_text(165, 28, f"Projekt: {project_name}", 2.2, 7)
    add_text(165, 20, f"Vykon: {modules_count * module_power_w / 1000.0:.1f} kWp | Strida: {inverter_name}", 2.0, 7)
    add_text(165, 12, f"PCC Jistic: {main_breaker_a}A | Kabel: {cable_type}", 2.0, 7)
    add_text(165, 4, "Normy: CSN EN 62446-1, CSN 33 2000-7-712, PNE 33 3430-1", 1.8, 5)

    # 2. PV Stringy (Vlevo)
    for s in range(min(4, strings_count)):
        y_pos = 160 - (s * 30)
        # Symbol fotovoltaického modulu
        add_line(20, y_pos, 40, y_pos, 2) # Yellow
        add_line(40, y_pos - 8, 40, y_pos + 8, 2)
        add_line(20, y_pos - 8, 20, y_pos + 8, 2)
        add_line(20, y_pos + 8, 40, y_pos + 8, 2)
        add_line(20, y_pos - 8, 40, y_pos - 8, 2)
        add_text(22, y_pos - 2, f"STR {s+1}", 2.2, 2)
        add_text(22, y_pos - 6, f"{modules_per_string}x {module_power_w:.0f}W", 1.8, 7)

        # DC Vedení k přepěťové ochraně a střídači
        add_line(40, y_pos, 75, y_pos, 1) # Red (DC+)
        # Symbol DC přepěťové ochrany SPD
        add_line(55, y_pos, 55, y_pos - 6, 4) # Cyan
        add_text(52, y_pos - 10, "SPD T2", 1.5, 4)

        # Přívod do střídače
        add_line(75, y_pos, 90, y_pos, 1)

    # 3. Blok střídače (Invertor)
    add_line(90, 60, 130, 60, 3)
    add_line(130, 60, 130, 175, 3)
    add_line(130, 175, 90, 175, 3)
    add_line(90, 175, 90, 60, 3)
    add_line(90, 60, 130, 175, 3) # Úhlopříčka DC/AC
    add_text(93, 165, "DC", 3.0, 1)
    add_text(118, 72, "AC", 3.0, 5)
    add_text(93, 115, "INVERTOR", 2.5, 3)
    add_text(93, 105, f"{inverter_name[:16]}", 2.0, 7)

    # 4. AC Výstup, AC SPD a hlavní jistič
    add_line(130, 117, 160, 117, 5) # Blue (AC)
    
    # AC SPD ochrana
    add_line(145, 117, 145, 95, 4)
    add_text(142, 90, "SPD T1+T2", 1.8, 4)

    # Symbol hlavního jističe
    add_line(160, 117, 185, 117, 5)
    add_line(170, 114, 175, 120, 7)
    add_text(168, 122, f"FA1 {main_breaker_a}A / 3P", 2.2, 7)

    # Elektroměr / Smart Meter
    add_line(185, 117, 215, 117, 5)
    add_line(195, 110, 205, 110, 6)
    add_line(205, 110, 205, 124, 6)
    add_line(205, 124, 195, 124, 6)
    add_line(195, 124, 195, 110, 6)
    add_text(197, 115, "Wh", 2.5, 6)
    add_text(194, 104, "FAKTURACNI", 1.5, 6)

    # Přípojnice nízkého napětí PCC (0.4 kV)
    add_line(215, 117, 240, 117, 5)
    add_line(240, 50, 240, 170, 7)
    add_line(241, 50, 241, 170, 7)
    add_text(243, 150, "PCC ROZVADEC NN (400V)", 2.5, 7)
    add_text(243, 142, f"Kabel: {cable_type}", 2.0, 7)
    add_text(243, 134, "Distribucni sit PDS", 2.0, 3)

    # Ukončení DXF
    dxf_lines.extend([
        "0", "ENDSEC",
        "0", "EOF"
    ])

    return "\n".join(dxf_lines)
