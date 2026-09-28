#!/usr/bin/env python3
# GFI v2 — validación, paso B: los 4 números de skill del paper, con sus definiciones EXACTAS.
#
# 1) SKILL ZONAL (foco asignado a SU zona) — estadístico OPERATIVO (calibración ≥ 2.2.0):
#    - DC de zona = media MÓVIL de 30 días al último día del mes ([fin−29, fin], ≥25 días
#      con dato — lo mismo que compara el worker), de fwi_<lat>_<lon>.csv.
#    - Disparo: DC (2 decimales) > umbral_dc_p90[mes] de enso_calibracion.json (el 11º
#      menor de las 13 móviles de fin de ese mes 2012–2024, leave-nothing-out, top-2 de 13).
#    - HIT = focos de ESA zona ese mes ≥ mediana de los 13 mismos-meses de la zona, Y > 0.
#    - Base = misma condición sobre TODOS los zona-mes 2012–2024.
#
# 2) COMPLEMENTARIEDAD DC×FWI (nivel provincial, 3.744 provincia-mes 2012–2024):
#    - FWI mensual provincial = Σ peso_zona · media(FWI diario del mes) (mismos CSVs + pesos).
#    - pct FWI con la misma fórmula; pct DC = campo 'pct' de gfi_v2_retro.json (dc_pond).
#    - HIT = focos provinciales del mes (historico.json) ≥ mediana del mes calendario 2012–2024.
#    - Celdas: ambos≥90 ("convergencia"), solo DC≥90, solo FWI≥90, ninguno (base).
#    - r = Pearson entre pct DC y pct FWI sobre los 3.744.
#    → paper: solo-DC 70.5% · convergencia 92.4% · r=0.70 · (base 'ninguno' 48.8%).
#
# Requiere: 05a_focos_por_zona.mjs corrido (→ ~/.openclaw/data/gfi_v2_focos_zona.json),
# ~/.openclaw/data/gfi_v2_fwi/*.csv, zonas_fuego.json, gfi_v2_retro.json, historico.json.
import json, csv, statistics, os, datetime as dt
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.expanduser('~/.openclaw/data/gfi_v2_fwi')
Z = json.load(open(os.path.join(HERE, 'zonas_fuego.json')))['zonas']
FZ = json.load(open(os.path.expanduser('~/.openclaw/data/gfi_v2_focos_zona.json')))
RETRO = json.load(open(os.path.join(HERE, 'gfi_v2_retro.json')))['provincias']
HIST = json.load(open(os.path.join(HERE, 'historico.json')))['prov']
UMB = json.load(open(os.path.join(HERE, 'enso_calibracion.json')))['v2']['zonas']

def mensual(f, col):
    acc = defaultdict(list)
    for row in csv.DictReader(open(f)):
        acc[row['date'][:7]].append(float(row[col]))
    return {ym: sum(v)/len(v) for ym, v in acc.items()}

def diario(f, col):
    return {row['date']: float(row[col]) for row in csv.DictReader(open(f))}

# ── 1) skill zonal (móvil 30d a fin de mes vs umbral de calibración) ─────────
esc, base = [], []
for prov, zs in Z.items():
    for j, z in enumerate(zs):
        zid = f"{z['lat']:.2f}_{z['lon']:.2f}"
        s = diario(f'{D}/fwi_{zid}.csv', 'dc')
        umb = UMB[zid]['umbral_dc_p90']
        foc = FZ[prov][j]
        for a in range(2012, 2025):
            for m in range(1, 13):
                ult = dt.date(a + (m == 12), (m % 12) + 1, 1) - dt.timedelta(days=1)
                vent = [s[(ult - dt.timedelta(days=k)).isoformat()] for k in range(30)
                        if (ult - dt.timedelta(days=k)).isoformat() in s]
                if len(vent) < 25: continue
                dispara = round(sum(vent)/len(vent), 2) > umb[m-1]
                fserie = [foc.get(f'{y}-{m:02d}', 0) for y in range(2012, 2025)]
                v = foc.get(f'{a}-{m:02d}', 0)
                hit = v >= statistics.median(fserie) and v > 0
                base.append(hit)
                if dispara: esc.append(hit)
print(f'1) SKILL ZONAL: disparos={len(esc)} · hit={100*sum(esc)/len(esc):.1f}% · base={100*sum(base)/len(base):.1f}%')

# ── 2) complementariedad provincial DC×FWI ──────────────────────────────────
fwi_m = defaultdict(lambda: defaultdict(float))
for prov, zs in Z.items():
    for z in zs:
        s = mensual(f"{D}/fwi_{z['lat']:.2f}_{z['lon']:.2f}.csv", 'fwi')
        for ym, v in s.items(): fwi_m[prov][ym] += z['peso'] * v

def pct_fwi(prov, a, m):
    clim = [fwi_m[prov][f'{y}-{m:02d}'] for y in range(2012, 2025)]
    return 100*sum(1 for c in clim if c < fwi_m[prov][f'{a}-{m:02d}'])/12

cells = {'ambos': [], 'solo_dc': [], 'solo_fwi': [], 'ninguno': []}
xs, ys = [], []
for prov, meses in RETRO.items():
    if prov not in HIST: continue
    mens = HIST[prov]['mensual']
    for ym, d in meses.items():
        a, m = int(ym[:4]), int(ym[5:7])
        if not (2012 <= a <= 2024): continue
        pf = pct_fwi(prov, a, m)
        xs.append(d['pct']); ys.append(pf)
        serie = [mens[str(y)][m-1] for y in range(2012, 2025) if str(y) in mens]
        hit = mens[str(a)][m-1] >= statistics.median(serie)
        k = 'ambos' if (d['pct'] >= 90 and pf >= 90) else 'solo_dc' if d['pct'] >= 90 else 'solo_fwi' if pf >= 90 else 'ninguno'
        cells[k].append(hit)
for k, v in cells.items():
    print(f'2) {k:8s} n={len(v):4d} · fuego≥mediana={100*sum(v)/len(v):.1f}%')
n = len(xs); mx, my = sum(xs)/n, sum(ys)/n
cov = sum((x-mx)*(y-my) for x, y in zip(xs, ys))/n
sd = (sum((x-mx)**2 for x in xs)/n)**.5 * (sum((y-my)**2 for y in ys)/n)**.5
print(f'2) r Pearson pct-DC vs pct-FWI: {cov/sd:.2f} (n={n})')
