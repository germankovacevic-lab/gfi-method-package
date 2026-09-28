#!/usr/bin/env python3
"""Fig. 1 — Las 116 zonas de fuego (centroides, tamaño ∝ peso provincial) sobre las
provincias coloreadas por región ENSO. Fuente: zonas_fuego.json + límites IGN."""
import json, os
from estilo import plt, MM, REGION, cargar, guardar, DATOS, HERE

Z = json.load(open(os.path.join(HERE, '..', 'zenodo_package', 'zonas_fuego.json')))['zonas']
RINGS = cargar('provincias_rings.json')
CAL = json.load(open(os.path.join(HERE, '..', 'zenodo_package', 'enso_calibracion.json')))
P2R = CAL['provincia_region']

fig, ax = plt.subplots(figsize=(100 * MM, 130 * MM))

for p in RINGS:
    reg = P2R.get(p['n'])
    col = REGION.get(reg, '#cccccc')
    for anillo in p['rings']:
        lats = [pt[0] for pt in anillo]
        lons = [pt[1] for pt in anillo]
        ax.fill(lons, lats, color=col, alpha=0.18, lw=0)
        ax.plot(lons + lons[:1], lats + lats[:1], color='#ffffff', lw=0.5, zorder=2)

for prov, zs in Z.items():
    reg = P2R[prov]
    for z in zs:
        ax.scatter(z['lon'], z['lat'], s=8 + 240 * z['peso'], color=REGION[reg],
                   edgecolors='white', linewidths=0.5, zorder=5, alpha=0.95)

# labels directos de región (refuerzo no-cromático)
LBL = {'NOA': (-68.8, -25.0), 'NEA': (-57.5, -26.6), 'Centro': (-69.3, -33.6),
       'Patagonia': (-72.8, -44.5)}
for reg, (x, y) in LBL.items():
    ax.text(x, y, reg, fontsize=9, fontweight='bold', color=REGION[reg],
            ha='center', va='center', zorder=6,
            path_effects=[])

# leyenda de tamaño
for peso, dy in ((0.1, 0), (0.3, 1.4), (0.5, 3.0)):
    ax.scatter(-56.6, -47.5 - dy, s=8 + 240 * peso, color='#777777',
               edgecolors='white', linewidths=0.5)
    ax.text(-55.7, -47.5 - dy, f'{int(peso*100)}%', va='center', fontsize=7)
ax.text(-58.3, -45.6, 'zone weight\n(share of\nprovince fire)', fontsize=7, ha='left')

ax.set_xlim(-74.5, -52.5)
ax.set_ylim(-56, -21)
ax.set_aspect(1.25)
ax.set_xlabel('Longitude (°E)')
ax.set_ylabel('Latitude (°N)')
ax.grid(True, alpha=0.4)
guardar(fig, 'fig1_mapa_zonas')
