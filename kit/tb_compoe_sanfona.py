"""Trânsito Brasil 3D: monta os quadros finais da cena do efeito sanfona (1080x1920): cena em cima, legenda em pílula com linha até o carro,
painel de baixo com a legenda de cores e o diagrama espaço-tempo com o cursor do tempo. Roda com o python do sistema (PIL).
    python3 kit3d/tb_compoe_sanfona.py PASTA_DOS_QUADROS SAIDA [--fps 24]   (a pasta tem NNNN.png, xt.png e pos_0.json)"""
import sys, os, json
from PIL import Image, ImageDraw, ImageFont

pasta, saida = sys.argv[1], sys.argv[2]
SEM_NEVOA = "--sem-nevoa" in sys.argv
os.makedirs(saida, exist_ok=True)
FPS = 24
FONTE = "/System/Library/Fonts/Supplemental/Arial Rounded Bold.ttf"
pos = json.load(open(os.path.join(pasta, "pos_0.json")))
xt = Image.open(os.path.join(pasta, "xt.png")).convert("RGB")
quadros = sorted(f for f in os.listdir(pasta) if f[:4].isdigit() and f.endswith(".png"))
q0 = Image.open(os.path.join(pasta, quadros[0]))
sc = q0.width / 1080
W, H, HC = int(1080 * sc), int(1920 * sc), q0.height
F = lambda n: ImageFont.truetype(FONTE, int(n * sc))
TINTA = (27, 31, 39); PAPEL = (243, 241, 236)
COR = {"verde": (34, 197, 94), "amarelo": (255, 194, 26), "vermelho": (255, 59, 48)}
M = dict(left=0.095, right=0.985)
xt = xt.resize((W, int(xt.height * W / xt.width)))
T_FREADA = 1.5

def suave(t, a, b, fade=0.25):
    if t < a or t > b:
        return 0.0
    return max(0.0, min(1.0, min((t - a) / fade, (b - t) / fade)))

def pilula(im, texto, alvo, tam, alfa, cor_fundo=TINTA, cor_texto=(255, 255, 255), acima=True, fixo_y=None):
    """legenda em pílula perto do alvo (x, y normalizados); linha curta até um aro amarelo em volta dele"""
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    f = F(tam); tw = d.textlength(texto, font=f); pad = int(tam * 0.55 * sc); ph = int(tam * sc * 1.55)
    tx, ty = alvo[0] * W, min(max(alvo[1], 0.04), 0.97) * HC
    a = int(255 * alfa)
    cx = min(max(tx, tw / 2 + pad + 14 * sc), W - tw / 2 - pad - 14 * sc)
    y = fixo_y * sc if fixo_y is not None else (ty - 150 * sc - ph if acima and ty > 330 * sc else min(ty + 110 * sc, HC - ph - 24 * sc))
    box = (cx - tw / 2 - pad, y, cx + tw / 2 + pad, y + ph)
    ponta = box[3] if y < ty else box[1]
    r = int(24 * sc)
    d.line([(cx if abs(cx - tx) < 1 else tx, ponta), (tx, ty + (-r if y < ty else r))], fill=(245, 197, 24, a), width=max(3, int(6 * sc)))
    d.ellipse((tx - r, ty - r, tx + r, ty + r), outline=(245, 197, 24, a), width=max(3, int(6 * sc)))
    d.rounded_rectangle(box, radius=int(tam * sc * 0.7), fill=(*cor_fundo, a))
    d.text((box[0] + pad, y + int(tam * sc * 0.2)), texto, font=f, fill=(*cor_texto, a))
    return Image.alpha_composite(im.convert("RGBA"), lay).convert("RGB")


def contador(im, texto, alfa, y=60, tam=44):
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    f = F(tam); tw = d.textlength(texto, font=f); pad = int(tam * 0.55 * sc); ph = int(tam * sc * 1.5)
    box = (W / 2 - tw / 2 - pad, y * sc, W / 2 + tw / 2 + pad, y * sc + ph); a = int(255 * alfa)
    d.rounded_rectangle(box, radius=int(tam * sc * 0.7), fill=(255, 59, 48, a))
    d.text((box[0] + pad, box[1] + int(tam * sc * 0.18)), texto, font=f, fill=(255, 255, 255, a))
    return Image.alpha_composite(im.convert("RGBA"), lay).convert("RGB")


def nevoa(cena, frac=0.26, cor=(231, 232, 234)):
    """o fundo some na névoa clara: menos carrinhos distantes brigando pela atenção"""
    w, h = cena.size; n = int(h * frac)
    grad = Image.new("L", (1, n)); 
    for yy in range(n):
        t = 1 - yy / n; grad.putpixel((0, yy), int(255 * 0.92 * t * t))
    grad = grad.resize((w, n)); base = Image.new("RGB", (w, n), cor)
    topo = cena.crop((0, 0, w, n)); topo = Image.composite(base, topo, grad); cena.paste(topo, (0, 0))
    return cena


for i, nome in enumerate(quadros):
    n = int(nome[:4]); t = (n - 1) / FPS
    cena = Image.open(os.path.join(pasta, nome)).convert("RGB")
    if not SEM_NEVOA:
        cena = nevoa(cena)
    im = Image.new("RGB", (W, H), PAPEL); im.paste(cena, (0, 0))
    d = ImageDraw.Draw(im)
    p = pos.get(str(n - 1), {})
    a = suave(t, 1.0, 5.4)
    if a > 0 and "freio" in p:
        im = pilula(im, "1 motorista freia", p["freio"], 52, a)
    b = suave(t, 5.8, 12.5)
    if b > 0 and "cauda" in p:
        im = pilula(im, "a fila cresce para trás", p["cauda"], 52, b, acima=False)
    if b > 0 and p.get("n_parados"):
        im = contador(im, f"{p['n_parados']} carros devagar ou parados", b)
    d = ImageDraw.Draw(im)
    # painel de baixo
    y0 = HC
    d.line([(0, y0), (W, y0)], fill=(215, 211, 203), width=max(2, int(3 * sc)))
    x = int(48 * sc)
    for k, rot in (("verde", "andando"), ("amarelo", "devagar"), ("vermelho", "parado")):
        r = int(15 * sc); cy = y0 + int(46 * sc)
        d.ellipse((x, cy - r, x + 2 * r, cy + r), fill=COR[k])
        d.text((x + 2 * r + int(12 * sc), cy - int(21 * sc)), rot, font=F(38), fill=TINTA)
        x += int(2 * r + 12 * sc + d.textlength(rot, font=F(38)) + 56 * sc)
    im.paste(xt, (0, y0 + int(84 * sc)))
    cx = int((M["left"] + min(t, 12) / 12 * (M["right"] - M["left"])) * W)
    ytop = y0 + int(84 * sc) + int(xt.height * 0.16); ybot = y0 + int(84 * sc) + int(xt.height * 0.8)
    d.line([(cx, ytop), (cx, ybot)], fill=TINTA, width=max(3, int(4 * sc)))
    d.text((int(48 * sc), H - int(86 * sc)), "Sem batida, sem obra: só uma freada.", font=F(40), fill=TINTA)
    im.save(os.path.join(saida, nome))
print(f"{len(quadros)} quadros em {saida}")
