"""Trânsito Brasil 3D, ep. 1, rascunho v3 (27/10/2026), roteiro curto de 8 falas (~43 s), depois de "prolixo, repete, a parada tem que aparecer já":
TUDO DE CIMA (câmera ortográfica reta para baixo), sem aérea e sem painel. A freada começa na palavra "nada" (1,7 s).
  1  UM plano longo (0 a 28,8 s, falas 1 a 6): o carro que freia, a fila que cresce e anda para trás, o 'você' (aro branco) que para e volta a andar
  3  espaço entre carros (fala 7, 'deixa espaço'), 4  poste e dois segundos (fala 7), 5  fecho (fala 8): a câmera sobe
Cada plano: dict(id, t0, t1, vista, anc, dist=[(t, valor)...], o=[(t, desloc)...]). Tempos: roteiros/voz-transito-v2/tempos.json."""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tb_camera_suave as CS

RAIZ = os.environ.get("TRANSITO3D_PROJETO") or os.getcwd()
SP = sys.modules[__name__]
TE = 1.7           # s do filme (e da simulação): a palavra "nada"
DUR_FREADA, DEC = 2.5, 6.0
TEMPOS = json.load(open(os.path.join(RAIZ, "roteiros", "voz-transito-v2", "tempos.json")))["falas"]
FALA_T = [(f["inicio"], f["inicio"] + f["duracao"]) for f in TEMPOS]
TOTAL = FALA_T[-1][1] + 1.6
# filme -> simulação: câmera lenta (~0,65x) logo depois da freada, depois ~1,35x enquanto a fila anda para trás
MAPA = [(0, 0.0, 1.0), (TE, TE, 0.66), (5.0, 3.9), (8.0, 5.9), (12.0, 8.7, 0.9), (15.0, 13.0, 1.4), (18.0, 17.2), (22.5, 23.2), (26.0, 27.7), (29.0, 31.0, 1.1),
        (36.0, 38.0), (TOTAL, TOTAL + 2.0, 1.0)]
sim_de = lambda film: CS.valor(MAPA, film)

T_GAP, T_POSTE, T_FECHO = 28.8, 31.54, 37.01     # cortes: fim da fala 6, 'Ele passa num poste', fim da fala 7
SHOTS = [
    dict(id=1, t0=0.0, t1=T_GAP, vista="topo", anc="mix",
         dist=[(0.0, 78.0), (TE, 62.0), (5.0, 58.0), (9.0, 64.0), (15.0, 100.0), (21.0, 108.0), (24.5, 84.0), (T_GAP, 68.0)],
         o=[(0.0, -12.0), (5.0, -12.0), (15.0, 0.0), (24.5, -10.0), (T_GAP, -4.0)]),
    dict(id=3, t0=T_GAP, t1=T_POSTE, vista="topo", anc="espB", dist=[(T_GAP, 62.0), (T_POSTE, 54.0)], o=[(T_GAP, 8.0), (T_POSTE, 10.0)]),
    dict(id=4, t0=T_POSTE, t1=T_FECHO, vista="topo", anc="espA2", dist=[(T_POSTE, 54.0), (T_FECHO, 60.0)], o=[(T_POSTE, -8.0), (T_FECHO, -12.0)]),
    dict(id=5, t0=T_FECHO, t1=TOTAL, vista="topo", anc="fila", dist=[(T_FECHO, 150.0), (TOTAL, 210.0)], o=[(T_FECHO, 0.0), (TOTAL, 0.0)]),
]
ESPECIAIS = (3, 4)
LENTE = {}
PILULAS = [(0.2, 2.3, "Marginal Pinheiros, São Paulo"), (2.4, 7.2, "1 motorista freia"), (17.9, 23.0, "a fila anda pra trás"),
           (28.9, 31.4, "espaço pra frear"), (31.7, 36.9, "regra dos 2 segundos")]


def plano_em(t):
    for s in SHOTS:
        if s["t0"] <= t < s["t1"]:
            return s
    return SHOTS[-1]


if __name__ == "__main__":
    for s in SHOTS:
        print(f"plano {s['id']:2d}  {s['t0']:5.2f}-{s['t1']:5.2f} s ({s['t1'] - s['t0']:5.2f})  {s['vista']:6s} {s['anc']}")
    print("total", round(TOTAL, 2), "| sim em 1,7/5/12/22,5/29/37:", [round(sim_de(x), 1) for x in (1.7, 5, 12, 22.5, 29, 37)])
