#!/usr/bin/env python3
"""GFI Indonesia — paso 7: control del Dipolo del Océano Índico (IOD).

Pregunta: ¿el término ENSO (ONI, lag 3) está absorbiendo señal que en realidad es del IOD?
(2019 fue IOD+ fuerte con ENSO apenas cálido; 2006 y 2015 combinaron ambos.)
Índice: DMI HadISST1.1 (NOAA PSL, dmi.had.long.data), IOD+ ⟺ DMI ≥ +0.4 °C (umbral BoM).
Mismas anomalías y ventanas que 04_enso.py. Se estratifica el fuego de la ventana por
fase ENSO (lag 3, operativo) × IOD (concurrente = diagnóstico; lag 3 = operativo).
Uso: python3 07_iod.py   (sin red; requiere 01 y 04)
"""
import importlib.util, os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import territorio as T

# reusar la maquinaria de 04 sin re-correr sus permutaciones: importar funciones puras
src = open(os.path.join(HERE, '04_enso.py')).read().split("fmt = lambda")[0]
ns = {'__file__': os.path.join(HERE, '04_enso.py')}
exec(compile(src, '04_enso.py', 'exec'), ns)
serie_anom, ventana, fase_lag, mediana, perm, AMB = (ns[k] for k in ('serie_anom', 'ventana', 'fase_lag', 'mediana', 'perm', 'AMB'))

dmi = {}
for ln in open(f'{T.FIRMS}/dmi.had.long.data'):
    c = ln.split()
    if len(c) == 13 and c[0].isdigit() and 1900 < int(c[0]) < 2100:
        for m in range(12):
            v = float(c[m + 1])
            if v > -99:
                dmi[(int(c[0]), m)] = v


def iod(y, m, lag):
    t = y * 12 + m - lag
    v = dmi.get((t // 12, t % 12))
    return None if v is None else ('iod+' if v >= 0.4 else 'resto')


out = {}
for amb in AMB:
    vent, _ = ventana(amb)
    an = [a for a in serie_anom(amb) if a[1] in vent]
    print(f'\n{amb} [{len(an)} meses-ventana]')
    out[amb] = {}
    for nom, lag_iod in (('IOD concurrente (diagnóstico)', 0), ('IOD lag 3 (operativo)', 3)):
        cel = {}
        for y, m, r in an:
            f, i = fase_lag(y, m, 3), iod(y, m, lag_iod)
            if f and i:
                cel.setdefault((f, i), []).append((y, r))
        print(f'  {nom}:')
        for f in ('nina', 'neutral', 'nino'):
            fila = []
            for i in ('resto', 'iod+'):
                v = cel.get((f, i), [])
                fila.append(f'{i}: {mediana([r for _, r in v]):.2f} (n={len(v)}, años {sorted(set(y for y, _ in v))})' if v else f'{i}: –')
            print(f'    ENSO {f:<8} ' + ' | '.join(fila))
        neu_mas = [r for _, r in cel.get(('neutral', 'iod+'), [])]
        neu_res = [r for _, r in cel.get(('neutral', 'resto'), [])]
        p = perm(neu_mas, neu_res, 20000)
        print(f'    dentro de ENSO neutral: IOD+ {mediana(neu_mas) if neu_mas else float("nan"):.2f} vs resto '
              f'{mediana(neu_res) if neu_res else float("nan"):.2f} · p_perm {p}')
        out[amb][f'lag{lag_iod}'] = {f'{f}|{i}': {'factor': round(mediana([r for _, r in v]), 2), 'n': len(v),
                                                   'anios': sorted(set(y for y, _ in v))}
                                     for (f, i), v in cel.items()} | {'p_neutral_iodmas_vs_resto': p}
json.dump(out, open(os.path.join(HERE, 'control_iod.json'), 'w'), indent=1)
