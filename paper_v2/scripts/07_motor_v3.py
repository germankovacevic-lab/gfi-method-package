#!/usr/bin/env python3
"""Paper v2 — reglas de combinación REDISEÑADAS con la evidencia (candidatas a calibración 3.0),
evaluadas con las mismas métricas que el motor actual (06_skill_indice_*). AR e ID.

Reglas v3 (D1, German 12/11/2026):
  * Señal ENSO declarada en una región SOLO si el IC95 bootstrap (bloque-año) del COCIENTE entre fases
    (factor Niña / factor Niño, lag 3) excluye 1: directa si lím. inf. > 1, inversa si lím. sup. < 1.
    Sin corte fijo 1.10/1.45 y sin declarar el signo a mano.
  * Nivel base = MEDIO. Gate estacional idéntico a producción (r < 1 y share < 8 % → BAJO).
  * Sequía (A-zonal, umbral top-2/13 congelado 2012–2024, ERA5 puro) → sube UN escalón (BAJO→MEDIO, MEDIO→ALTO).
  * ENSO ya no escala solo: fase coincidente sin sequía → MEDIO (se declara); fase CONTRARIA sin sequía
    → BAJO; coincidente + sequía → ALTO "convergente".
    Variante v3b (más estricta): en regiones con señal, ALTO exige sequía Y fase coincidente.
  * Regla país: umbral de extensión elegido por LOYO (el que maximiza PSS en los otros 12 años).
Fase ENSO del mes = ONI del trimestre centrado 2 meses antes (último publicado; igual que producción).

Uso: python3 07_motor_v3.py AR | ID
"""
import json, csv, os, sys, statistics, datetime as dt
import numpy as np
from collections import defaultdict

T = sys.argv[1] if len(sys.argv) > 1 else 'AR'
HOME = os.path.expanduser('~'); G = f'{HOME}/.openclaw/workspace/geofuego'; DATA = f'{HOME}/.openclaw/data'
OUTD = f'{G}/paper/v2/resultados'; rng = np.random.default_rng(11)
YS = list(range(2012, 2025)); MESES = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic']
ENSO = json.load(open(f'{OUTD}/enso_{T}.json'))

def parse_oni(path):
    SEAS = {'DJF': 0, 'JFM': 1, 'FMA': 2, 'MAM': 3, 'AMJ': 4, 'MJJ': 5, 'JJA': 6, 'JAS': 7, 'ASO': 8, 'SON': 9, 'OND': 10, 'NDJ': 11}
    oni = {}
    for ln in open(path):
        c = ln.split()
        if len(c) >= 4 and c[0] in SEAS: oni[(int(c[1]), SEAS[c[0]])] = float(c[3])
    return oni

if T == 'AR':
    P = f'{G}/tools/gfi_era5_ar/pkg_cds'
    ZON = json.load(open(f'{P}/zonas_fuego.json'))['zonas']; FWI = f'{DATA}/gfi_v2_fwi_cds'
    FOC = json.load(open(f'{DATA}/gfi_v2_focos_zona.json')); NEW = json.load(open(f'{DATA}/gfi_v2_focos_zona_2025_2026.json'))
    CAL = json.load(open(f'{P}/enso_calibracion.json'))
    REGION = CAL['provincia_region']; CLIM = CAL['climatologia']; oni = parse_oni(f'{DATA}/firms_ar/oni.ascii.txt')
    fire = defaultdict(dict)
    for p, zs in FOC.items():
        for z in zs:
            for ym, n in z.items(): fire[p][ym] = fire[p].get(ym, 0) + n
    for p, d in NEW['prov_mensual'].items():
        for ym, n in d.items(): fire[p][ym] = fire[p].get(ym, 0) + n
    focos_zona = {p: [dict(z) for z in zs] for p, zs in FOC.items()}
    for p, zs in NEW['focos'].items():
        for j, z in enumerate(zs): focos_zona[p][j].update(z)
    LAST = '2026-10'; AMB_PAIS = 'pais'
else:
    sys.path.insert(0, f'{G}/tools/gfi_id'); import territorio as TT
    ZON = json.load(open(f'{G}/tools/gfi_id/zonas_fuego.json'))['zonas']; FWI = f'{DATA}/gfi_id_fwi'
    FOC = json.load(open(f'{DATA}/gfi_id_cache/focos_zona.json'))
    import ast
    T26 = json.load(open(f'{G}/tools/gfi_id/temporada_2026.json'))['cnt_prov']; T26 = ast.literal_eval(T26) if isinstance(T26, str) else T26
    REGION = {p: r for p, (r, _) in TT.PROVINCIAS.items()}
    S = json.load(open(f'{DATA}/gfi_id_cache/series.json'))['VIIRS']
    CLIM = {p: [statistics.median([S[p][str(y)][m] for y in range(2012, 2026) if str(y) in S[p]]) for m in range(12)] for p in REGION}
    oni = parse_oni(f'{DATA}/firms_id/oni.ascii.txt')
    fire = defaultdict(dict)
    for p, zs in FOC.items():
        for z in zs:
            for ym, n in z.items(): fire[p][ym] = fire[p].get(ym, 0) + n
    for p, v in T26.items():
        for m in range(10): fire[p][f'2026-{m+1:02d}'] = v[m]
    focos_zona = FOC; LAST = '2026-10'; AMB_PAIS = 'territorio'
PROVS = [p for p in ZON if p in REGION]

# señal ENSO v3: declarada solo si IC excluye 1
# criterio único: el IC95 bloque-año del COCIENTE entre fases (Niña/Niño a lag 3) excluye 1.
# directa si el límite inferior > 1 (Niña > Niño); inversa si el límite superior < 1 (Niño > Niña).
SIG = {}
for r in ENSO['barrido_cortes']:
    ci = ENSO['ambitos'][r['ambito']]['lags']['3']['ci']['ratio_nina_nino']
    tipo = 'directa' if ci[0] > 1 else 'inversa' if ci[1] < 1 else 'ninguna'
    SIG[r['ambito']] = dict(tipo=tipo, ratio_ci=ci, f=r['f_match'], ci=r['ci_match'], v2_tipo=r['tipo'])
print(f'[{T}] señales v3 (IC95 excluye 1): ' + ' · '.join(f"{a}: {s['tipo']} (v2 {s['v2_tipo']})" for a, s in SIG.items()))

def fase(v): return None if v is None else ('nino' if v >= 0.5 else 'nina' if v <= -0.5 else 'neutral')
def fase_mes(y, m0):  # trimestre centrado 2 meses antes (último publicado)
    t = y * 12 + m0 - 2; return fase(oni.get((t // 12, t % 12)))

# ── sequía A-zonal por provincia-mes (umbrales congelados 2012–2024) ──
def zid(z): return f"{z['lat']:.2f}_{z['lon']:.2f}"
def movil(s, y, m, W=30):
    fin = dt.date(y + (m == 12), (m % 12) + 1, 1) - dt.timedelta(days=1)
    v = [s[k] for k in ((fin - dt.timedelta(days=i)).isoformat() for i in range(W)) if k in s]
    return round(sum(v) / len(v), 2) if len(v) >= 25 else None
print('sequía por zona…')
disp = defaultdict(set)          # 'YYYY-MM' → set(prov) con alguna zona disparada
disp_zona = defaultdict(dict)    # prov → ym → nombre zona que dispara (primera)
for p in PROVS:
    for j, z in enumerate(ZON[p]):
        s = {}
        for r in csv.DictReader(open(f'{FWI}/fwi_{zid(z)}.csv')): s[r['date']] = float(r['dc'])
        for m in range(1, 13):
            clim = [movil(s, y, m) for y in YS]
            if None in clim: continue
            umb = sorted(clim)[10]
            for y in range(2012, 2027):
                v = movil(s, y, m)
                if v is not None and v > umb: disp[f'{y}-{m:02d}'].add(p)

# ── gate ──
def fuera_temporada(p, m0):
    clim = CLIM[p]; total = sum(clim)
    if total < 24: return True
    r = sum([4, 3, 2, 1][i] * clim[(m0 + i) % 12] for i in range(4)) / total * 12 / 10
    return r < 1.0 and clim[m0] / total < 0.08

# ── niveles v3 ──
ORD = ['B', 'M', 'A']
def nivel_v3(p, y, m0, estricta=False):
    ym = f'{y}-{m0+1:02d}'; f = fase_mes(y, m0); reg = REGION[p]; sig = SIG.get(reg, {'tipo': 'ninguna'})['tipo']
    match = (sig == 'directa' and f == 'nina') or (sig == 'inversa' and f == 'nino')
    contra = (sig == 'directa' and f == 'nino') or (sig == 'inversa' and f == 'nina')
    seq = p in disp.get(ym, ())
    if fuera_temporada(p, m0):
        lvl = 1 if seq else 0; drv = 's' if seq else '.'
        return ORD[lvl], drv
    lvl = 1
    if contra and not seq: lvl = 0
    if seq:
        if estricta and sig != 'ninguna': lvl = 2 if match else 1
        else: lvl = 2
    drv = 'x' if (seq and match) else 's' if seq else 'e' if match else 'c' if contra else '.'
    return ORD[lvl], drv

def metr(pred, ev):
    pred = np.array(pred, bool); ev = np.array(ev, bool)
    a = int((pred & ev).sum()); b = int((pred & ~ev).sum()); c = int((~pred & ev).sum()); d = int((~pred & ~ev).sum())
    pod = a / (a + c) if a + c else float('nan'); pofd = b / (b + d) if b + d else float('nan')
    return dict(a=a, b=b, c=c, d=d, rate=(a + b) / max(1, len(ev)), base=(a + c) / max(1, len(ev)), prec=(a / (a + b) if a + b else float('nan')), pod=pod, pofd=pofd, pss=pod - pofd)

def mediana_mes(p, m): return statistics.median([fire[p].get(f'{y}-{m:02d}', 0) for y in YS])

def evaluar(estricta, titulo):
    rows = []
    for p in PROVS:
        for y in range(2012, 2027):
            for m in range(1, 13):
                ym = f'{y}-{m:02d}'
                if ym > LAST: continue
                f = fire[p].get(ym); 
                if f is None and y >= 2025: continue
                f = f or 0; med = mediana_mes(p, m)
                if med < 5: continue
                lv, drv = nivel_v3(p, y, m - 1, estricta)
                rows.append((p, y, m, lv, drv, f, med, f >= med and f > 0))
    out = {}
    for nom, sel in (('in_sample_2012_2024', lambda r: r[1] <= 2024), ('oos_2025', lambda r: r[1] == 2025), ('oos_2026', lambda r: r[1] == 2026)):
        rs = [r for r in rows if sel(r)]
        ev = [r[7] for r in rs]
        MA = metr([r[3] == 'A' for r in rs], ev); MAM = metr([r[3] in 'AM' for r in rs], ev)
        anios = sorted(set(r[1] for r in rs)); byY = defaultdict(list)
        for r in rs: byY[r[1]].append(r)
        bs = []
        for _ in range(600):
            Sm = [x for yy in rng.choice(anios, len(anios), replace=True) for x in byY[yy]]
            bs.append(metr([r[3] == 'A' for r in Sm], [r[7] for r in Sm])['pss'])
        MA['ci_pss'] = [float(np.nanpercentile(bs, 2.5)), float(np.nanpercentile(bs, 97.5))]
        niveles = {}
        for lv, nm in (('B', 'BAJO'), ('M', 'MEDIO'), ('A', 'ALTO')):
            sub = [r for r in rs if r[3] == lv]
            if sub: niveles[nm] = dict(n=len(sub), tasa_evento=float(np.mean([r[7] for r in sub])), share_fuego=sum(r[5] for r in sub) / max(1, sum(r[5] for r in rs)))
        drv = defaultdict(list)
        for r in rs:
            if r[3] == 'A': drv[r[4]].append(r[7])
        out[nom] = dict(n=len(rs), niveles=niveles, ALTO=MA, ALTO_o_MEDIO=MAM, ALTO_por_driver={k: dict(n=len(v), tasa_evento=float(np.mean(v))) for k, v in drv.items()})
        print(f"  [{titulo}] {nom}: n={len(rs)} · ALTO tasa {100*MA['rate']:.1f}% prec {100*MA['prec']:.1f}% (base {100*MA['base']:.1f}%) POD {100*MA['pod']:.1f}% PSS {MA['pss']:.3f} [{MA['ci_pss'][0]:.3f},{MA['ci_pss'][1]:.3f}] · "
              f"fuego en ALTO {100*niveles.get('ALTO',{}).get('share_fuego',0):.0f}% · gate PSS {MAM['pss']:.3f} · drivers " + ' '.join(f"{k}:{len(v)}/{100*np.mean(v):.0f}%" for k, v in sorted(drv.items())))
    # por región: la unidad natural es la región de teleconexión, no el país
    out['por_region'] = {}
    for reg in sorted(set(REGION.values())):
        out['por_region'][reg] = {}
        for nom, sel in (('in_sample_2012_2024', lambda r: r[1] <= 2024), ('oos_2025', lambda r: r[1] == 2025), ('oos_2026', lambda r: r[1] == 2026), ('oos_2025_2026', lambda r: r[1] >= 2025)):
            rs = [r for r in rows if sel(r) and REGION[r[0]] == reg]
            if not rs: continue
            M = metr([r[3] == 'A' for r in rs], [r[7] for r in rs])
            hi = [r for r in rs if r[3] == 'A']
            M['n'] = len(rs); M['share_fuego_en_ALTO'] = sum(r[5] for r in hi) / max(1, sum(r[5] for r in rs))
            M['anom_mediana_ALTO'] = float(np.median([r[5] / r[6] for r in hi])) if hi else float('nan')
            M['anom_mediana_resto'] = float(np.median([r[5] / r[6] for r in rs if r[3] != 'A'])) if len(hi) < len(rs) else float('nan')
            out['por_region'][reg][nom] = M
        o = out['por_region'][reg]
        print(f"  [{titulo}] {reg:10} ALTO PSS in-sample {o['in_sample_2012_2024']['pss']:.3f} (prec {100*o['in_sample_2012_2024']['prec']:.0f}% base {100*o['in_sample_2012_2024']['base']:.0f}%, fuego en ALTO {100*o['in_sample_2012_2024']['share_fuego_en_ALTO']:.0f}%) · "
              + ' · '.join(f"{k[4:]}: {o[k]['pss']:.3f} (n={o[k]['n']}, fuego en ALTO {100*o[k]['share_fuego_en_ALTO']:.0f}%)" for k in ('oos_2025', 'oos_2026', 'oos_2025_2026') if k in o))
    # regla de EXTENSIÓN REGIONAL (provincias de la región con sequía vs fuego regional ≥ mediana), umbral por LOYO
    out['extension_regional'] = {}
    for reg in sorted(set(REGION.values())):
        provs = [p for p in PROVS if REGION[p] == reg]; Nr = len(provs)
        rf = defaultdict(int)
        for p in provs:
            for ym, n in fire[p].items(): rf[ym] += n
        yms = [f'{y}-{m:02d}' for y in range(2012, 2027) for m in range(1, 13) if f'{y}-{m:02d}' <= LAST]
        cntr = {ym: sum(1 for p in provs if p in disp.get(ym, ())) for ym in yms}
        evr = {ym: rf.get(ym, 0) >= statistics.median([rf.get(f'{y}-{ym[5:]}', 0) for y in YS]) for ym in yms}
        def pss_t(sub, t): return metr([cntr[ym] >= t for ym in sub], [evr[ym] for ym in sub])['pss']
        pred, ev, eleg = [], [], {}
        for y in YS:
            tr = [ym for ym in yms if int(ym[:4]) in YS and int(ym[:4]) != y]
            b = max(range(1, Nr + 1), key=lambda t: (pss_t(tr, t) if pss_t(tr, t) == pss_t(tr, t) else -9)); eleg[y] = b
            for ym in yms:
                if int(ym[:4]) == y: pred.append(cntr[ym] >= b); ev.append(evr[ym])
        Ml = metr(pred, ev)
        tr_all = [ym for ym in yms if int(ym[:4]) in YS]; b_all = max(range(1, Nr + 1), key=lambda t: (pss_t(tr_all, t) if pss_t(tr_all, t) == pss_t(tr_all, t) else -9))
        oo = [ym for ym in yms if int(ym[:4]) >= 2025]; Mo = metr([cntr[ym] >= b_all for ym in oo], [evr[ym] for ym in oo])
        out['extension_regional'][reg] = dict(N=Nr, umbral_full=b_all, umbrales_loyo=sorted(set(eleg.values())), loyo=Ml, oos_2025_2026=Mo)
        print(f"  [{titulo}] extensión regional {reg:10}: umbral {b_all}/{Nr} (LOYO {sorted(set(eleg.values()))}) · PSS LOYO {Ml['pss']:.3f} (prec {100*Ml['prec']:.0f}%, POD {100*Ml['pod']:.0f}%) · OOS 2025–26 PSS {Mo['pss']:.3f} ({Mo['a']}/{Mo['a']+Mo['b']} aciertos)")
    return out

R = {'territorio': T, 'senales_v3': SIG}
print('\nV3a: sequía → ALTO; ENSO solo nunca escala; contra-fase sin sequía → BAJO')
R['v3a'] = evaluar(False, 'v3a')
print('\nV3b: además, en regiones con señal ALTO exige sequía Y fase coincidente')
R['v3b'] = evaluar(True, 'v3b')

# ── regla país por LOYO ──
print('\nRegla país — umbral de extensión por LOYO')
N = len(PROVS)
pais_fire = defaultdict(int)
for p in PROVS:
    for ym, n in fire[p].items(): pais_fire[ym] += n
cnt = {f'{y}-{m:02d}': len(disp.get(f'{y}-{m:02d}', ())) for y in range(2012, 2027) for m in range(1, 13) if f'{y}-{m:02d}' <= LAST}
ev_pais = {ym: pais_fire.get(ym, 0) >= statistics.median([pais_fire.get(f'{y}-{ym[5:]}', 0) for y in YS]) for ym in cnt}
def pss_thr(yms, thr): return metr([cnt[ym] >= thr for ym in yms], [ev_pais[ym] for ym in yms])['pss']
loyo_pred, loyo_ev, elegidos = [], [], {}
for y in YS:
    train = [ym for ym in cnt if int(ym[:4]) in YS and int(ym[:4]) != y]
    best = max(range(1, N + 1), key=lambda t: (pss_thr(train, t) if not np.isnan(pss_thr(train, t)) else -9))
    elegidos[y] = best
    for ym in cnt:
        if int(ym[:4]) == y: loyo_pred.append(cnt[ym] >= best); loyo_ev.append(ev_pais[ym])
M_loyo = metr(loyo_pred, loyo_ev)
train_all = [ym for ym in cnt if int(ym[:4]) in YS]
best_all = max(range(1, N + 1), key=lambda t: pss_thr(train_all, t))
oos = [ym for ym in cnt if int(ym[:4]) >= 2025]
M_oos = metr([cnt[ym] >= best_all for ym in oos], [ev_pais[ym] for ym in oos])
M_23 = metr([cnt[ym] >= int(np.ceil(2 * N / 3)) for ym in train_all], [ev_pais[ym] for ym in train_all])
R['pais'] = dict(N=N, umbral_elegido_full=best_all, umbrales_loyo=elegidos, loyo_in_2012_2024=M_loyo, oos_2025_2026=M_oos, regla_dos_tercios_in_sample=M_23,
                 meses_oos={ym: dict(n_prov=cnt[ym], activa=cnt[ym] >= best_all, evento=ev_pais[ym]) for ym in oos})
print(f"  umbral por LOYO: {sorted(set(elegidos.values()))} (full-sample {best_all}/{N}) · PSS LOYO {M_loyo['pss']:.3f} (prec {100*M_loyo['prec']:.0f}%, POD {100*M_loyo['pod']:.0f}%) · 2/3 in-sample PSS {M_23['pss']:.3f}")
print(f"  OOS 2025–26 con umbral {best_all}: activa {M_oos['a']+M_oos['b']} meses, aciertos {M_oos['a']} · PSS {M_oos['pss']:.3f}")
json.dump(R, open(f'{OUTD}/motor_v3_{T}.json', 'w'), indent=1, default=float)
print(f'→ {OUTD}/motor_v3_{T}.json')
