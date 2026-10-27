"""Trânsito Brasil 3D, ep. 1: ficha de elenco e objetos no visual didático (mapa claro, pista escura, carros brilhantes).
    blender -b -P kit3d/tb_ficha_ep1.py -- saida_prefixo [--escala 1.0]
Gera <prefixo>-tipo.png (veículos por tipo e por velocidade), <prefixo>-objetos.png (aro, poste, régua dos 2 segundos, legendas) e <prefixo>-topo.png (os mesmos, de cima reto)."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from mathutils import Vector
import tb_assets as A
import tb_cena as C
import tb_mapa as MP
import tb_trafego as T

argv = sys.argv[sys.argv.index("--") + 1:]
pref = argv[0]; esc = float(argv[argv.index("--escala") + 1]) if "--escala" in argv else 1.0
E = MP.ESTILOS["didatico"]
C.limpa(); C.motor(True, 48, 1920, 1080, esc); C.mundo(E["mundo"], 1.0); C.sol(42, -50, E["sol"], E["sol_cor"], 3.0)
A.fita([(-120, 0), (520, 0)], 400, A.mat_cor(E["chao"], 0.95, nome="tb_chao_f"), -0.2, "chao")
asf = A.mat_cor(E["asf1"], 0.82, nome="tb_asf_f"); tinta = A.mat_cor("#ffffff", 0.5, nome="tb_tinta_f")
def pista(x0, x1, y):
    A.fita([(x0, y), (x1, y)], 9.0, asf, 0.0, "pista")
    for s_ in (-1, 1):
        A.fita([(x0, y + s_ * 4.2), (x1, y + s_ * 4.2)], 0.2, tinta, 0.02, "borda")
ESC = 1.12
def carro(mod, x, y, cor, cor2="#c9ccd1", escala=ESC, **prop):
    o = A.veiculo(mod, cor, cor2, escala=T.esc_de(mod, escala)); o.location = (x, y, 0.02)
    for k, v in prop.items(): o[k] = v
    return o
def rot(t, x, y, tam=1.4, **k): return A.rotulo(t, (x, y, 0.08), tam, **k)

# --- quadro 1: elenco. faixa de cima = por TIPO; faixa de baixo = por VELOCIDADE
pista(-90, 90, 8); pista(-90, 90, -8)
tipos = [("hatch", "carro", T.COR_TIPO["carro"]), ("taxi", "táxi", T.COR_TIPO["taxi"]), ("onibus", "ônibus", T.COR_TIPO["onibus"]),
         ("vuc", "caminhão", T.COR_TIPO["caminhao"]), ("moto", "moto", T.COR_TIPO["moto"]), ("ambulancia", "emergência", T.COR_TIPO["emergencia"])]
x = -44
for mod, nome, (c, c2) in tipos:
    L = A.COMPRIMENTO[mod] * T.esc_de(mod, ESC); x += L / 2
    carro(mod, x, 8, c, c2); rot(nome.upper(), x, 8 + 6.6)
    x += L / 2 + 5.5
x = -32
for r, nome in ((1.0, "ANDANDO BEM"), (0.7, ""), (0.45, "DEVAGAR"), (0.2, ""), (0.0, "PARADO")):
    carro("sedan", x, -8, "#ffffff", freio=1.0 if r < 0.3 else 0.0).color = T.cor_velocidade(r)
    if nome: rot(nome, x, -8 - 6.6)
    x += 16
# --- quadro 2: objetos da cena, a leste (x = 300)
X = 300
pista(X - 90, X + 90, 0)
c1 = carro("sedan", X - 38, 0, "#16b85b"); c1.color = T.cor_velocidade(1.0)
A.anel(4.2, "#ffd21f", 0.5, pos=(X - 38, 0, 0.5)); rot("ARO NO CARRO QUE FREIA", X - 38, -6.6)
A.poste((X - 12, 6.6, 0)); rot("POSTE", X - 12, 10.2)
vms = 14.0
cA = carro("sedan", X + 22, 0, "#16b85b"); cA.color = T.cor_velocidade(1.0)
cB = carro("sedan", X + 22 - vms * 1.0 - 6, 0, "#ffc21a"); cB.color = T.cor_velocidade(0.45)    # perto demais: dentro da régua
A.regua_tempo((X + 22 - 2.6, 0), 0.0, vms, 2.0, 2.4, 0.03)
rot("RÉGUA DE 2 SEGUNDOS", X + 22 - vms - 2.6, -6.6)
A.rotulo("1 motorista freia", (X - 20, 14, 0.1), 2.0, yaw=0.0)
A.rotulo("a fila cresce para trás", (X + 14, 14, 0.1), 2.0, yaw=0.0)

def render(nome, alvo, dist, elev, azim, lente):
    cam = C.camera(alvo, dist, elev, azim, lente); C.render(f"{pref}-{nome}.png"); bpy.data.objects.remove(cam)
render("tipo", (-3, -1, 0), 104, 58, 0, 40)
render("objetos", (X - 12, 3, 0), 96, 58, 0, 40)
cam = C.camera((X - 12, 3, 0), 150, 90, 0, 40); cam.data.type = "ORTHO"; cam.data.ortho_scale = 96; cam.location = (X - 12, 3, 150); cam.rotation_euler = (0, 0, 0)
C.render(f"{pref}-topo.png")
