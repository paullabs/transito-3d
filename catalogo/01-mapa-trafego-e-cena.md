# Mapa, tráfego e cena

- `tb_assets` — Trânsito Brasil 3D: biblioteca de veículos e objetos de via (Blender por script). Tudo em metros, x = frente do veículo, z = cima. Os veículos de um mesmo modelo dividem … · hexrgb(), mat_cor(), mat_pintura(), mat_pintura2(), mat_luz(), brilho_luzes(), MATS(), Malha, m_hatch(), m_sedan()…
- `tb_brilho` — Trânsito Brasil 3D: brilho (bloom) das luzes, fora do Blender. Para o estilo noite. python3 kit3d/tb_brilho.py arquivo.png [mais.png ...]   (sobrescreve)   |   python3 ki… · brilho()
- `tb_cena` — Trânsito Brasil 3D: cena, luz, câmera e render (EEVEE por padrão, Cycles opcional). · limpa(), motor(), mundo(), sol(), camera(), poe_camera(), largura_vista(), render()
- `tb_mapa` — Trânsito Brasil 3D: monta o mapa 3D a partir do JSON do OpenStreetMap (tb_osm.py), em um dos estilos.     import tb_mapa as MP;  mapa = MP.Mapa("transito/dados_osm/estaia… · base_tipo(), largura_via(), chave(), offset(), tracejado(), Mapa
- `tb_osm` — Trânsito Brasil 3D: converte um recorte do OpenStreetMap (.osm em XML, da API 0.6) num JSON limpo em metros. x = leste, y = norte, origem no centro do recorte. Roda fora … · converte()
- `tb_trafego` — Trânsito Brasil 3D: faixas de rodagem e simulação de tráfego (modelo IDM: cada motorista acelera até a sua velocidade desejada e freia para manter distância de quem vai n… · esc_de(), sorteia(), cor_velocidade(), sat(), Faixa, Veic, Trafego
- `tb_xt` — Trânsito Brasil 3D: desenha o diagrama espaço-tempo (roda no python do sistema, que tem matplotlib).     python3 -I kit3d/tb_xt.py dados.json saida.png
