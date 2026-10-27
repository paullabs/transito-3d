"""Trânsito Brasil 3D: monta o mapa 3D a partir do JSON do OpenStreetMap (tb_osm.py), em um dos estilos.
    import tb_mapa as MP;  mapa = MP.Mapa("transito/dados_osm/estaiada.json", estilo="maquete");  mapa.monta(regiao=(x, y, raio))
Vias viram fitas na largura de verdade (faixas x 3,4 m), pontes sobem com rampa (altura propagada pela rede de ruas),
prédios sobem na altura do OSM (ou estimada), rio, verde, trem da Linha 9 e monotrilho da Linha 17, e a torre da Ponte Estaiada."""
import json, math, heapq, random
import bpy, bmesh
from mathutils import Vector
import tb_assets as A

ESTILOS = {
    "maquete": dict(chao="#dbd5c9", calcada="#e9e4da", verde="#a9cf8c", agua="#6cb4d4", asf1="#474c55", asf2="#5c6169", ciclo="#c4523e",
                    tinta="#f7f7f3", amarelo="#f2c230", parede="#f1eee7", teto="#fbfaf6", torre="#a9bccb", ponte="#d1ccc2",
                    trilho="#8c8277", monotrilho="#c9b37a", mundo="#dde6ee", mundo_forca=1.0, sol=4.2, sol_cor="#fff3e0", ceu=False),
    # didático: o mapa todo em tons claros e calmos; só o que está em foco (via, carros, rótulos) tem cor e contraste
    "didatico": dict(chao="#e6e4de", calcada="#f3f1ec", verde="#d4e2c8", agua="#bcd6e6", asf1="#2f3541", asf2="#3d4450", via_apagada="#d9dadc",
                     ciclo="#e2b3a8", tinta="#ffffff", amarelo="#f5c518", parede="#f7f6f2", teto="#ffffff", torre="#cfd8e0", ponte="#dcd9d2",
                     trilho="#d2cdc4", monotrilho="#d9c9a0", mundo="#eceef0", mundo_forca=1.0, sol=3.4, sol_cor="#fff6e8", ceu=False),
    "noite": dict(chao="#0f1828", calcada="#142033", verde="#132a24", agua="#0c2a44", asf1="#33405e", asf2="#253049", ciclo="#4a2328",
                  tinta="#7d8db0", amarelo="#a08a42", parede="#1a2539", teto="#24304a", torre="#22314f", ponte="#2c3956",
                  trilho="#2f3644", monotrilho="#8a7536", mundo="#16243f", mundo_forca=1.4, sol=2.6, sol_cor="#9db4ff", ceu=False),
    "real": dict(chao="#9d978a", calcada="#b3ad9f", verde="#5d7f3e", agua="#3f6f78", asf1="#34373b", asf2="#4b4e52", ciclo="#9c3b2e",
                 tinta="#ecebe4", amarelo="#e3b33a", parede="#c4bcae", teto="#8a847a", torre="#5f7a90", ponte="#aaa498",
                 trilho="#5e574e", monotrilho="#b09a5c", mundo="#cfdbe6", mundo_forca=0.35, sol=6.0, sol_cor="#ffe9c8", ceu=True),
}
LARG_FAIXA = {"motorway": 3.6, "trunk": 3.5}
FAIXAS_PADRAO = {"motorway": 3, "trunk": 3, "primary": 2, "secondary": 2, "tertiary": 2, "residential": 2, "living_street": 2,
                 "unclassified": 2, "service": 1, "busway": 1}
ORDEM = {"service": 0, "living_street": 0, "residential": 1, "unclassified": 1, "busway": 2, "tertiary": 2, "secondary": 3,
         "primary": 4, "trunk": 5, "motorway": 6}
PRINCIPAIS = {"motorway", "trunk", "primary", "secondary"}
ALT_PONTE = 8.5


def base_tipo(t):
    return t.replace("_link", "")


def largura_via(v):
    t = base_tipo(v["tipo"])
    if v["tipo"] == "cycleway":
        return 2.2
    n = v["faixas"] or (1 if v["tipo"].endswith("_link") else FAIXAS_PADRAO.get(t, 2))
    return n * LARG_FAIXA.get(t, 3.3)


def chave(p):
    return (round(p[0], 1), round(p[1], 1))


def offset(pts, d):
    """desloca uma polilinha d metros para a ESQUERDA (d < 0 = direita), com meia-esquadria limitada; mantém z"""
    P = [Vector((p[0], p[1], p[2] if len(p) > 2 else 0.0)) for p in pts]
    out = []
    for i, p in enumerate(P):
        a = P[max(i - 1, 0)]; b = P[min(i + 1, len(P) - 1)]
        t = b - a; t.z = 0
        if t.length < 1e-6:
            t = Vector((1, 0, 0))
        t.normalize(); n = Vector((-t.y, t.x, 0))
        if 0 < i < len(P) - 1:
            t1 = p - a; t1.z = 0; t2 = b - p; t2.z = 0
            if t1.length > 1e-6 and t2.length > 1e-6:
                t1.normalize(); t2.normalize()
                n1 = Vector((-t1.y, t1.x, 0)); m = n1 + Vector((-t2.y, t2.x, 0))
                if m.length > 1e-6:
                    m.normalize(); n = m / max(m.dot(n1), 0.4)
        out.append(p + n * d)
    return out


def tracejado(pts, traco=3.0, vao=6.0):
    """corta a polilinha em pedaços (traço, vão) e devolve a lista de pedaços"""
    P = [Vector(p) for p in pts]; out = []; acc = 0.0; ligado = True; atual = [P[0]]
    for i in range(len(P) - 1):
        a, b = P[i], P[i + 1]; seg = (b - a).length; pos = 0.0
        while seg - pos > 1e-6:
            lim = (traco if ligado else vao) - acc
            passo = min(lim, seg - pos); pos += passo; acc += passo
            q = a.lerp(b, pos / seg)
            if ligado:
                atual.append(q)
            if acc >= (traco if ligado else vao) - 1e-6:
                if ligado and len(atual) > 1:
                    out.append(atual)
                ligado = not ligado; acc = 0.0; atual = [q]
    if ligado and len(atual) > 1:
        out.append(atual)
    return out


class Mapa:
    def __init__(self, caminho, estilo="maquete", semente=7, dz=0.02):
        """dz = 1 unidade de altura entre camadas (m). Com a câmera longe a precisão de profundidade é de milímetros SE o plano
        próximo da câmera for afastado (tb_cena.camera faz isso); todas as camadas ficam separadas de pelo menos 1 unidade."""
        self.d = json.load(open(caminho))
        self.E = ESTILOS[estilo]; self.estilo = estilo
        self.rnd = random.Random(semente)
        self.dz = dz; self.foco = None; self.foco_nomes = None; self.foco_ids = None; self.foco_extra = None; self.removidos_predios = 0; self.pilares_pulados = 0
        self._alturas()

    def pista_de(self, ponto, nome, profundidade=8):
        """ids das vias que formam a MESMA pista (mesmo nome, ligadas ponta com ponta) da via do nome mais perto do ponto:
        serve para pôr em foco só um sentido da avenida e deixar o outro apagado"""
        cand = [v for v in self.d["vias"] if v["nome"] == nome]
        ini = min(cand, key=lambda v: min(math.dist(p, ponto) for p in v["pts"]))
        pegos = {ini["id"]}; fila = [(ini, 0)]
        while fila:
            v, k = fila.pop(0)
            if k >= profundidade:
                continue
            for w in cand:
                if w["id"] in pegos:
                    continue
                if chave(w["pts"][0]) == chave(v["pts"][-1]) or chave(w["pts"][-1]) == chave(v["pts"][0]):
                    pegos.add(w["id"]); fila.append((w, k + 1))
        return pegos

    def ativa(self, v):
        """a via está em foco? (sem foco definido, todas estão)"""
        if self.foco_extra:   # uma segunda área em destaque (ex.: a vista aérea da Estaiada): vias principais e rampas, sem tráfego
            x, y, r, nomes = self.foco_extra
            if self._dentro(v["pts"], (x, y, r)) and (v["nome"] in nomes or base_tipo(v["tipo"]) in ("motorway", "trunk") or v["tipo"].endswith("_link")):
                return True
        if self.foco_ids is not None:
            return v["id"] in self.foco_ids
        if self.foco_nomes is not None and v["nome"] not in self.foco_nomes and base_tipo(v["tipo"]) not in ("motorway", "trunk") \
                and not v["tipo"].endswith("_link"):
            return False
        return self._dentro(v["pts"], self.foco) if self.foco else True

    def superficie(self, v, ativa=True):
        """altura do asfalto sobre o chão-base daquela via, em metros (vias mais importantes ficam por cima nos cruzamentos)"""
        o = ORDEM.get(base_tipo(v["tipo"]), 0)
        return (10 + 2 * o) * self.dz if ativa else (7 + 0.4 * o) * self.dz

    # ------------------------------------------------ alturas das pontes (Dijkstra a partir dos nós de ponte)
    def _alturas(self, rampa=0.055):
        viz = {}; h = {}
        for v in self.d["vias"]:
            if v["tipo"] in ("cycleway",):
                continue
            pts = v["pts"]
            for i in range(len(pts) - 1):
                a, b = chave(pts[i]), chave(pts[i + 1]); dist = math.dist(pts[i], pts[i + 1])
                if not v["ponte"]:
                    viz.setdefault(a, []).append((b, dist)); viz.setdefault(b, []).append((a, dist))
            if v["ponte"]:
                hb = ALT_PONTE * max(v["nivel"], 1)
                for p in pts:
                    h[chave(p)] = max(h.get(chave(p), 0.0), hb)
        fila = [(-hh, k) for k, hh in h.items()]; heapq.heapify(fila)
        while fila:
            nh, k = heapq.heappop(fila); hk = -nh
            if hk < h.get(k, 0.0) - 1e-6:
                continue
            for k2, dist in viz.get(k, []):
                h2 = hk - dist * rampa
                if h2 > h.get(k2, 0.0) + 1e-3:
                    h[k2] = h2; heapq.heappush(fila, (-h2, k2))
        self.h = h

    def z(self, p):
        return self.h.get(chave(p), 0.0)

    def pts3(self, pts, v=None):
        """pontos com a altura de ponte; com v, soma a altura do asfalto (é por onde os carros andam)"""
        s = self.superficie(v, self.ativa(v)) if v is not None else 0.0
        return [(p[0], p[1], self.z(p) + s) for p in pts]

    # ------------------------------------------------ peças
    def _poligono(self, pts, z, mat, nome, col="mapa"):
        bm = bmesh.new()
        vs = []
        for p in pts:
            if not vs or (Vector(p[:2]) - vs[-1].co.xy).length > 0.05:
                vs.append(bm.verts.new((p[0], p[1], z)))
        if len(vs) > 2 and (vs[0].co - vs[-1].co).length < 0.05:
            bm.verts.remove(vs.pop())
        if len(vs) < 3:
            bm.free(); return None
        try:
            bm.faces.new(vs)
        except ValueError:
            bm.free(); return None
        me = bpy.data.meshes.new(nome); bm.to_mesh(me); bm.free(); me.materials.append(mat)
        o = bpy.data.objects.new(nome, me); A.colecao(col).objects.link(o)
        return o

    def _dentro(self, pts, regiao):
        if not regiao:
            return True
        cx, cy, r = regiao
        return any((p[0] - cx) ** 2 + (p[1] - cy) ** 2 < r * r for p in pts)

    def chao(self, regiao=None):
        E = self.E
        x0, y0, x1, y1 = self.d["limites"]
        if regiao:
            cx, cy, r = regiao; x0, y0, x1, y1 = cx - r * 1.6, cy - r * 1.6, cx + r * 1.6, cy + r * 1.6
        x0 -= 3000; y0 -= 3000; x1 += 3000; y1 += 3000
        mat = A.mat_cor(E["chao"], 0.95, nome="tb_m_chao")
        if self.estilo == "real":
            mat = self._mat_ruido("tb_m_chao_real", E["chao"], 0.12, 0.02)
        self._poligono([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], -4 * self.dz, mat, "chao")

    def _mat_ruido(self, nome, cor, var=0.1, escala=0.05):
        """cor com manchas leves (estilo real)"""
        m = bpy.data.materials.get(nome)
        if m:
            return m
        m = bpy.data.materials.new(nome); m.use_nodes = True; nt = m.node_tree
        b = nt.nodes.get("Principled BSDF"); b.inputs["Roughness"].default_value = 0.92
        tc = nt.nodes.new("ShaderNodeTexCoord"); nz = nt.nodes.new("ShaderNodeTexNoise")
        nz.inputs["Scale"].default_value = escala; nz.inputs["Detail"].default_value = 8.0
        nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
        mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.blend_type = "MIX"
        c = A.hexrgb(cor); esc = tuple(max(0, k * (1 - var * 2)) for k in c[:3]) + (1,); cla = tuple(min(1, k * (1 + var * 2)) for k in c[:3]) + (1,)
        mx.inputs[6].default_value = esc; mx.inputs[7].default_value = cla
        nt.links.new(nz.outputs["Fac"], mx.inputs[0]); nt.links.new(mx.outputs[2], b.inputs["Base Color"])
        return m

    def verde_agua(self, regiao=None):
        E = self.E
        mv = A.mat_cor(E["verde"], 0.95, nome="tb_m_verde") if self.estilo != "real" else self._mat_ruido("tb_m_verde_real", E["verde"], 0.18, 0.08)
        for g in self.d["verde"]:
            if len(g["pts"]) > 3 and self._dentro(g["pts"], regiao):
                self._poligono(g["pts"], 0.0, mv, "verde")
        ma = A.mat_cor(E["agua"], 0.08, nome="tb_m_agua")
        for a in self.d["agua"]:
            if self._dentro(a, regiao):
                self._poligono(a, 2 * self.dz, ma, "agua")
        for r in self.d["rio"]:
            if r["nome"] == "Rio Pinheiros":
                A.fita(r["pts"], 78.0, ma, 3 * self.dz, "rio", "mapa")
                A.fita(r["pts"], 92.0, mv, 1 * self.dz, "margem", "mapa")

    def vias(self, regiao=None, faixas_pintadas=True):
        E = self.E; u = self.dz
        m_asf1 = A.mat_cor(E["asf1"], 0.82, nome="tb_m_asf1"); m_asf2 = A.mat_cor(E["asf2"], 0.85, nome="tb_m_asf2")
        m_apag = A.mat_cor(E.get("via_apagada", E["asf2"]), 0.9, nome="tb_m_apagada")
        m_calc = A.mat_cor(E["calcada"], 0.9, nome="tb_m_calcada"); m_ciclo = A.mat_cor(E["ciclo"], 0.8, nome="tb_m_ciclo")
        m_tinta = A.mat_cor(E["tinta"], 0.5, nome="tb_m_tinta"); m_amar = A.mat_cor(E["amarelo"], 0.5, nome="tb_m_amarelo")
        m_ponte = A.mat_cor(E["ponte"], 0.85, nome="tb_m_ponte")
        self.vias_feitas = []
        for v in sorted(self.d["vias"], key=lambda v: ORDEM.get(base_tipo(v["tipo"]), 0)):
            if not self._dentro(v["pts"], regiao):
                continue
            t = base_tipo(v["tipo"]); w = largura_via(v); P = self.pts3(v["pts"])
            ativa = self.ativa(v); dz = self.superficie(v, ativa)
            if v["tipo"] == "cycleway":
                A.fita(P, w, m_ciclo, 7 * u, "ciclovia", "mapa"); continue
            principal = t in PRINCIPAIS
            if not ativa:  # fora de foco: só o desenho da rua, em cinza claro, sem pintura
                A.fita(P, w, m_apag, dz, v["tipo"], "mapa")
                continue
            if not principal:
                A.fita(P, w + 3.6, m_calc, 5 * u, "calcada", "mapa")
            A.fita(P, w, m_asf1 if principal else m_asf2, dz, v["tipo"], "mapa")
            alta = max(p[2] for p in P) > 0.5
            if alta:  # tabuleiro de ponte: saia e pilares
                self._tabuleiro(P, w, m_ponte)
            if faixas_pintadas and principal and w >= 6:
                n = max(1, round(w / LARG_FAIXA.get(t, 3.3)))
                for s in (-1, 1):
                    A.fita(offset(P, s * (w / 2 - 0.35)), 0.2, m_tinta, dz + u, "borda", "mapa")
                if v["mao_unica"]:
                    for i in range(1, n):
                        d = -w / 2 + i * w / n
                        for pedaco in tracejado(offset(P, d), 3.0, 7.0):
                            A.fita(pedaco, 0.18, m_tinta, dz + u, "traco", "mapa")
                else:
                    for s in (-1, 1):
                        A.fita(offset(P, s * 0.18), 0.14, m_amar, dz + u, "eixo", "mapa")
            self.vias_feitas.append(v)

    # ------------------------------------------------ espaço: o que está em cima do quê
    def _amostras(self, passo=4.0):
        """pontos (x, y, z, meia_largura) ao longo das vias de carro, no centro e nas bordas, com grade de 8 m para busca rápida"""
        if getattr(self, "_grade_vias", None) is not None:
            return self._grade_vias
        g = {}
        for v in self.d["vias"]:
            if v["tipo"] == "cycleway":
                continue
            w = largura_via(v); P = self.pts3(v["pts"]); Q = [Vector(p) for p in P]
            lados = [0.0] if w < 6 else [0.0, w / 2 - 0.4, -(w / 2 - 0.4)]
            L = [offset(P, d) for d in lados]
            for pts in L:
                for i in range(len(pts) - 1):
                    a, b = pts[i], pts[i + 1]; seg = (b - a).length; n = max(1, int(seg // passo))
                    for k in range(n + 1):
                        q = a.lerp(b, k / n)
                        g.setdefault((int(q.x // 8), int(q.y // 8)), []).append((q.x, q.y, q.z, w / 2))
        self._grade_vias = g
        return g

    def _perto(self, x, y, raio):
        g = self._amostras(); r = int(raio // 8) + 1; cx, cy = int(x // 8), int(y // 8)
        for dx in range(-r, r + 1):
            for dy in range(-r, r + 1):
                for q in g.get((cx + dx, cy + dy), []):
                    yield q

    @staticmethod
    def _dentro_poly(x, y, pts):
        d = False; n = len(pts)
        for i in range(n):
            x1, y1 = pts[i]; x2, y2 = pts[(i + 1) % n]
            if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1 + 1e-12) + x1:
                d = not d
        return d

    def verifica(self):
        """vão livre sob os viadutos: para cada ponto elevado, a distância entre a parte de baixo do tabuleiro e o teto de um caminhão (4,4 m)
        da via de baixo que passa por ali. Imprime quantos pontos ficam baixos demais."""
        ruins = []; total = 0
        for chave_, lst in self._amostras().items():
            for (x, y, z, hw) in lst:
                if z < 3.0:
                    continue
                total += 1
                for (x2, y2, z2, hw2) in self._perto(x, y, 6.0):
                    if z2 < 1.5 and (x - x2) ** 2 + (y - y2) ** 2 < (hw2 + 0.5) ** 2:
                        vao = (z - 1.3) - (z2 + 4.4)
                        if vao < 0:
                            ruins.append((x, y, round(vao, 2)))
                        break
        print(f"[vão] {len(ruins)} de {total} pontos de viaduto passam baixos demais sobre uma via de baixo (menos de 4,4 m); piores:", sorted(ruins, key=lambda r: r[2])[:5])
        print(f"[espaço] prédios removidos por estarem em cima de uma via: {self.removidos_predios}; pilares que cairiam na pista e foram pulados: {self.pilares_pulados}")
        return ruins

    def _pilar_livre(self, q):
        """o pilar não pode cair dentro da faixa de uma via mais baixa (senão os carros passam por dentro dele)"""
        for (x2, y2, z2, hw2) in self._perto(q.x, q.y, 14.0):
            if z2 < q.z - 3.0 and (q.x - x2) ** 2 + (q.y - y2) ** 2 < (hw2 + 2.2) ** 2:
                self.pilares_pulados += 1
                return False
        return True

    def _tabuleiro(self, P, w, mat, passo=28.0):
        bm = bmesh.new()
        L = offset(P, w / 2 + 0.3); R = offset(P, -w / 2 - 0.3)
        for i in range(len(P) - 1):
            if P[i][2] < 0.5 and P[i + 1][2] < 0.5:
                continue
            for lado in (L, R):
                a, b = lado[i], lado[i + 1]
                vs = [bm.verts.new(a + Vector((0, 0, 0.9))), bm.verts.new(b + Vector((0, 0, 0.9))),
                      bm.verts.new(b - Vector((0, 0, 1.2))), bm.verts.new(a - Vector((0, 0, 1.2)))]
                bm.faces.new(vs)
        acc = 0.0
        for i in range(len(P) - 1):
            a, b = Vector(P[i]), Vector(P[i + 1]); seg = (b - a).length
            while acc < seg:
                q = a.lerp(b, acc / max(seg, 1e-6))
                if q.z > 3.0 and self._pilar_livre(q):
                    bmesh.ops.create_cube(bm, size=1.0, matrix=__import__("mathutils").Matrix.Translation((q.x, q.y, (q.z - 1.2) / 2)) @
                                          __import__("mathutils").Matrix.Diagonal((1.8, 1.8, max(q.z - 1.2, 0.1), 1.0)))
                acc += passo
            acc -= seg
        me = bpy.data.meshes.new("tabuleiro"); bm.to_mesh(me); bm.free(); me.materials.append(mat)
        o = bpy.data.objects.new("tabuleiro", me); A.colecao("mapa").objects.link(o)

    def _predio_sobre_via(self, pts, alt):
        """a planta do prédio cobre um ponto de via de carro mais baixo que o topo dele? (erro de mapeamento ou prédio em cima do viaduto)"""
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
        raio = max(max(xs) - min(xs), max(ys) - min(ys)) / 2 + 1
        for (x, y, z, hw) in self._perto(cx, cy, raio):
            if z < alt - 1.5 and min(xs) - 0.5 < x < max(xs) + 0.5 and min(ys) - 0.5 < y < max(ys) + 0.5 and self._dentro_poly(x, y, pts):
                return True
        return False

    def predios(self, regiao=None, alt_padrao=(7, 24)):
        E = self.E
        m_par = A.mat_cor(E["parede"], 0.8, nome="tb_m_parede"); m_teto = A.mat_cor(E["teto"], 0.85, nome="tb_m_teto")
        m_torre = A.mat_cor(E["torre"], 0.25, 0.1, nome="tb_m_torre")
        if self.estilo == "noite":
            m_torre = self._mat_janelas("tb_m_janelas", E["torre"])
            m_par = self._mat_janelas("tb_m_janelas2", E["parede"], 0.6)
        bm = bmesh.new()
        for p in self.d["predios"]:
            if not self._dentro(p["pts"], regiao):
                continue
            pts = p["pts"]
            if p["tipo"] in ("roof", "carport"):
                continue
            alt = p["alt"] or self.rnd.uniform(*alt_padrao) * (0.45 if p["tipo"] in ("house", "residential", "garage") else 1.0)
            if self._predio_sobre_via(pts, alt):
                self.removidos_predios += 1
                continue
            vs = [bm.verts.new((x, y, 0.0)) for x, y in pts]
            try:
                f = bm.faces.new(vs)
            except ValueError:
                continue
            f.normal_update()
            if f.normal.z < 0:
                f.normal_flip()
            ext = bmesh.ops.extrude_face_region(bm, geom=[f])
            topo = [g for g in ext["geom"] if isinstance(g, bmesh.types.BMFace)]
            for v in [g for g in ext["geom"] if isinstance(g, bmesh.types.BMVert)]:
                v.co.z = alt
            torre = alt > 45
            for fc in topo:
                fc.material_index = 1
            for fc in {fc for v in vs for fc in v.link_faces}:
                if fc not in topo and abs(fc.normal.z) < 0.5:
                    fc.material_index = 2 if torre else 0
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
        me = bpy.data.meshes.new("predios"); bm.to_mesh(me); bm.free()
        for m in (m_par, m_teto, m_torre):
            me.materials.append(m)
        o = bpy.data.objects.new("predios", me); A.colecao("mapa").objects.link(o)
        return o

    def _mat_janelas(self, nome, cor, forca=1.0):
        """parede com janelas acesas (noite): grade de luz pelas coordenadas do objeto"""
        m = bpy.data.materials.get(nome)
        if m:
            return m
        m = bpy.data.materials.new(nome); m.use_nodes = True; nt = m.node_tree
        b = nt.nodes.get("Principled BSDF"); b.inputs["Base Color"].default_value = A.hexrgb(cor); b.inputs["Roughness"].default_value = 0.6
        tc = nt.nodes.new("ShaderNodeTexCoord")
        bk = nt.nodes.new("ShaderNodeTexBrick"); bk.inputs["Scale"].default_value = 0.45
        bk.inputs["Mortar Size"].default_value = 0.35; bk.inputs["Color1"].default_value = A.hexrgb("#ffd79a")
        bk.inputs["Color2"].default_value = A.hexrgb("#1a2030"); bk.inputs["Mortar"].default_value = A.hexrgb("#000000")
        nt.links.new(tc.outputs["Object"], bk.inputs["Vector"])
        nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 0.6
        nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
        mr = nt.nodes.new("ShaderNodeMapRange"); mr.inputs[1].default_value = 0.52; mr.inputs[2].default_value = 0.56
        nt.links.new(nz.outputs["Fac"], mr.inputs[0])
        mul = nt.nodes.new("ShaderNodeMix"); mul.data_type = "RGBA"; mul.blend_type = "MULTIPLY"; mul.inputs[0].default_value = 1.0
        nt.links.new(bk.outputs["Color"], mul.inputs[6]); nt.links.new(mr.outputs[0], mul.inputs[7])
        nt.links.new(mul.outputs[2], b.inputs["Emission Color"]); b.inputs["Emission Strength"].default_value = forca
        return m

    def trilhos(self, regiao=None):
        E = self.E
        m_brita = A.mat_cor(E["trilho"], 0.95, nome="tb_m_brita"); m_aco = A.mat_cor("#b9bec4", 0.3, 0.8, nome="tb_m_trilho")
        m_mono = A.mat_cor(E["monotrilho"], 0.6, nome="tb_m_mono"); m_conc = A.mat_cor(E["ponte"], 0.85, nome="tb_m_ponte")
        for t in self.d["trilhos"]:
            if not self._dentro(t["pts"], regiao):
                continue
            if t["tipo"] == "rail":
                A.fita(t["pts"], 4.2, m_brita, 6 * self.dz, "linha9", "mapa")
                for s in (-0.75, 0.75):
                    A.fita(offset(t["pts"], s), 0.12, m_aco, 8 * self.dz, "trilho", "mapa")
            elif t["tipo"] == "monorail":
                P = [(p[0], p[1], 13.0) for p in t["pts"]]
                A.fita(P, 1.6, m_mono, 0.0, "linha17", "mapa")
                self._tabuleiro(P, 0.8, m_conc, 30.0)

    def estaiada(self):
        """torre em X da Ponte Estaiada (138 m) no cruzamento dos dois tabuleiros estaiados, com os cabos"""
        dk = [v for v in self.d["vias"] if v.get("estaiada")]
        if len(dk) < 2:
            return None
        P1, P2 = [Vector(p) for p in dk[0]["pts"]], [Vector(p) for p in dk[1]["pts"]]
        best = None
        for a in P1:
            for b in P2:
                d = (a - b).length
                if best is None or d < best[0]:
                    best = (d, (a + b) / 2)
        c = best[1]
        m = A.Malha("estaiada"); conc = A.mat_cor("#e9e6df" if self.estilo != "noite" else "#56607a", 0.6, nome="tb_m_torre_est")
        # duas pernas que se cruzam (X), no plano perpendicular à direção média dos tabuleiros
        dmed = (P1[-1] - P1[0]).normalized() + (P2[-1] - P2[0]).normalized()
        ang = math.atan2(dmed.y, dmed.x) + math.pi / 2
        import mathutils
        for s in (-1, 1):
            base = Vector((s * 13, 0, 0)); topo = Vector((-s * 6, 0, 138))
            meio = (base + topo) / 2; L = (topo - base).length
            inc = math.atan2(topo.x - base.x, topo.z - base.z)
            M = (mathutils.Matrix.Translation(meio) @ mathutils.Matrix.Rotation(inc, 4, "Y") @ mathutils.Matrix.Diagonal((7.0, 5.0, L, 1)))
            vs = bmesh.ops.create_cube(m.bm, size=1.0, matrix=M)["verts"]; m._pinta(vs, conc)
        o = bpy.data.objects.new("estaiada", m.malha()); A.colecao("mapa").objects.link(o)
        o.location = (c.x, c.y, 0); o.rotation_euler.z = ang
        # cabos (vão até pontos dos tabuleiros a até 150 m do mastro)
        cabo = A.mat_cor("#f4f2ee" if self.estilo != "noite" else "#8fa6d8", 0.4, emis=0.0 if self.estilo != "noite" else 0.8, nome="tb_m_cabo")
        bm = bmesh.new()
        for v in dk:
            P = self.pts3(v["pts"]); dens = []
            for i in range(len(P) - 1):
                a, b = Vector(P[i]), Vector(P[i + 1])
                for k in range(8):
                    q = a.lerp(b, k / 8)
                    dist = (q.xy - c.xy).length
                    if 25 < dist < 150:
                        dens.append((dist, q))
            dens.sort(key=lambda x: x[0])
            for j, (dist, q) in enumerate(dens[::3][:28]):
                ztop = 70 + 62 * min(dist / 150, 1)
                topo = Vector((c.x, c.y, ztop)); dirv = (q + Vector((0, 0, 1)) - topo)
                L = dirv.length
                M = (mathutils.Matrix.Translation((topo + q + Vector((0, 0, 1))) / 2) @ dirv.to_track_quat("Z", "Y").to_matrix().to_4x4()
                     @ mathutils.Matrix.Diagonal((0.18, 0.18, L, 1)))
                bmesh.ops.create_cube(bm, size=1.0, matrix=M)
        me = bpy.data.meshes.new("cabos"); bm.to_mesh(me); bm.free(); me.materials.append(cabo)
        oc = bpy.data.objects.new("cabos", me); A.colecao("mapa").objects.link(oc)
        self.torre = c
        return o

    def monta(self, regiao=None, faixas_pintadas=True, foco=None, nomes=None):
        """foco = (x, y, raio): só as vias dessa área recebem asfalto escuro, pintura e trânsito; o resto vira desenho cinza claro.
        nomes = lista de nomes de via (ex.: ["Marginal Pinheiros (Expressa)"]): dentro do foco, só essas ficam em destaque"""
        self.foco = foco; self.foco_nomes = set(nomes) if nomes else None
        self.chao(regiao); self.verde_agua(regiao); self.vias(regiao, faixas_pintadas); self.trilhos(regiao)
        self.predios(regiao); self.estaiada()
        return self
