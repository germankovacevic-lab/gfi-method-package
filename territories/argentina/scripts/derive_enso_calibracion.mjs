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
const HISTORICO = new URL('./historico.json', import.meta.url).pathname;
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

// ---------- Anomalías y agregación (idéntico al spike) ----------
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
      out.push({ y, m, sensor, focos: porAño[y][m], ratio: porAño[y][m] / med[m] });
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
// dos contrastes: Niña-vs-resto prueba una señal directa; Niño-vs-resto una inversa
const permTest = (g) => permAB(g.nina, [...g.neutral, ...g.nino]);
const permTestNino = (g) => permAB(g.nino, [...g.neutral, ...g.nina]);

// ---------- Ventana propia por ámbito (share ≥ 8% VIIRS 2012–2025) ----------
function ventanaPropia(amb) {
  const pa = amb === 'pais' ? serie.VIIRS.pais : serie.VIIRS.prov[amb];
  const tot = new Array(12).fill(0);
  let g = 0;
  for (const y of Object.keys(pa)) for (let m = 0; m < 12; m++) { tot[m] += pa[y][m]; g += pa[y][m]; }
  const meses = [];
  for (let m = 0; m < 12; m++) if (tot[m] / g >= SHARE_MIN) meses.push(m);
  return { meses, cobertura: +(meses.reduce((a, m) => a + tot[m], 0) / g).toFixed(2) };
}

// ---------- Factores por región (cada ámbito en SU ventana) ----------
const MESES_ES = ['ene','feb','mar','abr','may','jun','jul','ago','sep','oct','nov','dic'];
const factores = {};
const ventanas = {};
for (const amb of ['pais', 'R:NEA', 'R:NOA', 'R:Centro', 'R:Patagonia']) {
  const anoms = serieAnom(amb);
  const key = amb === 'pais' ? 'pais' : amb.slice(2);
  const vent = ventanaPropia(amb);
  ventanas[key] = { meses: vent.meses.map(m => MESES_ES[m]), cobertura_fuego: vent.cobertura };
  factores[key] = {};
  for (const lag of [0, 3]) {
    const g = porFase(anoms, lag, vent.meses);
    factores[key]['lag' + lag] = {
      nina:    { factor: +mediana(g.nina).toFixed(2),    n: g.nina.length },
      neutral: { factor: +mediana(g.neutral).toFixed(2), n: g.neutral.length },
      nino:    { factor: +mediana(g.nino).toFixed(2),    n: g.nino.length },
      p_perm_nina_vs_resto: permTest(g),
      p_perm_nino_vs_resto: permTestNino(g),
    };
  }
}

// Señal por región — clasificación cualitativa, parte del artefacto versionado.
//
// ⚠️ REGLA (27/09/2026): el tipo se declara SOLO si el signo se sostiene en el LAG QUE USA
// EL MOTOR (lag 3, ver enso_logic.js) Y es estable en el barrido {0,3,6,9,12}.
//
// RE-DERIVACIÓN 27/09/2026 (ventana propia por ámbito, share ≥ 8% VIIRS 2012–2025;
// barrido en tools/barrido_ventana_propia.mjs, MODIS 2001–2011 + VIIRS 2012–2025):
//   NOA (ago–nov, 81% del fuego):   directa en lags 0/3/6 (p_Niña 0,005 · 0,005 · 0,047);
//                                    lag3 Niña 1,50 / neutral 1,25 / Niño 0,92.
//   Patagonia (dic–mar, 65%):        INVERSA EN LOS 5 LAGS (Niño>Niña siempre); lag3
//                                    Niña 0,87 / Niño 1,16 (p_Niño 0,12), lag9 p_Niño 0,009.
//                                    El signo nunca se da vuelta — a diferencia del caso
//                                    Centro que la auditoría anuló. Mecanismo con literatura
//                                    (Kitzberger & Veblen: Niño → primavera húmeda → carga de
//                                    combustible fino → fuego en la temporada seca siguiente,
//                                    consistente con que la señal crezca con el lag).
//   Centro (ene+ago–oct+dic, 71%):   con su ventana el signo se estabiliza en directa
//                                    (lags 0–9) pero nunca baja de p=0,27 en lags cortos;
//                                    el lag12 inverso p=0,029 es un nominal aislado entre
//                                    25 tests. Sigue 'ninguna'.
//   NEA (jul–oct, 64%) y país (jul–oct, 61%): directa débil a lag 3 (p 0,20 y 0,22).
const senal = {
  pais:      { tipo: 'directa', significancia: 'sugerente',
               nota: 'gradiente Niña>neutral>Niño a lag 0-6 en su ventana jul–oct; p lag3=0,22 nominal, n efectivo ~6 episodios' },
  NEA:       { tipo: 'directa', significancia: 'sugerente', nota: 'Chaco/Sgo. del Estero/Entre Ríos empujan; p lag3=0,20 en su ventana jul–oct' },
  NOA:       { tipo: 'directa', significancia: 'robusta', nota: 'la región fuerte: p lag3=0,005 en su ventana ago–nov, +50% en Niña y −8% en Niño; dirección estable en lags 0/3/6' },
  Centro:    { tipo: 'ninguna', significancia: 'ninguna',
               nota: 'sin señal utilizable: con su ventana propia (ene+ago–oct+dic) el signo es directo en lags 0–9 pero nunca significativo (p≥0,27); domina la climatología local' },
  Patagonia: { tipo: 'inversa', significancia: 'sugerente',
               nota: 'medida por primera vez en SU temporada (dic–mar): Niño por encima de Niña en los 5 lags del barrido, lag3 0,87/0,88/1,16 (p_Niño=0,12 nominal, lag9 p=0,009); consistente con el mecanismo Kitzberger–Veblen (Niño → primavera húmeda → combustible fino). Sugerente, no robusta: n efectivo bajo y sin significancia al lag operativo' },
};

// ---------- Provincia → región (declarado: el spike midió REGIONES) ----------
const provincia_region = {};
for (const [reg, provs] of Object.entries(REGIONES))
  for (const pn of provs) provincia_region[pn] = reg;
const nombresHistorico = Object.keys(viirs.prov);
const sinRegion = nombresHistorico.filter(pn => !provincia_region[pn]);
if (sinRegion.length) throw new Error('provincias sin región: ' + sinRegion.join(', '));

// ---------- Climatología mensual (medianas VIIRS 2012–2025) ----------
const climatologia = { pais: medianasMensuales(serie.VIIRS.pais, VIIRS_Y).map(Math.round) };
for (const pn of nombresHistorico)
  climatologia[pn] = medianasMensuales(serie.VIIRS.prov[pn], VIIRS_Y).map(Math.round);

// ---------- Artefacto ----------
const cal = {
  version: '1.1.0',
  generado: new Date().toISOString().slice(0, 10),
  fuente: {
    spike: 'copernicus/tools/fuego/spike_enso_fuego.mjs + spike_enso_fuego.md (2026-09-25); re-derivación con ventana propia por región 2026-09-27 (tools/barrido_ventana_propia.mjs)',
    fuego: 'FIRMS MODIS país 2001–2011 (conf≥30, type=0; base medianas 2001–2024) + VIIRS S-NPP 2012–2025 (historico.json)',
    enso: 'ONI oficial NOAA/CPC, trimestres móviles asignados al mes central; Niño ≥ +0,5 · Niña ≤ −0,5',
    metodo: 'anomalía = focos del mes / mediana de ese mes calendario del MISMO sensor; factor = mediana de anomalías de la TEMPORADA PROPIA de cada ámbito (meses con share ≥ 8% del fuego anual, VIIRS 2012–2025) por fase; lag = fase ENSO 0/3 meses antes del mes de fuego',
    derivacion: 'geofuego/tools/derive_enso_calibracion.mjs',
  },
  n_episodios_nina: 6,
  caveats: [
    'n efectivo ≈ 6 episodios Niña sustanciales en 2001–2025: autocorrelación intra-episodio → p nominales optimistas; señal país sugerente, no concluyente',
    'la señal es REGIONAL: fuerte en NOA (directa), sugerente inversa en Patagonia, moderada NEA, sin señal utilizable en Centro — el análisis midió regiones, no provincias: cada provincia hereda el factor de su región (mapeo declarado)',
    'el tipo de señal se declara solo si el signo se sostiene en el lag OPERATIVO (3) y es estable en el barrido {0,3,6,9,12}: Centro queda en ninguna (directo pero p≥0,27); Patagonia pasa a inversa SUGERENTE (signo estable en los 5 lags de su temporada dic–mar, p_Niño lag3=0,12 nominal — no significativa al lag operativo)',
    'cada ámbito se mide en SU temporada (share ≥ 8% del fuego anual, VIIRS 2012–2025): NOA ago–nov (81%), NEA jul–oct (64%), Centro ene+ago–oct+dic (71%), Patagonia dic–mar (65%), país jul–oct (61%) — reemplaza la jul–nov fija que dejaba a Patagonia sin medir (v1.0.0)',
    'la temporada 2003-04 (brutal) fue NEUTRAL: fase ENSO = factor de riesgo probabilístico, jamás causa ni pronóstico determinista',
    'p_perm por permutación (20k iters, aleatorio): reproducciones varían en ±0,01; dos contrastes (Niña-vs-resto y Niño-vs-resto — el segundo es el relevante para señales inversas); sin corrección por multiplicidad: con 50 tests (5 ámbitos × 5 lags × 2 contrastes) el umbral Bonferroni es 0,001 y NINGUNA celda lo alcanza (NOA lag3 p=0,005 es la mejor) — la robustez de NOA se sostiene en la estabilidad del signo y efecto en lags 0/3/6, no en sobrevivir la corrección',
    'climatología mensual = medianas VIIRS 2012–2025 por ámbito (mismos filtros que historico.json); temporada 2026 en curso NO incluida',
  ],
  ventanas,
  regiones: Object.fromEntries(Object.entries(REGIONES).map(([r, p]) => [r, p])),
  provincia_region,
  senal,
  factores,
  climatologia,
};

writeFileSync(SALIDA, JSON.stringify(cal, null, 1) + '\n');
console.log('OK →', SALIDA);
console.log('\nFactores por temporada propia (mediana de anomalía):');
for (const [k, v] of Object.entries(factores))
  console.log(`  ${k} [${ventanas[k].meses.join(' ')}]: lag0 Ñ ${v.lag0.nina.factor} / n ${v.lag0.neutral.factor} / N ${v.lag0.nino.factor} (pÑ ${v.lag0.p_perm_nina_vs_resto}/pN ${v.lag0.p_perm_nino_vs_resto}) · lag3 Ñ ${v.lag3.nina.factor} / n ${v.lag3.neutral.factor} / N ${v.lag3.nino.factor} (pÑ ${v.lag3.p_perm_nina_vs_resto}/pN ${v.lag3.p_perm_nino_vs_resto})`);
