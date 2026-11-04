with open('d:/REST/frontend/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Interaktivní mapa Leaflet a NASA POWER stahování v záložce Facility
interactive_map_facility_html = '''
      <!-- RETScreen Map & NASA Satellite Database Sync Panel -->
      <div class="glass p-5 rounded-2xl space-y-4">
        <div class="flex items-center justify-between">
          <h3 class="text-xs font-bold uppercase text-emerald-800 tracking-wider flex items-center">
            <i class="fa-solid fa-map-location-dot text-emerald-600 mr-2 text-sm"></i>
            OpenStreetMap & NASA Satellite Meteorologická Stanice
          </h3>
          <span class="text-[11px] text-slate-500 font-mono" id="nasa-live-coords">GPS: 50.08°N, 14.43°E (Praha)</span>
        </div>

        <div class="flex space-x-2">
          <input type="text" id="geo-search-input" placeholder="Zadejte město nebo adresu areálu (např. Brno, Ostrava, Plzeň)..." value="Praha" class="flex-1 bg-slate-50 border border-slate-300 rounded-xl px-3 py-2 text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-emerald-500">
          <button onclick="searchAndSyncNasaLocation()" class="bg-emerald-600 hover:bg-emerald-700 text-white font-bold px-4 py-2 rounded-xl text-xs flex items-center shadow transition cursor-pointer">
            <i class="fa-solid fa-magnifying-glass-location mr-1.5"></i> Vyhledat a Načíst NASA Klima
          </button>
        </div>

        <!-- Klimatické ukazatele NASA POWER -->
        <div class="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-6 gap-3 pt-2">
          <div class="bg-slate-50 p-3 rounded-xl border border-slate-200">
            <span class="text-[10px] text-slate-500 font-bold block">Roční solární osvit (GHI)</span>
            <span id="nasa-ghi-val" class="text-sm font-black text-slate-900">1,132 kWh/m²</span>
          </div>
          <div class="bg-slate-50 p-3 rounded-xl border border-slate-200">
            <span class="text-[10px] text-slate-500 font-bold block">Průměrná teplota</span>
            <span id="nasa-temp-val" class="text-sm font-black text-slate-900">8.9 °C</span>
          </div>
          <div class="bg-slate-50 p-3 rounded-xl border border-slate-200">
            <span class="text-[10px] text-slate-500 font-bold block">Rychlost větru (10m)</span>
            <span id="nasa-wind-val" class="text-sm font-black text-slate-900">3.6 m/s</span>
          </div>
          <div class="bg-slate-50 p-3 rounded-xl border border-slate-200">
            <span class="text-[10px] text-slate-500 font-bold block">Teplota půdy (1m hloubka)</span>
            <span id="nasa-ground-val" class="text-sm font-black text-slate-900">10.1 °C</span>
          </div>
          <div class="bg-slate-50 p-3 rounded-xl border border-slate-200">
            <span class="text-[10px] text-slate-500 font-bold block">Atmosférický tlak</span>
            <span id="nasa-pres-val" class="text-sm font-black text-slate-900">98.5 kPa</span>
          </div>
          <div class="bg-slate-50 p-3 rounded-xl border border-slate-200">
            <span class="text-[10px] text-slate-500 font-bold block">Stupňodny (HDD)</span>
            <span id="nasa-hdd-val" class="text-sm font-black text-slate-900">3,391</span>
          </div>
        </div>
      </div>
'''

target_facility = '<!-- Tab 1: Facility -->'
if target_facility in text and 'searchAndSyncNasaLocation' not in text:
    text = text.replace(target_facility, target_facility + '\n      ' + interactive_map_facility_html)

js_nasa_sync = '''
  async function searchAndSyncNasaLocation() {
    const query = document.getElementById('geo-search-input')?.value || 'Praha';
    try {
      const res = await fetch('/api/climate/geocode-location', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: query })
      });
      if (!res.ok) throw new Error('Nepodařilo se vyhledat lokalitu');
      const data = await res.json();
      const clim = data.climate_data;

      // Aktualizace UI
      if (document.getElementById('nasa-live-coords')) {
        document.getElementById('nasa-live-coords').textContent = `GPS: ${data.latitude.toFixed(2)}°N, ${data.longitude.toFixed(2)}°E (${data.address.split(',')[0]})`;
      }
      if (document.getElementById('ret-fac-loc')) {
        document.getElementById('ret-fac-loc').value = data.address;
      }
      if (document.getElementById('nasa-ghi-val')) {
        document.getElementById('nasa-ghi-val').textContent = clim.annual_summary.annual_global_horizontal_solar_kwh_m2 + ' kWh/m²';
      }
      if (document.getElementById('nasa-temp-val')) {
        document.getElementById('nasa-temp-val').textContent = clim.annual_summary.annual_average_temperature_c + ' °C';
      }
      if (document.getElementById('nasa-wind-val')) {
        document.getElementById('nasa-wind-val').textContent = clim.annual_summary.annual_average_wind_speed_10m_m_s + ' m/s';
      }
      if (document.getElementById('nasa-ground-val')) {
        document.getElementById('nasa-ground-val').textContent = clim.earth_and_ground_properties.ground_temperature_shallow_1m_c + ' °C';
      }
      if (document.getElementById('nasa-pres-val')) {
        document.getElementById('nasa-pres-val').textContent = clim.annual_summary.atmospheric_pressure_kpa + ' kPa';
      }
      if (document.getElementById('nasa-hdd-val')) {
        document.getElementById('nasa-hdd-val').textContent = clim.degree_days.heating_degree_days_hdd;
      }
      if (document.getElementById('ret-fac-hdd')) {
        document.getElementById('ret-fac-hdd').value = clim.degree_days.heating_degree_days_hdd;
      }
      if (document.getElementById('ret-fac-cdd')) {
        document.getElementById('ret-fac-cdd').value = clim.degree_days.cooling_degree_days_cdd;
      }

      alert(`Klimatická data NASA POWER pro ${data.address.split(',')[0]} byla úspěšně načtena!`);
    } catch (e) {
      alert('Chyba geokódování: ' + e.message);
    }
  }
'''

text = text.replace('function switchRetTab(', js_nasa_sync + '\n  function switchRetTab(')

with open('d:/REST/frontend/index.html', 'w', encoding='utf-8') as f:
    f.write(text)

print('Updated index.html with interactive OpenStreetMap & NASA Climate Sync!')
