#!/usr/bin/env python3
"""GFI v2 — Paso 2: meteo histórica ERA5 (Open-Meteo Archive) para las zonas de fuego.

Mismo patrón que copernicus/tools/fuego/01_descarga_meteo.py: hourly T/HR/viento/precip,
reducido a valores de 12:00 locales + lluvia 24h previas al mediodía.

- Puntos: zonas_fuego.json (todas las zonas de todas las provincias).
- Rango: 2011-10-01 (spin-up 92 días antes de 2012) → hoy.
- Chunks de ~4 años con 1 día de solape (rain24 cruza el borde), throttle + backoff 429.
- Cache reanudable: ~/.openclaw/data/gfi_v2_meteo/meteo_<lat>_<lon>.csv — si existe, skip.

Uso: python3 02_descarga_meteo.py
"""
import json
import os
import sys
import time
import datetime as dt

import requests
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.expanduser("~/.openclaw/data/gfi_v2_meteo")
URL = "https://archive-api.open-meteo.com/v1/archive"
TZ = "America/Argentina/Buenos_Aires"
START = dt.date(2011, 10, 1)
END = dt.date.today()
CHUNK_YEARS = 4
SLEEP = 1.2          # pausa entre requests (Open-Meteo tira 429 con ráfagas)
MAX_RETRIES = 6


def point_id(lat, lon):
    return f"{lat:.2f}_{lon:.2f}"


def fetch_chunk(lat, lon, d0, d1):
    params = {
        "latitude": lat, "longitude": lon,
        "start_date": d0.isoformat(), "end_date": d1.isoformat(),
        "hourly": "temperature_2m,relative_humidity_2m,wind_speed_10m,precipitation",
        "timezone": TZ,
    }
    for attempt in range(MAX_RETRIES):
        try:
            r = requests.get(URL, params=params, timeout=180)
            if r.status_code == 429:
                wait = 30 * (attempt + 1)
                print(f"    429 → sleep {wait}s", flush=True)
                time.sleep(wait)
                continue
            r.raise_for_status()
            h = r.json()["hourly"]
            return pd.DataFrame({
                "time": pd.to_datetime(h["time"]),
                "temp": h["temperature_2m"],
                "rh": h["relative_humidity_2m"],
                "wind": h["wind_speed_10m"],   # km/h
                "precip": h["precipitation"],  # mm
            })
        except requests.RequestException as e:
            wait = 15 * (attempt + 1)
            print(f"    error {e} → retry en {wait}s", flush=True)
            time.sleep(wait)
    raise RuntimeError(f"punto ({lat},{lon}) chunk {d0}→{d1}: {MAX_RETRIES} intentos fallidos")


def daily_noon(df):
    """12:00 locales + precip acumulada (noon-23h, noon] — idéntico al script 01 probado."""
    df = df.set_index("time").sort_index()
    df = df[~df.index.duplicated(keep="first")]
    noon = df[df.index.hour == 12].copy()
    rain24 = []
    for t in noon.index:
        rain24.append(df.loc[t - pd.Timedelta(hours=23): t, "precip"].sum())
    return pd.DataFrame({
        "date": noon.index.date,
        "temp": noon["temp"].values,
        "rh": noon["rh"].values,
        "wind": noon["wind"].values,
        "rain24": rain24,
    })


def download_point(lat, lon):
    out_path = os.path.join(CACHE, f"meteo_{point_id(lat, lon)}.csv")
    if os.path.exists(out_path):
        return "cached"
    frames = []
    d0 = START
    while d0 <= END:
        d1 = min(dt.date(d0.year + CHUNK_YEARS, d0.month, d0.day), END)
        frames.append(fetch_chunk(lat, lon, d0, d1))
        time.sleep(SLEEP)
        d0 = d1 + dt.timedelta(days=-1)  # 1 día de solape para rain24
        if d1 == END:
            break
    daily = daily_noon(pd.concat(frames, ignore_index=True))
    tmp = out_path + ".tmp"
    daily.to_csv(tmp, index=False)
    os.replace(tmp, out_path)
    return f"{len(daily)} días"


def main():
    with open(os.path.join(HERE, "zonas_fuego.json")) as f:
        zonas = json.load(f)["zonas"]
    points = []
    for prov, zs in zonas.items():
        for z in zs:
            points.append((z["lat"], z["lon"]))
    points = sorted(set(points))  # dedupe (centroides pueden coincidir)
    print(f"{len(points)} puntos únicos · {START} → {END}", flush=True)
    ok = err = 0
    for n, (lat, lon) in enumerate(points, 1):
        try:
            res = download_point(lat, lon)
            ok += 1
            print(f"[{n}/{len(points)}] ({lat},{lon}) {res}", flush=True)
        except Exception as e:
            err += 1
            print(f"[{n}/{len(points)}] ({lat},{lon}) FALLÓ: {e}", flush=True)
    print(f"OK={ok} ERR={err}")
    sys.exit(1 if err else 0)


if __name__ == "__main__":
    main()
