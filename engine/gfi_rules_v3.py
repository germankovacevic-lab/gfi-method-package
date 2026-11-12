#!/usr/bin/env python3
"""GFI rules 3.0 — reference implementation (pure Python, no dependencies).

Reads a territory calibration file (territories/<t>/calibracion_3.0.json) and returns the level of a
province for a given month from three observed inputs:
  * dc30: {zone_index: 30-day trailing mean of the Drought Code of each fire zone of the province}
  * oni_phase: 'nina' | 'neutral' | 'nino' (ONI trimester published for the month, i.e. centred two months earlier)
  * month: 1..12
The production engine (JavaScript) must reproduce this function byte for byte on the same inputs;
the paper's verification (tools 07_motor_v3.py) uses the same logic.

Levels: 'LOW' | 'MEDIUM' | 'HIGH'. Drivers: '.' none, 's' drought, 'e' ENSO match (no drought),
'c' ENSO opposite (no drought), 'x' drought + ENSO match (convergent).
"""
import json

LEVELS = ['LOW', 'MEDIUM', 'HIGH']


class GFI:
    def __init__(self, calibration_path):
        self.cal = json.load(open(calibration_path, encoding='utf-8'))

    # ── season gate ──
    def out_of_season(self, province, month):
        clim = self.cal['climatologia_mensual'][province]; g = self.cal['gate']
        total = sum(clim)
        if total < g['total_min']:
            return True
        m0 = month - 1
        r = sum(w * clim[(m0 + i) % 12] for i, w in enumerate(g['pesos'])) / total * 12 / sum(g['pesos'])
        return r < g['r_min'] and clim[m0] / total < g['share_min']

    # ── drought term ──
    def drought_zone(self, province, month, dc30):
        """index of the first zone above its monthly threshold, or None."""
        for j, z in enumerate(self.cal['zonas'][province]):
            thr = z['umbral_dc'][month - 1]
            v = dc30.get(j)
            if thr is not None and v is not None and round(v, 2) > thr:
                return j
        return None

    # ── ENSO term ──
    def enso_relation(self, province, oni_phase):
        reg = self.cal['provincia_region'][province]; sig = self.cal['senales'].get(reg, {}).get('tipo', 'ninguna')
        match = (sig == 'directa' and oni_phase == 'nina') or (sig == 'inversa' and oni_phase == 'nino')
        opposite = (sig == 'directa' and oni_phase == 'nino') or (sig == 'inversa' and oni_phase == 'nina')
        return sig, match, opposite

    # ── combination ──
    def level(self, province, month, dc30, oni_phase):
        zj = self.drought_zone(province, month, dc30); drought = zj is not None
        if self.out_of_season(province, month):
            return dict(level=LEVELS[1 if drought else 0], driver='s' if drought else '.', zone=zj, gate='out_of_season')
        sig, match, opposite = self.enso_relation(province, oni_phase)
        lvl = 1
        if opposite and not drought:
            lvl = 0
        if drought:
            lvl = 2
        driver = 'x' if (drought and match) else 's' if drought else 'e' if match else 'c' if opposite else '.'
        return dict(level=LEVELS[lvl], driver=driver, zone=zj, gate='in_season', enso_signal=sig)

    # ── regional extent ──
    def regional_level(self, region, escalated_provinces):
        """HIGH for the region when the number of drought-escalated provinces reaches the LOYO threshold."""
        e = self.cal['extension_regional'][region]
        n = sum(1 for p in escalated_provinces if self.cal['provincia_region'].get(p) == region)
        return dict(level='HIGH' if n >= e['umbral'] else 'MEDIUM', n=n, threshold=e['umbral'], N=e['N'])


if __name__ == '__main__':
    import sys
    g = GFI(sys.argv[1])
    print(g.cal['territorio'], g.cal['version'], '· regions:', g.cal['regiones'])
    for r, s in g.cal['senales'].items():
        print(f"  {r}: {s['tipo']} (ratio {s['cociente_nina_nino']} CI {s['cociente_ic95']})")
