# Voz e palavras

- `palavras` — Tempo de cada palavra da narração (para sincronizar gestos, selos e legendas). python3 palavras.py ../roteiros/voz-transito ../roteiros/transito-ep1.json · norm(), whisper_words(), align(), main()
- `voz_eleven` — Narração da ElevenLabs (um arquivo só) → narracao.wav + tempos.json + palavras.json no mesmo formato da voz do Mac. python3 voz_eleven.py ../roteiros/voz-transito ../rote… · main()
- `voz_medida` — Mede um trecho de voz: duração, nível (rms) e tom mediano (autocorrelação). O tom do Lucas não pode afundar (< ~110 Hz) nem mudar entre trechos. python3 kit3d/voz_medida.… · le(), tom()
- `voz_monta_transito` — Trânsito Brasil 3D, ep. 1: monta a narração a partir dos 13 trechos do Lucas (roteiros/voz-transito/curtos/cNN.mp3), SEM mexer no tom: corta as pontas, highpass 70 Hz, +2… · le(), main()
- `voz_monta_transito2` — Trânsito Brasil 3D, ep. 1: monta a narração a partir dos 9 trechos do Lucas (roteiros/voz-transito/curtos/cNN.mp3), SEM mexer no tom: corta as pontas, highpass 70 Hz, +2,… · le(), main()
