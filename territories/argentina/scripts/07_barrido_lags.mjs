// Barrido de lags con VENTANA PROPIA por región — insumo de la re-derivación del
// término ENSO (27/09/2026, decisión de German post-auditoría).
// Misma maquinaria que derive_enso_calibracion.mjs / 07_barrido_lags.mjs; lo único
// que cambia es la ventana: en vez de jul–nov fija, cada ámbito usa los meses con
// share ≥ 8% de su fuego anual (VIIRS 2012–2025) — el mismo umbral del gate
// estacional del producto, para no inventar un criterio nuevo.
// Uso: node 07_barrido_lags.mjs   (desde el paquete) — reproduce el Apéndice A
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { homedir } from 'node:os';
import { PROVINCIAS } from './provincias_pip.js';
const MODIS_DIR = join(homedir(), '.openclaw', 'data', 'firms_ar');
const HIST = new URL('historico.json', import.meta.url).pathname;
const CONF_MIN = 30, MODIS_Y = {desde:2001,hasta:2011}, MODIS_BASE={desde:2001,hasta:2024}, VIIRS_Y={desde:2012,hasta:2025};
const SHARE_MIN = 0.08;
const REGIONES = {
  NEA:['Misiones','Corrientes','Entre Ríos','Formosa','Chaco','Santa Fe','Santiago del Estero'],
  NOA:['Jujuy','Salta','Tucumán','Catamarca','La Rioja'],
  Centro:['Córdoba','San Luis','Mendoza','San Juan','La Pampa','Buenos Aires','Ciudad Autónoma de Buenos Aires'],
  Patagonia:['Neuquén','Río Negro','Chubut','Santa Cruz','Tierra del Fuego, Antártida e Islas del Atlántico Sur'],
};
const SEAS={DJF:0,JFM:1,FMA:2,MAM:3,AMJ:4,MJJ:5,JJA:6,JAS:7,ASO:8,SON:9,OND:10,NDJ:11};
const oni=new Map();
for (const ln of readFileSync(join(MODIS_DIR,'oni.ascii.txt'),'utf8').split('\n')){
  const c=ln.trim().split(/\s+/); if(c.length!==4||!(c[0] in SEAS))continue;
  oni.set(`${c[1]}-${String(SEAS[c[0]]+1).padStart(2,'0')}`,+c[3]);
}
const fase=a=>a===undefined?null:a>=0.5?'nino':a<=-0.5?'nina':'neutral';
const clave=(y,m)=>`${y}-${String(m+1).padStart(2,'0')}`;
const faseLag=(y,m,lag)=>{const t=y*12+m-lag;return fase(oni.get(clave(Math.floor(t/12),t%12)));};
function enPoly(lat,lon,rings){for(const an of rings){let d=false;for(let i=0,j=an.length-1;i<an.length;j=i++){const[yi,xi]=an[i],[yj,xj]=an[j];if((yi>lat)!==(yj>lat)&&lon<(xj-xi)*(lat-yi)/(yj-yi)+xi)d=!d;}if(d)return true;}return false;}
function provinciaDe(lat,lon){for(const p of PROVINCIAS){const[a,b,c,d]=p.bbox;if(lat<a||lat>c||lon<b||lon>d)continue;if(enPoly(lat,lon,p.rings))return p.n;}return null;}
const serie={MODIS:{pais:{},prov:{}},VIIRS:{pais:{},prov:{}}};
process.stderr.write('parseando MODIS 2001–2024…\n');
for(let y=MODIS_BASE.desde;y<=MODIS_BASE.hasta;y++){
  const mesAr=new Array(12).fill(0), provAr={};
  for(const ln of readFileSync(`${MODIS_DIR}/modis_${y}_Argentina.csv`,'utf8').split('\n')){
    const c=ln.split(','); if(c.length<15||c[0]==='latitude')continue;
    if(c[14].trim()!=='0'||+c[9]<CONF_MIN)continue;
    const m=+c[5].slice(5,7)-1; if(m<0||m>11)continue;
    mesAr[m]++; const pn=provinciaDe(+c[0],+c[1]);
    if(pn)(provAr[pn]||(provAr[pn]=new Array(12).fill(0)))[m]++;
  }
  serie.MODIS.pais[y]=mesAr;
  for(const[pn,arr]of Object.entries(provAr))(serie.MODIS.prov[pn]||(serie.MODIS.prov[pn]={}))[y]=arr;
}
const viirs=JSON.parse(readFileSync(HIST,'utf8'));
for(let y=VIIRS_Y.desde;y<=VIIRS_Y.hasta;y++){
  serie.VIIRS.pais[y]=viirs.ar.mensual[String(y)];
  for(const[pn,d]of Object.entries(viirs.prov))if(d.mensual[String(y)])(serie.VIIRS.prov[pn]||(serie.VIIRS.prov[pn]={}))[y]=d.mensual[String(y)];
}
for(const s of['MODIS','VIIRS'])for(const[reg,ps]of Object.entries(REGIONES)){
  const out={};for(const y of Object.keys(serie[s].pais)){const a=new Array(12).fill(0);
  for(const pn of ps){const q=serie[s].prov[pn]?.[y];if(q)for(let m=0;m<12;m++)a[m]+=q[m];}out[y]=a;}
  serie[s].prov['R:'+reg]=out;}
const mediana=v=>{const s=[...v].sort((a,b)=>a-b),h=s.length>>1;return s.length%2?s[h]:(s[h-1]+s[h])/2;};
function medMens(pa,base){const m=new Array(12);for(let i=0;i<12;i++){const v=[];for(let y=base.desde;y<=base.hasta;y++)if(pa[y])v.push(pa[y][i]);m[i]=mediana(v);}return m;}
function anom(pa,base,uso,sensor){const med=medMens(pa,base),out=[];
  for(let y=uso.desde;y<=uso.hasta;y++){if(!pa[y])continue;for(let m=0;m<12;m++){if(med[m]<5)continue;out.push({y,m,sensor,ratio:pa[y][m]/med[m]});}}return out;}
function serieAnom(amb){const g=s=>amb==='pais'?serie[s].pais:(serie[s].prov[amb]||{});
  return[...anom(g('MODIS'),MODIS_BASE,MODIS_Y,'MODIS'),...anom(g('VIIRS'),VIIRS_Y,VIIRS_Y,'VIIRS')];}
const media=v=>v.reduce((a,b)=>a+b,0)/v.length;
function permAB(A,B,it=20000){const a=A.map(Math.log),b=B.map(Math.log);
  if(a.length<5||b.length<5)return null;const obs=media(a)-media(b),t=[...a,...b];let e=0;
  for(let i=0;i<it;i++){for(let j=0;j<a.length;j++){const k=j+Math.floor(Math.random()*(t.length-j));[t[j],t[k]]=[t[k],t[j]];}
  if(Math.abs(media(t.slice(0,a.length))-media(t.slice(a.length)))>=Math.abs(obs))e++;}return +(e/it).toFixed(3);}
const perm=(g)=>permAB(g.nina,[...g.neutral,...g.nino]);           // Niña vs resto (señal directa)
const permNino=(g)=>permAB(g.nino,[...g.neutral,...g.nina]);       // Niño vs resto (señal inversa)

// ---- ventana propia: meses con share ≥ 8% del fuego anual del ámbito (VIIRS 2012–2025) ----
const MESES_ES=['ene','feb','mar','abr','may','jun','jul','ago','sep','oct','nov','dic'];
function ventanaPropia(amb){
  const pa = amb==='pais'?serie.VIIRS.pais:serie.VIIRS.prov[amb];
  const tot=new Array(12).fill(0); let g=0;
  for(const y of Object.keys(pa))for(let m=0;m<12;m++){tot[m]+=pa[y][m];g+=pa[y][m];}
  const meses=[]; for(let m=0;m<12;m++)if(tot[m]/g>=SHARE_MIN)meses.push(m);
  const cober=meses.reduce((a,m)=>a+tot[m],0)/g;
  return {meses,shares:tot.map(t=>t/g),cober};
}
function porFaseVent(an,lag,vent){const g={nina:[],neutral:[],nino:[]};
  for(const a of an){if(!vent.includes(a.m))continue;const f=faseLag(a.y,a.m,lag);if(f)g[f].push(a.ratio);}return g;}

console.log('\nBARRIDO CON VENTANA PROPIA (share≥8% VIIRS 2012–2025) · MODIS 2001–2011 + VIIRS 2012–2025, anomalía intra-sensor\n');
for(const amb of['pais','R:NOA','R:NEA','R:Centro','R:Patagonia']){
  const v=ventanaPropia(amb);
  const an=serieAnom(amb);
  console.log(`━━━ ${amb.replace('R:','')} · ventana [${v.meses.map(m=>MESES_ES[m]).join(' ')}] cubre ${(100*v.cober).toFixed(0)}% del fuego ━━━`);
  for(const lag of[0,3,6,9,12]){
    const g=porFaseVent(an,lag,v.meses);
    const N=+mediana(g.nina).toFixed(2), Ne=+mediana(g.neutral).toFixed(2), Ni=+mediana(g.nino).toFixed(2);
    const p=perm(g), pN=permNino(g);
    const dir = Ni>N ? 'INVERSA ' : N>Ni ? 'directa ' : 'plana   ';
    console.log(`  lag ${String(lag).padStart(2)}  Niña ${N.toFixed(2)}(n=${String(g.nina.length).padStart(2)}) · neutral ${Ne.toFixed(2)}(n=${String(g.neutral.length).padStart(2)}) · Niño ${Ni.toFixed(2)}(n=${String(g.nino.length).padStart(2)})  → ${dir} p_Niña=${p} p_Niño=${pN}`);
  }
  console.log('');
}
