"""Trânsito Brasil 3D, ep. 1: RASCUNHO ANIMADO (meia resolução, com a voz; sem efeitos sonoros). Câmera PLANEJADA de cada plano (pré-passagem da simulação, filtrada),
mesma simulação nas quatro vistas, tempo do filme -> tempo da simulação (câmera lenta depois da freada) e a cena do espaço (planos 10 e 11).
    blender -b -P kit3d/anim_ep1.py -- plano  PASTA            (pré-passagem + medição da câmera e das colisões; grava camera.json e xt.png, não renderiza)
    blender -b -P kit3d/anim_ep1.py -- frame  ARQ.png --t 20.0 [--escala 0.5]
    blender -b -P kit3d/anim_ep1.py -- render PASTA [--escala 0.5] [--parte i/n] [--de 0 --ate 9999]
Os quadros saem de 1080x1350 (x escala). A composição final (painel, legenda, pílulas) é do compoe_ep1.py."""
import sys, os, math, json, bisect
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from mathutils import Vector
import tb_assets as A
import tb_cena as C
import tb_mapa as MP
import tb_trafego as T
import tb_camera_suave as CS
import anim_ep1_planos as AP
SP = AP.SP

RAIZ = SP.RAIZ
argv = sys.argv[sys.argv.index("--") + 1:]
modo, saida = argv[0], argv[1]
op = lambda k, d: argv[argv.index(k) + 1] if k in argv else d
FPS = 24
NOME = "Marginal Pinheiros (Expressa)"
Y0 = float(op("--y", "800"))
TE, DUR_FREADA, DEC = SP.TE, SP.DUR_FREADA, SP.DEC
SIM_MAX = 92.0
N_FRAMES = int(round(AP.TOTAL * FPS))
MIX = {"expressa": [("hatch", 34), ("sedan", 28), ("suv", 22), ("picape", 6), ("taxi", 4), ("vuc", 3)],
       "avenida": [("hatch", 40), ("sedan", 30), ("suv", 20)], "rua": [("hatch", 50), ("sedan", 50)], "corredor": [("moto", 50), ("moto_entrega", 50)]}
PRINCIPAIS = ["Marginal Pinheiros (Expressa)", "Marginal Pinheiros (Local)", "Avenida Jornalista Roberto Marinho", "Avenida Engenheiro Luís Carlos Berrini",
              "Avenida das Nações Unidas", "Avenida dos Bandeirantes", "Ponte do Morumbi"]
ESP_T0 = 6.0       # simulação da cena do espaço: de 6 s (pista livre) em diante, no mesmo ritmo do filme
sim_de = SP.sim_de
dt_para = lambda t_sim: (1 / 96) if t_sim < TE + 16 else (1 / 48)   # passo fino na câmera lenta (cada quadro avança ~1,8 passos); o mesmo na pré-passagem e no render


def anda(tr, alvo):
    while tr.t < alvo - 1e-9:
        tr.passo(dt_para(tr.t))


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
tx, ty, tz = AP.AEREA["alvo"]
mp.foco_ids = mp.pista_de((cx, cy), NOME)
mp.foco_extra = (tx, ty, 650.0, PRINCIPAIS)
reg_c = ((cx + tx) / 2, (cy + ty) / 2); reg_r = math.hypot(cx - tx, cy - ty) / 2 + 620
mp.monta((reg_c[0], reg_c[1], reg_r), foco=(cx, cy, 480), nomes=[NOME])


def monta_trafego(visual):
    T.Veic._n = 0
    tr = T.Trafego(mp, (cx, cy, 520), fluxo=1.0, escala_veic=1.12, visual=visual, cor="velocidade", dens=0.9, enche=False, folga=2.6, tempo=1.0, mix=MIX)
    lane, s_c = tr.faixa_perto((cx, cy), NOME)
    lane.dens = 2.1
    tr.enche(); tr.grava = lane
    tr.aquece(60); tr.xt = []; tr.t = 0.0
    return tr, lane, s_c


def slow(lane):
    return [v for v in lane.veics if v.v < 0.30 * lane.vmax * T.VEL_VERDE]


FILM_ESP0 = 58.69      # início do plano 10 no filme
FILM_PAR2 = 66.33      # início do plano 11: aqui se escolhe o par da régua
FILM_POSTE = 69.5      # o carro da frente passa no poste (palavra "poste")


class Espaco:
    """cena do espaço (planos 10 e 11): a pista ainda livre (simulação a partir de 6 s) com duas encenações:
    plano 10: B abre um vão grande para A (recua 10 a 14 m) e A dá uma freada leve;  plano 11: um par (A2, B2) com B2 dentro dos 2 segundos que depois abre o vão"""
    def __init__(self, visual):
        self.tr, self.lane, _ = monta_trafego(visual)
        anda(self.tr, ESP_T0)
        vs = sorted(self.lane.veics, key=lambda v: v.s)
        i = min(range(1, len(vs)), key=lambda i: abs(vs[i].s - S_E))
        self.A, self.B = vs[i], vs[i - 1]
        C_ = vs[i - 2] if i >= 2 else None
        folga = (self.B.s - self.B.L / 2) - ((C_.s + C_.L / 2) if C_ else self.B.s - 40)
        self.recuo = min(14.0, max(folga - 8.0, 0.0))
        self.B.s -= self.recuo
        self.A.evento = (ESP_T0 + 4.0, ESP_T0 + 6.0, self.A.v * 0.55, 2.5)
        self.A2 = self.B2 = None; self.nudge = 0.0
        self.ser = {"t": [], "A": [], "B": [], "A2": [], "B2": []}

    def film(self, t_e):
        return FILM_ESP0 + (t_e - ESP_T0)

    def escolhe_par2(self):
        vs = sorted([v for v in self.lane.veics if abs(v.s - S_E) < 70], key=lambda v: v.s)
        melhor = None
        for i in range(1, len(vs)):
            gap = (vs[i].s - vs[i].L / 2 - (vs[i - 1].s + vs[i - 1].L / 2)) / max(vs[i - 1].v, 1.0)
            if melhor is None or gap < melhor[0]:
                melhor = (gap, vs[i], vs[i - 1])
        _, self.A2, self.B2 = melhor

    def vai(self, t_e):
        tr = self.tr
        while tr.t < t_e - 1e-9:
            if self.A2 is None and self.film(tr.t) >= FILM_PAR2:
                self.escolhe_par2()
            tr.passo(dt_para(tr.t))
            if self.B2 is not None:   # B2 abre o vão: recua 9 m com curva suave entre 70,0 e 71,8 s do filme
                u = min(max((self.film(tr.t) - 70.0) / 1.8, 0.0), 1.0)
                alvo = 9.0 * u * u * (3 - 2 * u)
                self.B2.s -= alvo - self.nudge; self.nudge = alvo
            for k, v in (("A", self.A), ("B", self.B), ("A2", self.A2), ("B2", self.B2)):
                self.ser[k].append(v.s if v is not None else None)
            self.ser["t"].append(tr.t)




# ---------------------------------------------------------------- pré-passagem A: qual carro freia e onde
tr0, lane0, s_c0 = monta_trafego(False)
anda(tr0, TE - 0.03)
cand = [v for v in lane0.veics if v.modelo in ("hatch", "sedan", "suv")]
v0 = min(cand, key=lambda v: abs(v.s - s_c0))
ID_VIT, S_E = v0.id, v0.s
del tr0, lane0, v0

# ---------------------------------------------------------------- pré-passagem B: a simulação inteira, sem objetos, gravando as âncoras da câmera, o diagrama e as sobreposições
tr1, lane1, _ = monta_trafego(False)
SER = {"t": [], "vit": [], "cauda": [], "cabeca": [], "fila": [], "n": []}
vit1 = None
sobrepos = set()
passos_med = 0
while tr1.t < SIM_MAX:
    if vit1 is None:
        ach = [v for v in lane1.veics if v.id == ID_VIT]
        if ach:
            vit1 = ach[0]; vit1.evento = (TE, TE + DUR_FREADA, 0.0, DEC)
    tr1.passo(dt_para(tr1.t))
    passos_med += 1
    if passos_med % 6 == 0:
        sobrepos |= set(tr1.sobreposicoes())
    ls = slow(lane1)
    SER["t"].append(tr1.t)
    SER["vit"].append(vit1.s if vit1 is not None and vit1 in lane1.veics else None)
    SER["cauda"].append(min(v.s for v in ls) if ls else None); SER["cabeca"].append(max(v.s for v in ls) if ls else None)
    SER["fila"].append((SER["cauda"][-1] + SER["cabeca"][-1]) / 2 if ls else None); SER["n"].append(len(ls))
XT = tr1.xt[::8]; LANE_VMAX = lane1.vmax
ESP_PRE = Espaco(False)
ESP_PRE.vai(ESP_T0 + (AP.TOTAL - FILM_ESP0) if False else ESP_T0 + (73.4 - FILM_ESP0))
def serie_esp(nome, t_e):
    ts = ESP_PRE.ser["t"]; vals = ESP_PRE.ser[nome]
    i = min(max(bisect.bisect_left(ts, t_e), 1), len(ts) - 1)
    def val(j):
        while j >= 0 and vals[j] is None: j -= 1
        return vals[j] if j >= 0 else S_E
    a_, b_ = val(i - 1), val(i)
    w = (t_e - ts[i - 1]) / max(ts[i] - ts[i - 1], 1e-9)
    return a_ + (b_ - a_) * min(max(w, 0.0), 1.0)
S_POSTE = serie_esp("A2", ESP_T0 + (FILM_POSTE - FILM_ESP0))
p_a, yaw_a, _ = lane1.pose(S_E)
ys = [lane1.pose(S_E + d)[1] for d in range(-200, 40, 20)]
AZ0 = math.degrees(math.atan2(sum(math.sin(y) for y in ys), sum(math.cos(y) for y in ys))) - 90
print(f"[ep1] pista {lane1.L:.0f} m, ponto da freada s={S_E:.0f}, carro {ID_VIT}, azimute {AZ0:.1f}°; sobreposições na simulação principal: {len(sobrepos)}")
LANE_PONTO = lane1.ponto       # a geometria da pista (a mesma da simulação visual)


def interp(arr, st):
    """valor da série SER[arr] no tempo de simulação st (preenche os vazios com o último valor conhecido)"""
    ts = SER["t"]; vals = SER[arr]
    i = bisect.bisect_left(ts, st)
    i = min(max(i, 1), len(ts) - 1)
    def val(j):
        while j >= 0 and vals[j] is None: j -= 1
        return vals[j] if j >= 0 else S_E
    a, b = val(i - 1), val(i)
    w = (st - ts[i - 1]) / max(ts[i] - ts[i - 1], 1e-9)
    return a + (b - a) * min(max(w, 0.0), 1.0)


# ---------------------------------------------------------------- planejamento da câmera: uma pose por quadro
SIG = {"vit": 1.3, "fila": 3.5, "cauda": 3.5, "cabeca": 3.5, "ponto": 0.1}   # o fim da fila salta um carro de cada vez: filtro forte
ANC = {}
for nome in ("vit", "fila", "cauda", "cabeca"):
    bruto = [interp(nome, sim_de(f / FPS)) for f in range(N_FRAMES + 1)]
    ANC[nome] = CS.filtra(bruto, FPS, SIG[nome])
ANC["ponto"] = [S_E] * (N_FRAMES + 1)
for nome in ("B", "A2"):
    bruto = [serie_esp(nome, ESP_T0 + min(max(f / FPS - FILM_ESP0, 0.0), 14.7)) for f in range(N_FRAMES + 1)]
    ANC["esp" + nome] = CS.filtra(bruto, FPS, 0.9)


def onda(u, m0=0.7, m1=0.7):
    return CS.valor([(0.0, 0.0, m0), (1.0, 1.0, m1)], u)


POSES = []
for f in range(N_FRAMES + 1):
    t = f / FPS; sh = AP.plano_em(min(t, AP.TOTAL - 1e-6)); u = min(max((t - sh["t0"]) / (sh["t1"] - sh["t0"]), 0.0), 1.0); h = onda(u)
    mix = lambda a, b: a + (b - a) * h
    if sh["vista"] == "aerea":
        POSES.append(dict(f=f, plano=0, vista="aerea", cx=tx, cy=ty, dist=mix(AP.AEREA["d0"], AP.AEREA["d1"]), elev=mix(AP.AEREA["e0"], AP.AEREA["e1"]),
                          azim=mix(AP.AEREA["a0"], AP.AEREA["a1"]), alvo_z=tz))
        continue
    s_c = ANC[sh["anc"]][f] + mix(sh["o0"], sh["o1"])
    pt = LANE_PONTO(s_c)
    POSES.append(dict(f=f, plano=sh["id"], vista=sh["vista"], cx=pt.x, cy=pt.y, dist=mix(sh["d0"], sh["d1"]), elev=mix(sh["e0"], sh["e1"]), azim=AZ0 + mix(sh["a0"], sh["a1"]), alvo_z=0.0))
# o traçado do OSM tem vértices: sem filtro, a cada um deles o centro da câmera troca de direção de uma vez. Filtra o caminho no chão DENTRO de cada plano (pontas repetidas)
for sh in AP.SHOTS:
    idx = [q["f"] for q in POSES if q["plano"] == sh["id"]]
    if sh["vista"] == "aerea" or len(idx) < 8:
        continue
    xs = CS.filtra([POSES[i]["cx"] for i in idx], FPS, 0.7); ys_ = CS.filtra([POSES[i]["cy"] for i in idx], FPS, 0.7)
    for k, i in enumerate(idx):
        POSES[i]["cx"], POSES[i]["cy"] = xs[k], ys_[k]


def loc_camera(p):
    if p["vista"] == "topo":
        return Vector((p["cx"], p["cy"], 150.0))
    e, a = math.radians(p["elev"]), math.radians(p["azim"])
    return Vector((p["cx"], p["cy"], p["alvo_z"])) + Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e))) * p["dist"]


# ---------------------------------------------------------------- medição da câmera por plano
def mede_planos():
    """por plano (sem o primeiro quadro do plano seguinte): velocidade da câmera RELATIVA à distância dela ao alvo (1/s: quanto da distância ela anda por segundo),
    jerk relativo (1/s³) e a menor velocidade no meio do plano. TRANCO = jerk relativo > 0,5; PARADA = cai a menos de 15% do pico no meio."""
    ok = True
    print("[ep1] câmera por plano: velocidade relativa (1/s) | jerk relativo (1/s³) | velocidade mínima no meio (% do pico) | zoom relativo (1/s) | veredito")
    for sh in AP.SHOTS:
        idx = [q["f"] for q in POSES if q["plano"] == sh["id"]]
        P = [loc_camera(POSES[f]) for f in idx]
        D = [POSES[f]["dist"] for f in idx]
        if len(P) < 12:
            continue
        v = [(P[i + 1] - P[i - 1]) * (FPS / 2) for i in range(1, len(P) - 1)]
        a = [(v[i + 1] - v[i - 1]) * (FPS / 2) for i in range(1, len(v) - 1)]
        j = [(a[i + 1] - a[i - 1]) * (FPS / 2) for i in range(1, len(a) - 1)]
        dm = sum(D) / len(D)
        vm = [x.length / dm for x in v]; jm = [x.length / dm for x in j]
        dv = [abs(D[i + 1] - D[i - 1]) * (FPS / 2) / dm for i in range(1, len(D) - 1)]
        pico = max(vm) if vm else 0.0
        meio = vm[len(vm) // 8: len(vm) - len(vm) // 8] or vm
        minimo = min(meio) / pico * 100 if pico > 0.02 else 100.0
        jerk = max(jm) if jm else 0.0
        ruim = (jerk > 0.5) or (pico > 0.04 and minimo < 15.0)
        ok &= not ruim
        print(f"   plano {sh['id']:2d} {sh['vista']:11s} vel {pico:5.3f} | jerk {jerk:6.3f} | mín {minimo:4.0f}% | zoom {max(dv) if dv else 0:5.3f} | {'REVER' if ruim else 'ok'}")
    return ok


if modo == "plano" and "--debug" in argv:
    for f in list(range(76, 84)) + list(range(180, 186)):
        q = POSES[f]; print(f"[dbg] f{f} plano {q['plano']} {q['vista']} cx {q['cx']:.1f} cy {q['cy']:.1f} dist {q['dist']:.1f} elev {q['elev']:.1f} azim {q['azim']:.1f}")
if modo == "plano":
    os.makedirs(saida, exist_ok=True)
    ok = mede_planos()
    json.dump([dict(f=p["f"], plano=p["plano"], vista=p["vista"], x=loc_camera(p).x, y=loc_camera(p).y, z=loc_camera(p).z, dist=p["dist"]) for p in POSES],
              open(os.path.join(saida, "camera.json"), "w"))
    tr1.xt = XT
    tr1.diagrama_xt(os.path.join(saida, "xt.png"), "Cada linha é um carro", marca=(TE + 0.3, S_E, "1 carro freia"), tam=[10.0, 3.0], dpi=108, xlim=[TE - 2, TE + 46],
                    ylim=[S_E - 520, S_E + 60], margens=dict(left=0.095, right=0.985, bottom=0.24, top=0.82), fundo="#f3f1ec")
    json.dump(dict(sobreposicoes=len(sobrepos), ok_camera=ok, ponto=S_E, vmax=LANE_VMAX), open(os.path.join(saida, "resumo.json"), "w"))
    print(f"[ep1] sobreposições de carros na simulação principal: {len(sobrepos)}; câmera {'OK' if ok else 'PRECISA REVER'}")
    sys.exit(0)

# ---------------------------------------------------------------- cena visual
del tr1
tr, lane, s_c = monta_trafego(True)
vit = None
esp = None            # a cena do espaço visual (criada quando o primeiro quadro dos planos 10 e 11 pede)
anel_esp = None
EXTRAS = []
E = MP.ESTILOS["didatico"]
esc = float(op("--escala", "0.5"))
C.motor(True, 40, 1080, 1350, esc)
C.mundo(E["mundo"], E["mundo_forca"]); C.sol(40, AZ0 - 55, E["sol"], E["sol_cor"], 3.0)
cam = C.camera(Vector((cx, cy, 0)), 70, 50, AZ0, 45)
anel = A.anel(4.2, "#ffd21f", 0.5, pos=(0, 0, 0.5))


def liga_evento():
    global vit
    if vit is None:
        ach = [v for v in lane.veics if v.id == ID_VIT]
        if ach:
            vit = ach[0]; vit.evento = (TE, TE + DUR_FREADA, 0.0, DEC)


def esconde(trf):
    for f_ in trf.faixas:
        for ve in f_.veics:
            if ve.obj is not None:
                ve.obj.hide_render = True
                if ve.obj.get("reboque"):
                    bpy.data.objects[ve.obj["reboque"]].hide_render = True


def limpa_extras():
    for o in EXTRAS:
        bpy.data.objects.remove(o)
    EXTRAS.clear()


def garante_espaco():
    global esp, anel_esp
    if esp is None:
        esp = Espaco(True)
        anel_esp = A.anel(3.6, "#22c55e", 0.4, pos=(0, 0, 0.5))
        print(f"[ep1] cena do espaço: B recuou {esp.recuo:.1f} m")
    return esp


def avanca_quadro(f):
    """leva as simulações até o quadro f SEM renderizar (para os quadros que outra parte do render cuida)"""
    t = f / FPS; sh = AP.plano_em(min(t, AP.TOTAL - 1e-6))
    if sh["id"] in (10, 11):
        garante_espaco().vai(ESP_T0 + (t - FILM_ESP0))
    else:
        anda(tr, sim_de(t)); liga_evento()


def render_frame(f, caminho):
    t = f / FPS
    p = POSES[f]; sh = AP.plano_em(min(t, AP.TOTAL - 1e-6))
    especial = sh["id"] in (10, 11)
    if especial:
        e = garante_espaco(); e.vai(ESP_T0 + (t - FILM_ESP0))
    else:
        anda(tr, sim_de(t)); liga_evento()
    # câmera
    if p["vista"] == "topo":
        cam.data.type = "ORTHO"; cam.data.ortho_scale = p["dist"]; cam.data.clip_start = 20; cam.data.clip_end = 400
        cam.location = (p["cx"], p["cy"], 150.0); cam.rotation_euler = (0, 0, math.radians(AZ0))
    else:
        cam.data.type = "PERSP"; cam.data.lens = AP.LENTE[p["vista"]]; cam.data.clip_start = 8 if p["vista"] != "aerea" else 20
        cam.data.clip_end = 2500 if p["vista"] == "aerea" else 900
        C.poe_camera(cam, Vector((p["cx"], p["cy"], p["alvo_z"])), p["dist"], p["elev"], p["azim"])
    limpa_extras()
    anel.hide_render = True
    if anel_esp is not None:
        anel_esp.hide_render = True
    if especial:
        esconde(tr)
        if sh["id"] == 11 and e.A2 is not None:   # a cor do carro de trás (dentro ou fora dos 2 segundos) precisa estar definida ANTES de aplicar
            a_, b_ = e.A2, e.B2
            gap_s = (a_.s - a_.L / 2 - (b_.s + b_.L / 2)) / max(b_.v, 1.0)
            b_.cor_forca = T.cor_velocidade(0.30) if (gap_s < 2.0 and t >= FILM_POSTE) else T.cor_velocidade(1.0)
        e.tr.aplica()
        if sh["id"] == 10 and e.B.obj is not None:
            anel_esp.hide_render = False; anel_esp.location = e.B.obj.location + Vector((0, 0, 0.6))
        if sh["id"] == 11 and e.A2 is not None:
            a_, b_ = e.A2, e.B2
            ps = e.lane.pose(S_POSTE); nx, ny = -math.sin(ps[1]), math.cos(ps[1])
            pos_poste = ps[0] + Vector((nx * 11.0, ny * 11.0, 0))
            po = A.poste((pos_poste.x, pos_poste.y, 0)); po.scale = (2.2, 2.2, 1.6); EXTRAS.append(po)
            # linha amarela atravessando a pista no poste: o ponto de onde se conta
            EXTRAS.append(A.fita([(ps[0].x - nx * 13.0, ps[0].y - ny * 13.0, ps[0].z + 0.5), (ps[0].x + nx * 11.0, ps[0].y + ny * 11.0, ps[0].z + 0.5)], 0.7,
                                 A.mat_cor("#ffd21f", 0.4, emis=1.1, nome="tb_regua_#ffd21f"), 0.0, "linha_poste", "rotulos"))
            if t >= FILM_POSTE and a_.obj is not None:      # a régua nasce quando o carro da frente passa no poste
                pa, ya, _ = e.lane.pose(a_.s)
                EXTRAS.extend(A.regua_tempo((pa.x - math.cos(ya) * (a_.L / 2 + 0.4), pa.y - math.sin(ya) * (a_.L / 2 + 0.4)), ya, max(a_.v, 8.0), 2.0, 2.6, pa.z + 0.5))
    else:
        if esp is not None:
            esconde(esp.tr)
        if sh["id"] != 0:
            tr.aplica()
            vis = 9.0 <= t <= 36.0 and vit is not None and vit.obj is not None
            anel.hide_render = not vis
            if vis:
                anel.location = vit.obj.location + Vector((0, 0, 0.6))
        else:
            esconde(tr)          # a vista aérea não tem carros
    bpy.context.view_layer.update()
    C.render(caminho)


if modo == "frame":
    t = float(op("--t", "20.0")); f = int(round(t * FPS))
    for k in range(0, f):
        avanca_quadro(k)
    render_frame(f, saida)
elif modo == "render":
    os.makedirs(saida, exist_ok=True)
    i_parte, n_partes = (int(x) for x in op("--parte", "0/1").split("/"))
    de, ate = int(op("--de", "0")), min(int(op("--ate", str(N_FRAMES))), N_FRAMES)
    for f in range(0, ate + 1):
        if f >= de and f % n_partes == i_parte:
            render_frame(f, os.path.join(saida, f"{f + 1:04d}.png"))
        else:
            avanca_quadro(f)
