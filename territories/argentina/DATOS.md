# Argentina — raw inputs (not redistributed) and how to fetch them

All scripts expect raw series under `~/.openclaw/data/`.

1. **FIRMS VIIRS S-NPP 2012–2025** (country archive) → `firms_ar/viirs_<year>.csv`; **2026** via the area API in 5-day blocks (`paper_v2/scripts/00_descarga_firms_2025_2026.sh`; SP to 2026-07-31, NRT after, static-source mask). **MODIS 2001–2025** → `firms_ar/modis_<year>_Argentina.csv`. Free MAP_KEY: https://firms.modaps.eosdis.nasa.gov/api/map_key/
2. **ONI** → `firms_ar/oni.ascii.txt` from https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt
3. **ERA5 (Copernicus CDS)** at each fire-zone centroid, 2011-10-01 → present: `scripts/02_descarga_era5_cds.py` (dataset `reanalysis-era5-single-levels-timeseries`; needs a CDS account and `~/.cdsapirc`) → `gfi_v2_cds/meteo_<lat>_<lon>.csv`; then `scripts/03_fwi_era5.py` → `gfi_v2_fwi_cds/fwi_<lat>_<lon>.csv`. Local noon, 24 h precipitation, southern-hemisphere day-length factors. **Do not use the Open-Meteo archive**: its default model blends ERA5 with ERA5-Land and, from 2017, the ECMWF operational analysis (versions 1.0 and 1.1 of this package did; see CHANGELOG).
4. Province boundaries: IGN, embedded in `scripts/provincias_pip.js`.

Run order: 05a (detections → zones) · 02 + 03 (ERA5 → DC) · derive_enso_calibracion (ENSO) · derive_calibracion_v2 (zone thresholds, v2 format) · `paper_v2/scripts/10_calibracion_v3.py AR` (calibration 3.0) · `paper_v2/scripts/01…07` (verification).
