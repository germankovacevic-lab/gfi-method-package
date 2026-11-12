// GFI — Fase 1 NHESS: (B) leave-one-year-out del término ENSO + (C) sensibilidad
// del umbral de ventana propia (share 6% / 8% / 10%).
//
// Reusa EXACTAMENTE la maquinaria de derive_enso_calibracion.mjs (mismos datos,
// mismos filtros, misma anomalía = focos/mediana del mes calendario del MISMO sensor,
// factor = mediana por fase ENSO en la temporada propia; permutación 20k, dos contrastes).
//
// (B) LOYO por AÑO DE FUEGO Y ∈ 2001–2025: se recalculan las medianas mensuales por
//     sensor SIN Y y los factores por fase SIN Y (ventana operativa fija, la de 2.2.0);
//     el año Y se evalúa con ratios normalizados por la mediana sin-Y (OOS de verdad).
//     Se reporta: rango de factores por fase entre folds, en cuántos folds se sostiene
//     el ORDEN declarado (NOA/NEA/país: Ñ>N directa; Patagonia: N>Ñ inversa), y el
//     pooled out-of-sample: mediana de los ratios OOS agrupados por fase.
//     Además: estabilidad de la propia ventana (share≥8% recalculado sin Y).
// (C) Ventana propia re-derivada con share ≥ 6% / 8% / 10% → factores lag0/lag3 y
//     p_perm de ambos contrastes por ámbito. ¿Sobreviven las conclusiones al umbral?
//
// Uso: node 10_loyo_enso_ventana.mjs   (sin red, ~1 min; requiere los crudos de DATOS.md §2–3)

import { readFileSync } from 'node:fs';
import { homedir } from 'node:os';
import { join } from 'node:path';
import { PROVINCIAS } from './provincias_pip.js';

const CACHE = join(homedir(), '.openclaw', 'data', 'firms_ar');
const HISTORICO = new URL('./historico.json', import.meta.url).pathname;
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

// ---------- ONI ----------
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

// ---------- PIP ----------
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

// ---------- series mensuales por sensor ----------
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

// ---------- helpers (idénticos a la derivación) ----------
const mediana = (v) => {
  const s = [...v].sort((a, b) => a - b);
  const h = s.length >> 1;
  return s.length % 2 ? s[h] : (s[h - 1] + s[h]) / 2;
};
function medianasMensuales(porAño, base, excluir = null) {
  const med = new Array(12);
  for (let m = 0; m < 12; m++) {
    const vals = [];
    for (let y = base.desde; y <= base.hasta; y++)
      if (porAño[y] && y !== excluir) vals.push(porAño[y][m]);
    med[m] = mediana(vals);
  }
  return med;
}
function anomalias(porAño, base, uso, sensor, excluir = null) {
  const med = medianasMensuales(porAño, base, excluir);
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
function serieAnom(ambito, excluir = null) {
  const g = (s) => ambito === 'pais' ? serie[s].pais : (serie[s].prov[ambito] || {});
  return [
    ...anomalias(g('MODIS'), MODIS_BASE, MODIS_Y, 'MODIS', excluir),
    ...anomalias(g('VIIRS'), VIIRS_Y, VIIRS_Y, 'VIIRS', excluir),
  ];
}
function porFase(anoms, lag, ventana) {
  const g = { nina: [], neutral: [], nino: [] };
  for (const a of anoms) {
    if (!ventana.includes(a.m)) continue;
    const f = faseLag(a.y, a.m, lag);
    if (f) g[f].push(a.ratio);
  }
  return g;
}
const media = (v) => v.reduce((a, b) => a + b, 0) / v.length;
function permAB(A, B, iters = 20000) {
  const a = A.map(Math.log), b = B.map(Math.log);
  if (a.length < 5 || b.length < 5) return null;
  const obs = media(a) - media(b);
  const todos = [...a, ...b];
  let ext = 0;
  for (let i = 0; i < iters; i++) {
    for (let j = 0; j < a.length; j++) {
      const k = j + Math.floor(Math.random() * (todos.length - j));
      [todos[j], todos[k]] = [todos[k], todos[j]];
    }
    const ma = media(todos.slice(0, a.length));
    const mb = media(todos.slice(a.length));
    if (Math.abs(ma - mb) >= Math.abs(obs)) ext++;
  }
  return +(ext / iters).toFixed(3);
}
function ventanaPropia(amb, shareMin, excluir = null) {
  const pa = amb === 'pais' ? serie.VIIRS.pais : serie.VIIRS.prov[amb];
  const tot = new Array(12).fill(0);
  let g = 0;
  for (const y of Object.keys(pa)) {
    if (+y === excluir) continue;
    for (let m = 0; m < 12; m++) { tot[m] += pa[y][m]; g += pa[y][m]; }
  }
  const meses = [];
  for (let m = 0; m < 12; m++) if (tot[m] / g >= shareMin) meses.push(m);
  return { meses, cobertura: +(meses.reduce((a, m) => a + tot[m], 0) / g).toFixed(2) };
}

const MESES_ES = ['ene','feb','mar','abr','may','jun','jul','ago','sep','oct','nov','dic'];
const AMBITOS = ['pais', 'R:NEA', 'R:NOA', 'R:Centro', 'R:Patagonia'];
const nom = (amb) => amb === 'pais' ? 'pais' : amb.slice(2);
const fmt = (x) => x === null || x === undefined ? '  –  ' : x.toFixed(2);

// ══════════ (C) SENSIBILIDAD DEL UMBRAL DE VENTANA: share 6% / 8% / 10% ══════════
console.log('\n══ (C) SENSIBILIDAD DE VENTANA — factores por fase y p_perm, share 6/8/10% ══');
for (const shareMin of [0.06, 0.08, 0.10]) {
  console.log(`\n-- share ≥ ${(shareMin * 100).toFixed(0)}% --`);
  for (const amb of AMBITOS) {
    const vent = ventanaPropia(amb, shareMin);
    const anoms = serieAnom(amb);
    const lineas = [];
    for (const lag of [0, 3]) {
      const g = porFase(anoms, lag, vent.meses);
      lineas.push(`lag${lag} Ñ ${fmt(mediana(g.nina))}/${g.nina.length} · n ${fmt(mediana(g.neutral))}/${g.neutral.length} · N ${fmt(mediana(g.nino))}/${g.nino.length}` +
        ` (pÑ ${permAB(g.nina, [...g.neutral, ...g.nino]) ?? '–'} · pN ${permAB(g.nino, [...g.neutral, ...g.nina]) ?? '–'})`);
    }
    console.log(`  ${nom(amb).padEnd(9)} [${vent.meses.map(m => MESES_ES[m]).join(' ')}] cob ${vent.cobertura}`);
    for (const l of lineas) console.log(`    ${l}`);
  }
}

// ══════════ (B) LOYO DEL TÉRMINO ENSO (lag 3 operativo, ventana 2.2.0 fija) ══════════
console.log('\n══ (B) LOYO ENSO — lag 3, ventana operativa fija (share ≥ 8%) ══');
const ORDEN = { pais: 'directa', NEA: 'directa', NOA: 'directa', Centro: null, Patagonia: 'inversa' };
const ANIOS = [];
for (let y = MODIS_Y.desde; y <= VIIRS_Y.hasta; y++) ANIOS.push(y);

for (const amb of AMBITOS) {
  const k = nom(amb);
  const vent = ventanaPropia(amb, 0.08).meses;
  const folds = [];        // { y, fac: {nina, neutral, nino} }
  const oosPorFase = { nina: [], neutral: [], nino: [] };
  let ventCambia = 0;
  for (const Y of ANIOS) {
    // factores SIN el año Y (medianas mensuales también sin Y)
    const anomsSinY = serieAnom(amb, Y).filter(a => a.y !== Y);
    const g = porFase(anomsSinY, 3, vent);
    const fac = { nina: mediana(g.nina), neutral: mediana(g.neutral), nino: mediana(g.nino) };
    folds.push({ y: Y, fac });
    // ratios OOS del año Y, normalizados por la mediana sin-Y
    const oos = serieAnom(amb, Y).filter(a => a.y === Y && vent.includes(a.m));
    for (const a of oos) {
      const f = faseLag(a.y, a.m, 3);
      if (f) oosPorFase[f].push(a.ratio);
    }
    // estabilidad de la ventana share≥8% recalculada sin Y (solo VIIRS)
    if (Y >= VIIRS_Y.desde) {
      const v2 = ventanaPropia(amb, 0.08, Y).meses;
      if (v2.join() !== vent.join()) ventCambia++;
    }
  }
  const rng = (f) => {
    const v = folds.map(x => x.fac[f]).filter(x => x !== undefined && !Number.isNaN(x));
    return `${Math.min(...v).toFixed(2)}–${Math.max(...v).toFixed(2)}`;
  };
  let sostiene = 0;
  for (const { fac } of folds) {
    if (ORDEN[k] === 'directa' && fac.nina > fac.nino) sostiene++;
    if (ORDEN[k] === 'inversa' && fac.nino > fac.nina) sostiene++;
  }
  console.log(`\n  ${k} [${vent.map(m => MESES_ES[m]).join(' ')}] — ${ANIOS.length} folds`);
  console.log(`    factores LOYO (rango entre folds): Ñ ${rng('nina')} · n ${rng('neutral')} · N ${rng('nino')}`);
  if (ORDEN[k])
    console.log(`    orden declarado (${ORDEN[k]}) se sostiene en ${sostiene}/${ANIOS.length} folds`);
  console.log(`    pooled OOS (mediana de ratios del año dejado afuera, por fase):` +
    ` Ñ ${fmt(mediana(oosPorFase.nina))}/${oosPorFase.nina.length}` +
    ` · n ${fmt(mediana(oosPorFase.neutral))}/${oosPorFase.neutral.length}` +
    ` · N ${fmt(mediana(oosPorFase.nino))}/${oosPorFase.nino.length}`);
  console.log(`    p_perm OOS (Ñ vs resto / N vs resto): ` +
    `${permAB(oosPorFase.nina, [...oosPorFase.neutral, ...oosPorFase.nino]) ?? '–'} / ` +
    `${permAB(oosPorFase.nino, [...oosPorFase.neutral, ...oosPorFase.nina]) ?? '–'}`);
  console.log(`    ventana share≥8% recalculada sin Y (14 folds VIIRS): cambia en ${ventCambia}/14`);
}
console.log('\nOK');
