// Paper v2 — asigna los focos VIIRS S-NPP de 2025 (archivo país SP) y 2026 (area API: SP hasta
// 2026-07-31, NRT después) a las 116 zonas de fuego CONGELADAS (zonas_fuego.json, 2012–2024).
// Mismo método que 05a_focos_por_zona.mjs (PIP provincia IGN → centroide más cercano de esa provincia).
// Filtros: confidence != 'l'; type == 0 cuando la fila trae 'type' (SP). Las filas NRT no traen
// 'type' → se quitan fuentes fijas con una MÁSCARA de celdas 0.01° que tuvieron alguna detección
// type != 0 en el archivo SP 2012–2025 (mismo criterio que la réplica Indonesia). Se reporta el
// efecto de la máscara sobre 2025 SP (control) contra el filtro oficial type==0.
// Salida: ~/.openclaw/data/gfi_v2_focos_zona_2025_2026.json
//   { focos: prov → [zona] → 'YYYY-MM' → n,  prov_mensual: prov → 'YYYY-MM' → n,  pais: 'YYYY-MM' → n,
//     control_mascara: {...} }
import { readFileSync, writeFileSync } from 'node:fs';
import { homedir } from 'node:os';
import { PROVINCIAS } from './provincias_pip.js';

const Z = JSON.parse(readFileSync(new URL('../gfi_era5_ar/pkg_cds/zonas_fuego.json', import.meta.url), 'utf8')).zonas;
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
const cell = (lat, lon) => `${lat.toFixed(2)}|${lon.toFixed(2)}`;

// ---- máscara de fuentes fijas: celdas 0.01° con alguna detección type != 0 (SP 2012–2025) ----
console.error('máscara de fuentes fijas…');
const mask = new Set();
for (let y = 2012; y <= 2025; y++) {
  const ls = readFileSync(`${DATA}/viirs_${y}.csv`, 'utf8').split('\n');
  const head = ls[0].split(','); const iT = head.indexOf('type');
  for (let i = 1; i < ls.length; i++) {
    const c = ls[i].split(',');
    if (c.length <= iT) continue;
    if (c[iT].trim() !== '0') mask.add(cell(+c[0], +c[1]));
  }
}
// también los 2026 SP (type presente)
console.error(`  ${mask.size} celdas enmascaradas`);

const focos = {}, provM = {}, pais = {};
for (const p in Z) { focos[p] = Z[p].map(() => ({})); provM[p] = {}; }
const ctrl = { sp2025_oficial: 0, sp2025_mascara: 0, sp2025_ambos: 0, nrt2026_total: 0, nrt2026_quitados: 0 };

function procesar(path, etiqueta) {
  const ls = readFileSync(path, 'utf8').split('\n');
  const head = ls[0].split(',');
  const iLat = head.indexOf('latitude'), iLon = head.indexOf('longitude'), iDate = head.indexOf('acq_date'),
    iConf = head.indexOf('confidence'), iType = head.indexOf('type'), iSrc = head.indexOf('source');
  let n = 0;
  for (let i = 1; i < ls.length; i++) {
    const c = ls[i].split(',');
    if (c.length < 14) continue;
    if (c[iConf] === 'l') continue;
    const lat = +c[iLat], lon = +c[iLon];
    const src = iSrc >= 0 ? c[c.length - 1] : 'SP';
    const tieneType = (iType >= 0) && (iSrc < 0 ? true : c.length === head.length);
    let oficial = null, enMask = mask.has(cell(lat, lon));
    if (tieneType) oficial = c[iType].trim() === '0';
    if (etiqueta === '2025') {
      if (oficial) ctrl.sp2025_oficial++;
      if (!enMask) ctrl.sp2025_mascara++;
      if (oficial && !enMask) ctrl.sp2025_ambos++;
    }
    let pasa;
    if (tieneType) pasa = oficial;                 // SP: filtro oficial
    else { ctrl.nrt2026_total++; pasa = !enMask; if (!pasa) ctrl.nrt2026_quitados++; }   // NRT: máscara
    if (!pasa) continue;
    const prov = provinciaDe(lat, lon);
    if (!prov || !Z[prov]) continue;
    let best = 0, bd = Infinity;
    Z[prov].forEach((z, j) => { const d = (lat - z.lat) ** 2 + (lon - z.lon) ** 2; if (d < bd) { bd = d; best = j; } });
    const ym = c[iDate].slice(0, 7);
    focos[prov][best][ym] = (focos[prov][best][ym] || 0) + 1;
    provM[prov][ym] = (provM[prov][ym] || 0) + 1;
    pais[ym] = (pais[ym] || 0) + 1;
    n++;
  }
  console.error(`${etiqueta}: ${n} focos asignados`);
}
procesar(`${DATA}/viirs_2025.csv`, '2025');
procesar(`${DATA}/viirs_2026_area.csv`, '2026');
console.error('control máscara 2025 SP:', ctrl);
writeFileSync(homedir() + '/.openclaw/data/gfi_v2_focos_zona_2025_2026.json',
  JSON.stringify({ generado: new Date().toISOString().slice(0, 10), focos, prov_mensual: provM, pais, control_mascara: ctrl }));
console.error('→ ~/.openclaw/data/gfi_v2_focos_zona_2025_2026.json');
