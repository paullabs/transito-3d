"""Trânsito Brasil 3D: brilho (bloom) das luzes, fora do Blender. Para o estilo noite.
    python3 kit3d/tb_brilho.py arquivo.png [mais.png ...]   (sobrescreve)   |   python3 kit3d/tb_brilho.py PASTA"""
import sys, os
import numpy as np
from PIL import Image, ImageFilter


def brilho(caminho, limiar=0.62, forca=0.9):
    im = Image.open(caminho).convert("RGB"); a = np.asarray(im).astype(np.float32) / 255
    lum = a.max(axis=2, keepdims=True)
    claro = np.clip((lum - limiar) / (1 - limiar), 0, 1) * a
    cl = Image.fromarray((claro * 255).astype(np.uint8))
    soma = np.zeros_like(a)
    for r, p in ((3, 0.6), (10, 0.5), (28, 0.4)):
        soma += np.asarray(cl.filter(ImageFilter.GaussianBlur(r * im.width / 1080))).astype(np.float32) / 255 * p
    out = 1 - (1 - a) * (1 - np.clip(soma * forca, 0, 1))
    Image.fromarray((out * 255).astype(np.uint8)).save(caminho)


if __name__ == "__main__":
    for x in sys.argv[1:]:
        fs = [os.path.join(x, f) for f in sorted(os.listdir(x)) if f.endswith(".png")] if os.path.isdir(x) else [x]
        for f in fs:
            brilho(f)
