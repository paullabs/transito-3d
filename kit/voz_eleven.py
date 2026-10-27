"""Narração da ElevenLabs (um arquivo só) → narracao.wav + tempos.json + palavras.json no mesmo formato da voz do Mac.
python3 voz_eleven.py ../roteiros/voz-transito ../roteiros/transito-ep1.json take1.mp3
Alinha as palavras da legenda com as do Whisper (palavras.align) no texto inteiro e corta as frases pelas palavras."""
import json, os, subprocess, sys, tempfile
import palavras as PW

LEAD = 0.3                                   # respiro antes da primeira palavra
TAIL = 1.4                                   # silêncio no fim para o último olhar e a música fecharem


def main(pasta, roteiro, take):
    R = json.load(open(roteiro))
    falas = []
    for bi, b in enumerate(R["blocos"]):
        for f in b["falas"]:
            falas.append(dict(n=len(falas) + 1, bloco=bi, nivel=b["nivel"], texto=f["fala"], legenda=f.get("legenda", f["fala"])))
    wav = os.path.join(pasta, "narracao.wav")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", os.path.join(pasta, take), "-af", f"adelay={int(LEAD * 1000)}:all=1,apad=pad_dur={TAIL}",
                    "-ar", "48000", "-ac", "2", wav], check=True)
    dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", wav]))
    with tempfile.TemporaryDirectory() as tmp:
        ww = PW.whisper_words(wav, tmp)
    ww = [w for w in ww if w[1] < dur - 0.05 and w[2] - w[1] > 0.0]
    words = [(w, f["n"]) for f in falas for w in f["legenda"].split()]
    times = PW.align([w for w, _ in words], ww, 0.0, dur)
    raw = subprocess.check_output(["ffmpeg", "-v", "error", "-i", wav, "-ac", "1", "-ar", "8000", "-f", "s16le", "-"])
    import numpy as np
    x = np.frombuffer(raw, np.int16).astype(float) / 32768; e = np.sqrt(np.convolve(x * x, np.ones(80) / 80, "same"))
    onset = float(np.argmax(e > 0.02)) / 8000                 # o Whisper costuma pôr a 1ª palavra em 0,0
    times[0] = (max(times[0][0], onset), max(times[0][1], onset + 0.1))
    pal = [dict(txt=w, t0=round(x, 3), t1=round(y, 3), frase=n) for (w, n), (x, y) in zip(words, times)]
    for f in falas:
        ws = [p for p in pal if p["frase"] == f["n"]]
        f["inicio"] = ws[0]["t0"]; f["duracao"] = round(ws[-1]["t1"] - ws[0]["t0"], 3); f["arquivo"] = wav
        print(f'{f["n"]:2d} {f["inicio"]:6.2f} {f["duracao"]:5.2f}  {f["legenda"]}')
    T = dict(titulo=R["titulo"], voz="ElevenLabs " + take, total=round(dur, 2), falas=falas)
    json.dump(T, open(os.path.join(pasta, "tempos.json"), "w"), ensure_ascii=False, indent=1)
    json.dump(pal, open(os.path.join(pasta, "palavras.json"), "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main(*sys.argv[1:4])
