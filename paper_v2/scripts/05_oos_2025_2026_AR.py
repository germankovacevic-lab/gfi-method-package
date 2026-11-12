#!/usr/bin/env python3
"""Paper v2 — Argentina FUERA DE MUESTRA: 2025 (término de sequía; nada de 2025 entró en los
umbrales DC 2012–2024) y 2026 (ambos términos; 2026 no entró en ninguna calibración).

Término de sequía: umbrales congelados (11º menor de las 13 móviles 30 d a fin de mes, 2012–2024,
ERA5 puro) → disparo zona-mes 2025/2026; evento = focos ≥ mediana 2012–2024 del mismo mes (y > 0).
Métricas idénticas al hindcast. Regla país ≥16/24 y barrido.
Término ENSO 2026: fase ONI lag 3 en cada mes de la ventana → anomalía observada (VIIRS 2026 /
mediana VIIRS 2012–2025 del mes, intra-sensor) por región; se compara con el factor calibrado.

Uso: python3 05_oos_2025_2026_AR.py
"""
import json, csv, os, statistics, datetime as dt
import numpy as np
from collections import defaultdict

HOME = os.path.expanduser('~'); G = f'{HOME}/.openclaw/workspace/geofuego'; DATA = f'{HOME}/.openclaw/data'
OUTD = f'{G}/paper/v2/resultados'
P = f'{G}/tools/gfi_era5_ar/pkg_cds'
ZON = json.load(open(f'{P}/zonas_fuego.json'))['zonas']
FOC = json.load(open(f'{DATA}/gfi_v2_focos_zona.json'))
NEW = json.load(open(f'{DATA}/gfi_v2_focos_zona_2025_2026.json'))
FWI = f'{DATA}/gfi_v2_fwi_cds'
HIST = json.load(open(f'{P}/historico.json'))
CAL = json.load(open(f'{P}/enso_calibracion.json'))
SER = json.load(open(f'{G}/tools/gfi_v2_paper/series_enso_AR.json'))
YS = list(range(2012, 2025))
MESES = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic']

def zid(z): return f"{z['lat']:.2f}_{z['lon']:.2f}"
def diario(z):
    out = {}
    for r in csv.DictReader(open(f'{FWI}/fwi_{zid(z)}.csv')): out[r['date']] = float(r['dc'])
    return out
def movil(s, y, m, W=30):
    fin = dt.date(y + (m == 12), (m % 12) + 1, 1) - dt.timedelta(days=1)
    v = [s[(fin - dt.timedelta(days=k)).isoformat()] for k in range(W) if (fin - dt.timedelta(days=k)).isoformat() in s]
    return round(sum(v) / len(v), 2) if len(v) >= 25 else None
def metr(a, b, c, d):
    n = a + b + c + d
    pod = a / (a + c) if a + c else float('nan'); pofd = b / (b + d) if b + d else float('nan')
    return dict(a=a, b=b, c=c, d=d, n=n, rate=(a + b) / n, base=(a + c) / n, prec=(a / (a + b) if a + b else float('nan')),
                pod=pod, pofd=pofd, pss=pod - pofd, bias=((a + b) / (a + c) if a + c else float('nan')))

R = {'generado': dt.date.today().isoformat()}
# ───────── término de sequía 2025 / 2026 ─────────
print('leyendo zonas…')
regs = []   # (y, m, prov, j, dispara, evento, focos, mediana, dc, umbral)
umbrales_loyo = {}
for prov, zs in ZON.items():
    for j, z in enumerate(zs):
        s = diario(z)
        hist = FOC[prov][j]; nuevo = NEW['focos'][prov][j]
        for m in range(1, 13):
            clim_dc = [movil(s, y, m) for y in YS]
            if None in clim_dc: continue
            umb = sorted(clim_dc)[10]                         # 11º menor de 13 (= enso_calibracion v2)
            ser = [hist.get(f'{y}-{m:02d}', 0) for y in YS]; medf = statistics.median(ser)
            for y in (2025, 2026):
                v = movil(s, y, m)
                if v is None: continue
                ym = f'{y}-{m:02d}'
                if y == 2026 and ym > '2026-10': continue          # NRT incompleto desde nov
                f = nuevo.get(ym, 0)
                regs.append((y, m, prov, j, v > umb, (f >= medf and f > 0), f, medf, v, umb))

for y in (2025, 2026):
    rr = [r for r in regs if r[0] == y]
    a = sum(1 for r in rr if r[4] and r[5]); b = sum(1 for r in rr if r[4] and not r[5])
    c = sum(1 for r in rr if not r[4] and r[5]); d = sum(1 for r in rr if not r[4] and not r[5])
    M = metr(a, b, c, d)
    # baseline climatología igualada en tasa (share mensual de la zona)
    R[f'sequia_{y}'] = M
    print(f"\nSEQUÍA {y}: N={M['n']} zona-meses · disparo {100*M['rate']:.1f}% · base {100*M['base']:.1f}% · precisión {100*M['prec']:.1f}% · POD {100*M['pod']:.1f}% · POFD {100*M['pofd']:.1f}% · PSS {M['pss']:.3f}")
    # por mes
    pm = defaultdict(lambda: [0, 0, 0, 0])
    for r in rr:
        k = f'{r[0]}-{r[1]:02d}'; i = 0 if (r[4] and r[5]) else 1 if r[4] else 2 if r[5] else 3; pm[k][i] += 1
    R[f'sequia_{y}_por_mes'] = dict(pm)
    for k in sorted(pm):
        a_, b_, c_, d_ = pm[k]
        print(f"   {k}: disparos {a_+b_:3} (aciertos {a_:3}) · eventos {a_+c_:3}/{a_+b_+c_+d_}")

# comparación con el hindcast 2012–2024 (misma definición, ERA5 puro) — cifras de sensibilidad_AR.json A k=2
try:
    S = json.load(open(f'{OUTD}/sensibilidad_AR.json'))
    k2 = [x for x in S['A_rango'] if x['k'] == 2][0]
    R['hindcast_2012_2024_ref'] = dict(prec=k2['prec'], pod=k2['pod'], pss=k2['pss'], ci=k2['ci'])
    print(f"\n(ref. hindcast 2012–2024: precisión {100*k2['prec']:.1f}% · POD {100*k2['pod']:.1f}% · PSS {k2['pss']:.3f} IC {k2['ci']['pss']})")
except Exception as e:
    print('sin referencia de hindcast:', e)

# ───────── regla país 2025/2026 ─────────
print('\nREGLA PAÍS (provincias con alguna zona disparada):')
ar = {int(y): v for y, v in HIST['ar']['mensual'].items()}
cnt = defaultdict(set)
for r in regs:
    if r[4]: cnt[f'{r[0]}-{r[1]:02d}'].add(r[2])
pais_new = NEW['pais']
tabla = []
for ym in sorted(set(f'{r[0]}-{r[1]:02d}' for r in regs)):
    y, m = int(ym[:4]), int(ym[5:])
    ser = [ar[k][m - 1] for k in YS]; medp = statistics.median(ser)
    f = pais_new.get(ym, 0)
    n = len(cnt.get(ym, ()))
    tabla.append(dict(ym=ym, n_prov=n, activa_16=n >= 16, focos=f, mediana=medp, evento=f >= medp))
    print(f"   {ym}: {n:2}/24 provincias escaladas {'[≥16 ACTIVA]' if n >= 16 else '            '} · focos país {f:6} vs mediana {medp:7.0f} {'↑' if f >= medp else '↓'}")
R['pais'] = tabla

# ───────── término ENSO 2026 (y 2025 como referencia) ─────────
print('\nTÉRMINO ENSO — temporadas 2025 y 2026 (anomalía VIIRS vs mediana 2012–2025 del mes, fase ONI lag 3):')
oni = {}
for k, v in SER['oni'].items():
    yy, mm = k.split('-'); oni[(int(yy), int(mm) - 1)] = v
def fase(v): return None if v is None else ('nino' if v >= 0.5 else 'nina' if v <= -0.5 else 'neutral')
def fase_lag(y, m0, lag=3):
    t = y * 12 + m0 - lag; return fase(oni.get((t // 12, t % 12)))
REG = SER['regiones']
viirs = SER['serie']['VIIRS']
def serie_amb(a):
    if a == 'pais': return viirs['pais']
    return viirs['prov'].get('R:' + a, {})
def obs_2026(a, y):
    if a == 'pais': return {m: NEW['pais'].get(f'{y}-{m+1:02d}') for m in range(12)}
    out = {}
    for m in range(12):
        tot = 0; ok = False
        for p in REG[a]:
            v = NEW['prov_mensual'].get(p, {}).get(f'{y}-{m+1:02d}')
            if v is not None: tot += v; ok = True
        out[m] = tot if ok else None
    return out
enso = {}
for a in ['pais'] + list(REG):
    vent = [MESES.index(x) for x in CAL['ventanas'][a]['meses']]
    base = serie_amb(a)
    sen = CAL['senal'][a]; fac = CAL['factores'][a]['lag3']
    for y in (2025, 2026):
        obs = obs_2026(a, y)
        filas = []
        for m in vent:
            med = statistics.median([base[str(yy)][m] for yy in range(2012, 2026) if str(yy) in base])
            v = obs.get(m)
            if v is None or med < 5: continue
            if y == 2026 and m >= 10: continue   # nov/dic 2026 sin dato
            filas.append(dict(mes=MESES[m], fase=fase_lag(y, m), focos=v, mediana=med, anom=v / med))
        if not filas: continue
        fases = [f['fase'] for f in filas]; anom = statistics.median([f['anom'] for f in filas])
        fdom = max(set(fases), key=fases.count)
        pred = fac.get(fdom, {}).get('factor')
        enso[f'{a}_{y}'] = dict(ambito=a, anio=y, senal=sen['tipo'], meses=filas, fase_dominante=fdom, anom_obs=anom, factor_calibrado=pred)
        print(f"   {a:10} {y}: fase lag3 {fdom:8} · anomalía observada {anom:.2f} · factor calibrado {pred} · señal {sen['tipo']} · meses " +
              ' '.join(f"{f['mes']}:{f['anom']:.2f}" for f in filas))
R['enso'] = enso
json.dump(R, open(f'{OUTD}/oos_2025_2026_AR.json', 'w'), indent=1, default=float)
print(f'\n→ {OUTD}/oos_2025_2026_AR.json')
