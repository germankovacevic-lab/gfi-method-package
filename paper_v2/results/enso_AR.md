# Término ENSO — AR

Ventanas: {'pais': ['jul', 'ago', 'sep', 'oct'], 'NEA': ['jul', 'ago', 'sep', 'oct'], 'NOA': ['ago', 'sep', 'oct', 'nov'], 'Centro': ['ene', 'ago', 'sep', 'oct', 'dic'], 'Patagonia': ['ene', 'feb', 'mar', 'dic']}

## Factores lag 3 (mediana de anomalías de la ventana; IC95 bootstrap bloque-año)

| ámbito | señal | Niña [IC] (n) | neutral | Niño [IC] (n) | Niña/Niño [IC] | p Niña vs resto | p Niño vs resto |
|---|---|---|---|---|---|---|---|
| pais | directa (sugerente) | 1.26 [1.12, 1.66] (12) | 1.07 | 1.03 [0.79, 1.16] (14) | 1.23 [1.05, 1.69] | 0.2188 | 0.5492 |
| NEA | directa (sugerente) | 1.20 [1.04, 1.86] (12) | 1.02 | 1.02 [0.74, 1.15] (14) | 1.18 [0.98, 2.02] | 0.1992 | 0.4292 |
| NOA | directa (robusta) | 1.50 [1.39, 1.76] (12) | 1.25 | 0.92 [0.83, 1.26] (15) | 1.62 [1.10, 2.02] | 0.0056 | 0.258 |
| Centro | ninguna (ninguna) | 1.10 [0.73, 1.64] (22) | 1.10 | 0.86 [0.63, 1.26] (26) | 1.28 [0.66, 2.14] | 0.546 | 0.2554 |
| Patagonia | inversa (sugerente) | 0.87 [0.48, 1.00] (34) | 0.88 | 1.16 [0.62, 1.81] (34) | 0.75 [0.41, 1.35] | 0.2998 | 0.1266 |

## Skill estacional (nivel temporada, lag 3): predicción = fase coincide con la señal declarada; evento = temporada sobre la mediana

| ámbito | fase | temporadas | a/b/c/d | precisión | POD | PSS | PSS LOYO | signo estable LOYO |
|---|---|---|---|---|---|---|---|---|
| pais | nina | 25 | 2/1/15/7 | 0.67 | 0.12 | -0.01 | -0.01 | True |
| NEA | nina | 25 | 2/1/11/11 | 0.67 | 0.15 | 0.07 | 0.07 | True |
| NOA | nina | 25 | 2/0/14/9 | 1.00 | 0.12 | 0.12 | 0.12 | True |
| Centro | — (ninguna) | 25 | | | | si Niña 0.05 / si Niño -0.11 | | |
| Patagonia | nino | 25 | 6/3/6/10 | 0.67 | 0.50 | 0.27 | 0.27 | True |

## Barrido del corte "elevado" (f_match ≥ c), lag 3

| ámbito | f_match [IC] | ≥1.05 | ≥1.1 | ≥1.15 | ≥1.2 | ≥1.25 | ≥1.3 | ≥1.45 | IC excluye 1 |
|---|---|---|---|---|---|---|---|---|---|
| pais | 1.26 [1.12, 1.66] | ✓ | ✓ | ✓ | ✓ | ✓ | · | · | sí |
| NEA | 1.20 [1.04, 1.86] | ✓ | ✓ | ✓ | ✓ | · | · | · | sí |
| NOA | 1.50 [1.39, 1.76] | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | sí |
| Patagonia | 1.16 [0.62, 1.81] | ✓ | ✓ | ✓ | · | · | · | · | no |
