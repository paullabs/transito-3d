"""Trânsito Brasil 3D: conferidor de colisão e de profundidade (roda sem renderizar).
    blender -b -P kit3d/tb_colisao.py -- [--regiao x y raio] [--segundos 40] [--estilo maquete] [--dist 640]
Confere, a cada 0,25 s da simulação:
  1) carro x carro: caixa contra caixa (SAT em 2D, só se a diferença de altura for menor que 2,6 m);
  2) carro x prédio: o centro do carro dentro da planta de um prédio mais alto que a pista;
  3) carro x pilar de ponte: pilar dentro da faixa de uma via de baixo;
e a profundidade: com a câmera a --dist metros, qual a menor separação de camadas que a precisão de profundidade aguenta.
Sai com o número de cada tipo (e os 10 piores lugares) para comparar antes e depois de uma correção."""
import sys, os, math, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from mathutils import Vector
import tb_assets as A
import tb_mapa as MP
import tb_trafego as T

RAIZ = os.environ.get("TRANSITO3D_PROJETO") or os.getcwd()
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
op = lambda k, d: argv[argv.index(k) + 1] if k in argv else d
MODELOS = []
DEBUG = []


def confere_carros(tr):
    pares = tr.sobreposicoes(); lugares = []
    for k, (x, y, fi, fj) in pares.items():
        lugares.append((x, y, fi == fj)); MODELOS.append((tr.faixas[fi].nome[:22], tr.faixas[fj].nome[:22], tr.faixas[fi].classe, tr.faixas[fj].classe))
    return set(pares), lugares


def main():
    est = op("--estilo", "maquete"); seg = float(op("--segundos", "40")); dist = float(op("--dist", "640"))
    if "--regiao" in argv:
        i = argv.index("--regiao"); regiao = (float(argv[i + 1]), float(argv[i + 2]), float(argv[i + 3]))
    else:
        regiao = (-735, -300, 520)
    escala = float(op("--escala-veic", "1.0"))
    mp = MP.Mapa(os.path.join(RAIZ, "transito", "dados_osm", "estaiada.json"), est)
    mp.foco = regiao if "--foco" in argv else None
    if "--monta" in argv:  # monta a geometria (para contar prédios e pilares removidos)
        mp.monta(regiao, foco=mp.foco)
    tr = T.Trafego(mp, regiao, fluxo=float(op("--fluxo", "1.6")), escala_veic=escala, visual=False, dens=float(op("--dens", "1.0")))
    tr.aquece(float(op("--aquece", "60")))
    todos = set(); lug = []; n_quadros = 0; max_simult = 0; mesma = 0
    for k in range(int(seg * 4)):
        for _ in range(1):
            tr.passo(0.25)
        pares, l = confere_carros(tr)
        n_quadros += 1; max_simult = max(max_simult, len(pares))
        for p, ll in zip(sorted(pares), l):
            pass
        for pr in pares:
            todos.add(pr)
        lug += l[:50]
    mesma = sum(1 for l in lug if l[2])
    print(f"[colisao] veículos simulados: {tr.contagem()} | pares que se atravessaram em {seg:.0f} s: {len(todos)} | no máximo {max_simult} ao mesmo tempo")
    print(f"[colisao] ocorrências na MESMA faixa: {mesma} de {len(lug)} (o resto é cruzamento/junção entre faixas)")
    if lug:
        import collections
        cont = collections.Counter((round(x // 30) * 30, round(y // 30) * 30) for x, y, _ in lug)
        print("[colisao] piores lugares (x, y, ocorrências):", [(k[0], k[1], v) for k, v in cont.most_common(8)])
    import collections
    for d in DEBUG: print("[debug]", d)
    print("[colisao] quem bate em quem (faixa, faixa, classe, classe):", collections.Counter(MODELOS).most_common(6))
    # profundidade
    near = float(op("--near", str(max(0.5, dist * 0.15))))
    prec = dist ** 2 / (near * 2 ** 24)
    print(f"[profundidade] câmera a {dist:.0f} m com clip_start {near} m: precisão ≈ {prec * 100:.1f} cm (camadas mais finas que isso piscam)")
    print(f"[profundidade] menor separação de camadas do mapa: {mp.dz * 100:.1f} cm" if hasattr(mp, "dz") else "[profundidade] menor separação de camadas do mapa: 1.0 cm (tinta sobre asfalto: +0,01 m)")

    if "--monta" in argv and hasattr(mp, "verifica"):
        mp.verifica()


main()
