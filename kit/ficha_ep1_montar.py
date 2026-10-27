"""Monta a prancha da ficha do ep. 1 do Trânsito Brasil 3D a partir de ficha-{tipo,objetos,topo}.png (system python, PIL).
    python3 kit3d/ficha_ep1_montar.py personagem/transito/ficha-ep1"""
import sys, textwrap
from PIL import Image, ImageDraw, ImageFont
D = sys.argv[1].rstrip("/") + "/"
F = lambda n: ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Rounded Bold.ttf', n)
FN = lambda n: ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', n)
tipo, obj, topo = (Image.open(D + f'ficha-{k}.png').convert('RGB') for k in ('tipo', 'objetos', 'topo')); W = 1920
def faixa(im, titulo, sub):
    linhas = textwrap.wrap(sub, width=135); h = 70 + 30 * len(linhas)
    out = Image.new('RGB', (W, im.height + h), '#15181d'); d = ImageDraw.Draw(out)
    d.text((28, 12), titulo, font=F(40), fill='white')
    for i, l in enumerate(linhas): d.text((28, 64 + 30 * i), l, font=FN(25), fill='#b8c0cc')
    out.paste(im, (0, h)); return out
a = faixa(tipo, "ELENCO: OS VEÍCULOS", "Em cima, por TIPO: carro branco, táxi amarelo, ônibus verde, caminhão laranja, moto rosa, emergência. Embaixo, por VELOCIDADE: verde andando bem, amarelo devagar, vermelho parado. Carros 12% maiores que o real; a moto fica no tamanho real para caber no corredor.")
b = faixa(obj, "OBJETOS DA CENA", "Aro amarelo no carro que freia, poste (a referência), régua dos 2 segundos no chão e legendas em pílula escura. A régua só ilustra a regra: a simulação não mede a distância real.")
c = faixa(topo, "OS MESMOS OBJETOS, DE CIMA RETO (TOPO PLANO)", "Ortográfica, sem perspectiva. Aqui o fluxo vai para a direita; na cena, o fluxo vai para cima da tela.")
board = Image.new('RGB', (W, a.height + b.height + c.height + 30), '#0b0d10'); y = 0
for im in (a, b, c): board.paste(im, (0, y)); y += im.height + 15
board.save(D + 'ficha-transito-ep1.png'); print(board.size)
