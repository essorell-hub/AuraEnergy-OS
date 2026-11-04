with open('d:/REST/frontend/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Nahrazení statických spanů v horním 5krokovém indikátoru za interaktivní klikací tlačítka s plynulým posunem
old_stepper = '''    <!-- 5krokový indikátor -->
    <div class="hidden lg:flex items-center space-x-2 bg-slate-50 px-4 py-2 rounded-2xl border border-slate-200 text-xs">
      <span class="font-bold text-emerald-400 flex items-center"><span class="w-5 h-5 rounded-full bg-emerald-500/20 flex items-center justify-center mr-1 text-[10px]">1</span> Lokalita</span>
      <i class="fa-solid fa-chevron-right text-slate-600 text-[10px]"></i>
      <span class="font-bold text-slate-700 flex items-center"><span class="w-5 h-5 rounded-full bg-slate-100 flex items-center justify-center mr-1 text-[10px]">2</span> HW & SAM</span>
      <i class="fa-solid fa-chevron-right text-slate-600 text-[10px]"></i>
      <span class="font-bold text-slate-700 flex items-center"><span class="w-5 h-5 rounded-full bg-slate-100 flex items-center justify-center mr-1 text-[10px]">3</span> Síť PCC</span>
      <i class="fa-solid fa-chevron-right text-slate-600 text-[10px]"></i>
      <span class="font-bold text-slate-700 flex items-center"><span class="w-5 h-5 rounded-full bg-slate-100 flex items-center justify-center mr-1 text-[10px]">4</span> Finance & LCOE</span>
      <i class="fa-solid fa-chevron-right text-slate-600 text-[10px]"></i>
      <span class="font-bold text-slate-700 flex items-center"><span class="w-5 h-5 rounded-full bg-slate-100 flex items-center justify-center mr-1 text-[10px]">5</span> Manažerský PDF</span>
    </div>'''

new_stepper = '''    <!-- 5krokový indikátor (Interaktivní navigace) -->
    <div class="hidden lg:flex items-center space-x-1.5 bg-slate-100 p-1.5 rounded-2xl border border-slate-300 text-xs shadow-inner">
      <button onclick="goToStep(1)" class="px-2.5 py-1 rounded-xl font-bold text-emerald-700 bg-white border border-emerald-300 shadow-sm flex items-center hover:bg-emerald-50 transition cursor-pointer">
        <span class="w-4 h-4 rounded-full bg-emerald-100 text-emerald-800 flex items-center justify-center mr-1.5 text-[10px]">1</span> Lokalita
      </button>
      <i class="fa-solid fa-chevron-right text-slate-400 text-[9px]"></i>
      <button onclick="goToStep(2)" class="px-2.5 py-1 rounded-xl font-bold text-slate-700 bg-white border border-slate-300 shadow-sm flex items-center hover:bg-slate-50 transition cursor-pointer">
        <span class="w-4 h-4 rounded-full bg-cyan-100 text-cyan-800 flex items-center justify-center mr-1.5 text-[10px]">2</span> HW & SAM
      </button>
      <i class="fa-solid fa-chevron-right text-slate-400 text-[9px]"></i>
      <button onclick="goToStep(3)" class="px-2.5 py-1 rounded-xl font-bold text-slate-700 bg-white border border-slate-300 shadow-sm flex items-center hover:bg-slate-50 transition cursor-pointer">
        <span class="w-4 h-4 rounded-full bg-purple-100 text-purple-800 flex items-center justify-center mr-1.5 text-[10px]">3</span> Síť PCC
      </button>
      <i class="fa-solid fa-chevron-right text-slate-400 text-[9px]"></i>
      <button onclick="goToStep(4)" class="px-2.5 py-1 rounded-xl font-bold text-slate-700 bg-white border border-slate-300 shadow-sm flex items-center hover:bg-slate-50 transition cursor-pointer">
        <span class="w-4 h-4 rounded-full bg-amber-100 text-amber-800 flex items-center justify-center mr-1.5 text-[10px]">4</span> Finance & LCOE
      </button>
      <i class="fa-solid fa-chevron-right text-slate-400 text-[9px]"></i>
      <button onclick="goToStep(5)" class="px-2.5 py-1 rounded-xl font-bold text-slate-700 bg-white border border-slate-300 shadow-sm flex items-center hover:bg-slate-50 transition cursor-pointer">
        <span class="w-4 h-4 rounded-full bg-emerald-100 text-emerald-800 flex items-center justify-center mr-1.5 text-[10px]">5</span> Manažerský PDF
      </button>
    </div>'''

text = text.replace(old_stepper, new_stepper)

# Přidání id do jednotlivých kroků a JS funkce goToStep
text = text.replace('<span class="text-[11px] font-bold text-emerald-400 uppercase tracking-wider">Krok 1: Typ objektu & OZE Technologie</span>',
                    '<div id="step-1-anchor"></div><span class="text-[11px] font-bold text-emerald-700 uppercase tracking-wider">Krok 1: Typ objektu & OZE Technologie</span>')

text = text.replace('<span class="text-[11px] font-bold text-cyan-400 uppercase tracking-wider">Krok 2: Výběr HW komponent</span>',
                    '<div id="step-2-anchor"></div><span class="text-[11px] font-bold text-cyan-700 uppercase tracking-wider">Krok 2: Výběr HW komponent</span>')

text = text.replace('<span class="text-[11px] font-bold text-purple-400 uppercase tracking-wider">Krok 3: Parametry připojení k síti</span>',
                    '<div id="step-3-anchor"></div><span class="text-[11px] font-bold text-purple-700 uppercase tracking-wider">Krok 3: Parametry připojení k síti</span>')

text = text.replace('<span class="text-[11px] font-bold text-amber-400 uppercase tracking-wider">Krok 4: Finanční zadání</span>',
                    '<div id="step-4-anchor"></div><span class="text-[11px] font-bold text-amber-700 uppercase tracking-wider">Krok 4: Finanční zadání</span>')

# JS funkce pro navigaci
js_function = '''
  function goToStep(stepNum) {
    selectMode('wizard');
    setTimeout(() => {
      if (stepNum === 5) {
        window.print();
        return;
      }
      const anchor = document.getElementById('step-' + stepNum + '-anchor');
      if (anchor) {
        anchor.scrollIntoView({ behavior: 'smooth', block: 'center' });
        // Zvýraznění panelu animací
        const parent = anchor.parentElement;
        if (parent) {
          parent.classList.add('ring-2', 'ring-emerald-500', 'bg-emerald-50/50', 'transition', 'duration-300');
          setTimeout(() => {
            parent.classList.remove('ring-2', 'ring-emerald-500', 'bg-emerald-50/50');
          }, 1500);
        }
      }
    }, 50);
  }
'''

text = text.replace('function selectMode(', js_function + '\n  function selectMode(')

with open('d:/REST/frontend/index.html', 'w', encoding='utf-8') as f:
    f.write(text)

print('Navigation buttons in top bar activated successfully!')
