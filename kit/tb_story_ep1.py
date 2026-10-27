"""Trânsito Brasil 3D, ep. 1: STORYBOARD RENDERIZADO das 13 falas, nas quatro vistas, sobre os tempos reais da voz (roteiros/voz-transito/tempos.json).
Cada plano tem a vista, a âncora da câmera (o ponto da freada, a fila ou a cauda), uma onda suave de câmera (início -> fim) e o mapa de tempo filme -> simulação
(câmera lenta de ~0,45x logo depois da freada, depois mais rápido), tudo na MESMA simulação.
    blender -b -P kit3d/tb_story_ep1.py -- lista
    blender -b -P kit3d/tb_story_ep1.py -- quadros PASTA [--escala 0.5] [--planos 1,2,3] [--u 0,0.5,1] [--especial]
(--especial renderiza os planos 10 e 11 (cena do espaço), que usam a pista ainda livre.)"""
import sys, os, math, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from mathutils import Vector
import tb_assets as A
import tb_cena as C
import tb_mapa as MP
import tb_trafego as T
import tb_camera_suave as CS

RAIZ = os.environ.get("TRANSITO3D_PROJETO") or os.getcwd()
argv = sys.argv[sys.argv.index("--") + 1:]
modo = argv[0]
op = lambda k, d: argv[argv.index(k) + 1] if k in argv else d
FPS = 24
NOME = "Marginal Pinheiros (Expressa)"
Y0 = float(op("--y", "800"))   # trecho reto e longe de viadutos: a fila anda 300 m para trás sem encontrar a Estaiada
MIX = {"expressa": [("hatch", 34), ("sedan", 28), ("suv", 22), ("picape", 6), ("taxi", 4), ("vuc", 3)],
       "avenida": [("hatch", 40), ("sedan", 30), ("suv", 20)], "rua": [("hatch", 50), ("sedan", 50)], "corredor": [("moto", 50), ("moto_entrega", 50)]}

from story_ep1_planos import *

if modo == "lista":
    for pid, fala, vista, anc, o0, o1, d0, d1, e0, e1, a0, a1, leg in PLANOS:
        t0, t1 = FALA_T[fala - 1]
        print(f"{pid:2d} fala {fala:2d} {t0:5.1f}-{t1:5.1f}s ({t1 - t0:3.1f}s) {vista:11s} âncora {anc:6s} sim {sim_de(t0):5.1f}->{sim_de(t1):5.1f}s")
    sys.exit(0)

# ---------------------------------------------------------------- mundo
C.limpa()
mp = MP.Mapa(os.path.join(RAIZ, "transito", "dados_osm", "estaiada.json"), "didatico")
best = None
for v in mp.d["vias"]:
    if v["nome"] == NOME and v["faixas"] >= 4:
        for p in v["pts"]:
            if best is None or abs(p[1] - Y0) < abs(best[1] - Y0):
                best = p
cx, cy = best[0], best[1]
regiao = (cx, cy, 520)
mp.foco_ids = mp.pista_de((cx, cy), NOME)
mp.monta(regiao, foco=(cx, cy, 480), nomes=[NOME])


def monta_trafego(visual):
    T.Veic._n = 0     # os ids dos carros são os mesmos nas duas montagens
    tr = T.Trafego(mp, regiao, fluxo=1.0, escala_veic=1.12, visual=visual, cor="velocidade", dens=0.9, enche=False, folga=2.6, tempo=1.0, mix=MIX)
    lane, s_c = tr.faixa_perto((cx, cy), NOME)
    lane.dens = 2.1
    tr.enche(); tr.grava = lane
    tr.aquece(60); tr.xt = []; tr.t = 0.0
    return tr, lane, s_c


# pré-passagem sem objetos: qual carro freia e onde ele está quando começa a frear
tr0, lane0, s_c0 = monta_trafego(False)
while tr0.t < TE - 0.03:
    tr0.passo(1 / FPS)
cand = [v for v in lane0.veics if v.modelo in ("hatch", "sedan", "suv")]
vit0 = min(cand, key=lambda v: abs(v.s - s_c0))
ID_VIT, S_E = vit0.id, vit0.s
del tr0, lane0, vit0
tr, lane, s_c = monta_trafego(modo != "sim")
print(f"[story] pista: {lane.L:.0f} m, s_c {s_c:.0f}, carro do evento id {ID_VIT} (s={S_E:.0f} m em {TE}s); ids no início: {min(v.id for v in lane.veics)}..{max(v.id for v in lane.veics)}")
vit = None


def liga_evento():
    """o carro que freia pode nascer depois do começo (entra na pista): assim que existe, ganha o evento"""
    global vit
    if vit is None:
        achou = [v for v in lane.veics if v.id == ID_VIT]
        if achou:
            vit = achou[0]; vit.evento = (TE, TE + DUR_FREADA, 0.0, DEC)


liga_evento()
p_a, yaw, _ = lane.pose(S_E)
ys = [lane.pose(S_E + d)[1] for d in range(-200, 40, 20)]
AZ0 = math.degrees(math.atan2(sum(math.sin(y) for y in ys), sum(math.cos(y) for y in ys))) - 90
E = MP.ESTILOS["didatico"]
C.motor(True, 40, 1080, 1350, float(op("--escala", "0.5")))
C.mundo(E["mundo"], E["mundo_forca"]); C.sol(40, AZ0 - 55, E["sol"], E["sol_cor"], 3.0)
cam = C.camera(Vector((p_a.x, p_a.y, 0)), 70, 50, AZ0, 45)
anel = A.anel(4.2, "#ffd21f", 0.5, pos=(0, 0, 0.5))
print(f"[story] carro que freia id {ID_VIT}, ponto da freada s={S_E:.0f} m, azimute {AZ0:.1f}°")


def lentos():
    return [v for v in lane.veics if v.v < 0.30 * lane.vmax * T.VEL_VERDE]


def ancora(nome):
    if nome == "ponto":
        return S_E
    if nome == "vit":
        return vit.s if vit is not None else S_E
    ls = lentos()
    if not ls:
        return S_E
    if nome == "fila":
        return (min(v.s for v in ls) + max(v.s for v in ls)) / 2
    if nome == "cauda":
        return min(v.s for v in ls)
    if nome == "cabeca":
        return max(v.s for v in ls)
    return S_E


def anda_sim(t_sim):
    while tr.t < t_sim - 1e-6:
        tr.passo(1 / FPS); liga_evento()


def poe(vista, s_centro, dist, elev, azim):
    p = lane.ponto(s_centro)
    if vista == "topo":
        cam.data.type = "ORTHO"; cam.data.ortho_scale = dist; cam.data.clip_start = 20; cam.data.clip_end = 400
        cam.location = (p.x, p.y, 150.0); cam.rotation_euler = (0, 0, math.radians(AZ0))
    else:
        cam.data.type = "PERSP"; cam.data.lens = LENTE[vista]; cam.data.clip_start = 8; cam.data.clip_end = 900
        C.poe_camera(cam, Vector((p.x, p.y, 0)), dist, elev, AZ0 + azim)


ESPECIAL = "--especial" in argv   # planos 10 e 11: cena do espaço, na pista ainda livre (6 a 13 s da simulação)
EXTRAS = []


def par_proximo(ref):
    """(A, B): o carro da frente e o que vem logo atrás, os mais perto da referência"""
    vs = sorted(lane.veics, key=lambda v: v.s)
    i = min(range(1, len(vs)), key=lambda i: abs(vs[i].s - ref))
    return vs[i], vs[i - 1]


def cena_espaco(pid):
    A_, B_ = par_proximo(S_E)
    gap = A_.s - A_.L / 2 - (B_.s + B_.L / 2)
    seg = gap / max(B_.v, 1.0)
    if pid == 10:   # aro no carro de trás: o vão até o da frente
        EXTRAS.append(A.anel(3.6, "#22c55e", 0.4, pos=(0, 0, 0.5)))
        pb = lane.pose(B_.s)[0]; EXTRAS[-1].location = (pb.x, pb.y, 0.5)
    else:           # poste ao lado da pista e régua de 2 segundos atrás do carro da frente
        pa, ya, _ = lane.pose(A_.s)
        nx, ny = -math.sin(ya), math.cos(ya)
        EXTRAS.append(A.poste((pa.x + nx * 7.5, pa.y + ny * 7.5, 0)))
        EXTRAS.extend(A.regua_tempo((pa.x - math.cos(ya) * (A_.L / 2 + 0.4), pa.y - math.sin(ya) * (A_.L / 2 + 0.4)), ya, max(A_.v, 8.0), 2.0, 2.6, pa.z + 0.5))
    return seg, gap


def renderiza(pid, u, saida):
    pl = [p for p in PLANOS if p[0] == pid][0]
    _, fala, vista, anc, o0, o1, d0, d1, e0, e1, a0, a1, leg = pl
    t0, t1 = FALA_T[fala - 1]
    film = t0 + (t1 - t0) * u
    anda_sim(6.0 + (film - t0) if (pid in (10, 11) and ESPECIAL) else sim_de(film))
    k = CS.sstep5(u)
    mix = lambda a, b: a + (b - a) * k
    s_centro = ancora(anc) + mix(o0, o1)
    poe(vista, s_centro, mix(d0, d1), mix(e0, e1), mix(a0, a1))
    tr.aplica()
    vis = 9.0 <= film <= 36.0 and vit is not None
    anel.hide_render = not (vis and vit.obj is not None)
    if vis and vit.obj is not None:
        anel.location = vit.obj.location + Vector((0, 0, 0.6))
    if pid in (10, 11) and ESPECIAL:
        seg_, gap_ = cena_espaco(pid)
        print(f"   vão entre os dois carros: {gap_:.1f} m = {seg_:.1f} s")
    bpy.context.view_layer.update()
    C.render(saida)
    for o in EXTRAS:
        bpy.data.objects.remove(o)
    EXTRAS.clear()
    return film, tr.t


if modo == "quadros":
    pasta = argv[1]; os.makedirs(pasta, exist_ok=True)
    quais = [int(x) for x in op("--planos", "1,2,3,4,5,6,7,8,9,12,13").split(",")]
    us = [float(x) for x in op("--u", "0,0.5,1").split(",")]
    info = {}
    for pid in quais:
        fala = [p for p in PLANOS if p[0] == pid][0][1]
        for u in us:
            film, simt = renderiza(pid, u, os.path.join(pasta, f"p{pid:02d}_u{int(u * 100):03d}.png"))
            info[f"p{pid:02d}_u{int(u * 100):03d}"] = dict(plano=pid, fala=fala, film=round(film, 2), sim=round(simt, 2), n_lentos=len(lentos()))
            print(f"plano {pid:2d} u={u:.1f}  filme {film:5.1f}s  sim {simt:5.1f}s  carros lentos {len(lentos()):2d}")
    json.dump(info, open(os.path.join(pasta, f"info_{'_'.join(map(str, quais))}.json"), "w"), indent=1)
