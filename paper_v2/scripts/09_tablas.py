#!/usr/bin/env python3
"""Paper v2 — Tablas 1–3 y Apéndices B/C en Markdown desde los JSON de resultados.
Salida: paper/v2/tablas_apendices.md.  Uso: python3 09_tablas.py"""
import json, os, ast
HOME = os.path.expanduser('~'); G = f'{HOME}/.openclaw/workspace/geofuego'; RES = f'{G}/paper/v2/resultados'
J = lambda p: json.load(open(p))
SA, SI, EA, EI = J(f'{RES}/sensibilidad_AR.json'), J(f'{RES}/sensibilidad_ID.json'), J(f'{RES}/enso_AR.json'), J(f'{RES}/enso_ID.json')
KA, KI, MA, MI = J(f'{RES}/skill_indice_AR.json'), J(f'{RES}/skill_indice_ID.json'), J(f'{RES}/motor_v3_AR.json'), J(f'{RES}/motor_v3_ID.json')
OA = J(f'{RES}/oos_2025_2026_AR.json'); IOD = J(f'{G}/tools/gfi_id/control_iod.json')
NOMB = {'pais': 'Argentina (country)', 'territorio': 'Sumatra + Kalimantan'}
L = ['# Tables and appendices — draft v2', '']
p = lambda v: f'{100*v:.1f}'
# ── Table 1 ──
L += ['## Table 1. Sensitivity of the drought term (ERA5; 2012–2024)', '',
      '**(a) Threshold rank, 30-day window, event = above-median fire.** PSS with 95 % year-block interval; climatology = rate-matched monthly-climatology predictor.', '',
      '| Rank (top-k of 13) | Firing rate (%) | Argentina precision (%) | AR POD (%) | AR PSS [95 % CI] | AR climatology PSS | Indonesia precision (%) | ID POD (%) | ID PSS [95 % CI] | ID climatology PSS |', '|---|---|---|---|---|---|---|---|---|---|']
for a, b in zip(SA['A_rango'], SI['A_rango']):
    L.append(f"| {a['k']} | {p(a['rate'])} | {p(a['prec'])} | {p(a['pod'])} | {a['pss']:.3f} [{a['ci']['pss'][0]:.3f}, {a['ci']['pss'][1]:.3f}] | {a['clim_pss']:.3f} | {p(b['prec'])} | {p(b['pod'])} | {b['pss']:.3f} [{b['ci']['pss'][0]:.3f}, {b['ci']['pss'][1]:.3f}] | {b['clim_pss']:.3f} |")
L += ['', f"Base rates: Argentina {p(SA['A_rango'][0]['base'])} %, Indonesia {p(SI['A_rango'][0]['base'])} %.", '',
      '**(b) Trailing-window length (top-2 of 13).**', '', '| Window (days) | AR PSS [95 % CI] | ID PSS [95 % CI] |', '|---|---|---|']
for a, b in zip(SA['B_ventana'], SI['B_ventana']):
    L.append(f"| {a['W']} | {a['pss']:.3f} [{a['ci']['pss'][0]:.3f}, {a['ci']['pss'][1]:.3f}] | {b['pss']:.3f} [{b['ci']['pss'][0]:.3f}, {b['ci']['pss'][1]:.3f}] |")
g, h = SA['G_efolding_dias'], SI['G_efolding_dias']
L += ['', f"Autocorrelation e-folding lag of the daily DC anomaly: Argentina median {g['mediana']:.0f} d (IQR {g['p25']:.0f}–{g['p75']:.0f}, n = {g['n']} zones); Indonesia {h['mediana']:.0f} d ({h['p25']:.0f}–{h['p75']:.0f}, n = {h['n']}).", '',
      '**(c) Event definition (30 d, top-2 of 13).**', '', '| Event | AR base (%) | AR PSS | ID base (%) | ID PSS |', '|---|---|---|---|---|']
for a, b in zip(SA['C_evento'], SI['C_evento']):
    L.append(f"| fire ≥ {dict(median='median', p75='upper quartile', mean='mean')[a['evento']]} | {p(a['base'])} | {a['pss']:.3f} | {p(b['base'])} | {b['pss']:.3f} |")
L += ['', '**(d) Provincial aggregation (event = above-median provincial fire).**', '', '| Rule | Territory | Firing rate (%) | Precision (%) | POD (%) | PSS [95 % CI] |', '|---|---|---|---|---|---|']
for Sx, t in ((SA, 'AR'), (SI, 'ID')):
    for r in Sx['E_agregacion']:
        if 'top-3' in r['regla'] or 'top-5' in r['regla']: continue
        EN = {'cualquier zona (A-zonal, regla publicada)': 'any zone above its threshold (rule in use)', 'zona dominante sola': 'dominant zone only',
              'media ponderada provincial (top-2/13)': 'weighted provincial mean, top-2 of 13', 'máximo provincial (top-2/13)': 'provincial maximum, top-2 of 13',
              'media ponderada provincial (top-4/13, tasa≈A-zonal)': 'weighted provincial mean, top-4 of 13 (rate matched to any-zone)', 'máximo provincial (top-4/13, tasa≈A-zonal)': 'provincial maximum, top-4 of 13 (rate matched)'}
        L.append(f"| {EN.get(r['regla'], r['regla'])} | {t} | {p(r['rate'])} | {p(r['prec'])} | {p(r['pod'])} | {r['pss']:.3f} [{r['ci']['pss'][0]:.3f}, {r['ci']['pss'][1]:.3f}] |")
L += ['', '**(e) Country-extent threshold (event = above-median national fire).**', '', '| Territory | Best in-sample threshold (PSS) | Two-thirds threshold: months active / hit rate / PSS | LOYO-selected thresholds | LOYO out-of-fold PSS | 2025–2026 PSS with full-sample threshold |', '|---|---|---|---|---|---|']
for Sx, Mx, t in ((SA, MA, 'Argentina'), (SI, MI, 'Indonesia')):
    F = [f for f in Sx['F_pais'] if f['meses']]; best = max(F, key=lambda f: f['pss'] if f['pss'] == f['pss'] else -9)
    N = Sx['provincias']; two = [f for f in F if f['thr'] == -(-2 * N // 3)][0]; pm = Mx['pais']
    L.append(f"| {t} | {best['thr']}/{N} ({best['pss']:.3f}) | {two['meses']} / {p(two['hit'])} % / {two['pss']:.3f} | {sorted(set(pm['umbrales_loyo'].values()))} | {pm['loyo_in_2012_2024']['pss']:.3f} | {pm['oos_2025_2026']['pss']:.3f} ({pm['umbral_elegido_full']}/{N}) |")
# ── Table 2 ──
L += ['', '## Table 2. ENSO term at lag 3 (own fire-season window, 2001–2025)', '',
      '| Region | Window | La Niña factor [95 % CI] (n) | Neutral | El Niño factor [95 % CI] (n) | La Niña / El Niño [95 % CI] | p (La Niña vs rest) | p (El Niño vs rest) | Declared signal (v2 rule) | Seasonal PSS (LOYO) |', '|---|---|---|---|---|---|---|---|---|---|']
for E, Mx, orden in ((EA, MA, ['NOA', 'NEA', 'pais', 'Centro', 'Patagonia']), (EI, MI, ['SUM-S', 'KAL', 'territorio', 'SUM-N'])):
    for a in orden:
        o = E['ambitos'][a]['lags']['3']; f, n, ci = o['factor'], o['n'], o['ci']; s = E['ambitos'][a]['skill_estacional_lag3']
        sig = Mx['senales_v3'][a]['tipo']
        if s.get('in_sample'): sk = f"{s['in_sample']['pss']:.2f} ({s['loyo']['pss']:.2f})"
        else: sk = f"— (La Niña {s['si_fuera_nina']['pss']:.2f} / El Niño {s['si_fuera_nino']['pss']:.2f})"
        L.append(f"| {NOMB.get(a, a)} | {'–'.join(E['ventanas'][a][i] for i in (0, -1))} | {f['nina']:.2f} [{ci['nina'][0]:.2f}, {ci['nina'][1]:.2f}] ({n['nina']}) | {f['neutral']:.2f} | {f['nino']:.2f} [{ci['nino'][0]:.2f}, {ci['nino'][1]:.2f}] ({n['nino']}) | {f['nina']/f['nino']:.2f} [{ci['ratio_nina_nino'][0]:.2f}, {ci['ratio_nina_nino'][1]:.2f}] | {o['p_nina_vs_resto']:.3f} | {o['p_nino_vs_resto']:.3f} | {sig} | {sk} |")
L += ['', 'n = month-observations of the window in each phase. Seasonal PSS: one case per fire season (25), prediction = phase matches the declared signal, event = season anomaly above 1; LOYO re-derives the sign without the evaluated season. Centro window: Jan + Aug–Oct + Dec; SUM-N window: Feb–Mar + Jun–Sep.']
# ── Table 3 ──
L += ['', '## Table 3. Skill of the published level (HIGH vs rest; event = above-median provincial fire)', '',
      '| Territory | Rules | Period | n | HIGH rate (%) | Precision (%) | Base (%) | POD (%) | PSS [95 % CI] | Fire in HIGH months (%) | Event rate in HIGH by driver (ENSO only / drought only / both) |', '|---|---|---|---|---|---|---|---|---|---|---|']
def fila(t, rules, per, d, n_key='n'):
    A = d['ALTO_vs_resto'] if 'ALTO_vs_resto' in d else d['ALTO']; niv = d['por_nivel'] if 'por_nivel' in d else d['niveles']; drv = d['ALTO_por_driver']
    ci = A.get('ci_pss', [float('nan'), float('nan')]); hi = niv.get('ALTO', {})
    dr = ' / '.join(f"{p(drv[k]['tasa_evento'])} ({drv[k]['n']})" if k in drv else '—' for k in ('e', 's', 'x'))
    return f"| {t} | {rules} | {per} | {d['n']} | {p(A['rate'])} | {p(A['prec'])} | {p(A['base'])} | {p(A['pod'])} | {A['pss']:.3f} [{ci[0]:.3f}, {ci[1]:.3f}] | {p(hi.get('share_fuego', 0))} | {dr} |"
for t, K, M in (('Argentina', KA, MA), ('Indonesia', KI, MI)):
    for per, k1, k2 in (('2012–2024 (in sample)', 'prov_in_sample', 'in_sample_2012_2024'), ('2025', 'prov_oos_2025', 'oos_2025'), ('2026 Jan–Oct', 'prov_oos_2026', 'oos_2026')):
        L.append(fila(t, 'first version', per, K[k1])); L.append(fila(t, 'revised (Sect. 3.4)', per, M['v3a'][k2]))
L += ['', 'Bootstrap intervals for single out-of-sample years are degenerate (one year) and are omitted in the text.']
# ── Table 4: unidad regional ──
L += ['', '## Table 4. Verification at the regional level (revised rules)', '',
      '**(a) Regional extent rule.** Prediction = number of drought-escalated provinces of the region reaches the LOYO-selected threshold; event = regional detections at or above the monthly median of 2012–2024.', '',
      '| Region | Provinces | Threshold (LOYO range) | 2012–2024 out-of-fold precision (%) | POD (%) | PSS | 2025–2026 hits / active | 2025–2026 PSS |', '|---|---|---|---|---|---|---|---|']
for Mx, orden in ((MA, ['NOA', 'NEA', 'Centro', 'Patagonia']), (MI, ['SUM-S', 'KAL', 'SUM-N'])):
    for reg in orden:
        e = Mx['v3a']['extension_regional'][reg]; l, o = e['loyo'], e['oos_2025_2026']
        L.append(f"| {reg} | {e['N']} | {e['umbral_full']} ({min(e['umbrales_loyo'])}–{max(e['umbrales_loyo'])}) | {p(l['prec'])} | {p(l['pod'])} | {l['pss']:.3f} | {o['a']} / {o['a']+o['b']} | {o['pss']:.3f} |")
L += ['', '**(b) Published level HIGH at province-month level, by region.** PSS against above-median provincial fire; share = fraction of the period\'s detections falling in HIGH months.', '',
      '| Region | 2012–2024 PSS | precision / base (%) | share of fire in HIGH (%) | 2025 PSS | 2026 PSS | 2025–2026 PSS | 2025–2026 share of fire in HIGH (%) |', '|---|---|---|---|---|---|---|---|']
for Mx, orden in ((MA, ['NOA', 'NEA', 'Centro', 'Patagonia']), (MI, ['SUM-S', 'KAL', 'SUM-N'])):
    for reg in orden:
        r = Mx['v3a']['por_region'][reg]; i = r['in_sample_2012_2024']
        L.append(f"| {reg} | {i['pss']:.3f} | {p(i['prec'])} / {p(i['base'])} | {p(i['share_fuego_en_ALTO'])} | {r['oos_2025']['pss']:.3f} | {r['oos_2026']['pss']:.3f} | {r['oos_2025_2026']['pss']:.3f} | {p(r['oos_2025_2026']['share_fuego_en_ALTO'])} |")
# ── Appendix B ──
L += ['', '## Appendix B. Lag sweep of the ENSO factors', '']
for E, orden, tit in ((EA, ['NOA', 'NEA', 'pais', 'Centro', 'Patagonia'], 'Argentina'), (EI, ['SUM-S', 'KAL', 'territorio', 'SUM-N'], 'Sumatra and Kalimantan')):
    L += [f'**{tit}.** Median window anomaly by phase; ratio = La Niña / El Niño with 95 % year-block interval; p = permutation (5000), uncorrected.', '', '| Region | Lag | La Niña (n) | Neutral (n) | El Niño (n) | Ratio [95 % CI] | p La Niña vs rest | p El Niño vs rest |', '|---|---|---|---|---|---|---|---|']
    for a in orden:
        for lag in ('0', '3', '6', '9', '12'):
            o = E['ambitos'][a]['lags'][lag]; f, n, ci = o['factor'], o['n'], o['ci']['ratio_nina_nino']
            pn = o['p_nina_vs_resto']; po = o['p_nino_vs_resto']
            L.append(f"| {NOMB.get(a, a)} | {lag} | {f['nina']:.2f} ({n['nina']}) | {f['neutral']:.2f} ({n['neutral']}) | {f['nino']:.2f} ({n['nino']}) | {f['nina']/f['nino']:.2f} [{ci[0]:.2f}, {ci[1]:.2f}] | {pn if pn is None else f'{pn:.3f}'} | {po if po is None else f'{po:.3f}'} |")
    L.append('')
# ── Appendix C ──
L += ['## Appendix C. Indian Ocean Dipole control (Indonesia)', '', 'Median Aug–Oct anomaly by ENSO phase and IOD state (IOD+ = DMI ≥ 0.4 °C), same month (lag 0) and three months earlier (lag 3).', '',
      '| Region | Lag | Stratum | Factor | n | Years |', '|---|---|---|---|---|---|']
for a in ('territorio', 'SUM-S', 'KAL', 'SUM-N'):
    if a not in IOD: continue
    for lag in ('lag0', 'lag3'):
        for k, v in IOD[a][lag].items():
            if not isinstance(v, dict): continue
            L.append(f"| {NOMB.get(a, a)} | {lag[-1]} | {k.replace('|', ' / ')} | {v['factor']:.2f} | {v['n']} | {', '.join(str(y) for y in v['anios'])} |")
        extra = {k: v for k, v in IOD[a][lag].items() if not isinstance(v, dict)}
        if extra: L.append(f"| {NOMB.get(a, a)} | {lag[-1]} | *p-values* | {', '.join(f'{k}={v}' for k, v in extra.items())} | | |")
open(f'{G}/paper/v2/tablas_apendices.md', 'w').write('\n'.join(L) + '\n'); print('→ paper/v2/tablas_apendices.md', len(L), 'líneas')
