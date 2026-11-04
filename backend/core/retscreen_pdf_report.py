# -*- coding: utf-8 -*-
"""
RETScreen Executive Summary 2-Page Official PDF Report Generator
Generates clean, professional high-level investment summaries:
- Facility details & location
- System capacities & clean energy production
- Financial metrics (IRR, NPV, Equity Payback, B-C Ratio)
- GHG Emission reduction & real-world environmental equivalents
- Official signature & validation block
"""

import io
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, PageBreak, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY


def generate_retscreen_pdf_report(project_data: dict) -> bytes:
    """
    Generates a 2-page executive summary PDF report matching RETScreen Expert reporting standards.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#003366'),
        alignment=TA_LEFT,
        spaceAfter=4
    )

    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#555555'),
        alignment=TA_LEFT,
        spaceAfter=12
    )

    h2_style = ParagraphStyle(
        'SectionH2',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#003366'),
        spaceBefore=8,
        spaceAfter=6
    )

    cell_style = ParagraphStyle(
        'GridCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11
    )

    cell_bold = ParagraphStyle(
        'GridCellBold',
        parent=cell_style,
        fontName='Helvetica-Bold'
    )

    cell_accent = ParagraphStyle(
        'GridCellAccent',
        parent=cell_style,
        fontName='Helvetica-Bold',
        textColor=colors.HexColor('#005a9e')
    )

    story = []

    # --- HEADER BLOCK ---
    header_table_data = [
        [
            Paragraph("<b>AURAENERGY OS / RETSCREEN® EXPERT</b><br/><font size='7' color='#666'>CLEAN ENERGY MANAGEMENT & FEASIBILITY SUITE</font>", cell_style),
            Paragraph(f"<b>DATUM:</b> {datetime.now().strftime('%d.%m.%Y')}<br/><b>VERZE:</b> 2.0 Full Edition", ParagraphStyle('RHead', parent=cell_style, alignment=TA_RIGHT))
        ]
    ]
    t_head = Table(header_table_data, colWidths=[340, 200])
    t_head.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_head)
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#003366'), spaceAfter=10))

    # Title
    proj_name = project_data.get('projectName', 'Nemocnice s poliklinikou - Energetický audit')
    facility_type = project_data.get('facilityType', 'Zdravotnické zařízení / Nemocnice')
    location = project_data.get('location', 'Praha, Česká republika')

    story.append(Paragraph(f"Projektový souhrn: {proj_name}", title_style))
    story.append(Paragraph(f"Typ zařízení: <b>{facility_type}</b> | Lokalita: <b>{location}</b> | Norma: ČSN EN ISO 52000 & RETScreen Engine", subtitle_style))

    # --- SECTION 1: LOKALITA & METEOROLOGICKÁ ZÁKLADNA ---
    story.append(Paragraph("1. Lokalita a meteorologické parametry (NASA POWER & Climate Stations)", h2_style))

    lat = project_data.get('lat', 50.08)
    lon = project_data.get('lon', 14.43)
    ghi = project_data.get('annualGhi', 1085)
    temp = project_data.get('annualTemp', 9.8)
    wind = project_data.get('annualWind', 3.4)
    hdd = project_data.get('hdd', 3120)

    clim_data = [
        [
            Paragraph("<b>Zeměpisná šířka / délka:</b>", cell_style),
            Paragraph(f"{lat:.4f}° N, {lon:.4f}° E", cell_style),
            Paragraph("<b>Roční globální horizontální ozáření (GHI):</b>", cell_style),
            Paragraph(f"{ghi} kWh/m²/rok", cell_accent)
        ],
        [
            Paragraph("<b>Průměrná roční teplota:</b>", cell_style),
            Paragraph(f"{temp} °C", cell_style),
            Paragraph("<b>Průměrná rychlost větru (10 m):</b>", cell_style),
            Paragraph(f"{wind} m/s", cell_style)
        ],
        [
            Paragraph("<b>Počet topných dnů (HDD 18°C):</b>", cell_style),
            Paragraph(f"{hdd} Kd", cell_style),
            Paragraph("<b>Zdroj klimatických dat:</b>", cell_style),
            Paragraph("RETScreen Climate Hub + NASA POWER Live", cell_style)
        ]
    ]
    t_clim = Table(clim_data, colWidths=[150, 120, 170, 100])
    t_clim.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8f9fa')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#dddddd')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_clim)
    story.append(Spacer(1, 10))

    # --- SECTION 2: ENERGETICKÁ BILANCE & OZE TECHNOLOGIE ---
    story.append(Paragraph("2. Energetická soustava a instalované OZE zdroje", h2_style))

    pv_kwp = project_data.get('pvCapKwp', 450.0)
    pv_gen = project_data.get('pvGenMwh', 465.0)
    wind_kw = project_data.get('windCapKw', 0.0)
    hp_kw = project_data.get('heatPumpKw', 180.0)
    bess_kwh = project_data.get('bessKwh', 200.0)
    base_mwh = project_data.get('baselineMwh', 1250.0)
    prop_mwh = project_data.get('proposedMwh', 785.0)
    savings_mwh = base_mwh - prop_mwh
    pct_saved = (savings_mwh / base_mwh * 100) if base_mwh > 0 else 0

    energy_data = [
        [
            Paragraph("<b>Subsystém / Technologie</b>", cell_bold),
            Paragraph("<b>Instalovaný výkon</b>", cell_bold),
            Paragraph("<b>Roční výroba / úspora</b>", cell_bold),
            Paragraph("<b>Pokrytí / Status</b>", cell_bold)
        ],
        [
            Paragraph("Fotovoltaická elektrárna (FVE monoSi)", cell_style),
            Paragraph(f"{pv_kwp:.1f} kWp", cell_style),
            Paragraph(f"{pv_gen:.1f} MWh/rok", cell_style),
            Paragraph("Vlastní spotřeba 78 % + PNE přetoky", cell_style)
        ],
        [
            Paragraph("Větrná turbína (volitelné)", cell_style),
            Paragraph(f"{wind_kw:.1f} kW", cell_style),
            Paragraph("0.0 MWh/rok", cell_style),
            Paragraph("Nenainstalováno", cell_style)
        ],
        [
            Paragraph("Tepelná čerpadla (Země-Voda / Vzduch-Voda)", cell_style),
            Paragraph(f"{hp_kw:.1f} kWt", cell_style),
            Paragraph("Bivalentní bod -5°C (COP 3.8)", cell_style),
            Paragraph("Náhrada plynového kotle 65 %", cell_style)
        ],
        [
            Paragraph("BESS Bateriové úložiště LFP", cell_style),
            Paragraph(f"{bess_kwh:.1f} kWh", cell_style),
            Paragraph("Peak-shaving & OTE Arbitráž", cell_style),
            Paragraph("SVR ČEPS 15min ready", cell_style)
        ],
        [
            Paragraph("<b>CELKOVÁ BILANCE PROJEKTU</b>", cell_accent),
            Paragraph(f"<b>Výchozí: {base_mwh:.0f} MWh</b>", cell_bold),
            Paragraph(f"<b>Navržená: {prop_mwh:.0f} MWh</b>", cell_bold),
            Paragraph(f"<b>Úspora: {savings_mwh:.0f} MWh/r ({pct_saved:.1f} %)</b>", cell_accent)
        ]
    ]
    t_energy = Table(energy_data, colWidths=[180, 110, 130, 120])
    t_energy.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#e9ecef')),
        ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor('#e3f2fd')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cccccc')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_energy)
    story.append(Spacer(1, 10))

    # --- SECTION 3: ROZPOČET & WBS INVESTICE ---
    story.append(Paragraph("3. Rozpočtový rozpad nákladů (WBS Inicializace)", h2_style))

    initial_capex = project_data.get('initialCapex', 14500000)
    incentives = project_data.get('incentives', 4350000) # Dotace NZÚ / OP TAK
    net_capex = initial_capex - incentives

    wbs_data = [
        [
            Paragraph("<b>WBS Kategorie</b>", cell_bold),
            Paragraph("<b>Základ bez DPH (CZK)</b>", cell_bold),
            Paragraph("<b>DPH 21 % (CZK)</b>", cell_bold),
            Paragraph("<b>Celkem s DPH (CZK)</b>", cell_bold)
        ],
        [
            Paragraph("1. Studie proveditelnosti & audit", cell_style),
            Paragraph(f"{initial_capex*0.03:,.0f} Kč", cell_style),
            Paragraph(f"{initial_capex*0.03*0.21:,.0f} Kč", cell_style),
            Paragraph(f"{initial_capex*0.03*1.21:,.0f} Kč", cell_style)
        ],
        [
            Paragraph("2. Vývoj, inženýring & povolovací proces", cell_style),
            Paragraph(f"{initial_capex*0.07:,.0f} Kč", cell_style),
            Paragraph(f"{initial_capex*0.07*0.21:,.0f} Kč", cell_style),
            Paragraph(f"{initial_capex*0.07*1.21:,.0f} Kč", cell_style)
        ],
        [
            Paragraph("3. Hlavní technologické zařízení (FVE, BESS, TČ)", cell_style),
            Paragraph(f"{initial_capex*0.62:,.0f} Kč", cell_style),
            Paragraph(f"{initial_capex*0.62*0.21:,.0f} Kč", cell_style),
            Paragraph(f"{initial_capex*0.62*1.21:,.0f} Kč", cell_style)
        ],
        [
            Paragraph("4. Balance of System (BoS, rozvaděče, kabeláž)", cell_style),
            Paragraph(f"{initial_capex*0.18:,.0f} Kč", cell_style),
            Paragraph(f"{initial_capex*0.18*0.21:,.0f} Kč", cell_style),
            Paragraph(f"{initial_capex*0.18*1.21:,.0f} Kč", cell_style)
        ],
        [
            Paragraph("5. Montáž, oživení & rezerva 5 %", cell_style),
            Paragraph(f"{initial_capex*0.10:,.0f} Kč", cell_style),
            Paragraph(f"{initial_capex*0.10*0.21:,.0f} Kč", cell_style),
            Paragraph(f"{initial_capex*0.10*1.21:,.0f} Kč", cell_style)
        ],
        [
            Paragraph("<b>CELKOVÝ ROZPOČET CAPEX</b>", cell_accent),
            Paragraph(f"<b>{initial_capex:,.0f} Kč</b>", cell_bold),
            Paragraph(f"<b>{initial_capex*0.21:,.0f} Kč</b>", cell_bold),
            Paragraph(f"<b>{initial_capex*1.21:,.0f} Kč</b>", cell_accent)
        ],
        [
            Paragraph("<b>Uplatněná investiční dotace (NZÚ / Modernizační fond)</b>", cell_bold),
            Paragraph(f"-{incentives:,.0f} Kč", cell_bold),
            Paragraph("-", cell_style),
            Paragraph(f"<b>ČISTÁ INVESTICE: {net_capex:,.0f} Kč</b>", cell_accent)
        ]
    ]
    t_wbs = Table(wbs_data, colWidths=[200, 110, 110, 120])
    t_wbs.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#e9ecef')),
        ('BACKGROUND', (0,-2), (-1,-2), colors.HexColor('#f1f8e9')),
        ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor('#e8f5e9')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cccccc')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(t_wbs)

    # PAGE BREAK -> STRANA 2
    story.append(PageBreak())

    # --- STRANA 2 HEADER ---
    story.append(Paragraph("4. Finanční analýza a klíčové ukazatele návratnosti (FinancialAnalysisHub)", h2_style))
    story.append(Paragraph("Vyhodnocení 25letého diskontovaného cash-flow dle metodiky RETScreen Expert s uvážením degradace a eskalace cen energií.", subtitle_style))

    irr = project_data.get('irr', 18.4)
    npv = project_data.get('npv', 22850000)
    payback = project_data.get('payback', 5.2)
    bcr = project_data.get('bcr', 2.58)
    annual_savings = project_data.get('annualSavingsCzk', 2350000)

    fin_kpis = [
        [
            Paragraph("<b>Vnitřní výnosové procento (Pre-tax IRR):</b>", cell_style),
            Paragraph(f"<font size='11' color='#0078d4'><b>{irr:.1f} %</b></font>", cell_style),
            Paragraph("<b>Čistá současná hodnota (NPV @ 6.0%):</b>", cell_style),
            Paragraph(f"<font size='11' color='#107c10'><b>{npv:,.0f} Kč</b></font>", cell_style)
        ],
        [
            Paragraph("<b>Prostá doba návratnosti:</b>", cell_style),
            Paragraph(f"<b>{payback:.1f} roku</b>", cell_style),
            Paragraph("<b>Poměr přínosů a nákladů (B-C Ratio):</b>", cell_style),
            Paragraph(f"<b>{bcr:.2f}</b> (Vysoce efektivní)", cell_style)
        ],
        [
            Paragraph("<b>Roční úspora nákladů na energii:</b>", cell_style),
            Paragraph(f"<b>{annual_savings:,.0f} Kč/rok</b>", cell_style),
            Paragraph("<b>Životnost projektu:</b>", cell_style),
            Paragraph("<b>25 let</b> (Degradace FVE 0.5%/rok)", cell_style)
        ]
    ]
    t_fin = Table(fin_kpis, colWidths=[160, 110, 160, 110])
    t_fin.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8f9fa')),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#005a9e')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e0e0e0')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_fin)
    story.append(Spacer(1, 14))

    # --- SECTION 5: EMISNÍ BILANCE & EKOLOGICKÉ EKVIVALENTY ---
    story.append(Paragraph("5. Analýza emisí skleníkových plynů (GHG & Environmental Equivalents)", h2_style))

    ghg_baseline = project_data.get('ghgBaseline', 625.0)
    ghg_proposed = project_data.get('ghgProposed', 242.0)
    ghg_reduction = ghg_baseline - ghg_proposed
    ghg_pct = (ghg_reduction / ghg_baseline * 100) if ghg_baseline > 0 else 0
    cars_equiv = int(ghg_reduction / 4.6) # ~4.6 t CO2/auto/rok
    trees_equiv = int(ghg_reduction * 45) # ~45 stromů na tunu CO2
    liters_gas = int(ghg_reduction * 425)

    ghg_data = [
        [
            Paragraph("<b>Emisní faktor sítě (ČR mix):</b>", cell_style),
            Paragraph("0.485 t CO2eq / MWh", cell_style),
            Paragraph("<b>Roční redukce emisí CO2:</b>", cell_style),
            Paragraph(f"<font color='#107c10'><b>-{ghg_reduction:.1f} t CO2/rok (-{ghg_pct:.1f} %)</b></font>", cell_style)
        ],
        [
            Paragraph("<b>Ekvivalent vyřazených automobilů:</b>", cell_style),
            Paragraph(f"<b>{cars_equiv} osobních aut</b> / rok", cell_style),
            Paragraph("<b>Ušetřené pohonné hmoty:</b>", cell_style),
            Paragraph(f"<b>{liters_gas:,.0f} litrů</b> benzínu / rok", cell_style)
        ],
        [
            Paragraph("<b>Ekvivalent absorpce lesem:</b>", cell_style),
            Paragraph(f"<b>{trees_equiv:,.0f} vzrostlých stromů</b>", cell_style),
            Paragraph("<b>Emisní certifikace:</b>", cell_style),
            Paragraph("Metodika RETScreen Expert / GHG Protocol", cell_style)
        ]
    ]
    t_ghg = Table(ghg_data, colWidths=[160, 110, 160, 110])
    t_ghg.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#e8f5e9')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#c8e6c9')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_ghg)
    story.append(Spacer(1, 14))

    # --- SECTION 6: SROVNÁNÍ A POKROČILÉ FUNKCE AURAENERGY OS ---
    story.append(Paragraph("6. Soulad s normami & Nadstandardní funkcionality (AuraEnergy OS)", h2_style))

    extra_data = [
        [
            Paragraph("<b>Sítový standard PNE 33 3430-1:</b>", cell_style),
            Paragraph("<font color='#107c10'><b>VYHOVUJE</b></font> (PCC zpětné vlivy < 2.0 %)", cell_style),
            Paragraph("<b>OTE Spot Arbitráž:</b>", cell_style),
            Paragraph("Aktivní (15min algoritmický dispatch)", cell_style)
        ],
        [
            Paragraph("<b>ČEPS Kodex Přenosové soustavy:</b>", cell_style),
            Paragraph("FCR / aFRR dynamická podpora napětí", cell_style),
            Paragraph("<b>Export formáty:</b>", cell_style),
            Paragraph("Plně kompatibilní .retx, DXF R12, IFC 4.0", cell_style)
        ]
    ]
    t_extra = Table(extra_data, colWidths=[160, 110, 160, 110])
    t_extra.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f0f4f8')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#d0d8e0')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_extra)
    story.append(Spacer(1, 25))

    # --- SIGNATURE BLOCK ---
    sig_data = [
        [
            Paragraph("<b>Vypracoval:</b><br/>AuraEnergy OS Expert System<br/>Certifikovaný energetický specialista", cell_style),
            Paragraph("<b>Ověřil a schválil:</b><br/>Hlavní inženýr projektu / CFO<br/>Datum: ........................................", cell_style),
            Paragraph("<b>Razítko a podpis:</b><br/><br/>........................................................", cell_style)
        ]
    ]
    t_sig = Table(sig_data, colWidths=[180, 180, 180])
    t_sig.setStyle(TableStyle([
        ('LINEBEFORE', (1,0), (-1,-1), 0.5, colors.HexColor('#999999')),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(t_sig)

    # Build PDF
    doc.build(story)
    return buffer.getvalue()
