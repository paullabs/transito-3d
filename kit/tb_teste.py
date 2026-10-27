"""Trânsito Brasil 3D: testes de estilo do mapa.
    blender -b -P kit3d/tb_teste.py -- planta  saida.png              (vista de cima ortográfica do recorte inteiro, para achar as coisas)
    blender -b -P kit3d/tb_teste.py -- quadro  saida.png --estilo maquete|noite|real --plano medio|aberto|perto [--escala 0.5]
    blender -b -P kit3d/tb_teste.py -- anim    PASTA     --estilo maquete --plano medio [--segundos 8] [--escala 0.5]"""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
import tb_assets as A
import tb_cena as C
import tb_mapa as MP

RAIZ = os.environ.get("TRANSITO3D_PROJETO") or os.getcwd()
DADOS = os.path.join(RAIZ, "transito", "dados_osm", "estaiada.json")
argv = sys.argv[sys.argv.index("--") + 1:]
modo, saida = argv[0], argv[1]
op = lambda k, d: argv[argv.index(k) + 1] if k in argv else d
estilo = op("--estilo", "maquete"); plano = op("--plano", "medio"); esc = float(op("--escala", "1.0"))

C.limpa()
if modo == "planta":
    C.motor(True, 16, 2000, 2000, esc)
    E = MP.ESTILOS["maquete"]
    C.mundo(E["mundo"], 1.0); C.sol(70, -30, 3.5)
    mp = MP.Mapa(DADOS, "maquete").monta(faixas_pintadas=False)
    cam = C.camera((0, 0, 0), 3000, 90, 0, 50)
    cam.data.type = "ORTHO"; cam.data.ortho_scale = 2400
    cam.rotation_euler = (0, 0, 0)
    # grade de 200 m com números para localizar
    for x in range(-1000, 1001, 200):
        A.fita([(x, -1200), (x, 1200)], 1.5, A.mat_cor("#ff3b30", 0.5, emis=1, nome="tb_grade"), 200, "grade")
        A.rotulo(str(x), (x, -1120, 201), 18)
    for y in range(-1000, 1001, 200):
        A.fita([(-1200, y), (1200, y)], 1.5, A.mat_cor("#ff3b30", 0.5, emis=1, nome="tb_grade"), 200, "grade")
        A.rotulo(str(y), (-1110, y, 201), 18)
    print("torre estaiada em", tuple(round(k) for k in mp.torre))
    C.render(saida)
    sys.exit(0)

import tb_trafego as T
from mathutils import Vector


def ponto_via(mp, nome, y):
    """ponto da via (pelo nome) mais perto da linha y"""
    best = None
    for v in mp.d["vias"]:
        if nome in v["nome"]:
            for p in v["pts"]:
                if best is None or abs(p[1] - y) < abs(best[1] - y):
                    best = p
    return best


E = MP.ESTILOS[estilo]
w, h = 1080, 1920
C.motor(True, 32 if modo == "quadro" else 16, w, h, esc)
C.mundo(E["mundo"], E["mundo_forca"], E["ceu"])
C.sol(48 if estilo != "noite" else 60, -60, E["sol"], E["sol_cor"], 2.0)
mp0 = MP.Mapa(DADOS, estilo)
mx, my = ponto_via(mp0, "Marginal Pinheiros (Expressa)", -120)[:2]
PLANOS = {  # alvo, distância, elevação, azimute, lente, raio da região montada
    "aberto": ((-420, -60, 0), 2700, 62, -18, 35, 1500),
    "medio": ((-735, -300, 0), 640, 46, -18, 35, 520),
    "perto": ((mx, my, 0), 150, 52, -18, 35, 160),
}
alvo, dist, elev, azim, lente, raio = PLANOS[plano]
regiao = (alvo[0], alvo[1], raio)
PRINCIPAIS = ["Marginal Pinheiros (Expressa)", "Marginal Pinheiros (Local)", "Avenida Jornalista Roberto Marinho",
              "Avenida Engenheiro Luís Carlos Berrini", "Avenida das Nações Unidas", "Avenida dos Bandeirantes", "Ponte do Morumbi"]
mp = mp0.monta(regiao, foco=regiao if estilo == "didatico" else None, nomes=PRINCIPAIS if estilo == "didatico" and plano != "perto" else None)
cam = C.camera(alvo, dist, elev, azim, lente)
print("largura vista (m):", round(C.largura_vista(dist, lente)))

tr = T.Trafego(mp, regiao, fluxo=1.0, escala_veic={"aberto": 2.2, "medio": 2.0, "perto": 1.25}[plano], cor=op("--cor", "tipo"), dens=1.3)
if modo == "anim":
    gx, gy = ponto_via(mp0, "Marginal Pinheiros (Expressa)", alvo[1] + 70)[:2]
    tr.gargalo_ponto((gx, gy), 35, 6, 1.0, 4.5)
if plano == "aberto":  # hora do rush: dois gargalos fixos na Marginal para aparecer o vermelho
    for yy in (-380, 420):
        gx, gy = ponto_via(mp0, "Marginal Pinheiros (Expressa)", yy)[:2]
        tr.gargalo_ponto((gx, gy), 80, 12, -1, 1e9, raio=60)
tr.aquece(150 if plano != "aberto" else 260)
tr.aplica()
print("veículos:", tr.contagem())
if estilo == "noite":
    A.brilho_luzes(8.0, 3.0, 10.0)
if "--cores" in argv or plano == "aberto":
    tr.mapa_de_cor(40.0 if plano == "aberto" else 20.0, 0.8, 14.0 if plano == "aberto" else 2.6)
    for o in bpy.data.collections["veiculos"].objects:
        o.hide_render = plano == "aberto"

# rótulos de identificação, em pé, virados para a câmera
def etiqueta(t, x, y, z, tam):
    r = A.rotulo(t, (x, y, z), tam)
    r.rotation_euler = (math.radians(90 - elev), 0, math.radians(azim))
    return r

tam = {"aberto": 34, "medio": 9, "perto": 2.6}[plano]
if plano in ("aberto", "medio"):
    tx, ty = mp.torre.x, mp.torre.y
    etiqueta("PONTE ESTAIADA", tx + (95 if plano == "medio" else 300), ty, 120 if plano == "medio" else 190, tam)
    p = ponto_via(mp, "Marginal Pinheiros (Expressa)", ty + (230 if plano == "medio" else 700))
    etiqueta("MARGINAL PINHEIROS", p[0] + 20, p[1], 25, tam)
    if plano == "aberto":
        p = ponto_via(mp, "Berrini", 150); etiqueta("AV. BERRINI", p[0], p[1], 60, tam)
        p = ponto_via(mp, "Bandeirantes", -900); etiqueta("AV. DOS BANDEIRANTES", p[0], p[1], 60, tam)
        p = ponto_via(mp, "Roberto Marinho", -420); etiqueta("AV. ROBERTO MARINHO", p[0] + 250, p[1] - 60, 60, tam)
else:
    etiqueta("PISTA EXPRESSA  70 km/h", mx + 4, my + 40, 6, tam)

if modo == "quadro":
    C.render(saida)
else:
    os.makedirs(saida, exist_ok=True)
    seg = float(op("--segundos", "8"))
    i_parte, n_partes = (int(x) for x in op("--parte", "0/1").split("/"))
    for f in range(int(seg * 24)):
        k = f / (seg * 24 - 1)
        s = k * k * (3 - 2 * k)
        C.poe_camera(cam, Vector(alvo) + Vector((0, 25 * s, 0)), dist * (1 - 0.12 * s), elev + 4 * s, azim + 6 * s)
        tr.passo(1 / 24); tr.aplica()
        if f % n_partes != i_parte:
            continue
        bpy.context.scene.frame_set(f + 1)
        C.render(os.path.join(saida, f"{f + 1:04d}.png"))
