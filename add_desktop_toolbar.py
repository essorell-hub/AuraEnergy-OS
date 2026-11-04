with open('d:/REST/frontend/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Nativní dialogy a desktopové akce: Ukládání souborů .aura, načítání projektů, export CAD .dxf
desktop_actions_html = '''
    <!-- Desktop Native Quick Actions Bar (RETScreen & SAM Suite) -->
    <div class="bg-white border-b border-slate-200 px-6 py-2 flex items-center justify-between text-xs text-slate-600 no-print">
      <div class="flex items-center space-x-4">
        <span class="font-bold text-slate-800 flex items-center">
          <i class="fa-solid fa-desktop text-emerald-600 mr-1.5"></i> Desktop Režim
        </span>
        <span class="text-slate-300">|</span>
        <button onclick="createNewProjectFile()" class="hover:text-emerald-700 font-medium flex items-center transition">
          <i class="fa-solid fa-file-circle-plus text-slate-400 mr-1"></i> Nový soubor (.aura)
        </button>
        <button onclick="openLocalProjectDialog()" class="hover:text-emerald-700 font-medium flex items-center transition">
          <i class="fa-solid fa-folder-open text-amber-500 mr-1"></i> Otevřít ze souboru
        </button>
        <button onclick="exportProjectFile()" class="hover:text-emerald-700 font-medium flex items-center transition">
          <i class="fa-solid fa-floppy-disk text-cyan-600 mr-1"></i> Uložit projekt jako...
        </button>
        <button onclick="downloadCadDxfDirect()" class="hover:text-emerald-700 font-medium flex items-center transition">
          <i class="fa-solid fa-drafting-compass text-purple-600 mr-1"></i> Export CAD SLD (.dxf)
        </button>
        <button onclick="downloadIfcBimDirect()" class="hover:text-emerald-700 font-medium flex items-center transition">
          <i class="fa-solid fa-cube text-blue-600 mr-1"></i> Export BIM (.ifc)
        </button>
      </div>
      <div class="flex items-center space-x-3">
        <span class="bg-emerald-50 text-emerald-700 px-2.5 py-0.5 rounded-full border border-emerald-300 font-bold text-[10px]">
          <i class="fa-solid fa-database mr-1"></i> CEC/Sandia Knihovna aktivní (47 modelů)
        </span>
        <span class="text-[11px] text-slate-400 font-mono" id="desktop-timestamp"></span>
      </div>
    </div>
'''

target_header = '</header>'
if target_header in text and 'Desktop Native Quick Actions Bar' not in text:
    text = text.replace(target_header, target_header + '\n' + desktop_actions_html)

desktop_js = '''
  function updateDesktopTimestamp() {
    const el = document.getElementById('desktop-timestamp');
    if (el) {
      const now = new Date();
      el.textContent = now.toLocaleDateString('cs-CZ') + ' ' + now.toLocaleTimeString('cs-CZ');
    }
  }
  setInterval(updateDesktopTimestamp, 1000);

  function createNewProjectFile() {
    if (confirm('Chcete vytvořit nový projekt? Všechny neuložené změny budou resetovány.')) {
      document.getElementById('cfg-modules-count').value = '172';
      document.getElementById('cfg-tilt').value = '35';
      document.getElementById('cfg-capex').value = '78000';
      document.getElementById('cfg-tariff').value = '165';
      runFullSamSimulation();
    }
  }

  function exportProjectFile() {
    const projectData = {
      app: 'AuraEnergy OS Desktop Pro',
      version: '25.0',
      exported_at: new Date().toISOString(),
      configuration: {
        segment: document.getElementById('cfg-segment')?.value,
        tech: document.getElementById('cfg-tech')?.value,
        module_id: document.getElementById('cfg-module')?.value,
        inverter_id: document.getElementById('cfg-inverter')?.value,
        modules_count: document.getElementById('cfg-modules-count')?.value,
        tilt_deg: document.getElementById('cfg-tilt')?.value,
        capex_eur: document.getElementById('cfg-capex')?.value,
        tariff_eur_mwh: document.getElementById('cfg-tariff')?.value
      }
    };

    const blob = new Blob([JSON.stringify(projectData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `projekt_auraenergy_${new Date().toISOString().slice(0, 10)}.aura`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  function openLocalProjectDialog() {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.aura,.json';
    input.onchange = e => {
      const file = e.target.files[0];
      if (!file) return;
      const reader = new FileReader();
      reader.onload = ev => {
        try {
          const data = JSON.parse(ev.target.result);
          if (data.configuration) {
            const c = data.configuration;
            if (c.modules_count && document.getElementById('cfg-modules-count')) document.getElementById('cfg-modules-count').value = c.modules_count;
            if (c.tilt_deg && document.getElementById('cfg-tilt')) document.getElementById('cfg-tilt').value = c.tilt_deg;
            if (c.capex_eur && document.getElementById('cfg-capex')) document.getElementById('cfg-capex').value = c.capex_eur;
            if (c.tariff_eur_mwh && document.getElementById('cfg-tariff')) document.getElementById('cfg-tariff').value = c.tariff_eur_mwh;
            runFullSamSimulation();
            alert('Projekt byl úspěšně načten ze souboru .aura!');
          }
        } catch (err) {
          alert('Chyba při čtení souboru: ' + err.message);
        }
      };
      reader.readAsText(file);
    };
    input.click();
  }

  async function downloadCadDxfDirect() {
    try {
      const pvKwp = (parseFloat(document.getElementById('cfg-modules-count')?.value || 172) * 580) / 1000.0;
      const res = await fetch('/api/cad/generate-sld', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          project_name: 'AuraEnergy Desktop Projekt',
          pv_capacity_kwp: pvKwp,
          strings_count: 8
        })
      });
      if (!res.ok) throw new Error('Generování DXF selhalo');
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'jednopolove_schema_cad.dxf';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (e) {
      alert('Chyba: ' + e.message);
    }
  }

  async function downloadIfcBimDirect() {
    try {
      const pvKwp = (parseFloat(document.getElementById('cfg-modules-count')?.value || 172) * 580) / 1000.0;
      const res = await fetch('/api/bim/export-ifc', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          project_name: 'AuraEnergy Desktop Model',
          pv_capacity_kwp: pvKwp
        })
      });
      if (!res.ok) throw new Error('Generování IFC selhalo');
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'model_fve_bim.ifc';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (e) {
      alert('Chyba: ' + e.message);
    }
  }
'''

text = text.replace('function runFullSamSimulation(', desktop_js + '\n  function runFullSamSimulation(')

with open('d:/REST/frontend/index.html', 'w', encoding='utf-8') as f:
    f.write(text)

print('Desktop toolbar with native file operations added successfully!')
