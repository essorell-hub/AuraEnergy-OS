import re

path = r'd:/REST/frontend/index.html'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

# Nahrazení temného motivu za čistý profesionální světlý styl RETScreen Expert / ČEPS / OTE
replacements = [
    ('class="h-full bg-slate-950 text-slate-100"', 'class="h-full bg-slate-50 text-slate-900 font-sans"'),
    ('bg-slate-950', 'bg-slate-50'),
    ('bg-slate-900/95', 'bg-white border-b border-slate-200 shadow-sm'),
    ('border-slate-800', 'border-slate-200'),
    ('border-slate-700', 'border-slate-300'),
    ('bg-slate-900', 'bg-white'),
    ('bg-slate-800', 'bg-slate-100'),
    ('text-slate-400', 'text-slate-500'),
    ('text-slate-300', 'text-slate-700'),
    ('text-white', 'text-slate-900'),
    ('bg-emerald-950/60', 'bg-emerald-50 border-emerald-300 text-emerald-800'),
    ('text-emerald-300', 'text-emerald-700'),
    ('.glass { background: rgba(30, 41, 59, 0.75); backdrop-filter: blur(14px); border: 1px solid rgba(255, 255, 255, 0.1); }',
     '.glass { background: #ffffff !important; border: 1px solid #e2e8f0 !important; box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05); }'),
    ('from-emerald-400 via-teal-200 to-cyan-400', 'from-emerald-700 via-teal-700 to-cyan-700'),
    ('bg-cyan-500/20 text-cyan-300 border border-cyan-500/30', 'bg-cyan-50 text-cyan-800 border border-cyan-300')
]

for old, new in replacements:
    text = text.replace(old, new)

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)

print("Light RETScreen / CEPS / OTE theme successfully written!")
