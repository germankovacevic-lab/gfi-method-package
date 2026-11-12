// GFI v2 — validación, paso A: asigna cada foco FIRMS 2012–2024 a su zona de fuego.
// Método (el mismo con que se midieron los números del paper): PIP provincia IGN
// (bbox pre-filtro, filtros conf!='l' y type=0, idénticos al histórico) → zona =
// centroide más cercano entre las 5 de ESA provincia (euclídeo lat/lon).
// Input:  ~/.openclaw/data/firms_ar/viirs_<año>.csv (archivo VIIRS S-NPP)
// Output: ~/.openclaw/data/gfi_v2_focos_zona.json → prov → [zonaIdx] → 'YYYY-MM' → count
// Uso: node 05a_focos_por_zona.mjs   (corre en ~2 min; 2.394.573 focos asignados)
import { readFileSync, writeFileSync } from 'node:fs';
import { homedir } from 'node:os';
import { PROVINCIAS } from './provincias_pip.js';

const Z = JSON.parse(readFileSync(new URL('./zonas_fuego.json', import.meta.url), 'utf8')).zonas;
const DATA = homedir() + '/.openclaw/data/firms_ar';

function enPoly(lat, lon, rings) {
  for (const anillo of rings) {
    let dentro = false;
    for (let i = 0, j = anillo.length - 1; i < anillo.length; j = i++) {
      const [yi, xi] = anillo[i], [yj, xj] = anillo[j];
      if ((yi > lat) !== (yj > lat) && lon < (xj - xi) * (lat - yi) / (yj - yi) + xi) dentro = !dentro;
    }
    if (dentro) return true;
  }
  return false;
}
function provinciaDe(lat, lon) {
  for (const p of PROVINCIAS) {
    const [a, b, c, d] = p.bbox;
    if (lat < a || lat > c || lon < b || lon > d) continue;
    if (enPoly(lat, lon, p.rings)) return p.n;
  }
  return null;
}

const out = {};
for (const p in Z) out[p] = Z[p].map(() => ({}));
let tot = 0;
for (let y = 2012; y <= 2024; y++) {
  const lineas = readFileSync(`${DATA}/viirs_${y}.csv`, 'utf8').split('\n');
  for (let i = 1; i < lineas.length; i++) {
    const c = lineas[i].split(',');
    if (c.length < 15) continue;
    if (c[9] === 'l') continue;
    if (c[14].trim() !== '0') continue;
    const lat = +c[0], lon = +c[1];
    const prov = provinciaDe(lat, lon);
    if (!prov || !Z[prov]) continue;
    let best = 0, bd = Infinity;
    Z[prov].forEach((z, j) => {
      const d = (lat - z.lat) ** 2 + (lon - z.lon) ** 2;
      if (d < bd) { bd = d; best = j; }
    });
    const ym = c[5].slice(0, 7);
    out[prov][best][ym] = (out[prov][best][ym] || 0) + 1;
    tot++;
  }
  console.error(y, 'ok');
}
writeFileSync(homedir() + '/.openclaw/data/gfi_v2_focos_zona.json', JSON.stringify(out));
console.error('total focos asignados:', tot);
