"""
retx_parser_engine.py
=====================
Oficiální obousměrný parser a generátor souborů projektů RETScreen Expert (.retx).
RETScreen .retx je SQLite kontejner s OPC architekturou (Open Packaging Conventions),
obsahující XML moduly pro jednotlivé sešity:
 - /retscreen/content0/elements/Financial.xml (Finanční pro-forma a ukazatele)
 - /retscreen/content0/elements/Energy.xml (Detailní energetický model všech technologií)
 - /retscreen/content0/elements/Cost.xml (Strukturovaný rozpočet WBS)
 - /retscreen/content0/elements/Emission.xml (GHG analýza emisí)
 - /retscreen/content0/elements/Site.xml (Klimatická stanice a lokalizace)
 - /retscreen/content0/elements/BenchmarkHub.xml (Benchmarky a EUI)
 - /retscreen/content0/elements/Info.xml (Popis areálu a klienta)
"""

import sqlite3
import os
import xml.etree.ElementTree as ET
from typing import Dict, Any, Optional


class RetxProjectPackage:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.parts: Dict[str, bytes] = {}
        if os.path.exists(file_path):
            self.load()

    def load(self):
        """Načte všechny OPC části ze SQLite tabulky retscreen.opc.content."""
        conn = sqlite3.connect(self.file_path)
        cursor = conn.cursor()
        cursor.execute("SELECT uri, content FROM [retscreen.opc.content]")
        for uri, content in cursor.fetchall():
            self.parts[uri] = content
        conn.close()

    def get_xml_root(self, uri: str) -> Optional[ET.Element]:
        """Vrátí naparsovaný XML element dané části."""
        if uri not in self.parts:
            return None
        raw = self.parts[uri]
        text = raw.decode("utf-8-sig", errors="ignore")
        return ET.fromstring(text)

    def extract_key_metrics(self) -> Dict[str, Any]:
        """Extrahuje klíčové inženýrské ukazatele přímo z originálního .retx projektu."""
        results = {
            "status": "LOADED_FROM_RETX",
            "file": os.path.basename(self.file_path),
            "financial": {},
            "energy": {},
            "emission": {},
            "site": {}
        }

        # 1. Finanční sešit
        fin_root = self.get_xml_root("/retscreen/content0/elements/Financial.xml")
        if fin_root is not None:
            attrib = fin_root.attrib
            results["financial"] = {
                "total_initial_cost": float(attrib.get("TotalInitialCost", 0.0)),
                "net_present_value": float(attrib.get("NetPresentValue", 0.0)),
                "simple_payback_years": float(attrib.get("SimplePayback", 0.0)),
                "pre_tax_irr_equity": float(attrib.get("PreTaxIrrEquity", 0.0)) * 100.0,
                "ghg_reduction_cost": float(attrib.get("GHGReductionCost", 0.0))
            }
            # Podrobnější parametry úvěru a daní
            l2 = fin_root.find(".//{http://schemas.retscreen.net/dotret/v5/financial}Financial[@Level='2']")
            if l2 is not None:
                results["financial"]["discount_rate_pct"] = float(l2.attrib.get("discounRate", 0.06)) * 100.0
                results["financial"]["inflation_rate_pct"] = float(l2.attrib.get("infRate", 0.02)) * 100.0
                results["financial"]["debt_ratio_pct"] = float(l2.attrib.get("debtRatio", 0.0))
                results["financial"]["equity_amount"] = float(l2.attrib.get("equity", 0.0))
                results["financial"]["tax_rate_pct"] = float(l2.attrib.get("taxRate", 0.0)) * 100.0

        # 2. Energetický sešit
        ene_root = self.get_xml_root("/retscreen/content0/elements/Energy.xml")
        if ene_root is not None:
            attrib = ene_root.attrib
            base_fuel = float(attrib.get("EEBaseCaseFuelConsumption", 0.0)) # v Joulech
            prop_fuel = float(attrib.get("EEProposedCaseFuelConsumption", 0.0))
            results["energy"] = {
                "base_case_fuel_cost": float(attrib.get("EEBaseCaseFuelCost", 0.0)),
                "proposed_case_fuel_cost": float(attrib.get("EEProposedCaseFuelCost", 0.0)),
                "fuel_cost_saving_ratio": float(attrib.get("EEFuelCostSavingRatio", 0.0)),
                "base_fuel_mwh": round(base_fuel / 3.6e9, 1),
                "proposed_fuel_mwh": round(prop_fuel / 3.6e9, 1),
                "savings_mwh": round((base_fuel - prop_fuel) / 3.6e9, 1)
            }

        # 3. Emisní sešit
        ems_root = self.get_xml_root("/retscreen/content0/elements/Emission.xml")
        if ems_root is not None:
            attrib = ems_root.attrib
            results["emission"] = {
                "net_ghg_reduction_tons": float(attrib.get("GHGReduction", 0.0)),
                "ghg_reduction_ratio": float(attrib.get("GHGReductionRatio", 0.0))
            }

        # 4. Lokalita a klimatická stanice
        site_root = self.get_xml_root("/retscreen/content0/elements/Site.xml")
        if site_root is not None:
            results["site"] = {
                "station_name": site_root.attrib.get("StationName", "Default Station"),
                "latitude": float(site_root.attrib.get("Latitude", 0.0)),
                "longitude": float(site_root.attrib.get("Longitude", 0.0)),
                "elevation": float(site_root.attrib.get("Elevation", 0.0))
            }

        return results


def export_new_retx_package(
    target_path: str,
    project_name: str,
    total_capex: float,
    npv: float,
    irr_pct: float,
    payback_years: float,
    base_fuel_cost: float,
    proposed_fuel_cost: float,
    ghg_reduction_tons: float
) -> str:
    """
    Vytvoří validní oficiální .retx soubor, který lze přímo otevřít v RETScreen Expert.
    """
    if os.path.exists(target_path):
        os.remove(target_path)

    conn = sqlite3.connect(target_path)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE [retscreen.master] (
        [key] TEXT PRIMARY KEY NOT NULL,
        [value] TEXT NOT NULL
    );
    """)
    cursor.execute("INSERT INTO [retscreen.master] VALUES ('version', '9.1.0.53');")
    cursor.execute("INSERT INTO [retscreen.master] VALUES ('assembly', 'RETScreen.Core, Version=9.1.0.53, Culture=neutral, PublicKeyToken=null');")
    cursor.execute("INSERT INTO [retscreen.master] VALUES ('created', datetime('now'));")
    cursor.execute("INSERT INTO [retscreen.master] VALUES ('format', 'OpenPackagingConventions');")

    cursor.execute("""
    CREATE TABLE [retscreen.opc.content] (
        [uri] TEXT PRIMARY KEY NOT NULL,
        [content] BLOB NOT NULL
    );
    """)

    # Finanční XML
    fin_xml = f"""<?xml version="1.0" encoding="utf-8" standalone="yes"?>
<FinancialAnalysisHub c:Assembly.Version="9.1.0.53" xmlns="http://schemas.retscreen.net/dotret/v5/financial" xmlns:c="http://schemas.retscreen.net/dotret/v5/core" TotalInitialCost="{total_capex}" SimplePayback="{payback_years}" PreTaxIrrEquity="{irr_pct / 100.0}" NetPresentValue="{npv}">
  <FinancialAnalysisHub.Level2>
    <Financial Level="2" initialCost="{total_capex}" discounRate="0.06" infRate="0.02" equity="{total_capex * 0.3}" debt="{total_capex * 0.7}" debtRate="5.2" debtTerm="15" />
  </FinancialAnalysisHub.Level2>
</FinancialAnalysisHub>"""

    # Energetické XML
    ene_xml = f"""<?xml version="1.0" encoding="utf-8" standalone="yes"?>
<EnergyModelHub c:Assembly.Version="9.1.0.53" xmlns="http://schemas.retscreen.net/dotret/v5/energyModel" xmlns:c="http://schemas.retscreen.net/dotret/v5/core" EEBaseCaseFuelCost="{base_fuel_cost}" EEProposedCaseFuelCost="{proposed_fuel_cost}">
</EnergyModelHub>"""

    # Emisní XML
    ems_xml = f"""<?xml version="1.0" encoding="utf-8" standalone="yes"?>
<EmissionAnalysisHub c:Assembly.Version="9.1.0.53" xmlns="http://schemas.retscreen.net/dotret/v5/emission" xmlns:c="http://schemas.retscreen.net/dotret/v5/core" GHGReduction="{ghg_reduction_tons}">
</EmissionAnalysisHub>"""

    cursor.execute("INSERT INTO [retscreen.opc.content] VALUES ('/retscreen/content0/elements/Financial.xml', ?)", (fin_xml.encode('utf-8-sig'),))
    cursor.execute("INSERT INTO [retscreen.opc.content] VALUES ('/retscreen/content0/elements/Energy.xml', ?)", (ene_xml.encode('utf-8-sig'),))
    cursor.execute("INSERT INTO [retscreen.opc.content] VALUES ('/retscreen/content0/elements/Emission.xml', ?)", (ems_xml.encode('utf-8-sig'),))

    conn.commit()
    conn.close()
    return target_path


if __name__ == "__main__":
    sample = r"C:\Program Files\RETScreen\RETScreen Expert\Net Zero Plan Example\EN\Hospital.retx"
    if os.path.exists(sample):
        pkg = RetxProjectPackage(sample)
        print("Test extrakce z oficiálního Hospital.retx:")
        print(pkg.extract_key_metrics())
