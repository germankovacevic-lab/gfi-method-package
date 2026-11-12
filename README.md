# GeoFuego Index (GFI) — method package v1.2.0

Seasonal fire-risk skill from ENSO phase and zone-level accumulated drought: a regional-scale categorical indicator transferred from Argentina to Indonesia. Companion of the manuscript submitted to *Natural Hazards and Earth System Sciences* (resubmission, November 2026). Concept DOI 10.5281/zenodo.23017739 · this version 10.5281/zenodo.24164911.

## What is here

- `engine/` — `gfi_rules_v3.py`: reference implementation of rules 3.0 (reads a territory calibration file); `fwi_vanwagner.py`: Fire Weather Index engine (Van Wagner 1987) used for both territories.
- `territories/argentina/` and `territories/indonesia/` — `calibracion_3.0.json` (fire zones with ERA5-derived monthly thresholds, regions, fire-season windows, ENSO signals with bootstrap intervals, provincial climatologies for the season gate, regional extent thresholds), `DATOS.md` (how to fetch the raw inputs), `scripts/` (zone building, ERA5 download and FWI, ENSO calibration, hindcast).
- `paper_v2/` — `scripts/00…10` reproduce every table and figure of the manuscript for both territories; `results/` are their outputs (JSON + Markdown); `figures/`; `tablas_apendices.md`.
- `CHANGELOG.md` — what changed between 1.0, 1.1 and 1.2 and why.

## Reproduce

1. Fetch raw inputs as described in each `territories/<t>/DATOS.md` (FIRMS, ONI, DMI, ERA5 from the CDS). Nothing raw is redistributed.
2. Run the territory scripts in the order given there, then `paper_v2/scripts/01…10` with `AR` or `ID`.
3. Compare with `paper_v2/results/`.

The calibration file published here is the file the operational product loads: paper and product cannot diverge.

## License and citation

Code: MIT. Derived data and calibration: CC BY 4.0 (LICENSE-DATA). "GeoFuego" is a registered trademark; the method and code are open. Cite as in `CITATION.cff`.
