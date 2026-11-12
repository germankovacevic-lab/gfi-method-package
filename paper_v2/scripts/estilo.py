"""Estilo común de las figuras NHESS del GFI.

Paleta Okabe–Ito (apta daltonismo; validada con el validador de contraste CVD —
peor par adyacente ΔE deutan 7,6 → SIEMPRE con refuerzo no-cromático: labels
directos, formas de marcador o posición). Identidad fija por entidad:
regiones y fases ENSO llevan siempre el mismo color en todas las figuras.
"""
import json, os
import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
DATOS = os.path.join(HERE, 'datos')

# regiones — identidad fija (labels directos en cada figura como refuerzo)
REGION = {'NEA': '#0072B2', 'NOA': '#E69F00', 'Centro': '#009E73', 'Patagonia': '#56B4E9'}
# (Patagonia celeste y no rosa: validado con --pairs all, peor ΔE CVD 11,4 — el par
#  limítrofe Centro–Patagonia con rosa caía a ΔE 7,6 y colapsaba en deutan)
# fases ENSO — convención de dominio (Niña fría/azul, Niño cálido/bermellón),
# neutral gris DELIBERADO (es la referencia, no una serie más); refuerzo por forma.
FASE = {'nina': '#0072B2', 'neutral': '#666666', 'nino': '#D55E00'}
MARCA_FASE = {'nina': 'o', 'neutral': 's', 'nino': '^'}
NOMBRE_FASE = {'nina': 'La Niña', 'neutral': 'Neutral', 'nino': 'El Niño'}
AZUL = '#0072B2'
VERMELLON = '#D55E00'
GRIS = '#666666'

MESES_EN = ['J', 'F', 'M', 'A', 'M', 'J', 'J', 'A', 'S', 'O', 'N', 'D']

MM = 1 / 25.4  # mm → inch

plt.rcParams.update({
    'font.size': 8,
    'axes.titlesize': 8.5,
    'axes.labelsize': 8,
    'xtick.labelsize': 7.5,
    'ytick.labelsize': 7.5,
    'legend.fontsize': 7.5,
    'axes.linewidth': 0.6,
    'axes.edgecolor': '#999999',
    'axes.spines.top': False,
    'axes.spines.right': False,
    'xtick.color': '#666666',
    'ytick.color': '#666666',
    'axes.labelcolor': '#333333',
    'text.color': '#333333',
    'grid.color': '#dddddd',
    'grid.linewidth': 0.5,
    'legend.frameon': False,
    'figure.dpi': 300,
    'savefig.dpi': 300,
    'savefig.bbox': 'tight',
    'font.family': 'sans-serif',
})


def cargar(nombre):
    return json.load(open(os.path.join(DATOS, nombre)))


def guardar(fig, nombre):
    for ext in ('png', 'pdf'):
        fig.savefig(os.path.join(HERE, f'{nombre}.{ext}'))
    print(f'{nombre}.png/.pdf OK')
