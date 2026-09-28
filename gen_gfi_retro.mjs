// Genera deploy/mapa/gfi_retro.json — hindcast del Riesgo Estacional de Incendio
// (GFI v2) para el tab "× GFI" del calendario: qué nivel hubiera mostrado el
// sistema cada mes 2012→hoy. MISMO motor que prod (enso_logic.nivelAmbito +
// riesgoV2 + enso_calibracion.json v2).
//
// Fase por mes = ONI del trimestre centrado 2 meses antes (el último publicado
// a ese mes — reproduce el lag de publicación del sistema vivo).
// Término de sequía (regla A-zonal): DC de cada zona de fuego desde los CSVs
// históricos (~/.openclaw/data/gfi_v2_fwi/fwi_<lat>_<lon>.csv, 2012→hoy), como
// media móvil de 30 días evaluada a FIN de mes (mismo cómputo que el cron del
// worker: ventana de 30 días, mínimo 25 con dato; para el mes corriente la
// ventana termina en el último día con dato). Mes sin DC → riesgoV2 degrada
// declaradamente a solo-ENSO (nivel v1 mapeado), igual que el sistema vivo.
//
// Al front viajan SOLO niveles y drivers, jamás los factores de calibración:
//   riesgo:  'B'/'M'/'A' (BAJO/MEDIO/ALTO) o '-' sin fase ONI
//   drivers: '.' ninguno · 'e' enso · 's' sequía · 'x' ambos · '-' sin fase
//   niveles: la base v1 ('b'/'n'/'e'/'c') se conserva — la consumen los tests
//            (tools/gfi_v2/test_gfi_v2.mjs) y sirve de traza del escalón.
// Uso: node tools/gen_gfi_retro.mjs   (desde geofuego/)
import { readFileSync, writeFileSync } from 'node:fs';
import { homedir } from 'node:os';
import { join } from 'node:path';
import { parseOni, faseDe, nivelAmbito, riesgoV2 } from './enso_logic.js';

const cal = JSON.parse(readFileSync(new URL('./enso_calibracion.json', import.meta.url), 'utf8'));
if (!cal.v2) throw new Error('calibración sin sección v2 — correr tools/gfi_v2/derive_calibracion_v2.mjs');
const oniTxt = await (await fetch('https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt')).text();
const filas = parseOni(oniTxt);
const porClave = new Map(filas.map(f => [f.anio * 12 + f.mes, f]));
const CODE = { bajo: 'b', normal: 'n', elevado: 'e', critico: 'c' };
const RCODE = { BAJO: 'B', MEDIO: 'M', ALTO: 'A' };
const Y0 = 2012, Y1 = new Date().getUTCFullYear();

// ---- DC 30d a fin de mes, por zona ----
const FWI_DIR = join(homedir(), '.openclaw', 'data', 'gfi_v2_fwi');
const DIA = 86400e3;
const epoca = (iso) => Math.floor(Date.parse(iso + 'T00:00:00Z') / DIA);
const dcZona = {};        // zona_id → Map(epochDay → dc)
let ultimoDia = 0;        // último día con dato en TODO el set (mes corriente parcial)
for (const id of Object.keys(cal.v2.zonas)) {
  const csv = readFileSync(join(FWI_DIR, `fwi_${id}.csv`), 'utf8').trim().split('\n');
  const head = csv[0].split(','), iD = head.indexOf('date'), iDC = head.indexOf('dc');
  const m = new Map();
  for (let i = 1; i < csv.length; i++) {
    const c = csv[i].split(',');
    m.set(epoca(c[iD]), +c[iDC]);
  }
  dcZona[id] = m;
  ultimoDia = Math.max(ultimoDia, Math.max(...m.keys()));
}
// { zona_id → dc30 } del mes (y, m 0-based) — ventana de 30 días que termina el
// último día del mes (o el último día con dato, si el mes es el corriente);
// mínimo 25 días con dato, como el worker. Sin ventana válida → zona ausente.
function dcPorZonaMes(y, m) {
  const finMes = epoca(new Date(Date.UTC(y, m + 1, 0)).toISOString().slice(0, 10));
  const iniMes = epoca(new Date(Date.UTC(y, m, 1)).toISOString().slice(0, 10));
  const fin = Math.min(finMes, ultimoDia);
  if (fin < iniMes) return null;                 // mes enteramente futuro: sin DC
  const out = {};
  for (const [id, serie] of Object.entries(dcZona)) {
    let s = 0, n = 0;
    for (let d = fin - 29; d <= fin; d++) {
      const v = serie.get(d);
      if (v !== undefined) { s += v; n++; }
    }
    if (n >= 25) out[id] = s / n;
  }
  return Object.keys(out).length ? out : null;
}
const dcMes = {};                                // cache (y*12+m) → dcPorZona
const dcDe = (y, m) => (dcMes[y * 12 + m] ??= dcPorZonaMes(y, m));

// ---- series ----
function seriePais() {
  const v1 = {}, r = {}, d = {};
  for (let y = Y0; y <= Y1; y++) {
    let s1 = '', sr = '', sd = '';
    for (let m = 0; m < 12; m++) {
      const f = porClave.get(y * 12 + m - 2);    // trimestre centrado 2 meses antes
      if (!f) { s1 += '-'; sr += '-'; sd += '-'; continue; }
      const n1 = nivelAmbito(cal, faseDe(f.anom), m, 'pais', cal.climatologia.pais, '').nivel;
      const NR = cal.v2.escala.mapeo_v1[n1];     // país: mapeo directo, la regla A es distrital
      s1 += CODE[n1]; sr += RCODE[NR]; sd += NR === 'ALTO' ? 'e' : '.';
    }
    v1[y] = s1; r[y] = sr; d[y] = sd;
  }
  return { v1, r, d };
}
function serieProv(prov, region, clim) {
  const v1 = {}, r = {}, d = {};
  for (let y = Y0; y <= Y1; y++) {
    let s1 = '', sr = '', sd = '';
    for (let m = 0; m < 12; m++) {
      const f = porClave.get(y * 12 + m - 2);
      if (!f) { s1 += '-'; sr += '-'; sd += '-'; continue; }
      const fase = faseDe(f.anom);
      const n1 = nivelAmbito(cal, fase, m, region, clim, '').nivel;
      const rv = riesgoV2(cal, prov, n1, dcDe(y, m), m, fase);
      s1 += CODE[n1]; sr += RCODE[rv.nivel];
      sd += rv.drivers.length === 2 ? 'x' : rv.drivers[0] === 'sequia' ? 's' : rv.drivers[0] === 'enso' ? 'e' : '.';
    }
    v1[y] = s1; r[y] = sr; d[y] = sd;
  }
  return { v1, r, d };
}

const pais = seriePais();
const out = {
  meta: {
    generado: new Date().toISOString().slice(0, 10),
    calibracion: cal.version,
    escala: cal.v2.escala,
    fase_fuente: 'ONI del trimestre centrado 2 meses antes del mes evaluado (último publicado a ese mes)',
    sequia_fuente: 'DC por zona de fuego (116, ERA5/Open-Meteo 2012→hoy), media móvil 30 días a fin de mes — regla A-zonal de la calibración v2 (dc > p90 del mes ⟺ sube un escalón)',
    codigos: { riesgo: 'B=BAJO M=MEDIO A=ALTO', drivers: '.=ninguno e=enso s=sequia x=ambos', niveles: 'base v1: b/n/e/c' },
    aviso: 'Hindcast sobre el período de calibración (ENSO 2001–2025, DC 2012–2024): coherencia in-sample, no verificación fuera de muestra. Desde el despliegue la serie es fuera de muestra.',
  },
  niveles: { pais: pais.v1, provincias: {} },
  riesgo: { pais: pais.r, provincias: {} },
  drivers: { pais: pais.d, provincias: {} },
};
for (const [prov, region] of Object.entries(cal.provincia_region)) {
  const s = serieProv(prov, region, cal.climatologia[prov]);
  out.niveles.provincias[prov] = s.v1;
  out.riesgo.provincias[prov] = s.r;
  out.drivers.provincias[prov] = s.d;
}
// regla de EXTENSIÓN país (misma del motor): ≥2/3 de las provincias (≥16) escaladas
// por sequía en el mes → el país sube un escalón sobre su nivel v1 mapeado.
{
  const RUP = { B: 'M', M: 'A', A: 'A' };
  for (const y of Object.keys(out.riesgo.pais)) {
    let sr = '', sd = '';
    for (let m = 0; m < 12; m++) {
      const c = out.riesgo.pais[y][m];
      if (!c || c === '-') { sr += c || '-'; sd += out.drivers.pais[y][m] || '-'; continue; }
      let nEsc = 0;
      for (const p of Object.values(out.drivers.provincias)) {
        const ch = (p[y] || '')[m];
        if (ch === 's' || ch === 'x') nEsc++;
      }
      const ext = nEsc >= 16;
      sr += ext ? RUP[c] : c;
      const d0 = out.drivers.pais[y][m];
      sd += ext ? (d0 === 'e' ? 'x' : 's') : d0;
    }
    out.riesgo.pais[y] = sr; out.drivers.pais[y] = sd;
  }
}
writeFileSync(new URL('./gfi_v2_retro.json', import.meta.url), JSON.stringify(out));
console.log('gfi_retro.json ok ·', Object.keys(out.riesgo.provincias).length, 'provincias · país 2026:', out.riesgo.pais[2026],
  '· ER 2020:', out.riesgo.provincias['Entre Ríos'][2020], out.drivers.provincias['Entre Ríos'][2020]);
