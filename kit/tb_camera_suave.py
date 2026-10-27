"""Trânsito Brasil 3D: curvas de câmera suaves (python puro, sem Blender).
A câmera é PLANEJADA, não reativa: cada movimento é uma onda (entra devagar, passa pelo meio mais rápida, sai devagar) e as ondas
se encadeiam com a MESMA velocidade na emenda (Hermite cúbico com tangente contínua), então não há tranco nem parada no meio.
    chaves = [(t, valor), (t, valor, tangente), ...]   tangente omitida = média das vizinhas (Catmull-Rom); 0.0 = repouso (começo, fim, ponto de virada)
    valor(chaves, t)"""
import math


def sstep5(u):
    """smootherstep: velocidade e aceleração zeram nas pontas"""
    u = min(max(u, 0.0), 1.0)
    return u * u * u * (u * (u * 6 - 15) + 10)


def valor(chaves, t):
    ks = sorted(chaves, key=lambda k: k[0])
    if t <= ks[0][0]:
        return ks[0][1]
    if t >= ks[-1][0]:
        return ks[-1][1]
    tang = []
    for i, k in enumerate(ks):
        if len(k) > 2 and k[2] is not None:
            tang.append(k[2])
        elif i == 0 or i == len(ks) - 1:
            tang.append(0.0)
        else:
            tang.append((ks[i + 1][1] - ks[i - 1][1]) / (ks[i + 1][0] - ks[i - 1][0]))
    for i in range(len(ks) - 1):
        t0, v0 = ks[i][0], ks[i][1]; t1, v1 = ks[i + 1][0], ks[i + 1][1]
        if t0 <= t <= t1:
            h = t1 - t0; u = (t - t0) / h
            h00 = 2 * u ** 3 - 3 * u ** 2 + 1; h10 = u ** 3 - 2 * u ** 2 + u
            h01 = -2 * u ** 3 + 3 * u ** 2; h11 = u ** 3 - u ** 2
            return h00 * v0 + h10 * h * tang[i] + h01 * v1 + h11 * h * tang[i + 1]
    return ks[-1][1]


def escala_tempo(chaves, f):
    """muda a duração do plano mantendo a forma das ondas"""
    return [(k[0] * f,) + ((k[1],) if len(k) == 2 else (k[1], None if k[2] is None else k[2] / f)) for k in chaves]


def serie_suave(chaves, fps, seg, sigma=0.5):
    """avalia a curva em todos os quadros e passa um filtro gaussiano (sigma em segundos): tira o degrau de aceleração das emendas.
    As pontas são repetidas, então a câmera continua começando e terminando em repouso."""
    n = int(round(seg * fps))
    bruto = [valor(chaves, f / fps) for f in range(n + 1)]
    r = max(1, int(3 * sigma * fps))
    peso = [math.exp(-0.5 * (k / (sigma * fps)) ** 2) for k in range(-r, r + 1)]
    tot = sum(peso)
    pad = [bruto[0]] * r + bruto + [bruto[-1]] * r
    return [sum(pad[i + j] * peso[j] for j in range(2 * r + 1)) / tot for i in range(n + 1)]


def filtra(vs, fps, sigma=0.5):
    """filtro gaussiano numa série qualquer (pontas repetidas)"""
    r = max(1, int(3 * sigma * fps))
    peso = [math.exp(-0.5 * (k / (sigma * fps)) ** 2) for k in range(-r, r + 1)]
    tot = sum(peso); pad = [vs[0]] * r + list(vs) + [vs[-1]] * r
    return [sum(pad[i + j] * peso[j] for j in range(2 * r + 1)) / tot for i in range(len(vs))]
