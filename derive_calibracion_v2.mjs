#!/usr/bin/env node
// GFI v2 — Derivador de calibración v2.0.0: umbrales DC p90 por zona de fuego.
//
// Lee los CSVs históricos por zona (~/.openclaw/data/gfi_v2_fwi/fwi_<lat>_<lon>.csv,
// columnas date,ffmc,dmc,dc,isi,bui,fwi — motor Van Wagner de 03_fwi.py, 2012→hoy)
// y agrega a worker/src/enso_calibracion.json la sección "v2", PRESERVANDO todo lo
// v1 existente (el motor v1 sigue siendo la base del nivel). Bump de version a 2.0.0.
//
// Por zona (116): lat, lon, provincia, descriptor cardinal, peso, umbral_dc_p90[12].
//
// UMBRAL (regla A-zonal congelada — re-derivado 27/09/2026 con el ESTADÍSTICO
// OPERATIVO): la climatología de cada mes son las 13 MEDIAS MÓVILES de 30 días
// evaluadas al último día de ese mes calendario, 2012–2024 (ventana [fin−29, fin],
// mínimo 25 días con dato — idéntico al worker y a gen_gfi_retro.mjs). Antes se
// usaban medias de mes calendario: lo calibrado no era lo operado (paper §6.5b).
// #(clim<v) ≥ 11 ⟺ v > s[10] (el 11º menor de los 13 ordenados). Se guarda
//   umbral_dc_p90[m] = s[10]  y el motor dispara con ESTRICTO dc > umbral —
// equivalencia exacta con pct ≥ 90 para todo v real (ties incluidos). Las móviles
// se comparan a 2 decimales (misma precisión con que se derivó).
//
// DESCRIPTOR cardinal: relativo al centroide provincial (media simple de las zonas
// de la provincia, calculado acá offline — nada de geocoding). 8 sectores de 45°
// por rumbo (atan2 de Δlon,Δlat); "centro" si la distancia al centroide es menor
// al 25% de la distancia máxima de las zonas de esa provincia.
//
// Uso: node tools/gfi_v2/derive_calibracion_v2.mjs   (desde geofuego/) — sin red.
import { readFileSync, writeFileSync } from 'node:fs';
import { homedir } from 'node:os';
import { join } from 'node:path';

const HERE = new URL('.', import.meta.url);
const FWI_DIR = join(homedir(), '.openclaw', 'data', 'gfi_v2_fwi');
const CAL_PATH = new URL('./enso_calibracion.json', HERE);
const CLIM_Y0 = 2012, CLIM_Y1 = 2024;

const zonasProv = JSON.parse(readFileSync(new URL('./zonas_fuego.json', HERE), 'utf8')).zonas;
const cal = JSON.parse(readFileSync(CAL_PATH, 'utf8'));

const zid = (z) => `${z.lat.toFixed(2)}_${z.lon.toFixed(2)}`;

// ---- descriptor cardinal (offline, determinista) ----
const SECTORES = ['norte', 'noreste', 'este', 'sureste', 'sur', 'suroeste', 'oeste', 'noroeste'];
function descriptores(zs) {
  const cLat = zs.reduce((a, z) => a + z.lat, 0) / zs.length;
  const cLon = zs.reduce((a, z) => a + z.lon, 0) / zs.length;
  const dist = zs.map(z => Math.hypot(z.lat - cLat, z.lon - cLon));
  const dMax = Math.max(...dist);
  return zs.map((z, i) => {
    if (zs.length === 1 || dist[i] < 0.25 * dMax) return 'centro';
    const rumbo = (Math.atan2(z.lon - cLon, z.lat - cLat) * 180 / Math.PI + 360) % 360;
    return SECTORES[Math.round(rumbo / 45) % 8];
  });
}

// ---- móvil 30d a fin de mes por zona (2 decimales), climatología y umbral s[10] ----
const DIA = 86400e3;
const epoca = (iso) => Math.floor(Date.parse(iso + 'T00:00:00Z') / DIA);
function umbralesDe(id) {
  const csv = readFileSync(join(FWI_DIR, `fwi_${id}.csv`), 'utf8').trim().split('\n');
  const head = csv[0].split(',');
  const iD = head.indexOf('date'), iDC = head.indexOf('dc');
  const serie = new Map(); // epochDay → dc
  for (let i = 1; i < csv.length; i++) {
    const c = csv[i].split(',');
    serie.set(epoca(c[iD]), +c[iDC]);
  }
  const umbral = [];
  for (let m = 1; m <= 12; m++) {
    const clim = [];
    for (let y = CLIM_Y0; y <= CLIM_Y1; y++) {
      const fin = epoca(new Date(Date.UTC(y, m, 0)).toISOString().slice(0, 10));
      let s = 0, n = 0;
      for (let d = fin - 29; d <= fin; d++) {
        const v = serie.get(d);
        if (v !== undefined) { s += v; n++; }
      }
      if (n >= 25) clim.push(+(s / n).toFixed(2));
    }
    if (clim.length !== 13) throw new Error(`${id} mes ${m}: climatología incompleta (${clim.length}/13)`);
    clim.sort((a, b) => a - b);
    umbral.push(clim[10]); // s[10]: dispara pct≥90 ⟺ dc > s[10]
  }
  return umbral;
}

// ---- armar sección v2 ----
const v2zonas = {};
let n = 0;
for (const [prov, zs] of Object.entries(zonasProv)) {
  const desc = descriptores(zs);
  zs.forEach((z, i) => {
    const id = zid(z);
    if (v2zonas[id]) throw new Error(`zona_id duplicado: ${id} (${prov} vs ${v2zonas[id].provincia})`);
    v2zonas[id] = {
      lat: z.lat, lon: z.lon, provincia: prov, descriptor: desc[i],
      peso: z.peso, umbral_dc_p90: umbralesDe(id),
    };
    n++;
  });
}

cal.version = '2.2.0'; // 2.1.0: ENSO con ventana propia por región · 2.2.0: umbrales DC desde móviles 30d a fin de mes — lo calibrado ES lo operado (27/09/2026)
cal.v2 = {
  generado: new Date().toISOString().slice(0, 10),
  fuente: {
    zonas: 'tools/gfi_v2/zonas_fuego.json (k-means ponderado FIRMS 2012–2024, 5 zonas/provincia)',
    dc: 'FWI/DC Van Wagner (03_fwi.py, motor copernicus/tools/fuego/02_fwi.py, hemisferio sur) sobre ERA5/Open-Meteo 2012→hoy',
    derivacion: 'geofuego/tools/gfi_v2/derive_calibracion_v2.mjs',
  },
  regla: 'A-zonal: si la móvil 30d de DC de CUALQUIER zona supera su umbral (dc > umbral_dc_p90[mes] ⟺ pct≥90 vs climatología 2012–2024 leave-nothing-out, pct=100·#(clim<v)/12) → el nivel del distrito sube UN escalón, cap en ALTO. Sin promedios ni umbrales de peso.',
  dc_mensual: 'media móvil de los últimos 30 días de DC diario, comparada (a 2 decimales) contra el umbral del mes calendario en que TERMINA la ventana; el umbral se deriva del MISMO estadístico (13 móviles a fin de mes, 2012–2024) — calibrado == operado desde 2.2.0',
  descriptor: 'cardinal relativo al centroide provincial (media simple de zonas); centro si dist < 25% de la máxima provincial',
  escala: {
    indice: 'GeoFuego Index (GFI)',
    nombre: 'Riesgo Estacional de Incendio', nombre_en: 'Seasonal Fire Risk',
    niveles: ['BAJO', 'MEDIO', 'ALTO'], niveles_en: ['LOW', 'MEDIUM', 'HIGH'],
    mapeo_v1: { bajo: 'BAJO', normal: 'MEDIO', elevado: 'ALTO', critico: 'ALTO' },
  },
  n_zonas: n,
  zonas: v2zonas,
};

writeFileSync(CAL_PATH, JSON.stringify(cal, null, 1));
console.log(`v2 derivada: ${n} zonas → ${CAL_PATH.pathname}`);
const bytes = JSON.stringify(cal).length;
console.log(`tamaño total calibración: ${(bytes / 1024).toFixed(1)} KB`);
