---
name: project-transito-ep1-rascunho
description: "Trânsito Brasil 3D ep. 1, rascunho animado v1 (26/10/2026): abertura aérea, cena do espaço, código e o que falta"
metadata:
  node_type: memory
  type: project
  modified: 2026-10-26T23:03:54.940Z
---

Decupagem aprovada em 26/10/2026 com dois pedidos: abrir com vista aérea da Ponte Estaiada e da Marginal SEM carros, e incluir a cena do espaço. Feito o rascunho animado v1: `personagem/transito/anim/ep1-rascunho-v1.mp4` (85,9 s, 540x960, voz Lucas, sem efeitos sonoros). Esperando aprovação.

Código (`kit/`): `anim_ep1_planos.py` (14 planos: o 0 é a aérea, de 0 a 3,18 s; cortes no meio das pausas; pílulas), `anim_ep1.py` (`plano PASTA` mede câmera e colisão; `render PASTA --escala 0.5 --parte i/n --de --ate`), `compoe_ep1.py` (painel de 285 px com legenda de uma palavra por vez, pílulas e o diagrama do plano 7). Render: `render_transito/ep1_v1` (quadros), `ep1_v1_final` (compostos), `ep1_plano` (camera.json, xt.png). Planos 10 e 11 = cena do espaço (classe `Espaco`: freada leve do A, B recua, poste e régua de 2 s).
Medido: 14 planos de câmera OK, 0 sobreposições, só 1 salto fora dos cortes (uma moto que entra no quadro).

**Why:** o plano 4 tinha um carro grande em primeiro plano tapando a ação; corrigido (câmera mais alta e de lado, `story_ep1_planos.PLANOS` linha 4; cópia antiga `story_ep1_planos_v1_antes_plano4.py`) e só esses quadros foram refeitos (`--de 494 --ate 634`).
**How to apply:** pendências honestas: a voz do trecho 12 ficou grave (~100 Hz, não tratada); planos 8 e 9 passam a 2x (time-lapse); a cena do espaço é encenada ("simulação ilustrativa"); o diagrama do plano 7 é pequeno; o `rm` de `ep1_teste/*` foi bloqueado pela segurança (não contornar, usar pasta nova). Depois da aprovação: som (trilha clássica sutil, um efeito por ação), render cheio 1080x1920, pós. Liga com project-transito-brasil-3d, project-transito-ep1-voz-decupagem e feedback-transito-camera-suave.

**Atualização (26/10, noite):** o v1 foi recusado (ver feedback-transito-so-de-cima). Refeito como v2 só de cima, tela cheia, 6 planos: `personagem/transito/anim/ep1-rascunho-v2-so-de-cima.mp4`; código `kit/anim_ep1b_planos.py`, `anim_ep1b.py`, `compoe_ep1b.py`. Esperando aprovação. Limite conhecido: câmera quase parada por instantes nos planos 1 e 2 (segue o carro que para).

**Atualização (27/10):** roteiro cortado para 8 falas (~43 s), voz Lucas regerada em `roteiros/voz-transito-v2/`, rascunho v3 `personagem/transito/anim/ep1-rascunho-v3-curto.mp4` (freada aos 2 s, um plano longo de cima). Esperando aprovação. Ver feedback-roteiro-direto-parada-ja.
