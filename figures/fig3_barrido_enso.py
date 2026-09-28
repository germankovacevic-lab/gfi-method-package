#!/usr/bin/env python3
"""Fig. 3 — El término ENSO: mediana de anomalía estacional por fase y lag, con IC95
bootstrap (nominal: autocorrelación intra-episodio, §6.1c), cada ámbito en SU ventana.
Es el Apéndice A en visual. Fuente: datos/barrido_ci.json (gen_datos_figuras.mjs)."""
from estilo import plt, MM, FASE, MARCA_FASE, NOMBRE_FASE, cargar, guardar

B = cargar('barrido_ci.json')
ORDEN = [('pais', 'Country\nJul–Oct'), ('NEA', 'NEA\nJul–Oct'), ('NOA', 'NOA\nAug–Nov'),
         ('Centro', 'Centro\nJan, Aug–Oct, Dec'), ('Patagonia', 'Patagonia\nDec–Mar')]
LAGS = [0, 3, 6, 9, 12]
OFF = {'nina': -0.7, 'neutral': 0.0, 'nino': 0.7}

fig, axs = plt.subplots(1, 5, figsize=(174 * MM, 52 * MM), sharey=True)
for i, (ax, (k, titulo)) in enumerate(zip(axs, ORDEN)):
    d = B[k]['lags']
    ax.axhline(1.0, color='#bbbbbb', lw=0.7, zorder=1)
    ax.axvline(3, color='#eeeeee', lw=6, zorder=0)
    for f in ('nina', 'neutral', 'nino'):
        xs = [lag + OFF[f] for lag in LAGS]
        ys = [d[str(lag)][f]['factor'] for lag in LAGS]
        lo = [d[str(lag)][f]['ci95'][0] for lag in LAGS]
        hi = [d[str(lag)][f]['ci95'][1] for lag in LAGS]
        ax.errorbar(xs, ys, yerr=[[y - l for y, l in zip(ys, lo)],
                                  [h - y for y, h in zip(ys, hi)]],
                    fmt=MARCA_FASE[f], color=FASE[f], ms=3.5, lw=0,
                    elinewidth=0.8, capsize=1.5, zorder=5,
                    label=NOMBRE_FASE[f] if i == 2 else None)
    ax.set_title(f'({chr(97 + i)}) {titulo}', loc='left', fontsize=7.5)
    ax.set_xticks(LAGS)
    ax.set_xlabel('lag (months)')
    ax.set_ylim(0.35, 2.35)
axs[0].set_ylabel('seasonal anomaly factor\n(median, 95% bootstrap CI)')
axs[2].legend(loc='upper right', handletextpad=0.2, borderaxespad=0.1, ncols=1)
axs[0].text(3, 0.44, 'operational\nlag', fontsize=6.5, ha='center', color='#888888')
fig.subplots_adjust(wspace=0.08)
guardar(fig, 'fig3_barrido_enso')
