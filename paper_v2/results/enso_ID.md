# Término ENSO — ID

Ventanas: {'territorio': ['ago', 'sep', 'oct'], 'SUM-N': ['feb', 'mar', 'jun', 'jul', 'ago', 'sep'], 'SUM-S': ['ago', 'sep', 'oct'], 'KAL': ['ago', 'sep', 'oct']}

## Factores lag 3 (mediana de anomalías de la ventana; IC95 bootstrap bloque-año)

| ámbito | señal | Niña [IC] (n) | neutral | Niño [IC] (n) | Niña/Niño [IC] | p Niña vs resto | p Niño vs resto |
|---|---|---|---|---|---|---|---|
| territorio | inversa (?) | 0.53 [0.16, 1.66] (8) | 1.10 | 4.59 [1.16, 7.19] (10) | 0.11 [0.03, 0.75] | 0.0154 | 0.0006 |
| SUM-N | inversa (?) | 1.00 [0.42, 1.73] (37) | 1.30 | 1.80 [0.83, 2.44] (34) | 0.56 [0.20, 1.56] | 0.0664 | 0.127 |
| SUM-S | inversa (?) | 0.70 [0.15, 1.73] (8) | 1.06 | 7.68 [0.94, 18.15] (10) | 0.09 [0.02, 0.74] | 0.022 | 0.0 |
| KAL | inversa (?) | 0.38 [0.16, 1.54] (8) | 1.10 | 4.87 [1.36, 7.55] (10) | 0.08 [0.03, 0.51] | 0.0054 | 0.0004 |

## Skill estacional (nivel temporada, lag 3): predicción = fase coincide con la señal declarada; evento = temporada sobre la mediana

| ámbito | fase | temporadas | a/b/c/d | precisión | POD | PSS | PSS LOYO | signo estable LOYO |
|---|---|---|---|---|---|---|---|---|
| territorio | nino | 25 | 3/0/12/10 | 1.00 | 0.20 | 0.20 | 0.20 | True |
| SUM-N | nino | 25 | 3/1/12/9 | 0.75 | 0.20 | 0.10 | 0.10 | True |
| SUM-S | nino | 25 | 3/0/13/9 | 1.00 | 0.19 | 0.19 | 0.19 | True |
| KAL | nino | 25 | 3/0/11/11 | 1.00 | 0.21 | 0.21 | 0.21 | True |

## Barrido del corte "elevado" (f_match ≥ c), lag 3

| ámbito | f_match [IC] | ≥1.05 | ≥1.1 | ≥1.15 | ≥1.2 | ≥1.25 | ≥1.3 | ≥1.45 | IC excluye 1 |
|---|---|---|---|---|---|---|---|---|---|
| territorio | 4.59 [1.16, 7.19] | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | sí |
| SUM-N | 1.80 [0.83, 2.44] | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | no |
| SUM-S | 7.68 [0.94, 18.15] | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | no |
| KAL | 4.87 [1.36, 7.55] | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | sí |
