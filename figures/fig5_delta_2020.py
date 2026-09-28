#!/usr/bin/env python3
"""Fig. 5 — Caso Delta del Paraná 2020. (a) DC móvil 30d de la zona sur del Delta de
Entre Ríos vs su umbral mensual (supera desde marzo 2020 — 5 meses antes del pico);
(b) ídem zona frente a Rosario; (c) detecciones mensuales de la zona frente a Rosario
(pico ago-2020: 7.973 vs mediana 78). Fuente: datos/delta_2020.json."""
import datetime as dt
from estilo import plt, MM, AZUL, VERMELLON, GRIS, cargar, guardar

D = cargar('delta_2020.json')
SUR, ROS = '-33.64_-58.69', '-32.88_-60.27'


def eje_dc(ax, zid, titulo):
    d = D[zid]
    x = [dt.date.fromisoformat(f) for f in d['fechas']]
    y = d['dc30']
    # umbral escalonado: el del mes calendario de cada día
    u = [d['umbral'][f.month - 1] for f in x]
    ax.plot(x, y, color=AZUL, lw=1.1, zorder=5)
    ax.step(x, u, color='#333333', lw=0.8, ls=(0, (4, 2)), zorder=4, where='mid')
    ax.fill_between(x, u, y, where=[yy > uu for yy, uu in zip(y, u)],
                    color=VERMELLON, alpha=0.35, lw=0, zorder=3)
    ax.set_ylabel('30-day DC')
    ax.set_title(titulo, loc='left')
    return x


fig, (a, b, c) = plt.subplots(3, 1, figsize=(174 * MM, 105 * MM), sharex=True)
x = eje_dc(a, SUR, '(a) Southern Delta zone (−33.64, −58.69) — 30-day DC vs. monthly threshold')
a.annotate('exceeds from Mar 2020', xy=(dt.date(2020, 3, 31), 392), fontsize=7,
           color=VERMELLON, xytext=(dt.date(2019, 8, 20), 320),
           arrowprops=dict(arrowstyle='-', color=VERMELLON, lw=0.7))
a.text(dt.date(2021, 2, 1), 120, 'monthly threshold (top-2 of 13)', fontsize=6.5, color='#333333')
eje_dc(b, ROS, '(b) Zone opposite Rosario (−32.88, −60.27)')

d = D[ROS]
ymm = [k for k in sorted(d['focos']) if k <= '2021-07']
xm = [dt.date(int(k[:4]), int(k[5:7]), 15) for k in ymm]
vm = [d['focos'][k] for k in ymm]
c.bar(xm, vm, width=22, color=AZUL, log=True)
c.axhline(max(d['mediana_agosto'], 1), color=GRIS, lw=0.8, ls=(0, (4, 2)))
c.text(dt.date(2019, 7, 10), d['mediana_agosto'] * 1.5,
       f"August median 2012–2024: {int(d['mediana_agosto'])}", fontsize=6.5, color=GRIS)
c.annotate('Aug 2020: 7,973', xy=(dt.date(2020, 8, 15), 7973), fontsize=7,
           color='#333333', fontweight='bold', xytext=(dt.date(2020, 10, 15), 6000),
           arrowprops=dict(arrowstyle='-', color='#888888', lw=0.7))
c.set_ylabel('VIIRS detections\n(log scale)')
c.set_ylim(0.8, 20000)
c.set_title('(c) Monthly detections, zone opposite Rosario', loc='left')
c.set_xlim(dt.date(2019, 6, 15), dt.date(2021, 8, 5))

fig.subplots_adjust(hspace=0.35)
guardar(fig, 'fig5_delta_2020')
