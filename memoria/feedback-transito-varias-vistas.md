---
name: feedback-transito-varias-vistas
description: Trânsito Brasil 3D — o Paulo quer várias visualizações da mesma cena, incluindo top view plano (ortográfica), não só perspectiva inclinada
metadata:
  type: feedback
---
Em 26/10/2026 o Paulo pediu "outras visualizações também, topview plano" para o Trânsito Brasil 3D.

**Why:** a perspectiva inclinada sozinha não responde a toda pergunta; o topo plano mostra a fila e o espaçamento sem distorção e é como mapa de verdade.

**How to apply:** toda cena nova do trânsito deve sair com várias vistas: `--vista topo` (ortográfica reta, fluxo para cima), `baixa` (por trás, dramática), `diagonal` e `perspectiva`. Cada uma com câmera planejada em onda suave (feedback-transito-camera-suave) e conferida com `tb_mede_camera.py`. Ligado a project-transito-brasil-3d e feedback-transito-legibilidade.
