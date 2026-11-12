#!/usr/bin/env python3
"""GFI Indonesia — paso 8: temporada 2026 = test FUERA DE MUESTRA para ambos términos.

Fuente: FIRMS area API, VIIRS S-NPP — SP (científico) hasta 2026-07-31, NRT desde 2026-08-01
(bbox 95,-6.5,119.5,7.5; viirs_2026_area.csv). Mismos filtros que el archivo (conf != 'l').
El NRT no trae la columna 'type' → las fuentes fijas (antorchas de gas, volcanes, industria)
se quitan con una MÁSCARA derivada del archivo SP 2012–2025: celdas de 0.01° con alguna
detección type ≠ 0. Se reporta cuánto quita la máscara y cuánto quitaría en un año SP
(control: la máscara aplicada al SP 2025 vs el filtro type==0 oficial).
Nada de 2026 entró en ninguna calibración (ENSO hasta 2025, DC hasta 2024).
Uso: /opt/homebrew/bin/python3 08_temporada_2026.py
"""
import csv, json, os, statistics, sys
import numpy as np
from matplotlib.path import Path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import territorio as T

HERE = os.path.dirname(os.path.abspath(__file__))
S = json.load(open(f'{T.CACHE}/series.json'))
_rp = os.path.join(HERE, 'gfi_id_retro.json')
RETRO = json.load(open(_rp)) if os.path.exists(_rp) else None
PROVS = list(T.PROVINCIAS)
geo = json.load(open(T.GEO))
polys = {}
for f in geo['features']:
    n = f['properties']['shapeName']
    if n in T.PROVINCIAS:
        g = f['geometry']
        parts = g['coordinates'] if g['type'] == 'MultiPolygon' else [g['coordinates']]
        polys[n] = [((np.array(p[0])[:, 1].min(), np.array(p[0])[:, 0].min(), np.array(p[0])[:, 1].max(), np.array(p[0])[:, 0].max()), Path(np.array(p[0]))) for p in parts]


def asignar(lat, lon):
    out = np.full(len(lat), -1, dtype=np.int16)
    pts = np.column_stack([lon, lat])
    for pi, p in enumerate(PROVS):
        for (a, b, c, d), path in polys[p]:
            m = (out == -1) & (lat >= a) & (lat <= c) & (lon >= b) & (lon <= d)
            if m.any():
                idx = np.nonzero(m)[0]
                out[idx[path.contains_points(pts[idx])]] = pi
    return out


# máscara de fuentes fijas (SP 2012–2025, type != 0, celdas 0.01°)
estat = set()
for y in range(2012, 2026):
    with open(f'{T.FIRMS}/viirs_{y}.csv') as fh:
        r = csv.reader(fh); next(r)
        for c in r:
            if len(c) >= 15 and c[14].strip() not in ('0', ''):
                estat.add((round(float(c[0]), 2), round(float(c[1]), 2)))
celda = lambda la, lo: (round(la, 2), round(lo, 2))
print(f'máscara de fuentes fijas: {len(estat)} celdas de 0.01°')

# control de la máscara sobre SP 2025: type==0 oficial vs máscara
of = ms = 0
with open(f'{T.FIRMS}/viirs_2025.csv') as fh:
    r = csv.reader(fh); next(r)
    for c in r:
        if len(c) < 15 or c[9] == 'l':
            continue
        of += c[14].strip() == '0'
        ms += celda(float(c[0]), float(c[1])) not in estat
print(f'control SP 2025 (todo Indonesia): type==0 oficial {of} · máscara {ms} ({100*(ms-of)/of:+.1f}%)')

# 2026
raw = open(f'{T.FIRMS}/viirs_2026_area.csv').read()
raw = raw.replace('VIIRS_SNPP_SP', 'VIIRS_SNPP_SP\n').replace('VIIRS_SNPP_NRT', 'VIIRS_SNPP_NRT\n')
lat, lon, mes, quit_ = [], [], [], 0
for ln in raw.splitlines():
    c = ln.split(',')
    if len(c) < 15 or c[0] == 'latitude' or c[9] == 'l':
        continue
    src = c[-1]
    if src == 'VIIRS_SNPP_SP' and c[14].strip() != '0':
        continue
    if src == 'VIIRS_SNPP_NRT' and celda(float(c[0]), float(c[1])) in estat:
        quit_ += 1
        continue
    lat.append(float(c[0])); lon.append(float(c[1])); mes.append(int(c[5][5:7]))
lat, lon, mes = np.array(lat), np.array(lon), np.array(mes)
pv = asignar(lat, lon)
print(f'2026: {len(lat)} detecciones filtradas en bbox · {int((pv >= 0).sum())} en el territorio · NRT quitadas por máscara: {quit_}')

cnt = {p: np.bincount(mes[pv == i] - 1, minlength=12).tolist() for i, p in enumerate(PROVS)}
ULTMES = 10  # octubre completo; noviembre parcial (NRT hasta el 02/11)


def agrega(provs, sensor_ser):
    out = {}
    for p in provs:
        for y, arr in sensor_ser[p].items():
            acc = out.setdefault(int(y), [0] * 12)
            for m in range(12):
                acc[m] += arr[m]
    return out


res = {'fuente': 'FIRMS VIIRS S-NPP SP (≤2026-07-31) + NRT (≥2026-08-01), conf!=l; NRT sin type → máscara de fuentes fijas SP 2012–2025',
       'meses': {}, 'region': {}}
amb = {'territorio': PROVS} | {r: [p for p in PROVS if T.PROVINCIAS[p][0] == r] for r in T.REGIONES}
print('\nfuego 2026 vs mediana 2012–2024 del mismo mes (ratio) · nivel GFI del hindcast:')
for a, ps in amb.items():
    hist = agrega(ps, S['VIIRS'])
    c26 = [sum(cnt[p][m] for p in ps) for m in range(12)]
    filas = []
    for m in range(ULTMES):
        med = statistics.median(hist[y][m] for y in range(2012, 2025))
        rk = sum(1 for y in range(2012, 2026) if hist[y][m] < c26[m]) + 1
        rk = 15 - rk + 1  # 1 = el mayor de 15 años
        filas.append({'mes': m + 1, 'focos': c26[m], 'mediana': med, 'ratio': round(c26[m] / med, 2) if med else None, 'rank_de_15': rk})
    res['region'][a] = filas
    ago_oct = sum(c26[7:10]); med_ao = statistics.median(sum(hist[y][7:10]) for y in range(2012, 2025))
    print(f'\n  {a}: ago–oct 2026 = {ago_oct} focos vs mediana {med_ao:.0f} → {ago_oct/med_ao:.2f}× · '
          f'años anteriores ago–oct: ' + ' '.join(f'{y}:{sum(hist[y][7:10])}' for y in range(2012, 2026)))
    for f in filas[6:]:
        print(f"    {f['mes']:02d}: {f['focos']:6d} · mediana {f['mediana']:7.0f} · ratio {f['ratio']} · puesto {f['rank_de_15']}/15")
res['cnt_prov'] = cnt
print('\n  nivel GFI 2026 (hindcast, ene→dic) por provincia:')
for p in (PROVS if RETRO else []):
    print(f'    {p:<24} {RETRO["riesgo"][p]["2026"]}  {RETRO["drivers"][p]["2026"]}  · ago–oct focos {sum(cnt[p][7:10])}')
json.dump(res, open(os.path.join(HERE, 'temporada_2026.json'), 'w'), indent=1, default=float)
