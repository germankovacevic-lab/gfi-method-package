// Figuras NHESS — datos parte 1 (node): fenología por ámbito + barrido de lags con IC.
//
// Reusa EXACTAMENTE la maquinaria de derive_enso_calibracion.mjs / 10_loyo_enso_ventana.mjs
// (mismos datos y filtros; anomalía intra-sensor, ventana propia share ≥ 8%).
// IC95 del factor (mediana por fase): bootstrap percentil de 2.000 remuestreos de las
// mes-observaciones — NOMINAL: la autocorrelación intra-episodio lo hace optimista,
// igual que los p de permutación (§6.1c del paper); se declara en el caption.
//
// Salida: paper/figures/datos/fenologia.json + barrido_ci.json
// Uso: node paper/figures/gen_datos_figuras.mjs   (desde geofuego/, sin red)

import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { homedir } from 'node:os';
import { join } from 'node:path';
import { PROVINCIAS } from '../../worker/src/provincias_pip.js';

const CACHE = join(homedir(), '.openclaw', 'data', 'firms_ar');
const HISTORICO = new URL('../../deploy/mapa/historico.json', import.meta.url).pathname;
const OUT = new URL('./datos/', import.meta.url).pathname;
mkdirSync(OUT, { recursive: true });
const CONF_MIN = 30;
const MODIS_Y = { desde: 2001, hasta: 2011 };
const MODIS_BASE = { desde: 2001, hasta: 2024 };
const VIIRS_Y = { desde: 2012, hasta: 2025 };

const REGIONES = {
  NEA: ['Misiones','Corrientes','Entre Ríos','Formosa','Chaco','Santa Fe','Santiago del Estero'],
  NOA: ['Jujuy','Salta','Tucumán','Catamarca','La Rioja'],
  Centro: ['Córdoba','San Luis','Mendoza','San Juan','La Pampa','Buenos Aires','Ciudad Autónoma de Buenos Aires'],
  Patagonia: ['Neuquén','Río Negro','Chubut','Santa Cruz','Tierra del Fuego, Antártida e Islas del Atlántico Sur'],
};

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

const mediana = (v) => {
  const s = [...v].sort((a, b) => a - b);
  const h = s.length >> 1;
  return s.length % 2 ? s[h] : (s[h - 1] + s[h]) / 2;
};
function medianasMensuales(porAño, base) {
  const med = new Array(12);
  for (let m = 0; m < 12; m++) {
    const vals = [];
    for (let y = base.desde; y <= base.hasta; y++) if (porAño[y]) vals.push(porAño[y][m]);
    med[m] = mediana(vals);
  }
  return med;
}
function anomalias(porAño, base, uso, sensor) {
  const med = medianasMensuales(porAño, base);
  const out = [];
  for (let y = uso.desde; y <= uso.hasta; y++) {
    if (!porAño[y]) continue;
    for (let m = 0; m < 12; m++) {
      if (med[m] < 5) continue;
      out.push({ y, m, sensor, ratio: porAño[y][m] / med[m] });
    }
  }
  return out;
}
function serieAnom(ambito) {
  const g = (s) => ambito === 'pais' ? serie[s].pais : (serie[s].prov[ambito] || {});
  return [
    ...anomalias(g('MODIS'), MODIS_BASE, MODIS_Y, 'MODIS'),
    ...anomalias(g('VIIRS'), VIIRS_Y, VIIRS_Y, 'VIIRS'),
  ];
}
function ventanaPropia(amb, shareMin = 0.08) {
  const pa = amb === 'pais' ? serie.VIIRS.pais : serie.VIIRS.prov[amb];
  const tot = new Array(12).fill(0);
  let g = 0;
  for (const y of Object.keys(pa)) for (let m = 0; m < 12; m++) { tot[m] += pa[y][m]; g += pa[y][m]; }
  const meses = [];
  for (let m = 0; m < 12; m++) if (tot[m] / g >= shareMin) meses.push(m);
  return { meses, cobertura: +(meses.reduce((a, m) => a + tot[m], 0) / g).toFixed(2), shares: tot.map(t => t / g) };
}

const AMBITOS = ['pais', 'R:NEA', 'R:NOA', 'R:Centro', 'R:Patagonia'];
const nom = (amb) => amb === 'pais' ? 'pais' : amb.slice(2);

// ── fenología ──
const fen = {};
for (const amb of AMBITOS) {
  const v = ventanaPropia(amb);
  fen[nom(amb)] = { shares: v.shares.map(x => +x.toFixed(4)), ventana: v.meses, cobertura: v.cobertura };
}
writeFileSync(join(OUT, 'fenologia.json'), JSON.stringify(fen, null, 1));
console.error('fenologia.json OK');

// ── barrido con IC bootstrap ──
function bootCI(vals, iters = 2000) {
  if (vals.length < 5) return null;
  const meds = [];
  for (let i = 0; i < iters; i++) {
    const s = [];
    for (let j = 0; j < vals.length; j++) s.push(vals[Math.floor(Math.random() * vals.length)]);
    meds.push(mediana(s));
  }
  meds.sort((a, b) => a - b);
  return [+meds[Math.floor(iters * 0.025)].toFixed(2), +meds[Math.floor(iters * 0.975)].toFixed(2)];
}
const barrido = {};
for (const amb of AMBITOS) {
  const k = nom(amb);
  const anoms = serieAnom(amb);
  const vent = ventanaPropia(amb).meses;
  barrido[k] = { ventana: vent, lags: {} };
  for (const lag of [0, 3, 6, 9, 12]) {
    const g = { nina: [], neutral: [], nino: [] };
    for (const a of anoms) {
      if (!vent.includes(a.m)) continue;
      const f = faseLag(a.y, a.m, lag);
      if (f) g[f].push(a.ratio);
    }
    barrido[k].lags[lag] = {};
    for (const f of ['nina', 'neutral', 'nino'])
      barrido[k].lags[lag][f] = { factor: +mediana(g[f]).toFixed(2), n: g[f].length, ci95: bootCI(g[f]) };
  }
}
writeFileSync(join(OUT, 'barrido_ci.json'), JSON.stringify(barrido, null, 1));
console.error('barrido_ci.json OK');

// cross-check contra Apéndice A (lag 3)
for (const k of Object.keys(barrido))
  console.error(`  ${k} lag3: Ñ ${barrido[k].lags[3].nina.factor} n ${barrido[k].lags[3].neutral.factor} N ${barrido[k].lags[3].nino.factor}`);
