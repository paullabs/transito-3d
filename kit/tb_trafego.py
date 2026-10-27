"""Trânsito Brasil 3D: faixas de rodagem e simulação de tráfego (modelo IDM: cada motorista acelera até a sua velocidade
desejada e freia para manter distância de quem vai na frente). É o mesmo modelo que explica o "efeito sanfona".
    import tb_trafego as T
    tr = T.Trafego(mapa, regiao=(x, y, r), cor="tipo"|"velocidade");  tr.aquece(30);  tr.aplica()      # quadro parado
    for f in range(n): tr.passo(1/24); tr.aplica(); render...                                         # animação
Regras que evitam carro atravessando carro (conferidas por tb_colisao.py):
  - faixas que andam coladas uma na outra (mão dupla desenhada duas vezes, rampa sobre a pista) são fundidas numa só;
  - só circula trânsito em faixas que NUNCA cruzam nem se juntam com outra do mesmo nível (conjunto independente: expressas primeiro,
    depois avenidas, depois ruas; a faixa que bateria numa já aceita fica vazia). Assim dois carros de faixas diferentes não se encontram;
  - dentro da faixa vale o modelo IDM (distância de segurança), e o carro novo só entra se houver vão, olhando o comprimento dos DOIS;
  - as motos andam no corredor entre as duas faixas da esquerda; as duas faixas ao lado dele só recebem veículos estreitos.
"""
import math, random
from mathutils import Vector
import tb_assets as A
import tb_mapa as MP

# frota de São Paulo (aproximada, para o visual): carros na maioria branco, prata, cinza e preto
CORES_CARRO = [("#f2f2ef", 30), ("#b9bcc0", 20), ("#7d8186", 16), ("#1d2024", 15), ("#a3171d", 7), ("#24467e", 5),
               ("#5a3d2b", 2), ("#c9b48a", 3), ("#2f5d3a", 2)]
# modo "tipo" (didático): a cor diz a classe do veículo e se vê de longe sobre o asfalto escuro
COR_TIPO = {"carro": ("#f4f4f1", "#c9ccd1"), "taxi": ("#ffd21f", "#202020"), "onibus": ("#16b85b", "#ffffff"),
            "caminhao": ("#ff7a1a", "#ffffff"), "moto": ("#ff2d75", "#fff1a8"), "emergencia": ("#ffffff", "#e0242c")}
CLASSE = {"hatch": "carro", "sedan": "carro", "suv": "carro", "picape": "carro", "taxi": "taxi", "viatura": "emergencia",
          "ambulancia": "emergencia", "moto": "moto", "moto_entrega": "moto", "onibus": "onibus", "articulado": "onibus",
          "vuc": "caminhao", "toco": "caminhao", "cavalo": "caminhao"}
# modo "velocidade": a cor é a velocidade em relação à da pista
ESCALA_VEL = [(0.0, "#c40d2c"), (0.18, "#ff3b30"), (0.45, "#ffc21a"), (0.75, "#22c55e"), (1.0, "#22c55e")]
VEL_VERDE = 0.55  # fração da velocidade da pista (70 km/h) que já conta como "andando bem" (verde)
MIX_VIA = {  # (modelo, peso) por tipo de via
    "expressa": [("hatch", 26), ("sedan", 22), ("suv", 18), ("picape", 6), ("taxi", 2), ("vuc", 4), ("toco", 4), ("cavalo", 4), ("onibus", 2)],
    "avenida": [("hatch", 30), ("sedan", 22), ("suv", 16), ("picape", 4), ("taxi", 5), ("vuc", 4), ("onibus", 8), ("toco", 2), ("ambulancia", 0.4), ("viatura", 0.6)],
    "rua": [("hatch", 40), ("sedan", 24), ("suv", 18), ("picape", 4), ("taxi", 3), ("vuc", 2)],
    "corredor": [("moto", 45), ("moto_entrega", 55)],
}
PRIO = {"corredor": 4, "expressa": 3, "avenida": 2, "rua": 1}
VEL_MAX = {"motorway": 70, "trunk": 60, "primary": 50, "secondary": 50, "tertiary": 40, "residential": 30, "service": 20,
           "living_street": 20, "unclassified": 30, "busway": 50}
ONIBUS_CORES = [("#2f9e57", "#f2f2ee"), ("#1f6fc0", "#f2f2ee"), ("#d8262b", "#f2f2ee"), ("#f2b705", "#1f2a36"), ("#7b3fa0", "#f2f2ee")]
TIPOS_TRAFEGO = {"motorway", "motorway_link", "trunk", "trunk_link", "primary", "primary_link", "secondary", "secondary_link",
                 "tertiary", "residential", "busway"}


def esc_de(modelo, esc):
    """escala de exagero (carros um pouco maiores para ler de cima); a moto nunca passa do tamanho real, senão não cabe no corredor"""
    return min(esc, 1.0) if modelo.startswith("moto") else esc


def sorteia(rnd, lista):
    tot = sum(p for _, p in lista); r = rnd.uniform(0, tot)
    for k, p in lista:
        r -= p
        if r <= 0:
            return k
    return lista[-1][0]


def cor_velocidade(razao):
    razao = min(max(razao, 0.0), 1.0)
    for (a, ca), (b, cb) in zip(ESCALA_VEL, ESCALA_VEL[1:]):
        if razao <= b:
            t = (razao - a) / max(b - a, 1e-6)
            return tuple(x + (y - x) * t for x, y in zip(A.hexrgb(ca), A.hexrgb(cb)))
    return A.hexrgb(ESCALA_VEL[-1][1])


def sat(a, b, folga=0.0):
    """duas caixas orientadas (cx, cy, z, yaw, meio_comprimento, meia_largura) se cortam? folga > 0 exige distância mínima"""
    for c in (a, b):
        ux, uy = math.cos(c[3]), math.sin(c[3])
        for ax in ((ux, uy), (-uy, ux)):
            def proj(k):
                kx, ky = math.cos(k[3]), math.sin(k[3])
                return k[0] * ax[0] + k[1] * ax[1], abs(kx * ax[0] + ky * ax[1]) * k[4] + abs(-ky * ax[0] + kx * ax[1]) * k[5]
            pa, ra = proj(a); pb, rb = proj(b)
            if abs(pa - pb) > ra + rb + folga:
                return False
    return True


class Faixa:
    def __init__(self, pts, tipo, vmax, classe, nome=""):
        self.P = [Vector(p) for p in pts]; self.tipo = tipo; self.vmax = vmax / 3.6; self.classe = classe; self.nome = nome
        self.cum = [0.0]
        for i in range(len(self.P) - 1):
            self.cum.append(self.cum[-1] + (self.P[i + 1] - self.P[i]).length)
        self.L = self.cum[-1]
        self.dens = None  # densidade própria desta faixa (None = a do tráfego)
        self.restrita = False  # ao lado do corredor das motos: só veículos estreitos
        self.rmin = self._raio_minimo()
        self.raio = 0.45 if classe == "corredor" else 1.6
        self.veics = []  # ordenados do mais à frente para o mais atrás
        self.limites = []  # (s0, s1, v, t0, t1): trecho lento (gargalo) num intervalo de tempo

    def _raio_minimo(self, passo=6.0):
        """menor raio de curva da faixa (m): veículo comprido é uma caixa dura e varre a faixa do lado nas curvas fechadas"""
        n = max(3, int(self.L // passo)); P = [self._ponto0(self.L * k / n) for k in range(n + 1)]
        rmin = 1e9
        for i in range(1, len(P) - 1):
            a, b = P[i] - P[i - 1], P[i + 1] - P[i]; a.z = b.z = 0
            if a.length < 1e-6 or b.length < 1e-6:
                continue
            ang = a.angle(b, 0.0)
            if ang > 1e-4:
                rmin = min(rmin, (a.length + b.length) / 2 / ang)
        return rmin

    def _ponto0(self, s):
        return self.ponto(s)

    def ponto(self, s):
        """ponto da faixa em s metros; passando das pontas, continua em linha reta na direção do primeiro/último trecho
        (antes o ponto ficava preso na ponta e o carro girava e empilhava ali)"""
        if s < 0.0 or s > self.L:
            if s < 0.0:
                a, b = self.P[0], self.P[1]; d = (a - b); base = a; extra = -s
            else:
                a, b = self.P[-2], self.P[-1]; d = (b - a); base = b; extra = s - self.L
            return base + d.normalized() * extra
        lo, hi = 0, len(self.cum) - 1
        while hi - lo > 1:
            m = (lo + hi) // 2
            if self.cum[m] <= s: lo = m
            else: hi = m
        seg = max(self.cum[hi] - self.cum[lo], 1e-6)
        return self.P[lo].lerp(self.P[hi], (s - self.cum[lo]) / seg)

    def pose(self, s, meia=2.0):
        a, b = self.ponto(s - meia), self.ponto(s + meia)
        d = b - a
        yaw = math.atan2(d.y, d.x) if d.xy.length > 1e-6 else 0.0
        pitch = -math.atan2(d.z, max(d.xy.length, 1e-6))
        return self.ponto(s), yaw, pitch


class Veic:
    _n = 0

    def __init__(self, modelo, rnd, vmax, esc, folga=1.0, tempo=1.0):
        Veic._n += 1; self.id = Veic._n
        self.modelo = modelo; self.esc = esc_de(modelo, esc)
        self.L = (A.COMPRIMENTO[modelo] + (14.5 if modelo == "cavalo" else 0.0)) * self.esc
        self.v0 = vmax * rnd.uniform(0.88, 1.06) * (0.85 if modelo in ("toco", "cavalo", "onibus", "vuc") else 1.0)
        if modelo.startswith("moto"):
            self.v0 = vmax * rnd.uniform(1.0, 1.2)
        self.T = rnd.uniform(0.95, 1.5) * tempo * (0.5 if modelo.startswith("moto") else 1.0)
        self.a = 1.4 if modelo not in ("toco", "cavalo", "onibus") else 0.8
        self.b = 2.2; self.s0 = (2.2 if not modelo.startswith("moto") else 1.2) * folga
        self.s = 0.0; self.v = self.v0 * 0.7; self.acc = 0.0; self.freio = 0.0; self.nasceu = None
        self.espera = 0.0; self.evento = None; self.hist = []
        self.obj = None; self.reb = None


class Trafego:
    def __init__(self, mapa, regiao=None, semente=3, fluxo=1.0, motos=True, escala_veic=1.0, visual=True, cor="tipo", dens=1.0, enche=True, folga=1.0, tempo=1.0, mix=None, reacao=0.0):
        self.mapa = mapa; self.regiao = regiao; self.rnd = random.Random(semente); self.rnd_cor = random.Random(semente + 1000); self.fluxo = fluxo; self.dens = dens
        self.esc = escala_veic; self.t = 0.0; self.livres = {}; self.faixas = []; self.visual = visual; self.modo_cor = cor
        self.removidos = 0; self.esperas = 0; self.grava = None; self.xt = []
        self.reacao = reacao   # s: o motorista freia com o que viu há "reacao" segundos (atraso de reação: é ele que amplifica a freada para trás)
        self.folga = folga; self.tempo = tempo  # folga: vão mínimo entre carros parados (x); tempo: distância de seguimento (x)
        self.mix = mix or MIX_VIA
        self._monta(motos)
        self._dedup()
        self._independentes()
        if enche:
            self._enche()

    # ------------------------------------------------ faixas
    def _ativa(self, v):
        if getattr(self.mapa, "foco_ids", None) is not None:   # tráfego só na pista escolhida (as outras áreas em destaque ficam sem carro)
            return v["id"] in self.mapa.foco_ids
        if getattr(self.mapa, "foco", None):
            return self.mapa.ativa(v)
        r = self.regiao and (self.regiao[0], self.regiao[1], self.regiao[2] * 1.4)
        return self.mapa._dentro(v["pts"], r)

    def _monta(self, motos):
        dirigidas = []
        for v in self.mapa.d["vias"]:
            if v["tipo"] not in TIPOS_TRAFEGO or not self._ativa(v):
                continue
            w = MP.largura_via(v); P = self.mapa.pts3(v["pts"], v)
            t = MP.base_tipo(v["tipo"])
            n = max(1, round(w / MP.LARG_FAIXA.get(t, 3.3)))
            vm = VEL_MAX.get(t, 40)
            try:
                vm = float(v["velmax"].split()[0]) if v.get("velmax") else vm
            except ValueError:
                pass
            classe = "expressa" if t in ("motorway", "trunk") else "avenida" if t in ("primary", "secondary", "busway") else "rua"
            if v["mao_unica"]:
                dirigidas.append(dict(P=P, n=n, w=w, tipo=v["tipo"], vm=vm, classe=classe, nome=v["nome"]))
            else:
                lw = w / n; nd = max(1, n // 2)
                dirigidas.append(dict(P=P, n=nd, w=nd * lw, tipo=v["tipo"], vm=vm, classe=classe, nome=v["nome"], lado=True))
                dirigidas.append(dict(P=P[::-1], n=nd, w=nd * lw, tipo=v["tipo"], vm=vm, classe=classe, nome=v["nome"], lado=True))
        # encadeia trechos que continuam (mesmo número de faixas)
        inicio = {}
        for i, d in enumerate(dirigidas):
            inicio.setdefault(MP.chave(d["P"][0]), []).append(i)
        tem_pred = set()
        for i, d in enumerate(dirigidas):
            for j in inicio.get(MP.chave(d["P"][-1]), []):
                if dirigidas[j]["n"] == d["n"] and j != i:
                    tem_pred.add(j)
        usado = set()
        ordem = [i for i in range(len(dirigidas)) if i not in tem_pred] + list(range(len(dirigidas)))
        for i in ordem:
            if i in usado:
                continue
            cadeia = [i]; usado.add(i)
            while True:
                d = dirigidas[cadeia[-1]]
                cand = [j for j in inicio.get(MP.chave(d["P"][-1]), []) if j not in usado and dirigidas[j]["n"] == d["n"]]
                if not cand:
                    break
                cand.sort(key=lambda j: (dirigidas[j]["nome"] != d["nome"], dirigidas[j]["tipo"] != d["tipo"]))
                cadeia.append(cand[0]); usado.add(cand[0])
            d0 = dirigidas[cadeia[0]]; n = d0["n"]
            for k in range(n):
                pts = []
                for j in cadeia:
                    d = dirigidas[j]
                    off = (-d["w"] / 2 + (k + 0.5) * d["w"] / n) if not d.get("lado") else -(k + 0.5) * d["w"] / n
                    seg = MP.offset(d["P"], off)
                    pts += seg if not pts else seg[1:]
                if len(pts) > 1:
                    fx = Faixa(pts, d0["tipo"], d0["vm"], d0["classe"], d0["nome"])
                    if motos and d0["classe"] == "expressa" and n >= 3 and not d0.get("lado") and k >= n - 2:
                        fx.restrita = True; fx.raio = 1.15
                    self.faixas.append(fx)
            if motos and d0["classe"] == "expressa" and n >= 3 and not d0.get("lado"):
                pts = []
                for j in cadeia:
                    d = dirigidas[j]
                    seg = MP.offset(d["P"], -d["w"] / 2 + (n - 1) * d["w"] / n)  # fronteira entre as duas faixas da esquerda
                    pts += seg if not pts else seg[1:]
                self.faixas.append(Faixa(pts, d0["tipo"], d0["vm"] + 15, "corredor", d0["nome"] + " (corredor)"))
        self.faixas = [f for f in self.faixas if f.L > 15]

    def _dedup(self):
        """funde faixas que andam coladas (mesma linha desenhada duas vezes, rampa colada na pista): fica a mais longa"""
        celula = 3.0; grade = {}; amostras = []
        for i, f in enumerate(self.faixas):
            n = max(2, int(f.L // 5)); pts = [f.ponto(f.L * k / n) for k in range(n + 1)]
            amostras.append(pts)
            for p in pts:
                grade.setdefault((int(p.x // celula), int(p.y // celula)), []).append((i, p))
        cobre = []
        for i, pts in enumerate(amostras):
            c = {}
            for p in pts:
                vistos = set(); cx, cy = int(p.x // celula), int(p.y // celula)
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        for j, q in grade.get((cx + dx, cy + dy), []):
                            if j != i and j not in vistos and abs(p.z - q.z) < 2.5 and (p.xy - q.xy).length < 1.8:
                                vistos.add(j); c[j] = c.get(j, 0) + 1
            cobre.append(c)
        cai = set()
        for i in sorted(range(len(self.faixas)), key=lambda i: self.faixas[i].L):
            if i in cai:
                continue
            for j, cnt in cobre[i].items():
                if j not in cai and cnt / len(amostras[i]) > 0.5:
                    cai.add(i); break
        n0 = len(self.faixas)
        self.faixas = [f for i, f in enumerate(self.faixas) if i not in cai]
        print(f"[trafego] {len(self.faixas)} faixas ({n0 - len(self.faixas)} coladas em outra, fundidas), {sum(f.L for f in self.faixas) / 1000:.1f} km de faixa")

    def _independentes(self):
        """fica só um conjunto de faixas que nunca se encontram: testa, ponto a ponto (a cada 2 m), se alguma outra já aceita
        passa a menos de (raio de uma + raio da outra) no mesmo nível. Cruzamento, junção de rampa e laço que cruza a si mesmo caem aqui."""
        celula = 6.0; grade = {}; aceitas = []
        ordem = sorted(self.faixas, key=lambda f: (-PRIO[f.classe], -f.L))
        recusadas = 0
        for f in ordem:
            n = max(2, int(f.L // 2.0)); amostras = [(f.ponto(f.L * k / n), f.L * k / n) for k in range(n + 1)]
            ruim = False
            for p, sp in amostras:
                cx, cy = int(p.x // celula), int(p.y // celula)
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        for g, q, sq in grade.get((cx + dx, cy + dy), ()):
                            lim = f.raio + g.raio
                            if abs(p.z - q.z) < 6.5 and (p.x - q.x) ** 2 + (p.y - q.y) ** 2 < lim * lim:
                                ruim = True; break
                        if ruim: break
                    if ruim: break
                if ruim: break
            if not ruim:  # laço que cruza a si mesmo
                visto = {}
                for p, sp in amostras:
                    visto.setdefault((int(p.x // 8), int(p.y // 8)), []).append((p, sp))
                for p, sp in amostras:
                    cx, cy = int(p.x // 8), int(p.y // 8)
                    for dx in (-1, 0, 1):
                        for dy in (-1, 0, 1):
                            for q, sq in visto.get((cx + dx, cy + dy), ()):
                                if abs(sp - sq) > 40 and abs(p.z - q.z) < 3.0 and (p.xy - q.xy).length < 3.4:
                                    ruim = True; break
                            if ruim: break
                        if ruim: break
                    if ruim: break
            if ruim:
                recusadas += 1; continue
            aceitas.append(f)
            for p, sp in amostras:
                grade.setdefault((int(p.x // celula), int(p.y // celula)), []).append((f, p, sp))
        self.faixas = aceitas
        print(f"[trafego] {len(aceitas)} faixas sem encontro com outra ({recusadas} ficam vazias para não haver carro atravessando carro)")

    # ------------------------------------------------ caixas (para colisão e prioridade)
    @staticmethod
    def k_saida(f, ve, dist=6.0):
        """1 = tamanho normal; cai a 0 nos últimos 6 m antes da ponta da faixa (o carro encolhe e some em vez de atravessar o que cruza ali)"""
        fim = ve.s + ve.L / 2 - (f.L - dist)
        if fim <= 0:
            return 1.0
        q = min(fim / dist, 1.0)
        return 1 - q * q * (3 - 2 * q)

    def caixas(self, f, ve, frente=0.0):
        """caixas (cx, cy, z, yaw, meio_comprimento, meia_largura) do veículo; frente > 0 alonga a primeira para a frente"""
        e = ve.esc * max(self.k_saida(f, ve), 0.02)
        if ve.modelo == "cavalo":
            sc = ve.s + ve.L / 2 - 2.7 * e
            p, yaw, _ = f.pose(sc)
            ux, uy = math.cos(yaw), math.sin(yaw)
            c1 = (p.x + ux * frente / 2, p.y + uy * frente / 2, p.z, yaw, 2.7 * e + frente / 2, 1.25 * e)
            pino = sc - 1.4 * e
            a, b = f.ponto(pino), f.ponto(pino - 11.0)
            d = a - b; yr = math.atan2(d.y, d.x)
            c = a - Vector((math.cos(yr), math.sin(yr), 0)) * 6.0 * e
            return [c1, (c.x, c.y, c.z, yr, 6.75 * e, 1.27 * e)]
        p, yaw, _ = f.pose(ve.s)
        ux, uy = math.cos(yaw), math.sin(yaw)
        meio = A.COMPRIMENTO[ve.modelo] / 2 * e
        return [(p.x + ux * frente / 2, p.y + uy * frente / 2, p.z, yaw, meio + frente / 2, A.LARGURA[ve.modelo] / 2 * e)]

    def _livre(self, caixa_nova, grade, folga=1.0):
        gx, gy = int(caixa_nova[0] // 25), int(caixa_nova[1] // 25)
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for b in grade.get((gx + dx, gy + dy), []):
                    if abs(b[2] - caixa_nova[2]) < 2.6 and (b[0] - caixa_nova[0]) ** 2 + (b[1] - caixa_nova[1]) ** 2 < (b[4] + caixa_nova[4] + 3) ** 2 \
                            and sat(caixa_nova, b, folga):
                        return False
        return True

    def enche(self):
        self._enche()

    def _enche(self):
        """pista já cheia no quadro 0: carros espaçados como no equilíbrio do modelo (olhando o comprimento dos dois)"""
        for f in self.faixas:
            s = f.L - 8; ant = None
            while s > 8:
                ve = Veic(self._sorteia_modelo(f), self.rnd, f.vmax, self.esc, self.folga, self.tempo)
                ve.v = ve.v0 * 0.85
                if ant is not None:
                    s = ant.s - ant.L / 2 - ve.L / 2 - ve.s0 - ve.v * ve.T * self.rnd.uniform(1.0, 1.5) / max(f.dens or self.dens, 0.2)
                if s < 8 + ve.L / 2:
                    break
                ve.s = s; f.veics.append(ve); ant = ve

    def _sorteia_modelo(self, f):
        mix = self.mix[f.classe]
        if f.restrita:
            mix = [(m, p) for m, p in mix if A.LARGURA[m] <= 1.9]
        if f.rmin < 350:  # curva fechada: nada comprido
            curtos = [(m, p) for m, p in mix if A.COMPRIMENTO[m] * esc_de(m, self.esc) <= 8.5]
            mix = curtos or [min(mix, key=lambda mp: A.COMPRIMENTO[mp[0]])]
        mod = sorteia(self.rnd, mix)
        if f.tipo == "busway":
            mod = "onibus"
        if mod == "onibus" and f.classe == "avenida" and not f.restrita and self.rnd.random() < 0.3:
            mod = "articulado"
        return mod

    # ------------------------------------------------ simulação
    def _entra(self, f, dt, grade):
        taxa = {"expressa": 0.55, "avenida": 0.30, "rua": 0.04, "corredor": 0.35}[f.classe] * self.fluxo * (f.dens or self.dens)
        if self.rnd.random() > taxa * dt:
            return
        ve = Veic(self._sorteia_modelo(f), self.rnd, f.vmax, self.esc, self.folga, self.tempo)
        ve.s = ve.L / 2 + 0.5
        if f.veics:
            ult = f.veics[-1]
            if ult.s - ult.L / 2 - (ve.s + ve.L / 2) < ve.s0 + max(ult.v, ve.v) * ve.T * 0.9:
                return
            ve.v = min(ve.v, ult.v)
        ve.nasceu = self.t
        f.veics.append(ve)

    def gargalo(self, nome_contem, s_frac, comp, v_kmh, t0, t1):
        """trecho lento: nas faixas cujo nome contém o texto, entre s_frac*L e +comp metros, de t0 a t1 segundos"""
        for f in self.faixas:
            if nome_contem in f.nome:
                s0 = f.L * s_frac
                f.limites.append((s0, s0 + comp, v_kmh / 3.6, t0, t1))

    def gargalo_ponto(self, xy, comp, v_kmh, t0, t1, classe="expressa", raio=40):
        """trecho lento perto de um ponto do mapa, em todas as faixas da classe que passam ali"""
        alvo = Vector((xy[0], xy[1], 0))
        for f in self.faixas:
            if f.classe not in (classe, "corredor"):
                continue
            best = min(range(len(f.P)), key=lambda i: (f.P[i].xy - alvo.xy).length)
            if (f.P[best].xy - alvo.xy).length < raio:
                s0 = f.cum[best]
                f.limites.append((s0, s0 + comp, v_kmh / 3.6 if f.classe != "corredor" else max(v_kmh, 35) / 3.6, t0, t1))

    def faixa_perto(self, xy, nome_contem="", classe="expressa"):
        """(faixa, s) da faixa da classe mais perto do ponto"""
        alvo = Vector((xy[0], xy[1], 0)); best = None
        for f in self.faixas:
            if f.classe != classe or nome_contem not in f.nome:
                continue
            i = min(range(len(f.P)), key=lambda i: (f.P[i].xy - alvo.xy).length)
            d = (f.P[i].xy - alvo.xy).length
            if best is None or d < best[0]:
                best = (d, f, f.cum[i])
        return (best[1], best[2]) if best else (None, None)

    def freada(self, faixa, s, t0, dur=3.0, v_kmh=12.0, modelos=("hatch", "sedan", "suv"), dec=3.0):
        """UM motorista freia (a faixa e o ponto s dados) de t0 a t0+dur: a onda de freada que anda para trás é o efeito sanfona"""
        cand = [ve for ve in faixa.veics if ve.s >= s - 200 and ve.modelo in modelos]
        ve = min(cand, key=lambda v: abs(v.s - s)) if cand else None
        if ve:
            ve.evento = (t0, t0 + dur, v_kmh / 3.6, dec)
        return ve

    def passo(self, dt):
        self.t += dt
        grade = {}
        for f in self.faixas:
            for ve in f.veics:
                for c in self.caixas(f, ve):
                    grade.setdefault((int(c[0] // 25), int(c[1] // 25)), []).append(c)
        for f in self.faixas:
            self._entra(f, dt, grade)
        # 1) cada motorista pelo modelo IDM
        for f in self.faixas:
            lider = None
            for ve in f.veics:
                v0 = ve.v0
                for (s0, s1, vl, t0, t1) in f.limites:
                    if t0 <= self.t <= t1 and s0 - 30 <= ve.s <= s1:
                        v0 = min(v0, vl)
                freada_cmd = None
                if ve.evento and ve.evento[0] <= self.t <= ve.evento[1]:
                    # freada de verdade: desacelera de forma contínua (dec m/s²) até a velocidade alvo e segura nela
                    vt, dec = ve.evento[2], (ve.evento[3] if len(ve.evento) > 3 else 3.0)
                    freada_cmd = -dec * min(1.0, (ve.v - vt) / 1.0) if ve.v > vt else min(1.2 * (vt - ve.v), 1.0)
                # o que o motorista "sabe": o estado de há `reacao` segundos (distância, velocidade dele e do carro da frente)
                if lider is not None:
                    est = (self.t, max(lider.s - lider.L / 2 - (ve.s + ve.L / 2), 0.1), ve.v, lider.v)
                else:
                    est = (self.t, None, ve.v, ve.v)
                if self.reacao > 0:
                    ve.hist.append(est)
                    while len(ve.hist) > 1 and ve.hist[1][0] <= self.t - self.reacao:
                        ve.hist.pop(0)
                    est = ve.hist[0]
                _, gap, vs, vl = est
                acc = ve.a * (1 - (vs / max(v0, 0.1)) ** 4)
                if gap is not None:
                    sst = ve.s0 + max(0.0, vs * ve.T + vs * (vs - vl) / (2 * math.sqrt(ve.a * ve.b)))
                    acc -= ve.a * (sst / gap) ** 2
                if freada_cmd is not None:
                    acc = min(acc, freada_cmd)
                ve.acc = max(acc, -9.0)
                lider = ve
        for f in self.faixas:
            lider = None
            for ve in f.veics:
                ve.v = max(ve.v + ve.acc * dt, 0.0); ve.s += ve.v * dt
                if lider is not None:   # trava física (freada de emergência): com atraso de reação o modelo sozinho deixaria um carro entrar no outro
                    teto = lider.s - lider.L / 2 - ve.L / 2 - 0.6
                    if ve.s > teto:
                        ve.s = teto; ve.v = min(ve.v, lider.v)
                lider = ve
                alvo = 1.0 if ve.acc < -0.6 or ve.v < 0.6 else 0.0
                ve.freio += (alvo - ve.freio) * min(1.0, dt * 8)
            saem = [ve for ve in f.veics if ve.s + ve.L / 2 > f.L]
            for ve in saem:
                self._solta(ve)
            f.veics = [ve for ve in f.veics if ve not in saem]
        if self.grava is not None:
            self.xt.append((self.t, [(ve.id, ve.s, ve.v) for ve in self.grava.veics]))

    def aquece(self, segundos, dt=1 / 24):
        n = int(segundos / dt)
        for _ in range(n):
            self.passo(dt)
        self.t = 0.0
        for f in self.faixas:  # quem nasceu durante o aquecimento já está na pista (senão ficaria com idade negativa e invisível)
            for ve in f.veics:
                ve.nasceu = None
            f.limites = [(a, b, c, d, e) for (a, b, c, d, e) in f.limites]

    # ------------------------------------------------ objetos 3D
    def _pega(self, ve):
        k = ve.modelo
        pool = self.livres.setdefault(k, [])
        if pool:
            return pool.pop()
        cl = CLASSE[k]
        if self.modo_cor == "tipo":
            c, c2 = COR_TIPO[cl]
            if cl == "carro":
                c = self.rnd_cor.choice(["#f4f4f1", "#f4f4f1", "#dfe2e6", "#c9ccd1"])
        elif k in ("onibus", "articulado"):
            c, c2 = self.rnd_cor.choice(ONIBUS_CORES)
        elif k == "ambulancia":
            c, c2 = "#ffffff", "#d0202a"
        elif k == "viatura":
            c, c2 = "#f4f4f2", "#14171a"
        elif k.startswith("moto"):
            c, c2 = sorteia(self.rnd_cor, CORES_CARRO), self.rnd_cor.choice(["#1d2b3a", "#2a2a2a", "#f2b705", "#c8161d", "#3a5f8a"])
        elif k == "taxi":
            c, c2 = "#f4f4f2", "#202020"
        elif k in ("toco", "cavalo", "vuc"):
            c, c2 = self.rnd_cor.choice(["#c8161d", "#f1f0ec", "#1f5fa8", "#2f6b3a", "#e0a400"]), self.rnd_cor.choice(["#c8161d", "#1f5fa8", "#2f6b3a"])
        else:
            c, c2 = sorteia(self.rnd_cor, CORES_CARRO), "#202020"
        o = A.veiculo(k, c, c2, escala=ve.esc)
        if k == "cavalo":
            r = A.veiculo("carreta", "#f0f0f0", c2, escala=ve.esc)
            o["reboque"] = r.name
        return o

    def _solta(self, ve):
        if ve.obj is not None and self.visual:
            import bpy
            ve.obj.hide_render = True; ve.obj.location = (0, 0, -5000)
            if ve.obj.get("reboque"):
                r = bpy.data.objects[ve.obj["reboque"]]; r.hide_render = True; r.location = (0, 0, -5000)
            self.livres.setdefault(ve.modelo, []).append(ve.obj)
        ve.obj = None

    def aplica(self):
        if not self.visual:
            return
        import bpy
        for f in self.faixas:
            for ve in f.veics:
                if ve.obj is None:
                    ve.obj = self._pega(ve)
                o = ve.obj; o.hide_render = False
                k = 1.0  # nasce crescendo (0,35 s) e some encolhendo nos últimos 9 m da faixa: nada estoura na tela
                if ve.nasceu is not None:
                    q = min(max((self.t - ve.nasceu) / 0.35, 0.0), 1.0); k = q * q * (3 - 2 * q)
                k *= self.k_saida(f, ve)
                o.scale = (ve.esc * max(k, 0.001),) * 3
                if ve.modelo == "cavalo":
                    sc = ve.s + ve.L / 2 - 2.7 * ve.esc  # centro do cavalo
                    p, yaw, pitch = f.pose(sc)
                    pino = sc - 1.4 * ve.esc
                    p2a, p2b = f.ponto(pino), f.ponto(pino - 11.0)
                    d = p2a - p2b; yr = math.atan2(d.y, d.x)
                    r = bpy.data.objects[o["reboque"]]; r.hide_render = False; r.scale = (ve.esc * max(k, 0.001),) * 3
                    r.location = p2a - Vector((math.cos(yr), math.sin(yr), 0)) * 6.0 * ve.esc
                    r.rotation_euler = (0, -math.atan2(d.z, max(d.xy.length, 1e-6)), yr)
                    r["freio"] = ve.freio
                    if self.modo_cor == "velocidade":
                        r.color = cor_velocidade(ve.v / (f.vmax * VEL_VERDE))
                else:
                    p, yaw, pitch = f.pose(ve.s)
                o.location = p; o.rotation_euler = (0, pitch, yaw)
                o["freio"] = ve.freio
                if getattr(ve, "cor_forca", None) is not None:
                    o.color = ve.cor_forca
                elif self.modo_cor == "velocidade":
                    o.color = cor_velocidade(ve.v / (f.vmax * VEL_VERDE))

    def sobreposicoes(self):
        """pares de veículos cujas caixas se cortam agora (dois carros um dentro do outro) e o lugar de cada um"""
        grade = {}; itens = []
        for fi, f in enumerate(self.faixas):
            for ve in f.veics:
                for cx in self.caixas(f, ve):
                    itens.append((fi, ve.id, cx))
        for i, (fi, vid, cx) in enumerate(itens):
            grade.setdefault((int(cx[0] // 25), int(cx[1] // 25)), []).append(i)
        pares = {}
        for i, (fi, vid, a) in enumerate(itens):
            gx, gy = int(a[0] // 25), int(a[1] // 25)
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    for j in grade.get((gx + dx, gy + dy), []):
                        if j <= i:
                            continue
                        fj, vj, b = itens[j]
                        if vid == vj or abs(a[2] - b[2]) > 2.6 or (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 > (a[4] + b[4] + 3) ** 2:
                            continue
                        if sat(a, b):
                            pares.setdefault((min(vid, vj), max(vid, vj)), (a[0], a[1], fi, fj))
        return pares

    def contagem(self):
        return sum(len(f.veics) for f in self.faixas)

    def mapa_de_cor(self, passo=30.0, z=0.6, larg=None, classes=("expressa", "avenida")):
        """pinta cada faixa pela velocidade média dos carros naquele trecho: verde (livre), amarelo, vermelho (parado)"""
        cores = {"verde": "#0fb85a", "amarelo": "#f5a800", "vermelho": "#e3161b", "vinho": "#7d0a1c"}
        mats = {k: A.mat_cor(c, 0.5, emis=0.35, nome=f"tb_tr_{k}") for k, c in cores.items()}
        for f in self.faixas:
            if f.classe not in classes:
                continue
            n = max(1, int(f.L // passo))
            for i in range(n):
                s0, s1 = i * f.L / n, (i + 1) * f.L / n
                vs = [ve.v for ve in f.veics if s0 <= ve.s < s1]
                razao = (sum(vs) / len(vs)) / f.vmax if vs else 1.0
                k = "verde" if razao > 0.7 else "amarelo" if razao > 0.4 else "vermelho" if razao > 0.15 else "vinho"
                pts = [f.ponto(s0 + (s1 - s0) * j / 4) for j in range(5)]
                A.fita(pts, larg or 2.4, mats[k], z, "cor_" + k, "trafego_cor")

    def diagrama_xt(self, caminho, titulo="", marca=None, **kw):
        """diagrama espaço-tempo da faixa gravada (tr.grava = faixa antes de simular): cada carro é uma linha colorida pela velocidade.
        A onda de freada aparece como a faixa vermelha que sobe inclinada. Desenha fora do Blender (tb_xt.py usa o matplotlib do sistema)."""
        import json, subprocess, os
        dados = {"vmax": self.grava.vmax if self.grava else 20.0, "titulo": titulo, "marca": marca, "escala": ESCALA_VEL,
                 "xt": [(t, lst) for t, lst in self.xt], "vref": (self.grava.vmax if self.grava else 20.0) * VEL_VERDE, **kw}
        js = caminho.rsplit(".", 1)[0] + ".json"
        json.dump(dados, open(js, "w"))
        aqui = os.path.dirname(os.path.abspath(__file__))
        subprocess.run([os.environ.get("TB_PYTHON", "/Applications/Xcode.app/Contents/Developer/usr/bin/python3"), os.path.join(aqui, "tb_xt.py"), js, caminho], check=True)
