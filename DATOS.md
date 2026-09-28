# Datos de entrada — cómo reponerlos

Los artefactos derivados (calibración, umbrales, zonas, hindcast) están en este
paquete. Las **series crudas no se redistribuyen** — son grandes y tienen su propia
fuente pública y estable. Este archivo dice exactamente cómo reponer cada una y
cuál script la consume.

Todos los scripts esperan los crudos bajo `~/.openclaw/data/`.

---

## 1. FIRMS VIIRS S-NPP — focos 2012–2024

**Consume:** `05a_focos_por_zona.mjs` (asigna cada foco a su zona de fuego).
**Destino:** `~/.openclaw/data/firms_ar/viirs_<año>.csv` (2012…2024).
**Fuente:** NASA FIRMS, archivo anual por país. Requiere un MAP_KEY gratuito
(https://firms.modaps.eosdis.nasa.gov/api/map_key/).

```sh
KEY=<tu MAP_KEY>
mkdir -p ~/.openclaw/data/firms_ar
for y in $(seq 2012 2024); do
  curl -fsS -o ~/.openclaw/data/firms_ar/viirs_${y}.csv \
    "https://firms.modaps.eosdis.nasa.gov/data/country/viirs-snpp/${y}/viirs-snpp_${y}_Argentina.csv?MAP_KEY=$KEY"
done
```

Filtros aplicados por los scripts: `confidence != 'l'` y `type == 0`. El archivo
filtrado tiene 2.394.573 detecciones.

## 2. FIRMS MODIS Terra/Aqua — focos 2001–2024

**Consume:** `derive_enso_calibracion.mjs` y `07_barrido_lags.mjs` (extienden el
término ENSO a 2001; las anomalías se computan **intra-sensor**, nunca mezcladas).
**Destino:** `~/.openclaw/data/firms_ar/modis_<año>_Argentina.csv` (2001…2024).

```sh
for y in $(seq 2001 2024); do
  curl -fsS -o ~/.openclaw/data/firms_ar/modis_${y}_Argentina.csv \
    "https://firms.modaps.eosdis.nasa.gov/data/country/modis/${y}/modis_${y}_Argentina.csv?MAP_KEY=$KEY"
done
```

Filtros: `confidence >= 30` y `type == 0`. Son ~347 MB en total.

> El derivador acepta `FIRMS_CACHE=<dir>` para leer de otra ruta. El barrido y el derivador miden cada región en su ventana propia (meses con ≥8% del fuego anual, VIIRS 2012–2025).

## 3. ONI — Oceanic Niño Index

**Consume:** `derive_enso_calibracion.mjs`, `07_barrido_lags.mjs`.
**Destino:** `~/.openclaw/data/firms_ar/oni.ascii.txt`.

```sh
curl -fsS -o ~/.openclaw/data/firms_ar/oni.ascii.txt \
  https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt
```

Trimestres móviles asignados a su mes central; umbrales oficiales
(El Niño ≥ +0,5 °C, La Niña ≤ −0,5 °C).

## 4. ERA5 / Open-Meteo — meteorología por zona, y las series FWI/DC

**Consume:** `derive_calibracion_v2.mjs` (deriva los umbrales),
`05b_valida_zonal_fwi.py` y `06_verificacion.py`.
**Destino:** `~/.openclaw/data/gfi_v2_fwi/fwi_<lat>_<lon>.csv`, una por zona
(116 + país), columnas `date,ffmc,dmc,dc,isi,bui,fwi`, desde 2011-10-01.

Se producen en dos pasos con los scripts del repositorio de método
(`02_descarga_meteo.py` → `03_fwi.py`), a partir de las coordenadas de
`zonas_fuego.json`: por cada centroide se bajan de la API archive de Open-Meteo
la temperatura, humedad y viento de las 12:00 locales más la precipitación
acumulada de las 24 h previas al mediodía, y se corre la recursión estándar del
sistema FWI de Van Wagner (1987) con los factores de duración del día del
hemisferio sur. Los primeros 92 días son spin-up del Drought Code y se descartan.

La API de Open-Meteo es pública y no requiere clave; el volumen son 116 pedidos.

## 5. Asignación de focos a zonas

`~/.openclaw/data/gfi_v2_focos_zona.json` lo produce `05a_focos_por_zona.mjs` a
partir de (1). Corré 05a antes de 05b y de 06.

---

## Orden de reproducción

```sh
node   05a_focos_por_zona.mjs      # (1)            → focos por zona-mes
python 05b_valida_zonal_fwi.py     # (4) + 05a      → §4 skill zonal y DC×FWI
python 06_verificacion.py          # (4) + 05a      → §4 contingencia, skill scores,
                                   #                   IC, baseline, lead time,
                                   #                   regla país, gate
node   07_barrido_lags.mjs         # (2) (3)        → Apéndice A (ventana propia
                                   #                   por región, share ≥8%)
python 09_loyo_dc.py               # (4) + 05a      → §4 leave-one-year-out del
                                   #                   término de sequía
node   10_loyo_enso_ventana.mjs    # (2) (3)        → §4 LOYO del término ENSO +
                                   #                   §6.1b sensibilidad 6/8/10%
node   derive_enso_calibracion.mjs # (2) (3)        → regenera la parte ENSO
node   derive_calibracion_v2.mjs   # (4)            → regenera los 116 umbrales
```

Los dos derivadores reescriben `enso_calibracion.json`; corrélos en ese orden (el
segundo repone la sección `v2` preservando la primera). `derive_enso_calibracion.mjs`
acepta `SALIDA=<archivo>` para derivar a otra ruta y comparar sin tocar el original.

El test de permutación usa aleatoriedad sin semilla: los *p* reproducen dentro de
±0,01 (desvío máximo medido 0,006 sobre tres corridas). Todo lo demás es determinista.
