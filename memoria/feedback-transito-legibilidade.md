---
name: feedback-transito-legibilidade
description: Trânsito Brasil 3D — o Paulo recusou o primeiro teste por falta de contraste, informação demais e colisão/piscadas; regras para o mapa didático
metadata:
  type: feedback
---
No primeiro teste do Trânsito Brasil 3D (26/10/2026) o Paulo disse: "não tem contraste, não dá para entender o trânsito na via expressa; vai ter muita informação na explicação; muita colisão e objetos piscando".

**Why:** carros pequenos, escuros e parecidos sobre asfalto escuro, com 5 pistas e rampas ao mesmo tempo, e sem nada dizendo o que olhar. Os problemas técnicos eram z-fighting (`clip_start` 0,5 com camadas de 1 cm), carros se atravessando em cruzamentos e carro preso na ponta da faixa.

**How to apply:** um plano = uma ideia. Mapa em tons claros e só a via do assunto em asfalto escuro; carros grandes e brilhantes, coloridos pela velocidade (verde/amarelo/vermelho) ou pelo tipo; legenda em pílula com aro no objeto; faixas vizinhas mais vazias. Câmera junto com o fenômeno. Antes de mostrar: rodar `kit/tb_colisao.py` (zero pares) e olhar um recorte 1:1 de linha pintada. Ligado a project-transito-brasil-3d, feedback-espaco-entre-objetos e feedback-cenario-limpo.
