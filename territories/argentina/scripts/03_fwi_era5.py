#!/usr/bin/env python3
"""GFI v2 — Paso 3: FWI/DC histórico por punto, reusando el motor Van Wagner probado.

Motor: copernicus/tools/fuego/02_fwi.py (run_series, hemisphere=south con day-length
factors corridos 6 meses — ya lo maneja, no se toca). Spin-up: oct-dic 2011, descartado.

Input:  ~/.openclaw/data/gfi_v2_cds/meteo_<lat>_<lon>.csv
Output: ~/.openclaw/data/gfi_v2_fwi/fwi_<lat>_<lon>.csv (fecha,ffmc,dmc,dc,isi,bui,fwi)

NaNs en meteo (colas ERA5T recientes): se cortan del final; huecos internos se
rellenan por forward-fill del estado (día sin dato = se saltea, el índice arrastra) —
se reporta cuántos por punto.

Uso: python3 03_fwi.py
"""
import glob
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.expanduser("~/.openclaw/workspace/copernicus/tools/fuego"))
fwi_mod = __import__("02_fwi")
run_series = fwi_mod.run_series

METEO = os.path.expanduser("~/.openclaw/data/gfi_v2_cds")
OUT = os.path.expanduser("~/.openclaw/data/gfi_v2_fwi_cds")
CORTE = pd.Timestamp("2012-01-01").date()


def main():
    files = sorted(glob.glob(os.path.join(METEO, "meteo_*.csv")))
    if not files:
        print("sin inputs en", METEO)
        sys.exit(1)
    stats = []
    for path in files:
        pid = os.path.basename(path)[len("meteo_"):-len(".csv")]
        out_path = os.path.join(OUT, f"fwi_{pid}.csv")
        df = pd.read_csv(path, parse_dates=["date"])
        # cortar cola de NaNs (retraso ERA5T)
        valid = df[["temp", "rh", "wind"]].notna().all(axis=1)
        last_ok = valid[::-1].idxmax() if valid.any() else None
        if last_ok is None:
            print(f"{pid}: TODO NaN, salteado")
            continue
        df = df.loc[:last_ok]
        n_total = len(df)
        n_nan = int((~valid.loc[:last_ok]).sum())
        df = df[valid.loc[:last_ok]]  # huecos internos: día salteado, estado arrastra
        rows = [{"date": d.date(), "temp": t, "rh": h, "wind": w, "rain24": (0.0 if pd.isna(p) else p)}
                for d, t, h, w, p in zip(df["date"], df["temp"], df["rh"], df["wind"], df["rain24"])]
        serie = run_series(rows, hemisphere="south")
        out = pd.DataFrame(serie)
        out = out[out["date"] >= CORTE]
        out[["date", "ffmc", "dmc", "dc", "isi", "bui", "fwi"]].to_csv(out_path, index=False)
        stats.append((pid, len(out), n_nan, n_total))
        print(f"{pid}: {len(out)} días · NaN internos {n_nan}/{n_total} · "
              f"DC max {out['dc'].max():.0f} ({out.loc[out['dc'].idxmax(), 'date']})", flush=True)
    print(f"\n{len(stats)} puntos procesados → {OUT}")


if __name__ == "__main__":
    main()
