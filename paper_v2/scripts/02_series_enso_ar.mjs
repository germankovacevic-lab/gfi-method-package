// Deriva worker/src/enso_calibracion.json — artefacto versionado del Semáforo ENSO.
// NO re-deriva ciencia: reusa exactamente la maquinaria del spike validado
// (copernicus/tools/fuego/spike_enso_fuego.mjs, 25/09/2026) sobre los mismos datos:
//   ~/.openclaw/data/firms_ar/  (MODIS país 2001–2024 + oni.ascii.txt)
//   deploy/mapa/historico.json (VIIRS 2012–2025)
// El cache vivía en /tmp y se perdió (27/09): el insumo MODIS quedaba irreproducible.
// Ahora es persistente. Para reponerlo: modis_<año>_Argentina.csv de
// firms.modaps.eosdis.nasa.gov/data/country/modis/<año>/ con MAP_KEY
// (~/.config/nasa/firms-map-key); ONI de cpc.ncep.noaa.gov/data/indices/oni.ascii.txt.
// Salida: factores de anomalía de la temporada PROPIA de cada ámbito por fase ENSO, lag 0 y 3,
// por región (NEA/NOA/Centro/Patagonia) y país, + climatología mensual (medianas
// VIIRS 2012–2025) por país y 24 provincias, + mapeo provincia→región DECLARADO
// (el spike midió regiones, no 24 provincias sueltas — el n provincial no da).
// Uso: node tools/derive_enso_calibracion.mjs   (desde geofuego/)

import { readFileSync, writeFileSync } from 'node:fs';
import { homedir } from 'node:os';
import { join } from 'node:path';
import { PROVINCIAS } from './provincias_pip.js';

const CACHE = process.env.FIRMS_CACHE || join(homedir(), '.openclaw', 'data', 'firms_ar');
const HISTORICO = new URL('../gfi_era5_ar/pkg_cds/historico.json', import.meta.url).pathname;
// SALIDA override = dry-run: permite derivar a un archivo aparte y diffear antes de tocar
// el artefacto de prod (la sección v2 la repone después derive_calibracion_v2.mjs).
const SALIDA = process.env.SALIDA || new URL('./enso_calibracion.json', import.meta.url).pathname;
const CONF_MIN = 30;
const MODIS_Y = { desde: 2001, hasta: 2011 };
const MODIS_BASE = { desde: 2001, hasta: 2024 };
const VIIRS_Y = { desde: 2012, hasta: 2025 };
// Ventana de temporada POR ÁMBITO (27/09/2026, re-derivación post-auditoría):
// meses con share ≥ 8% del fuego anual del ámbito (VIIRS 2012–2025) — el mismo
// umbral del gate estacional del producto. Se computa del dato más abajo
// (ventanaPropia); la jul–nov fija anterior medía la temporada del norte en las
// cuatro regiones y dejaba a Patagonia (pico dic–feb) sin medir.
const SHARE_MIN = 0.08;

const REGIONES = {
  NEA: ['Misiones','Corrientes','Entre Ríos','Formosa','Chaco','Santa Fe','Santiago del Estero'],
  NOA: ['Jujuy','Salta','Tucumán','Catamarca','La Rioja'],
  Centro: ['Córdoba','San Luis','Mendoza','San Juan','La Pampa','Buenos Aires','Ciudad Autónoma de Buenos Aires'],
  Patagonia: ['Neuquén','Río Negro','Chubut','Santa Cruz','Tierra del Fuego, Antártida e Islas del Atlántico Sur'],
};

// ---------- ONI (idéntico al spike) ----------
const SEAS = { DJF:0, JFM:1, FMA:2, MAM:3, AMJ:4, MJJ:5, JJA:6, JAS:7, ASO:8, SON:9, OND:10, NDJ:11 };
const oni = new Map();
for (const ln of readFileSync(`${CACHE}/oni.ascii.txt`, 'utf8').split('\n')) {
  const c = ln.trim().split(/\s+/);
  if (c.length !== 4 || !(c[0] in SEAS)) continue;
  oni.set(`${c[1]}-${String(SEAS[c[0]] + 1).padStart(2, '0')}`, +c[3]);
}
const fase = (a) => a === undefined ? null : a >= 0.5 ? 'nino' : a <= -0.5 ? 'nina' : 'neutral';
const clave = (y, m) => `${y}-${String(m + 1).padStart(2, '0')}`;
const faseLag = (y, m, lag) => {
  const t = y * 12 + m - lag;
  return fase(oni.get(clave(Math.floor(t / 12), t % 12)));
};

// ---------- PIP (idéntico al spike) ----------
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

// ---------- Series mensuales por sensor (idéntico al spike) ----------
const serie = { MODIS: { pais: {}, prov: {} }, VIIRS: { pais: {}, prov: {} } };

console.error('Parseando MODIS 2001–2024…');
for (let y = MODIS_BASE.desde; y <= MODIS_BASE.hasta; y++) {
  const mesAr = new Array(12).fill(0);
  const provAr = {};
  for (const ln of readFileSync(`${CACHE}/modis_${y}_Argentina.csv`, 'utf8').split('\n')) {
    const c = ln.split(',');
    if (c.length < 15 || c[0] === 'latitude') continue;
    if (c[14].trim() !== '0' || +c[9] < CONF_MIN) continue;
    const m = +c[5].slice(5, 7) - 1;
    if (m < 0 || m > 11) continue;
    mesAr[m]++;
    const pn = provinciaDe(+c[0], +c[1]);
    if (pn) (provAr[pn] || (provAr[pn] = new Array(12).fill(0)))[m]++;
  }
  serie.MODIS.pais[y] = mesAr;
  for (const [pn, arr] of Object.entries(provAr))
    (serie.MODIS.prov[pn] || (serie.MODIS.prov[pn] = {}))[y] = arr;
}

const viirs = JSON.parse(readFileSync(HISTORICO, 'utf8'));
for (let y = VIIRS_Y.desde; y <= VIIRS_Y.hasta; y++) {
  serie.VIIRS.pais[y] = viirs.ar.mensual[String(y)];
  for (const [pn, d] of Object.entries(viirs.prov))
    if (d.mensual[String(y)]) (serie.VIIRS.prov[pn] || (serie.VIIRS.prov[pn] = {}))[y] = d.mensual[String(y)];
}
for (const sensor of ['MODIS', 'VIIRS']) {
  for (const [reg, provs] of Object.entries(REGIONES)) {
    const out = {};
    for (const y of Object.keys(serie[sensor].pais)) {
      const arr = new Array(12).fill(0);
      for (const pn of provs) {
        const s = serie[sensor].prov[pn]?.[y];
        if (s) for (let m = 0; m < 12; m++) arr[m] += s[m];
      }
      out[y] = arr;
    }
    serie[sensor].prov['R:' + reg] = out;
  }
}

// ---- paper v2: volcado de las series mensuales por sensor/ámbito + ONI para el análisis en Python ----
const oniOut = {};
for (const [k, v] of oni) oniOut[k] = v;
writeFileSync(new URL('./series_enso_AR.json', import.meta.url).pathname,
  JSON.stringify({ serie, oni: oniOut, regiones: REGIONES }, null, 0));
console.error('series_enso_AR.json escrito');
process.exit(0);
