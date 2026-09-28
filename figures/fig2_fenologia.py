#!/usr/bin/env python3
"""Fig. 2 — Fenología del fuego: share mensual de detecciones VIIRS 2012–2025 por
ámbito, con el umbral del 8% y la ventana propia (meses llenos = dentro de la ventana).
Fuente: datos/fenologia.json (gen_datos_figuras.mjs)."""
from estilo import plt, MM, AZUL, MESES_EN, cargar, guardar

FEN = cargar('fenologia.json')
ORDEN = [('pais', 'Country'), ('NEA', 'NEA'), ('NOA', 'NOA'),
         ('Centro', 'Centro'), ('Patagonia', 'Patagonia')]

fig, axs = plt.subplots(1, 5, figsize=(174 * MM, 42 * MM), sharey=True)
for ax, (k, titulo) in zip(axs, ORDEN):
    d = FEN[k]
    x = range(12)
    dentro = [m in d['ventana'] for m in x]
    ax.bar(x, [100 * s for s in d['shares']],
           color=[AZUL if w else '#b8d4e8' for w in dentro], width=0.72)
    ax.axhline(8, color='#333333', lw=0.8, ls=(0, (4, 2)))
    ax.set_title(f"({chr(97 + list(axs).index(ax))}) {titulo}", loc='left')
    if k == 'pais':
        ax.text(-0.4, 8.7, '8%', fontsize=7, ha='left', color='#333333')
    ax.set_xticks(x)
    ax.set_xticklabels(MESES_EN)
    ax.tick_params(axis='x', length=0)
    ax.text(0.02, 0.93, f"window {int(round(100*d['cobertura']))}% of fire",
            transform=ax.transAxes, fontsize=7, color='#555555')
axs[0].set_ylabel('share of annual detections (%)')
for ax in axs: ax.set_ylim(0, 27.5)
fig.subplots_adjust(wspace=0.08)
guardar(fig, 'fig2_fenologia')
