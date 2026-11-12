#!/usr/bin/env python3
"""GFI Indonesia — paso 5: término de sequía (umbrales DC por zona) + verificación.

Definiciones IDÉNTICAS a AR (paper §3–4; 06_verificacion.py + 09_loyo_dc.py, calibración 2.2.0):
  DC de zona  = media MÓVIL de 30 días al último día del mes (≥25 días con dato), 2 dec.
  UMBRAL      = 11º menor de las 13 móviles de fin de ese mes calendario 2012–2024 (s[10]);
                DISPARO ⟺ DC > umbral (⟺ percentil ≥ 90, top-2 de 13).
  EVENTO      = focos VIIRS del zona-mes ≥ mediana de los 13 mismos-meses 2012–2024, y > 0.
Agregado respecto de AR: 2025 queda FUERA de la calibración (umbral y mediana del evento
de 2012–2024) → año genuinamente fuera de muestra.

Produce: umbrales_dc.json (acá) + reporte: contingencia, IC95 bloque-año, baseline de
climatología igualada en tasa, lead time, LOYO (algebraico + variantes), 2025 OOS.
Uso: python3 05_sequia.py   (sin red; requiere 01 y 03)
"""
import csv, json, os, random, statistics, sys, datetime as dt
from collections import defaultdict
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import territorio as T

HERE = os.path.dirname(os.path.abspath(__file__))
Z = json.load(open(os.path.join(HERE, 'zonas_fuego.json')))['zonas']
FZ = json.load(open(f'{T.CACHE}/focos_zona.json'))
YS = list(range(2012, 2025))
Y_OOS = 2025


def diario(zid):
    return {r['date']: float(r['dc']) for r in csv.DictReader(open(f'{T.FWI}/fwi_{zid}.csv'))}


def movil_fin(s, a, m):
    fin = dt.date(a + (m == 12), m % 12 + 1, 1) - dt.timedelta(days=1)
    v = [s[k] for k in ((fin - dt.timedelta(days=i)).isoformat() for i in range(30)) if k in s]
    return round(sum(v) / len(v), 2) if len(v) >= 25 else None


def metricas(a, b, c, d):
    n = a + b + c + d
    pod, pofd = a / (a + c), b / (b + d)
    esp = ((a + b) * (a + c) + (c + d) * (b + d)) / n
    return dict(prec=a / (a + b) if a + b else float('nan'), pod=pod, far=b / (a + b) if a + b else float('nan'),
                pofd=pofd, bias=(a + b) / (a + c), pss=pod - pofd, hss=((a + d) - esp) / (n - esp),
                tasa=(a + b) / n, base=(a + c) / n, n=n)


# ── carga ──────────────────────────────────────────────────────────────────────
umbrales, regs, share, mov_all = {}, [], {}, {}
for prov, zs in Z.items():
    for j, z in enumerate(zs):
        zid = f"{z['lat']:.2f}_{z['lon']:.2f}"
        s = diario(zid)
        mov = {(a, m): movil_fin(s, a, m) for a in range(2012, 2027) for m in range(1, 13)}  # 2026: para el hindcast; verificación hasta 2025
        mov_all[zid] = mov
        umb = []
        for m in range(1, 13):
            clim = sorted(mov[(a, m)] for a in YS if mov[(a, m)] is not None)
            if len(clim) != 13:
                sys.exit(f'{zid} mes {m}: climatología incompleta ({len(clim)}/13)')
            umb.append(clim[10])
        umbrales[zid] = {'lat': z['lat'], 'lon': z['lon'], 'provincia': prov, 'region': T.PROVINCIAS[prov][0],
                         'peso': z['peso'], 'umbral_dc_p90': umb}
        foc = FZ[prov][j]
        tot = sum(v for k, v in foc.items() if int(k[:4]) in YS) or 1
        share[(prov, j)] = {m: sum(foc.get(f'{y}-{m:02d}', 0) for y in YS) / tot for m in range(1, 13)}
        med = {m: statistics.median([foc.get(f'{y}-{m:02d}', 0) for y in YS]) for m in range(1, 13)}
        for a in range(2012, 2026):
            for m in range(1, 13):
                v0 = mov[(a, m)]
                if v0 is None:
                    continue
                ev = []
                for k in range(5):
                    t = a * 12 + (m - 1) + k
                    ay, am = t // 12, t % 12 + 1
                    if ay > 2025:
                        ev.append(None); continue
                    v = foc.get(f'{ay}-{am:02d}', 0)
                    ev.append(v >= med[am] and v > 0)
                # LOYO: umbral sin el año (solo en el período de calibración)
                otros = sorted(mov[(y, m)] for y in YS if y != a)
                regs.append(dict(a=a, m=m, prov=prov, j=j, zid=zid, v=v0, dispara=v0 > umb[m - 1],
                                 loyo11=(v0 > otros[10]) if a in YS else None,
                                 loyo10=(v0 > otros[9]) if a in YS else None, ev=ev))

json.dump({'territorio': 'Indonesia — Sumatra + Kalimantan', 'generado': '2026-11-05',
           'regla': 'A-zonal: dc_movil30 > umbral_dc_p90[mes] (11º de 13 móviles a fin de mes 2012–2024) → la provincia sube un escalón',
           'dc': 'Van Wagner, factores ecuatoriales (Le=9, Lf=1.4), ERA5 puro (Copernicus CDS, reanalysis-era5-single-levels-timeseries), mediodía local WIB/WITA',
           'n_zonas': len(umbrales), 'zonas': umbrales},
          open(os.path.join(HERE, 'umbrales_dc.json'), 'w'), indent=1, ensure_ascii=False)


def tabla(rs, key='dispara', lag=0):
    a = sum(1 for r in rs if r[key] and r['ev'][lag]); b = sum(1 for r in rs if r[key] and not r['ev'][lag])
    c = sum(1 for r in rs if not r[key] and r['ev'][lag]); d = sum(1 for r in rs if not r[key] and not r['ev'][lag])
    return a, b, c, d


def linea(nom, M):
    print(f'   {nom}: N={M["n"]} · tasa disparo {100*M["tasa"]:.1f}% · base rate {100*M["base"]:.1f}% · '
          f'precisión {100*M["prec"]:.1f}% · POD {100*M["pod"]:.1f}% · POFD {100*M["pofd"]:.1f}% · PSS {M["pss"]:.3f} · HSS {M["hss"]:.3f}')


cal = [r for r in regs if r['a'] in YS]
oos = [r for r in regs if r['a'] == Y_OOS]
res = {}
print(f'zonas {len(umbrales)} · zona-meses calibración {len(cal)} · 2025 {len(oos)}')

print('\n1) CONTINGENCIA ZONAL 2012–2024 (in-sample)')
a, b, c, d = tabla(cal); M = metricas(a, b, c, d); linea('in-sample', M)
print(f'   a={a} b={b} c={c} d={d}')
res['in_sample'] = M | dict(a=a, b=b, c=c, d=d)

# 2) IC95 bloque-año
random.seed(11)
pa = defaultdict(list)
for r in cal:
    pa[r['a']].append((r['dispara'], r['ev'][0]))
bp, bs = [], []
for _ in range(3000):
    Sm = [x for _ in YS for x in pa[random.choice(YS)]]
    A = sum(1 for x in Sm if x[0] and x[1]); B = sum(1 for x in Sm if x[0] and not x[1])
    C = sum(1 for x in Sm if not x[0] and x[1]); D = sum(1 for x in Sm if not x[0] and not x[1])
    mm = metricas(A, B, C, D); bp.append(100 * mm['prec']); bs.append(mm['pss'])
bp.sort(); bs.sort()
print(f'\n2) IC95 BLOQUE-AÑO  precisión [{bp[74]:.1f}%, {bp[2924]:.1f}%] · PSS [{bs[74]:.3f}, {bs[2924]:.3f}]')
res['ic95'] = dict(prec=[bp[74], bp[2924]], pss=[bs[74], bs[2924]])

# 3) baseline climatología igualada en tasa
k = a + b
rk = sorted(cal, key=lambda r: -share[(r['prov'], r['j'])][r['m']])
sel = set(id(r) for r in rk[:k])
for r in cal:
    r['clim'] = id(r) in sel
M2 = metricas(*tabla(cal, 'clim'))
print('\n3) BASELINE CLIMATOLOGÍA MENSUAL (misma tasa de disparo)'); linea('baseline', M2)
print(f'   >>> sequía {"GANA" if M["pss"] > M2["pss"] else "PIERDE"}: PSS {M["pss"]:.3f} vs {M2["pss"]:.3f}')
res['baseline'] = M2

# 4) lead time
print('\n4) LEAD TIME (precisión por lag, 2012–2024)')
res['lead'] = []
for L in range(5):
    e = [r['ev'][L] for r in cal if r['dispara'] and r['ev'][L] is not None]
    bb = [r['ev'][L] for r in cal if r['ev'][L] is not None]
    pe, pb = 100 * sum(e) / len(e), 100 * sum(bb) / len(bb)
    res['lead'].append(dict(lag=L, prec=pe, base=pb))
    print(f'   +{L}: {len(e)} disparos · precisión {pe:.1f}% · base {pb:.1f}% · {pe-pb:+.1f} pp')

# 5) LOYO
print('\n5) LOYO (umbral sin el año evaluado)')
dif = sum(1 for r in cal if r['loyo11'] != r['dispara'])
print(f'   rango 11-de-12 vs in-sample: {dif} zona-meses difieren (esperado 0 — equivalencia algebraica)')
M3 = metricas(*tabla(cal, 'loyo10')); linea('variante 10-de-12 (más laxa)', M3)
pss_anio = {}
for y in YS:
    ry = [r for r in cal if r['a'] == y]
    A, B, C, D = tabla(ry)
    pss_anio[y] = (A / (A + C) if A + C else 0) - (B / (B + D) if B + D else 0)
pos = sum(1 for v in pss_anio.values() if v > 0)
print(f'   PSS por año > 0 en {pos}/13: ' + ' '.join(f'{y}:{v:.2f}' for y, v in pss_anio.items()))
res['loyo'] = dict(difieren_11de12=dif, variante_10de12=M3, pss_por_anio=pss_anio)

# 6) 2025 fuera de muestra
print('\n6) 2025 FUERA DE MUESTRA (umbrales y evento de 2012–2024)')
A, B, C, D = tabla(oos)
if A + B:
    M4 = metricas(A, B, C, D); linea('2025 OOS', M4); res['oos_2025'] = M4 | dict(a=A, b=B, c=C, d=D)
else:
    print(f'   0 disparos en 2025 (zona-meses {len(oos)}, eventos {A + C})'); res['oos_2025'] = dict(disparos=0, eventos=A + C)

# 7) por región
print('\n7) POR REGIÓN (2012–2024)')
res['region'] = {}
for reg in T.REGIONES:
    rr = [r for r in cal if T.PROVINCIAS[r['prov']][0] == reg]
    MR = metricas(*tabla(rr)); linea(reg, MR); res['region'][reg] = MR

json.dump(res, open(os.path.join(HERE, 'verificacion_sequia.json'), 'w'), indent=1, default=float)
json.dump({zid: {f'{a}-{m:02d}': v for (a, m), v in mov.items() if v is not None} for zid, mov in mov_all.items()},
          open(f'{T.CACHE}/dc_movil_fin_mes.json', 'w'))
