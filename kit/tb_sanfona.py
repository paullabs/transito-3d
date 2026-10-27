"""Trânsito Brasil 3D: cena didática do EFEITO SANFONA na Marginal Pinheiros (expressa).
Um motorista freia; os de trás freiam mais, e a freada vira uma onda vermelha que anda PARA TRÁS, mesmo sem obstáculo.
    blender -b -P kit3d/tb_sanfona.py -- sim      PASTA_SAIDA         (só a simulação: diagrama espaço-tempo + números)
    blender -b -P kit3d/tb_sanfona.py -- quadro   saida.png [--t 6.0] (um quadro no instante t)
    blender -b -P kit3d/tb_sanfona.py -- anim     PASTA [--parte i/n] (todos os quadros)
Opções: --escala 0.5  --segundos 12  --cor tipo|velocidade  --camera tras|alto"""
import sys, os, math
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
modo, saida = argv[0], argv[1]
op = lambda k, d: argv[argv.index(k) + 1] if k in argv else d
esc = float(op("--escala", "1.0")); seg = float(op("--segundos", "12")); cor_modo = op("--cor", "velocidade")
NOME = "Marginal Pinheiros (Expressa)"
FPS = 24
T_FREADA = float(op("--t-freada", "1.5"))  # s em que o motorista freia
ESC_VEIC = float(op("--esc-veic", "1.12"))   # carros só um pouco maiores que o real: sobra vão dos lados
MIX = {"expressa": [("hatch", 34), ("sedan", 28), ("suv", 22), ("picape", 6), ("taxi", 4), ("vuc", 3)],   # sem carreta nem ônibus: cada um é um carro e cabe no olho
       "avenida": [("hatch", 40), ("sedan", 30), ("suv", 20)], "rua": [("hatch", 50), ("sedan", 50)], "corredor": [("moto", 50), ("moto_entrega", 50)]}

C.limpa()
mp = MP.Mapa(os.path.join(RAIZ, "transito", "dados_osm", "estaiada.json"), "didatico")
# ponto da Marginal expressa onde a pista é reta e larga
best = None
for v in mp.d["vias"]:
    if v["nome"] == NOME and v["faixas"] >= 4:
        for p in v["pts"]:
            if best is None or abs(p[1] - (-120)) < abs(best[1] - (-120)):
                best = p
cx, cy = best[0], best[1]
regiao = (cx, cy, 380)
mp.foco_ids = mp.pista_de((cx, cy), NOME)   # só UM sentido da Marginal em destaque; o outro fica apagado
mp.monta(regiao, foco=(cx, cy, 330), nomes=[NOME])
def monta_trafego(visual):
    tr = T.Trafego(mp, regiao, fluxo=1.0, escala_veic=ESC_VEIC, visual=visual, cor=cor_modo, dens=float(op("--dens-vizinhas", "0.9")), enche=False,
                   folga=float(op("--folga", "2.6")), tempo=float(op("--tempo", "1.0")), mix=MIX, reacao=float(op("--reacao", "0.0")))
    lane, s_c = tr.faixa_perto((cx, cy), NOME)
    lane.dens = float(op("--dens", "2.1"))  # só a faixa do foco fica cheia; as vizinhas andam soltas
    tr.enche()
    tr.grava = lane
    tr.aquece(60)
    tr.xt = []; tr.t = 0.0
    amort = int(op("--amortecedor", "0"))   # 0 = nada; K = o K-ésimo carro atrás do que freia deixa mais espaço (some o carro da frente dele)
    if amort:
        cand = [ve for ve in lane.veics if ve.modelo in ("hatch", "sedan", "suv")]
        base = min(range(len(lane.veics)), key=lambda i: abs(lane.veics[i].s - s_c))     # o que vai frear
        alvo = lane.veics[base + amort]
        if amort > 1 and float(op("--amortecedor-remove", "1")) > 0:
            frente = lane.veics[base + amort - 1]; lane.veics.remove(frente)               # abre o vão: o motorista "deixou espaço"
        alvo.T = float(op("--amortecedor-T", "1.0")) * alvo.T
        globals()["AMORT"] = alvo
    vit = tr.freada(lane, s_c, T_FREADA, dur=float(op("--freada-dur", "2.5")), v_kmh=float(op("--freada-v", "0")), dec=float(op("--freada-dec", "6.0")))
    return tr, lane, s_c, vit


H = None
if modo != "sim":
    # pré-passagem sem objetos (a simulação é idêntica): onde o carro que freia PARA. A câmera é planejada em volta desse ponto fixo.
    tr0, lane0, s_c0, vit0 = monta_trafego(False)
    while tr0.t < 6.0:
        tr0.passo(1 / FPS)
    H = vit0.s
    del tr0, lane0, vit0
tr, lane, s_c, vit = monta_trafego(visual=(modo != "sim"))
print(f"[sanfona] faixa {lane.nome}, {len(lane.veics)} carros nela; o que freia é um {vit.modelo if vit else None}" + (f"; para em s={H:.0f} m (ponto de partida s={s_c:.0f})" if H else ""))
if modo == "sim":
    os.makedirs(saida, exist_ok=True)
    vs = lane.veics; gaps = [vs[i].s - vs[i].L / 2 - (vs[i + 1].s + vs[i + 1].L / 2) for i in range(len(vs) - 1)]
    print(f"[sanfona] vão médio entre carros na pista em foco: {sum(gaps) / len(gaps):.1f} m (mínimo {min(gaps):.1f} m); carro tem ~{sum(v.L for v in vs) / len(vs):.1f} m")
    pares = set()
    for k in range(int(seg * FPS)):
        tr.passo(1 / FPS)
        pares |= set(tr.sobreposicoes())
    print(f"[sanfona] carros que se atravessaram em {seg:.0f} s: {len(pares)}")
    tr.diagrama_xt(os.path.join(saida, "xt.png"), "Cada linha é um carro", marca=(T_FREADA + 0.2, s_c, "1 carro freia"),
                   tam=[10.0, 3.7], dpi=108, xlim=[0, 12], ylim=[s_c - 250, s_c + 110], margens=dict(left=0.095, right=0.985, bottom=0.2, top=0.84),
                   fundo="#f3f1ec")
    # fila: o menor v em cada instante, e até onde a onda andou
    # a freada de cada carro ao longo do tempo: quem freia primeiro, e o quanto cada um de trás freia (a amplificação)
    ids = [i for i, _, _ in tr.xt[0][1]]
    minimo = {}
    for t, lst in tr.xt:
        for i, ss, vv in lst:
            minimo[i] = min(minimo.get(i, 99.0), vv * 3.6)
    ordem = sorted(ids, key=lambda i: -dict((a, b) for a, b, _ in tr.xt[0][1])[i])
    base = [i for i in ordem if abs(dict((a, b) for a, b, _ in tr.xt[0][1])[i] - s_c) < 400]
    freado = [(round(minimo[i])) for i in ordem[: len(ordem)] if i in minimo]
    print("[sanfona] velocidade MÍNIMA (km/h) de cada carro, do da frente para o de trás:", [minimo[i].__round__() for i in ordem if i in minimo][:40])
    for t, lst in tr.xt[::48]:
        lentos = [(s, v) for _, s, v in lst if v < 0.35 * lane.vmax]
        print(f"t={t:5.1f}s  carros parados/lentos: {len(lentos):2d}  trecho: " + (f"{min(s for s,_ in lentos):.0f}..{max(s for s,_ in lentos):.0f} m" if lentos else "-"))
    sys.exit(0)

E = MP.ESTILOS["didatico"]
C.motor(True, 40, 1080, 1350, esc)
C.mundo(E["mundo"], E["mundo_forca"]); 
# direção da pista no ponto: a câmera olha NO sentido do fluxo, por trás e por cima
p_a, yaw, _ = lane.pose(s_c)
az = math.degrees(yaw) - 90          # azimute da câmera (0 = olha para +y)
centro = Vector((p_a.x, p_a.y, 0)) + Vector((math.cos(yaw), math.sin(yaw), 0)) * 28
C.sol(40, math.degrees(yaw) - 90 - 55, E["sol"], E["sol_cor"], 3.0)
elev = 50
dist = float(op("--dist", "75")); elev = float(op("--elev", "44"))
VISTA_NOME = op("--vista", "perspectiva")
# Vistas de câmera. Metros relativos a H (onde o carro que freia PARA). "dist" é a distância da câmera; no topo plano é a ALTURA VISÍVEL em metros (ortográfica).
# Todas seguem a mesma regra: uma onda suave só (tb_camera_suave), começando e terminando em repouso.
VISTAS = {
    "perspectiva": dict(tipo="persp", lente=45, cs=[(0, -8, 0.0), (12, -35, 0.0)], dist=[(0, 62.0, 0.0), (12, 99.0, 0.0)],
                        elev=[(0, 50.0, 0.0), (12, 58.0, 0.0)], azim=[(0, 0.0, 0.0), (12, 7.0, 0.0)]),
    "topo": dict(tipo="topo", lente=45, cs=[(0, -3, 0.0), (12, -34, 0.0)], dist=[(0, 56.0, 0.0), (12, 88.0, 0.0)],
                 elev=[(0, 90.0, 0.0), (12, 90.0, 0.0)], azim=[(0, 0.0, 0.0), (12, 0.0, 0.0)]),
    "baixa": dict(tipo="persp", lente=35, cs=[(0, -18, 0.0), (12, -44, 0.0)], dist=[(0, 38.0, 0.0), (12, 66.0, 0.0)],
                  elev=[(0, 15.0, 0.0), (12, 25.0, 0.0)], azim=[(0, 0.0, 0.0), (12, 12.0, 0.0)]),
    "diagonal": dict(tipo="persp", lente=45, cs=[(0, -8, 0.0), (12, -34, 0.0)], dist=[(0, 70.0, 0.0), (12, 112.0, 0.0)],
                     elev=[(0, 38.0, 0.0), (12, 46.0, 0.0)], azim=[(0, 38.0, 0.0), (12, 26.0, 0.0)]),
}
VISTA = VISTAS[VISTA_NOME]
LENTE = float(op("--lente", str(VISTA["lente"])))
# --- CÂMERA PLANEJADA: ondas suaves encadeadas (tb_camera_suave). Metros relativos a H, o ponto onde o carro que freia para.
#   centro: desliza devagar PARA TRÁS, junto com a fila (vai de H-8 a H-40, sem parar no meio)
#   distância: onda 1 = chega perto do freio (66 -> 60); onda 2 = abre devagar para a fila inteira caber (60 -> 90); a virada em 3 s é suave
#   elevação e azimute: giram bem pouco, só para dar paralaxe e mostrar a profundidade da fila
K = seg / 12.0
SIGMA = float(op("--suave", "0.55"))   # s; tira o degrau de aceleração nas emendas das ondas
CAMINHO = {nome: CS.serie_suave(CS.escala_tempo([(c[0], (c[1] + H) if nome == "cs" else c[1], c[2]) for c in VISTA[nome]], K), FPS, seg, SIGMA)
           for nome in ("cs", "dist", "elev", "azim")} if H is not None else None
CAM = {"cs": 0.0, "dist": 0.0, "elev": 0.0}
if CAMINHO:
    # o centro segue a pista, mas o traçado do OSM tem pequenas dobras: o caminho no chão é filtrado e o azimute é UMA direção só (a média do trecho),
    # senão a cada vértice a câmera dá um tranco de alguns metros
    n_q = len(CAMINHO["cs"])
    _pts = [lane.ponto(CAMINHO["cs"][i]) for i in range(n_q)]
    CAMINHO["x"] = CS.filtra([p.x for p in _pts], FPS, SIGMA); CAMINHO["y"] = CS.filtra([p.y for p in _pts], FPS, SIGMA)
    _ys = [lane.pose(CAMINHO["cs"][i])[1] for i in range(0, n_q, 6)]
    AZ0 = math.degrees(math.atan2(sum(math.sin(y) for y in _ys), sum(math.cos(y) for y in _ys))) - 90
    print(f"[sanfona] azimute fixo {AZ0:.1f}°; o traçado muda de direção até {math.degrees(max(abs(y - math.radians(AZ0 + 90)) for y in _ys)):.1f}° no trecho filmado")


def atualiza_camera(t):
    i = min(max(int(round(t * FPS)), 0), len(CAMINHO["cs"]) - 1)
    for k in ("cs", "dist", "elev"):
        CAM[k] = CAMINHO[k][i]
    az = CAMINHO["azim"][i]
    if VISTA["tipo"] == "topo":   # de cima reto, ortográfica: a imagem tem o sentido do fluxo para cima; "dist" = altura visível em metros
        cam.data.ortho_scale = CAM["dist"]
        cam.location = (CAMINHO["x"][i], CAMINHO["y"][i], 150.0)
        cam.rotation_euler = (0.0, 0.0, math.radians(AZ0))
    else:
        C.poe_camera(cam, Vector((CAMINHO["x"][i], CAMINHO["y"][i], 0)), CAM["dist"], CAM["elev"], AZ0 + az)


cam = C.camera(Vector((0, 0, 0)), 70, 50, 0, LENTE)
if VISTA["tipo"] == "topo":
    cam.data.type = "ORTHO"; cam.data.clip_start = 20.0; cam.data.clip_end = 400.0
else:
    cam.data.clip_start = 8.0; cam.data.clip_end = 900.0   # a câmera nunca fica a menos de ~40 m de nada; camadas de 2 cm ficam estáveis
if CAMINHO:
    atualiza_camera(0.0)
print(f"[sanfona] vista \"{VISTA_NOME}\" ({VISTA['tipo']}), lente {LENTE} mm")
# marcador no carro que freia
anel = A.anel(4.2, "#ffd21f", 0.5, pos=(0, 0, 0.5))

from bpy_extras.object_utils import world_to_camera_view
POS = {}


def na_tela(co):
    p = world_to_camera_view(bpy.context.scene, cam, co)
    return [round(p.x, 4), round(1 - p.y, 4)]


def passo_cena(t_alvo):
    while tr.t < t_alvo - 1e-6:
        tr.passo(1 / FPS)
    atualiza_camera(t_alvo)
    bpy.context.view_layer.update()
    tr.aplica()
    if vit and vit.obj is not None:
        anel.location = vit.obj.location + Vector((0, 0, 0.6)); anel.hide_render = not (T_FREADA - 0.6 <= tr.t <= T_FREADA + 5)
    d = {}
    if vit and vit.obj is not None:
        d["freio"] = na_tela(vit.obj.location + Vector((0, 0, 1.5)))
    lentos = [ve for ve in lane.veics if ve.v < 0.30 * lane.vmax * T.VEL_VERDE and ve.obj is not None]
    if lentos and tr.t > 3.0:
        ult = min(lentos, key=lambda v: v.s)  # o de trás: ponta da fila
        d["cauda"] = na_tela(ult.obj.location + Vector((0, 0, 1.5)))
        d["n_parados"] = len(lentos)
    POS[round(tr.t * FPS)] = d

if modo == "camlog":   # só a câmera, sem renderizar: grava a posição de cada quadro para medir tranco, aceleração e jerk
    import json
    log = []
    for f in range(int(seg * FPS)):
        passo_cena(f / FPS)
        m = cam.matrix_world.translation
        log.append({"f": f, "cs": CAM["cs"], "dist": CAM["dist"], "elev": CAM["elev"], "x": m.x, "y": m.y, "z": m.z, "pos": POS.get(f, {})})
    os.makedirs(saida, exist_ok=True)
    json.dump({"fps": FPS, "log": log}, open(os.path.join(saida, "camera.json"), "w"))
    sys.exit(0)

if modo == "quadro":
    alvo_t = float(op("--t", "6.0"))
    for f in range(int(alvo_t * FPS) + 1):
        passo_cena(f / FPS)
    C.render(saida)
else:
    os.makedirs(saida, exist_ok=True)
    i_parte, n_partes = (int(x) for x in op("--parte", "0/1").split("/"))
    for f in range(int(seg * FPS)):
        passo_cena(f / FPS)
        if f % n_partes != i_parte:
            continue
        bpy.context.scene.frame_set(f + 1)
        C.render(os.path.join(saida, f"{f + 1:04d}.png"))
    import json
    json.dump(POS, open(os.path.join(saida, f"pos_{i_parte}.json"), "w"))
    if i_parte == 0:
        tr.diagrama_xt(os.path.join(saida, "xt.png"), "Cada linha é um carro", marca=(T_FREADA + 0.2, s_c, "1 carro freia"),
                       tam=[10.0, 3.7], dpi=108, xlim=[0, 12], ylim=[s_c - 250, s_c + 110],
                       margens=dict(left=0.095, right=0.985, bottom=0.2, top=0.84), fundo="#f3f1ec")
