#!/usr/bin/env python3
"""GFI Indonesia — paso 1: asigna focos FIRMS a provincia y deriva las zonas de fuego.

Port 1:1 de geofuego/tools/gfi_v2/01_zonas_fuego.mjs + 05a_focos_por_zona.mjs:
  - filtros VIIRS: confidence != 'l', type == 0 · MODIS: confidence >= 30, type == 0
  - provincia por point-in-polygon (geoBoundaries IDN ADM1, ODbL)
  - grilla 0.25° por provincia (VIIRS 2012–2024) → k-means ponderado k=min(5,celdas),
    DETERMINISTA (init farthest-point ponderado, Lloyd), centroide ponderado a 2 dec.
  - foco → zona = centroide más cercano entre las zonas de SU provincia.

Salidas:
  zonas_fuego.json                         (acá)
  ~/.openclaw/data/gfi_id_cache/series.json   series mensuales por sensor/provincia/año
  ~/.openclaw/data/gfi_id_cache/focos_zona.json  prov → [zona] → 'YYYY-MM' → count (VIIRS 2012–2025)
Uso: /opt/homebrew/bin/python3 01_asigna_y_zonas.py   (numpy + matplotlib)
"""
import csv, json, os, sys
import numpy as np
from matplotlib.path import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import territorio as T

HERE = os.path.dirname(os.path.abspath(__file__))
os.makedirs(T.CACHE, exist_ok=True)

# ---------- polígonos ----------
geo = json.load(open(T.GEO))
PROVS = list(T.PROVINCIAS)
polys = {}  # prov -> [(bbox, Path)]
for f in geo['features']:
    n = f['properties']['shapeName']
    if n not in T.PROVINCIAS:
        continue
    g = f['geometry']
    parts = g['coordinates'] if g['type'] == 'MultiPolygon' else [g['coordinates']]
    lst = []
    for poly in parts:
        ring = np.array(poly[0])  # anillo exterior (lon, lat); islas = partes aparte
        lst.append(((ring[:, 1].min(), ring[:, 0].min(), ring[:, 1].max(), ring[:, 0].max()), Path(ring)))
    polys[n] = lst
faltan = set(PROVS) - set(polys)
if faltan:
    sys.exit(f'provincias sin polígono: {faltan}')


def asignar_prov(lat, lon):
    """vector de índices de provincia (-1 = fuera del territorio)."""
    out = np.full(len(lat), -1, dtype=np.int16)
    pts = np.column_stack([lon, lat])
    for pi, p in enumerate(PROVS):
        for (a, b, c, d), path in polys[p]:
            m = (out == -1) & (lat >= a) & (lat <= c) & (lon >= b) & (lon <= d)
            if not m.any():
                continue
            idx = np.nonzero(m)[0]
            dentro = path.contains_points(pts[idx])
            out[idx[dentro]] = pi
    return out


def leer(sensor, y):
    fn = f'{T.FIRMS}/{"viirs" if sensor == "VIIRS" else "modis"}_{y}.csv'
    lat, lon, mes = [], [], []
    with open(fn) as fh:
        r = csv.reader(fh)
        next(r)
        for c in r:
            if len(c) < 15 or c[14].strip() != '0':
                continue
            if sensor == 'VIIRS':
                if c[9] == 'l':
                    continue
            elif float(c[9]) < 30:
                continue
            lat.append(float(c[0])); lon.append(float(c[1])); mes.append(int(c[5][5:7]))
    return np.array(lat), np.array(lon), np.array(mes, dtype=np.int8)


# ---------- pasada 1: provincia por foco, series mensuales ----------
series = {'VIIRS': {p: {} for p in PROVS}, 'MODIS': {p: {} for p in PROVS}}
viirs_pts = {}  # y -> (lat, lon, mes, prov)
for sensor, (y0, y1) in (('VIIRS', T.VIIRS_ALL), ('MODIS', T.MODIS)):
    for y in range(y0, y1 + 1):
        lat, lon, mes = leer(sensor, y)
        pv = asignar_prov(lat, lon)
        for pi, p in enumerate(PROVS):
            sel = pv == pi
            series[sensor][p][str(y)] = np.bincount(mes[sel] - 1, minlength=12).tolist()
        if sensor == 'VIIRS':
            viirs_pts[y] = (lat, lon, mes, pv)
        print(f'{sensor} {y}: {len(lat)} focos filtrados · {int((pv >= 0).sum())} en el territorio', flush=True)

# ---------- zonas: k-means ponderado determinista (port de 01_zonas_fuego.mjs) ----------
def kmeans_ponderado(cells, k):
    # cells: list of (lat, lon, w) ordenadas por w desc, lat asc, lon asc
    cells = sorted(cells, key=lambda c: (-c[2], c[0], c[1]))
    k = min(k, len(cells))
    d2 = lambda a, b: (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2
    cent = [[cells[0][0], cells[0][1]]]
    while len(cent) < k:
        best, bs = None, -1
        for c in cells:
            sc = c[2] * min(d2(c, ct) for ct in cent)
            if sc > bs:
                bs, best = sc, c
        cent.append([best[0], best[1]])
    assign = [0] * len(cells)
    for _ in range(100):
        changed = False
        for ci, c in enumerate(cells):
            bi, bd = 0, float('inf')
            for g, ct in enumerate(cent):
                d = d2(c, ct)
                if d < bd:
                    bd, bi = d, g
            if assign[ci] != bi:
                assign[ci] = bi; changed = True
        acc = [[0.0, 0.0, 0.0] for _ in cent]
        for ci, c in enumerate(cells):
            a = acc[assign[ci]]
            a[0] += c[0] * c[2]; a[1] += c[1] * c[2]; a[2] += c[2]
        for g in range(len(cent)):
            if acc[g][2] > 0:
                cent[g] = [acc[g][0] / acc[g][2], acc[g][1] / acc[g][2]]
        if not changed:
            break
    out = [[0, 0.0, 0.0] for _ in cent]
    for ci, c in enumerate(cells):
        o = out[assign[ci]]
        o[0] += c[2]; o[1] += c[0] * c[2]; o[2] += c[1] * c[2]
    res = [{'lat': round(o[1] / o[0], 2), 'lon': round(o[2] / o[0], 2), 'n_focos': o[0]} for o in out if o[0] > 0]
    return sorted(res, key=lambda r: -r['n_focos'])


grid = {p: {} for p in PROVS}
tot = {p: 0 for p in PROVS}
for y in range(T.VIIRS_CAL[0], T.VIIRS_CAL[1] + 1):
    lat, lon, mes, pv = viirs_pts[y]
    for pi, p in enumerate(PROVS):
        sel = pv == pi
        ii = np.floor(lat[sel] / T.CELL).astype(int)
        jj = np.floor(lon[sel] / T.CELL).astype(int)
        tot[p] += int(sel.sum())
        for key, cnt in zip(*np.unique(np.column_stack([ii, jj]), axis=0, return_counts=True)) if sel.any() else []:
            k = (int(key[0]), int(key[1]))
            grid[p][k] = grid[p].get(k, 0) + int(cnt)

zonas = {}
print()
for p in PROVS:
    cells = [((i + 0.5) * T.CELL, (j + 0.5) * T.CELL, w) for (i, j), w in grid[p].items()]
    if not cells:
        zonas[p] = []
        continue
    comps = kmeans_ponderado(cells, T.MAX_ZONAS)
    zonas[p] = [{'lat': c['lat'], 'lon': c['lon'], 'peso': round(c['n_focos'] / tot[p], 4), 'n_focos': c['n_focos']} for c in comps]
    print(f'{p} [{T.PROVINCIAS[p][0]}]: {tot[p]} focos → {len(comps)} zonas · ' +
          ' '.join(f"({c['lat']},{c['lon']}) {100 * c['n_focos'] / tot[p]:.0f}%" for c in comps))

json.dump({
    'territorio': 'Indonesia — Sumatra + Kalimantan',
    'fuente': f'NASA FIRMS VIIRS S-NPP {T.VIIRS_CAL[0]}–{T.VIIRS_CAL[1]}, filtros conf!=l & type=0, PIP geoBoundaries IDN ADM1 (ODbL)',
    'metodo': 'grilla 0.25° (ERA5) → k-means ponderado k=5 determinista (init farthest-point) → centroide ponderado (port 1:1 de AR)',
    'total_focos': sum(tot.values()),
    'zonas': zonas,
}, open(os.path.join(HERE, 'zonas_fuego.json'), 'w'), indent=1, ensure_ascii=False)

# ---------- foco → zona (VIIRS 2012–2025) ----------
fz = {p: [{} for _ in zonas[p]] for p in PROVS}
for y in range(T.VIIRS_ALL[0], T.VIIRS_ALL[1] + 1):
    lat, lon, mes, pv = viirs_pts[y]
    for pi, p in enumerate(PROVS):
        if not zonas[p]:
            continue
        sel = pv == pi
        C = np.array([[z['lat'], z['lon']] for z in zonas[p]])
        d = (lat[sel, None] - C[None, :, 0]) ** 2 + (lon[sel, None] - C[None, :, 1]) ** 2
        best = d.argmin(axis=1)
        for j in range(len(zonas[p])):
            cnt = np.bincount(mes[sel][best == j] - 1, minlength=12)
            for m in range(12):
                if cnt[m]:
                    fz[p][j][f'{y}-{m + 1:02d}'] = int(cnt[m])

json.dump(series, open(f'{T.CACHE}/series.json', 'w'))
json.dump(fz, open(f'{T.CACHE}/focos_zona.json', 'w'))
print(f'\nzonas: {sum(len(z) for z in zonas.values())} · total VIIRS cal: {sum(tot.values())}')
