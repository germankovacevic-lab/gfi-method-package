#!/usr/bin/env python3
"""Paper v2 — término ENSO: factores por fase con IC bootstrap, skill estacional (PSS a nivel año),
sensibilidad de los cortes (0.90 / 1.10 / 1.45) y LOYO. AR e ID con el mismo código.

Método (idéntico a derive_enso_calibracion.mjs / 04_enso.py):
  anomalía = focos del mes / mediana de ese mes calendario del MISMO sensor (med < 5 → excluido)
  MODIS 2001–2011 (base de medianas 2001–2024) + VIIRS 2012–2025 (base 2012–2025), intra-sensor
  factor(fase, lag) = mediana de las anomalías de los meses de la VENTANA del ámbito cuya fase ONI
  'lag' meses antes fue esa fase.

Lo nuevo para v2:
  1. IC95 bootstrap de los factores remuestreando AÑOS DE FUEGO (bloque = año), no meses.
  2. Skill ESTACIONAL del término: por (ámbito, año) la fase ONI al lag operativo en el mes central
     de la ventana → predicción binaria "temporada sobre la mediana" si la fase coincide con la señal
     declarada → PSS/precision sobre 25 temporadas, in-sample y LOYO (signo re-derivado sin el año).
  3. Barrido del corte 'elevado' (f ≥ c) y 'bajo' (f ≤ c'): qué ámbitos cambian de veredicto.

Uso: python3 04_enso_term.py AR | ID
"""
import json, os, sys, statistics, math
import numpy as np
from collections import defaultdict

T = sys.argv[1] if len(sys.argv) > 1 else 'AR'
HOME = os.path.expanduser('~'); G = f'{HOME}/.openclaw/workspace/geofuego'; DATA = f'{HOME}/.openclaw/data'
OUTD = f'{G}/paper/v2/resultados'; os.makedirs(OUTD, exist_ok=True)
rng = np.random.default_rng(11)
MESES = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic']

def parse_oni(path):
    SEAS = {'DJF': 0, 'JFM': 1, 'FMA': 2, 'MAM': 3, 'AMJ': 4, 'MJJ': 5, 'JJA': 6, 'JAS': 7, 'ASO': 8, 'SON': 9, 'OND': 10, 'NDJ': 11}
    oni = {}
    for ln in open(path):
        c = ln.split()
        if len(c) < 4 or c[0] not in SEAS: continue
        oni[(int(c[1]), SEAS[c[0]])] = float(c[3])
    return oni

if T == 'AR':
    S = json.load(open(f'{G}/tools/gfi_v2_paper/series_enso_AR.json'))
    serie = S['serie']                       # sensor → {pais:{y:[12]}, prov:{name|R:reg:{y:[12]}}}
    oni = {}
    for k, v in S['oni'].items():
        y, m = k.split('-'); oni[(int(y), int(m) - 1)] = v
    CAL = json.load(open(f'{G}/tools/gfi_era5_ar/pkg_cds/enso_calibracion.json'))
    AMBITOS = {'pais': lambda s: serie[s]['pais'], **{r: (lambda s, r=r: serie[s]['prov'].get('R:' + r, {})) for r in S['regiones']}}
    SENAL = {a: CAL['senal'][a] for a in AMBITOS}
    MODIS_USO, MODIS_BASE, VIIRS = (2001, 2011), (2001, 2024), (2012, 2025)
elif T == 'ID':
    sys.path.insert(0, f'{G}/tools/gfi_id'); import territorio as TT
    S = json.load(open(f'{DATA}/gfi_id_cache/series.json'))   # sensor → prov → y → [12]
    oni = parse_oni(f'{DATA}/firms_id/oni.ascii.txt')
    CAL = json.load(open(f'{G}/tools/gfi_id/enso_calibracion_id.json'))
    def suma(sensor, provs):
        out = defaultdict(lambda: [0] * 12)
        for p in provs:
            for y, arr in S[sensor].get(p, {}).items():
                for m in range(12): out[y][m] += arr[m]
        return dict(out)
    REG = defaultdict(list)
    for p, (r, _) in TT.PROVINCIAS.items(): REG[r].append(p)
    AMBITOS = {'territorio': lambda s: suma(s, list(TT.PROVINCIAS)), **{r: (lambda s, r=r: suma(s, REG[r])) for r in TT.REGIONES}}
    SENAL = {a: CAL.get('senal', {}).get(a, {'tipo': 'inversa', 'significancia': '?'}) for a in AMBITOS}
    MODIS_USO, MODIS_BASE, VIIRS = (2001, 2011), (2001, 2025), (2012, 2025)
else:
    sys.exit('AR|ID')

VENT = {a: [MESES.index(m) for m in CAL['ventanas'][a]['meses']] for a in AMBITOS}

def fase(v): return None if v is None else ('nino' if v >= 0.5 else 'nina' if v <= -0.5 else 'neutral')
def fase_lag(y, m, lag):
    t = y * 12 + m - lag
    return fase(oni.get((t // 12, t % 12)))

def anomalias(porAnio, base, uso, excluir=None):
    """lista de (y, m, ratio) con medianas intra-sensor (excluyendo 'excluir' de la base si se pide)."""
    out = []
    med = []
    for m in range(12):
        vals = [porAnio[str(y)][m] for y in range(base[0], base[1] + 1) if str(y) in porAnio and y != excluir]
        med.append(statistics.median(vals) if vals else 0)
    for y in range(uso[0], uso[1] + 1):
        if str(y) not in porAnio: continue
        for m in range(12):
            if med[m] < 5: continue
            out.append((y, m, porAnio[str(y)][m] / med[m]))
    return out

def serie_anom(a, excluir=None):
    g = AMBITOS[a]
    return anomalias(g('MODIS'), MODIS_BASE, MODIS_USO, excluir) + anomalias(g('VIIRS'), VIIRS, VIIRS, excluir)

def por_fase(anoms, lag, vent, anios=None):
    g = {'nina': [], 'neutral': [], 'nino': []}
    for (y, m, r) in anoms:
        if m not in vent: continue
        if anios is not None and y not in anios: continue
        f = fase_lag(y, m, lag)
        if f: g[f].append(r)
    return g

def perm_p(A, B, iters=5000):
    a, b = np.log(A), np.log(B)
    if len(a) < 5 or len(b) < 5: return None
    obs = abs(a.mean() - b.mean()); allv = np.r_[a, b]; ext = 0
    for _ in range(iters):
        rng.shuffle(allv)
        if abs(allv[:len(a)].mean() - allv[len(a):].mean()) >= obs: ext += 1
    return ext / iters

med = lambda v: float(np.median(v)) if len(v) else float('nan')
R = {'territorio': T, 'ventanas': {a: [MESES[m] for m in VENT[a]] for a in AMBITOS}, 'ambitos': {}}
LAGS = [0, 3, 6, 9, 12]
print(f'[{T}] término ENSO — ventanas: {R["ventanas"]}')

for a in AMBITOS:
    an = serie_anom(a)
    anios = sorted(set(y for y, m, r in an))
    out = {'senal_declarada': SENAL[a], 'lags': {}}
    for lag in LAGS:
        g = por_fase(an, lag, VENT[a])
        f = {k: med(v) for k, v in g.items()}; n = {k: len(v) for k, v in g.items()}
        # bootstrap bloque-año de los factores y del cociente Niña/Niño
        bf = {'nina': [], 'nino': [], 'neutral': [], 'ratio_nina_nino': []}
        for _ in range(2000):
            ys = set(rng.choice(anios, len(anios), replace=True).tolist())
            # remuestreo con reposición: replicar años → construir lista con multiplicidad
            picks = rng.choice(anios, len(anios), replace=True)
            gg = {'nina': [], 'neutral': [], 'nino': []}
            idx = defaultdict(list)
            for (y, m, r) in an:
                if m in VENT[a]: idx[y].append((m, r))
            for y in picks:
                for (m, r) in idx.get(y, []):
                    ff = fase_lag(y, m, lag)
                    if ff: gg[ff].append(r)
            for k in ('nina', 'nino', 'neutral'): bf[k].append(med(gg[k]) if len(gg[k]) >= 3 else np.nan)
            bf['ratio_nina_nino'].append((med(gg['nina']) / med(gg['nino'])) if len(gg['nina']) >= 3 and len(gg['nino']) >= 3 else np.nan)
        ci = {k: [float(np.nanpercentile(v, 2.5)), float(np.nanpercentile(v, 97.5))] for k, v in bf.items()}
        p_nina = perm_p(g['nina'], g['neutral'] + g['nino']); p_nino = perm_p(g['nino'], g['neutral'] + g['nina'])
        out['lags'][lag] = dict(factor=f, n=n, ci=ci, p_nina_vs_resto=p_nina, p_nino_vs_resto=p_nino)
        if lag in (0, 3):
            print(f"  {a:10} lag{lag}: Niña {f['nina']:.2f} [{ci['nina'][0]:.2f},{ci['nina'][1]:.2f}] n={n['nina']} · neutral {f['neutral']:.2f} · "
                  f"Niño {f['nino']:.2f} [{ci['nino'][0]:.2f},{ci['nino'][1]:.2f}] n={n['nino']} · Niña/Niño {f['nina']/f['nino']:.2f} "
                  f"[{ci['ratio_nina_nino'][0]:.2f},{ci['ratio_nina_nino'][1]:.2f}] · p(Niña) {p_nina} p(Niño) {p_nino}")

    # ── skill ESTACIONAL (nivel año), lag 3 ──
    # temporada = mediana de las anomalías de la ventana en el año y; fase = ONI lag 3 en el mes central de la ventana
    vent = sorted(VENT[a]); mc = vent[len(vent) // 2]
    temporadas = {}
    for y in anios:
        rs = [r for (yy, m, r) in an if yy == y and m in VENT[a]]
        if len(rs) >= max(2, len(vent) // 2):
            temporadas[y] = dict(anom=med(rs), fase=fase_lag(y, mc, 3))
    tipo = SENAL[a].get('tipo')
    match_phase = 'nina' if tipo == 'directa' else 'nino' if tipo == 'inversa' else None
    def pss_bin(pred, ev):
        a_ = sum(p and e for p, e in zip(pred, ev)); b_ = sum(p and not e for p, e in zip(pred, ev))
        c_ = sum((not p) and e for p, e in zip(pred, ev)); d_ = sum((not p) and (not e) for p, e in zip(pred, ev))
        pod = a_ / (a_ + c_) if a_ + c_ else float('nan'); pofd = b_ / (b_ + d_) if b_ + d_ else float('nan')
        return dict(a=a_, b=b_, c=c_, d=d_, pod=pod, pofd=pofd, pss=pod - pofd, prec=(a_ / (a_ + b_) if a_ + b_ else float('nan')))
    ys = sorted(temporadas)
    ev = [temporadas[y]['anom'] > 1 for y in ys]
    sk = None
    if match_phase:
        pred = [temporadas[y]['fase'] == match_phase for y in ys]
        sk = pss_bin(pred, ev)
        # LOYO: el signo (qué fase es la "match") se re-deriva sin el año y
        pred_loyo = []
        for y in ys:
            rest = [yy for yy in ys if yy != y]
            fn = med([temporadas[yy]['anom'] for yy in rest if temporadas[yy]['fase'] == 'nina'])
            fo = med([temporadas[yy]['anom'] for yy in rest if temporadas[yy]['fase'] == 'nino'])
            mp = 'nina' if fn > fo else 'nino'
            pred_loyo.append(temporadas[y]['fase'] == mp)
        sk_loyo = pss_bin(pred_loyo, ev)
        signo_estable = all(((med([temporadas[yy]['anom'] for yy in ys if yy != y and temporadas[yy]['fase'] == 'nina']) >
                              med([temporadas[yy]['anom'] for yy in ys if yy != y and temporadas[yy]['fase'] == 'nino'])) == (tipo == 'directa')) for y in ys)
        out['skill_estacional_lag3'] = dict(n_temporadas=len(ys), fase_match=match_phase, in_sample=sk, loyo=sk_loyo, signo_estable_loyo=signo_estable,
                                           temporadas={str(y): temporadas[y] for y in ys})
        print(f"    → skill estacional ({len(ys)} temporadas, fase {match_phase}): PSS {sk['pss']:.2f} (prec {sk['prec']:.2f}, POD {sk['pod']:.2f}) · LOYO PSS {sk_loyo['pss']:.2f} · signo estable {signo_estable}")
    else:
        out['skill_estacional_lag3'] = dict(n_temporadas=len(ys), fase_match=None, temporadas={str(y): temporadas[y] for y in ys})
        # señal "ninguna": mostrar qué daría cada fase
        for mp in ('nina', 'nino'):
            s2 = pss_bin([temporadas[y]['fase'] == mp for y in ys], ev)
            out['skill_estacional_lag3'][f'si_fuera_{mp}'] = s2
        print(f"    → sin señal declarada; PSS si Niña {out['skill_estacional_lag3']['si_fuera_nina']['pss']:.2f} · si Niño {out['skill_estacional_lag3']['si_fuera_nino']['pss']:.2f}")
    R['ambitos'][a] = out

# ── barrido de cortes (lag 3) ──
print('\nBarrido de cortes sobre el factor de la fase declarada (lag 3):')
cortes = [1.05, 1.10, 1.15, 1.20, 1.25, 1.30, 1.45]
tabla = []
for a in AMBITOS:
    tipo = SENAL[a].get('tipo'); f = R['ambitos'][a]['lags'][3]['factor']; ci = R['ambitos'][a]['lags'][3]['ci']
    fm = f['nina'] if tipo == 'directa' else f['nino'] if tipo == 'inversa' else None
    fc = f['nino'] if tipo == 'directa' else f['nina'] if tipo == 'inversa' else None
    cim = ci['nina'] if tipo == 'directa' else ci['nino'] if tipo == 'inversa' else None
    row = dict(ambito=a, tipo=tipo, f_match=fm, f_contra=fc, ci_match=cim,
               elevado_en={c: (fm is not None and fm >= c) for c in cortes},
               bajo_en={c: (fc is not None and fc <= c) for c in (0.80, 0.85, 0.90, 0.95)},
               ci_excluye_1=(cim is not None and (cim[0] > 1 or cim[1] < 1)))
    tabla.append(row)
    print(f"  {a:10} {str(tipo):8} f_match {fm if fm is None else round(fm,2)} IC {None if cim is None else [round(x,2) for x in cim]} · elevado≥: " +
          ' '.join(f"{c}:{'✓' if row['elevado_en'][c] else '·'}" for c in cortes) + f" · f_contra {fc if fc is None else round(fc,2)}")
R['barrido_cortes'] = tabla
json.dump(R, open(f'{OUTD}/enso_{T}.json', 'w'), indent=1, default=float)

# markdown
L = [f'# Término ENSO — {T}', '', f'Ventanas: {R["ventanas"]}', '',
     '## Factores lag 3 (mediana de anomalías de la ventana; IC95 bootstrap bloque-año)', '',
     '| ámbito | señal | Niña [IC] (n) | neutral | Niño [IC] (n) | Niña/Niño [IC] | p Niña vs resto | p Niño vs resto |', '|---|---|---|---|---|---|---|---|']
for a in AMBITOS:
    o = R['ambitos'][a]['lags'][3]; f, n, ci = o['factor'], o['n'], o['ci']
    L.append(f"| {a} | {SENAL[a].get('tipo')} ({SENAL[a].get('significancia')}) | {f['nina']:.2f} [{ci['nina'][0]:.2f}, {ci['nina'][1]:.2f}] ({n['nina']}) | {f['neutral']:.2f} | "
             f"{f['nino']:.2f} [{ci['nino'][0]:.2f}, {ci['nino'][1]:.2f}] ({n['nino']}) | {f['nina']/f['nino']:.2f} [{ci['ratio_nina_nino'][0]:.2f}, {ci['ratio_nina_nino'][1]:.2f}] | {o['p_nina_vs_resto']} | {o['p_nino_vs_resto']} |")
L += ['', '## Skill estacional (nivel temporada, lag 3): predicción = fase coincide con la señal declarada; evento = temporada sobre la mediana', '',
      '| ámbito | fase | temporadas | a/b/c/d | precisión | POD | PSS | PSS LOYO | signo estable LOYO |', '|---|---|---|---|---|---|---|---|---|']
for a in AMBITOS:
    s = R['ambitos'][a]['skill_estacional_lag3']
    if s.get('in_sample'):
        i, l = s['in_sample'], s['loyo']
        L.append(f"| {a} | {s['fase_match']} | {s['n_temporadas']} | {i['a']}/{i['b']}/{i['c']}/{i['d']} | {i['prec']:.2f} | {i['pod']:.2f} | {i['pss']:.2f} | {l['pss']:.2f} | {s['signo_estable_loyo']} |")
    else:
        L.append(f"| {a} | — (ninguna) | {s['n_temporadas']} | | | | si Niña {s['si_fuera_nina']['pss']:.2f} / si Niño {s['si_fuera_nino']['pss']:.2f} | | |")
L += ['', '## Barrido del corte "elevado" (f_match ≥ c), lag 3', '', '| ámbito | f_match [IC] | ' + ' | '.join(f'≥{c}' for c in cortes) + ' | IC excluye 1 |', '|---|---|' + '---|' * len(cortes) + '---|']
for r in tabla:
    if r['f_match'] is None: continue
    L.append(f"| {r['ambito']} | {r['f_match']:.2f} [{r['ci_match'][0]:.2f}, {r['ci_match'][1]:.2f}] | " + ' | '.join('✓' if r['elevado_en'][c] else '·' for c in cortes) + f" | {'sí' if r['ci_excluye_1'] else 'no'} |")
open(f'{OUTD}/enso_{T}.md', 'w').write('\n'.join(L) + '\n')
print(f'→ {OUTD}/enso_{T}.md')
