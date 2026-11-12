#!/usr/bin/env python3
"""Figura resumen GFI Indonesia (preview de Zenodo): zonas de fuego + factores ENSO lag 3 + 2026 observado.
Uso: /opt/homebrew/bin/python3 fig_indonesia.py <salida.png>"""
import json, os, sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MPoly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import territorio as T

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[1]
_ZF = json.load(open(os.path.join(HERE, 'zonas_fuego.json'))); Z, TOT = _ZF['zonas'], _ZF['total_focos']
E = json.load(open(os.path.join(HERE, 'enso_calibracion_id.json')))
X = json.load(open(os.path.join(HERE, 'temporada_2026.json')))
V = json.load(open(os.path.join(HERE, 'verificacion_sequia.json')))
G = json.load(open(os.path.expanduser('~/.openclaw/workspace/geofuego/deploy/indonesia/provincias.json')))
COL = {'SUM-N': '#CC79A7', 'SUM-S': '#E69F00', 'KAL': '#009E73'}
NOM = {'SUM-N': 'North Sumatra region', 'SUM-S': 'South Sumatra region', 'KAL': 'Kalimantan', 'territorio': 'Sumatra + Kalimantan'}
S = json.load(open(f'{T.CACHE}/series.json'))

plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 11})
fig = plt.figure(figsize=(16, 9), dpi=150)
fig.suptitle('The GeoFuego Index (GFI) transferred to Indonesia — Sumatra and Kalimantan', fontsize=19, fontweight='bold', x=0.02, ha='left', y=0.975)
fig.text(0.02, 0.915, 'Same method as Argentina, no tuning: fire zones, seasons, ENSO factors and drought thresholds derived from Indonesia\'s own data '
         '(NASA FIRMS 2001–2026, ONI, ERA5 / Copernicus CDS).', fontsize=11.5, color='#444')

# (a) mapa
ax = fig.add_axes([0.01, 0.10, 0.54, 0.78])
for f in G['features']:
    g, r = f['geometry'], f['properties']['r']
    parts = g['coordinates'] if g['type'] == 'MultiPolygon' else [g['coordinates']]
    for p in parts:
        ax.add_patch(MPoly(p[0], closed=True, fc=COL[r], alpha=0.13, ec=COL[r], lw=0.8))
for prov, zs in Z.items():
    r = T.PROVINCIAS[prov][0]
    for z in zs:
        ax.scatter(z['lon'], z['lat'], s=25 + 900 * z['peso'], c=COL[r], ec='white', lw=0.7, zorder=3)
ax.set_xlim(94.8, 119.6); ax.set_ylim(-6.6, 7.2); ax.set_aspect('equal')
ax.set_xticks([]); ax.set_yticks([])
for s in ax.spines.values(): s.set_color('#ccc')
ax.set_title(f'(a) 75 fire zones from {TOT:,} VIIRS detections (2012–2024)', loc='left', fontsize=12.5)
for r in ('SUM-N', 'SUM-S', 'KAL'):
    ax.scatter([], [], s=80, c=COL[r], label=NOM[r])
ax.legend(loc='lower left', frameon=False, fontsize=10.5)

# (b) factores ENSO lag 3 + 2026 observado
bx = fig.add_axes([0.58, 0.20, 0.40, 0.66])
regs = ['SUM-S', 'KAL', 'territorio', 'SUM-N']
fases = [('nina', 'La Niña', '#56B4E9'), ('neutral', 'neutral', '#9aa3ad'), ('nino', 'El Niño', '#E69F00')]
amb = {'territorio': list(T.PROVINCIAS)} | {r: [p for p in T.PROVINCIAS if T.PROVINCIAS[p][0] == r] for r in T.REGIONES}
for i, a in enumerate(regs):
    b = E['barrido_lags'][a]['lag3']
    for k, (f, lab, c) in enumerate(fases):
        bx.bar(i + (k - 1) * 0.26, b[f]['factor'], 0.25, color=c, label=lab if i == 0 else None)
    # 2026 observado ago–oct
    obs = [x for x in X['region'][a] if x['mes'] in (8, 9, 10)]
    o = sum(x['focos'] for x in obs)
    import statistics
    hist = [sum(sum(S['VIIRS'][p][str(y)][m] for p in amb[a]) for m in (7, 8, 9)) for y in range(2012, 2025)]
    r26 = o / statistics.median(hist)
    bx.scatter(i + 0.26, r26, marker='D', s=70, c='#D55E00', ec='black', zorder=4, label='2026 observed (out of sample)' if i == 0 else None)
    bx.text(i + 0.26, max(b['nino']['factor'], r26) + 0.3, f"{b['nino']['factor']:.1f}×", ha='center', fontsize=10.5, fontweight='bold')
bx.axhline(1, color='#333', lw=0.8, ls='--')
bx.set_xticks(range(len(regs))); bx.set_xticklabels([NOM[a].replace(' region', '\nregion').replace(' + ', ' +\n') for a in regs], fontsize=10)
bx.set_ylabel('Aug–Oct fire / historical median')
bx.set_title('(b) ENSO three months earlier (lag 3), 2001–2025', loc='left', fontsize=12.5)
bx.spines[['top', 'right']].set_visible(False)
bx.legend(frameon=False, fontsize=10, loc='upper right')
fig.text(0.58, 0.045, f"El Niño > La Niña in 25/25 leave-one-year-out folds in every region.\n"
         f"Drought term (zone DC > p90): precision {100*V['in_sample']['prec']:.1f}% vs base rate {100*V['in_sample']['base']:.1f}%,\n"
         f"Peirce skill score {V['in_sample']['pss']:.2f} (2025, out of sample: {V['oos_2025']['pss']:.2f}).", fontsize=10.5, color='#333')
fig.text(0.98, 0.012, 'geofuego.com.ar/indonesia · doi:' + os.environ.get('GFI_DOI', '10.5281/zenodo.23017739') + ' · CC BY 4.0', ha='right', fontsize=9.5, color='#777')
fig.savefig(OUT, facecolor='white')
print(OUT)
