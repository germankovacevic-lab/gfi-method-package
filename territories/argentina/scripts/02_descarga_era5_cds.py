#!/usr/bin/env python3
"""GFI — ERA5 por punto desde el Copernicus CDS (dataset reanalysis-era5-single-levels-timeseries).

Alternativa oficial a 02_descarga_meteo.py (Open-Meteo): mismo reanálisis ERA5, sin el
límite por IP. Produce EXACTAMENTE el mismo formato (date,temp,rh,wind,rain24):
  temp  = 2 m temperature a las 12:00 locales (°C)
  rh    = humedad relativa de t2m y d2m (Magnus, misma fórmula que Open-Meteo)
  wind  = |(u10, v10)| a las 12:00 locales, km/h
  rain24= precipitación total de las 24 h (12:00−23 h … 12:00], mm
Requiere ~/.cdsapirc. Uso:
  python3 02b_descarga_cds.py <lat> <lon> <tz> <salida.csv>
"""
import os, sys, zipfile, tempfile, io
import numpy as np
import pandas as pd
import cdsapi

lat, lon, tz, out = float(sys.argv[1]), float(sys.argv[2]), sys.argv[3], sys.argv[4]
VARS = ['2m_temperature', '2m_dewpoint_temperature', '10m_u_component_of_wind',
        '10m_v_component_of_wind', 'total_precipitation']
tmpd = tempfile.mkdtemp()
target = os.path.join(tmpd, 'ts.zip')
cdsapi.Client(quiet=True).retrieve('reanalysis-era5-single-levels-timeseries', {
    'variable': VARS, 'location': {'longitude': lon, 'latitude': lat},
    'date': ['2011-09-30/2026-11-04'], 'data_format': 'csv'}, target)

raw = open(target, 'rb').read()
if raw[:2] == b'PK':
    z = zipfile.ZipFile(io.BytesIO(raw))
    df = pd.concat([pd.read_csv(z.open(n)) for n in z.namelist() if n.endswith('.csv')], axis=1)
else:
    df = pd.read_csv(io.BytesIO(raw))
df = df.loc[:, ~df.columns.duplicated()]
tcol = 'valid_time' if 'valid_time' in df else 'time'
df['t'] = pd.to_datetime(df[tcol], utc=True).dt.tz_convert(tz).dt.tz_localize(None)
df = df.set_index('t').sort_index()
T = df['t2m'] - 273.15
Td = df['d2m'] - 273.15
a, b = 17.625, 243.04
rh = 100 * np.exp(a * Td / (b + Td)) / np.exp(a * T / (b + T))
wind = np.hypot(df['u10'], df['v10']) * 3.6
tp = df['tp'] * 1000
noon = df.index[df.index.hour == 12]
rain24 = [tp.loc[t - pd.Timedelta(hours=23): t].sum() for t in noon]
pd.DataFrame({'date': noon.date, 'temp': T.loc[noon].round(1).values, 'rh': rh.loc[noon].round(0).values,
              'wind': wind.loc[noon].round(1).values, 'rain24': np.round(rain24, 2)}).to_csv(out, index=False)
print(out, len(noon), 'días')
