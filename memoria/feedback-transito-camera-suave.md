---
name: feedback-transito-camera-suave
description: Trânsito Brasil 3D — câmera dura e sem sentido; a regra é câmera planejada com ondas suaves, medida em número e nos quadros
metadata:
  type: feedback
---
Em 26/10/2026 o Paulo disse que os movimentos de câmera do Trânsito Brasil 3D estavam "muito durões e sem sentido" e que têm que ser bem suaves, "com ondas bem suaves que se conectem às outras com transições".

**Why:** a câmera era reativa (seguia a fila e o alvo pulava a cada carro que cruzava o limite): centro a 33 m/s, 133 trancos. O suavizador exponencial só disfarçava.

**How to apply:** nunca câmera reativa. Planeje a trajetória (poucas ondas com entrada e saída suaves, velocidade contínua nas emendas, sem inversão nem parada no meio) com `kit/tb_camera_suave.py`; o movimento deve ter motivo (aqui: afastar junto com a fila). Antes de mostrar: `tb_mede_camera.py` (zero trancos, zero paradas, jerk baixo) e a conferência nos quadros reais (calçada sem carros). Mesma regra de feedback-animacao-profissional e feedback-transicoes. Ligado a project-transito-brasil-3d.
