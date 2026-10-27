"""Trânsito Brasil 3D: biblioteca de veículos e objetos de via (Blender por script).
Tudo em metros, x = frente do veículo, z = cima. Os veículos de um mesmo modelo dividem a malha (cópia ligada);
a cor da lataria vem de obj.color, a 2ª cor (faixa do ônibus, jaqueta do motoboy) de obj["cor2"],
e a lanterna acende com obj["freio"] (0 a 1) e o pisca com obj["pisca"] (0 a 1). Assim 300 carros custam quase nada.
Uso:  import tb_assets as A;  c = A.veiculo("sedan", cor="#c8c8c8");  A.pedagio(8)
Classes de veículo (VEICULOS): hatch, sedan, suv, picape, taxi, moto, moto_entrega, onibus, articulado, vuc, toco, cavalo + carreta,
ambulancia, viatura.  Objetos de via: pedagio, portico_free_flow, placa_portico, radar, semaforo, cone, barreira, rotulo, anel, seta_chao."""
import math
import bpy, bmesh
from mathutils import Vector, Matrix

FONTE = "/System/Library/Fonts/Supplemental/Arial Rounded Bold.ttf"
FONTE_PLACA = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"


def hexrgb(h, a=1.0):
    h = h.lstrip("#")
    srgb = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in srgb]
    return (*lin, a)


# ---------------------------------------------------------------- materiais
def _bsdf(nome):
    m = bpy.data.materials.get(nome)
    if m:
        return m, None
    m = bpy.data.materials.new(nome)
    m.use_nodes = True
    return m, m.node_tree.nodes.get("Principled BSDF")


def mat_cor(h, rough=0.6, metal=0.0, emis=0.0, nome=None):
    """material de cor chapada (cacheado pelo nome)"""
    nome = nome or f"tb_{h}_{rough}_{metal}_{emis}"
    m, b = _bsdf(nome)
    if b:
        b.inputs["Base Color"].default_value = hexrgb(h)
        b.inputs["Roughness"].default_value = rough
        b.inputs["Metallic"].default_value = metal
        if emis:
            b.inputs["Emission Color"].default_value = hexrgb(h)
            b.inputs["Emission Strength"].default_value = emis
    return m


def _attr(nt, nome, tipo="OBJECT"):
    a = nt.nodes.new("ShaderNodeAttribute"); a.attribute_type = tipo; a.attribute_name = nome
    return a


def mat_pintura():
    """lataria: a cor é a do objeto (obj.color), com verniz"""
    m, b = _bsdf("tb_pintura")
    if b:
        nt = m.node_tree
        oi = nt.nodes.new("ShaderNodeObjectInfo")
        nt.links.new(oi.outputs["Color"], b.inputs["Base Color"])
        b.inputs["Roughness"].default_value = 0.32
        b.inputs["Coat Weight"].default_value = 0.35
    return m


def mat_pintura2():
    """2ª cor do veículo: obj["cor2"]"""
    m, b = _bsdf("tb_pintura2")
    if b:
        nt = m.node_tree
        nt.links.new(_attr(nt, "cor2").outputs["Color"], b.inputs["Base Color"])
        b.inputs["Roughness"].default_value = 0.45
    return m


def mat_luz(nome, cor, base, prop=None, ganho=6.0):
    """luz do veículo: brilho = base + ganho * obj[prop]"""
    m, b = _bsdf(nome)
    if b:
        nt = m.node_tree
        b.inputs["Base Color"].default_value = hexrgb(cor)
        b.inputs["Emission Color"].default_value = hexrgb(cor)
        b.inputs["Roughness"].default_value = 0.3
        if prop:
            mul = nt.nodes.new("ShaderNodeMath"); mul.operation = "MULTIPLY_ADD"
            nt.links.new(_attr(nt, prop).outputs["Fac"], mul.inputs[0])
            mul.inputs[1].default_value = ganho; mul.inputs[2].default_value = base
            nt.links.new(mul.outputs[0], b.inputs["Emission Strength"])
        else:
            b.inputs["Emission Strength"].default_value = base
    return m


def brilho_luzes(farol=2.0, lanterna=0.6, ganho_freio=6.0):
    """noite: farol e lanterna mais fortes (chame depois de criar os veículos)"""
    for nome, base in (("tb_farol", farol), ("tb_lanterna", lanterna)):
        m = bpy.data.materials.get(nome)
        if not m:
            continue
        for n in m.node_tree.nodes:
            if n.type == "MATH":
                n.inputs[2].default_value = base; n.inputs[1].default_value = ganho_freio
            elif n.type == "BSDF_PRINCIPLED" and not n.inputs["Emission Strength"].is_linked:
                n.inputs["Emission Strength"].default_value = base


def MATS():
    return {
        "pintura": mat_pintura(), "pintura2": mat_pintura2(),
        "vidro": mat_cor("#16202b", 0.06, nome="tb_vidro"), "pneu": mat_cor("#151515", 0.85, nome="tb_pneu"),
        "preto": mat_cor("#24272b", 0.5, nome="tb_preto"), "branco": mat_cor("#f1f0ec", 0.45, nome="tb_branco"),
        "cinza": mat_cor("#8e9296", 0.5, nome="tb_cinza"), "cromo": mat_cor("#c9ccd0", 0.2, 0.8, nome="tb_cromo"),
        "farol": mat_luz("tb_farol", "#fff6dc", 0.8), "lanterna": mat_luz("tb_lanterna", "#ff2414", 0.5, "freio", 7.0),
        "pisca": mat_luz("tb_pisca", "#ffa31a", 0.05, "pisca", 8.0),
        "giro_v": mat_luz("tb_giro_v", "#ff2030", 0.3, "giro", 9.0), "giro_a": mat_luz("tb_giro_a", "#2050ff", 0.3, "giro", 9.0),
        "bau": mat_cor("#d8262b", 0.5, nome="tb_bau"), "pele": mat_cor("#7a5236", 0.6, nome="tb_pele"),
        "amarelo": mat_cor("#f2b705", 0.5, nome="tb_amarelo"), "vermelho": mat_cor("#c8161d", 0.5, nome="tb_vermelho"),
        "lona": mat_cor("#3d5a73", 0.8, nome="tb_lona"),
    }


# ---------------------------------------------------------------- construtor de malha
class Malha:
    """junta caixas, cilindros e esferas numa malha só, com um material por peça"""
    def __init__(self, nome):
        self.nome = nome; self.bm = bmesh.new(); self.mats = []

    def _idx(self, mat):
        if mat not in self.mats:
            self.mats.append(mat)
        return self.mats.index(mat)

    def _pinta(self, verts, mat):
        i = self._idx(mat)
        fs = {f for v in verts for f in v.link_faces}
        for f in fs:
            f.material_index = i
        return fs

    def caixa(self, mat, c, tam, bevel=0.0, seg=2, topo=None, rot_z=0.0):
        """caixa centrada em c; topo=(recuo_frente, recuo_tras, recuo_lado) afina a face de cima (para-brisa inclinado)"""
        M = Matrix.Translation(Vector(c)) @ Matrix.Rotation(rot_z, 4, "Z") @ Matrix.Diagonal((*tam, 1.0))
        vs = bmesh.ops.create_cube(self.bm, size=1.0, matrix=M)["verts"]
        if topo:
            rf, rt, rl = topo
            zc = c[2]
            for v in vs:
                if v.co.z > zc:
                    lx = Vector((math.cos(rot_z), math.sin(rot_z), 0)); ly = Vector((-math.sin(rot_z), math.cos(rot_z), 0))
                    d = v.co - Vector(c)
                    ax, ay = d.dot(lx), d.dot(ly)
                    ax = ax - rf if ax > 0 else ax + rt
                    ay = ay - rl if ay > 0 else ay + rl
                    v.co = Vector(c) + lx * ax + ly * ay + Vector((0, 0, d.z))
        self._pinta(vs, mat)
        if bevel > 0:
            es = list({e for v in vs for e in v.link_edges})
            bmesh.ops.bevel(self.bm, geom=es + vs, offset=bevel, segments=seg, affect="EDGES", profile=0.5, clamp_overlap=True)
        return vs

    def cilindro(self, mat, c, r, h, eixo="Y", seg=14):
        R = {"X": Matrix.Rotation(math.pi / 2, 4, "Y"), "Y": Matrix.Rotation(math.pi / 2, 4, "X"), "Z": Matrix.Identity(4)}[eixo]
        vs = bmesh.ops.create_cone(self.bm, cap_ends=True, segments=seg, radius1=r, radius2=r, depth=h,
                                   matrix=Matrix.Translation(Vector(c)) @ R)["verts"]
        self._pinta(vs, mat)
        return vs

    def esfera(self, mat, c, r, esc=(1, 1, 1)):
        vs = bmesh.ops.create_uvsphere(self.bm, u_segments=12, v_segments=8, radius=r,
                                       matrix=Matrix.Translation(Vector(c)) @ Matrix.Diagonal((*esc, 1.0)))["verts"]
        self._pinta(vs, mat)
        return vs

    def rodas(self, mats, eixos_x, bitola, r=0.32, w=0.22):
        for x in eixos_x:
            for s in (-1, 1):
                self.cilindro(mats["pneu"], (x, s * bitola / 2, r), r, w, "Y")

    def malha(self):
        me = bpy.data.meshes.new(self.nome)
        self.bm.normal_update(); self.bm.to_mesh(me); self.bm.free()
        for m in self.mats:
            me.materials.append(m)
        for p in me.polygons:
            p.use_smooth = False
        return me


# ---------------------------------------------------------------- veículos (cada função devolve a malha do modelo)
def _carro_base(nome, L, W, H, cap=(0.0, 0.0), alt_capo=0.62, rodas_r=0.31, cabine_frac=(0.30, 0.78), aberto=False):
    """carro genérico: lataria baixa + cabine de vidro afinada + teto da cor do carro.
    cabine_frac = (onde a cabine começa, onde termina) medido de trás (0) para a frente (1)"""
    k = MATS(); m = Malha(nome)
    zc = 0.18
    m.caixa(k["pintura"], (0, 0, zc + alt_capo / 2), (L, W, alt_capo), bevel=0.12)
    x0 = -L / 2 + L * cabine_frac[0]; x1 = -L / 2 + L * cabine_frac[1]
    hc = H - zc - alt_capo
    cx = (x0 + x1) / 2; lc = x1 - x0
    if not aberto:
        m.caixa(k["vidro"], (cx, 0, zc + alt_capo + hc / 2 - 0.01), (lc, W * 0.86, hc), bevel=0.05, topo=(lc * 0.26, lc * 0.14, W * 0.06))
        m.caixa(k["pintura"], (cx - lc * 0.05, 0, H - 0.035), (lc * 0.56, W * 0.72, 0.07), bevel=0.03)
    # faróis, lanternas, piscas, retrovisores
    for s in (-1, 1):
        m.caixa(k["farol"], (L / 2 - 0.02, s * W * 0.33, zc + alt_capo * 0.72), (0.06, W * 0.2, 0.12), bevel=0.02)
        m.caixa(k["lanterna"], (-L / 2 + 0.02, s * W * 0.36, zc + alt_capo * 0.78), (0.06, W * 0.18, 0.13), bevel=0.02)
        m.caixa(k["pisca"], (L / 2 - 0.05, s * W * 0.47, zc + alt_capo * 0.72), (0.08, 0.06, 0.08))
        m.caixa(k["pisca"], (-L / 2 + 0.05, s * W * 0.47, zc + alt_capo * 0.78), (0.08, 0.06, 0.08))
        m.caixa(k["preto"], (x1 - lc * 0.12, s * (W / 2 + 0.07), zc + alt_capo + 0.05), (0.12, 0.14, 0.09), bevel=0.02)
    m.caixa(k["preto"], (L / 2 - 0.03, 0, zc + 0.12), (0.08, W * 0.9, 0.16))
    m.caixa(k["preto"], (-L / 2 + 0.03, 0, zc + 0.12), (0.08, W * 0.9, 0.16))
    m.rodas(k, (L / 2 - L * 0.19, -L / 2 + L * 0.19), W * 0.86, rodas_r)
    return m, k


def m_hatch():
    m, k = _carro_base("tb_hatch", 3.95, 1.72, 1.48, cabine_frac=(0.10, 0.70), alt_capo=0.64)
    return m.malha()


def m_sedan():
    m, k = _carro_base("tb_sedan", 4.55, 1.78, 1.46, cabine_frac=(0.24, 0.72))
    return m.malha()


def m_suv():
    m, k = _carro_base("tb_suv", 4.45, 1.84, 1.70, cabine_frac=(0.08, 0.72), alt_capo=0.80, rodas_r=0.36)
    for s in (-1, 1):
        m.caixa(k["preto"], (-0.3, s * 0.62, 1.73), (2.2, 0.05, 0.04))
    return m.malha()


def m_picape():
    k = MATS(); m = Malha("tb_picape")
    L, W = 5.30, 1.88
    m.caixa(k["pintura"], (0, 0, 0.62), (L, W, 0.82), bevel=0.12)
    m.caixa(k["vidro"], (0.55, 0, 1.33), (1.9, W * 0.86, 0.62), bevel=0.05, topo=(0.5, 0.15, 0.1))
    m.caixa(k["pintura"], (0.45, 0, 1.64), (1.15, W * 0.74, 0.06), bevel=0.03)
    m.caixa(k["preto"], (-1.45, 0, 1.0), (2.1, W * 0.84, 0.06))  # caçamba (fundo)
    for s in (-1, 1):
        m.caixa(k["farol"], (L / 2 - 0.02, s * 0.62, 0.86), (0.06, 0.36, 0.13))
        m.caixa(k["lanterna"], (-L / 2 + 0.02, s * 0.78, 0.9), (0.06, 0.18, 0.22))
        m.caixa(k["pisca"], (L / 2 - 0.05, s * 0.88, 0.86), (0.08, 0.06, 0.08))
    m.rodas(k, (1.6, -1.6), W * 0.86, 0.38)
    return m.malha()


def m_taxi():
    m, k = _carro_base("tb_taxi", 4.45, 1.76, 1.46, cabine_frac=(0.22, 0.72))
    m.caixa(k["farol"], (-0.05, 0, 1.55), (0.28, 0.75, 0.14), bevel=0.04)  # luminoso TÁXI
    return m.malha()


def m_viatura():
    m, k = _carro_base("tb_viatura", 4.55, 1.80, 1.48, cabine_frac=(0.24, 0.72))
    m.caixa(k["preto"], (0.0, 0, 1.53), (0.32, 1.3, 0.1), bevel=0.03)
    m.caixa(k["giro_v"], (0.0, -0.36, 1.6), (0.26, 0.5, 0.08), bevel=0.03)
    m.caixa(k["giro_a"], (0.0, 0.36, 1.6), (0.26, 0.5, 0.08), bevel=0.03)
    m.caixa(k["pintura2"], (1.9, 0, 0.82), (0.6, 1.72, 0.03))  # faixa no capô
    return m.malha()


def m_ambulancia():
    k = MATS(); m = Malha("tb_ambulancia")
    L, W = 5.6, 2.0
    m.caixa(k["branco"], (-0.45, 0, 1.45), (4.4, W, 2.3), bevel=0.12)
    m.caixa(k["branco"], (2.25, 0, 0.75), (1.1, W * 0.96, 0.9), bevel=0.15)
    m.caixa(k["vidro"], (1.62, 0, 1.55), (0.3, W * 0.88, 0.7), topo=(0.25, 0, 0.04))
    m.caixa(k["pintura2"], (-0.45, 0, 1.2), (4.42, W + 0.02, 0.2))
    m.caixa(k["vermelho"], (-0.45, 0, 2.61), (0.7, 0.24, 0.02)); m.caixa(k["vermelho"], (-0.45, 0, 2.62), (0.24, 0.7, 0.02))
    m.caixa(k["giro_v"], (1.25, -0.5, 2.66), (0.22, 0.6, 0.12)); m.caixa(k["giro_a"], (1.25, 0.5, 2.66), (0.22, 0.6, 0.12))
    for s in (-1, 1):
        m.caixa(k["farol"], (L / 2 - 0.02, s * 0.66, 0.9), (0.06, 0.3, 0.14))
        m.caixa(k["lanterna"], (-L / 2 + 0.14, s * 0.85, 1.0), (0.06, 0.16, 0.4))
    m.rodas(k, (1.9, -1.6), W * 0.88, 0.36)
    return m.malha()


def m_moto(entrega=False):
    k = MATS(); m = Malha("tb_moto_entrega" if entrega else "tb_moto")
    m.cilindro(k["pneu"], (0.72, 0, 0.31), 0.31, 0.12, "Y"); m.cilindro(k["pneu"], (-0.68, 0, 0.31), 0.31, 0.15, "Y")
    m.caixa(k["pintura"], (0.05, 0, 0.62), (1.1, 0.34, 0.32), bevel=0.08)  # tanque e carenagem
    m.caixa(k["preto"], (-0.45, 0, 0.78), (0.7, 0.28, 0.1), bevel=0.04)  # banco
    m.caixa(k["preto"], (0.68, 0, 1.02), (0.06, 0.72, 0.04))  # guidão
    m.caixa(k["farol"], (0.86, 0, 0.88), (0.06, 0.16, 0.12), bevel=0.03)
    m.caixa(k["lanterna"], (-0.92, 0, 0.82), (0.05, 0.14, 0.07))
    # piloto: jaqueta (2ª cor), capacete, braços
    m.caixa(k["pintura2"], (-0.32, 0, 1.18), (0.34, 0.44, 0.62), bevel=0.1, topo=(0.06, 0.0, 0.05))
    m.esfera(k["preto"] if not entrega else k["branco"], (-0.18, 0, 1.66), 0.16, (1.15, 1.0, 1.0))
    for s in (-1, 1):
        m.caixa(k["pintura2"], (0.2, s * 0.24, 1.18), (0.62, 0.11, 0.11), bevel=0.04)
        m.caixa(k["preto"], (-0.15, s * 0.16, 0.66), (0.5, 0.12, 0.14), bevel=0.04)
    if entrega:
        m.caixa(k["bau"], (-0.78, 0, 1.18), (0.44, 0.46, 0.44), bevel=0.04)
    return m.malha()


def m_onibus(L=12.6, articulado=False):
    k = MATS(); m = Malha("tb_articulado" if articulado else "tb_onibus")
    W, H = 2.55, 3.2
    m.caixa(k["pintura"], (0, 0, 0.35 + (H - 0.35) / 2), (L, W, H - 0.35), bevel=0.14)
    m.caixa(k["pintura2"], (0, 0, 0.95), (L + 0.02, W + 0.02, 0.5))  # faixa da linha
    for s in (-1, 1):
        m.caixa(k["vidro"], (0.3, s * (W / 2 + 0.005), 2.15), (L - 1.6, 0.02, 0.95))
    m.caixa(k["vidro"], (L / 2 + 0.005, 0, 2.0), (0.02, W * 0.92, 1.35))
    m.caixa(k["farol"], (L / 2 + 0.01, 0, 2.93), (0.02, W * 0.6, 0.24))  # letreiro
    m.caixa(k["branco"], (0, 0, H + 0.01), (L - 0.4, W - 0.25, 0.02))  # teto
    m.caixa(k["cinza"], (L * 0.18, 0, H + 0.16), (2.8, 1.8, 0.3), bevel=0.06)  # ar-condicionado
    if articulado:
        m.caixa(k["preto"], (0, 0, 1.75), (0.9, W + 0.04, 2.8))  # sanfona
    for s in (-1, 1):
        m.caixa(k["farol"], (L / 2 + 0.01, s * 0.95, 0.65), (0.03, 0.34, 0.16))
        m.caixa(k["lanterna"], (-L / 2 - 0.01, s * 1.02, 0.9), (0.03, 0.18, 0.5))
        m.caixa(k["pisca"], (L / 2 + 0.01, s * 1.18, 0.65), (0.03, 0.12, 0.12))
    eixos = (L / 2 - 2.5, -L / 2 + 3.2) if not articulado else (L / 2 - 2.5, 1.2, -L / 2 + 2.6)
    m.rodas(k, eixos, W * 0.84, 0.5, 0.3)
    return m.malha()


def m_vuc():
    """VUC: o caminhão pequeno que pode rodar no centro expandido"""
    k = MATS(); m = Malha("tb_vuc")
    m.caixa(k["pintura"], (2.25, 0, 1.25), (1.7, 2.1, 1.9), bevel=0.12, topo=(0.25, 0, 0.05))
    m.caixa(k["vidro"], (3.08, 0, 1.6), (0.06, 1.9, 0.8))
    m.caixa(k["branco"], (-0.75, 0, 1.75), (4.2, 2.2, 2.5), bevel=0.05)
    m.caixa(k["preto"], (0, 0, 0.55), (6.0, 1.4, 0.25))
    for s in (-1, 1):
        m.caixa(k["farol"], (3.11, s * 0.72, 0.75), (0.04, 0.3, 0.16))
        m.caixa(k["lanterna"], (-2.86, s * 0.9, 0.75), (0.04, 0.2, 0.2))
    m.rodas(k, (2.1, -1.6), 1.8, 0.42, 0.26)
    return m.malha()


def m_toco():
    """caminhão toco (um eixo atrás), baú com lona"""
    k = MATS(); m = Malha("tb_toco")
    m.caixa(k["pintura"], (3.35, 0, 1.55), (1.9, 2.45, 2.3), bevel=0.12, topo=(0.2, 0, 0.05))
    m.caixa(k["vidro"], (4.31, 0, 2.0), (0.06, 2.2, 0.9))
    m.caixa(k["lona"], (-1.0, 0, 2.0), (6.6, 2.5, 2.7), bevel=0.06)
    m.caixa(k["preto"], (0, 0, 0.6), (8.6, 1.3, 0.3))
    for s in (-1, 1):
        m.caixa(k["farol"], (4.33, s * 0.85, 0.85), (0.04, 0.34, 0.18))
        m.caixa(k["lanterna"], (-4.31, s * 1.05, 0.8), (0.04, 0.22, 0.22))
    m.rodas(k, (3.1, -2.4), 2.05, 0.52, 0.32)
    return m.malha()


def m_cavalo():
    """cavalo mecânico (a frente da carreta); a quinta roda fica em x = -1.4"""
    k = MATS(); m = Malha("tb_cavalo")
    m.caixa(k["pintura"], (1.35, 0, 1.75), (2.3, 2.5, 2.7), bevel=0.14, topo=(0.15, 0, 0.05))
    m.caixa(k["vidro"], (2.52, 0, 2.3), (0.06, 2.25, 1.0))
    m.caixa(k["pintura"], (0.35, 0, 3.25), (1.2, 2.3, 0.4), bevel=0.15, topo=(0.4, 0, 0.1))  # defletor
    m.caixa(k["preto"], (-0.9, 0, 0.75), (3.2, 1.3, 0.3))
    m.cilindro(k["cromo"], (-0.15, 1.05, 0.75), 0.28, 0.9, "X")
    for s in (-1, 1):
        m.caixa(k["farol"], (2.53, s * 0.9, 0.9), (0.04, 0.34, 0.18))
        m.cilindro(k["cromo"], (0.12, s * 1.12, 2.9), 0.08, 1.4, "Z")
    m.rodas(k, (1.7, -1.3, -2.5), 2.05, 0.52, 0.32)
    return m.malha()


def m_carreta():
    """semirreboque baú de 13,5 m; o pino-rei fica em x = +6.0 (é por ele que o cavalo puxa)"""
    k = MATS(); m = Malha("tb_carreta")
    m.caixa(k["branco"], (0, 0, 2.45), (13.5, 2.55, 2.8), bevel=0.05)
    m.caixa(k["pintura2"], (0, 0, 1.15), (13.52, 2.57, 0.2))
    m.caixa(k["preto"], (-0.5, 0, 0.85), (12.4, 1.2, 0.3))
    for s in (-1, 1):
        m.caixa(k["lanterna"], (-6.76, s * 1.05, 0.85), (0.04, 0.24, 0.2))
    m.rodas(k, (-3.8, -5.1, -6.4 + 0.1), 2.05, 0.52, 0.32)
    return m.malha()


MODELOS = {"hatch": m_hatch, "sedan": m_sedan, "suv": m_suv, "picape": m_picape, "taxi": m_taxi, "viatura": m_viatura,
           "ambulancia": m_ambulancia, "moto": lambda: m_moto(False), "moto_entrega": lambda: m_moto(True),
           "onibus": lambda: m_onibus(12.6), "articulado": lambda: m_onibus(18.6, True), "vuc": m_vuc, "toco": m_toco,
           "cavalo": m_cavalo, "carreta": m_carreta}
COMPRIMENTO = {"hatch": 3.95, "sedan": 4.55, "suv": 4.45, "picape": 5.3, "taxi": 4.45, "viatura": 4.55, "ambulancia": 5.6,
               "moto": 2.1, "moto_entrega": 2.2, "onibus": 12.6, "articulado": 18.6, "vuc": 6.3, "toco": 8.7, "cavalo": 5.4, "carreta": 13.5}
LARGURA = {"hatch": 1.72, "sedan": 1.78, "suv": 1.84, "picape": 1.88, "taxi": 1.76, "viatura": 1.8, "ambulancia": 2.0, "moto": 0.8,
           "moto_entrega": 0.9, "onibus": 2.55, "articulado": 2.55, "vuc": 2.2, "toco": 2.5, "cavalo": 2.5, "carreta": 2.55}
VEICULOS = list(MODELOS)
_CACHE = {}


def colecao(nome):
    c = bpy.data.collections.get(nome)
    if not c:
        c = bpy.data.collections.new(nome); bpy.context.scene.collection.children.link(c)
    return c


def veiculo(modelo, cor="#d0d0d0", cor2="#202020", nome=None, col="veiculos", escala=1.0):
    me = _CACHE.get(modelo)
    if me is None or me.name not in bpy.data.meshes:
        me = MODELOS[modelo](); _CACHE[modelo] = me
    o = bpy.data.objects.new(nome or modelo, me)
    colecao(col).objects.link(o)
    o.color = hexrgb(cor)
    o["cor2"] = hexrgb(cor2)[:3]
    o["freio"] = 0.0; o["pisca"] = 0.0; o["giro"] = 0.0
    o["modelo"] = modelo
    o.scale = (escala,) * 3
    return o


def carreta_completa(cor="#2b5d9e", cor2="#2b5d9e", nome="carreta"):
    """cavalo + semirreboque; devolve (cavalo, reboque). Para posicionar ao longo de um caminho, o reboque segue o pino em x = -1.4 do cavalo"""
    cav = veiculo("cavalo", cor, cor2, nome + "_cavalo")
    reb = veiculo("carreta", "#f0f0f0", cor2, nome + "_reboque")
    reb.location = (-1.4 - 6.0, 0, 0)
    return cav, reb


# ---------------------------------------------------------------- texto e marcadores
def texto(t, tam=1.0, mat=None, fonte=FONTE, alinha="CENTER", extrude=0.0, col="rotulos"):
    cu = bpy.data.curves.new("txt", "FONT")
    try:
        cu.font = bpy.data.fonts.load(fonte, check_existing=True)
    except Exception:
        pass
    cu.body = t; cu.size = tam; cu.align_x = alinha; cu.align_y = "CENTER"; cu.extrude = extrude
    o = bpy.data.objects.new("txt_" + t[:12], cu)
    colecao(col).objects.link(o)
    if mat:
        o.data.materials.append(mat)
    return o


def pilula(comp, alt, esp, mat, nome="pilula", col="rotulos"):
    """retângulo de cantos redondos (deitado no plano xy)"""
    r = min(comp, alt) / 2; dx = max(comp / 2 - r, 0.0)
    contorno = [(dx + r * math.cos(a), r * math.sin(a)) for a in [math.radians(-90 + 180 * i / 10) for i in range(11)]]
    contorno += [(-dx + r * math.cos(a), r * math.sin(a)) for a in [math.radians(90 + 180 * i / 10) for i in range(11)]]
    bm = bmesh.new()
    f = bm.faces.new([bm.verts.new((x, y, -esp / 2)) for x, y in contorno])
    ext = bmesh.ops.extrude_face_region(bm, geom=[f])
    for v in [g for g in ext["geom"] if isinstance(g, bmesh.types.BMVert)]:
        v.co.z += esp
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new(nome); bm.to_mesh(me); bm.free(); me.materials.append(mat)
    o = bpy.data.objects.new(nome, me); colecao(col).objects.link(o)
    return o


def rotulo(t, pos, tam=6.0, fundo="#14181f", cor_txt="#ffffff", yaw=0.0, col="rotulos", deitado=True):
    """etiqueta em pílula escura com texto claro. deitado=True: no chão, para câmera de cima. yaw gira para a câmera"""
    raiz = bpy.data.objects.new("rotulo_" + t[:10], None); colecao(col).objects.link(raiz)
    tx = texto(t, tam, mat_cor(cor_txt, 0.5, emis=0.6, nome=f"tb_txt_{cor_txt}"), col=col)
    bpy.context.view_layer.update()
    larg = tx.dimensions.x if tx.dimensions.x > tam * 0.3 else len(t) * tam * 0.66
    p = pilula(larg + tam * 1.0, tam * 1.55, tam * 0.12, mat_cor(fundo, 0.6, nome=f"tb_pil_{fundo}"), col=col)
    p.parent = raiz; tx.parent = raiz
    tx.location = (0, -tam * 0.04, tam * 0.08)
    raiz.location = pos
    raiz.rotation_euler = (0 if deitado else math.pi / 2, 0, yaw)
    return raiz


def anel(raio=3.2, cor="#ffd21f", esp=0.35, pos=(0, 0, 0.06), col="rotulos"):
    """aro brilhante no chão em volta de um veículo (identificação)"""
    bm = bmesh.new()
    bmesh.ops.create_circle(bm, cap_ends=False, segments=40, radius=raio)
    ext = bmesh.ops.extrude_edge_only(bm, edges=bm.edges[:])
    for v in [g for g in ext["geom"] if isinstance(g, bmesh.types.BMVert)]:
        v.co *= (raio + esp) / raio
    me = bpy.data.meshes.new("anel"); bm.to_mesh(me); bm.free()
    me.materials.append(mat_cor(cor, 0.4, emis=1.5, nome=f"tb_anel_{cor}"))
    o = bpy.data.objects.new("anel", me); colecao(col).objects.link(o); o.location = pos
    return o


def fita(pts, larg, mat, z=0.0, nome="fita", col="via"):
    """faixa (ribbon) ao longo de uma polilinha 2D/3D; z soma à altura de cada ponto"""
    pts = [Vector((p[0], p[1], (p[2] if len(p) > 2 else 0.0) + z)) for p in pts]
    if len(pts) < 2:
        return None
    bm = bmesh.new(); esq, dir_ = [], []
    for i, p in enumerate(pts):
        a = pts[max(i - 1, 0)]; b = pts[min(i + 1, len(pts) - 1)]
        t = (b - a); t.z = 0
        if t.length < 1e-6:
            t = Vector((1, 0, 0))
        t.normalize(); n = Vector((-t.y, t.x, 0))
        # meia-esquadria limitada
        if 0 < i < len(pts) - 1:
            t1 = (p - a); t1.z = 0; t2 = (b - p); t2.z = 0
            if t1.length > 1e-6 and t2.length > 1e-6:
                t1.normalize(); t2.normalize()
                n1 = Vector((-t1.y, t1.x, 0)); mit = (n1 + Vector((-t2.y, t2.x, 0)))
                if mit.length > 1e-6:
                    mit.normalize(); f = 1.0 / max(mit.dot(n1), 0.35); n = mit * f
        esq.append(bm.verts.new(p + n * larg / 2)); dir_.append(bm.verts.new(p - n * larg / 2))
    for i in range(len(pts) - 1):
        try:
            bm.faces.new((dir_[i], dir_[i + 1], esq[i + 1], esq[i]))
        except ValueError:
            pass
    me = bpy.data.meshes.new(nome); bm.to_mesh(me); bm.free(); me.materials.append(mat)
    o = bpy.data.objects.new(nome, me); colecao(col).objects.link(o)
    return o


def seta_chao(pts, larg=4.0, cor="#ffd21f", z=0.4, col="rotulos"):
    """rota desenhada no chão, com ponta de seta no fim"""
    mat = mat_cor(cor, 0.4, emis=1.2, nome=f"tb_seta_{cor}")
    corpo = fita(pts[:-1] + [Vector(pts[-1]).lerp(Vector(pts[-2]), min(0.99, larg * 1.2 / max((Vector(pts[-1]) - Vector(pts[-2])).length, 1e-3)))], larg, mat, z, "seta", col)
    p1, p0 = Vector(pts[-1]), Vector(pts[-2]); d = (p1 - p0); d.z = 0; d.normalize(); n = Vector((-d.y, d.x, 0))
    base = p1 - d * larg * 1.6
    bm = bmesh.new()
    vs = [bm.verts.new(v + Vector((0, 0, z))) for v in (p1, base + n * larg * 1.1, base - n * larg * 1.1)]
    bm.faces.new(vs); me = bpy.data.meshes.new("ponta"); bm.to_mesh(me); bm.free(); me.materials.append(mat)
    o = bpy.data.objects.new("ponta", me); colecao(col).objects.link(o)
    return corpo, o


# ---------------------------------------------------------------- objetos de via
def _obj(m, nome, pos=(0, 0, 0), yaw=0.0, col="via"):
    o = bpy.data.objects.new(nome, m.malha()); colecao(col).objects.link(o)
    o.location = pos; o.rotation_euler.z = yaw
    return o


def pedagio(n=8, faixa=3.6, tag=(0, 1), pos=(0, 0, 0), yaw=0.0, nome_praca="PEDÁGIO", col="via"):
    """praça de pedágio atravessando a pista (o trânsito anda em +x). tag = índices das cabines automáticas (TAG).
    Cabines em ilhas de concreto, cobertura com a faixa do nome, sinal verde/vermelho sobre cada faixa."""
    k = MATS(); m = Malha("pedagio")
    larg = n * faixa
    conc = mat_cor("#d9d6cf", 0.8, nome="tb_concreto"); verde = mat_luz("tb_sinal_verde", "#19d35a", 3.0)
    verm = mat_luz("tb_sinal_verm", "#ff2b2b", 3.0); amar = mat_cor("#f2b705", 0.5, nome="tb_amarelo")
    for i in range(n + 1):
        y = -larg / 2 + i * faixa
        m.caixa(conc, (0, y, 0.15), (16.0, 1.3, 0.3), bevel=0.25)  # ilha
        m.caixa(amar, (8.2, y, 0.32), (0.6, 1.2, 0.5), bevel=0.1)  # nariz da ilha
        if i < n + 1:
            m.caixa(k["branco"], (0, y, 1.55), (2.4, 1.15, 2.4), bevel=0.08)  # cabine
            m.caixa(k["vidro"], (0, y, 1.85), (2.42, 1.17, 0.8))
    m.caixa(k["branco"], (0, 0, 6.2), (11.0, larg + 3.0, 0.5), bevel=0.15)  # cobertura
    m.caixa(mat_cor("#0d5aa7", 0.5, nome="tb_azul_ped"), (4.6, 0, 6.2), (1.9, larg + 3.02, 0.9), bevel=0.1)  # testeira
    for i in range(n):
        y = -larg / 2 + (i + 0.5) * faixa
        m.caixa(verde if i not in tag else amar, (5.6, y, 5.45), (0.15, 0.9, 0.9), bevel=0.05)
    for i in range(n + 1):
        y = -larg / 2 + i * faixa
        m.caixa(conc, (0, y, 3.9), (0.5, 0.5, 4.2))
    o = _obj(m, "pedagio", pos, yaw, col)
    t = texto(nome_praca, 0.75, mat_cor("#ffffff", 0.5, emis=0.4, nome="tb_txt_branco"), col=col)
    t.parent = o; t.location = (5.56, 0, 6.2); t.rotation_euler = (math.pi / 2, 0, math.pi / 2)
    for i in tag:
        y = -larg / 2 + (i + 0.5) * faixa
        tt = texto("TAG", 0.45, mat_cor("#1a1400", 0.5, nome="tb_txt_escuro"), col=col)
        tt.parent = o; tt.location = (5.69, y, 5.45); tt.rotation_euler = (math.pi / 2, 0, math.pi / 2)
        f = fita([(-30, y), (-6, y)], 0.25, amar, 0.03, "faixa_tag", col); f.parent = o
    return o


def portico_free_flow(larg=14.0, pos=(0, 0, 0), yaw=0.0, col="via"):
    """pórtico do free flow: câmeras e antenas sobre cada faixa, sem cabine e sem cancela"""
    k = MATS(); m = Malha("free_flow")
    aco = mat_cor("#9aa3ab", 0.35, 0.6, nome="tb_aco")
    for s in (-1, 1):
        m.caixa(aco, (0, s * (larg / 2 + 0.6), 3.4), (0.45, 0.45, 6.8))
        m.caixa(mat_cor("#d9d6cf", 0.8, nome="tb_concreto"), (0, s * (larg / 2 + 0.6), 0.25), (1.2, 1.2, 0.5))
    m.caixa(aco, (0, 0, 6.6), (0.9, larg + 1.8, 0.7))
    nf = max(2, int(larg // 3.5))
    for i in range(nf):
        y = -larg / 2 + (i + 0.5) * larg / nf
        m.caixa(k["preto"], (0.65, y, 6.2), (0.5, 0.35, 0.3), bevel=0.04)
        m.caixa(mat_luz("tb_led_ff", "#8fe3ff", 2.0), (0.92, y, 6.2), (0.04, 0.2, 0.12))
    return _obj(m, "free_flow", pos, yaw, col)


def placa_portico(linhas, larg=12.0, pos=(0, 0, 0), yaw=0.0, col="via"):
    """placa verde de rodovia num pórtico (texto branco). linhas = lista de textos"""
    k = MATS(); m = Malha("placa")
    aco = mat_cor("#9aa3ab", 0.35, 0.6, nome="tb_aco"); verde = mat_cor("#0b6b3a", 0.55, nome="tb_verde_placa")
    for s in (-1, 1):
        m.caixa(aco, (0, s * (larg / 2 + 0.5), 3.6), (0.35, 0.35, 7.2))
    m.caixa(aco, (0, 0, 6.9), (0.3, larg + 1.4, 0.3))
    h = 0.9 + 0.75 * len(linhas)
    m.caixa(verde, (0.2, 0, 6.6 + h / 2 - 0.6), (0.12, larg * 0.7, h), bevel=0.05)
    o = _obj(m, "placa", pos, yaw, col)
    for i, t in enumerate(linhas):
        tt = texto(t, 0.6, mat_cor("#ffffff", 0.5, emis=0.4, nome="tb_txt_branco"), FONTE_PLACA, col=col)
        tt.parent = o; tt.location = (0.27, 0, 6.6 + h - 0.6 - 0.45 - i * 0.75); tt.rotation_euler = (math.pi / 2, 0, math.pi / 2)
    return o


def radar(pos=(0, 0, 0), yaw=0.0, col="via"):
    k = MATS(); m = Malha("radar")
    m.caixa(mat_cor("#c9ccd0", 0.4, 0.5, nome="tb_poste"), (0, 0, 2.3), (0.18, 0.18, 4.6))
    m.caixa(mat_cor("#f2b705", 0.5, nome="tb_amarelo"), (0.15, 0, 4.4), (0.5, 0.6, 0.7), bevel=0.06)
    m.caixa(k["vidro"], (0.41, 0, 4.45), (0.04, 0.35, 0.25))
    m.caixa(mat_luz("tb_flash", "#ffffff", 0.2, "flash", 30.0), (0.41, 0.2, 4.7), (0.04, 0.12, 0.12))
    return _obj(m, "radar", pos, yaw, col)


def semaforo(pos=(0, 0, 0), yaw=0.0, braco=4.0, col="via"):
    k = MATS(); m = Malha("semaforo")
    poste = mat_cor("#3a3f44", 0.5, nome="tb_poste_esc")
    m.caixa(poste, (0, 0, 2.8), (0.16, 0.16, 5.6)); m.caixa(poste, (0, braco / 2, 5.5), (0.12, braco, 0.12))
    m.caixa(k["preto"], (0, braco - 0.2, 4.9), (0.35, 0.35, 1.05), bevel=0.05)
    for j, (c, e) in enumerate((("#ff2b2b", 2.5), ("#ffb000", 0.15), ("#19d35a", 0.15))):
        m.caixa(mat_cor(c, 0.4, emis=e, nome=f"tb_lamp_{c}_{e}"), (0.18, braco - 0.2, 5.2 - j * 0.3), (0.04, 0.22, 0.22))
    return _obj(m, "semaforo", pos, yaw, col)


def cone(pos=(0, 0, 0), col="via"):
    m = Malha("cone")
    m.caixa(mat_cor("#ff6a00", 0.5, nome="tb_laranja"), (0, 0, 0.36), (0.34, 0.34, 0.7), topo=(0.12, 0.12, 0.12))
    m.caixa(mat_cor("#f1f0ec", 0.45, nome="tb_branco"), (0, 0, 0.03), (0.42, 0.42, 0.06))
    return _obj(m, "cone", pos, 0, col)


def barreira(comp=6.0, pos=(0, 0, 0), yaw=0.0, col="via"):
    """mureta New Jersey de concreto"""
    m = Malha("barreira")
    m.caixa(mat_cor("#cfcbc2", 0.85, nome="tb_concreto2"), (0, 0, 0.42), (comp, 0.6, 0.84), topo=(0, 0, 0.18))
    return _obj(m, "barreira", pos, yaw, col)


# ---------------------------------------------------------------- objetos do ep. 1 (regra dos dois segundos)
def poste(pos=(0, 0, 0), alt=7.5, col="via"):
    """poste de iluminação com a faixa amarela e preta na base: é o ponto que o carro da frente 'passa' na regra dos dois segundos"""
    m = Malha("poste")
    aco = mat_cor("#9aa3ab", 0.35, 0.6, nome="tb_aco")
    m.caixa(aco, (0, 0, alt / 2), (0.55, 0.55, alt), bevel=0.06)
    m.caixa(aco, (1.3, 0, alt - 0.15), (2.8, 0.3, 0.3))
    m.caixa(mat_luz("tb_lamp_poste", "#fff1c9", 1.6), (2.5, 0, alt - 0.45), (1.1, 0.6, 0.25), bevel=0.05)
    am, pr = mat_cor("#f5c518", 0.5, nome="tb_amarelo2"), mat_cor("#1a1400", 0.6, nome="tb_preto2")
    for i in range(7):   # faixa zebrada na base (para ler de longe)
        m.caixa(am if i % 2 == 0 else pr, (0, 0, 0.45 + i * 0.45), (0.62, 0.62, 0.45))
    return _obj(m, "poste", pos, 0, col)


def regua_tempo(p0, yaw, v_ms, segundos=2.0, larg=2.6, z=0.0, cor="#ffd21f", col="rotulos"):
    """régua no chão para a regra dos 2 segundos: parte do ponto p0 (o para-choque de trás do carro da frente) e anda para TRÁS v*segundos metros;
    uma divisão por segundo, com o número em pílula. yaw = sentido em que o carro anda."""
    import mathutils
    dx, dy = math.cos(yaw), math.sin(yaw)
    mat = mat_cor(cor, 0.4, emis=1.1, nome=f"tb_regua_{cor}"); esc = mat_cor("#8a6d00", 0.5, emis=0.3, nome="tb_regua_esc")
    objs = []
    n = int(math.ceil(segundos))
    for s in range(n):
        a = p0[0] - dx * v_ms * s, p0[1] - dy * v_ms * s
        b = p0[0] - dx * v_ms * min(s + 1, segundos), p0[1] - dy * v_ms * min(s + 1, segundos)
        objs.append(fita([(a[0], a[1], z), (b[0], b[1], z)], larg * (0.8 if s % 2 else 1.0), mat if s % 2 == 0 else esc, 0.0, f"regua{s}", col))
    for s in range(n + 1):
        t = min(s, segundos); q = (p0[0] - dx * v_ms * t, p0[1] - dy * v_ms * t)
        objs.append(fita([(q[0] - dy * larg, q[1] + dx * larg, z), (q[0] + dy * larg, q[1] - dx * larg, z)], 0.35, mat, 0.01, f"marca{s}", col))
    return objs


def aro_tipo(col="rotulos"):
    return anel(3.4, "#ffd21f", 0.45, pos=(0, 0, 0.5), col=col)
