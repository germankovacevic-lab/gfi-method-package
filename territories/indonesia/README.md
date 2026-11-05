# GFI — Indonesia (Sumatra + Kalimantan): transfer of the method

Replication of the GeoFuego Index (GFI) method — manuscript *The GeoFuego Index (GFI): an
operational seasonal fire-risk indicator combining ENSO phase and zone-level accumulated
drought* (NHESS, egusphere-2026-5917) — on a second territory, **without tuning**.

Everything the index uses is derived from Indonesia's own data with the same rules as
Argentina: fire zones (weighted k-means over the VIIRS density grid), each region's fire
season (months holding ≥ 8% of annual fire), ENSO factors (intra-sensor anomaly by ONI
phase, 25 seasons) and drought thresholds (90th percentile of each zone's 30-day Drought
Code). The only hand-declared choices are fixed in `territorio.py` **before** any result
was computed: which provinces enter (the 15 ADM1 provinces of Sumatra and Kalimantan),
how they group into ENSO regions (North Sumatra / South Sumatra / Kalimantan, after
Aldrian & Susanto 2003, doi:10.1002/joc.950) and the local-noon time zone (WIB/WITA).

Two physical adaptations, both standard:
- **Equatorial day-length factors** for the FWI system: Le = 9 (DMC) and Lf = 1.4 (DC),
  as in the `cffdrs` reference implementation for |lat| ≤ 10° / 20°. The Canadian table
  (calibrated near 46°N) does not apply at 6°N–6°S. The Van Wagner engine itself is
  unchanged.
- **Local noon** read in each province's own time zone.

## Run order

| Step | Script | Produces |
|---|---|---|
| 1 | `01_asigna_y_zonas.py` | `zonas_fuego.json`; monthly series per province and sensor; detections per zone |
| 2 | `02b_descarga_cds.py` | **pure ERA5** per zone from the Copernicus CDS point time-series dataset, 2011-10 → present |
| 3 | `03_fwi.py` | daily FWI/DC per zone (equatorial factors) |
| 4 | `04_enso.py` | `enso_calibracion_id.json`: factors by phase, lag sweep 0–12, LOYO (25 folds), window sensitivity 6/8/10% |
| 5 | `05_sequia.py` | `umbrales_dc.json`, `verificacion_sequia.json`: contingency, year-block CI, rate-matched climatology baseline, lead time, LOYO, **2025 out of sample** |
| 6 | `06_hindcast.py` | `gfi_id_retro.json`: monthly LOW/MEDIUM/HIGH per province and territory, 2012–2026, with Argentina's production rules |
| 7 | `07_iod.py` | `control_iod.json`: ENSO × Indian Ocean Dipole stratification |
| 8 | `08_temporada_2026.py` | `temporada_2026.json`: the 2026 season as an out-of-sample test of both terms |
| 9 | `09_panel_data.py` | data file of the public panel |

Steps 1 and 8 use `numpy` + `matplotlib` (point-in-polygon); the rest, `pandas` +
`requests` (step 2) or the standard library. Raw inputs (not redistributed) — see `DATOS.md`.

## Inputs

- NASA FIRMS country archive, Indonesia: VIIRS S-NPP 2012–2025 (`confidence != 'l'`,
  `type == 0`), MODIS 2001–2025 (`confidence ≥ 30`, `type == 0`). 2026: FIRMS area API,
  VIIRS S-NPP SP (to 2026-07-31) + NRT (from 2026-08-01), bbox 95,-6.5,119.5,7.5.
- ONI (NOAA/CPC), DMI HadISST1.1 (NOAA PSL).
- ERA5 hourly 2 m temperature and dewpoint (→ relative humidity, Magnus), 10 m wind and total
  precipitation, from the Copernicus Climate Data Store dataset
  `reanalysis-era5-single-levels-timeseries` (doi:10.24381/cds.adbb2d47 family). Open-Meteo's
  archive API was tested and **not used**: its default `best_match` blends ERA5 with ERA5-Land and,
  from 2017, the ECMWF IFS HRES analysis, which introduces a break in the precipitation series
  (r = 1.000 with ERA5 for 2012–2016, 0.53–0.59 from 2017 in the zones compared).
- Province boundaries: geoBoundaries gbOpen IDN ADM1 (OpenStreetMap, ODbL).

## Results (2026-11-05)

| | Indonesia | Argentina (manuscript) |
|---|---|---|
| Fire zones / detections | 75 / 2,236,596 | 116 / 2,394,573 |
| ENSO term, lag 3, Aug–Oct | South Sumatra El Niño 7.68× / La Niña 0.70× (p < 0.001); Kalimantan 4.87× / 0.38× (p < 0.001); North Sumatra 1.80× / 1.00× (p = 0.13, weak — declared before running) | NOA La Niña 1.50× (p = 0.005) |
| ENSO LOYO (25 folds) | El Niño > La Niña in 25/25 in every region | declared signs in 25/25 |
| Drought term, zone-month 2012–2024 | precision 84.8% vs base rate 54.2%; PSS 0.190 (95% year-block CI 0.131–0.252) vs 0.000 rate-matched climatology; PSS > 0 in 13/13 years | precision 72.3% vs 53.6%; PSS 0.116 |
| Drought term, 2025 out of sample | PSS 0.380 | — |
| 2026 season, out of sample for both terms | Aug–Oct fire: South Sumatra 7.79× median (7.68× calibrated), Kalimantan 5.72× (4.87×), North Sumatra 0.70× (false alarm in the weak region) | prospective registry |

The ENSO sign is the opposite of northern Argentina's (El Niño, not La Niña, raises fire); the
calibration derives it, it is not assumed. The signal lives at lags 0–3 and vanishes at 6–12.
Indian Ocean Dipole control (`07_iod.py`): within ENSO-neutral seasons, a positive IOD in the
**same** month raises fire (South Sumatra 5.38×, p = 0.003; Kalimantan 2.29×, p = 0.029), but the
IOD three months earlier carries no anticipatory skill — so it is not a base term; the drought
term captures IOD droughts in real time (its best year is 2019, PSS 0.40).

`series_mensuales.json` is the per-province monthly detection series produced by step 1
(`~/.openclaw/data/gfi_id_cache/series.json` when re-run).

## Licence

Code MIT · data and text CC BY 4.0 — same as the parent package.
