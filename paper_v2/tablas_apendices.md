# Tables and appendices — draft v2

## Table 1. Sensitivity of the drought term (ERA5; 2012–2024)

**(a) Threshold rank, 30-day window, event = above-median fire.** PSS with 95 % year-block interval; climatology = rate-matched monthly-climatology predictor.

| Rank (top-k of 13) | Firing rate (%) | Argentina precision (%) | AR POD (%) | AR PSS [95 % CI] | AR climatology PSS | Indonesia precision (%) | ID POD (%) | ID PSS [95 % CI] | ID climatology PSS |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 7.7 | 72.5 | 10.4 | 0.058 [0.030, 0.087] | 0.000 | 88.0 | 12.5 | 0.105 [0.062, 0.144] | 0.000 |
| 2 | 15.4 | 70.1 | 20.1 | 0.102 [0.062, 0.137] | 0.002 | 84.8 | 24.1 | 0.190 [0.131, 0.253] | 0.000 |
| 3 | 23.1 | 68.3 | 29.4 | 0.137 [0.090, 0.179] | 0.003 | 81.6 | 34.7 | 0.255 [0.198, 0.319] | 0.001 |
| 4 | 30.8 | 67.7 | 38.9 | 0.174 [0.137, 0.214] | 0.008 | 79.1 | 44.9 | 0.308 [0.251, 0.370] | 0.002 |
| 5 | 38.5 | 66.2 | 47.5 | 0.195 [0.148, 0.234] | 0.006 | 76.2 | 54.1 | 0.341 [0.282, 0.399] | 0.005 |
| 6 | 46.1 | 65.1 | 56.0 | 0.213 [0.170, 0.258] | 0.006 | 73.4 | 62.5 | 0.357 [0.306, 0.411] | 0.010 |

Base rates: Argentina 53.6 %, Indonesia 54.2 %.

**(b) Trailing-window length (top-2 of 13).**

| Window (days) | AR PSS [95 % CI] | ID PSS [95 % CI] |
|---|---|---|
| 7 | 0.112 [0.076, 0.141] | 0.178 [0.113, 0.231] |
| 15 | 0.106 [0.070, 0.141] | 0.190 [0.137, 0.247] |
| 30 | 0.102 [0.065, 0.136] | 0.190 [0.126, 0.253] |
| 45 | 0.086 [0.052, 0.121] | 0.169 [0.101, 0.237] |
| 60 | 0.084 [0.050, 0.115] | 0.162 [0.096, 0.228] |
| 90 | 0.060 [0.029, 0.094] | 0.147 [0.081, 0.228] |

Autocorrelation e-folding lag of the daily DC anomaly: Argentina median 126 d (IQR 82–193, n = 112 zones); Indonesia 47 d (24–61, n = 75).

**(c) Event definition (30 d, top-2 of 13).**

| Event | AR base (%) | AR PSS | ID base (%) | ID PSS |
|---|---|---|---|---|
| fire ≥ median | 53.6 | 0.102 | 54.2 | 0.190 |
| fire ≥ upper quartile | 31.6 | 0.123 | 31.6 | 0.256 |
| fire ≥ mean | 32.9 | 0.122 | 31.6 | 0.264 |

**(d) Provincial aggregation (event = above-median provincial fire).**

| Rule | Territory | Firing rate (%) | Precision (%) | POD (%) | PSS [95 % CI] |
|---|---|---|---|---|---|
| any zone above its threshold (rule in use) | AR | 34.5 | 68.5 | 44.7 | 0.216 [0.143, 0.275] |
| dominant zone only | AR | 15.4 | 72.2 | 20.9 | 0.119 [0.076, 0.152] |
| weighted provincial mean, top-2 of 13 | AR | 15.4 | 71.2 | 20.7 | 0.113 [0.063, 0.156] |
| provincial maximum, top-2 of 13 | AR | 15.4 | 67.4 | 19.6 | 0.089 [0.052, 0.118] |
| weighted provincial mean, top-4 of 13 (rate matched to any-zone) | AR | 30.8 | 69.8 | 40.6 | 0.208 [0.157, 0.261] |
| provincial maximum, top-4 of 13 (rate matched) | AR | 30.8 | 65.1 | 37.9 | 0.151 [0.102, 0.189] |
| any zone above its threshold (rule in use) | ID | 32.3 | 79.7 | 47.3 | 0.330 [0.254, 0.419] |
| dominant zone only | ID | 15.4 | 85.6 | 24.2 | 0.193 [0.117, 0.281] |
| weighted provincial mean, top-2 of 13 | ID | 15.4 | 88.6 | 25.1 | 0.212 [0.136, 0.279] |
| provincial maximum, top-2 of 13 | ID | 15.4 | 86.9 | 24.6 | 0.202 [0.125, 0.284] |
| weighted provincial mean, top-4 of 13 (rate matched to any-zone) | ID | 30.8 | 84.3 | 47.7 | 0.371 [0.296, 0.440] |
| provincial maximum, top-4 of 13 (rate matched) | ID | 30.7 | 81.2 | 45.9 | 0.333 [0.253, 0.406] |

**(e) Country-extent threshold (event = above-median national fire).**

| Territory | Best in-sample threshold (PSS) | Two-thirds threshold: months active / hit rate / PSS | LOYO-selected thresholds | LOYO out-of-fold PSS | 2025–2026 PSS with full-sample threshold |
|---|---|---|---|---|---|
| Argentina | 6/24 (0.294) | 19 / 73.7 % / 0.097 | [5, 6, 10] | 0.187 | 0.231 (6/24) |
| Indonesia | 5/15 (0.274) | 24 / 83.3 % / 0.183 | [3, 4, 5, 8] | 0.202 | 0.455 (5/15) |

## Table 2. ENSO term at lag 3 (own fire-season window, 2001–2025)

| Region | Window | La Niña factor [95 % CI] (n) | Neutral | El Niño factor [95 % CI] (n) | La Niña / El Niño [95 % CI] | p (La Niña vs rest) | p (El Niño vs rest) | Declared signal (v2 rule) | Seasonal PSS (LOYO) |
|---|---|---|---|---|---|---|---|---|---|
| NOA | ago–nov | 1.50 [1.39, 1.76] (12) | 1.25 | 0.92 [0.83, 1.26] (15) | 1.62 [1.10, 2.02] | 0.006 | 0.258 | directa | 0.12 (0.12) |
| NEA | jul–oct | 1.20 [1.04, 1.86] (12) | 1.02 | 1.02 [0.74, 1.15] (14) | 1.18 [0.98, 2.02] | 0.199 | 0.429 | ninguna | 0.07 (0.07) |
| Argentina (country) | jul–oct | 1.26 [1.12, 1.66] (12) | 1.07 | 1.03 [0.79, 1.16] (14) | 1.23 [1.05, 1.69] | 0.219 | 0.549 | directa | -0.01 (-0.01) |
| Centro | ene–dic | 1.10 [0.73, 1.64] (22) | 1.10 | 0.86 [0.63, 1.26] (26) | 1.28 [0.66, 2.14] | 0.546 | 0.255 | ninguna | — (La Niña 0.05 / El Niño -0.11) |
| Patagonia | ene–dic | 0.87 [0.48, 1.00] (34) | 0.88 | 1.16 [0.62, 1.81] (34) | 0.75 [0.41, 1.35] | 0.300 | 0.127 | ninguna | 0.27 (0.27) |
| SUM-S | ago–oct | 0.70 [0.15, 1.73] (8) | 1.06 | 7.68 [0.94, 18.15] (10) | 0.09 [0.02, 0.74] | 0.022 | 0.000 | inversa | 0.19 (0.19) |
| KAL | ago–oct | 0.38 [0.16, 1.54] (8) | 1.10 | 4.87 [1.36, 7.55] (10) | 0.08 [0.03, 0.51] | 0.005 | 0.000 | inversa | 0.21 (0.21) |
| Sumatra + Kalimantan | ago–oct | 0.53 [0.16, 1.66] (8) | 1.10 | 4.59 [1.16, 7.19] (10) | 0.11 [0.03, 0.75] | 0.015 | 0.001 | inversa | 0.20 (0.20) |
| SUM-N | feb–sep | 1.00 [0.42, 1.73] (37) | 1.30 | 1.80 [0.83, 2.44] (34) | 0.56 [0.20, 1.56] | 0.066 | 0.127 | ninguna | 0.10 (0.10) |

n = month-observations of the window in each phase. Seasonal PSS: one case per fire season (25), prediction = phase matches the declared signal, event = season anomaly above 1; LOYO re-derives the sign without the evaluated season. Centro window: Jan + Aug–Oct + Dec; SUM-N window: Feb–Mar + Jun–Sep.

## Table 3. Skill of the published level (HIGH vs rest; event = above-median provincial fire)

| Territory | Rules | Period | n | HIGH rate (%) | Precision (%) | Base (%) | POD (%) | PSS [95 % CI] | Fire in HIGH months (%) | Event rate in HIGH by driver (ENSO only / drought only / both) |
|---|---|---|---|---|---|---|---|---|---|---|
| Argentina | first version | 2012–2024 (in sample) | 3432 | 19.1 | 63.2 | 54.3 | 22.3 | 0.069 [0.002, 0.129] | 34.2 | 48.4 (93) / 64.1 (462) / 72.5 (102) |
| Argentina | revised (Sect. 3.4) | 2012–2024 (in sample) | 3432 | 17.6 | 65.3 | 54.3 | 21.1 | 0.078 [0.021, 0.132] | 32.7 | — / 64.7 (572) / 77.4 (31) |
| Argentina | first version | 2025 | 264 | 27.3 | 44.4 | 46.6 | 26.0 | -0.024 [-0.024, -0.024] | 34.6 | — / 44.4 (72) / — |
| Argentina | revised (Sect. 3.4) | 2025 | 264 | 28.8 | 44.7 | 46.6 | 27.6 | -0.021 [-0.021, -0.021] | 35.5 | — / 44.7 (76) / — |
| Argentina | first version | 2026 Jan–Oct | 219 | 14.2 | 25.8 | 31.5 | 11.6 | -0.037 [-0.037, -0.037] | 8.9 | 57.1 (7) / 18.2 (22) / 0.0 (2) |
| Argentina | revised (Sect. 3.4) | 2026 Jan–Oct | 219 | 13.7 | 30.0 | 31.5 | 13.0 | -0.010 [-0.010, -0.010] | 16.6 | — / 30.0 (30) / — |
| Indonesia | first version | 2012–2024 (in sample) | 2327 | 21.3 | 72.9 | 54.4 | 28.5 | 0.159 [0.068, 0.243] | 62.0 | 46.2 (160) / 81.7 (202) / 91.7 (133) |
| Indonesia | revised (Sect. 3.4) | 2012–2024 (in sample) | 2327 | 14.9 | 84.4 | 54.4 | 23.1 | 0.180 [0.120, 0.242] | 57.9 | — / 80.5 (267) / 97.5 (79) |
| Indonesia | first version | 2025 | 179 | 20.7 | 75.7 | 30.7 | 50.9 | 0.437 [0.437, 0.437] | 38.7 | — / 75.7 (37) / — |
| Indonesia | revised (Sect. 3.4) | 2025 | 179 | 20.7 | 75.7 | 30.7 | 50.9 | 0.437 [0.437, 0.437] | 38.7 | — / 75.7 (37) / — |
| Indonesia | first version | 2026 Jan–Oct | 150 | 52.7 | 72.2 | 63.3 | 60.0 | 0.200 [0.200, 0.200] | 94.8 | 0.0 (4) / 57.1 (28) / 87.2 (47) |
| Indonesia | revised (Sect. 3.4) | 2026 Jan–Oct | 150 | 50.0 | 76.0 | 63.3 | 60.0 | 0.273 [0.273, 0.273] | 94.7 | — / 57.9 (38) / 94.6 (37) |

Bootstrap intervals for single out-of-sample years are degenerate (one year) and are omitted in the text.

## Table 4. Verification at the regional level (revised rules)

**(a) Regional extent rule.** Prediction = number of drought-escalated provinces of the region reaches the LOYO-selected threshold; event = regional detections at or above the monthly median of 2012–2024.

| Region | Provinces | Threshold (LOYO range) | 2012–2024 out-of-fold precision (%) | POD (%) | PSS | 2025–2026 hits / active | 2025–2026 PSS |
|---|---|---|---|---|---|---|---|
| NOA | 5 | 2 (1–4) | 65.6 | 50.0 | 0.194 | 5 / 18 | 0.235 |
| NEA | 7 | 1 (1–2) | 69.9 | 85.7 | 0.427 | 7 / 15 | 0.467 |
| Centro | 7 | 2 (2–2) | 68.6 | 70.2 | 0.327 | 5 / 17 | 0.294 |
| Patagonia | 5 | 2 (2–2) | 59.8 | 65.5 | 0.141 | 15 / 19 | 0.271 |
| SUM-S | 5 | 2 (2–3) | 78.6 | 52.4 | 0.357 | 11 / 16 | 0.417 |
| KAL | 5 | 2 (1–2) | 71.6 | 57.1 | 0.308 | 13 / 16 | 0.667 |
| SUM-N | 5 | 2 (2–2) | 74.7 | 73.8 | 0.446 | 7 / 18 | 0.267 |

**(b) Published level HIGH at province-month level, by region.** PSS against above-median provincial fire; share = fraction of the period's detections falling in HIGH months.

| Region | 2012–2024 PSS | precision / base (%) | share of fire in HIGH (%) | 2025 PSS | 2026 PSS | 2025–2026 PSS | 2025–2026 share of fire in HIGH (%) |
|---|---|---|---|---|---|---|---|
| NOA | 0.087 | 67.5 / 54.4 | 38.8 | -0.124 | -0.250 | -0.133 | 50.6 |
| NEA | 0.102 | 71.0 / 53.8 | 31.4 | 0.089 | 0.091 | 0.110 | 17.7 |
| Centro | 0.069 | 63.7 / 54.4 | 35.0 | -0.062 | -0.067 | -0.057 | 36.4 |
| Patagonia | 0.039 | 59.0 / 54.8 | 26.4 | -0.002 | 0.107 | 0.075 | 72.1 |
| SUM-S | 0.176 | 87.5 / 54.9 | 63.1 | 0.475 | 0.414 | 0.506 | 91.3 |
| KAL | 0.138 | 92.8 / 54.0 | 51.9 | 0.354 | 0.512 | 0.436 | 88.1 |
| SUM-N | 0.227 | 79.2 / 54.2 | 65.4 | 0.426 | 0.218 | 0.337 | 76.8 |

## Appendix B. Lag sweep of the ENSO factors

**Argentina.** Median window anomaly by phase; ratio = La Niña / El Niño with 95 % year-block interval; p = permutation (5000), uncorrected.

| Region | Lag | La Niña (n) | Neutral (n) | El Niño (n) | Ratio [95 % CI] | p La Niña vs rest | p El Niño vs rest |
|---|---|---|---|---|---|---|---|
| NOA | 0 | 1.38 (28) | 1.25 (42) | 0.95 (30) | 1.46 [1.09, 1.94] | 0.004 | 0.064 |
| NOA | 3 | 1.50 (12) | 1.25 (73) | 0.92 (15) | 1.62 [1.10, 2.02] | 0.006 | 0.258 |
| NOA | 6 | 1.34 (23) | 1.24 (56) | 1.01 (21) | 1.32 [0.97, 1.77] | 0.047 | 0.246 |
| NOA | 9 | 1.27 (39) | 1.09 (26) | 1.27 (35) | 1.00 [0.53, 1.49] | 0.302 | 0.956 |
| NOA | 12 | 1.35 (28) | 1.03 (42) | 1.30 (30) | 1.04 [0.52, 1.52] | 0.899 | 0.791 |
| NEA | 0 | 1.05 (20) | 1.08 (55) | 1.00 (25) | 1.05 [0.73, 1.54] | 0.801 | 0.303 |
| NEA | 3 | 1.20 (12) | 1.02 (74) | 1.02 (14) | 1.18 [0.98, 2.02] | 0.199 | 0.429 |
| NEA | 6 | 1.07 (30) | 1.01 (43) | 1.04 (27) | 1.03 [0.51, 1.39] | 0.442 | 0.157 |
| NEA | 9 | 1.02 (38) | 0.95 (26) | 1.09 (36) | 0.93 [0.55, 1.29] | 0.473 | 0.016 |
| NEA | 12 | 1.00 (20) | 1.04 (55) | 1.08 (25) | 0.93 [0.63, 1.17] | 0.413 | 0.338 |
| Argentina (country) | 0 | 1.13 (20) | 1.11 (55) | 1.00 (25) | 1.13 [0.81, 1.45] | 0.902 | 0.481 |
| Argentina (country) | 3 | 1.26 (12) | 1.07 (74) | 1.03 (14) | 1.23 [1.05, 1.69] | 0.219 | 0.549 |
| Argentina (country) | 6 | 1.24 (30) | 1.07 (43) | 1.06 (27) | 1.18 [0.60, 1.35] | 0.571 | 0.398 |
| Argentina (country) | 9 | 1.06 (38) | 1.03 (26) | 1.13 (36) | 0.93 [0.56, 1.28] | 0.283 | 0.052 |
| Argentina (country) | 12 | 1.02 (20) | 1.07 (55) | 1.11 (25) | 0.92 [0.59, 1.28] | 0.311 | 0.539 |
| Centro | 0 | 1.01 (38) | 1.18 (48) | 0.95 (39) | 1.07 [0.63, 1.54] | 0.961 | 0.422 |
| Centro | 3 | 1.10 (22) | 1.10 (77) | 0.86 (26) | 1.28 [0.66, 2.14] | 0.546 | 0.255 |
| Centro | 6 | 1.33 (25) | 1.10 (75) | 0.90 (25) | 1.48 [0.72, 2.06] | 0.890 | 0.179 |
| Centro | 9 | 1.06 (42) | 1.14 (46) | 1.00 (37) | 1.06 [0.65, 1.53] | 0.311 | 0.657 |
| Centro | 12 | 0.90 (39) | 1.26 (47) | 0.94 (39) | 0.96 [0.56, 1.48] | 0.030 | 0.890 |
| Patagonia | 0 | 0.87 (36) | 0.90 (32) | 1.09 (32) | 0.80 [0.47, 1.32] | 0.273 | 0.257 |
| Patagonia | 3 | 0.87 (34) | 0.88 (32) | 1.16 (34) | 0.75 [0.41, 1.35] | 0.300 | 0.127 |
| Patagonia | 6 | 0.82 (15) | 0.95 (66) | 1.14 (19) | 0.72 [0.28, 1.31] | 0.205 | 0.252 |
| Patagonia | 9 | 0.98 (20) | 0.87 (64) | 1.39 (16) | 0.70 [0.21, 1.31] | 0.389 | 0.011 |
| Patagonia | 12 | 0.67 (39) | 1.03 (29) | 0.97 (32) | 0.69 [0.36, 1.24] | 0.009 | 0.198 |

**Sumatra and Kalimantan.** Median window anomaly by phase; ratio = La Niña / El Niño with 95 % year-block interval; p = permutation (5000), uncorrected.

| Region | Lag | La Niña (n) | Neutral (n) | El Niño (n) | Ratio [95 % CI] | p La Niña vs rest | p El Niño vs rest |
|---|---|---|---|---|---|---|---|
| SUM-S | 0 | 0.33 (18) | 1.00 (36) | 3.71 (21) | 0.09 [0.03, 0.50] | 0.001 | 0.000 |
| SUM-S | 3 | 0.70 (8) | 1.06 (57) | 7.68 (10) | 0.09 [0.02, 0.74] | 0.022 | 0.000 |
| SUM-S | 6 | 1.10 (20) | 1.36 (37) | 1.05 (18) | 1.05 [0.06, 3.65] | 0.105 | 0.344 |
| SUM-S | 9 | 1.12 (30) | 2.03 (18) | 1.06 (27) | 1.06 [0.18, 3.65] | 0.225 | 0.656 |
| SUM-S | 12 | 1.15 (18) | 1.57 (36) | 1.04 (21) | 1.10 [0.16, 4.13] | 0.270 | 0.831 |
| KAL | 0 | 0.55 (18) | 0.97 (36) | 4.25 (21) | 0.13 [0.06, 0.29] | 0.000 | 0.000 |
| KAL | 3 | 0.38 (8) | 1.10 (57) | 4.87 (10) | 0.08 [0.03, 0.51] | 0.005 | 0.000 |
| KAL | 6 | 0.83 (20) | 1.51 (37) | 0.93 (18) | 0.90 [0.14, 3.85] | 0.137 | 0.990 |
| KAL | 9 | 1.20 (30) | 1.70 (18) | 0.99 (27) | 1.21 [0.31, 3.19] | 0.302 | 0.784 |
| KAL | 12 | 0.83 (18) | 1.70 (36) | 0.99 (21) | 0.84 [0.23, 2.47] | 0.055 | 0.600 |
| Sumatra + Kalimantan | 0 | 0.50 (18) | 0.98 (36) | 3.44 (21) | 0.14 [0.06, 0.35] | 0.001 | 0.000 |
| Sumatra + Kalimantan | 3 | 0.53 (8) | 1.10 (57) | 4.59 (10) | 0.11 [0.03, 0.75] | 0.015 | 0.001 |
| Sumatra + Kalimantan | 6 | 0.97 (20) | 1.30 (37) | 0.93 (18) | 1.04 [0.15, 3.80] | 0.081 | 0.707 |
| Sumatra + Kalimantan | 9 | 1.11 (30) | 1.78 (18) | 1.00 (27) | 1.11 [0.28, 2.85] | 0.232 | 0.909 |
| Sumatra + Kalimantan | 12 | 0.97 (18) | 1.69 (36) | 1.00 (21) | 0.97 [0.19, 2.49] | 0.157 | 0.922 |
| SUM-N | 0 | 0.69 (31) | 1.34 (86) | 1.76 (33) | 0.39 [0.20, 1.24] | 0.010 | 0.379 |
| SUM-N | 3 | 1.00 (37) | 1.30 (79) | 1.80 (34) | 0.56 [0.20, 1.56] | 0.066 | 0.127 |
| SUM-N | 6 | 1.20 (46) | 1.51 (60) | 1.26 (44) | 0.95 [0.24, 2.87] | 0.139 | 0.815 |
| SUM-N | 9 | 1.00 (42) | 1.94 (68) | 1.19 (40) | 0.84 [0.22, 2.31] | 0.023 | 0.662 |
| SUM-N | 12 | 1.12 (34) | 1.56 (83) | 1.00 (33) | 1.11 [0.56, 3.97] | 0.362 | 0.108 |

## Appendix C. Indian Ocean Dipole control (Indonesia)

Median Aug–Oct anomaly by ENSO phase and IOD state (IOD+ = DMI ≥ 0.4 °C), same month (lag 0) and three months earlier (lag 3).

| Region | Lag | Stratum | Factor | n | Years |
|---|---|---|---|---|---|
| Sumatra + Kalimantan | 0 | neutral / resto | 0.93 | 49 | 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014, 2016, 2017, 2018, 2020, 2021, 2024, 2025 |
| Sumatra + Kalimantan | 0 | nino / iod+ | 4.97 | 7 | 2002, 2015, 2019, 2023 |
| Sumatra + Kalimantan | 0 | neutral / iod+ | 2.80 | 8 | 2006, 2012, 2018, 2019, 2023 |
| Sumatra + Kalimantan | 0 | nina / resto | 0.53 | 8 | 2008, 2010, 2011, 2022 |
| Sumatra + Kalimantan | 0 | nino / resto | 1.16 | 3 | 2009, 2015, 2016 |
| Sumatra + Kalimantan | 0 | *p-values* | p_neutral_iodmas_vs_resto=0.0112 | | |
| Sumatra + Kalimantan | 3 | neutral / resto | 1.13 | 50 | 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014, 2016, 2018, 2020, 2021, 2024, 2025 |
| Sumatra + Kalimantan | 3 | nino / resto | 5.35 | 6 | 2002, 2009, 2015, 2016 |
| Sumatra + Kalimantan | 3 | nina / resto | 0.53 | 8 | 2008, 2010, 2011, 2022 |
| Sumatra + Kalimantan | 3 | neutral / iod+ | 0.65 | 7 | 2012, 2017, 2019, 2020, 2023 |
| Sumatra + Kalimantan | 3 | nino / iod+ | 3.48 | 4 | 2019, 2023 |
| Sumatra + Kalimantan | 3 | *p-values* | p_neutral_iodmas_vs_resto=0.5265 | | |
| SUM-S | 0 | neutral / resto | 1.00 | 49 | 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014, 2016, 2017, 2018, 2020, 2021, 2024, 2025 |
| SUM-S | 0 | nino / iod+ | 7.96 | 7 | 2002, 2015, 2019, 2023 |
| SUM-S | 0 | neutral / iod+ | 5.38 | 8 | 2006, 2012, 2018, 2019, 2023 |
| SUM-S | 0 | nina / resto | 0.70 | 8 | 2008, 2010, 2011, 2022 |
| SUM-S | 0 | nino / resto | 0.94 | 3 | 2009, 2015, 2016 |
| SUM-S | 0 | *p-values* | p_neutral_iodmas_vs_resto=0.0026 | | |
| SUM-S | 3 | neutral / resto | 1.10 | 50 | 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014, 2016, 2018, 2020, 2021, 2024, 2025 |
| SUM-S | 3 | nino / resto | 9.36 | 6 | 2002, 2009, 2015, 2016 |
| SUM-S | 3 | nina / resto | 0.70 | 8 | 2008, 2010, 2011, 2022 |
| SUM-S | 3 | neutral / iod+ | 0.61 | 7 | 2012, 2017, 2019, 2020, 2023 |
| SUM-S | 3 | nino / iod+ | 5.91 | 4 | 2019, 2023 |
| SUM-S | 3 | *p-values* | p_neutral_iodmas_vs_resto=0.8931 | | |
| KAL | 0 | neutral / resto | 0.99 | 49 | 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014, 2016, 2017, 2018, 2020, 2021, 2024, 2025 |
| KAL | 0 | nino / iod+ | 5.49 | 7 | 2002, 2015, 2019, 2023 |
| KAL | 0 | neutral / iod+ | 2.29 | 8 | 2006, 2012, 2018, 2019, 2023 |
| KAL | 0 | nina / resto | 0.38 | 8 | 2008, 2010, 2011, 2022 |
| KAL | 0 | nino / resto | 1.36 | 3 | 2009, 2015, 2016 |
| KAL | 0 | *p-values* | p_neutral_iodmas_vs_resto=0.0293 | | |
| KAL | 3 | neutral / resto | 1.11 | 50 | 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014, 2016, 2018, 2020, 2021, 2024, 2025 |
| KAL | 3 | nino / resto | 6.52 | 6 | 2002, 2009, 2015, 2016 |
| KAL | 3 | nina / resto | 0.38 | 8 | 2008, 2010, 2011, 2022 |
| KAL | 3 | neutral / iod+ | 0.50 | 7 | 2012, 2017, 2019, 2020, 2023 |
| KAL | 3 | nino / iod+ | 3.33 | 4 | 2019, 2023 |
| KAL | 3 | *p-values* | p_neutral_iodmas_vs_resto=0.3966 | | |
| SUM-N | 0 | nina / resto | 1.00 | 36 | 2001, 2006, 2008, 2009, 2010, 2011, 2012, 2018, 2021, 2022, 2023 |
| SUM-N | 0 | neutral / resto | 1.36 | 69 | 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2009, 2010, 2011, 2012, 2013, 2014, 2016, 2017, 2018, 2020, 2021, 2024, 2025 |
| SUM-N | 0 | nino / resto | 1.95 | 24 | 2003, 2005, 2007, 2010, 2015, 2016, 2019, 2020, 2024 |
| SUM-N | 0 | neutral / iod+ | 1.14 | 10 | 2006, 2012, 2017, 2018, 2023 |
| SUM-N | 0 | nino / iod+ | 0.90 | 10 | 2010, 2015, 2019, 2020, 2023, 2024 |
| SUM-N | 0 | nina / iod+ | 0.17 | 1 | 2023 |
| SUM-N | 0 | *p-values* | p_neutral_iodmas_vs_resto=0.9782 | | |
| SUM-N | 3 | nina / resto | 1.00 | 37 | 2001, 2006, 2008, 2009, 2010, 2011, 2012, 2018, 2021, 2022, 2023 |
| SUM-N | 3 | neutral / resto | 1.51 | 72 | 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2009, 2010, 2011, 2012, 2013, 2014, 2016, 2017, 2018, 2020, 2021, 2024, 2025 |
| SUM-N | 3 | nino / resto | 2.00 | 23 | 2003, 2005, 2007, 2010, 2015, 2016, 2019, 2020 |
| SUM-N | 3 | nino / iod+ | 0.83 | 11 | 2007, 2010, 2019, 2020, 2023, 2024 |
| SUM-N | 3 | neutral / iod+ | 0.28 | 7 | 2017, 2020, 2023 |
| SUM-N | 3 | *p-values* | p_neutral_iodmas_vs_resto=0.0071 | | |
