#!/usr/bin/env python3
"""Calibración 3.0 — el archivo ÚNICO que comparten el paquete Zenodo 1.2, el paper v2 y producción.
Un archivo por territorio: paper/zenodo_package_v1.2/territories/<t>/calibracion_3.0.json

Contenido (todo derivado de ERA5 CDS 2012–2024 + FIRMS + ONI; nada de 2025–2026):
  zonas (lat, lon, peso, umbral_dc[12] = 11º menor de las 13 móviles 30 d a fin de mes),
  regiones y mapeo provincia→región, ventanas de temporada, señal ENSO por región
  (criterio: IC95 bloque-año del cociente Niña/Niño a lag 3 excluye 1) con factores e IC,
  climatología mensual por provincia (gate), regla de extensión REGIONAL (umbral LOYO) y
  las reglas de combinación en texto. Reglas: ver engine/gfi_rules_v3.py.
Uso: python3 10_calibracion_v3.py AR | ID
"""
import json, csv, os, sys, statistics, datetime as dt
T = sys.argv[1]
HOME = os.path.expanduser('~'); G = f'{HOME}/.openclaw/workspace/geofuego'; DATA = f'{HOME}/.openclaw/data'; RES = f'{G}/paper/v2/resultados'
OUT = f'{G}/paper/zenodo_package_v1.2/territories/{"argentina" if T == "AR" else "indonesia"}'; os.makedirs(OUT, exist_ok=True)
YS = list(range(2012, 2025)); MESES = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic']
E = json.load(open(f'{RES}/enso_{T}.json')); M3 = json.load(open(f'{RES}/motor_v3_{T}.json'))
if T == 'AR':
    P = f'{G}/tools/gfi_era5_ar/pkg_cds'; ZON = json.load(open(f'{P}/zonas_fuego.json'))['zonas']; FWI = f'{DATA}/gfi_v2_fwi_cds'
    CAL = json.load(open(f'{P}/enso_calibracion.json')); REGION = CAL['provincia_region']; CLIM = {p: v for p, v in CAL['climatologia'].items() if p != 'pais'}
    AMB_T = 'pais'; nombre = 'Argentina'; fuentes_geo = 'IGN (límites provinciales)'
else:
    sys.path.insert(0, f'{G}/tools/gfi_id'); import territorio as TT
    ZON = json.load(open(f'{G}/tools/gfi_id/zonas_fuego.json'))['zonas']; FWI = f'{DATA}/gfi_id_fwi'
    REGION = {p: r for p, (r, _) in TT.PROVINCIAS.items()}
    S = json.load(open(f'{DATA}/gfi_id_cache/series.json'))['VIIRS']
    CLIM = {p: [statistics.median([S[p][str(y)][m] for y in range(2012, 2026) if str(y) in S[p]]) for m in range(12)] for p in REGION}
    AMB_T = 'territorio'; nombre = 'Sumatra + Kalimantan (Indonesia)'; fuentes_geo = 'geoBoundaries gbOpen IDN ADM1 (ODbL)'

def movil(s, y, m, W=30):
    fin = dt.date(y + (m == 12), (m % 12) + 1, 1) - dt.timedelta(days=1)
    v = [s[k] for k in ((fin - dt.timedelta(days=i)).isoformat() for i in range(W)) if k in s]
    return round(sum(v) / len(v), 2) if len(v) >= 25 else None
zonas = {}
for p, zs in ZON.items():
    if p not in REGION: continue
    zonas[p] = []
    for z in zs:
        s = {}
        for r in csv.DictReader(open(f"{FWI}/fwi_{z['lat']:.2f}_{z['lon']:.2f}.csv")): s[r['date']] = float(r['dc'])
        umb = []
        for m in range(1, 13):
            clim = [movil(s, y, m) for y in YS]
            umb.append(None if None in clim else sorted(clim)[10])
        zonas[p].append(dict(lat=z['lat'], lon=z['lon'], peso=z.get('peso'), n_focos=z.get('n_focos'), umbral_dc=umb))
senales = {}
for a, sg in M3['senales_v3'].items():
    o = E['ambitos'][a]['lags']['3']
    senales[a] = dict(tipo=sg['tipo'], criterio='IC95 bloque-año del cociente Niña/Niño a lag 3 excluye 1', cociente_nina_nino=round(o['factor']['nina'] / o['factor']['nino'], 3),
                      cociente_ic95=[round(x, 3) for x in sg['ratio_ci']], factores_lag3={k: dict(factor=round(v, 3), n=o['n'][k], ic95=[round(x, 3) for x in o['ci'][k]]) for k, v in o['factor'].items()},
                      p_perm_nina_vs_resto=o['p_nina_vs_resto'], p_perm_nino_vs_resto=o['p_nino_vs_resto'])
ext = {r: dict(N=v['N'], umbral=v['umbral_full'], umbrales_loyo=v['umbrales_loyo'], pss_loyo=round(v['loyo']['pss'], 3)) for r, v in M3['v3a']['extension_regional'].items()}
cal = {
    'version': '3.0.0', 'territorio': nombre, 'generado': dt.date.today().isoformat(),
    'fuentes': {'fuego': 'NASA FIRMS VIIRS S-NPP 2012–2024 (conf != l, type 0) para zonas, climatologías y umbrales; MODIS 2001–2025 + VIIRS 2012–2025 (intra-sensor) para el término ENSO',
                'meteorologia': 'ERA5 (Copernicus Climate Data Store, reanalysis-era5-single-levels-timeseries) en el centroide de cada zona; FWI Van Wagner 1987' + ('; factores de duración del día ecuatoriales Le=9, Lf=1.4' if T == 'ID' else '; hemisferio sur'),
                'enso': 'ONI NOAA/CPC, ±0.5 °C, trimestre asignado al mes central', 'limites': fuentes_geo},
    'regiones': sorted(set(REGION.values())), 'provincia_region': REGION, 'ambito_total': AMB_T,
    'ventanas': E['ventanas'], 'senales': senales,
    'climatologia_mensual': CLIM, 'gate': {'pesos': [4, 3, 2, 1], 'share_min': 0.08, 'r_min': 1.0, 'total_min': 24},
    'sequia': {'estadistico': 'media móvil 30 d de DC diario al último día con dato (mín. 25 días)', 'umbral': '11º menor de las 13 móviles de fin de ese mes calendario 2012–2024 (top-2 de 13); dispara con dc > umbral',
               'escalacion': 'A-zonal: cualquier zona de la provincia por encima de su umbral sube UN escalón (cap ALTO); se nombra la zona'},
    'extension_regional': ext,
    'reglas': ['base MEDIO', 'gate: fuera de temporada → BAJO (la sequía igual sube un escalón)', 'sequía → +1 escalón',
               'ENSO: en región con señal, fase contraria sin sequía → BAJO; fase coincidente sin sequía → MEDIO (declarado); coincidente + sequía → ALTO convergente; el ENSO solo nunca llega a ALTO',
               'región: ALTO regional cuando las provincias escaladas alcanzan extension_regional.umbral', 'país/territorio: informativo, derivado de las regiones; no es objeto de verificación'],
    'zonas': zonas,
}
json.dump(cal, open(f'{OUT}/calibracion_3.0.json', 'w'), indent=1, ensure_ascii=False)
print(f'→ {OUT}/calibracion_3.0.json · zonas {sum(len(v) for v in zonas.values())} · señales {[(a, s["tipo"]) for a, s in senales.items()]} · extensión {[(r, v["umbral"], v["N"]) for r, v in ext.items()]}')
