# Changelog — GFI method package

| Version | Date | Territories | Meteorology | Rules | Paper |
|---|---|---|---|---|---|
| 1.0.0 | 2026-09-28 | Argentina (116 zones) | Open-Meteo archive, default model (ERA5 blended with ERA5-Land and, from 2017, ECMWF HRES). **Superseded.** | 2.2.0: fixed ENSO cut-offs (0.90/1.10/1.45), Patagonia declared inverse, national two-thirds rule | egusphere-2026-5917 (not accepted at screening) |
| 1.1.0 | 2026-11-05 | + Sumatra and Kalimantan (75 zones) | Argentina as 1.0; Indonesia ERA5 (CDS). **Superseded** (mixed sources). | as 1.0, applied unchanged to Indonesia | — |
| **1.2.0** | 2026-11 | Argentina + Indonesia, seven climatic regions | **ERA5 (Copernicus CDS) in both territories**, same FWI engine | **3.0**: ENSO signal declared only where the year-block bootstrap interval of the phase ratio excludes 1; HIGH requires drought; regional extent rule with LOYO thresholds; the region, not the country, is the unit | NHESS resubmission (v2); DOI 10.5281/zenodo.24164911 |

Version 1.2 re-derives every Argentine result of 1.0 with ERA5; the 1.0 numbers remain in that version's record for traceability and are not reproduced here.
