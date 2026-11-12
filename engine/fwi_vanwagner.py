#!/usr/bin/env python3
"""Sistema FWI canadiense (Van Wagner 1987) — implementación estándar completa.

Componentes: FFMC, DMC, DC, ISI, BUI, FWI.
Ecuaciones: Van Wagner & Pickett (1985) "Equations and FORTRAN program for the
Canadian Forest Fire Weather Index System", Forestry Technical Report 33.

HEMISFERIO SUR: los day-length factors del DMC (Le) y DC (Lf) están tabulados
para Canadá (hemisferio norte). Acá se aplica el corrimiento estándar de 6 meses
(enero austral usa el factor de julio boreal, etc.) — práctica documentada en la
literatura (p.ej. implementación cffdrs de R, opción lat<0; Dowdy et al. 2009).

Entradas diarias: temp (°C, 12:00 local), rh (%, 12:00), wind (km/h a 10m, 12:00),
rain24 (mm acumulados 24h previas al mediodía). Unidades = las canónicas del sistema.

Inicialización estándar: FFMC=85, DMC=6, DC=15, con spin-up (acá: oct-dic 2018,
descartado del análisis).
"""
import math

# Day-length factors DMC (Le) y DC (Lf), tabulados ene..dic HEMISFERIO NORTE
LE_NH = [6.5, 7.5, 9.0, 12.8, 13.9, 13.9, 12.4, 10.9, 9.4, 8.0, 7.0, 6.0]
LF_NH = [-1.6, -1.6, -1.6, 0.9, 3.8, 5.8, 6.4, 5.0, 2.4, 0.4, -1.6, -1.6]
# Hemisferio sur: corrimiento de 6 meses
LE_SH = LE_NH[6:] + LE_NH[:6]
LF_SH = LF_NH[6:] + LF_NH[:6]


def ffmc_calc(temp, rh, wind, rain, ffmc_prev):
    mo = 147.2 * (101.0 - ffmc_prev) / (59.5 + ffmc_prev)
    if rain > 0.5:
        rf = rain - 0.5
        if mo > 150.0:
            mo = (mo + 42.5 * rf * math.exp(-100.0 / (251.0 - mo)) * (1.0 - math.exp(-6.93 / rf))) \
                 + 0.0015 * (mo - 150.0) ** 2 * math.sqrt(rf)
        else:
            mo = mo + 42.5 * rf * math.exp(-100.0 / (251.0 - mo)) * (1.0 - math.exp(-6.93 / rf))
        if mo > 250.0:
            mo = 250.0
    ed = 0.942 * rh ** 0.679 + 11.0 * math.exp((rh - 100.0) / 10.0) \
         + 0.18 * (21.1 - temp) * (1.0 - math.exp(-0.115 * rh))
    if mo < ed:
        ew = 0.618 * rh ** 0.753 + 10.0 * math.exp((rh - 100.0) / 10.0) \
             + 0.18 * (21.1 - temp) * (1.0 - math.exp(-0.115 * rh))
        if mo < ew:
            kl = 0.424 * (1.0 - ((100.0 - rh) / 100.0) ** 1.7) \
                 + 0.0694 * math.sqrt(wind) * (1.0 - ((100.0 - rh) / 100.0) ** 8)
            kw = kl * 0.581 * math.exp(0.0365 * temp)
            m = ew - (ew - mo) / 10.0 ** kw
        else:
            m = mo
    elif mo == ed:
        m = mo
    else:
        kl = 0.424 * (1.0 - (rh / 100.0) ** 1.7) \
             + 0.0694 * math.sqrt(wind) * (1.0 - (rh / 100.0) ** 8)
        kw = kl * 0.581 * math.exp(0.0365 * temp)
        m = ed + (mo - ed) / 10.0 ** kw
    ffmc = 59.5 * (250.0 - m) / (147.2 + m)
    return min(max(ffmc, 0.0), 101.0)


def dmc_calc(temp, rh, rain, dmc_prev, month, le):
    if rain > 1.5:
        re = 0.92 * rain - 1.27
        mo = 20.0 + math.exp(5.6348 - dmc_prev / 43.43)
        if dmc_prev <= 33.0:
            b = 100.0 / (0.5 + 0.3 * dmc_prev)
        elif dmc_prev <= 65.0:
            b = 14.0 - 1.3 * math.log(dmc_prev)
        else:
            b = 6.2 * math.log(dmc_prev) - 17.2
        mr = mo + 1000.0 * re / (48.77 + b * re)
        pr = 244.72 - 43.43 * math.log(mr - 20.0)
        dmc_prev = max(pr, 0.0)
    t = max(temp, -1.1)
    k = 1.894 * (t + 1.1) * (100.0 - rh) * le[month - 1] * 1e-6
    return dmc_prev + 100.0 * k


def dc_calc(temp, rain, dc_prev, month, lf):
    if rain > 2.8:
        rd = 0.83 * rain - 1.27
        qo = 800.0 * math.exp(-dc_prev / 400.0)
        qr = qo + 3.937 * rd
        dc_prev = max(400.0 * math.log(800.0 / qr), 0.0)
    t = max(temp, -2.8)
    v = 0.36 * (t + 2.8) + lf[month - 1]
    v = max(v, 0.0)
    return dc_prev + 0.5 * v


def isi_calc(ffmc, wind):
    mo = 147.2 * (101.0 - ffmc) / (59.5 + ffmc)
    ff = 91.9 * math.exp(-0.1386 * mo) * (1.0 + mo ** 5.31 / 4.93e7)
    return 0.208 * math.exp(0.05039 * wind) * ff


def bui_calc(dmc, dc):
    if dmc == 0 and dc == 0:
        return 0.0
    if dmc <= 0.4 * dc:
        bui = 0.8 * dmc * dc / (dmc + 0.4 * dc)
    else:
        bui = dmc - (1.0 - 0.8 * dc / (dmc + 0.4 * dc)) \
              * (0.92 + (0.0114 * dmc) ** 1.7)
    return max(bui, 0.0)


def fwi_calc(isi, bui):
    if bui <= 80.0:
        fd = 0.626 * bui ** 0.809 + 2.0
    else:
        fd = 1000.0 / (25.0 + 108.64 * math.exp(-0.023 * bui))
    b = 0.1 * isi * fd
    if b > 1.0:
        return math.exp(2.72 * (0.434 * math.log(b)) ** 0.647)
    return b


def run_series(rows, hemisphere="south", ffmc0=85.0, dmc0=6.0, dc0=15.0):
    """rows: iterable de dicts con keys date(datetime.date), temp, rh, wind, rain24.
    Devuelve lista de dicts con los 6 componentes."""
    le = LE_SH if hemisphere == "south" else LE_NH
    lf = LF_SH if hemisphere == "south" else LF_NH
    ffmc, dmc, dc = ffmc0, dmc0, dc0
    out = []
    for r in rows:
        m = r["date"].month
        rh = min(r["rh"], 100.0)
        ffmc = ffmc_calc(r["temp"], rh, r["wind"], r["rain24"], ffmc)
        dmc = dmc_calc(r["temp"], rh, r["rain24"], dmc, m, le)
        dc = dc_calc(r["temp"], r["rain24"], dc, m, lf)
        isi = isi_calc(ffmc, r["wind"])
        bui = bui_calc(dmc, dc)
        fwi = fwi_calc(isi, bui)
        out.append({"date": r["date"], "temp": r["temp"], "rh": rh,
                    "wind": r["wind"], "rain24": r["rain24"],
                    "ffmc": round(ffmc, 2), "dmc": round(dmc, 2), "dc": round(dc, 2),
                    "isi": round(isi, 2), "bui": round(bui, 2), "fwi": round(fwi, 2)})
    return out


if __name__ == "__main__":
    import pandas as pd
    import sys
    for name in ("delta", "sanfernando"):
        df = pd.read_csv(f"meteo_{name}.csv", parse_dates=["date"])
        rows = [{"date": d.date(), "temp": t, "rh": h, "wind": w, "rain24": p}
                for d, t, h, w, p in zip(df["date"], df["temp"], df["rh"], df["wind"], df["rain24"])]
        serie = run_series(rows)
        out = pd.DataFrame(serie)
        # descartar spin-up (oct-dic 2018)
        out = out[out["date"] >= pd.Timestamp("2019-01-01").date()]
        out.to_csv(f"fwi_{name}.csv", index=False)
        print(f"{name}: {len(out)} días 2019-2023, FWI max={out['fwi'].max():.1f} "
              f"({out.loc[out['fwi'].idxmax(), 'date']}), mediana={out['fwi'].median():.1f}")
