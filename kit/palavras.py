"""Tempo de cada palavra da narração (para sincronizar gestos, selos e legendas).
python3 palavras.py ../roteiros/voz-transito ../roteiros/transito-ep1.json
Roda o Whisper local em cada frase, alinha as palavras do roteiro (o que aparece na legenda) com as do Whisper
e grava PASTA/palavras.json = [{"txt", "t0", "t1", "frase"}, ...] em segundos do vídeo."""
import json, os, re, subprocess, sys, unicodedata, difflib, tempfile

MODEL = "mlx-community/whisper-large-v3-turbo"
NUM = {"quarenta mil": ["40", "mil"], "cinquenta e dois": ["52"], "cinco": ["5"], "cem": ["100"], "um": ["1"], "dois": ["2"],
       "três": ["3"], "quatro": ["4"], "mil": ["mil", "1000", "1.000"]}


def norm(w):
    w = unicodedata.normalize("NFD", w.lower())
    w = "".join(c for c in w if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]", "", w)


def whisper_words(aiff, tmp):
    stem = os.path.splitext(os.path.basename(aiff))[0]
    wav = os.path.join(tmp, stem + ".wav")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", aiff, "-ar", "16000", "-ac", "1", wav], check=True)
    subprocess.run(["mlx_whisper", wav, "--model", MODEL, "--language", "pt", "--word-timestamps", "True",
                    "--output-format", "json", "--output-dir", tmp], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    j = json.load(open(os.path.join(tmp, stem + ".json")))
    return [(w["word"].strip(), w["start"], w["end"]) for seg in j["segments"] for w in seg.get("words", [])]


def align(script_words, ww, t_off, dur):
    """alinha as palavras do roteiro com as do Whisper; o que não casar é interpolado entre as âncoras"""
    a = [norm(w) for w in script_words]; b = [norm(w[0]) for w in ww]
    sm = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
    t0 = [None] * len(a); t1 = [None] * len(a)
    for blk in sm.get_matching_blocks():
        for k in range(blk.size):
            t0[blk.a + k] = ww[blk.b + k][1]; t1[blk.a + k] = ww[blk.b + k][2]
    s0 = ww[0][1] if ww else 0.0; s1 = ww[-1][2] if ww else dur
    # âncoras de começo/fim da fala
    idx = [i for i, v in enumerate(t0) if v is not None]
    if not idx:
        L = [len(w) + 1 for w in script_words]; tot = sum(L); acc = s0
        for i, l in enumerate(L):
            t0[i] = acc; acc += (s1 - s0) * l / tot; t1[i] = acc
    else:
        for i in range(len(a)):
            if t0[i] is not None:
                continue
            lo = max([j for j in idx if j < i], default=None); hi = min([j for j in idx if j > i], default=None)
            gl = [k for k in range(len(a)) if t0[k] is None and (lo is None or k > lo) and (hi is None or k < hi)]
            ta = t1[lo] if lo is not None else s0; tb = t0[hi] if hi is not None else s1
            L = [len(script_words[k]) + 1 for k in gl]; tot = sum(L); acc = ta
            for k, l in zip(gl, L):
                t0[k] = acc; acc += (tb - ta) * l / tot; t1[k] = acc
    return [(t_off + x, t_off + y) for x, y in zip(t0, t1)]


def main(pasta, roteiro):
    T = json.load(open(os.path.join(pasta, "tempos.json")))
    out = []
    with tempfile.TemporaryDirectory() as tmp:
        for f in T["falas"]:
            ww = whisper_words(f["arquivo"], tmp)
            txt = f["legenda"] if f.get("legenda") else f["texto"]
            words = txt.split()
            times = align(words, ww, f["inicio"], f["duracao"])
            for w, (x, y) in zip(words, times):
                out.append(dict(txt=w, t0=round(x, 3), t1=round(y, 3), frase=f["n"]))
            print(f["n"], " ".join(f"{w}@{x:.2f}" for w, (x, y) in zip(words, times)))
    json.dump(out, open(os.path.join(pasta, "palavras.json"), "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
