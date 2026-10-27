"""Trânsito Brasil 3D: desenha o diagrama espaço-tempo (roda no python do sistema, que tem matplotlib).
    python3 -I kit3d/tb_xt.py dados.json saida.png
Eixo x = tempo, eixo y = posição na pista; cada carro é uma linha colorida pela velocidade (verde = livre, vermelho = parado).
Opções no JSON: tam (largura, altura em polegadas), fundo, cursor (tempo atual em s, linha vertical), transparente."""
import sys, json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.colors import LinearSegmentedColormap, Normalize
import numpy as np

d = json.load(open(sys.argv[1]))
cmap = LinearSegmentedColormap.from_list("vel", [(p, c) for p, c in d["escala"]])
tam = d.get("tam", [5.4, 4.6]); fundo = d.get("fundo", "#ffffff"); ink = d.get("tinta", "#1b1f27")
por_id = {}
for t, lst in d["xt"]:
    for k, s, v in lst:
        por_id.setdefault(k, []).append((t, s, v))
fig, ax = plt.subplots(figsize=tam, dpi=d.get("dpi", 200), facecolor=fundo); ax.set_facecolor(fundo)
segs, cols = [], []
for pts in por_id.values():
    for (t0, s0, v0), (t1, s1, v1) in zip(pts, pts[1:]):
        if abs(s1 - s0) < 30:
            segs.append([(t0, s0), (t1, s1)]); cols.append(v1 / d.get("vref", d["vmax"]))
ax.add_collection(LineCollection(segs, array=np.array(cols), cmap=cmap, norm=Normalize(0, 1), linewidths=d.get("lw", 1.6)))
ax.autoscale()
if d.get("xlim"): ax.set_xlim(*d["xlim"])
if d.get("ylim"): ax.set_ylim(*d["ylim"])
ax.set_xlabel("tempo (s)", fontsize=15, color=ink); ax.set_ylabel("posição (m)", fontsize=15, color=ink)
ax.set_title(d.get("titulo", ""), fontsize=18, fontweight="bold", color=ink, loc="left")
ax.tick_params(colors=ink, labelsize=13)
for sp in ("top", "right"):
    ax.spines[sp].set_visible(False)
for sp in ("left", "bottom"):
    ax.spines[sp].set_color(ink)
if d.get("marca"):
    t, s, txt = d["marca"]
    ax.annotate(txt, xy=(t, s), xytext=(t + 3.0, s + 55), fontsize=21, fontweight="bold", color=ink,
                arrowprops=dict(arrowstyle="->", lw=1.6, color=ink))
if d.get("cursor") is not None:
    ax.axvline(d["cursor"], color=ink, lw=1.4, ls="--")
if d.get("margens"):
    fig.subplots_adjust(**d["margens"])
else:
    fig.tight_layout()
fig.savefig(sys.argv[2], transparent=d.get("transparente", False)); plt.close(fig)
