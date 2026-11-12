#!/usr/bin/env python3
"""Paper v2 — skill del ÍNDICE COMPLETO (nivel publicado BAJO/MEDIO/ALTO por provincia y mes,
motor de producción + calibración 2.2.0 + DC ERA5 puro) contra el fuego observado.

Lo que la v1 no medía: el término ENSO y el de sequía se verificaban por separado; aquí se verifica
el nivel que el producto habría publicado. Hindcast: tools/gfi_era5_ar/pkg_cds/gfi_v2_retro.json
(gen_gfi_retro.mjs). Fuego: VIIRS por provincia 2012–2024 (focos por zona sumados) y 2025–2026
(gfi_v2_focos_zona_2025_2026.json). Evento = focos provinciales del mes ≥ mediana 2012–2024 del mes.

Métricas: por nivel, tasa de evento y anomalía mediana (monotonía B<M<A); ALTO como predictor
binario (precision, POD, PSS, IC bloque-año); ALTO-o-MEDIO vs BAJO (el gate); in-sample 2012–2024 y
fuera de muestra 2025–2026 (hasta oct); país aparte.
Uso: python3 06_skill_indice_AR.py
"""
import json, os, statistics
import numpy as np
from collections import defaultdict

HOME = os.path.expanduser('~'); G = f'{HOME}/.openclaw/workspace/geofuego'; DATA = f'{HOME}/.openclaw/data'
OUTD = f'{G}/paper/v2/resultados'; P = f'{G}/tools/gfi_era5_ar/pkg_cds'
RET = json.load(open(f'{P}/gfi_v2_retro.json'))
FOC = json.load(open(f'{DATA}/gfi_v2_focos_zona.json'))
NEW = json.load(open(f'{DATA}/gfi_v2_focos_zona_2025_2026.json'))
HIST = json.load(open(f'{P}/historico.json'))
YS = list(range(2012, 2025)); rng = np.random.default_rng(11)

# fuego provincial mensual
fire = defaultdict(dict)   # prov → 'YYYY-MM' → n
for p, zs in FOC.items():
    for z in zs:
        for ym, n in z.items(): fire[p][ym] = fire[p].get(ym, 0) + n
for p, d in NEW['prov_mensual'].items():
    for ym, n in d.items(): fire[p][ym] = fire[p].get(ym, 0) + n
pais_fire = {f'{y}-{m+1:02d}': HIST['ar']['mensual'][str(y)][m] for y in YS for m in range(12)}
pais_fire.update(NEW['pais'])

def mediana_mes(p, m):
    ser = [(fire[p] if p != 'pais' else pais_fire).get(f'{y}-{m:02d}', 0) for y in YS]
    return statistics.median(ser)

rows = []   # (prov, y, m, nivel, driver, focos, mediana, evento)
AMB = {'pais': (RET['riesgo']['pais'], RET['drivers']['pais'])}
AMB.update({p: (RET['riesgo']['provincias'][p], RET['drivers']['provincias'][p]) for p in RET['riesgo']['provincias']})
for p, (anios, drv_p) in AMB.items():
    for ys, s in anios.items():
        y = int(ys)
        for m in range(1, 13):
            lv = s[m - 1]
            if lv == '-': continue
            ym = f'{y}-{m:02d}'
            if ym > '2026-10': continue
            f = (fire[p] if p != 'pais' else pais_fire).get(ym)
            if f is None and y >= 2025: continue
            f = f or 0
            med = mediana_mes(p, m)
            if med < 5 and p != 'pais': continue          # jurisdicciones sin fuego relevante ese mes
            rows.append((p, y, m, lv, drv_p[ys][m - 1], f, med, f >= med and f > 0))

def metr(pred, ev):
    pred = np.array(pred); ev = np.array(ev)
    a = int((pred & ev).sum()); b = int((pred & ~ev).sum()); c = int((~pred & ev).sum()); d = int((~pred & ~ev).sum())
    pod = a / (a + c) if a + c else float('nan'); pofd = b / (b + d) if b + d else float('nan')
    return dict(a=a, b=b, c=c, d=d, rate=(a + b) / len(ev), base=(a + c) / len(ev), prec=(a / (a + b) if a + b else float('nan')), pod=pod, pofd=pofd, pss=pod - pofd)

def resumen(rs, titulo):
    print(f'\n== {titulo}: {len(rs)} provincia-meses ==')
    out = {'n': len(rs), 'por_nivel': {}}
    for lv, nom in (('B', 'BAJO'), ('M', 'MEDIO'), ('A', 'ALTO')):
        sub = [r for r in rs if r[3] == lv]
        if not sub: continue
        ev = np.mean([r[7] for r in sub]); an = statistics.median([r[5] / r[6] if r[6] else float('nan') for r in sub if r[6]])
        share = sum(r[5] for r in sub) / max(1, sum(r[5] for r in rs))
        out['por_nivel'][nom] = dict(n=len(sub), frac_meses=len(sub) / len(rs), tasa_evento=ev, anom_mediana=an, share_fuego=share)
        print(f'  {nom:5}: {len(sub):5} meses ({100*len(sub)/len(rs):4.1f}%) · evento {100*ev:5.1f}% · anomalía mediana {an:.2f} · {100*share:5.1f}% del fuego')
    ev = [r[7] for r in rs]
    MA = metr([r[3] == 'A' for r in rs], ev); MAM = metr([r[3] in 'AM' for r in rs], ev)
    # bloque-año
    anios = sorted(set(r[1] for r in rs)); byY = defaultdict(list)
    for r in rs: byY[r[1]].append(r)
    bs = []
    for _ in range(1000):
        S = [x for y in rng.choice(anios, len(anios), replace=True) for x in byY[y]]
        bs.append(metr([r[3] == 'A' for r in S], [r[7] for r in S])['pss'])
    MA['ci_pss'] = [float(np.nanpercentile(bs, 2.5)), float(np.nanpercentile(bs, 97.5))]
    out['ALTO_vs_resto'] = MA; out['ALTO_o_MEDIO_vs_BAJO'] = MAM
    print(f"  ALTO como predictor: tasa {100*MA['rate']:.1f}% · base {100*MA['base']:.1f}% · precisión {100*MA['prec']:.1f}% · POD {100*MA['pod']:.1f}% · PSS {MA['pss']:.3f} IC [{MA['ci_pss'][0]:.3f}, {MA['ci_pss'][1]:.3f}]")
    print(f"  ALTO∪MEDIO vs BAJO (gate): tasa {100*MAM['rate']:.1f}% · precisión {100*MAM['prec']:.1f}% · POD {100*MAM['pod']:.1f}% · PSS {MAM['pss']:.3f}")
    # por driver dentro de ALTO
    drv = defaultdict(list)
    for r in rs:
        if r[3] == 'A': drv[r[4]].append(r[7])
    out['ALTO_por_driver'] = {k: dict(n=len(v), tasa_evento=float(np.mean(v))) for k, v in drv.items()}
    print('  ALTO por driver (e=ENSO, s=sequía, x=ambos): ' + ' · '.join(f"{k}: n={len(v)} evento {100*np.mean(v):.0f}%" for k, v in sorted(drv.items())))
    return out

R = {}
prov_rows = [r for r in rows if r[0] != 'pais']
R['prov_in_sample'] = resumen([r for r in prov_rows if r[1] <= 2024], 'PROVINCIAS in-sample 2012–2024')
R['prov_oos_2025'] = resumen([r for r in prov_rows if r[1] == 2025], 'PROVINCIAS fuera de muestra 2025')
R['prov_oos_2026'] = resumen([r for r in prov_rows if r[1] == 2026], 'PROVINCIAS fuera de muestra 2026 (ene–oct)')
R['pais_in_sample'] = resumen([r for r in rows if r[0] == 'pais' and r[1] <= 2024], 'PAÍS in-sample 2012–2024')
R['pais_oos'] = resumen([r for r in rows if r[0] == 'pais' and r[1] >= 2025], 'PAÍS fuera de muestra 2025–2026')
# por región (in-sample): el ENSO es regional
REG = {'NEA': ['Misiones', 'Corrientes', 'Entre Ríos', 'Formosa', 'Chaco', 'Santa Fe', 'Santiago del Estero'],
       'NOA': ['Jujuy', 'Salta', 'Tucumán', 'Catamarca', 'La Rioja'],
       'Centro': ['Córdoba', 'San Luis', 'Mendoza', 'San Juan', 'La Pampa', 'Buenos Aires', 'Ciudad Autónoma de Buenos Aires'],
       'Patagonia': ['Neuquén', 'Río Negro', 'Chubut', 'Santa Cruz', 'Tierra del Fuego, Antártida e Islas del Atlántico Sur']}
R['por_region_in_sample'] = {reg: resumen([r for r in prov_rows if r[1] <= 2024 and r[0] in ps], f'{reg} in-sample') for reg, ps in REG.items()}
json.dump(R, open(f'{OUTD}/skill_indice_AR.json', 'w'), indent=1, default=float)
print(f'\n→ {OUTD}/skill_indice_AR.json')
