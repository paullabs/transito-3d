"""Trânsito Brasil 3D, ep. 1, v2: compõe o rascunho em TELA CHEIA (sem painel, sem legenda de cores): a cena de cima, as pílulas de texto no alto e a legenda
UMA PALAVRA POR VEZ numa pílula escura (bounce no ritmo da voz, palavras.json).
    python3 kit3d/compoe_ep1b.py PASTA_DOS_QUADROS SAIDA [--de N --ate M]"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw, ImageFont
import anim_ep1b_planos as AP
SP = AP.SP

quadros_dir, saida = sys.argv[1], sys.argv[2]
op = lambda k, d: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d
os.makedirs(saida, exist_ok=True)
FPS = 24
FONTE = "/System/Library/Fonts/Supplemental/Arial Rounded Bold.ttf"
A0 = sorted(f for f in os.listdir(quadros_dir) if f[:4].isdigit() and f.endswith(".png"))
q0 = Image.open(os.path.join(quadros_dir, A0[0])); sc = q0.width / 1080; W, H = q0.size
F = lambda n: ImageFont.truetype(FONTE, max(8, int(n * sc)))
PAL = []
for w in json.load(open(os.path.join(SP.RAIZ, "roteiros", "voz-transito", "palavras.json"))):
    t = w["txt"].strip().strip(",.:;!?").strip()
    if t:
        PAL.append(dict(txt=t, t0=w["t0"], t1=w["t1"]))
for i, w in enumerate(PAL):
    prox = PAL[i + 1]["t0"] if i + 1 < len(PAL) else w["t1"] + 0.3
    w["fim"] = prox if prox - w["t1"] < 0.30 else w["t1"] + 0.12


def alfa_pilula(t, a, b, fade=0.25):
    return 0.0 if (t < a or t > b) else max(0.0, min(1.0, (t - a) / fade, (b - t) / fade))


def pilula(im, texto, alfa):
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    f = F(50); tw = d.textlength(texto, font=f); pad = int(30 * sc); ph = int(84 * sc); y0 = int(150 * sc)
    box = (W / 2 - tw / 2 - pad, y0, W / 2 + tw / 2 + pad, y0 + ph)
    d.rounded_rectangle(box, radius=int(ph * 0.5), fill=(20, 24, 31, int(240 * alfa)))
    d.text((box[0] + pad, y0 + int(11 * sc)), texto, font=f, fill=(255, 255, 255, int(255 * alfa)))
    return Image.alpha_composite(im.convert("RGBA"), lay).convert("RGB")


def palavra_em(t):
    for w in PAL:
        if w["t0"] <= t < w["fim"]:
            return w
    return None


def palavra(im, w, t):
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    tau = (t - w["t0"]) / 0.25
    esc = 0.55 + 0.55 * (tau / 0.6) if tau < 0.6 else (1.1 - 0.1 * ((tau - 0.6) / 0.4) if tau < 1.0 else 1.0)
    f = F(96 * esc); tw = d.textlength(w["txt"], font=f); pad = int(40 * sc * esc); ph = int(150 * sc * esc); yc = int(1570 * sc)
    box = (W / 2 - tw / 2 - pad, yc - ph / 2, W / 2 + tw / 2 + pad, yc + ph / 2)
    d.rounded_rectangle(box, radius=int(ph * 0.5), fill=(20, 24, 31, 238))
    d.text((W / 2 - tw / 2, yc - 96 * sc * esc * 0.64), w["txt"], font=f, fill=(255, 255, 255, 255))
    return Image.alpha_composite(im.convert("RGBA"), lay).convert("RGB")


de, ate = int(op("--de", "0")), int(op("--ate", str(len(A0) - 1)))
for i in range(de, min(ate, len(A0) - 1) + 1):
    nome = A0[i]; n = int(nome[:4]); t = (n - 1) / FPS
    im = Image.open(os.path.join(quadros_dir, nome)).convert("RGB")
    for a, b, txt in AP.PILULAS:
        al = alfa_pilula(t, a, b)
        if al > 0:
            im = pilula(im, txt, al)
    d = ImageDraw.Draw(im)
    d.text((int(36 * sc), int(60 * sc)), "simulação ilustrativa", font=F(30), fill=(96, 102, 112))
    w = palavra_em(t)
    if w:
        im = palavra(im, w, t)
    im.save(os.path.join(saida, nome))
print("quadros compostos:", len(os.listdir(saida)))
