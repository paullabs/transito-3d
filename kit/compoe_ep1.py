"""Trânsito Brasil 3D, ep. 1: compõe o rascunho (system python, PIL). Cada quadro: a cena (1080x1350 x escala) em cima e o painel embaixo (570 px x escala):
legenda de cores + 'simulação ilustrativa', a legenda UMA PALAVRA POR VEZ com bounce no ritmo da voz (palavras.json) e, no plano 7, o diagrama espaço-tempo com o
cursor andando no tempo da SIMULAÇÃO (não do filme). Pílulas de texto no alto da cena.
    python3 kit3d/compoe_ep1.py PASTA_DOS_QUADROS PASTA_XT SAIDA [--de N --ate M]"""
import os, sys, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw, ImageFont
import anim_ep1_planos as AP
SP = AP.SP

quadros_dir, xt_dir, saida = sys.argv[1], sys.argv[2], sys.argv[3]
op = lambda k, d: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
os.makedirs(saida, exist_ok=True)
FPS = 24
FONTE = "/System/Library/Fonts/Supplemental/Arial Rounded Bold.ttf"
TINTA, PAPEL = (27, 31, 39), (243, 241, 236)
COR = {"verde": (34, 197, 94), "amarelo": (255, 194, 26), "vermelho": (255, 59, 48)}
A0 = sorted(f for f in os.listdir(quadros_dir) if f[:4].isdigit() and f.endswith(".png"))
q0 = Image.open(os.path.join(quadros_dir, A0[0])); sc = q0.width / 1080
W, HC = q0.width, q0.height; HP = int(570 * sc); H = HC + HP
F = lambda n: ImageFont.truetype(FONTE, max(8, int(n * sc)))
# palavras
PAL = []
for w in json.load(open(os.path.join(SP.RAIZ, "roteiros", "voz-transito", "palavras.json"))):
    t = w["txt"].strip().strip(",.:;!?").strip()
    if t:
        PAL.append(dict(txt=t, t0=w["t0"], t1=w["t1"]))
for i, w in enumerate(PAL):
    prox = PAL[i + 1]["t0"] if i + 1 < len(PAL) else w["t1"] + 0.3
    w["fim"] = prox if prox - w["t1"] < 0.30 else w["t1"] + 0.12
XT = Image.open(os.path.join(xt_dir, "xt.png")).convert("RGB")
XT = XT.resize((W, int(XT.height * W / XT.width)))
XL, XR = 0.095, 0.985; X0, X1 = SP.TE - 2, SP.TE + 46


def alfa_pilula(t, a, b, fade=0.25):
    if t < a or t > b:
        return 0.0
    return max(0.0, min(1.0, (t - a) / fade, (b - t) / fade))


def pilula(im, texto, alfa):
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    f = F(46); tw = d.textlength(texto, font=f); pad = int(26 * sc); ph = int(76 * sc)
    box = (W / 2 - tw / 2 - pad, int(34 * sc), W / 2 + tw / 2 + pad, int(34 * sc) + ph); a = int(235 * alfa)
    d.rounded_rectangle(box, radius=int(ph * 0.5), fill=(20, 24, 31, a))
    d.text((box[0] + pad, box[1] + int(9 * sc)), texto, font=f, fill=(255, 255, 255, int(255 * alfa)))
    return Image.alpha_composite(im.convert("RGBA"), lay).convert("RGB")


def palavra_em(t):
    for w in PAL:
        if w["t0"] <= t < w["fim"]:
            return w
    return None


def desenha_palavra(im, w, t, y_c, tam):
    d = ImageDraw.Draw(im); tau = (t - w["t0"]) / 0.25
    esc = 0.55 + 0.55 * (tau / 0.6) if tau < 0.6 else (1.1 - 0.1 * ((tau - 0.6) / 0.4) if tau < 1.0 else 1.0)
    f = F(tam * esc); txt = w["txt"]
    tw = d.textlength(txt, font=f)
    d.text((W / 2 - tw / 2, y_c - tam * sc * esc * 0.62), txt, font=f, fill=TINTA)


de, ate = int(op("--de", "0")), int(op("--ate", str(len(A0) - 1)))
for i in range(de, min(ate, len(A0) - 1) + 1):
    nome = A0[i]; n = int(nome[:4]); t = (n - 1) / FPS
    cena = Image.open(os.path.join(quadros_dir, nome)).convert("RGB")
    im = Image.new("RGB", (W, H), PAPEL); im.paste(cena, (0, 0))
    for a, b, txt in AP.PILULAS:
        al = alfa_pilula(t, a, b)
        if al > 0:
            im = pilula(im, txt, al)
    d = ImageDraw.Draw(im)
    sh = AP.plano_em(min(t, AP.TOTAL - 1e-6))
    y0 = HC
    d.line([(0, y0), (W, y0)], fill=(215, 211, 203), width=max(1, int(3 * sc)))
    w = palavra_em(t)
    if sh["id"] == 7:   # diagrama com o cursor no tempo da simulação
        im.paste(XT, (0, y0 + int(6 * sc)))
        st = SP.sim_de(t)
        cx = int((XL + (st - X0) / (X1 - X0) * (XR - XL)) * W)
        cx = min(max(cx, int(XL * W)), int(XR * W))
        d.line([(cx, y0 + int(40 * sc)), (cx, y0 + int(6 * sc) + int(XT.height * 0.78))], fill=TINTA, width=max(2, int(4 * sc)))
        if w:
            desenha_palavra(im, w, t, y0 + HP - int(78 * sc), 70)
    else:
        x = int(40 * sc)
        for k, rot in (("verde", "andando"), ("amarelo", "devagar"), ("vermelho", "parado")):
            r = int(14 * sc); cy = y0 + int(44 * sc)
            d.ellipse((x, cy - r, x + 2 * r, cy + r), fill=COR[k]); d.text((x + 2 * r + int(10 * sc), cy - int(19 * sc)), rot, font=F(36), fill=TINTA)
            x += int(2 * r + 10 * sc + d.textlength(rot, font=F(36)) + 44 * sc)
        d.text((int(40 * sc), y0 + HP - int(52 * sc)), "simulação ilustrativa", font=F(30), fill=(130, 136, 146))
        if w:
            desenha_palavra(im, w, t, y0 + int(285 * sc), 108)
    im.save(os.path.join(saida, nome))
print("quadros compostos:", len(os.listdir(saida)))
