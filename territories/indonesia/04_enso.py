#!/usr/bin/env python3
"""GFI Indonesia — paso 4: término ENSO (factores por fase, barrido de lags, LOYO, ventana).

Port 1:1 de la maquinaria AR (derive_enso_calibracion.mjs + 07_barrido_lags.mjs +
10_loyo_enso_ventana.mjs):
  anomalía  = focos del mes / mediana de ese mes calendario del MISMO sensor
              (MODIS base 2001–2025, usado 2001–2011; VIIRS 2012–2025), meses con mediana < 5 fuera
  ventana   = meses con share ≥ 8% del fuego anual del ámbito (VIIRS 2012–2025)
  factor    = mediana de anomalías de la ventana por fase ENSO (ONI, ±0.5, mes central)
              a lag L (fase L meses antes del mes de fuego)
  p_perm    = permutación de medias de log-anomalía, 20k iters, Niña-vs-resto y Niño-vs-resto
ORDEN ESPERADO declarado antes de correr (literatura: Field et al. 2009/2016; Aldrian &
Susanto 2003): Niño > Niña en las tres regiones (en la convención AR = 'inversa'); SUM-N
con respuesta débil esperada (régimen ecuatorial bimodal).

Salida: enso_calibracion_id.json (acá) + reporte por stdout.
Uso: python3 04_enso.py   (sin red; requiere 01)
"""
import json, math, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import territorio as T

HERE = os.path.dirname(os.path.abspath(__file__))
random.seed(20261105)
S = json.load(open(f'{T.CACHE}/series.json'))
MESES = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic']
MODIS_USO, MODIS_BASE, VIIRS = (2001, 2011), (2001, 2025), (2012, 2025)

# ---------- ONI ----------
SEAS = dict(DJF=0, JFM=1, FMA=2, MAM=3, AMJ=4, MJJ=5, JJA=6, JAS=7, ASO=8, SON=9, OND=10, NDJ=11)
oni = {}
for ln in open(f'{T.FIRMS}/oni.ascii.txt'):
    c = ln.split()
    if len(c) == 4 and c[0] in SEAS:
        oni[(int(c[1]), SEAS[c[0]])] = float(c[3])


def fase_lag(y, m, lag):
    t = y * 12 + m - lag
    a = oni.get((t // 12, t % 12))
    if a is None:
        return None
    return 'nino' if a >= 0.5 else 'nina' if a <= -0.5 else 'neutral'


# ---------- series por ámbito ----------
def suma(sensor, provs):
    out = {}
    for p in provs:
        for y, arr in S[sensor][p].items():
            acc = out.setdefault(int(y), [0] * 12)
            for m in range(12):
                acc[m] += arr[m]
    return out


AMB = {'territorio': list(T.PROVINCIAS)}
for r in T.REGIONES:
    AMB[r] = [p for p, (rr, _) in T.PROVINCIAS.items() if rr == r]
SER = {a: {s: suma(s, ps) for s in ('MODIS', 'VIIRS')} for a, ps in AMB.items()}


def mediana(v):
    s = sorted(v)
    if not s:
        return float('nan')
    h = len(s) // 2
    return s[h] if len(s) % 2 else (s[h - 1] + s[h]) / 2


def med_mens(por, base, excl=None):
    return [mediana([por[y][m] for y in range(base[0], base[1] + 1) if y in por and y != excl]) for m in range(12)]


def anomalias(por, base, uso, excl=None):
    med = med_mens(por, base, excl)
    return [(y, m, por[y][m] / med[m]) for y in range(uso[0], uso[1] + 1) if y in por
            for m in range(12) if med[m] >= 5]


def serie_anom(amb, excl=None):
    return anomalias(SER[amb]['MODIS'], MODIS_BASE, MODIS_USO, excl) + anomalias(SER[amb]['VIIRS'], VIIRS, VIIRS, excl)


def ventana(amb, share=T.SHARE_MIN, excl=None):
    tot = [0] * 12
    for y, arr in SER[amb]['VIIRS'].items():
        if y == excl:
            continue
        for m in range(12):
            tot[m] += arr[m]
    g = sum(tot)
    ms = [m for m in range(12) if tot[m] / g >= share]
    return ms, round(sum(tot[m] for m in ms) / g, 2)


def por_fase(anoms, lag, vent):
    g = {'nina': [], 'neutral': [], 'nino': []}
    for y, m, r in anoms:
        if m in vent:
            f = fase_lag(y, m, lag)
            if f:
                g[f].append(r)
    return g


CEROS = [0]


def lg(v):
    if v <= 0:
        CEROS[0] += 1
        return math.log(1e-3)
    return math.log(v)


def perm(A, B, iters=20000):
    if len(A) < 5 or len(B) < 5:
        return None
    a, b = [lg(x) for x in A], [lg(x) for x in B]
    obs = sum(a) / len(a) - sum(b) / len(b)
    todos = a + b
    na, ext = len(a), 0
    for _ in range(iters):
        random.shuffle(todos)
        ma = sum(todos[:na]) / na
        mb = sum(todos[na:]) / (len(todos) - na)
        if abs(ma - mb) >= abs(obs):
            ext += 1
    return round(ext / iters, 4)


def fila(g):
    return {f: {'factor': round(mediana(g[f]), 2), 'n': len(g[f])} for f in ('nina', 'neutral', 'nino')} | {
        'p_perm_nina_vs_resto': perm(g['nina'], g['neutral'] + g['nino']),
        'p_perm_nino_vs_resto': perm(g['nino'], g['neutral'] + g['nina'])}


fmt = lambda x: '  –  ' if x is None or x != x else f'{x:.2f}'

# ---------- (A) factores por ámbito en su ventana + barrido de lags ----------
print('══ (A) FACTORES ENSO — ventana propia (share ≥ 8%), barrido lags 0/3/6/9/12 ══')
factores, ventanas, barrido = {}, {}, {}
for amb in AMB:
    vent, cob = ventana(amb)
    ventanas[amb] = {'meses': [MESES[m] for m in vent], 'cobertura_fuego': cob}
    anoms = serie_anom(amb)
    barrido[amb] = {}
    print(f'\n  {amb} [{" ".join(MESES[m] for m in vent)}] cobertura {cob}')
    for lag in (0, 3, 6, 9, 12):
        r = fila(por_fase(anoms, lag, vent))
        barrido[amb][f'lag{lag}'] = r
        print(f'    lag{lag:<2} Ñ {fmt(r["nina"]["factor"])}/{r["nina"]["n"]:<3} · n {fmt(r["neutral"]["factor"])}/{r["neutral"]["n"]:<3}'
              f' · N {fmt(r["nino"]["factor"])}/{r["nino"]["n"]:<3}  pÑ {r["p_perm_nina_vs_resto"]}  pN {r["p_perm_nino_vs_resto"]}')
    factores[amb] = {k: barrido[amb][k] for k in ('lag0', 'lag3')}

# ---------- (B) LOYO a lag 3 (operativo), ventana fija ----------
print('\n══ (B) LOYO ENSO — lag 3, ventana fija; orden esperado Niño > Niña ══')
ANIOS = list(range(2001, 2026))
loyo = {}
for amb in AMB:
    vent, _ = ventana(amb)
    folds, oos = [], {'nina': [], 'neutral': [], 'nino': []}
    vcambia = 0
    for Y in ANIOS:
        an = serie_anom(amb, Y)
        g = por_fase([a for a in an if a[0] != Y], 3, vent)
        folds.append({f: mediana(g[f]) for f in g})
        for y, m, r in an:
            if y == Y and m in vent:
                f = fase_lag(y, m, 3)
                if f:
                    oos[f].append(r)
        if Y >= 2012 and ventana(amb, excl=Y)[0] != vent:
            vcambia += 1
    sost = sum(1 for f in folds if f['nino'] > f['nina'])
    rng = lambda k: f"{min(f[k] for f in folds):.2f}–{max(f[k] for f in folds):.2f}"
    pN = perm(oos['nino'], oos['neutral'] + oos['nina'])
    loyo[amb] = {'folds': len(ANIOS), 'orden_nino_mayor_nina_se_sostiene': sost,
                 'oos': {f: {'factor': round(mediana(oos[f]), 2), 'n': len(oos[f])} for f in oos},
                 'p_perm_oos_nino_vs_resto': pN, 'ventana_cambia_sin_Y': f'{vcambia}/14'}
    print(f'\n  {amb}: Niño>Niña en {sost}/{len(ANIOS)} folds · rango Ñ {rng("nina")} · n {rng("neutral")} · N {rng("nino")}')
    print(f'    pooled OOS: Ñ {fmt(mediana(oos["nina"]))}/{len(oos["nina"])} · n {fmt(mediana(oos["neutral"]))}/{len(oos["neutral"])}'
          f' · N {fmt(mediana(oos["nino"]))}/{len(oos["nino"])} · p_perm OOS Niño-vs-resto {pN}')
    print(f'    ventana recalculada sin Y: cambia en {vcambia}/14')

# ---------- (C) sensibilidad de ventana 6/8/10% a lag 3 ----------
print('\n══ (C) SENSIBILIDAD DE VENTANA — lag 3 ══')
sens = {}
for sh in (0.06, 0.08, 0.10):
    for amb in AMB:
        vent, cob = ventana(amb, sh)
        r = fila(por_fase(serie_anom(amb), 3, vent))
        sens.setdefault(f'{int(sh * 100)}%', {})[amb] = {'meses': [MESES[m] for m in vent], 'lag3': r}
        print(f'  {int(sh*100):>2}% {amb:<10} [{" ".join(MESES[m] for m in vent)}] Ñ {fmt(r["nina"]["factor"])} · n {fmt(r["neutral"]["factor"])}'
              f' · N {fmt(r["nino"]["factor"])}  pN {r["p_perm_nino_vs_resto"]}')

print(f'\nlog-anomalías con valor 0 (reemplazadas por log(1e-3)): {CEROS[0]}')
json.dump({
    'territorio': 'Indonesia — Sumatra + Kalimantan',
    'generado': '2026-11-05',
    'fuente': {'fuego': 'FIRMS MODIS 2001–2011 (conf≥30, type=0; base medianas 2001–2025) + VIIRS S-NPP 2012–2025 (conf!=l, type=0)',
               'enso': 'ONI NOAA/CPC, mes central; Niño ≥ +0.5 · Niña ≤ −0.5'},
    'regiones': AMB, 'ventanas': ventanas, 'factores': factores, 'barrido_lags': barrido,
    'loyo_lag3': loyo, 'sensibilidad_ventana_lag3': sens,
    'n_log_cero': CEROS[0],
}, open(os.path.join(HERE, 'enso_calibracion_id.json'), 'w'), indent=1, ensure_ascii=False)
