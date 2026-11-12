#!/bin/zsh
# Paper v2 — focos Argentina 2025 (archivo país VIIRS S-NPP SP) y 2026 (area API: SP + NRT).
# 2025/2026 NO entraron en ninguna calibración (DC hasta 2024, ENSO hasta 2025 solo para factores;
# aquí 2025 se usa para el término de sequía fuera de muestra y 2026 para ambos términos).
# Key: ~/.config/nasa/firms-map-key. Salida: ~/.openclaw/data/firms_ar/
set -e
KEY=$(cat ~/.config/nasa/firms-map-key)
D=~/.openclaw/data/firms_ar
AREA='-73.6,-55.1,-53.6,-21.7'   # W,S,E,N Argentina (misma bbox que FLAMA)
BASE=https://firms.modaps.eosdis.nasa.gov/api/area/csv

if [ ! -s $D/viirs_2025.csv ]; then
  echo "2025: archivo país…"
  curl -fsS -o $D/viirs_2025.csv "https://firms.modaps.eosdis.nasa.gov/data/country/viirs-snpp/2025/viirs-snpp_2025_Argentina.csv?MAP_KEY=$KEY"
  echo "2025: $(wc -l < $D/viirs_2025.csv) filas"
fi

# 2026: SP (científico, con columna type) hasta 2026-07-31 (data_availability); NRT desde 2026-08-01.
# Bloques de 5 días (máximo de la area API). Límite 5000 transacciones / 10 min.
OUT=$D/viirs_2026_area.csv
TMP=$(mktemp -d)
echo "2026: area API…"
d=2026-01-01
HOY=$(date -u +%Y-%m-%d)
first=1
while [[ "$d" < "$HOY" ]]; do
  if [[ "$d" < "2026-08-01" ]]; then src=VIIRS_SNPP_SP; else src=VIIRS_SNPP_NRT; fi
  f=$TMP/${src}_$d.csv
  if curl -fsS -o $f "$BASE/$KEY/$src/$AREA/5/$d"; then
    n=$(($(wc -l < $f)-1))
    if [ $first = 1 ]; then head -1 $f | sed 's/$/,source/' > $OUT; first=0; fi
    [ $n -gt 0 ] && tail -n +2 $f | sed "s/\$/,$src/" >> $OUT
    echo "  $d $src $n"
  else
    echo "fallo $src $d"
  fi
  sleep 0.5
  d=$(date -u -j -f %Y-%m-%d -v+5d $d +%Y-%m-%d)
done
echo "2026: $(($(wc -l < $OUT)-1)) filas → $OUT"
rm -rf $TMP
