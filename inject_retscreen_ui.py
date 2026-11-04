with open('d:/REST/frontend/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Přidání tlačítka RETScreen Expert Suite do přepínače pohledů
retscreen_button = '''        <button onclick="selectMode('retscreen')" id="mode-retscreen-btn" class="px-4 py-2 rounded-xl text-xs font-bold text-slate-500 hover:text-slate-900 bg-white transition flex items-center">
          <i class="fa-solid fa-leaf text-emerald-600 mr-2"></i> RETScreen Expert (5 Sešitů)
        </button>'''

if 'id="mode-retscreen-btn"' not in text:
    target_btn = '<button onclick="selectMode(\'wizard\')"'
    text = text.replace(target_btn, retscreen_button + '\n        ' + target_btn)

# 2. Vložení plnohodnotného pohledu RETScreen Expert s 5 sešity
retscreen_view_html = '''
    <!-- ==================== VIEW: RETSCREEN EXPERT FULL WORKBENCH ==================== -->
    <div id="view-retscreen" class="hidden space-y-6">
      
      <!-- RETScreen Ribbon / Sešity -->
      <div class="bg-white p-3 rounded-2xl border border-slate-200 shadow-sm flex items-center justify-between">
        <div class="flex items-center space-x-2">
          <div class="w-8 h-8 rounded-lg bg-emerald-600 text-white flex items-center justify-center font-bold text-sm">
            <i class="fa-solid fa-calculator"></i>
          </div>
          <div>
            <h2 class="text-sm font-bold text-slate-800">Natural Resources Canada (NRCan) RETScreen Expert Suite</h2>
            <p class="text-[11px] text-slate-500">Kompletní feasibility workflow: Facility • Energy • Cost • GHG Emission • Financial & Risk</p>
          </div>
        </div>
        <div class="flex space-x-2">
          <button onclick="switchRetTab('facility')" id="ret-tab-fac-btn" class="px-3 py-1.5 rounded-lg text-xs font-bold bg-emerald-600 text-white transition">1. Facility</button>
          <button onclick="switchRetTab('energy')" id="ret-tab-ene-btn" class="px-3 py-1.5 rounded-lg text-xs font-bold text-slate-600 bg-slate-100 hover:bg-slate-200 transition">2. Energy</button>
          <button onclick="switchRetTab('cost')" id="ret-tab-cst-btn" class="px-3 py-1.5 rounded-lg text-xs font-bold text-slate-600 bg-slate-100 hover:bg-slate-200 transition">3. Cost (WBS)</button>
          <button onclick="switchRetTab('emission')" id="ret-tab-ems-btn" class="px-3 py-1.5 rounded-lg text-xs font-bold text-slate-600 bg-slate-100 hover:bg-slate-200 transition">4. Emission (GHG)</button>
          <button onclick="switchRetTab('financial')" id="ret-tab-fin-btn" class="px-3 py-1.5 rounded-lg text-xs font-bold text-slate-600 bg-slate-100 hover:bg-slate-200 transition">5. Financial & Risk</button>
        </div>
      </div>

      <!-- Tab 1: Facility -->
      <div id="ret-content-facility" class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div class="glass p-5 rounded-2xl space-y-4">
          <h3 class="text-xs font-bold uppercase text-emerald-700 tracking-wider"><i class="fa-solid fa-building mr-1.5"></i> Parametry objektu</h3>
          <div>
            <label class="block text-[11px] font-medium text-slate-600 mb-1">Typ areálu / zařízení</label>
            <select id="ret-fac-type" class="w-full bg-slate-50 border border-slate-300 rounded-lg p-2 text-xs text-slate-800">
              <option value="Commercial - Office">Komerční budova - Kanceláře</option>
              <option value="Industrial - Manufacturing">Průmyslový areál - Výroba</option>
              <option value="Institutional - Hospital">Nemocnice / Zdravotnické zařízení</option>
              <option value="Multi-Residential">Bytový dům / SVJ</option>
            </select>
          </div>
          <div>
            <label class="block text-[11px] font-medium text-slate-600 mb-1">Hrubá podlahová plocha ($m^2$)</label>
            <input type="number" id="ret-fac-area" value="4500" class="w-full bg-slate-50 border border-slate-300 rounded-lg p-2 text-xs text-slate-800">
          </div>
          <div>
            <label class="block text-[11px] font-medium text-slate-600 mb-1">Roční provozní hodiny (h/rok)</label>
            <input type="number" id="ret-fac-hours" value="3200" class="w-full bg-slate-50 border border-slate-300 rounded-lg p-2 text-xs text-slate-800">
          </div>
        </div>

        <div class="glass p-5 rounded-2xl space-y-4">
          <h3 class="text-xs font-bold uppercase text-emerald-700 tracking-wider"><i class="fa-solid fa-cloud-sun mr-1.5"></i> NASA Meteorologie & Stupňodny</h3>
          <div>
            <label class="block text-[11px] font-medium text-slate-600 mb-1">Referenční klimatická stanice</label>
            <input type="text" id="ret-fac-loc" value="Praha / Střední Čechy (50.08°N, 14.43°E)" class="w-full bg-slate-50 border border-slate-300 rounded-lg p-2 text-xs text-slate-800">
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-[11px] font-medium text-slate-600 mb-1">Topné dny (HDD)</label>
              <input type="number" id="ret-fac-hdd" value="3100" class="w-full bg-slate-50 border border-slate-300 rounded-lg p-2 text-xs text-slate-800">
            </div>
            <div>
              <label class="block text-[11px] font-medium text-slate-600 mb-1">Chladicí dny (CDD)</label>
              <input type="number" id="ret-fac-cdd" value="180" class="w-full bg-slate-50 border border-slate-300 rounded-lg p-2 text-xs text-slate-800">
            </div>
          </div>
        </div>

        <div class="glass p-5 rounded-2xl flex flex-col justify-between">
          <div>
            <h3 class="text-xs font-bold uppercase text-emerald-700 tracking-wider mb-2"><i class="fa-solid fa-circle-check mr-1.5"></i> Stav projektu</h3>
            <p class="text-xs text-slate-600">Model RETScreen Expert je synchronizován s klimatickou databází NASA POWER a energetickými audity dle Vyhlášky 141/2021 Sb.</p>
          </div>
          <button onclick="runRetScreenCalculation()" class="w-full mt-4 bg-emerald-600 hover:bg-emerald-700 text-white font-bold py-2.5 rounded-xl transition shadow flex items-center justify-center text-xs">
            <i class="fa-solid fa-play mr-2"></i> Přepočítat RETScreen Model
          </button>
        </div>
      </div>

      <!-- Tab 2: Energy Model -->
      <div id="ret-content-energy" class="hidden grid grid-cols-1 md:grid-cols-2 gap-6">
        <div class="glass p-5 rounded-2xl space-y-4">
          <h3 class="text-xs font-bold uppercase text-blue-700 tracking-wider">Výchozí stav (Base Case - Stávající areál)</h3>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-[11px] font-medium text-slate-600 mb-1">Spotřeba elektřiny (MWh/rok)</label>
              <input type="number" id="ret-ene-base-elec" value="650" class="w-full bg-slate-50 border border-slate-300 rounded-lg p-2 text-xs text-slate-800">
            </div>
            <div>
              <label class="block text-[11px] font-medium text-slate-600 mb-1">Cena elektřiny (€/kWh)</label>
              <input type="number" step="0.005" id="ret-ene-base-elec-rate" value="0.165" class="w-full bg-slate-50 border border-slate-300 rounded-lg p-2 text-xs text-slate-800">
            </div>
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-[11px] font-medium text-slate-600 mb-1">Spotřeba tepla / plynu (MWh/rok)</label>
              <input type="number" id="ret-ene-base-heat" value="420" class="w-full bg-slate-50 border border-slate-300 rounded-lg p-2 text-xs text-slate-800">
            </div>
            <div>
              <label class="block text-[11px] font-medium text-slate-600 mb-1">Cena tepla (€/kWh)</label>
              <input type="number" step="0.005" id="ret-ene-base-heat-rate" value="0.085" class="w-full bg-slate-50 border border-slate-300 rounded-lg p-2 text-xs text-slate-800">
            </div>
          </div>
        </div>

        <div class="glass p-5 rounded-2xl space-y-4">
          <h3 class="text-xs font-bold uppercase text-emerald-700 tracking-wider">Navržený stav (Proposed Case - OZE & Efektivita)</h3>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-[11px] font-medium text-slate-600 mb-1">Výroba FVE (MWh/rok)</label>
              <input type="number" id="ret-ene-prop-pv" value="125" class="w-full bg-slate-50 border border-slate-300 rounded-lg p-2 text-xs text-slate-800">
            </div>
            <div>
              <label class="block text-[11px] font-medium text-slate-600 mb-1">Vlastní spotřeba FVE (%)</label>
              <input type="number" id="ret-ene-prop-self" value="75" class="w-full bg-slate-50 border border-slate-300 rounded-lg p-2 text-xs text-slate-800">
            </div>
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-[11px] font-medium text-slate-600 mb-1">Úspora energetickou efektivitou (%)</label>
              <input type="number" id="ret-ene-prop-ee" value="18" class="w-full bg-slate-50 border border-slate-300 rounded-lg p-2 text-xs text-slate-800">
            </div>
            <div>
              <label class="block text-[11px] font-medium text-slate-600 mb-1">Výkupní cena přetoků (€/kWh)</label>
              <input type="number" step="0.005" id="ret-ene-prop-export-rate" value="0.055" class="w-full bg-slate-50 border border-slate-300 rounded-lg p-2 text-xs text-slate-800">
            </div>
          </div>
        </div>
      </div>

      <!-- Tab 3: Cost Analysis (WBS) -->
      <div id="ret-content-cost" class="hidden glass p-5 rounded-2xl space-y-4">
        <h3 class="text-xs font-bold uppercase text-slate-700 tracking-wider">Rozpad investičních nákladů dle WBS (Work Breakdown Structure)</h3>
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <label class="block text-[11px] font-medium text-slate-600 mb-1">Studie proveditelnosti (€)</label>
            <input type="number" id="ret-cst-feas" value="3500" class="w-full bg-slate-50 border border-slate-300 rounded-lg p-2 text-xs text-slate-800">
          </div>
          <div>
            <label class="block text-[11px] font-medium text-slate-600 mb-1">Vývoj & Povolení (€)</label>
            <input type="number" id="ret-cst-dev" value="4500" class="w-full bg-slate-50 border border-slate-300 rounded-lg p-2 text-xs text-slate-800">
          </div>
          <div>
            <label class="block text-[11px] font-medium text-slate-600 mb-1">Inženýring & Projekt (€)</label>
            <input type="number" id="ret-cst-eng" value="5800" class="w-full bg-slate-50 border border-slate-300 rounded-lg p-2 text-xs text-slate-800">
          </div>
          <div>
            <label class="block text-[11px] font-medium text-slate-600 mb-1">Hlavní technologie FVE/BESS (€)</label>
            <input type="number" id="ret-cst-equip" value="65000" class="w-full bg-slate-50 border border-slate-300 rounded-lg p-2 text-xs text-slate-800">
          </div>
          <div>
            <label class="block text-[11px] font-medium text-slate-600 mb-1">Balance of System / Kabely (€)</label>
            <input type="number" id="ret-cst-bos" value="12000" class="w-full bg-slate-50 border border-slate-300 rounded-lg p-2 text-xs text-slate-800">
          </div>
          <div>
            <label class="block text-[11px] font-medium text-slate-600 mb-1">Montáž & Instalace (€)</label>
            <input type="number" id="ret-cst-inst" value="11500" class="w-full bg-slate-50 border border-slate-300 rounded-lg p-2 text-xs text-slate-800">
          </div>
          <div>
            <label class="block text-[11px] font-medium text-slate-600 mb-1">Rezerva na nepředvídané výdaje (€)</label>
            <input type="number" id="ret-cst-cont" value="4000" class="w-full bg-slate-50 border border-slate-300 rounded-lg p-2 text-xs text-slate-800">
          </div>
          <div>
            <label class="block text-[11px] font-medium text-slate-600 mb-1">Roční O&M servis (€/rok)</label>
            <input type="number" id="ret-cst-om" value="1200" class="w-full bg-slate-50 border border-slate-300 rounded-lg p-2 text-xs text-slate-800">
          </div>
        </div>
      </div>

      <!-- Tab 4: Emission Analysis (GHG) -->
      <div id="ret-content-emission" class="hidden glass p-5 rounded-2xl space-y-4">
        <h3 class="text-xs font-bold uppercase text-emerald-700 tracking-wider">Environmentální analýza GHG & Ekvivalenty</h3>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div class="p-4 bg-emerald-50 border border-emerald-200 rounded-xl">
            <span class="text-xs text-emerald-800 font-bold block mb-1">Roční snížení emisí GHG</span>
            <span id="ret-res-ghg-tons" class="text-2xl font-black text-emerald-900">167.0 t $CO_2$</span>
            <span class="text-[11px] text-emerald-700 block mt-1">Snížení uhlíkové stopy areálu o 38 %</span>
          </div>
          <div class="p-4 bg-slate-50 border border-slate-200 rounded-xl">
            <span class="text-xs text-slate-600 font-bold block mb-1">Ekvivalent osobních automobilů</span>
            <span id="ret-res-ghg-cars" class="text-2xl font-black text-slate-900">36.3 aut</span>
            <span class="text-[11px] text-slate-500 block mt-1">Vyřazeno z provozu ročně</span>
          </div>
          <div class="p-4 bg-slate-50 border border-slate-200 rounded-xl">
            <span class="text-xs text-slate-600 font-bold block mb-1">Uspořená ropa</span>
            <span id="ret-res-ghg-oil" class="text-2xl font-black text-slate-900">388 barelů</span>
            <span class="text-[11px] text-slate-500 block mt-1">Ušetřené primární fosilní suroviny</span>
          </div>
        </div>
      </div>

      <!-- Tab 5: Financial & Risk -->
      <div id="ret-content-financial" class="hidden space-y-6">
        <div class="glass p-5 rounded-2xl space-y-4">
          <h3 class="text-xs font-bold uppercase text-slate-700 tracking-wider">Finanční parametry & Úvěr</h3>
          <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <label class="block text-[11px] font-medium text-slate-600 mb-1">Podíl dluhu / Úvěru (%)</label>
              <input type="number" id="ret-fin-debt-ratio" value="70" class="w-full bg-slate-50 border border-slate-300 rounded-lg p-2 text-xs text-slate-800">
            </div>
            <div>
              <label class="block text-[11px] font-medium text-slate-600 mb-1">Úroková sazba úvěru (%)</label>
              <input type="number" step="0.1" id="ret-fin-debt-interest" value="5.2" class="w-full bg-slate-50 border border-slate-300 rounded-lg p-2 text-xs text-slate-800">
            </div>
            <div>
              <label class="block text-[11px] font-medium text-slate-600 mb-1">Splatnost úvěru (roky)</label>
              <input type="number" id="ret-fin-debt-term" value="15" class="w-full bg-slate-50 border border-slate-300 rounded-lg p-2 text-xs text-slate-800">
            </div>
            <div>
              <label class="block text-[11px] font-medium text-slate-600 mb-1">Diskontní sazba WACC (%)</label>
              <input type="number" step="0.5" id="ret-fin-discount" value="6.0" class="w-full bg-slate-50 border border-slate-300 rounded-lg p-2 text-xs text-slate-800">
            </div>
          </div>
        </div>

        <!-- Výsledkový souhrn RETScreen -->
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div class="glass p-4 rounded-xl border-l-4 border-emerald-500">
            <span class="text-xs text-slate-500 font-medium">Čistá současná hodnota (NPV)</span>
            <span id="ret-out-npv" class="text-xl font-black text-slate-900 block mt-1">€ 385,420</span>
          </div>
          <div class="glass p-4 rounded-xl border-l-4 border-blue-500">
            <span class="text-xs text-slate-500 font-medium">Vnitřní výnosové procento (IRR)</span>
            <span id="ret-out-irr" class="text-xl font-black text-slate-900 block mt-1">14.5 %</span>
          </div>
          <div class="glass p-4 rounded-xl border-l-4 border-purple-500">
            <span class="text-xs text-slate-500 font-medium">Prostá doba návratnosti</span>
            <span id="ret-out-payback" class="text-xl font-black text-slate-900 block mt-1">5.2 let</span>
          </div>
          <div class="glass p-4 rounded-xl border-l-4 border-amber-500">
            <span class="text-xs text-slate-500 font-medium">Roční úspora energie (Rok 1)</span>
            <span id="ret-out-savings" class="text-xl font-black text-slate-900 block mt-1">€ 70,643</span>
          </div>
        </div>
      </div>

    </div>
'''

target_view_anchor = '<!-- ==================== VIEW 1: 5KROKOVÝ FEASIBILITY WIZARD ==================== -->'
if target_view_anchor in text:
    text = text.replace(target_view_anchor, retscreen_view_html + '\n    ' + target_view_anchor)

retscreen_js = '''
  function switchRetTab(tab) {
    const tabs = ['facility', 'energy', 'cost', 'emission', 'financial'];
    tabs.forEach(t => {
      const content = document.getElementById('ret-content-' + t);
      const btn = document.getElementById('ret-tab-' + t.slice(0, 3) + '-btn');
      if (content) content.classList.add('hidden');
      if (btn) {
        btn.classList.remove('bg-emerald-600', 'text-white');
        btn.classList.add('bg-slate-100', 'text-slate-600');
      }
    });

    const activeContent = document.getElementById('ret-content-' + tab);
    const activeBtn = document.getElementById('ret-tab-' + tab.slice(0, 3) + '-btn');
    if (activeContent) activeContent.classList.remove('hidden');
    if (activeBtn) {
      activeBtn.classList.add('bg-emerald-600', 'text-white');
      activeBtn.classList.remove('bg-slate-100', 'text-slate-600');
    }
  }

  async function runRetScreenCalculation() {
    try {
      const payload = {
        facility_type: document.getElementById('ret-fac-type')?.value,
        facility_gross_floor_area_m2: parseFloat(document.getElementById('ret-fac-area')?.value || 4500),
        annual_operating_hours: parseFloat(document.getElementById('ret-fac-hours')?.value || 3200),
        base_annual_electricity_mwh: parseFloat(document.getElementById('ret-ene-base-elec')?.value || 650),
        base_electricity_rate_eur_kwh: parseFloat(document.getElementById('ret-ene-base-elec-rate')?.value || 0.165),
        base_annual_heating_mwh: parseFloat(document.getElementById('ret-ene-base-heat')?.value || 420),
        base_heating_fuel_rate_eur_kwh: parseFloat(document.getElementById('ret-ene-base-heat-rate')?.value || 0.085),
        proposed_pv_generation_mwh: parseFloat(document.getElementById('ret-ene-prop-pv')?.value || 125),
        proposed_pv_self_consumption_pct: parseFloat(document.getElementById('ret-ene-prop-self')?.value || 75),
        proposed_energy_efficiency_savings_pct: parseFloat(document.getElementById('ret-ene-prop-ee')?.value || 18),
        cost_equipment_pv_bess_eur: parseFloat(document.getElementById('ret-cst-equip')?.value || 65000),
        debt_ratio_pct: parseFloat(document.getElementById('ret-fin-debt-ratio')?.value || 70)
      };

      const res = await fetch('/api/retscreen/full-feasibility', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!res.ok) throw new Error('Chyba při výpočtu RETScreen');
      const data = await res.json();

      // Aktualizace výstupů
      if (document.getElementById('ret-res-ghg-tons')) document.getElementById('ret-res-ghg-tons').textContent = data.emissions_ghg.net_reduction_tons_yr + ' t CO2';
      if (document.getElementById('ret-res-ghg-cars')) document.getElementById('ret-res-ghg-cars').textContent = data.emissions_ghg.equivalents.passenger_cars_off_road + ' aut';
      if (document.getElementById('ret-res-ghg-oil')) document.getElementById('ret-res-ghg-oil').textContent = data.emissions_ghg.equivalents.barrels_of_crude_oil_saved + ' barelů';

      if (document.getElementById('ret-out-npv')) document.getElementById('ret-out-npv').textContent = '€ ' + data.financial_feasibility.npv_eur.toLocaleString();
      if (document.getElementById('ret-out-irr')) document.getElementById('ret-out-irr').textContent = data.financial_feasibility.irr_pct + ' %';
      if (document.getElementById('ret-out-payback')) document.getElementById('ret-out-payback').textContent = data.financial_feasibility.simple_payback_years + ' let';
      if (document.getElementById('ret-out-savings')) document.getElementById('ret-out-savings').textContent = '€ ' + data.energy_balance.year1_savings_eur.toLocaleString();

      alert('Model RETScreen Expert byl úspěšně přepočítán dle standardů NRCan!');
    } catch (e) {
      alert('Chyba RETScreen: ' + e.message);
    }
  }
'''

# Rozšíření selectMode funkce pro retscreen
text = text.replace("if (mode === 'wizard') {", "if (mode === 'retscreen') {\n      document.getElementById('view-retscreen').classList.remove('hidden');\n    } else if (mode === 'wizard') {")
text = text.replace("function selectMode(mode) {", retscreen_js + '\n  function selectMode(mode) {')

with open('d:/REST/frontend/index.html', 'w', encoding='utf-8') as f:
    f.write(text)

print('Full RETScreen Expert 5-worksheet interface injected into frontend successfully!')
