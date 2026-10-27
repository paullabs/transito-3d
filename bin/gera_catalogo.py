#!/usr/bin/env python3
"""Gera CATALOGO.md: um índice de uma linha por módulo do kit (para o Claude achar a peça pronta sem ler o código).
    python3 bin/gera_catalogo.py            # escreve CATALOGO.md na raiz do plugin"""
import ast, glob, os, re, unicodedata
RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
GRUPOS = [
    ("Mapa, tráfego e cena", r"^(tb_mapa|tb_osm|tb_trafego|tb_assets|tb_cena|tb_xt|tb_brilho)"),
    ("Câmera planejada e conferências", r"^(tb_camera|tb_mede|tb_colisao)"),
    ("Cenas prontas, ficha e testes", r"^(tb_sanfona|tb_teste|tb_ficha|tb_compoe|tb_story|ficha_ep1|story_ep1)"),
    ("Animação do ep. 1 (planos, render, composição)", r"^(anim_ep1|compoe_ep1)"),
    ("Voz e palavras", r"^(voz|palavras)"),
]
def grupo(nome):
    for g, rx in GRUPOS:
        if re.match(rx, nome): return g
    return "Outros"
def resumo(doc):
    if not doc: return ""
    l = " ".join(doc.strip().split("\n")[0:2]).strip()
    return (l[:170] + "…") if len(l) > 170 else l
tab = {}
for f in sorted(glob.glob(os.path.join(RAIZ, "kit", "*.py"))):
    nome = os.path.basename(f)[:-3]
    try: t = ast.parse(open(f, encoding="utf-8").read())
    except Exception: continue
    pub = []
    for n in t.body:
        if isinstance(n, (ast.FunctionDef, ast.ClassDef)) and not n.name.startswith("_"):
            pub.append(n.name + ("()" if isinstance(n, ast.FunctionDef) else ""))
    tab.setdefault(grupo(nome), []).append((nome, resumo(ast.get_docstring(t)), pub))
os.makedirs(os.path.join(RAIZ, "catalogo"), exist_ok=True)
for f in glob.glob(os.path.join(RAIZ, "catalogo", "*.md")): os.remove(f)
idx = ["# Catálogo do kit", "",
       "**Antes de escrever código novo, procure aqui.** Quase tudo (mapa, simulação de tráfego, carros, câmera planejada, conferências, voz, render) já existe em `kit/`.",
       "Abra só o arquivo do assunto que você precisa: cada um tem uma linha por módulo, com o que faz e as funções públicas.",
       "Assinaturas de um módulo: `grep -n '^def \\|^class ' kit/<modulo>.py`. Scripts rodam com `blender -b -P kit/<script>.py -- ARGS` (o cabeçalho de cada um explica os argumentos).", ""]
for n, (g, _) in enumerate(GRUPOS + [("Outros", "")], 1):
    if g not in tab: continue
    arq = f"{n:02d}-" + re.sub(r"[^a-z0-9]+", "-", unicodedata.normalize("NFD", g.lower()).encode("ascii", "ignore").decode()).strip("-") + ".md"
    linhas = [f"# {g}", ""]
    for nome, r, pub in tab[g]:
        lista = ", ".join(pub[:10]) + ("…" if len(pub) > 10 else "")
        linhas.append(f"- `{nome}` — {r or 'sem descrição'}" + (f" · {lista}" if lista else ""))
    open(os.path.join(RAIZ, "catalogo", arq), "w", encoding="utf-8").write("\n".join(linhas) + "\n")
    idx.append(f"## {g} → `catalogo/{arq}`")
    idx.append(", ".join(f"`{x[0]}`" for x in tab[g])); idx.append("")
open(os.path.join(RAIZ, "CATALOGO.md"), "w", encoding="utf-8").write("\n".join(idx))
print("módulos:", sum(len(v) for v in tab.values()), "→ CATALOGO.md + catalogo/")
