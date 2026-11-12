#!/usr/bin/env python3
"""GFI — verificación: reproduce las cifras de §4 del paper que 05b no cubre.

Corre desde este directorio, sin red. Requiere las series diarias de DC/FWI por
zona en ~/.openclaw/data/gfi_v2_fwi/ y la asignación de focos por zona en
~/.openclaw/data/gfi_v2_focos_zona.json (la produce 05a). Ver DATOS.md.

Produce, en orden:
  1. Tabla de contingencia zonal 2×2 + precisión, POD, FAR, POFD, bias, PSS, HSS.
  2. IC95 por bootstrap de BLOQUE-AÑO (remuestrea los 13 años, no los zona-mes:
     la media móvil de 30 días y el clima regional compartido los autocorrelacionan).
  3. Baseline de climatología mensual pura, igualada en tasa de disparo.
  4. Tabla de lead time (precisión a lags 0..4).
  5. Regla país: estadístico operativo (móvil 30d, el calibrado desde 2.2.0)
     y media de mes calendario como sensibilidad.
  6. Conteos del gate estacional (178 / 145 / 33 / 9).

Definiciones (idénticas a 05b y al motor de producción — calibración ≥ 2.2.0):
  DC de zona          = media MÓVIL de 30 días evaluada al último día del mes
                        (ventana [fin−29, fin], mínimo 25 días con dato — el
                        estadístico que opera el worker)
  DISPARO             = DC (2 decimales) > umbral_dc_p90[mes]; el umbral es el 11º
                        menor de las 13 móviles de fin de ese mes calendario
                        2012–2024 (leave-nothing-out, top-2 de 13)
  EVENTO observado    = focos de esa zona ese mes ≥ mediana de los 13 mismos-meses, y > 0
  (hasta calibración 2.1.x el umbral salía de medias de mes calendario: lo
   calibrado no era lo operado — §6.5b del paper; resuelto en 2.2.0)
"""
import json, csv, statistics, os, random, datetime as dt
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.expanduser('~/.openclaw/data/gfi_v2_fwi_cds')
Z = json.load(open(os.path.join(HERE, 'zonas_fuego.json')))['zonas']
CAL = json.load(open(os.path.join(HERE, 'enso_calibracion.json')))
UMB = CAL['v2']['zonas']
FZ = json.load(open(os.path.expanduser('~/.openclaw/data/gfi_v2_focos_zona.json')))
HIST = json.load(open(os.path.join(HERE, 'historico.json')))
YS = list(range(2012, 2025))
MESES = [f'{a}-{m:02d}' for a in YS for m in range(1, 13)]


def diario(zid, col='dc'):
    out = {}
    for r in csv.DictReader(open(f'{D}/fwi_{zid}.csv')):
        out[r['date']] = float(r[col])
    return out


def por_mes(s):
    acc = defaultdict(list)
    for d, v in s.items():
        acc[d[:7]].append(v)
    return {ym: sum(v) / len(v) for ym, v in acc.items()}


def metricas(a, b, c, d):
    pod, far = a / (a + c), b / (a + b)
    pofd = b / (b + d)
    n = a + b + c + d
    esp = ((a + b) * (a + c) + (c + d) * (b + d)) / n
    return dict(prec=a / (a + b), pod=pod, far=far, pofd=pofd,
                bias=(a + b) / (a + c), pss=pod - pofd,
                hss=((a + d) - esp) / (n - esp))


# ── carga: por zona-mes, (año, mes, disparo, evento a lags 0..4) ────────────────
print('leyendo las 116 zonas…')
regs, share, disp_cal, disp_roll = [], {}, defaultdict(set), defaultdict(set)
for prov, zs in Z.items():
    for j, z in enumerate(zs):
        zid = f"{z['lat']:.2f}_{z['lon']:.2f}"
        s = diario(zid)
        mens = por_mes(s)
        foc = FZ[prov][j]
        tot = sum(foc.values()) or 1
        share[(prov, j)] = {m: sum(foc.get(f'{y}-{m:02d}', 0) for y in YS) / tot
                            for m in range(1, 13)}
        umb = UMB[zid]['umbral_dc_p90']
        for a in YS:
            for m in range(1, 13):
                ym = f'{a}-{m:02d}'
                clim = [mens.get(f'{y}-{m:02d}') for y in YS]
                if None in clim:
                    continue
                # estadístico OPERATIVO: móvil 30d al último día del mes vs umbral 2.2.0
                ult0 = dt.date(a + (m == 12), (m % 12) + 1, 1) - dt.timedelta(days=1)
                v0 = [s[(ult0 - dt.timedelta(days=k)).isoformat()] for k in range(30)
                      if (ult0 - dt.timedelta(days=k)).isoformat() in s]
                if len(v0) < 25:
                    continue
                dispara = round(sum(v0) / len(v0), 2) > umb[m - 1]
                ev = []
                for k in range(5):
                    t = a * 12 + (m - 1) + k
                    ay, am = t // 12, t % 12 + 1
                    if ay > 2024:
                        ev.append(None); continue
                    ser = [foc.get(f'{y}-{am:02d}', 0) for y in YS]
                    v = foc.get(f'{ay}-{am:02d}', 0)
                    ev.append(v >= statistics.median(ser) and v > 0)
                regs.append((a, m, prov, j, dispara, ev))
                # regla país: operativo (= dispara) y calendario (sensibilidad)
                if dispara:
                    disp_roll[ym].add(prov)
                if round(mens[ym], 2) > umb[m - 1]:
                    disp_cal[ym].add(prov)

# ── 1) contingencia + métricas ────────────────────────────────────────────────
a = sum(1 for r in regs if r[4] and r[5][0])
b = sum(1 for r in regs if r[4] and not r[5][0])
c = sum(1 for r in regs if not r[4] and r[5][0])
d = sum(1 for r in regs if not r[4] and not r[5][0])
M = metricas(a, b, c, d)
print(f'\n1) CONTINGENCIA ZONAL  N={a+b+c+d}  a={a} b={b} c={c} d={d}')
print(f'   tasa de disparo = {100*(a+b)/(a+b+c+d):.2f}% · base rate = {100*(a+c)/(a+b+c+d):.1f}%')
print(f'   precisión={100*M["prec"]:.1f}%  POD={100*M["pod"]:.1f}%  FAR={100*M["far"]:.1f}%'
      f'  POFD={100*M["pofd"]:.1f}%  bias={M["bias"]:.3f}')
print(f'   PSS={M["pss"]:.4f}  HSS={M["hss"]:.4f}')

# ── 2) IC95 bootstrap de bloque-año ───────────────────────────────────────────
random.seed(11)
por_anio = defaultdict(list)
for (y, m, p, j, dp, ev) in regs:
    por_anio[y].append((dp, ev[0]))
bs_prec, bs_pss = [], []
for _ in range(3000):
    S = []
    for _ in YS:
        S += por_anio[random.choice(YS)]
    A = sum(1 for x in S if x[0] and x[1]); B = sum(1 for x in S if x[0] and not x[1])
    C = sum(1 for x in S if not x[0] and x[1]); Dd = sum(1 for x in S if not x[0] and not x[1])
    mm = metricas(A, B, C, Dd)
    bs_prec.append(100 * mm['prec']); bs_pss.append(mm['pss'])
bs_prec.sort(); bs_pss.sort()
print(f'\n2) IC95 BLOQUE-AÑO  precisión [{bs_prec[74]:.1f}%, {bs_prec[2924]:.1f}%]'
      f' · PSS [{bs_pss[74]:.4f}, {bs_pss[2924]:.4f}]')
print(f'   (binomial ingenuo sobre la precisión: ±{100*(M["prec"]*(1-M["prec"])/(a+b))**.5*1.96:.1f} pp)')

# ── 3) baseline de climatología mensual pura, igualada en tasa de disparo ──────
rk = sorted(((share[(p, j)][m], p, j, y, m) for (y, m, p, j, dp, ev) in regs), reverse=True)
sel = set((p, j, y, m) for _, p, j, y, m in rk[:a + b])
a2 = sum(1 for (y, m, p, j, dp, ev) in regs if (p, j, y, m) in sel and ev[0])
b2 = sum(1 for (y, m, p, j, dp, ev) in regs if (p, j, y, m) in sel and not ev[0])
c2 = sum(1 for (y, m, p, j, dp, ev) in regs if (p, j, y, m) not in sel and ev[0])
d2 = sum(1 for (y, m, p, j, dp, ev) in regs if (p, j, y, m) not in sel and not ev[0])
M2 = metricas(a2, b2, c2, d2)
print(f'\n3) BASELINE CLIMATOLOGÍA MENSUAL (k={a+b}, misma tasa de disparo)')
print(f'   precisión={100*M2["prec"]:.1f}%  POD={100*M2["pod"]:.1f}%  PSS={M2["pss"]:.4f}  HSS={M2["hss"]:.4f}')
print(f'   >>> el término de sequía {"GANA" if M["pss"] > M2["pss"] else "PIERDE"}:'
      f' PSS {M["pss"]:.4f} vs {M2["pss"]:.4f}')

# ── 4) lead time ──────────────────────────────────────────────────────────────
print('\n4) LEAD TIME (precisión por lag)')
print('   lag | n disparos | precisión | base  | delta')
for k in range(5):
    e = [r[5][k] for r in regs if r[4] and r[5][k] is not None]
    bb = [r[5][k] for r in regs if r[5][k] is not None]
    pe, pb = 100 * sum(e) / len(e), 100 * sum(bb) / len(bb)
    print(f'    +{k}  | {len(e):10d} | {pe:8.1f}% | {pb:5.1f}% | {pe-pb:+5.1f} pp')

# ── 5) regla país bajo los dos estadísticos ───────────────────────────────────
ar = HIST['ar']['mensual']


def fuego_pais(ym):
    y, m = int(ym[:4]), int(ym[5:7])
    ser = [ar[str(k)][m - 1] for k in YS if str(k) in ar]
    return ar[str(y)][m - 1] >= statistics.median(ser)


print('\n5) REGLA PAÍS — el estadístico cambia el resultado')
for nom, dd in [('media móvil 30d (OPERATIVO)', disp_roll), ('media de mes calendario (sensibilidad — desde 2.2.0 el estadístico calibrado ES la móvil)', disp_cal)]:
    print(f'   {nom}:')
    for thr in (14, 15, 16, 17, 18):
        act = [ym for ym in MESES if len(dd.get(ym, ())) >= thr]
        h = sum(1 for ym in act if fuego_pais(ym))
        print(f'     ≥{thr}/24 → {len(act):3d}/156 meses · fuego país ≥ mediana'
              f' {h:3d} ({100*h/len(act) if act else 0:5.1f}%)')
act16 = [ym for ym in MESES if len(disp_roll.get(ym, ())) >= 16]
print(f'   ≥16 móvil: n={len(act16)} · meses: {" ".join(sorted(act16))}')
print(f'   fallos: {" ".join(sorted(ym for ym in act16 if not fuego_pais(ym))) or "ninguno"}')
print(f'   activaciones en años tranquilos (2014-2017, 2024): '
      f'{sorted(ym for ym in act16 if ym[:4] in ("2014","2015","2016","2017","2024")) or "ninguna"}')

# ── 6) gate estacional ────────────────────────────────────────────────────────
clim = CAL['climatologia']
PESOS = [4, 3, 2, 1]
bajo8, cierra, sobrevive, casi_cero = 0, 0, 0, 0
for prov, cl in clim.items():
    if prov == 'pais':
        continue
    tot = sum(cl)
    if tot < 24:
        continue
    for mes in range(12):
        sh = cl[mes] / tot
        if sh >= 0.08:
            continue
        bajo8 += 1
        r = (sum(PESOS[i] * cl[(mes + i) % 12] for i in range(4)) / tot) * (12 / 10)
        if r < 1.0:
            cierra += 1
        else:
            sobrevive += 1
        if cl[mes] <= 5:
            casi_cero += 1
print(f'\n6) GATE ESTACIONAL  pares (jurisdicción, mes) con share < 8%: {bajo8}')
print(f'   el gate los apaga (r < 1.0): {cierra} · sobreviven (r ≥ 1.0): {sobrevive}')
print(f'   de los {bajo8}, con registro casi nulo (mediana ≤ 5 focos): {casi_cero}')
print('   nota: el gate NUNCA puede apagar un mes con share ≥ 8% — es garantía')
print('         algebraica de la regla (condición necesaria), no resultado empírico.')
