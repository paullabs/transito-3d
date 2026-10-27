"""Trânsito Brasil 3D, ep. 1: planos do RASCUNHO ANIMADO (python puro). Parte da decupagem aprovada (story_ep1_planos.PLANOS) e acrescenta:
  - o plano 0: vista aérea da Ponte Estaiada e da Marginal, sem carros, até o fim de "em São Paulo," (3,18 s);
  - os cortes no meio da pausa entre as falas (nada fica sem imagem), e o último plano até o fim da voz;
  - as pílulas de texto e o tempo de cada uma.
Cada plano: dict(id, t0, t1, vista, anc, o0, o1, d0, d1, e0, e1, a0, a1)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import story_ep1_planos as SP

TOTAL = SP.TEMPOS and (SP.FALA_T[-1][1] + 1.6)          # a voz acaba em ~84,3 s; o filme vai a ~85,9 s (cauda de 1,4 s)
CORTE_AEREO = 3.18                                       # entre "Paulo," e "e quando chegou lá na frente"
# bordas entre as falas: no meio da pausa
BORDAS = [0.0] + [(SP.FALA_T[i][1] + SP.FALA_T[i + 1][0]) / 2 for i in range(len(SP.FALA_T) - 1)] + [TOTAL]

# o ponto que a vista aérea mira: a torre da Estaiada (mundo, metros) e a câmera (distância, elevação, azimute absoluto) no começo e no fim
AEREA = dict(alvo=(-755.0, -370.0, 38.0), d0=640.0, d1=520.0, e0=30.0, e1=36.0, a0=48.0, a1=30.0, lente=35)

SHOTS = [dict(id=0, t0=0.0, t1=CORTE_AEREO, vista="aerea", anc="aerea", fala=1)]
for pl in SP.PLANOS:
    pid, fala, vista, anc, o0, o1, d0, d1, e0, e1, a0, a1, leg = pl
    t0 = BORDAS[fala - 1] if pid != 1 else CORTE_AEREO
    t1 = BORDAS[fala]
    SHOTS.append(dict(id=pid, t0=t0, t1=t1, vista=vista, anc=anc, o0=o0, o1=o1, d0=d0, d1=d1, e0=e0, e1=e1, a0=a0, a1=a1, fala=fala, legenda=leg))

# cena do espaço (planos 10 e 11): a câmera acompanha o par de carros (B = o carro do vão grande; A2 = o da frente na régua), não o ponto fixo
for sh in SHOTS:
    if sh["id"] == 10:
        sh.update(anc="espB", o0=15, o1=11, d0=44, d1=36)
    if sh["id"] == 11:
        sh.update(anc="espA2", o0=-12, o1=-13, d0=54, d1=60)

PILULAS = [(0.36, 3.10, "Marginal Pinheiros, São Paulo"), (18.6, 24.5, "1 motorista freia"), (41.4, 47.2, "EFEITO SANFONA"),
           (53.6, 58.4, "pista cheia"), (69.0, 73.3, "regra dos 2 segundos")]
LENTE = dict(SP.LENTE, aerea=AEREA["lente"])


def plano_em(t):
    for s in SHOTS:
        if s["t0"] <= t < s["t1"]:
            return s
    return SHOTS[-1]


if __name__ == "__main__":
    for s in SHOTS:
        print(f"plano {s['id']:2d}  {s['t0']:5.2f}-{s['t1']:5.2f} s ({s['t1'] - s['t0']:4.2f})  {s['vista']:11s} {s['anc']}")
    print("total", round(TOTAL, 2))
