#!/usr/bin/env python3
"""GFI Indonesia — paso 3: FWI/DC histórico por zona con el MISMO motor Van Wagner.

Motor: copernicus/tools/fuego/02_fwi.py (sin tocar). Único cambio respecto de AR:
los factores de duración del día. El territorio cae entre 6°N y 6°S, donde la tabla
canadiense (calibrada a ~46°N) no aplica; se usan los factores ECUATORIALES
estándar de Lawson & Armitage (2008, Weather Guide for the CFFDRS) — los mismos que
usa el paquete de referencia cffdrs (R) para |lat| ≤ 10° (DMC) y |lat| ≤ 20° (DC):
  Le (DMC) = 9.0 constante · Lf (DC) = 1.4 constante (verificado en cffdrs R/drought_code.r y duff_moisture_code.r, 05/11/2026)
El sistema de alerta de Indonesia (Fire Danger Rating System, BMKG) es una adaptación
del FWI canadiense, así que el DC es el código de sequía con que el país ya opera.

Input:  ~/.openclaw/data/gfi_id_cds/meteo_<lat>_<lon>.csv (02b_descarga_cds.py — ERA5 puro)
Output: ~/.openclaw/data/gfi_id_fwi/fwi_<lat>_<lon>.csv (date,ffmc,dmc,dc,isi,bui,fwi)
Spin-up: oct–dic 2011, descartado. Uso: python3 03_fwi.py
"""
import glob, os, sys
import pandas as pd

sys.path.insert(0, os.path.expanduser("~/.openclaw/workspace/copernicus/tools/fuego"))
fwi_mod = __import__("02_fwi")
# factores ecuatoriales: run_series lee estas listas del módulo en cada llamada
fwi_mod.LE_SH = [9.0] * 12
fwi_mod.LF_SH = [1.4] * 12
run_series = fwi_mod.run_series

METEO = os.path.expanduser("~/.openclaw/data/gfi_id_cds")  # ERA5 puro (CDS), ver 02b
OUT = os.path.expanduser("~/.openclaw/data/gfi_id_fwi")
CORTE = pd.Timestamp("2012-01-01").date()


def main():
    os.makedirs(OUT, exist_ok=True)
    files = sorted(glob.glob(os.path.join(METEO, "meteo_*.csv")))
    if not files:
        sys.exit(f"sin inputs en {METEO}")
    for path in files:
        pid = os.path.basename(path)[len("meteo_"):-len(".csv")]
        df = pd.read_csv(path, parse_dates=["date"])
        valid = df[["temp", "rh", "wind"]].notna().all(axis=1)
        if not valid.any():
            print(f"{pid}: TODO NaN, salteado"); continue
        last_ok = valid[::-1].idxmax()
        df = df.loc[:last_ok]
        n_nan = int((~valid.loc[:last_ok]).sum())
        df = df[valid.loc[:last_ok]]
        rows = [{"date": d.date(), "temp": t, "rh": h, "wind": w, "rain24": (0.0 if pd.isna(p) else p)}
                for d, t, h, w, p in zip(df["date"], df["temp"], df["rh"], df["wind"], df["rain24"])]
        out = pd.DataFrame(run_series(rows, hemisphere="south"))
        out = out[out["date"] >= CORTE]
        out[["date", "ffmc", "dmc", "dc", "isi", "bui", "fwi"]].to_csv(os.path.join(OUT, f"fwi_{pid}.csv"), index=False)
        print(f"{pid}: {len(out)} días · NaN internos {n_nan} · DC max {out['dc'].max():.0f} "
              f"({out.loc[out['dc'].idxmax(), 'date']})", flush=True)


if __name__ == "__main__":
    main()
