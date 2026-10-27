"""Trânsito Brasil 3D: ficha de veículos e objetos de via, numa pista de estúdio vista de cima em 3/4.
    blender -b -P kit3d/tb_ficha.py -- saida.png [--escala 0.5]"""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
import tb_assets as A
import tb_cena as C

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else ["/tmp/ficha.png"]
saida = argv[0]
esc = float(argv[argv.index("--escala") + 1]) if "--escala" in argv else 1.0

C.limpa()
C.motor(True, 48, 1920, 1080, esc)
C.mundo("#e9edf1", 0.9)
C.sol(55, -40, 3.6)

# chão de asfalto com faixas
A.fita([(-60, 0), (60, 0)], 120, A.mat_cor("#e4e1db", 0.9, nome="tb_chao"), -0.02, "chao")
asf = A.mat_cor("#4a4f57", 0.85, nome="tb_asfalto")
linhas = [  # (y, [(modelo, cor, cor2)])
    (24, [("hatch", "#d7d7d7", ""), ("sedan", "#9aa0a6", ""), ("suv", "#1e2226", ""), ("picape", "#f1f0ec", ""),
          ("taxi", "#f4f4f2", ""), ("viatura", "#f4f4f2", "#14171a"), ("ambulancia", "#ffffff", "#d0202a")]),
    (14, [("moto", "#c8161d", "#1d2b3a"), ("moto_entrega", "#1f1f1f", "#f2b705"), ("vuc", "#e8e8e8", ""), ("toco", "#c8161d", ""),
          ("onibus", "#2f9e57", "#f2f2ee")]),
    (2, [("articulado", "#1f6fc0", "#f2f2ee"), ("carreta", "", "")]),
]
for y, itens in linhas:
    A.fita([(-58, y), (58, y)], 8.2, asf, 0.0, "pista")
    for s in (-1, 1):
        A.fita([(-58, y + s * 4.0), (58, y + s * 4.0)], 0.18, A.mat_cor("#f5f5f0", 0.5, nome="tb_tinta"), 0.01, "borda")
    x = -50
    for mod, cor, cor2 in itens:
        if mod == "carreta":
            cav, reb = A.carreta_completa("#c8161d", "#c8161d")
            x += 10.5
            cav.location = (x + 5, y, 0); reb.parent = cav
            A.rotulo("CARRETA", (x - 1, y - 6.5, 0.05), 1.0)
            x += 15
            continue
        L = A.COMPRIMENTO[mod]
        x += L / 2 + 2.8
        v = A.veiculo(mod, cor, cor2 or "#202020")
        v.location = (x, y, 0)
        if mod == "viatura":
            v["giro"] = 1.0
        nome = {"moto_entrega": "MOTOBOY", "onibus": "ÔNIBUS", "articulado": "ARTICULADO", "ambulancia": "AMBULÂNCIA",
                "picape": "PICAPE", "viatura": "VIATURA", "vuc": "VUC", "toco": "CAMINHÃO"}.get(mod, mod.upper())
        A.rotulo(nome, (x, y - 6.5, 0.05), 1.0)
        x += L / 2
# um carro freando e outro com pisca para ver as luzes
for o in bpy.data.objects:
    if o.get("modelo") == "sedan":
        o["freio"] = 1.0
    if o.get("modelo") == "hatch":
        o["pisca"] = 1.0

# objetos de via
A.fita([(-58, -22), (58, -22)], 30, asf, 0.0, "pista_ped")
A.pedagio(6, 3.6, tag=(0, 1), pos=(-34, -22, 0))
A.rotulo("PEDÁGIO", (-34, -40, 0.05), 1.4)
A.portico_free_flow(18, pos=(-8, -22, 0))
A.rotulo("FREE FLOW", (-8, -40, 0.05), 1.4)
A.placa_portico(["MARGINAL PINHEIROS", "INTERLAGOS  →"], 16, pos=(12, -22, 0))
A.rotulo("PLACA", (12, -40, 0.05), 1.4)
A.radar((26, -30, 0), 0); A.rotulo("RADAR", (26, -40, 0.05), 1.4)
A.semaforo((34, -31, 0), 0, 5.0); A.rotulo("SEMÁFORO", (36, -40, 0.05), 1.4)
for i in range(4):
    A.cone((44 + i * 1.6, -26, 0))
A.barreira(8, (48, -18, 0)); A.rotulo("CONE E MURETA", (48, -40, 0.05), 1.4)
c = A.veiculo("sedan", "#2b6cb0")
c.location = (-12, -30, 0); A.anel(3.4, pos=(-12, -30, 0.06))

CAMS = {"geral": ((0, 0, 0), 175, 62, 0, 50), "carros": ((-22, 24, 0), 42, 48, -25, 50), "pesados": ((-18, 8, 0), 60, 50, -25, 50),
        "via": ((-10, -24, 0), 75, 45, -20, 50)}
cam = argv[argv.index("--cam") + 1] if "--cam" in argv else "geral"
C.camera(*CAMS[cam])
C.render(saida)
