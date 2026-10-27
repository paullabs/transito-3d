"""Trânsito Brasil 3D, ep. 1, rascunho v2 (26/10, depois de "tem que ser visto do alto, sem barra branca, takes demais, mais contraste"):
TUDO VISTO DE CIMA (câmera ortográfica reta para baixo), sem painel, poucos planos longos e lentos.
  0  aérea sem carros (Estaiada + Marginal), 0 a 3,18 s
  1  a onda inteira num plano só (falas 1 a 7): a pista andando, um carro freia, a fila cresce e anda para trás; a câmera chega perto do carro e recua devagar
  2  'você' dentro da onda (falas 8 e 9): um carro com aro branco chega na fila, para e volta a andar
  3  espaço entre carros (fala 10), 4  poste e dois segundos (fala 11), 5  fecho (falas 12 e 13): a câmera sobe e mostra a pista toda
Cada plano: dict(id, t0, t1, vista, anc, dist=[(t, valor)...], o=[(t, desloc)...])."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import story_ep1_planos as SP

TOTAL = SP.FALA_T[-1][1] + 1.6
CORTE_AEREO = 3.18
B = lambda i: (SP.FALA_T[i - 1][1] + SP.FALA_T[i][0]) / 2        # meio da pausa entre a fala i e a i+1
AEREA = dict(alvo=(-755.0, -370.0, 38.0), d0=640.0, d1=520.0, e0=58.0, e1=74.0, a0=48.0, a1=30.0, lente=35)

SHOTS = [
    dict(id=0, t0=0.0, t1=CORTE_AEREO, vista="aerea", anc="aerea"),
    dict(id=1, t0=CORTE_AEREO, t1=B(7), vista="topo", anc="mix", dist=[(CORTE_AEREO, 104.0), (13.0, 60.0), (25.0, 74.0), (34.0, 100.0), (B(7), 150.0)], o=[(CORTE_AEREO, -10.0), (B(7), 0.0)]),
    dict(id=2, t0=B(7), t1=B(9), vista="topo", anc="voce", dist=[(B(7), 84.0), (B(9), 70.0)], o=[(B(7), 2.0), (B(9), -16.0)], voce=True),
    dict(id=3, t0=B(9), t1=B(10), vista="topo", anc="espB", dist=[(B(9), 62.0), (B(10), 54.0)], o=[(B(9), 8.0), (B(10), 10.0)]),
    dict(id=4, t0=B(10), t1=B(11), vista="topo", anc="espA2", dist=[(B(10), 54.0), (B(11), 60.0)], o=[(B(10), -8.0), (B(11), -12.0)]),
    dict(id=5, t0=B(11), t1=TOTAL, vista="topo", anc="fila", dist=[(B(11), 150.0), (TOTAL, 210.0)], o=[(B(11), 0.0), (TOTAL, 0.0)]),
]
ESPECIAIS = (3, 4)
LENTE = dict(aerea=AEREA["lente"])
PILULAS = [(0.36, 3.10, "Marginal Pinheiros, São Paulo"), (18.6, 24.5, "1 motorista freia"), (36.5, 41.0, "a fila continua"), (41.4, 47.2, "a fila anda pra trás"),
           (53.6, 58.4, "pista cheia"), (59.2, 64.8, "espaço pra frear"), (69.0, 73.3, "regra dos 2 segundos")]


def plano_em(t):
    for s in SHOTS:
        if s["t0"] <= t < s["t1"]:
            return s
    return SHOTS[-1]


if __name__ == "__main__":
    for s in SHOTS:
        print(f"plano {s['id']:2d}  {s['t0']:5.2f}-{s['t1']:5.2f} s ({s['t1'] - s['t0']:5.2f})  {s['vista']:6s} {s['anc']}")
    print("total", round(TOTAL, 2))
