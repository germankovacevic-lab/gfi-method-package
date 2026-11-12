// Semáforo de Temporada ENSO — lógica PURA (sin I/O): la comparten el worker
// (cron diario → fila en flama_enso) y los tests de humo.
// Fuente científica: enso_calibracion.json (derivado del spike ENSO×fuego
// 2001–2025, geofuego/tools/derive_enso_calibracion.mjs). Los factores son
// medianas de anomalía estacional por fase ENSO con lag 3 meses, cada región
// medida sobre SU PROPIA ventana de temporada (meses con ≥8% del fuego anual;
// nota técnica §3.1) — el ONI de meses antes anticipa la temporada de cada región.
// El nivel declara PROBABILIDAD sobre 25 años medidos, jamás causalidad.

// ---------- ONI ----------
// Formato oni.ascii.txt (CPC): "SEAS  YR  TOTAL  ANOM", trimestres móviles.
// El trimestre se asigna a su mes CENTRAL (DJF=ene … NDJ=dic), igual que el spike.
const SEAS = { DJF: 0, JFM: 1, FMA: 2, MAM: 3, AMJ: 4, MJJ: 5, JJA: 6, JAS: 7, ASO: 8, SON: 9, OND: 10, NDJ: 11 };

export function parseOni(txt) {
  const filas = [];
  for (const ln of txt.split('\n')) {
    const c = ln.trim().split(/\s+/);
    if (c.length !== 4 || !(c[0] in SEAS)) continue;
    filas.push({ trimestre: c[0] + ' ' + c[1], anio: +c[1], mes: SEAS[c[0]], anom: +c[3] });
  }
  filas.sort((a, b) => (a.anio * 12 + a.mes) - (b.anio * 12 + b.mes));
  return filas;
}

export const faseDe = (anom) => anom >= 0.5 ? 'nino' : anom <= -0.5 ? 'nina' : 'neutral';
const ETIQUETA = { nina: 'Niña', neutral: 'neutral', nino: 'Niño' };
const ETIQUETA_EN = { nina: 'La Niña', neutral: 'neutral', nino: 'El Niño' };

// Pronóstico fallback por PERSISTENCIA: últimos 3 trimestres ONI + tendencia.
// Se usa porque no hay fuente probabilística oficial machine-readable estable
// (IRI ProbForecast quedó tras login OAuth; los .txt históricos de
// iri.columbia.edu/~forecast/ensofcst/Data/ dan 404 — probado 26/09/2026).
// NUNCA se inventa un pronóstico: esto se declara como lo que es.
export function pronosticoPersistencia(filasOni) {
  const u3 = filasOni.slice(-3);
  const d = u3[u3.length - 1].anom - u3[0].anom;
  const tendencia = d >= 0.15 ? 'subiendo' : d <= -0.15 ? 'bajando' : 'estable';
  return {
    fuente: 'persistencia',
    detalle: `Sin fuente probabilística oficial machine-readable (IRI/CPC, verificado 2026-09-26). ` +
      `Persistencia: ONI ${u3.map(f => `${f.trimestre} ${f.anom >= 0 ? '+' : ''}${f.anom.toFixed(1)}`).join(' · ')} — tendencia ${tendencia}.`,
    trimestres: u3.map(f => ({ trimestre: f.trimestre, anom: f.anom })),
    tendencia,
  };
}

// ---------- Semáforo ----------
const COLOR = { bajo: 'verde', normal: 'amarillo', elevado: 'naranja', critico: 'rojo' };
const pct = (f) => Math.round((f - 1) * 100);

// Nivel de UN ámbito. region = clave de factores ('pais'|'NEA'|'NOA'|'Centro'|'Patagonia').
export function nivelAmbito(cal, fase, mes, region, clim, nombreRegion, nombreRegionEn) {
  const total = clim.reduce((a, b) => a + b, 0);
  // ámbito sin fuego histórico relevante (ej. CABA): el semáforo no aplica
  if (total < 24) return {
    nivel: 'bajo', color: COLOR.bajo, factor: null, peso_temporada: null,
    frase: 'Sin actividad de fuego histórica relevante en este ámbito (mediana mensual 2012–2025 ≈ 0).',
    frase_en: 'No historically relevant fire activity in this area (2012–2025 monthly median ≈ 0).',
  };

  // peso climatológico de la ventana (mes corriente + 3 próximos) vs uniforme,
  // con peso DECRECIENTE hacia adelante (4,3,2,1): el fuego del mes presente pesa
  // más que el del horizonte — evita encender Patagonia en septiembre porque
  // diciembre asoma al final de la ventana. "Fuera de temporada" = ventana liviana
  // Y mes corriente sin fuego propio (≥8% del año enciende por sí solo: la cola de
  // temporada del norte —octubre— sigue prendida aunque la ventana ya mire el verano).
  // Validado contra 2012–2024: amarillo-sin-fuego 33→9 provincia-mes (los 9 son
  // pre-temporada legítima a un mes del pico), 0 meses de temporada real apagados.
  const PESOS = [4, 3, 2, 1];
  let ventana = 0;
  for (let i = 0; i < 4; i++) ventana += PESOS[i] * clim[(mes + i) % 12];
  const r = (ventana / total) * (12 / 10);
  const shareMes = clim[mes] / total;
  const fueraTemporada = r < 1.0 && shareMes < 0.08;

  const s = cal.senal[region];
  const f = cal.factores[region].lag3[fase].factor;
  const match = (s.tipo === 'directa' && fase === 'nina') || (s.tipo === 'inversa' && fase === 'nino');
  const contra = (s.tipo === 'directa' && fase === 'nino') || (s.tipo === 'inversa' && fase === 'nina');

  let nivel = 'normal';
  if (fueraTemporada) nivel = 'bajo';
  else if (match && f >= 1.45 && s.significancia === 'robusta' && r >= 1) nivel = 'critico';
  else if (match && f >= 1.10) nivel = 'elevado';
  else if (contra && f <= 0.90) nivel = 'bajo';

  // frase por regla — declara probabilidad medida, jamás causalidad ni certeza.
  // Bilingüe server-side: frase (ES) + frase_en (EN), mismas reglas, un solo motor.
  const rEn = nombreRegionEn || nombreRegion;
  let frase, frase_en;
  if (fueraTemporada) {
    frase = 'Fuera de la temporada principal de fuego de este ámbito según su climatología 2012–2025.';
    frase_en = "Outside this area's main fire season per its 2012–2025 climatology.";
    if (match && f >= 1.10) {
      frase += ` De cara a la próxima temporada: bajo ${ETIQUETA[fase]}, ${nombreRegion} estuvo ~${pct(f)}% sobre su mediana histórica.`;
      frase_en += ` Looking ahead to next season: under ${ETIQUETA_EN[fase]}, ${rEn} ran ~${pct(f)}% above its historical median.`;
    }
  } else if (nivel === 'critico') {
    frase = `Niña activa: en ${nombreRegion} las temporadas bajo Niña estuvieron ~${pct(f)}% sobre su mediana histórica (2001–2025) — la señal regional más robusta del país.`;
    frase_en = `La Niña active: in ${rEn}, seasons under La Niña ran ~${pct(f)}% above their historical median (2001–2025) — the country's most robust regional signal.`;
  } else if (nivel === 'elevado') {
    if (s.tipo === 'inversa') {
      frase = `Niño activo: en ${nombreRegion} las temporadas bajo Niño estuvieron sobre su mediana histórica (2001–2025) — la precipitación del Niño incrementa la biomasa fina que luego se cura y se quema.`;
      frase_en = `El Niño active: in ${rEn}, seasons under El Niño ran above their historical median (2001–2025) — El Niño's precipitation increases the fine biomass that later cures and burns.`;
    } else {
      frase = `${ETIQUETA[fase] === 'Niña' ? 'Niña activa' : 'Fase ' + ETIQUETA[fase]}: en ${nombreRegion} las temporadas bajo ${ETIQUETA[fase]} estuvieron ~${pct(f)}% sobre su mediana histórica (2001–2025).`;
      frase_en = `${fase === 'nina' ? 'La Niña active' : ETIQUETA_EN[fase] + ' phase'}: in ${rEn}, seasons under ${ETIQUETA_EN[fase]} ran ~${pct(f)}% above their historical median (2001–2025).`;
    }
  } else if (nivel === 'bajo' && contra) {
    frase = `${ETIQUETA[fase]} activo: en ${nombreRegion} las temporadas bajo ${ETIQUETA[fase]} estuvieron en o bajo su mediana histórica (2001–2025).`;
    frase_en = `${ETIQUETA_EN[fase]} active: in ${rEn}, seasons under ${ETIQUETA_EN[fase]} stayed at or below their historical median (2001–2025).`;
  } else if (s.tipo === 'ninguna') {
    frase = 'El ENSO no muestra señal medible en esta región (2001–2025): domina la climatología local.';
    frase_en = 'ENSO shows no measurable signal in this region (2001–2025): local climatology governs.';
  } else if (fase === 'neutral') {
    frase = 'Fase ENSO neutral: la expectativa la define la climatología del ámbito.';
    frase_en = "Neutral ENSO phase: the expectation is set by the area's climatology.";
  } else {
    frase = `El ENSO en fase ${ETIQUETA[fase]} no modifica sustancialmente la expectativa histórica de esta región.`;
    frase_en = `ENSO in ${ETIQUETA_EN[fase]} phase does not substantially modify this region's historical expectation.`;
  }

  return { nivel, color: COLOR[nivel], factor: f, peso_temporada: +r.toFixed(2), frase, frase_en };
}

// ---------- GFI v2: Riesgo Estacional de Incendio (escala de 3 niveles) ----------
// Escala nueva: BAJO / MEDIO / ALTO (EN: LOW / MEDIUM / HIGH). El motor v1 sigue
// siendo la base del nivel: bajo→BAJO, normal→MEDIO, elevado y crítico→ALTO.
//
// Regla A-zonal (calibración v2, cal.v2.zonas): si el DC MENSUAL CORRIENTE de
// CUALQUIER zona de fuego de la provincia supera su umbral del mes
// (dc > umbral_dc_p90[mes] ⟺ percentil ≥ 90 vs climatología 2012–2024,
// leave-nothing-out, pct = 100·#(clim<v)/12) → el nivel sube UN escalón, cap en
// ALTO. Sin promedios ni umbrales de peso: un aviso de peligro no promedia.
//
// "DC mensual corriente" = media móvil de los últimos 30 días de DC diario
// (tabla gfi_dc, alimentada por el cron), comparada a 2 decimales contra el
// umbral del mes calendario en que TERMINA la ventana (mes actual).
//
// Sin dato de DC (tabla vacía / migración pendiente / cobertura 0 zonas) →
// degradación DECLARADA a solo-ENSO: nivel v1 mapeado, frase sin término de
// sequía, sequia.disponible=false. NUNCA se rompe el payload.
const V2_ORD = { bajo: 0, normal: 1, elevado: 2, critico: 2 };
const V2_NIVEL = ['BAJO', 'MEDIO', 'ALTO'];
const V2_NIVEL_EN = ['LOW', 'MEDIUM', 'HIGH'];
const V2_COLOR = ['verde', 'amarillo', 'rojo'];
export const DESC_EN = { centro: 'central', norte: 'northern', noreste: 'northeastern', este: 'eastern',
  sureste: 'southeastern', sur: 'southern', suroeste: 'southwestern', oeste: 'western', noroeste: 'northwestern' };

// Nivel v2 de UNA provincia. nivelV1 = 'bajo'|'normal'|'elevado'|'critico' (motor v1).
// dcPorZona = { zona_id → DC mensual corriente (número) } o null (sin dato).
// mes 0-based. fase = 'nina'|'neutral'|'nino' (para nombrar el driver ENSO).
export function riesgoV2(cal, provincia, nivelV1, dcPorZona, mes, fase) {
  const base = V2_ORD[nivelV1];
  const zonas = Object.entries(cal.v2.zonas).filter(([, z]) => z.provincia === provincia);

  // evaluación de sequía sobre las zonas CON dato (dato parcial solo puede
  // perder disparos, jamás inventarlos — la cobertura se declara)
  const conDato = [];
  for (const [id, z] of zonas) {
    const dc = dcPorZona ? dcPorZona[id] : undefined;
    if (typeof dc !== 'number' || !isFinite(dc)) continue;
    const umbral = z.umbral_dc_p90[mes];
    conDato.push({ id, descriptor: z.descriptor, descriptor_en: DESC_EN[z.descriptor],
      lat: z.lat, lon: z.lon, dc: +dc.toFixed(2), umbral, dispara: +dc.toFixed(2) > umbral });
  }
  const disponible = conDato.length > 0;
  const disparos = conDato.filter(d => d.dispara);
  const sequia = disparos.length > 0;
  // zona nombrada: la de mayor exceso sobre su umbral
  const peor = sequia ? disparos.reduce((a, b) => (b.dc - b.umbral > a.dc - a.umbral ? b : a)) : null;

  const n = Math.min(base + (sequia ? 1 : 0), 2);
  const ensoDrv = base === 2;                       // el ENSO ya elevaba (v1 elevado/crítico)
  const drivers = [...(ensoDrv ? ['enso'] : []), ...(sequia ? ['sequia'] : [])];

  const NIV = V2_NIVEL[n], NIV_EN = V2_NIVEL_EN[n];
  const FASE = ETIQUETA[fase], FASE_EN = ETIQUETA_EN[fase];
  const dEs = peor ? peor.descriptor : '', dEn = peor ? DESC_EN[peor.descriptor] : '';
  let frase, frase_en;
  if (ensoDrv && sequia) {
    frase = `${NIV}: fase ${FASE} y sequía acumulada convergen (zona ${dEs}) — el índice de sequía DC de esa zona supera su percentil 90 histórico (2012–2024).`;
    frase_en = `${NIV_EN}: ${FASE_EN} phase and accumulated drought converge (${dEn} zone) — that zone's DC drought index exceeds its historical 90th percentile (2012–2024).`;
  } else if (sequia) {
    frase = `${NIV} por sequía acumulada (zona ${dEs}): el índice de sequía DC de esa zona supera su percentil 90 histórico (2012–2024).`;
    frase_en = `${NIV_EN} due to accumulated drought (${dEn} zone): that zone's DC drought index exceeds its historical 90th percentile (2012–2024).`;
  } else if (ensoDrv) {
    frase = `${NIV} por fase ${FASE}: temporadas históricamente sobre la mediana de su región (2001–2025).`;
    frase_en = `${NIV_EN} due to ${FASE_EN} phase: seasons historically above their regional median (2001–2025).`;
  } else if (n === 1) {
    frase = disponible
      ? 'MEDIO: riesgo estacional dentro del rango normal del ámbito; sin sequía por encima de lo normal en sus zonas de fuego.'
      : 'MEDIO: riesgo estacional dentro del rango normal del ámbito.';
    frase_en = disponible
      ? "MEDIUM: seasonal risk within the area's normal range; no above-normal drought in its fire zones."
      : "MEDIUM: seasonal risk within the area's normal range.";
  } else {
    frase = disponible
      ? 'BAJO: sin señal ENSO ni de sequía por encima de lo normal.'
      : 'BAJO: sin señal ENSO por encima de lo normal.';
    frase_en = disponible
      ? 'LOW: no ENSO or drought signal above normal.'
      : 'LOW: no ENSO signal above normal.';
  }

  return {
    nivel: NIV, nivel_en: NIV_EN, color: V2_COLOR[n],
    escalado: sequia && n > base, drivers,
    zona: peor ? { id: peor.id, descriptor: peor.descriptor, descriptor_en: DESC_EN[peor.descriptor], dc: peor.dc, umbral: peor.umbral } : null,
    // estado por zona (display zonal del mapa) — solo zonas CON dato: el dato
    // parcial se declara en sequia.zonas_con_dato, jamás se rellena
    zonas: conDato,
    sequia: disponible
      ? { disponible: true, zonas_con_dato: conDato.length, zonas_total: zonas.length, disparos: disparos.length }
      : { disponible: false, motivo: 'sin dato de DC (gfi_dc vacía o sin cobertura): nivel solo-ENSO' },
    frase, frase_en,
  };
}

// Payload completo de /api/enso a partir del texto ONI crudo + calibración.
// mesActual 0-based; se pasa explícito para que el test lo controle.
// dcPorZona (opcional): { zona_id → DC mensual corriente } — habilita el riesgo v2
// con término de sequía; null/omitido = degradación declarada a solo-ENSO.
export function construirPayload(cal, oniTxt, mesActual, fechaISO, dcPorZona = null) {
  const filas = parseOni(oniTxt);
  if (!filas.length) throw new Error('ONI vacío/no parseable');
  const ult = filas[filas.length - 1];
  const fase = faseDe(ult.anom);

  const ambitos = {
    pais: nivelAmbito(cal, fase, mesActual, 'pais', cal.climatologia.pais, 'el país', 'the country'),
    provincias: {},
  };
  const NOMBRE_REGION = { NEA: 'el NEA', NOA: 'el NOA', Centro: 'el centro del país', Patagonia: 'la Patagonia' };
  const NOMBRE_REGION_EN = { NEA: 'the NEA', NOA: 'the NOA', Centro: 'central Argentina', Patagonia: 'Patagonia' };
  for (const [prov, region] of Object.entries(cal.provincia_region)) {
    const v1 = nivelAmbito(cal, fase, mesActual, region, cal.climatologia[prov], NOMBRE_REGION[region], NOMBRE_REGION_EN[region]);
    ambitos.provincias[prov] = { region, ...v1 };
    // riesgo v2 (aditivo — el front v1 sigue leyendo nivel/color/frase intactos)
    if (cal.v2) ambitos.provincias[prov].riesgo = riesgoV2(cal, prov, v1.nivel, dcPorZona, mesActual, fase);
  }
  // país: escala v2 mapeada del v1 + regla de EXTENSIÓN — el país sube un escalón
  // cuando la sequía zonal está extendida a ≥2/3 de las provincias (≥16 de 24).
  // Validado 2012–2024: 31 activaciones (~2,4 meses/año), 83,9% (26/31) con focos
  // país sobre la mediana del mes; años tranquilos (2014–2017, 2024) intactos;
  // ago-2020 → ALTO, ene-2022 → MEDIO. (Nota técnica §6.5b: sobre medias de mes
  // calendario la misma regla da 19 meses al 100%.)
  if (cal.v2) {
    const provs = Object.values(ambitos.provincias);
    const nEsc = provs.filter(p => p.riesgo && p.riesgo.drivers.includes('sequia')).length;
    const total = provs.length;
    const extendida = nEsc >= 16;
    const base = V2_ORD[ambitos.pais.nivel];
    const n = Math.min(base + (extendida ? 1 : 0), 2);
    const ensoDrv = base === 2;
    const drivers = [...(ensoDrv ? ['enso'] : []), ...(extendida ? ['sequia'] : [])];
    let frase, frase_en;
    if (extendida) {
      frase = `${V2_NIVEL[n]}: sequía acumulada extendida — ${nEsc} de ${total} provincias con zonas de fuego sobre su percentil 90 histórico de DC (2012–2024)${ensoDrv ? ', convergente con la fase ENSO' : ''}.`;
      frase_en = `${V2_NIVEL_EN[n]}: widespread accumulated drought — ${nEsc} of ${total} provinces with fire zones above their historical 90th-percentile DC (2012–2024)${ensoDrv ? ', converging with the ENSO phase' : ''}.`;
    }
    ambitos.pais.riesgo = {
      nivel: V2_NIVEL[n], nivel_en: V2_NIVEL_EN[n], color: V2_COLOR[n],
      escalado: extendida && n > base, drivers,
      sequia: { aplica: true, regla: 'extensión: ≥2/3 de las provincias escaladas por sequía zonal', provincias_escaladas: nEsc, provincias_total: total },
      ...(frase && { frase, frase_en }),
    };
  }

  return {
    fase: { oni: ult.anom, trimestre: ult.trimestre, etiqueta: ETIQUETA[fase] },
    pronostico: pronosticoPersistencia(filas),
    ambitos,
    ...(cal.v2 && { escala: cal.v2.escala }),
    calibracion_version: cal.version,
    aviso: 'Factor de riesgo estacional probabilístico calibrado sobre 2001–2025 (n≈6 episodios Niña). No es un pronóstico determinista ni una alerta oficial.',
    generado: fechaISO,
  };
}
