#!/usr/bin/env python3
"""GFI Indonesia — paso 6: hindcast del Riesgo Estacional de Incendio (BAJO/MEDIO/ALTO).

Port 1:1 del motor de producción AR (enso_logic.js: nivelAmbito + riesgoV2; gen_gfi_retro.mjs):
  fase       = ONI del trimestre centrado 2 meses antes (último publicado a ese mes)
  base v1    = fuera de temporada → bajo · match & f≥1.45 & robusta & r≥1 → crítico ·
               match & f≥1.10 → elevado · contra & f≤0.90 → bajo · resto → normal
               (f = factor lag 3 de la región; r = peso de la ventana 4-3-2-1 de la climatología)
  v2         = bajo→BAJO, normal→MEDIO, elevado/crítico→ALTO; +1 escalón si CUALQUIER zona
               de la provincia tiene DC móvil 30d > umbral del mes (cap ALTO)
  territorio = mapeo directo + regla de extensión: ≥ 2/3 de las provincias (10 de 15)
               escaladas por sequía → sube un escalón
Señal por región (declarada a partir de 04_enso.py, 05/11/2026 — regla AR: tipo solo si el
signo se sostiene al lag operativo 3; robusta = significativa a lag 0 y 3 y LOYO 25/25):
  territorio, SUM-S, KAL: Niño > Niña (convención AR 'inversa'), ROBUSTA
  SUM-N: Niño > Niña, SUGERENTE (p lag3 0,13; débil, como se declaró antes de correr)
Salida: gfi_id_retro.json (acá) + verificación de coherencia del hindcast por stdout.
Uso: python3 06_hindcast.py   (sin red; requiere 01, 04 y 05)
"""
import json, os, statistics, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import territorio as T

HERE = os.path.dirname(os.path.abspath(__file__))
S = json.load(open(f'{T.CACHE}/series.json'))
CAL = json.load(open(os.path.join(HERE, 'enso_calibracion_id.json')))
UMB = json.load(open(os.path.join(HERE, 'umbrales_dc.json')))['zonas']
DCM = json.load(open(f'{T.CACHE}/dc_movil_fin_mes.json'))
SENAL = {'territorio': ('inversa', 'robusta'), 'SUM-S': ('inversa', 'robusta'),
         'KAL': ('inversa', 'robusta'), 'SUM-N': ('inversa', 'sugerente')}
SEAS = dict(DJF=0, JFM=1, FMA=2, MAM=3, AMJ=4, MJJ=5, JJA=6, JAS=7, ASO=8, SON=9, OND=10, NDJ=11)
oni = {}
for ln in open(f'{T.FIRMS}/oni.ascii.txt'):
    c = ln.split()
    if len(c) == 4 and c[0] in SEAS:
        oni[int(c[1]) * 12 + SEAS[c[0]]] = float(c[3])
fase_de = lambda a: 'nino' if a >= 0.5 else 'nina' if a <= -0.5 else 'neutral'
Y0, Y1 = 2012, 2026
ULT = max(k for v in DCM.values() for k in v)  # último mes con DC completo


def clim(provs):
    por = {}
    for p in provs:
        for y, arr in S['VIIRS'][p].items():
            acc = por.setdefault(int(y), [0] * 12)
            for m in range(12):
                acc[m] += arr[m]
    return [round(statistics.median([por[y][m] for y in range(2012, 2026)])) for m in range(12)]


def nivel_v1(fase, mes, region, cl):
    total = sum(cl)
    if total < 24:
        return 'bajo'
    r = sum(w * cl[(mes + i) % 12] for i, w in enumerate((4, 3, 2, 1))) / total * 12 / 10
    fuera = r < 1.0 and cl[mes] / total < 0.08
    tipo, sig = SENAL[region]
    f = CAL['factores'][region]['lag3'][fase]['factor']
    match = (tipo == 'directa' and fase == 'nina') or (tipo == 'inversa' and fase == 'nino')
    contra = (tipo == 'directa' and fase == 'nino') or (tipo == 'inversa' and fase == 'nina')
    if fuera:
        return 'bajo'
    if match and f >= 1.45 and sig == 'robusta' and r >= 1:
        return 'critico'
    if match and f >= 1.10:
        return 'elevado'
    if contra and f <= 0.90:
        return 'bajo'
    return 'normal'


ORD = {'bajo': 0, 'normal': 1, 'elevado': 2, 'critico': 2}
COD = 'BMA'
zonas_prov = {}
for zid, z in UMB.items():
    zonas_prov.setdefault(z['provincia'], []).append((zid, z['umbral_dc_p90']))

out = {'meta': {'territorio': 'Indonesia — Sumatra + Kalimantan', 'generado': '2026-11-05',
                'codigos': {'riesgo': 'B=BAJO M=MEDIO A=ALTO', 'drivers': '.=ninguno e=enso s=sequia x=ambos -=sin dato'},
                'fase_fuente': 'ONI del trimestre centrado 2 meses antes', 'ultimo_mes_dc': ULT,
                'aviso': 'Hindcast sobre el período de calibración (ENSO 2001–2025, DC 2012–2024): coherencia in-sample. 2025 queda fuera de la calibración del término de sequía; 2026 es fuera de muestra para ambos términos.'},
       'riesgo': {}, 'drivers': {}, 'zonas_disparadas': {}}
for prov, (region, _) in T.PROVINCIAS.items():
    cl = clim([prov])
    rr, dd = {}, {}
    for y in range(Y0, Y1 + 1):
        sr = sd = ''
        for m in range(12):
            ym = f'{y}-{m + 1:02d}'
            a = oni.get(y * 12 + m - 2)
            if a is None or ym > ULT:
                sr += '-'; sd += '-'; continue
            fase = fase_de(a)
            base = ORD[nivel_v1(fase, m, region, cl)]
            disp = [zid for zid, u in zonas_prov[prov] if ym in DCM[zid] and DCM[zid][ym] > u[m]]
            n = min(base + (1 if disp else 0), 2)
            sr += COD[n]
            sd += 'x' if base == 2 and disp else 'e' if base == 2 else 's' if disp else '.'
            if disp:
                out['zonas_disparadas'].setdefault(prov, {})[ym] = disp
        rr[y], dd[y] = sr, sd
    out['riesgo'][prov], out['drivers'][prov] = rr, dd

# territorio: mapeo directo de su v1 + regla de extensión (≥10 de 15 provincias con sequía)
clt = clim(list(T.PROVINCIAS))
rt, dt_ = {}, {}
for y in range(Y0, Y1 + 1):
    sr = sd = ''
    for m in range(12):
        ym = f'{y}-{m + 1:02d}'
        a = oni.get(y * 12 + m - 2)
        if a is None or ym > ULT:
            sr += '-'; sd += '-'; continue
        base = ORD[nivel_v1(fase_de(a), m, 'territorio', clt)]
        nesc = sum(1 for p in T.PROVINCIAS if out['drivers'][p][y][m] in 'sx')
        ext = nesc >= 10
        sr += COD[min(base + ext, 2)]
        sd += ('x' if base == 2 else 's') if ext else ('e' if base == 2 else '.')
    rt[y], dt_[y] = sr, sd
out['riesgo']['_territorio'], out['drivers']['_territorio'] = rt, dt_
json.dump(out, open(os.path.join(HERE, 'gfi_id_retro.json'), 'w'), ensure_ascii=False)

# ── coherencia del hindcast (provincia-mes 2012–2025 vs fuego VIIRS observado) ──
print(f'último mes con DC: {ULT}\n')
filas = []
for prov in T.PROVINCIAS:
    ser = {int(y): v for y, v in S['VIIRS'][prov].items()}
    for y in range(2012, 2026):
        for m in range(12):
            c = out['riesgo'][prov][y][m]
            if c == '-':
                continue
            med = statistics.median(ser[k][m] for k in range(2012, 2025))
            v = ser[y][m]
            filas.append((prov, y, m, c, v >= med and v > 0, v, med))
for c in 'BMA':
    sub = [f for f in filas if f[3] == c]
    ev = sum(1 for f in sub if f[4])
    foc = sum(f[5] for f in sub)
    print(f'  {c}: {len(sub):4d} provincia-meses · fuego ≥ mediana en {100*ev/len(sub):5.1f}% · '
          f'{100*foc/sum(f[5] for f in filas):5.1f}% de todos los focos')
top = sorted(filas, key=lambda f: -(f[5] / max(f[6], 1)))[:int(len(filas) * 0.05)]
top = [f for f in top if f[5] >= 100]
print(f'\n  peores provincia-meses (top 5% por anomalía, ≥100 focos: n={len(top)}): '
      f'ALTO {sum(1 for f in top if f[3]=="A")} · MEDIO {sum(1 for f in top if f[3]=="M")} · BAJO {sum(1 for f in top if f[3]=="B")}')

print('\n  territorio por año (ene→dic):')
for y in range(Y0, Y1 + 1):
    print(f'   {y} {rt[y]}  {dt_[y]}')
print('\n  casos (riesgo / drivers):')
for prov in ('Central Kalimantan', 'South Sumatra', 'Riau', 'West Kalimantan'):
    for y in (2006 if False else 2014, 2015, 2019, 2023, 2025, 2026):
        print(f'   {prov:<20} {y} {out["riesgo"][prov][y]}  {out["drivers"][prov][y]}')
