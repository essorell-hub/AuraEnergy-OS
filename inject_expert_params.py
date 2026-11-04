with open('d:/REST/frontend/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

# JS funkce pro načtení plného hardwarového katalogu při startu a doplnění panelu expertních parametrů
expert_panel_html = '''
            <!-- Expertní inženýrské parametry (NREL SAM & RETScreen Expert Full Sizing) -->
            <div class="border-t border-slate-200 pt-3">
              <button type="button" onclick="toggleExpertParams()" class="w-full py-2 px-3 bg-slate-100 hover:bg-slate-200 text-slate-800 text-xs font-bold rounded-xl border border-slate-300 flex items-center justify-between transition cursor-pointer">
                <span><i class="fa-solid fa-microchip text-indigo-600 mr-2"></i> Expertní inženýrské parametry (NREL SAM)</span>
                <i id="expert-chevron" class="fa-solid fa-chevron-down text-slate-500"></i>
              </button>

              <div id="expert-params-container" class="hidden mt-3 p-3 bg-slate-50 rounded-xl border border-slate-300 space-y-3 text-xs">
                <div class="grid grid-cols-2 gap-3">
                  <div>
                    <label class="block text-[11px] font-medium text-slate-600 mb-1">Teplotní koef. Pmax (%/°C)</label>
                    <input type="number" step="0.01" id="exp-gamma" value="-0.30" class="w-full bg-white border border-slate-300 rounded-lg px-2.5 py-1.5 text-xs text-slate-800">
                  </div>
                  <div>
                    <label class="block text-[11px] font-medium text-slate-600 mb-1">Teplota NOCT (°C)</label>
                    <input type="number" id="exp-noct" value="45.0" class="w-full bg-white border border-slate-300 rounded-lg px-2.5 py-1.5 text-xs text-slate-800">
                  </div>
                </div>

                <div class="grid grid-cols-2 gap-3">
                  <div>
                    <label class="block text-[11px] font-medium text-slate-600 mb-1">Bifacialita panelu (0-1.0)</label>
                    <input type="number" step="0.05" id="exp-bifacial" value="0.80" class="w-full bg-white border border-slate-300 rounded-lg px-2.5 py-1.5 text-xs text-slate-800">
                  </div>
                  <div>
                    <label class="block text-[11px] font-medium text-slate-600 mb-1">Euro účinnost střídače (%)</label>
                    <input type="number" step="0.1" id="exp-inv-eff" value="98.4" class="w-full bg-white border border-slate-300 rounded-lg px-2.5 py-1.5 text-xs text-slate-800">
                  </div>
                </div>

                <div class="grid grid-cols-2 gap-3">
                  <div>
                    <label class="block text-[11px] font-medium text-slate-600 mb-1">Znečištění & Soiling ztráty (%)</label>
                    <input type="number" step="0.1" id="exp-soiling" value="2.0" class="w-full bg-white border border-slate-300 rounded-lg px-2.5 py-1.5 text-xs text-slate-800">
                  </div>
                  <div>
                    <label class="block text-[11px] font-medium text-slate-600 mb-1">Mismatch ztráty pole (%)</label>
                    <input type="number" step="0.1" id="exp-mismatch" value="1.5" class="w-full bg-white border border-slate-300 rounded-lg px-2.5 py-1.5 text-xs text-slate-800">
                  </div>
                </div>

                <div>
                  <label class="block text-[11px] font-medium text-slate-600 mb-1">Degradace panelů v roce 1 (%/rok)</label>
                  <input type="number" step="0.05" id="exp-degradation" value="0.40" class="w-full bg-white border border-slate-300 rounded-lg px-2.5 py-1.5 text-xs text-slate-800">
                </div>
              </div>
            </div>
'''

target_anchor = '<!-- Krok 3: Síť PCC parametry -->'
if target_anchor in text:
    text = text.replace(target_anchor, expert_panel_html + '\n          ' + target_anchor)

js_hw_loader = '''
  function toggleExpertParams() {
    const c = document.getElementById('expert-params-container');
    const chev = document.getElementById('expert-chevron');
    if (c) {
      c.classList.toggle('hidden');
      if (chev) {
        chev.classList.toggle('fa-chevron-down');
        chev.classList.toggle('fa-chevron-up');
      }
    }
  }

  async function loadFullHardwareCatalog() {
    try {
      const res = await fetch('/api/hardware/catalog');
      if (!res.ok) return;
      const items = await res.json();
      
      const modSelect = document.getElementById('cfg-module');
      const invSelect = document.getElementById('cfg-inverter');

      if (modSelect) {
        const modules = items.filter(x => x.category === 'MODULE');
        if (modules.length > 0) {
          modSelect.innerHTML = modules.map(m => {
            const p = m.params || {};
            return `<option value="${m.id}" data-pmax="${p.temp_coeff_pmax || -0.30}" data-noct="${p.noct_c || 45}" data-bi="${p.bifaciality_factor || 0}">${m.manufacturer} - ${m.model_name} (${p.rated_power_w || 500}W, ${p.cell_technology || 'TOPCon'})</option>`;
          }).join('');
        }
      }

      if (invSelect) {
        const inverters = items.filter(x => x.category === 'INVERTER');
        if (inverters.length > 0) {
          invSelect.innerHTML = inverters.map(i => {
            const p = i.params || {};
            return `<option value="${i.id}" data-eff="${p.max_efficiency_pct || 98.0}">${i.manufacturer} - ${i.model_name} (${p.rated_ac_power_kw || 10} kW AC, ${p.inverter_type || 'String'})</option>`;
          }).join('');
        }
      }

      // Propojení auto-vyplnění expertních parametrů při změně modelu
      if (modSelect) {
        modSelect.addEventListener('change', function() {
          const opt = this.options[this.selectedIndex];
          if (opt) {
            const gamma = opt.getAttribute('data-pmax');
            const noct = opt.getAttribute('data-noct');
            const bi = opt.getAttribute('data-bi');
            if (gamma && document.getElementById('exp-gamma')) document.getElementById('exp-gamma').value = gamma;
            if (noct && document.getElementById('exp-noct')) document.getElementById('exp-noct').value = noct;
            if (bi && document.getElementById('exp-bifacial')) document.getElementById('exp-bifacial').value = bi;
          }
        });
      }

      if (invSelect) {
        invSelect.addEventListener('change', function() {
          const opt = this.options[this.selectedIndex];
          if (opt) {
            const eff = opt.getAttribute('data-eff');
            if (eff && document.getElementById('exp-inv-eff')) document.getElementById('exp-inv-eff').value = eff;
          }
        });
      }

    } catch (e) {
      console.error('Chyba pri nacitani HW katalogu:', e);
    }
  }

  window.addEventListener('DOMContentLoaded', () => {
    loadFullHardwareCatalog();
  });
'''

text = text.replace('window.addEventListener(\'DOMContentLoaded\', () => {', js_hw_loader + '\n  // existing loader\n  window.addEventListener(\'DOMContentLoaded\', () => {')

with open('d:/REST/frontend/index.html', 'w', encoding='utf-8') as f:
    f.write(text)

print('Updated frontend with full hardware catalog and expert params panel!')
