/**
 * AuraEnergy OS - User Onboarding, Interactive Tooltips and Glossary Guide (FÁZE 18)
 */

const GLOSSARY_TOOLTIPS = {
  "ghi": {
    "title": "GHI (Global Horizontal Irradiation)",
    "desc": "Globální horizontální záření vyjadřuje celkovou energii dopadající na vodorovný povrch (v kWh/m²/rok). V ČR se obvykle pohybuje mezi 1 000 a 1 180 kWh/m²/rok.",
    "benchmark": "Benchmark ČR: 1 120 kWh/m²/rok"
  },
  "poa": {
    "title": "POA (Plane of Array Irradiance)",
    "desc": "Osvit přepočtený Perezovým transpozičním modelem přímo do skloněné a orientované roviny fotovoltaických panelů.",
    "benchmark": "Obvyklý nárůst oproti GHI: +12 % až +18 %"
  },
  "noct": {
    "title": "NOCT (Nominal Operating Cell Temperature)",
    "desc": "Jmenovitá provozní teplota FV článku při osvitu 800 W/m², teplotě vzduchu 20 °C a rychlosti větru 1 m/s. Čím nižší NOCT, tím menší ztráty v létě.",
    "benchmark": "Moderní TOPCon / HJT: 42 - 45 °C"
  },
  "pr": {
    "title": "PR (Performance Ratio) dle IEC 61724",
    "desc": "Výkonnostní poměr solární elektrárny. Udává podíl skutečně dodané AC elektřiny vůči teoretickému ideálnímu výnosu bez jakýchkoliv ztrát.",
    "benchmark": "Průmyslový standard: 80.0 % až 85.5 %"
  },
  "cuf": {
    "title": "CUF (Capacity Utilization Factor)",
    "desc": "Faktor využití instalovaného výkonu za celý rok (8 760 hodin). Vyjadřuje poměr reálné roční výroby k teoretickému chodu na 100 % výkon 24/7.",
    "benchmark": "FVE v ČR: 11.5 % až 14.5 %"
  },
  "lcoe": {
    "title": "LCOE (Levelized Cost of Energy)",
    "desc": "Zlevněné měrné náklady na výrobu 1 kWh/MWh elektřiny za celou 25letou životnost projektu. Zahrnuje CAPEX, OPEX i diskontní sazbu očištěnou o inflaci (Fisherova rovnice).",
    "benchmark": "Komerční FVE: 1.10 až 1.60 Kč/kWh (45 - 65 €/MWh)"
  },
  "delta_u": {
    "title": "ΔU % (Nárůst napětí v bodě PCC)",
    "desc": "Procentuální zvýšení napětí v předávacím místě připojení k distribuční soustavě (PDS) způsobené dodávkou činného výkonu FVE dle normy PNE 33 3430-1.",
    "benchmark": "Limit bez vyvolaných investic: ΔU ≤ 2.0 %"
  },
  "qu_mode": {
    "title": "Regulace jalového výkonu Q(U)",
    "desc": "Autonomní funkce střídače, který při zvýšení síťového napětí začne induktivně odebírat jalový výkon, čímž lokálně srazí napětí zpět do normy.",
    "benchmark": "Pásmo aktivace: 2.0 % < ΔU ≤ 3.0 %"
  },
  "dscr": {
    "title": "DSCR (Debt Service Coverage Ratio)",
    "desc": "Ukazatel krytí bankovní dluhové služby. Poměr provozního cash-flow k roční splátce úvěru.",
    "benchmark": "Požadavek financujících bank: DSCR ≥ 1.25"
  },
  "nzu": {
    "title": "Nová zelená úsporám (NZÚ)",
    "desc": "Státní dotační program pro rodinné domy financovaný z Modernizačního fondu. Poskytuje přímý odečet z pořizovací ceny FVE, baterie a nabíjecího Wallboxu.",
    "benchmark": "Typická dotace: 160 000 až 200 000 Kč"
  }
};

function showTooltipModal(termKey) {
  const item = GLOSSARY_TOOLTIPS[termKey];
  if (!item) return;

  const modal = document.getElementById('tooltip-modal');
  document.getElementById('tt-title').innerText = item.title;
  document.getElementById('tt-desc').innerText = item.desc;
  document.getElementById('tt-benchmark').innerText = item.benchmark;
  modal.classList.remove('hidden');
}

function closeTooltipModal() {
  document.getElementById('tooltip-modal').classList.add('hidden');
}

function startGuidedTour() {
  const steps = [
    { title: "Vítejte v AuraEnergy OS", text: "Váš operační a rozhodovací systém pro čistou energetiku. Provede vás kompletním návrhem, síťovým posouzením i bankovním modelem." },
    { title: "1. Krok: Segment & OZE", text: "Zde zvolte, zda navrhujete Rodinný dům (s dotací NZÚ a tepelným čerpadlem), nebo Komerční/Průmyslový areál." },
    { title: "2. Krok: Výběr Tier-1 HW", text: "Vyberte konkrétní fotovoltaické panely, střídače a baterie z globální databáze (JinkoSolar, Huawei, Fronius, BYD)." },
    { title: "3. Krok: Síťové posouzení PCC", text: "Systém ověří nárůst napětí ΔU dle normy PNE 33 3430-1, proudovou zatížitelnost kabelů a dimenzuje jistič." },
    { title: "4. Krok: 1-Klik Spuštění & PDF", text: "Kliknutím na 'Spustit kompletní simulaci' spočítáte NREL SAM model, Monte Carlo rizika (1 200 iterací) a vygenerujete PDF zprávu pro banku." }
  ];

  let currentStep = 0;
  function renderTourStep() {
    const s = steps[currentStep];
    const box = document.getElementById('tour-box');
    document.getElementById('tour-step-indicator').innerText = `Krok ${currentStep + 1} z ${steps.length}`;
    document.getElementById('tour-title').innerText = s.title;
    document.getElementById('tour-text').innerText = s.text;
    document.getElementById('tour-modal').classList.remove('hidden');
  }

  window.nextTourStep = function() {
    currentStep++;
    if (currentStep < steps.length) {
      renderTourStep();
    } else {
      closeTourModal();
    }
  };

  renderTourStep();
}

function closeTourModal() {
  document.getElementById('tour-modal').classList.add('hidden');
}
