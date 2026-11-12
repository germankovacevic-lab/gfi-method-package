#!/usr/bin/env python3
"""GFI Indonesia — paso 9: arma deploy/indonesia/panel.json (todo lo que el panel muestra).

Solo lee artefactos ya derivados (01–08); no recalcula ciencia. Al front viajan niveles,
factores publicados y conteos agregados — los mismos que van al depósito Zenodo.
Uso: python3 09_panel_data.py
"""
import json, os, statistics, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import territorio as T

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.expanduser('~/.openclaw/workspace/geofuego/deploy/indonesia/panel.json')
J = lambda f: json.load(open(os.path.join(HERE, f)))
Z, E, U, V = J('zonas_fuego.json'), J('enso_calibracion_id.json'), J('umbrales_dc.json'), J('verificacion_sequia.json')
R, I, X = J('gfi_id_retro.json'), J('control_iod.json'), J('temporada_2026.json')
S = json.load(open(f'{T.CACHE}/series.json'))

SEAS = dict(DJF=0, JFM=1, FMA=2, MAM=3, AMJ=4, MJJ=5, JJA=6, JAS=7, ASO=8, SON=9, OND=10, NDJ=11)
oni = {}
for ln in open(f'{T.FIRMS}/oni.ascii.txt'):
    c = ln.split()
    if len(c) == 4 and c[0] in SEAS:
        oni[f'{c[1]}-{SEAS[c[0]] + 1:02d}'] = float(c[3])
dmi = {}
for ln in open(f'{T.FIRMS}/dmi.had.long.data'):
    c = ln.split()
    if len(c) == 13 and c[0].isdigit() and 2000 <= int(c[0]) <= 2026:
        for m in range(12):
            if float(c[m + 1]) > -99:
                dmi[f'{c[0]}-{m + 1:02d}'] = float(c[m + 1])

amb = {'territorio': list(T.PROVINCIAS)} | {r: [p for p in T.PROVINCIAS if T.PROVINCIAS[p][0] == r] for r in T.REGIONES}


def serie(sensor, provs, y0, y1):
    out = {}
    for y in range(y0, y1 + 1):
        out[y] = [sum(S[sensor][p][str(y)][m] for p in provs) for m in range(12)]
    return out


series = {}
for a, ps in amb.items():
    v = serie('VIIRS', ps, 2012, 2025)
    v[2026] = [sum(X['cnt_prov'][p][m] for p in ps) for m in range(12)]
    series[a] = {'modis': serie('MODIS', ps, 2001, 2025), 'viirs': v}

panel = {
    'generado': '2026-11-05',
    'zonas': [{'lat': z['lat'], 'lon': z['lon'], 'prov': p, 'reg': T.PROVINCIAS[p][0], 'peso': z['peso'], 'n': z['n_focos']}
              for p, zs in Z['zonas'].items() for z in zs],
    'total_focos_cal': Z['total_focos'],
    'enso': {a: {'ventana': E['ventanas'][a], 'barrido': {k: {f: v[f]['factor'] for f in ('nina', 'neutral', 'nino')}
                                                          | {'pN': v['p_perm_nino_vs_resto'], 'pÑ': v['p_perm_nina_vs_resto'],
                                                             'n': {f: v[f]['n'] for f in ('nina', 'neutral', 'nino')}}
                                                          for k, v in E['barrido_lags'][a].items()},
                 'loyo': E['loyo_lag3'][a]} for a in amb},
    'sequia': V,
    'iod': I,
    'retro': {'riesgo': R['riesgo'], 'drivers': R['drivers'], 'meta': R['meta']},
    'series': series,
    'oni': oni, 'dmi': dmi,
    't2026': X['region'],
    'provincias': {p: T.PROVINCIAS[p][0] for p in T.PROVINCIAS},
}
json.dump(panel, open(OUT, 'w'), separators=(',', ':'), ensure_ascii=False, default=float)
print(f'{OUT}: {os.path.getsize(OUT) / 1024:.0f} KB')
