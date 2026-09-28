#!/usr/bin/env python3
"""Fig. 4 — Skill del término de sequía. (a) precisión vs lead time contra la base;
(b) PSS por año bajo leave-one-year-out (cada año contra umbrales derivados sin él).
Fuente: datos/skill_lead_anio.json (gen_datos_figuras.py, definiciones de 06/09)."""
from estilo import plt, MM, AZUL, GRIS, cargar, guardar

D = cargar('skill_lead_anio.json')

fig, (a, b) = plt.subplots(1, 2, figsize=(174 * MM, 55 * MM))

# (a) lead time
lags = [r['lag'] for r in D['lead']]
prec = [r['prec'] for r in D['lead']]
base = [r['base'] for r in D['lead']]
a.plot(lags, prec, '-o', color=AZUL, ms=4, lw=1.4, zorder=5)
a.plot(lags, base, '-s', color=GRIS, ms=3.5, lw=1.1, zorder=4)
a.text(0.9, 61.5, 'precision', color=AZUL, ha='center', fontsize=8)
a.text(2, 51.2, 'base rate', color=GRIS, ha='center', fontsize=8)
for x, p, bs in zip(lags, prec, base):
    dx = -2 if x == lags[-1] else 10
    a.annotate(f'+{p - bs:.1f} pp', (x, p), textcoords='offset points',
               xytext=(dx, 7), ha='center', fontsize=6.5, color='#555555')
a.set_xticks(lags)
a.set_xticklabels([f'+{k}' for k in lags])
a.set_xlabel('lead (months)')
a.set_ylabel('precision (%)')
a.set_ylim(45, 82)
a.set_title('(a) Skill vs. lead time', loc='left')

# (b) PSS por año LOYO
anios = [r['anio'] for r in D['por_anio']]
pss = [r['pss'] for r in D['por_anio']]
b.bar(anios, pss, color=AZUL, width=0.72)
b.axhline(0, color='#333333', lw=0.7)
for x, y in zip(anios, pss):
    b.annotate(f'{y:.3f}'.replace('0.', '.'), (x, y), textcoords='offset points',
               xytext=(0, 2), ha='center', fontsize=6, color='#555555')
b.set_xticks(anios)
b.set_xticklabels(anios, rotation=45)
b.set_ylabel('Peirce skill score (LOYO)')
b.set_ylim(0, 0.23)
b.set_title('(b) Leave-one-year-out skill by year', loc='left')

fig.subplots_adjust(wspace=0.25)
guardar(fig, 'fig4_skill')
