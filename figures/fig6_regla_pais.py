#!/usr/bin/env python3
"""Fig. 6 — Regla país 2012–2024. (a) provincias con escalada de sequía por mes vs el
umbral de ⅔ (≥16/24): 18 meses activos, todos con fuego país ≥ mediana; (b) detecciones
país mensuales (log) con los meses activos marcados. Fuente: datos/regla_pais.json."""
import datetime as dt
from estilo import plt, MM, AZUL, VERMELLON, GRIS, cargar, guardar

R = cargar('regla_pais.json')
x = [dt.date(int(r['ym'][:4]), int(r['ym'][5:7]), 15) for r in R]
n = [r['n_prov'] for r in R]
f = [r['focos'] for r in R]
act = [r['n_prov'] >= 16 for r in R]

fig, (a, b) = plt.subplots(2, 1, figsize=(174 * MM, 80 * MM), sharex=True)

a.bar(x, n, width=26, color=[VERMELLON if s else '#b8d4e8' for s in act])
a.axhline(16, color='#333333', lw=0.8, ls=(0, (4, 2)))
a.text(dt.date(2012, 2, 1), 16.6, '≥ 16 of 24 (two-thirds rule)', fontsize=7, color='#333333')
a.set_ylabel('provinces with\ndrought escalation')
a.set_ylim(0, 24)
a.set_title('(a) Extent of drought escalation — 18 active months in 156, all with country fire ≥ median', loc='left')

b.plot(x, f, color=AZUL, lw=0.9, zorder=4)
for xi, fi, s in zip(x, f, act):
    if s:
        b.scatter(xi, fi, s=14, color=VERMELLON, zorder=6, edgecolors='white', linewidths=0.4)
b.scatter([], [], s=14, color=VERMELLON, edgecolors='white', linewidths=0.4,
          label='country-extent rule active')
b.set_yscale('log')
b.set_ylabel('country VIIRS detections\n(log scale)')
b.legend(loc='lower left')
b.set_title('(b) Observed country fire activity', loc='left')
b.set_xlim(dt.date(2011, 11, 1), dt.date(2025, 2, 1))

fig.subplots_adjust(hspace=0.3)
guardar(fig, 'fig6_regla_pais')
