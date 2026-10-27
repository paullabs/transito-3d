"""Trânsito Brasil 3D, ep. 1: monta a narração a partir dos 13 trechos do Lucas (roteiros/voz-transito/curtos/cNN.mp3), SEM mexer no tom:
corta as pontas, highpass 70 Hz, +2,5 dB a 3,2 kHz (consoantes), -1,5 dB a 180 Hz, compressor 2,5:1, nivela cada trecho no mesmo rms e junta com pausas.
Depois roda voz_eleven.py (narracao.wav, tempos.json, palavras.json).
    python3 kit3d/voz_monta_transito.py"""
import os, subprocess, sys, json
import numpy as np
AQUI = os.path.dirname(os.path.abspath(__file__)); RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, AQUI)
PASTA = os.path.join(RAIZ, "roteiros", "voz-transito"); CURTOS = os.path.join(PASTA, "curtos")
ALVO_DB = -20.5            # rms (só nas partes com voz) de todos os trechos
ATEMPO = 1.06             # só velocidade (não mexe no tom): 2,9 palavras/s naturais -> ~3,1
PAUSA = {2: 0.55, 12: 0.50}  # pausa DEPOIS desse trecho (fim do gancho; antes do fecho); as outras: 0,40 s
PAUSA_PADRAO = 0.40
SR = 48000
FILTRO = "highpass=f=70,equalizer=f=3200:t=q:w=1:g=2.5,equalizer=f=180:t=q:w=1:g=-1.5,acompressor=threshold=-20dB:ratio=2.5:attack=8:release=120,atempo=1.06"


def le(p):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", p, "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"], capture_output=True).stdout
    return np.frombuffer(raw, dtype=np.float32).copy()


def main():
    partes = []; rel = []
    for n in range(1, 14):
        x = le(os.path.join(CURTOS, f"c{n:02d}.mp3"))
        env = np.abs(x); ativo = np.where(env > 10 ** (-45 / 20))[0]
        i0 = max(ativo[0] - int(0.06 * SR), 0); i1 = min(ativo[-1] + int(0.14 * SR), len(x))
        x = x[i0:i1]
        tmp = os.path.join(PASTA, "_t.wav")
        np.save(os.path.join(PASTA, "_t.npy"), x)
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-", "-af", FILTRO, "-ar", str(SR), tmp],
                       input=x.tobytes(), check=True)
        y = le(tmp); act = y[np.abs(y) > 0.01]
        db = 20 * np.log10(np.sqrt(np.mean(act ** 2)) + 1e-9); g = 10 ** ((ALVO_DB - db) / 20)
        y = np.clip(y * g, -0.98, 0.98)
        partes.append(y); rel.append((n, len(y) / SR, db, 20 * np.log10(g)))
    saida = []
    for n, y in enumerate(partes, 1):
        saida.append(y)
        if n < len(partes):
            saida.append(np.zeros(int(PAUSA.get(n, PAUSA_PADRAO) * SR), dtype=np.float32))
    full = np.concatenate(saida)
    wav = os.path.join(PASTA, "voz_montada.wav")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-", wav], input=full.tobytes(), check=True)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", wav, "-b:a", "192k", os.path.join(PASTA, "voz.mp3")], check=True)
    for n, d, db, g in rel:
        print(f"trecho {n:2d}: {d:5.2f} s  (rms {db:6.1f} dB, ganho {g:+.1f} dB)")
    print(f"total montado: {len(full) / SR:.2f} s")
    for f in ("_t.wav", "_t.npy"):
        try: os.remove(os.path.join(PASTA, f))
        except OSError: pass
    import voz_eleven
    voz_eleven.main(PASTA, os.path.join(RAIZ, "roteiros", "transito-ep1.json"), "voz.mp3")


if __name__ == "__main__":
    main()
