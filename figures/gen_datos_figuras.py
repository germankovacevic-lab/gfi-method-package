#!/usr/bin/env python3
"""Figuras NHESS — datos parte 2 (python): lead time, PSS por año (LOYO),
caso Delta 2020 y regla país. Definiciones IDÉNTICAS a 06_verificacion.py /
09_loyo_dc.py (móvil 30d a fin de mes, umbral 2.2.0, evento ≥ mediana y > 0).

Salida: paper/figures/datos/{skill_lead_anio.json, delta_2020.json, regla_pais.json}
Uso: python3 paper/figures/gen_datos_figuras.py   (desde geofuego/, sin red, ~15 s)
"""
import json, csv, statistics, os, datetime as dt
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.join(HERE, '..', 'zenodo_package')
D = os.path.expanduser('~/.openclaw/data/gfi_v2_fwi')
Z = json.load(open(os.path.join(PKG, 'zonas_fuego.json')))['zonas']
CAL = json.load(open(os.path.join(PKG, 'enso_calibracion.json')))
UMB = CAL['v2']['zonas']
FZ = json.load(open(os.path.expanduser('~/.openclaw/data/gfi_v2_focos_zona.json')))
HIST = json.load(open(os.path.join(PKG, 'historico.json')))
YS = list(range(2012, 2025))
MESES = [f'{a}-{m:02d}' for a in YS for m in range(1, 13)]
OUT = os.path.join(HERE, 'datos')
os.makedirs(OUT, exist_ok=True)


def diario(zid, col='dc'):
    out = {}
    for r in csv.DictReader(open(f'{D}/fwi_{zid}.csv')):
        out[r['date']] = float(r[col])
    return out


# ── carga idéntica a 06 ───────────────────────────────────────────────────────
print('leyendo las 116 zonas…')
regs, disp_roll = [], defaultdict(set)
series_cache = {}
for prov, zs in Z.items():
    for j, z in enumerate(zs):
        zid = f"{z['lat']:.2f}_{z['lon']:.2f}"
        s = diario(zid)
        series_cache[zid] = s
        foc = FZ[prov][j]
        umb = UMB[zid]['umbral_dc_p90']
        for m in range(1, 13):
            fila = {}
            for a in YS:
                ult0 = dt.date(a + (m == 12), (m % 12) + 1, 1) - dt.timedelta(days=1)
                v0 = [s[(ult0 - dt.timedelta(days=k)).isoformat()] for k in range(30)
                      if (ult0 - dt.timedelta(days=k)).isoformat() in s]
                if len(v0) >= 25:
                    fila[a] = round(sum(v0) / len(v0), 2)
            for a, mov in fila.items():
                ym = f'{a}-{m:02d}'
                dispara = mov > umb[m - 1]
                # LOYO 11-de-12 (idéntico a 09): umbral sin el año evaluado
                loyo = (len(fila) == 13 and
                        mov > sorted(v for y, v in fila.items() if y != a)[10])
                ev = []
                for k in range(5):
                    t = a * 12 + (m - 1) + k
                    ay, am = t // 12, t % 12 + 1
                    if ay > 2024:
                        ev.append(None); continue
                    ser = [foc.get(f'{y}-{am:02d}', 0) for y in YS]
                    v = foc.get(f'{ay}-{am:02d}', 0)
                    ev.append(v >= statistics.median(ser) and v > 0)
                regs.append((a, m, prov, j, dispara, ev, loyo))
                if dispara:
                    disp_roll[ym].add(prov)

# ── skill: lead time + PSS por año (idéntico a 06 §4 y 09 por-año) ────────────
lead = []
for k in range(5):
    e = [r[5][k] for r in regs if r[4] and r[5][k] is not None]
    bb = [r[5][k] for r in regs if r[5][k] is not None]
    lead.append(dict(lag=k, n=len(e), prec=100 * sum(e) / len(e), base=100 * sum(bb) / len(bb)))

por_anio = []
for Y in YS:
    sub = [(r[6], r[5][0]) for r in regs if r[0] == Y]  # r[6] = disparo LOYO 11-de-12
    a = sum(1 for p, e in sub if p and e); b = sum(1 for p, e in sub if p and not e)
    c = sum(1 for p, e in sub if not p and e); d = sum(1 for p, e in sub if not p and not e)
    pod, pofd = a / (a + c), b / (b + d)
    por_anio.append(dict(anio=Y, disp=a + b, prec=100 * a / (a + b),
                         base=100 * (a + c) / len(sub), pss=pod - pofd))
json.dump(dict(lead=lead, por_anio=por_anio), open(f'{OUT}/skill_lead_anio.json', 'w'), indent=1)
print('skill_lead_anio.json OK')

# ── caso Delta 2020: las dos zonas del Delta de Entre Ríos ────────────────────
# -32.88_-60.27 (frente a Rosario, 33% del fuego provincial; pico ago-2020 = 7.973) y
# -33.64_-58.69 (Delta sur/"sureste": la que dispara desde MARZO 2020 — verificado 28/09,
# es la zona de la anticipación de 5 meses que cita §4)
delta = {}
for zid in ['-32.88_-60.27', '-33.64_-58.69']:
    s = series_cache[zid]
    umb = UMB[zid]['umbral_dc_p90']
    # móvil 30d DIARIA 2019-07-01..2021-06-30
    rolled, fechas = [], []
    d0, d1 = dt.date(2019, 7, 1), dt.date(2021, 6, 30)
    dd = d0
    while dd <= d1:
        v = [s[(dd - dt.timedelta(days=k)).isoformat()] for k in range(30)
             if (dd - dt.timedelta(days=k)).isoformat() in s]
        if len(v) >= 25:
            fechas.append(dd.isoformat()); rolled.append(round(sum(v) / len(v), 2))
        dd += dt.timedelta(days=1)
    prov, j = ('Entre Ríos', [f"{z['lat']:.2f}_{z['lon']:.2f}" for z in Z['Entre Ríos']].index(zid))
    foc = FZ['Entre Ríos'][j]
    focos = {ym: foc.get(ym, 0) for ym in
             [f'{y}-{m:02d}' for y in (2019, 2020, 2021) for m in range(1, 13)]}
    med_agosto = statistics.median([foc.get(f'{y}-08', 0) for y in YS])
    # primer mes-fin ≥2020 con disparo (control de la afirmación de §4)
    primer = next((f'{a}-{m:02d}' for a in (2020, 2021) for m in range(1, 13)
                   for r in [regs] if True
                   and any(rr[0] == a and rr[1] == m and rr[2] == 'Entre Ríos' and rr[3] == j and rr[4]
                           for rr in regs)), None)
    delta[zid] = dict(umbral=umb, fechas=fechas, dc30=rolled, focos=focos,
                      mediana_agosto=med_agosto, primer_disparo_2020=primer, peso=UMB[zid]['peso'])
json.dump(delta, open(f'{OUT}/delta_2020.json', 'w'), indent=1)
print('delta_2020.json OK · primer disparo:',
      {z: delta[z]['primer_disparo_2020'] for z in delta},
      '· ago-2020 focos:', {z: delta[z]['focos']['2020-08'] for z in delta})

# ── regla país: provincias escaladas por mes + fuego país ─────────────────────
ar = HIST['ar']['mensual']
def fuego_pais(ym):
    y, m = int(ym[:4]), int(ym[5:7])
    ser = [ar[str(k)][m - 1] for k in YS if str(k) in ar]
    return ar[str(y)][m - 1], statistics.median(ser)
rp = []
for ym in MESES:
    f, med = fuego_pais(ym)
    rp.append(dict(ym=ym, n_prov=len(disp_roll.get(ym, ())), focos=f, mediana_mes=med))
json.dump(rp, open(f'{OUT}/regla_pais.json', 'w'), indent=1)
act = [r for r in rp if r['n_prov'] >= 16]
print(f'regla_pais.json OK · activos ≥16: {len(act)} · todos ≥ mediana:',
      all(r['focos'] >= r['mediana_mes'] for r in act))
