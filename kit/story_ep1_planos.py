"""Trânsito Brasil 3D, ep. 1: tabela dos planos (python puro). Usada pelo storyboard (tb_story_ep1.py), pela decupagem em texto e, depois, pela animação.
Tempos: roteiros/voz-transito/tempos.json. Mapa de tempo filme -> simulação: câmera lenta (~0,45x) logo depois da freada, depois mais rápido."""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tb_camera_suave as CS

RAIZ = os.environ.get("TRANSITO3D_PROJETO") or os.getcwd()
TE = 18.5          # s do filme: a palavra "pisa"
DUR_FREADA, DEC = 2.5, 6.0
TEMPOS = json.load(open(os.path.join(RAIZ, "roteiros", "voz-transito", "tempos.json")))["falas"]
FALA_T = [(f["inicio"], f["inicio"] + f["duracao"]) for f in TEMPOS]
FALA_TXT = [f["legenda"] for f in TEMPOS]

# ---------------------------------------------------------------- tempo: filme -> simulação
MAPA = [(0, 0.0, 1.0), (TE, TE, 0.75)] + [(f, TE + s) for f, s in
        [(19.7, 0.9), (21.5, 1.7), (24.3, 2.9), (26.5, 3.9), (31.6, 6.5), (34.2, 8.0), (41.0, 13.5), (47.0, 22.0), (50.0, 29.0), (58.5, 44.0),
         (73.36, 56.0), (79.7, 66.0), (85.9, 72.0)]]
sim_de = lambda film: CS.valor(MAPA, film)

# ---------------------------------------------------------------- planos: (id, fala, vista, âncora, desloc0, desloc1, dist0, dist1, elev0, elev1, azim0, azim1, o que a legenda diz)
# deslocamento em metros ao longo da pista (+ = para frente, no sentido do fluxo) a partir da âncora; dist = distância (ou altura visível, no topo)
PLANOS = [
 (1,  1, "perspectiva", "ponto", -10, -24, 70, 88, 50, 54, 0, 5,   "Marginal Pinheiros, São Paulo"),
 (2,  2, "baixa",       "vit",    18,  16, 42, 34, 16, 13, -6, 4,  ""),
 (3,  3, "diagonal",    "vit",    16,  10, 74, 60, 40, 36, 38, 30, "1 motorista freia"),
 (4,  4, "baixa",       "ponto",  -2,  -8, 40, 46, 22, 26, 24, 12, ""),
 (5,  5, "topo",        "fila",    2,  -2, 58, 66, 90, 90, 0, 0,   ""),
 (6,  6, "diagonal",    "fila",   12,   8, 86, 100, 40, 44, 36, 28, ""),
 (7,  7, "topo",        "fila",   -2, -12, 70, 94, 90, 90, 0, 0,   "EFEITO SANFONA"),
 (8,  8, "perspectiva", "cauda",   8,  -6, 56, 60, 44, 40, 4, 0,   ""),
 (9,  9, "diagonal",    "fila",    0,  -6, 118, 150, 44, 50, 30, 22, "pista cheia"),
 (10, 10, "baixa",      "ponto",  -4,   6, 40, 34, 15, 14, 4, -6,  ""),
 (11, 11, "topo",       "ponto",  -6, -10, 52, 58, 90, 90, 0, 0,   "regra dos 2 segundos"),
 (12, 12, "perspectiva", "cabeca", 18, 10, 92, 100, 52, 54, 8, 4,  ""),
 (13, 13, "topo",       "fila",    0,   0, 120, 260, 90, 90, 0, 0,  ""),
]
LENTE = {"perspectiva": 45, "baixa": 35, "diagonal": 45, "topo": 45}

