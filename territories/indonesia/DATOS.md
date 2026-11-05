# Indonesia — raw inputs and how to fetch them

All scripts expect the raw series under `~/.openclaw/data/` (paths in `territorio.py`).
A free FIRMS MAP_KEY is required (https://firms.modaps.eosdis.nasa.gov/api/map_key/).

```sh
KEY=<your MAP_KEY>
D=~/.openclaw/data/firms_id; mkdir -p $D
# VIIRS S-NPP 2012–2025 and MODIS 2001–2025, Indonesia country archive
for y in $(seq 2012 2025); do
  curl -fsS -o $D/viirs_$y.csv "https://firms.modaps.eosdis.nasa.gov/data/country/viirs-snpp/$y/viirs-snpp_${y}_Indonesia.csv?MAP_KEY=$KEY"
done
for y in $(seq 2001 2025); do
  curl -fsS -o $D/modis_$y.csv "https://firms.modaps.eosdis.nasa.gov/data/country/modis/$y/modis_${y}_Indonesia.csv?MAP_KEY=$KEY"
done
# climate indices
curl -fsS -o $D/oni.ascii.txt https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt
curl -fsS -o $D/dmi.had.long.data https://psl.noaa.gov/gcos_wgsp/Timeseries/Data/dmi.had.long.data
# province boundaries (geoBoundaries gbOpen IDN ADM1, ODbL)
mkdir -p ~/.openclaw/data/geo_id
curl -fsSL -o ~/.openclaw/data/geo_id/idn_adm1.geojson \
  https://github.com/wmgeolab/geoBoundaries/raw/9469f09/releaseData/gbOpen/IDN/ADM1/geoBoundaries-IDN-ADM1_simplified.geojson
```

**2026 season** (`viirs_2026_area.csv`): FIRMS area API, 5-day requests over
bbox `95,-6.5,119.5,7.5`, source `VIIRS_SNPP_SP` up to 2026-07-31 and `VIIRS_SNPP_NRT`
from 2026-08-01; a `source` column is appended to each row. NRT rows carry no `type`
column — `08_temporada_2026.py` removes static sources with a mask built from the
archive (0.01° cells with any `type != 0` detection, 2012–2025) and reports its effect
on 2025 against the official filter.

**ERA5** is fetched per zone by `02b_descarga_cds.py` from the Copernicus Climate Data
Store (dataset `reanalysis-era5-single-levels-timeseries`; free account and `~/.cdsapirc`
required, ERA5 licence accepted). One request per zone, seconds each.
