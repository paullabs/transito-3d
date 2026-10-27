"""Mede um trecho de voz: duração, nível (rms) e tom mediano (autocorrelação). O tom do Lucas não pode afundar (< ~110 Hz) nem mudar entre trechos.
    python3 kit3d/voz_medida.py a.mp3 [b.mp3 ...]"""
import sys, subprocess, numpy as np

def le(path, sr=16000):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "f32le", "-ac", "1", "-ar", str(sr), "-"], capture_output=True).stdout
    return np.frombuffer(raw, dtype=np.float32), sr

def tom(x, sr, fmin=70, fmax=300):
    out = []; n = int(0.04 * sr); h = int(0.01 * sr)
    for i in range(0, len(x) - 2 * n, h):
        j = x[i:i + 2 * n]
        if np.sqrt(np.mean(j ** 2)) < 0.02:
            continue
        j = j - j.mean(); ac = np.correlate(j, j, "full")[len(j) - 1:]
        lo, hi = int(sr / fmax), int(sr / fmin)
        k = lo + int(np.argmax(ac[lo:hi]))
        if ac[k] > 0.35 * ac[0]:
            out.append(sr / k)
    return float(np.median(out)) if out else float("nan")

if __name__ == "__main__":
    for p in sys.argv[1:]:
        x, sr = le(p)
        ativo = x[np.abs(x) > 0.01]
        rms = 20 * np.log10(np.sqrt(np.mean(ativo ** 2)) + 1e-9)
        print(f"{p.split('/')[-1]:<14} {len(x) / sr:5.2f} s | rms {rms:6.1f} dB | tom {tom(x, sr):5.1f} Hz")
