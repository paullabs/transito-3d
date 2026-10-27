# Câmera planejada e conferências

- `tb_camera_suave` — Trânsito Brasil 3D: curvas de câmera suaves (python puro, sem Blender). A câmera é PLANEJADA, não reativa: cada movimento é uma onda (entra devagar, passa pelo meio mais … · sstep5(), valor(), escala_tempo(), serie_suave(), filtra()
- `tb_colisao` — Trânsito Brasil 3D: conferidor de colisão e de profundidade (roda sem renderizar).     blender -b -P kit3d/tb_colisao.py -- [--regiao x y raio] [--segundos 40] [--estilo … · confere_carros(), main()
- `tb_mede_camera` — Trânsito Brasil 3D: mede o movimento da câmera (roda no python do sistema).     python3 kit3d/tb_mede_camera.py camera.json [saida.png] · serie(), deriv(), pos3(), deriv3(), norma(), resumo3(), resumo(), paradas()
