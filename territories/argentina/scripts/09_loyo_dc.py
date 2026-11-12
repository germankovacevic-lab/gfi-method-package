#!/usr/bin/env python3
"""GFI — Fase 1 NHESS: leave-one-year-out (LOYO) del término de sequía.

Definiciones IDÉNTICAS a paper/zenodo_package/06_verificacion.py (calibración 2.2.0):
  DC de zona  = media MÓVIL de 30 días al último día del mes (≥25 días con dato), 2 dec.
  DISPARO     = dc > umbral, umbral in-sample = 11º menor de las 13 móviles de ese mes 2012–2024.
  EVENTO      = focos del zona-mes ≥ mediana de los 13 mismos-meses, y > 0.

LOYO por año Y (fold Y): umbral del mes = 11º menor de las 12 móviles de los años ≠ Y;
la predicción del año Y se evalúa contra ese umbral. Propiedad algebraica esperada:
para una regla de RANGO con > estricto, "v > 11º de los 12 restantes" ⟺ "v le gana a
≥11 de los otros 12" ⟺ la regla in-sample (la auto-comparación v<v es siempre falsa).
El script lo VERIFICA numéricamente y agrega dos variantes más exigentes:
  (a) rank 10-de-12 (mantiene la semántica top-2 sobre 12 años → operating point más laxo);
  (b) LOYO también de la mediana del EVENTO (mediana de los 12 mismos-meses sin Y).

Uso: python3 09_loyo_dc.py   (sin red, ~10 s; requiere los insumos de 06 — ver DATOS.md)
"""
import json, csv, statistics, os, datetime as dt
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = HERE
D = os.path.expanduser('~/.openclaw/data/gfi_v2_fwi_cds')
Z = json.load(open(os.path.join(PKG, 'zonas_fuego.json')))['zonas']
CAL = json.load(open(os.path.join(PKG, 'enso_calibracion.json')))
UMB = CAL['v2']['zonas']
FZ = json.load(open(os.path.expanduser('~/.openclaw/data/gfi_v2_focos_zona.json')))
YS = list(range(2012, 2025))


def diario(zid, col='dc'):
    out = {}
    for r in csv.DictReader(open(f'{D}/fwi_{zid}.csv')):
        out[r['date']] = float(r[col])
    return out


def metricas(a, b, c, d):
    pod, far = a / (a + c), b / (a + b)
    pofd = b / (b + d)
    n = a + b + c + d
    esp = ((a + b) * (a + c) + (c + d) * (b + d)) / n
    return dict(prec=a / (a + b), pod=pod, far=far, pofd=pofd,
                bias=(a + b) / (a + c), pss=pod - pofd,
                hss=((a + d) - esp) / (n - esp))


# ── carga: móvil 30d de fin de mes por (zona, año, mes) + focos ────────────────
print('leyendo las 116 zonas…')
regs = []  # (año, mes, prov, j, dc_movil, umbral_in_sample, focos_serie_13, focos_y)
for prov, zs in Z.items():
    for j, z in enumerate(zs):
        zid = f"{z['lat']:.2f}_{z['lon']:.2f}"
        s = diario(zid)
        foc = FZ[prov][j]
        umb = UMB[zid]['umbral_dc_p90']
        for m in range(1, 13):
            fila = {}
            for a in YS:
                ult0 = dt.date(a + (m == 12), (m % 12) + 1, 1) - dt.timedelta(days=1)
                v0 = [s[(ult0 - dt.timedelta(days=k)).isoformat()] for k in range(30)
                      if (ult0 - dt.timedelta(days=k)).isoformat() in s]
                if len(v0) >= 25:
                    fila[a] = round(sum(v0) / len(v0), 2)
            if len(fila) < 13:
                continue  # mismo criterio que la derivación (climatología completa)
            ser_foc = [foc.get(f'{y}-{m:02d}', 0) for y in YS]
            for a in YS:
                regs.append((a, m, prov, j, fila[a], umb[m - 1], fila, ser_foc,
                             foc.get(f'{a}-{m:02d}', 0)))

print(f'zona-meses evaluables: {len(regs)}')

# sanity: el umbral in-sample del artefacto == 11º menor de las 13 móviles
mal = sum(1 for r in regs if abs(sorted(r[6].values())[10] - r[5]) > 0.005)
print(f'sanity umbral 2.2.0 (s[10] de las 13 móviles == artefacto): '
      f'{"OK" if mal == 0 else f"{mal} DIFIEREN"}')


def evento(ser, v):
    return v >= statistics.median(ser) and v > 0


def evento_loyo(ser, idx, v):
    resto = [x for i, x in enumerate(ser) if i != idx]
    return v >= statistics.median(resto) and v > 0


def contingencia(pred_ev):
    a = sum(1 for p, e in pred_ev if p and e)
    b = sum(1 for p, e in pred_ev if p and not e)
    c = sum(1 for p, e in pred_ev if not p and e)
    d = sum(1 for p, e in pred_ev if not p and not e)
    return a, b, c, d


VAR = {
    'in-sample (paper §4)':
        lambda r: (r[4] > r[5], evento(r[7], r[8])),
    'LOYO rank 11-de-12 (mismo operating point)':
        lambda r: (r[4] > sorted(v for y, v in r[6].items() if y != r[0])[10],
                   evento(r[7], r[8])),
    'LOYO rank 10-de-12 (top-2 de 12, más laxo)':
        lambda r: (r[4] > sorted(v for y, v in r[6].items() if y != r[0])[9],
                   evento(r[7], r[8])),
    'LOYO 11-de-12 + mediana del evento LOYO':
        lambda r: (r[4] > sorted(v for y, v in r[6].items() if y != r[0])[10],
                   evento_loyo(r[7], YS.index(r[0]), r[8])),
}

print('\n== TABLA LOYO (pooled, N=%d) ==' % len(regs))
print(f'{"variante":47s} {"disp":>5s} {"prec":>6s} {"POD":>6s} {"FAR":>6s} '
      f'{"bias":>6s} {"PSS":>7s} {"HSS":>7s}')
res = {}
for nom, f in VAR.items():
    pe = [f(r) for r in regs]
    a, b, c, d = contingencia(pe)
    M = metricas(a, b, c, d)
    res[nom] = (pe, (a, b, c, d), M)
    print(f'{nom:47s} {a+b:5d} {100*M["prec"]:5.1f}% {100*M["pod"]:5.1f}% '
          f'{100*M["far"]:5.1f}% {M["bias"]:6.3f} {M["pss"]:7.4f} {M["hss"]:7.4f}')

ins = res['in-sample (paper §4)'][0]
loy = res['LOYO rank 11-de-12 (mismo operating point)'][0]
dif = sum(1 for x, y in zip(ins, loy) if x[0] != y[0])
print(f'\nEquivalencia algebraica in-sample ⟺ LOYO 11-de-12: '
      f'{dif} disparos difieren de {len(regs)}'
      f' → {"CONFIRMADA (idénticos)" if dif == 0 else "NO se cumple, revisar"}')

# ── por año: cada fila usa el umbral derivado SIN ese año ─────────────────────
print('\n== POR AÑO (LOYO 11-de-12; cada año contra umbral sin sí mismo) ==')
print('  año | n disp | acier | prec   | base  | PSS')
for Y in YS:
    sub = [(p, e) for r, (p, e) in zip(regs, loy) if r[0] == Y]
    a, b, c, d = contingencia(sub)
    n = a + b
    base = 100 * (a + c) / len(sub)
    if n == 0:
        print(f' {Y} | {n:6d} |     – |      – | {base:4.1f}% |      –')
        continue
    M = metricas(a, b, c, d) if (a + c) and (b + d) else None
    print(f' {Y} | {n:6d} | {a:5d} | {100*a/n:5.1f}% | {base:4.1f}% |'
          f' {M["pss"]:7.4f}' if M else f' {Y} | {n:6d} | {a:5d} | {100*a/n:5.1f}% | {base:4.1f}% |       –')
