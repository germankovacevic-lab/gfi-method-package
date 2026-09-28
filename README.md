# The GeoFuego Index (GFI) — method package

Contents:

**Note**
- `nota_tecnica_gfi.md` — technical note (CC BY 4.0)

**Calibration and engine**
- `enso_calibracion.json` — calibration (version 2.2.0): regional ENSO factors 2001–2025 + 116 fire zones with their monthly DC thresholds 2012–2024 (CC BY 4.0)
- `zonas_fuego.json` — the 116 fire zones: centroid, province and weight (CC BY 4.0)
- `enso_logic.js` — classification engine (ENSO base, A-zonal drought rule, season gate, country-extent rule), byte-identical to the logic run in production (MIT)
- `provincias_pip.js` — official IGN province boundaries for point-in-polygon assignment (MIT)

**Derivation**
- `derive_enso_calibracion.mjs` — ENSO calibration derivation (MIT). Accepts `FIRMS_CACHE` and `SALIDA`.
- `derive_calibracion_v2.mjs` — fire-zone DC-threshold derivation (MIT)
- `gen_gfi_retro.mjs` — hindcast generator (MIT) · `gfi_v2_retro.json` — its output (CC BY 4.0)

**Verification — reproduces every figure of §4 and Appendix A**
- `05a_focos_por_zona.mjs` — assigns each of the 2,394,573 filtered VIIRS detections to its fire zone (MIT)
- `05b_valida_zonal_fwi.py` — zone-level skill (72.4% / 53.6%) and the DC × FWI cells (MIT)
- `06_verificacion.py` — contingency table, precision/POD/FAR/PSS/HSS, year-block confidence intervals, climatology baseline, lead-time table, country-extent rule under both statistics, season-gate counts (MIT)
- `07_barrido_lags.mjs` — the lag sweep of Appendix A (MIT)
- `08_ventana_por_region.py` — seasonal distribution of fire by region; the basis of limitation 1b (VIIRS-only, scope declared in its header) (MIT)
- `09_loyo_dc.py` — leave-one-year-out validation of the drought term: pooled variants and the per-year skill table of §4 (MIT)
- `10_loyo_enso_ventana.mjs` — leave-one-year-out of the ENSO term (25 folds) and the 6/8/10% window-sensitivity sweep of §6.1b (MIT)

**Supporting data**
- `historico.json` — monthly VIIRS detection series, country and 24 provinces (CC BY 4.0)
- `DATOS.md` — **how to fetch the raw FIRMS / ONI / ERA5 series** (not redistributed), the run order, and which figure each script produces

**Legal**
- `CITATION.cff` · `LICENSE-MIT` · `LICENSE-DATA`

---

The derived artefacts in this package are self-contained: `05b` and `06_verificacion.py`
run from this directory once the raw series of `DATOS.md` are in place. `06` completes
in a few seconds.

Live product: https://geofuego.com.ar · Public API: https://ingesta.geofuego.com.ar/api/enso

**Figures**
- `figures/` — the six manuscript figures (PDF vector + PNG 300 dpi, colorblind-validated Okabe–Ito palette), their generation scripts (`fig1…fig6*.py`, `estilo.py`) and the intermediate data (`figures/datos/`, produced by `gen_datos_figuras.{mjs,py}`). Reproduce any figure by running its script in place (CC BY 4.0).
