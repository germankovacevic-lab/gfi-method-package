#!/usr/bin/env python3
"""Paper v2 (NHESS resubmit) — sensibilidad del término de sequía (DC) a cada regla declarada.

Responde a la crítica del editor (12/11/2026): "classification scheme and regional adjustment
criteria rely on rules that lack physical grounding, theoretical justification, or empirical
evidence". Aquí cada regla se barre y se mide con las MISMAS métricas (Jolliffe & Stephenson 2012):
precision (success ratio), POD, POFD, bias, Peirce skill score (PSS = POD − POFD), HSS; IC95 por
bootstrap de bloque-año; baseline de climatología mensual igualada en tasa de disparo.

Meteorología: ERA5 PURO (Copernicus CDS), en ambos territorios.

Barridos:
  A. Rango del umbral  (top-k de 13, k = 1..6; k = 2 es la regla "p90" publicada) → curva operativa
  B. Ventana de la media móvil (7, 15, 30, 45, 60, 90 días; umbrales re-derivados por ventana)
  C. Definición del evento (fuego ≥ mediana · ≥ p75 · ≥ media de los 13 mismos-meses)
  D. Lead time 0..4 meses (precision, POD, PSS)
  E. Agregación provincial: cualquier zona (A-zonal) · zona dominante · media ponderada · máximo
  F. Regla país: umbral de extensión n/N provincias (todas) → meses activos, aciertos, PSS país
  G. Memoria del DC: autocorrelación de la anomalía diaria → tiempo de e-folding por zona (base física
     de la ventana de 30 días y de la escala "estacional")

Uso:  python3 01_sensibilidad_sequia.py AR | ID
Salida: paper/v2/resultados/sensibilidad_<T>.json + .md
"""
import json, csv, os, sys, statistics, datetime as dt, math, random
from collections import defaultdict
import numpy as np

T = sys.argv[1] if len(sys.argv) > 1 else 'AR'
HOME = os.path.expanduser('~')
G = f'{HOME}/.openclaw/workspace/geofuego'
DATA = f'{HOME}/.openclaw/data'
OUTD = f'{G}/paper/v2/resultados'
os.makedirs(OUTD, exist_ok=True)

if T == 'AR':
    ZON = json.load(open(f'{G}/tools/gfi_era5_ar/pkg_cds/zonas_fuego.json'))['zonas']
    FOC = json.load(open(f'{DATA}/gfi_v2_focos_zona.json'))
    FWI = f'{DATA}/gfi_v2_fwi_cds'
    HIST = json.load(open(f'{G}/tools/gfi_era5_ar/pkg_cds/historico.json'))
    pais_mensual = {int(y): v for y, v in HIST['ar']['mensual'].items()}
    EXCL_PROV = set()
elif T == 'ID':
    ZON = json.load(open(f'{G}/tools/gfi_id/zonas_fuego.json'))['zonas']
    FOC = json.load(open(f'{DATA}/gfi_id_cache/focos_zona.json'))
    FWI = f'{DATA}/gfi_id_fwi'
    pais_mensual = None
    EXCL_PROV = set()
else:
    sys.exit('territorio AR|ID')

YS = list(range(2012, 2025))          # calibración (13 años)
NY = len(YS)
PROVS = [p for p in ZON if p not in EXCL_PROV]
N_PROV = len(PROVS)
random.seed(11); rng = np.random.default_rng(11)

# ───────────────────────── carga de series diarias de DC ─────────────────────────
def zid(z): return f"{z['lat']:.2f}_{z['lon']:.2f}"

print(f'[{T}] leyendo DC diario de {sum(len(v) for v in ZON.values())} zonas…', flush=True)
D0 = dt.date(2011, 12, 1)
def didx(d): return (d - D0).days
NDAYS = didx(dt.date(2026, 12, 31)) + 1
dc_daily = {}   # zid -> np.array (nan donde falta)
for p in PROVS:
    for z in ZON[p]:
        arr = np.full(NDAYS, np.nan)
        with open(f'{FWI}/fwi_{zid(z)}.csv') as fh:
            for r in csv.DictReader(fh):
                d = dt.date.fromisoformat(r['date'])
                if d >= D0:
                    arr[didx(d)] = float(r['dc'])
        dc_daily[zid(z)] = arr

def month_end(y, m):
    return dt.date(y + (m == 12), (m % 12) + 1, 1) - dt.timedelta(days=1)

def trailing_mean(arr, end, W, min_frac=25/30):
    i = didx(end)
    seg = arr[i - W + 1:i + 1]
    ok = seg[~np.isnan(seg)]
    if len(ok) < max(1, int(round(W * min_frac))):
        return None
    return round(float(ok.mean()), 2)

# zone-month table: for each zone, for each (y,m): DC statistic per window, fire counts
zones = []  # list of dict(prov, j, zid, peso, foc{ym:n})
for p in PROVS:
    for j, z in enumerate(ZON[p]):
        zones.append(dict(prov=p, j=j, zid=zid(z), peso=z.get('peso', 1.0), foc=FOC[p][j]))
NZ = len(zones)
print(f'[{T}] {NZ} zonas · {N_PROV} provincias', flush=True)

WINDOWS = [7, 15, 30, 45, 60, 90]
# stat[W][zi, yi, m-1] = trailing mean at month end (nan if missing)
stat = {W: np.full((NZ, NY, 12), np.nan) for W in WINDOWS}
fire = np.zeros((NZ, NY, 12))
for zi, z in enumerate(zones):
    arr = dc_daily[z['zid']]
    for yi, y in enumerate(YS):
        for m in range(1, 13):
            fire[zi, yi, m - 1] = z['foc'].get(f'{y}-{m:02d}', 0)
            e = month_end(y, m)
            for W in WINDOWS:
                v = trailing_mean(arr, e, W)
                if v is not None:
                    stat[W][zi, yi, m - 1] = v

# ───────────────────────── eventos ─────────────────────────
def event_matrix(kind='median', fire=fire):
    """ev[zi,yi,m] bool: fuego del zona-mes ≥ estadístico de los 13 mismos-meses, y > 0."""
    ev = np.zeros_like(fire, dtype=bool)
    for zi in range(NZ):
        for m in range(12):
            s = fire[zi, :, m]
            if kind == 'median':
                thr = np.median(s)
            elif kind == 'p75':
                thr = np.sort(s)[9]            # 10º menor de 13 ≈ top-4
            elif kind == 'mean':
                thr = s.mean()
            ev[zi, :, m] = (s >= thr) & (s > 0)
    return ev

EV = {k: event_matrix(k) for k in ('median', 'p75', 'mean')}

# ───────────────────────── disparos por rango (leave-nothing-out) ─────────────────────────
def fire_rank(S, k):
    """dispara si el valor supera al menos (13-k) de los OTROS 12 → top-k de 13 (k=2: regla publicada).
    Equivale (06_verificacion) a v > (13-k)º menor de los 13 (con v incluido)."""
    disp = np.zeros_like(S, dtype=bool)
    for zi in range(NZ):
        for m in range(12):
            col = S[zi, :, m]
            if np.isnan(col).any():
                continue
            srt = np.sort(col)
            thr = srt[NY - k - 1]          # k=2 → srt[10] = 11º menor
            disp[zi, :, m] = col > thr
    return disp

def metrics(disp, ev, mask=None):
    if mask is None:
        mask = np.ones_like(disp, dtype=bool)
    a = int(((disp) & ev & mask).sum()); b = int((disp & ~ev & mask).sum())
    c = int((~disp & ev & mask).sum()); d = int((~disp & ~ev & mask).sum())
    n = a + b + c + d
    if a + b == 0 or a + c == 0 or b + d == 0:
        return dict(a=a, b=b, c=c, d=d, n=n, rate=(a + b) / n, base=(a + c) / n,
                    prec=float('nan'), pod=float('nan'), pofd=float('nan'), pss=float('nan'), hss=float('nan'), bias=float('nan'))
    pod, pofd = a / (a + c), b / (b + d)
    esp = ((a + b) * (a + c) + (c + d) * (b + d)) / n
    return dict(a=a, b=b, c=c, d=d, n=n, rate=(a + b) / n, base=(a + c) / n, prec=a / (a + b),
                pod=pod, pofd=pofd, far=b / (a + b), bias=(a + b) / (a + c), pss=pod - pofd,
                hss=((a + d) - esp) / (n - esp))

def block_ci(disp, ev, nboot=1000, mask=None):
    """IC95 bloque-año: remuestrea los 13 años con reposición."""
    pss, prec = [], []
    for _ in range(nboot):
        ys = rng.integers(0, NY, NY)
        dd, ee = disp[:, ys, :], ev[:, ys, :]
        mm = None if mask is None else mask[:, ys, :]
        M = metrics(dd, ee, mm)
        pss.append(M['pss']); prec.append(M['prec'])
    return dict(pss=[float(np.nanpercentile(pss, 2.5)), float(np.nanpercentile(pss, 97.5))],
                prec=[float(np.nanpercentile(prec, 2.5)), float(np.nanpercentile(prec, 97.5))])

# climatología mensual pura igualada en tasa
share = np.zeros((NZ, 12))
for zi in range(NZ):
    tot = fire[zi].sum() or 1
    share[zi] = fire[zi].sum(axis=0) / tot
def clim_baseline(nfire, ev, valid):
    """predictor que dispara en los zona-meses con mayor share climatológico, mismo n de disparos."""
    sc = np.broadcast_to(share[:, None, :], ev.shape).copy()
    sc[~valid] = -1
    flat = sc.ravel()
    idx = np.argsort(-flat, kind='stable')[:nfire]
    disp = np.zeros(flat.shape, dtype=bool); disp[idx] = True
    return metrics(disp.reshape(ev.shape), ev, valid)

R = {'territorio': T, 'zonas': NZ, 'provincias': N_PROV, 'anios': YS, 'meteo': 'ERA5 (CDS) puro'}
fmt = lambda M: f"rate {100*M['rate']:.1f}% · prec {100*M['prec']:.1f}% (base {100*M['base']:.1f}%) · POD {100*M['pod']:.1f}% · POFD {100*M['pofd']:.1f}% · bias {M['bias']:.2f} · PSS {M['pss']:.3f} · HSS {M['hss']:.3f}"

# ── A. rango del umbral ───────────────────────────────────────────────────────
print('\nA. RANGO DEL UMBRAL (ventana 30 d, evento ≥ mediana)')
S30 = stat[30]; valid30 = ~np.isnan(S30)
A = []
for k in range(1, 7):
    disp = fire_rank(S30, k)
    M = metrics(disp, EV['median'], valid30)
    ci = block_ci(disp, EV['median'], 600, valid30)
    cb = clim_baseline(M['a'] + M['b'], EV['median'], valid30)
    A.append(dict(k=k, **M, ci=ci, clim_pss=cb['pss'], clim_prec=cb['prec']))
    print(f"  top-{k}/13: {fmt(M)} · IC PSS [{ci['pss'][0]:.3f},{ci['pss'][1]:.3f}] · clim PSS {cb['pss']:.3f}")
R['A_rango'] = A

# ── B. ventana ────────────────────────────────────────────────────────────────
print('\nB. VENTANA DE LA MEDIA MÓVIL (top-2/13, evento ≥ mediana)')
B = []
for W in WINDOWS:
    S = stat[W]; valid = ~np.isnan(S)
    disp = fire_rank(S, 2)
    M = metrics(disp, EV['median'], valid)
    ci = block_ci(disp, EV['median'], 400, valid)
    B.append(dict(W=W, **M, ci=ci))
    print(f"  {W:>3} d: {fmt(M)} · IC PSS [{ci['pss'][0]:.3f},{ci['pss'][1]:.3f}]")
R['B_ventana'] = B

# ── C. definición del evento ─────────────────────────────────────────────────
print('\nC. DEFINICIÓN DEL EVENTO (30 d, top-2/13)')
disp30 = fire_rank(S30, 2)
C = []
for kind in ('median', 'p75', 'mean'):
    M = metrics(disp30, EV[kind], valid30)
    cb = clim_baseline(M['a'] + M['b'], EV[kind], valid30)
    C.append(dict(evento=kind, **M, clim_pss=cb['pss']))
    print(f"  fuego ≥ {kind:6}: {fmt(M)} · clim PSS {cb['pss']:.3f}")
R['C_evento'] = C

# ── D. lead time ─────────────────────────────────────────────────────────────
print('\nD. LEAD TIME (30 d, top-2/13, evento ≥ mediana)')
D = []
ev = EV['median']
for lag in range(5):
    # disparo en (y,m) vs evento en (y,m)+lag
    disp_l = np.zeros_like(disp30); ev_l = np.zeros_like(ev); mask = np.zeros_like(ev)
    for yi in range(NY):
        for m in range(12):
            t = yi * 12 + m + lag
            yy, mm = t // 12, t % 12
            if yy >= NY:
                continue
            disp_l[:, yi, m] = disp30[:, yi, m]; ev_l[:, yi, m] = ev[:, yy, mm]
            mask[:, yi, m] = valid30[:, yi, m]
    M = metrics(disp_l, ev_l, mask)
    D.append(dict(lag=lag, **M))
    print(f"  +{lag}: {fmt(M)}")
R['D_lead'] = D

# ── E. agregación provincial ─────────────────────────────────────────────────
print('\nE. AGREGACIÓN PROVINCIAL (evento = fuego provincial ≥ mediana)')
pfire = np.zeros((N_PROV, NY, 12)); pev = np.zeros((N_PROV, NY, 12), dtype=bool)
pz = defaultdict(list)
for zi, z in enumerate(zones):
    pz[z['prov']].append(zi)
for pi, p in enumerate(PROVS):
    pfire[pi] = fire[pz[p]].sum(axis=0)
    for m in range(12):
        s = pfire[pi, :, m]; pev[pi, :, m] = (s >= np.median(s)) & (s > 0)
# percentil de cada estadístico provincial (rank entre los 13) — misma regla top-2
def prov_stat(fn):
    S = np.full((N_PROV, NY, 12), np.nan)
    for pi, p in enumerate(PROVS):
        zs = pz[p]
        w = np.array([zones[zi]['peso'] for zi in zs]); w = w / w.sum()
        sub = S30[zs]                               # (nz, NY, 12)
        S[pi] = fn(sub, w)
    return S
def rank_fire(S, k=2):
    disp = np.zeros_like(S, dtype=bool)
    for pi in range(N_PROV):
        for m in range(12):
            col = S[pi, :, m]
            if np.isnan(col).any(): continue
            disp[pi, :, m] = col > np.sort(col)[NY - k - 1]
    return disp
# A-zonal = alguna zona dispara (cada zona contra SU umbral)
disp_any = np.zeros((N_PROV, NY, 12), dtype=bool)
disp_dom = np.zeros((N_PROV, NY, 12), dtype=bool)
for pi, p in enumerate(PROVS):
    zs = pz[p]
    disp_any[pi] = disp30[zs].any(axis=0)
    dom = zs[int(np.argmax([zones[zi]['peso'] for zi in zs]))]
    disp_dom[pi] = disp30[dom]
agg = {
    'cualquier zona (A-zonal, regla publicada)': disp_any,
    'zona dominante sola': disp_dom,
    'media ponderada provincial (top-2/13)': rank_fire(prov_stat(lambda sub, w: np.nansum(sub * w[:, None, None], axis=0))),
    'máximo provincial (top-2/13)': rank_fire(prov_stat(lambda sub, w: np.nanmax(sub, axis=0))),
}
# comparación a TASA IGUALADA: la A-zonal dispara más (unión de zonas); la media ponderada se lleva al k
# que iguala su tasa de disparo (interpolando entre k enteros se reporta el k más cercano)
S_mean = prov_stat(lambda sub, w: np.nansum(sub * w[:, None, None], axis=0))
S_max = prov_stat(lambda sub, w: np.nanmax(sub, axis=0))
rate_any = disp_any[~np.isnan(S_mean)].mean()
k_match = int(round(rate_any * NY))
for kk in sorted({k_match - 1, k_match, k_match + 1}):
    if 1 <= kk <= 8:
        agg[f'media ponderada provincial (top-{kk}/13, tasa≈A-zonal)'] = rank_fire(S_mean, kk)
        agg[f'máximo provincial (top-{kk}/13, tasa≈A-zonal)'] = rank_fire(S_max, kk)
E = []
pvalid = ~np.isnan(prov_stat(lambda sub, w: np.nanmax(sub, axis=0)))
for nom, dsp in agg.items():
    M = metrics(dsp, pev, pvalid)
    ci = block_ci(dsp, pev, 400, pvalid)
    E.append(dict(regla=nom, **M, ci=ci))
    print(f"  {nom:44}: {fmt(M)} · IC PSS [{ci['pss'][0]:.3f},{ci['pss'][1]:.3f}]")
R['E_agregacion'] = E

# ── F. regla país ────────────────────────────────────────────────────────────
print('\nF. REGLA PAÍS — umbral de extensión (provincias con alguna zona disparada)')
cnt = disp_any.sum(axis=0)                       # (NY,12) nº provincias escaladas
if pais_mensual is None:
    pais = pfire.sum(axis=0)
else:
    pais = np.array([[pais_mensual[y][m] for m in range(12)] for y in YS], dtype=float)
pev_pais = np.zeros((NY, 12), dtype=bool)
for m in range(12):
    s = pais[:, m]; pev_pais[:, m] = s >= np.median(s)
F = []
for thr in range(1, N_PROV + 1):
    act = cnt >= thr
    n = int(act.sum()); h = int((act & pev_pais).sum())
    M = metrics(act[None], pev_pais[None])
    F.append(dict(thr=thr, frac=thr / N_PROV, meses=n, aciertos=h, hit=(h / n if n else None), pss=M['pss']))
    if n:
        print(f"  ≥{thr:2}/{N_PROV} ({100*thr/N_PROV:4.0f}%): {n:3} meses · aciertos {h:3} ({100*h/n:5.1f}%) · PSS país {M['pss']:.3f}")
R['F_pais'] = F
R['F_pais_conteo_mensual'] = {f'{y}-{m+1:02d}': int(cnt[yi, m]) for yi, y in enumerate(YS) for m in range(12)}

# ── G. memoria del DC ────────────────────────────────────────────────────────
print('\nG. MEMORIA DEL DC: e-folding de la autocorrelación de la anomalía diaria')
efold = []
for z in zones:
    arr = dc_daily[z['zid']]
    i0, i1 = didx(dt.date(2012, 1, 1)), didx(dt.date(2024, 12, 31)) + 1
    x = arr[i0:i1]
    if np.isnan(x).mean() > 0.05: continue
    x = np.where(np.isnan(x), np.nanmean(x), x)
    # anomalía vs climatología por día del año (suavizada 15 d)
    doy = np.array([(dt.date(2012, 1, 1) + dt.timedelta(days=i)).timetuple().tm_yday - 1 for i in range(len(x))]) % 365
    clim = np.array([x[doy == d].mean() for d in range(365)])
    ker = np.ones(15) / 15; clim_s = np.convolve(np.r_[clim[-7:], clim, clim[:7]], ker, 'valid')
    an = x - clim_s[doy]; an -= an.mean()
    v = (an * an).mean()
    lagE = None
    for L in range(1, 400):
        r = (an[:-L] * an[L:]).mean() / v
        if r < math.exp(-1):
            lagE = L; break
    if lagE: efold.append(lagE)
efold = np.array(efold)
R['G_efolding_dias'] = dict(mediana=float(np.median(efold)), p25=float(np.percentile(efold, 25)),
                            p75=float(np.percentile(efold, 75)), n=int(len(efold)))
print(f"  e-folding de la anomalía de DC: mediana {np.median(efold):.0f} d (IQR {np.percentile(efold,25):.0f}–{np.percentile(efold,75):.0f}), n={len(efold)} zonas")

json.dump(R, open(f'{OUTD}/sensibilidad_{T}.json', 'w'), indent=1, default=float)

# ── markdown ─────────────────────────────────────────────────────────────────
L = [f'# Sensibilidad del término de sequía — {T} (ERA5 puro, {YS[0]}–{YS[-1]})', '',
     f'{NZ} zonas · {N_PROV} provincias · métricas: Jolliffe & Stephenson (2012); IC95 bootstrap bloque-año.', '',
     '## A. Rango del umbral (ventana 30 d)', '',
     '| top-k/13 | tasa disparo | precisión | base | POD | POFD | bias | PSS [IC95] | HSS | PSS climatología |', '|---|---|---|---|---|---|---|---|---|---|']
for r in A:
    L.append(f"| {r['k']} | {100*r['rate']:.1f}% | {100*r['prec']:.1f}% | {100*r['base']:.1f}% | {100*r['pod']:.1f}% | {100*r['pofd']:.1f}% | {r['bias']:.2f} | {r['pss']:.3f} [{r['ci']['pss'][0]:.3f}, {r['ci']['pss'][1]:.3f}] | {r['hss']:.3f} | {r['clim_pss']:.3f} |")
L += ['', '## B. Ventana de la media móvil (top-2/13)', '', '| ventana | tasa | precisión | POD | PSS [IC95] |', '|---|---|---|---|---|']
for r in B:
    L.append(f"| {r['W']} d | {100*r['rate']:.1f}% | {100*r['prec']:.1f}% | {100*r['pod']:.1f}% | {r['pss']:.3f} [{r['ci']['pss'][0]:.3f}, {r['ci']['pss'][1]:.3f}] |")
L += ['', '## C. Definición del evento (30 d, top-2/13)', '', '| evento | base | precisión | POD | PSS | PSS climatología |', '|---|---|---|---|---|---|']
for r in C:
    L.append(f"| fuego ≥ {r['evento']} | {100*r['base']:.1f}% | {100*r['prec']:.1f}% | {100*r['pod']:.1f}% | {r['pss']:.3f} | {r['clim_pss']:.3f} |")
L += ['', '## D. Lead time', '', '| lead | precisión | base | POD | PSS |', '|---|---|---|---|---|']
for r in D:
    L.append(f"| +{r['lag']} | {100*r['prec']:.1f}% | {100*r['base']:.1f}% | {100*r['pod']:.1f}% | {r['pss']:.3f} |")
L += ['', '## E. Agregación provincial (evento = fuego provincial ≥ mediana)', '', '| regla | tasa | precisión | base | POD | PSS [IC95] |', '|---|---|---|---|---|---|']
for r in E:
    L.append(f"| {r['regla']} | {100*r['rate']:.1f}% | {100*r['prec']:.1f}% | {100*r['base']:.1f}% | {100*r['pod']:.1f}% | {r['pss']:.3f} [{r['ci']['pss'][0]:.3f}, {r['ci']['pss'][1]:.3f}] |")
L += ['', f'## F. Regla país (N = {N_PROV})', '', '| umbral | fracción | meses activos | aciertos | % | PSS país |', '|---|---|---|---|---|---|']
for r in F:
    if r['meses']:
        L.append(f"| ≥{r['thr']} | {100*r['frac']:.0f}% | {r['meses']} | {r['aciertos']} | {100*r['hit']:.1f}% | {r['pss']:.3f} |")
g = R['G_efolding_dias']
L += ['', '## G. Memoria del DC', '', f"e-folding de la autocorrelación de la anomalía diaria de DC: mediana **{g['mediana']:.0f} días** (IQR {g['p25']:.0f}–{g['p75']:.0f}; n = {g['n']} zonas).", '']
open(f'{OUTD}/sensibilidad_{T}.md', 'w').write('\n'.join(L))
print(f'\n→ {OUTD}/sensibilidad_{T}.md / .json')
