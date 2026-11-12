#!/usr/bin/env python3
"""GFI — reparto estacional del fuego por región, y el término ENSO en ventanas alternativas.

Sostiene la limitación §6.1b del paper: la ventana jul–nov del término ENSO se aplica a
las CUATRO regiones, pero captura ~88% del fuego del NOA y solo ~25% del de Patagonia,
cuyo pico es dic–feb. El nulo patagónico es por eso un nulo DE ESTA VENTANA, no una
ausencia medida de teleconexión en la región.

⚠️ ALCANCE DECLARADO: este script usa SOLO VIIRS 2012–2025 (historico.json), no la serie
pooled MODIS+VIIRS de derive_enso_calibracion.mjs. Son 14 temporadas y los n por celda
quedan chicos; los factores NO son comparables uno a uno con los de §3.1, que son la
calibración oficial. Sirve para lo que se afirma con él: (a) el reparto mensual del fuego
por región, que es puro conteo y no depende del pooling, y (b) mostrar que la separación
entre fases CAMBIA según la ventana. El barrido de lags con la serie completa está en
07_barrido_lags.mjs, y de ahí sale el p=0,033 de Patagonia a lag 9 que cita §6.1b.

Requiere: historico.json (en este paquete) + ~/.openclaw/data/firms_ar/oni.ascii.txt (DATOS.md).
Uso: python3 08_ventana_por_region.py
"""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
H = json.load(open(os.path.join(HERE, 'historico.json')))
ONI_PATH = os.path.expanduser('~/.openclaw/data/firms_ar/oni.ascii.txt')

SEAS = {'DJF': 0, 'JFM': 1, 'FMA': 2, 'MAM': 3, 'AMJ': 4, 'MJJ': 5,
        'JJA': 6, 'JAS': 7, 'ASO': 8, 'SON': 9, 'OND': 10, 'NDJ': 11}
oni = {}
for ln in open(ONI_PATH):
    c = ln.split()
    if len(c) != 4 or c[0] not in SEAS:
        continue
    oni[(int(c[1]), SEAS[c[0]])] = float(c[3])


def fase(y, m, lag=3):
    t = y * 12 + m - lag
    a = oni.get((t // 12, t % 12))
    return None if a is None else ('nino' if a >= .5 else 'nina' if a <= -.5 else 'neutral')


REG = {
    'NOA': ['Jujuy', 'Salta', 'Tucumán', 'Catamarca', 'La Rioja'],
    'NEA': ['Misiones', 'Corrientes', 'Entre Ríos', 'Formosa', 'Chaco', 'Santa Fe', 'Santiago del Estero'],
    'Centro': ['Córdoba', 'San Luis', 'Mendoza', 'San Juan', 'La Pampa', 'Buenos Aires',
               'Ciudad Autónoma de Buenos Aires'],
    'Patagonia': ['Neuquén', 'Río Negro', 'Chubut', 'Santa Cruz',
                  'Tierra del Fuego, Antártida e Islas del Atlántico Sur'],
}
YS = list(range(2012, 2026))
VENTANA_MOTOR = [6, 7, 8, 9, 10]          # jul–nov, 0-based — la que usa el término ENSO
VENTANAS = {'jul–nov (la del motor)': VENTANA_MOTOR,
            'dic–mar (verano austral)': [11, 0, 1, 2],
            'ene–feb (pico patagónico)': [0, 1]}


def med(v):
    s = sorted(v); h = len(s) // 2
    return s[h] if len(s) % 2 else (s[h - 1] + s[h]) / 2


def serie(provs):
    out = {}
    for y in YS:
        a = [0] * 12
        for p in provs:
            m = H['prov'].get(p, {}).get('mensual', {}).get(str(y))
            if m:
                for i in range(12):
                    a[i] += m[i]
        out[y] = a
    return out


def factores(provs, vent):
    S = serie(provs)
    mm = [med([S[y][m] for y in YS]) for m in range(12)]
    g = {'nina': [], 'neutral': [], 'nino': []}
    for y in YS:
        for m in vent:
            if mm[m] < 5:                 # mismo filtro que el derivador oficial
                continue
            f = fase(y, m)
            if f:
                g[f].append(S[y][m] / mm[m])
    return {k: (round(med(v), 2) if v else None, len(v)) for k, v in g.items()}


MES = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic']
print('REPARTO MENSUAL DEL FUEGO POR REGIÓN (VIIRS 2012–2025, % del total de la región)')
print('  región      ' + ' '.join(f'{m:>4}' for m in MES) + '   jul–nov')
for r, ps in REG.items():
    S = serie(ps)
    tot = [sum(S[y][m] for y in YS) for m in range(12)]
    T = sum(tot) or 1
    sh = [100 * t / T for t in tot]
    print(f'  {r:11s} ' + ' '.join(f'{s:4.0f}' for s in sh)
          + f'   {sum(sh[m] for m in VENTANA_MOTOR):5.0f}%')
print()
print('  → la ventana del motor captura casi todo el fuego del NOA y una fracción del patagónico:')
print('    ESE es el contenido de la limitación §6.1b.')
print()

print('FACTOR ENSO (lag 3) POR VENTANA — mediana de anomalía, VIIRS 2012–2025 ÚNICAMENTE')
print('(no comparable uno a uno con §3.1, que agrupa MODIS+VIIRS — ver el encabezado)')
for r in REG:
    print(f'  ━━ {r} ━━')
    for nom, v in VENTANAS.items():
        f = factores(REG[r], v)
        ni, ne, no = f['nina'], f['neutral'], f['nino']
        lider = ('Niño' if (no[0] and ni[0] and no[0] > ni[0])
                 else 'Niña' if (ni[0] and no[0] and ni[0] > no[0]) else '—')
        print(f'    {nom:26s} Niña {str(ni[0]):5s}(n={ni[1]:2d}) · neutral {str(ne[0]):5s}(n={ne[1]:2d})'
              f' · Niño {str(no[0]):5s}(n={no[1]:2d})  → lidera {lider}')
