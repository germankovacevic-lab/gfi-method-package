"""GFI Indonesia — declaración del territorio (fijada ANTES de ver resultados, 05/11/2026).

Réplica del método GFI (paper NHESS egusphere-2026-5917) sobre Sumatra + Kalimantan.
Todo lo que el método deriva del dato (zonas, ventanas, umbrales, factores ENSO) se
deriva acá con los mismos scripts/reglas que Argentina. Lo único declarado a mano es:
  1. qué jurisdicciones entran (provincias ADM1 de Sumatra y Kalimantan),
  2. la agrupación en regiones para el término ENSO (el análisis mide regiones, no
     provincias sueltas — igual que en AR),
  3. el huso horario de la lectura del mediodía (meteo FWI).

Regiones: siguen la regionalización de lluvia de Aldrian & Susanto (2003,
doi:10.1002/joc.950): el norte de Sumatra es régimen ecuatorial bimodal con respuesta
ENSO débil; el sur de Sumatra y Kalimantan, régimen monzónico con respuesta ENSO
fuerte en la estación seca. Kalimantan va como una sola región (n de provincias
chico; separarla sería elegir después de mirar).
"""

PROVINCIAS = {
    # nombre geoBoundaries (gbOpen IDN ADM1)  : (región, tz del mediodía)
    'Aceh':                    ('SUM-N', 'Asia/Jakarta'),
    'North Sumatra':           ('SUM-N', 'Asia/Jakarta'),
    'West Sumatra':            ('SUM-N', 'Asia/Jakarta'),
    'Riau':                    ('SUM-N', 'Asia/Jakarta'),
    'Riau Islands':            ('SUM-N', 'Asia/Jakarta'),
    'Jambi':                   ('SUM-S', 'Asia/Jakarta'),
    'South Sumatra':           ('SUM-S', 'Asia/Jakarta'),
    'Bengkulu':                ('SUM-S', 'Asia/Jakarta'),
    'Lampung':                 ('SUM-S', 'Asia/Jakarta'),
    'Bangka-Belitung Islands': ('SUM-S', 'Asia/Jakarta'),
    'West Kalimantan':         ('KAL', 'Asia/Jakarta'),
    'Central Kalimantan':      ('KAL', 'Asia/Jakarta'),
    'South Kalimantan':        ('KAL', 'Asia/Makassar'),
    'East Kalimantan':         ('KAL', 'Asia/Makassar'),
    'North Kalimantan':        ('KAL', 'Asia/Makassar'),
}
REGIONES = ['SUM-N', 'SUM-S', 'KAL']

import os
DATA = os.path.expanduser('~/.openclaw/data')
FIRMS = f'{DATA}/firms_id'
GEO = f'{DATA}/geo_id/idn_adm1.geojson'
METEO = f'{DATA}/gfi_id_cds'   # ERA5 puro del CDS (02b); gfi_id_meteo = Open-Meteo best_match, descartado
FWI = f'{DATA}/gfi_id_fwi'
CACHE = f'{DATA}/gfi_id_cache'

# Ventanas temporales (idénticas en espíritu a AR):
VIIRS_CAL = (2012, 2024)   # zonas + climatología DC + umbrales (13 años, como AR)
VIIRS_ALL = (2012, 2025)   # 2025 = año fuera de muestra para el término de sequía
MODIS = (2001, 2025)       # término ENSO: MODIS 2001–2011 + VIIRS 2012–2025, intra-sensor
CELL = 0.25
MAX_ZONAS = 5
SHARE_MIN = 0.08
