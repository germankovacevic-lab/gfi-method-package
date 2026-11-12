#!/usr/bin/env python3
"""Paper v2 — figuras 1–6 (ambos territorios), estilo Okabe-Ito de paper/figures/estilo.py.
Salida: paper/v2/figures/fig{1..6}_*.png/.pdf (300 dpi).  Uso: python3 08_figuras_v2.py"""
import json, os, sys, statistics, ast
import numpy as np
HOME = os.path.expanduser('~'); G = f'{HOME}/.openclaw/workspace/geofuego'; DATA = f'{HOME}/.openclaw/data'
sys.path.insert(0, f'{G}/paper/figures'); sys.path.insert(0, f'{G}/tools/gfi_id')
from estilo import plt, MM, REGION, FASE, MARCA_FASE, NOMBRE_FASE, AZUL, VERMELLON, GRIS, MESES_EN
import territorio as TT
RES = f'{G}/paper/v2/resultados'; OUT = f'{G}/paper/v2/figures'; os.makedirs(OUT, exist_ok=True)
REGION_ID = {'SUM-N': '#CC79A7', 'SUM-S': '#E69F00', 'KAL': '#009E73'}
def guardar(fig, nombre):
    for ext in ('png', 'pdf'): fig.savefig(f'{OUT}/{nombre}.{ext}')
    plt.close(fig); print(nombre, 'OK')
J = lambda p: json.load(open(p))
SA, SI = J(f'{RES}/sensibilidad_AR.json'), J(f'{RES}/sensibilidad_ID.json')
EA, EI = J(f'{RES}/enso_AR.json'), J(f'{RES}/enso_ID.json')

# ── Fig. 1: zonas ────────────────────────────────────────────────────────────
ZA = J(f'{G}/tools/gfi_era5_ar/pkg_cds/zonas_fuego.json')['zonas']; CAL = J(f'{G}/tools/gfi_era5_ar/pkg_cds/enso_calibracion.json'); P2R = CAL['provincia_region']
RINGS = J(f'{G}/paper/figures/datos/provincias_rings.json')
ZI = J(f'{G}/tools/gfi_id/zonas_fuego.json')['zonas']; GI = J(f'{G}/deploy/indonesia/provincias.json')
fig, (ax, bx) = plt.subplots(1, 2, figsize=(174 * MM, 100 * MM), gridspec_kw={'width_ratios': [0.95, 1.45]})
for p in RINGS:
    col = REGION.get(P2R.get(p['n']), '#cccccc')
    for an in p['rings']:
        lats = [q[0] for q in an]; lons = [q[1] for q in an]
        ax.fill(lons, lats, color=col, alpha=0.18, lw=0); ax.plot(lons + lons[:1], lats + lats[:1], color='white', lw=0.4, zorder=2)
for prov, zs in ZA.items():
    for z in zs: ax.scatter(z['lon'], z['lat'], s=6 + 200 * z['peso'], color=REGION[P2R[prov]], edgecolors='white', linewidths=0.4, zorder=5)
BB = dict(boxstyle='round,pad=0.15', fc='white', ec='none', alpha=0.85)
for reg, (x, y) in {'NOA': (-69.5, -24.2), 'NEA': (-55.2, -30.2), 'Centro': (-70.6, -36.0), 'Patagonia': (-72.6, -46.5)}.items():
    ax.text(x, y, reg, fontsize=8, fontweight='bold', color=REGION[reg], ha='center', va='center', zorder=7, bbox=BB)
ax.set_xlim(-74.5, -52.5); ax.set_ylim(-56, -21); ax.set_aspect(1.25); ax.grid(True, alpha=0.4)
ax.set_title('(a) Argentina: 116 fire zones, 2,394,573 detections', loc='left'); ax.set_xlabel('Longitude (°E)'); ax.set_ylabel('Latitude (°N)')
from matplotlib.patches import Polygon as MPoly
for f in GI['features']:
    g, r = f['geometry'], f['properties']['r']
    for part in (g['coordinates'] if g['type'] == 'MultiPolygon' else [g['coordinates']]):
        bx.add_patch(MPoly(part[0], closed=True, fc=REGION_ID[r], alpha=0.18, ec='white', lw=0.4))
for prov, zs in ZI.items():
    for z in zs: bx.scatter(z['lon'], z['lat'], s=6 + 200 * z['peso'], color=REGION_ID[TT.PROVINCIAS[prov][0]], edgecolors='white', linewidths=0.4, zorder=5)
for reg, (x, y) in {'SUM-N': (96.3, 5.2), 'SUM-S': (108.0, -4.8), 'KAL': (113.5, 5.0)}.items():
    bx.text(x, y, reg, fontsize=8, fontweight='bold', color=REGION_ID[reg], ha='center', va='center', zorder=7, bbox=BB)
bx.set_xlim(94.8, 119.6); bx.set_ylim(-6.6, 7.2); bx.set_aspect('equal'); bx.grid(True, alpha=0.4)
bx.set_title('(b) Sumatra and Kalimantan: 75 fire zones, 2,236,596 detections', loc='left'); bx.set_xlabel('Longitude (°E)')
for peso, dx in ((0.1, 0), (0.3, 2.2), (0.5, 4.8)):
    bx.scatter(111.5 + dx, -5.4, s=6 + 200 * peso, color='#777777', edgecolors='white', linewidths=0.4); bx.text(111.5 + dx, -6.3, f'{int(peso*100)}%', ha='center', fontsize=6.5)
bx.text(110.3, -4.3, 'zone weight (share of province fire)', fontsize=6.5)
guardar(fig, 'fig1_zonas')

# ── Fig. 2: fenología ────────────────────────────────────────────────────────
FEN = J(f'{G}/paper/figures/datos/fenologia.json')
S = J(f'{DATA}/gfi_id_cache/series.json')['VIIRS']; EC = J(f'{G}/tools/gfi_id/enso_calibracion_id.json')
MES = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic']
def fen_id(provs):
    tot = np.zeros(12)
    for p in provs:
        for y in range(2012, 2026):
            if str(y) in S[p]: tot += np.array(S[p][str(y)])
    return tot / tot.sum()
amb_id = {'territorio': list(TT.PROVINCIAS)} | {r: [p for p in TT.PROVINCIAS if TT.PROVINCIAS[p][0] == r] for r in TT.REGIONES}
paneles = [('AR', 'pais', 'Argentina'), ('AR', 'NEA', 'NEA'), ('AR', 'NOA', 'NOA'), ('AR', 'Centro', 'Centro'), ('AR', 'Patagonia', 'Patagonia'),
           ('ID', 'territorio', 'Sum. + Kal.'), ('ID', 'SUM-N', 'SUM-N'), ('ID', 'SUM-S', 'SUM-S'), ('ID', 'KAL', 'KAL')]
fig, axs = plt.subplots(2, 5, figsize=(174 * MM, 80 * MM), sharey=True); axs = axs.ravel(); axs[-1].axis('off')
for i, (t, k, tit) in enumerate(paneles):
    ax = axs[i]
    if t == 'AR': sh, vent, cob = FEN[k]['shares'], FEN[k]['ventana'], FEN[k]['cobertura']
    else:
        sh = fen_id(amb_id[k]); vent = [MES.index(m) for m in EC['ventanas'][k]['meses']]; cob = EC['ventanas'][k]['cobertura_fuego']
    col = AZUL if t == 'AR' else '#009E73'
    ax.bar(range(12), [100 * s for s in sh], color=[col if m in vent else ('#b8d4e8' if t == 'AR' else '#b3e0d0') for m in range(12)], width=0.72)
    ax.axhline(8, color='#333333', lw=0.8, ls=(0, (4, 2))); ax.set_title(f'({chr(97+i)}) {tit}', loc='left')
    ax.set_xticks(range(12)); ax.set_xticklabels(MESES_EN); ax.tick_params(axis='x', length=0)
    ax.text(0.02, 0.9, f'window {int(round(100*cob))}% of fire', transform=ax.transAxes, fontsize=6.5, color='#555')
fig.supylabel('share of annual detections (%)', fontsize=8)
for ax in axs[:9]: ax.set_ylim(0, 45)
fig.subplots_adjust(wspace=0.08, hspace=0.45); guardar(fig, 'fig2_fenologia')

# ── Fig. 3: curvas operativas ────────────────────────────────────────────────
fig, axs = plt.subplots(1, 3, figsize=(174 * MM, 55 * MM))
for Sx, lab, col, mk in ((SA, 'Argentina', AZUL, 'o'), (SI, 'Sumatra + Kalimantan', '#009E73', 's')):
    A = Sx['A_rango']
    axs[0].errorbar([a['k'] for a in A], [a['pss'] for a in A], yerr=[[a['pss'] - a['ci']['pss'][0] for a in A], [a['ci']['pss'][1] - a['pss'] for a in A]], color=col, marker=mk, ms=3.5, lw=1, capsize=2, label=lab)
    axs[0].plot([a['k'] for a in A], [a['clim_pss'] for a in A], color=col, ls=':', lw=1)
    axs[1].plot([100 * a['pod'] for a in A], [100 * a['prec'] for a in A], color=col, marker=mk, ms=3.5, lw=1)
    for a in A: axs[1].annotate(str(a['k']), (100 * a['pod'], 100 * a['prec']), textcoords='offset points', xytext=(3, 3), fontsize=6, color=col)
    axs[1].axhline(100 * A[0]['base'], color=col, ls=':', lw=0.8)
    B = Sx['B_ventana']
    axs[2].errorbar([b['W'] for b in B], [b['pss'] for b in B], yerr=[[b['pss'] - b['ci']['pss'][0] for b in B], [b['ci']['pss'][1] - b['pss'] for b in B]], color=col, marker=mk, ms=3.5, lw=1, capsize=2)
axs[0].set_xlabel('threshold rank (top-k of 13 years)'); axs[0].set_ylabel('Peirce skill score'); axs[0].set_title('(a) Threshold rank', loc='left'); axs[0].legend(loc='upper left')
axs[0].axvline(2, color='#999', lw=0.6, ls='--')
axs[1].set_xlabel('probability of detection (%)'); axs[1].set_ylabel('precision (%)'); axs[1].set_title('(b) Precision vs detection', loc='left')
axs[2].set_xlabel('trailing window (days)'); axs[2].set_ylabel('Peirce skill score'); axs[2].set_title('(c) Window length', loc='left'); axs[2].set_xscale('log'); axs[2].set_xticks([7, 15, 30, 60, 90]); axs[2].set_xticklabels(['7', '15', '30', '60', '90'])
axs[2].axvline(30, color='#999', lw=0.6, ls='--')
fig.subplots_adjust(wspace=0.35); guardar(fig, 'fig3_curvas_operativas')

# ── Fig. 4: lead time ────────────────────────────────────────────────────────
fig, (ax, bx) = plt.subplots(1, 2, figsize=(120 * MM, 50 * MM))
for Sx, lab, col, mk in ((SA, 'Argentina', AZUL, 'o'), (SI, 'Sumatra + Kalimantan', '#009E73', 's')):
    D = Sx['D_lead']
    ax.plot([d['lag'] for d in D], [d['pss'] for d in D], color=col, marker=mk, ms=3.5, lw=1, label=lab)
    bx.plot([d['lag'] for d in D], [100 * (d['prec'] - d['base']) for d in D], color=col, marker=mk, ms=3.5, lw=1)
ax.axhline(0, color='#999', lw=0.6); ax.set_xlabel('lead (months)'); ax.set_ylabel('Peirce skill score'); ax.set_title('(a) Skill vs lead', loc='left'); ax.legend(loc='lower left')
bx.axhline(0, color='#999', lw=0.6); bx.set_xlabel('lead (months)'); bx.set_ylabel('precision − base rate (pp)'); bx.set_title('(b) Precision margin vs lead', loc='left')
fig.subplots_adjust(wspace=0.4); guardar(fig, 'fig4_lead')

# ── Fig. 5: factores ENSO con IC (lag 3) + barrido de lags ───────────────────
ordenA = ['NOA', 'NEA', 'pais', 'Centro', 'Patagonia']; ordenI = ['SUM-S', 'KAL', 'territorio', 'SUM-N']
NOMB = {'pais': 'Argentina', 'territorio': 'Sum.+Kal.'}
fig, (ax, bx) = plt.subplots(1, 2, figsize=(174 * MM, 60 * MM), gridspec_kw={'width_ratios': [1.2, 1]})
xs = []; labels = []; i = 0
for E, orden in ((EA, ordenA), (EI, ordenI)):
    for a in orden:
        o = E['ambitos'][a]['lags']['3']
        for k, f in enumerate(('nina', 'neutral', 'nino')):
            x = i + (k - 1) * 0.27; v = o['factor'][f]; ci = o['ci'][f]
            ax.errorbar(x, v, yerr=[[max(0, v - ci[0])], [max(0, ci[1] - v)]], fmt=MARCA_FASE[f], color=FASE[f], ms=4, lw=1, capsize=2, label=NOMBRE_FASE[f] if i == 0 else None)
        xs.append(i); labels.append(NOMB.get(a, a)); i += 1
    i += 0.6
ax.axhline(1, color='#333', lw=0.8, ls='--'); ax.set_yscale('log'); ax.set_yticks([0.25, 0.5, 1, 2, 4, 8, 16]); ax.set_yticklabels(['0.25', '0.5', '1', '2', '4', '8', '16'])
ax.set_xticks(xs); ax.set_xticklabels(labels, rotation=35, ha='right'); ax.set_ylabel('fire-season anomaly (median, lag 3)'); ax.set_title('(a) Factors by phase, lag 3 (95% intervals)', loc='left'); ax.legend(loc='upper left')
# (b) cociente Niña/Niño por lag
for E, orden, cols in ((EA, ordenA, REGION | {'pais': GRIS}), (EI, ordenI, REGION_ID | {'territorio': GRIS})):
    for a in orden:
        L = E['ambitos'][a]['lags']; lags = sorted(int(k) for k in L)
        r = [L[str(l)]['factor']['nina'] / L[str(l)]['factor']['nino'] for l in lags]
        bx.plot(lags, r, marker='o', ms=3, lw=1, color=cols.get(a, GRIS), ls='-' if E is EA else '--', label=NOMB.get(a, a))
bx.axhline(1, color='#333', lw=0.8, ls='--'); bx.set_yscale('log'); bx.set_xlabel('lag (months)'); bx.set_ylabel('La Niña / El Niño factor ratio'); bx.set_title('(b) Phase ratio vs lag', loc='left')
bx.legend(ncol=2, fontsize=5.5, loc='lower right')
fig.subplots_adjust(wspace=0.3, bottom=0.25); guardar(fig, 'fig5_enso')

# ── Fig. 6: regla de extensión REGIONAL 2012–2026 (7 regiones) ───────────────
M3A, M3I = J(f'{RES}/motor_v3_AR.json'), J(f'{RES}/motor_v3_ID.json')
T26 = J(f'{G}/tools/gfi_id/temporada_2026.json')['cnt_prov']; T26 = ast.literal_eval(T26) if isinstance(T26, str) else T26
import csv as _csv, datetime as _dt, statistics as _st
from collections import defaultdict as _dd
# conteo de provincias escaladas por región y fuego regional: recomputar desde focos + umbrales (mismo método que 07)
def regional_series(T):
    if T == 'AR':
        ZON = ZA; FWI = f'{DATA}/gfi_v2_fwi_cds'; REG = P2R
        fire = _dd(dict)
        FOC = J(f'{DATA}/gfi_v2_focos_zona.json'); NEWf = J(f'{DATA}/gfi_v2_focos_zona_2025_2026.json')
        for p_, zs in FOC.items():
            for z in zs:
                for ym, n in z.items(): fire[p_][ym] = fire[p_].get(ym, 0) + n
        for p_, d in NEWf['prov_mensual'].items():
            for ym, n in d.items(): fire[p_][ym] = fire[p_].get(ym, 0) + n
    else:
        ZON = ZI; FWI = f'{DATA}/gfi_id_fwi'; REG = {p_: r for p_, (r, _) in TT.PROVINCIAS.items()}
        fire = _dd(dict); FOC = J(f'{DATA}/gfi_id_cache/focos_zona.json')
        for p_, zs in FOC.items():
            for z in zs:
                for ym, n in z.items(): fire[p_][ym] = fire[p_].get(ym, 0) + n
        for p_, v in T26.items():
            for m in range(10): fire[p_][f'2026-{m+1:02d}'] = v[m]
    def movil(sr, y, m, W=30):
        fin = _dt.date(y + (m == 12), (m % 12) + 1, 1) - _dt.timedelta(days=1)
        v = [sr[k] for k in ((fin - _dt.timedelta(days=i)).isoformat() for i in range(W)) if k in sr]
        return round(sum(v) / len(v), 2) if len(v) >= 25 else None
    disp = _dd(set)
    for p_ in ZON:
        if p_ not in REG: continue
        for z in ZON[p_]:
            sr = {}
            for r in _csv.DictReader(open(f"{FWI}/fwi_{z['lat']:.2f}_{z['lon']:.2f}.csv")): sr[r['date']] = float(r['dc'])
            for m in range(1, 13):
                clim = [movil(sr, y, m) for y in range(2012, 2025)]
                if None in clim: continue
                umb = sorted(clim)[10]
                for y in range(2012, 2027):
                    v = movil(sr, y, m)
                    if v is not None and v > umb: disp[f'{y}-{m:02d}'].add(p_)
    return REG, fire, disp
fig, axs = plt.subplots(7, 1, figsize=(174 * MM, 200 * MM), sharex=True)
k = 0
for T, M3, orden, cols in (('AR', M3A, ['NOA', 'NEA', 'Centro', 'Patagonia'], REGION), ('ID', M3I, ['SUM-S', 'KAL', 'SUM-N'], REGION_ID)):
    REG, fire, disp = regional_series(T)
    yms = [f'{y}-{m:02d}' for y in range(2012, 2027) for m in range(1, 13) if f'{y}-{m:02d}' <= '2026-10']; x = np.arange(len(yms))
    for reg in orden:
        ax = axs[k]; k += 1
        provs = [p_ for p_ in REG if REG[p_] == reg and p_ in fire]; e = M3['v3a']['extension_regional'][reg]; thr = e['umbral_full']; N = e['N']
        rf = _dd(int)
        for p_ in provs:
            for ym, n in fire[p_].items(): rf[ym] += n
        med = {m: _st.median([rf.get(f'{y}-{m:02d}', 0) for y in range(2012, 2025)]) for m in range(1, 13)}
        anom = np.array([rf.get(ym, 0) / max(1, med[int(ym[5:])]) for ym in yms])
        cnt = [sum(1 for p_ in provs if p_ in disp.get(ym, ())) for ym in yms]
        ax.bar(x, cnt, color=[cols[reg] if c >= thr else '#cccccc' for c in cnt], width=1.0)
        ax.axhline(thr, color='#333', lw=0.6, ls='--'); ax.set_ylim(0, N + 0.5); ax.set_yticks([0, thr, N])
        i25 = yms.index('2025-01'); ax.axvspan(i25 - 0.5, len(yms) - 0.5, color='#eeeeee', zorder=0)
        a2 = ax.twinx(); a2.plot(x, anom, color='#333333', lw=0.7); a2.set_yscale('log'); a2.axhline(1, color='#333', lw=0.4, ls=':'); a2.set_yticks([0.1, 1, 10]); a2.set_yticklabels(['0.1', '1', '10'], fontsize=6); a2.spines['top'].set_visible(False)
        o = e['oos_2025_2026']; l = e['loyo']
        ax.set_title(f"({chr(96+k)}) {reg} ({'Argentina' if T == 'AR' else 'Indonesia'}): threshold {thr}/{N} provinces · PSS out-of-fold {l['pss']:.2f} · 2025–26 {o['pss']:.2f} ({o['a']}/{o['a']+o['b']} hits)", loc='left', fontsize=7.5)
        if k == 4: ax.set_ylabel('provinces with drought escalation (bars)   ·   regional detections / monthly median (line)', fontsize=7)
axs[-1].set_xticks([yms.index(f'{y}-01') for y in range(2012, 2027)]); axs[-1].set_xticklabels([str(y) for y in range(2012, 2027)], fontsize=6.5)
fig.subplots_adjust(hspace=0.55); guardar(fig, 'fig6_regla_regional')
