"""Trânsito Brasil 3D: mede o movimento da câmera (roda no python do sistema).
    python3 kit3d/tb_mede_camera.py camera.json [saida.png]
Para cada grandeza (posição da câmera, centro, distância, elevação): velocidade, aceleração e jerk por segundo.
TRANCO = o jerk passa de um limite (a velocidade muda de uma vez, sem curva de entrada e saída).
Saída: resumo no terminal e, se pedido, o gráfico."""
import sys, json, math

d = json.load(open(sys.argv[1])); fps = d["fps"]; L = d["log"]
def serie(k): return [q[k] for q in L]
def deriv(v): return [(v[i + 1] - v[i - 1]) * fps / 2 for i in range(1, len(v) - 1)]
def pos3():
    return [math.sqrt(q["x"] ** 2 + q["y"] ** 2 + q["z"] ** 2) for q in L]

def deriv3(vs):
    """derivada de uma série de vetores (x, y, z): componente a componente"""
    return [tuple((vs[i + 1][k] - vs[i - 1][k]) * fps / 2 for k in range(3)) for i in range(1, len(vs) - 1)]

def norma(vs): return [math.sqrt(x * x + y * y + z * z) for x, y, z in vs]

def resumo3(nome, lim_jerk):
    """a câmera no espaço: velocidade, aceleração e jerk do VETOR posição (não do módulo)"""
    P = [(q["x"], q["y"], q["z"]) for q in L]
    v3 = deriv3(P); a3 = deriv3(v3); j3 = deriv3(a3)
    vel, acc, jer = norma(v3), norma(a3), norma(j3)
    tr = [round((i + 3) / fps, 2) for i, x in enumerate(jer) if x > lim_jerk]
    print(f"{nome:<18} vel máx {max(vel):6.2f} m/s | acel máx {max(acc):6.2f} m/s² | jerk máx {max(jer):7.2f} m/s³ | trancos: {len(tr)} {tr[:8]}")
    pa = paradas(vel)
    print(f"{'':<18} velocidade mínima no meio: {min(vel[len(vel)//8: -len(vel)//8]):.2f} m/s ({100 * min(vel[len(vel)//8: -len(vel)//8]) / max(vel):.0f}% do pico) | PARADAS: {pa or 'nenhuma'}")
    return vel, acc, jer

def resumo(nome, v, un, lim_jerk):
    vel = deriv(v); acc = deriv(vel); jer = deriv(acc)
    pv, pa, pj = max(map(abs, vel)), max(map(abs, acc)), max(map(abs, jer))
    # inversões de sentido da velocidade (câmera que vai e volta) e trancos (jerk acima do limite)
    sinais = [1 if x > 0.02 * pv else -1 if x < -0.02 * pv else 0 for x in vel]
    inv = sum(1 for a, b in zip(sinais, sinais[1:]) if a * b < 0)
    tr = [round((i + 2) / fps, 2) for i, x in enumerate(jer) if abs(x) > lim_jerk]
    print(f"{nome:<18} vel máx {pv:6.2f} {un}/s | acel máx {pa:6.2f} {un}/s² | jerk máx {pj:7.2f} {un}/s³ | inversões {inv} | trancos: {len(tr)} {tr[:8]}")
    return vel, acc, jer

def paradas(vs, frac=0.15, janela=12):
    """a velocidade cai a menos de 15% do pico e volta a subir: a câmera quase para no meio do movimento (anda, para, anda)"""
    pico = max(vs); out = []
    for i in range(2, len(vs) - 2):
        if vs[i] <= min(vs[i - 1], vs[i + 1]):
            antes = max(vs[max(0, i - janela):i]); depois = max(vs[i + 1:i + janela + 1])
            if min(antes, depois) > 0.2 * pico and vs[i] < frac * min(antes, depois):
                out.append(round((i + 1) / fps, 2))
    return out

print(f"{len(L)} quadros a {fps} qps")
res = {}
res["centro (m)"] = resumo("centro (m)", serie("cs"), "m", 14.0)
res["distância (m)"] = resumo("distância (m)", serie("dist"), "m", 6.0)
res["elevação (°)"] = resumo("elevação (°)", serie("elev"), "°", 6.0)
res["câmera 3D (m)"] = resumo3("câmera 3D (m)", 20.0)
if len(sys.argv) > 2:
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    t = [i / fps for i in range(len(L))]
    fig, ax = plt.subplots(4, 2, figsize=(11, 8), sharex=True)
    for r, (nome, k, un) in enumerate((("centro", "cs", "m"), ("distância", "dist", "m"), ("elevação", "elev", "°"))):
        ax[r][0].plot(t, serie(k), lw=2); ax[r][0].set_ylabel(f"{nome} ({un})")
        vel, acc, jer = res[{"centro": "centro (m)", "distância": "distância (m)", "elevação": "elevação (°)"}[nome]]
        ax[r][1].plot(t[1:-1], vel, lw=1.8, label="velocidade"); ax[r][1].plot(t[2:-2], acc, lw=1.2, label="aceleração", alpha=.7)
        ax[r][1].axhline(0, color="#999", lw=.7)
        if r == 0: ax[r][1].legend(fontsize=8)
    ax[3][0].plot(t[3:-3], deriv(deriv(deriv(serie("cs")))), lw=1.2, color="#c0392b"); ax[3][0].set_ylabel("jerk do centro (m/s³)")
    ax[3][1].plot(t[1:-1], res["câmera 3D (m)"][0][:len(t[1:-1])] if len(res["câmera 3D (m)"][0]) == len(t[1:-1]) else res["câmera 3D (m)"][0], lw=1.8, color="#2c3e50"); ax[3][1].set_ylabel("velocidade 3D (m/s)")
    for a in ax[3]: a.set_xlabel("tempo (s)")
    fig.tight_layout(); fig.savefig(sys.argv[2], dpi=110)
