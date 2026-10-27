# Cenas prontas, ficha e testes

- `ficha_ep1_montar` — Monta a prancha da ficha do ep. 1 do Trânsito Brasil 3D a partir de ficha-{tipo,objetos,topo}.png (system python, PIL). python3 kit3d/ficha_ep1_montar.py personagem/trans… · faixa()
- `story_ep1_montar` — Monta as pranchas do storyboard do ep. 1 e a decupagem em texto a partir dos quadros de personagem/transito/story-ep1 e da tabela story_ep1_planos.py. python3 kit3d/story… · vel_sim()
- `story_ep1_planos` — Trânsito Brasil 3D, ep. 1: tabela dos planos (python puro). Usada pelo storyboard (tb_story_ep1.py), pela decupagem em texto e, depois, pela animação. Tempos: roteiros/vo…
- `tb_compoe_sanfona` — Trânsito Brasil 3D: monta os quadros finais da cena do efeito sanfona (1080x1920): cena em cima, legenda em pílula com linha até o carro, painel de baixo com a legenda de… · suave(), pilula(), contador(), nevoa()
- `tb_ficha` — Trânsito Brasil 3D: ficha de veículos e objetos de via, numa pista de estúdio vista de cima em 3/4. blender -b -P kit3d/tb_ficha.py -- saida.png [--escala 0.5]
- `tb_ficha_ep1` — Trânsito Brasil 3D, ep. 1: ficha de elenco e objetos no visual didático (mapa claro, pista escura, carros brilhantes).     blender -b -P kit3d/tb_ficha_ep1.py -- saida_pr… · pista(), carro(), rot(), render()
- `tb_sanfona` — Trânsito Brasil 3D: cena didática do EFEITO SANFONA na Marginal Pinheiros (expressa). Um motorista freia; os de trás freiam mais, e a freada vira uma onda vermelha que an… · monta_trafego(), atualiza_camera(), na_tela(), passo_cena()
- `tb_story_ep1` — Trânsito Brasil 3D, ep. 1: STORYBOARD RENDERIZADO das 13 falas, nas quatro vistas, sobre os tempos reais da voz (roteiros/voz-transito/tempos.json). Cada plano tem a vist… · monta_trafego(), liga_evento(), lentos(), ancora(), anda_sim(), poe(), par_proximo(), cena_espaco(), renderiza()
- `tb_teste` — Trânsito Brasil 3D: testes de estilo do mapa. blender -b -P kit3d/tb_teste.py -- planta  saida.png              (vista de cima ortográfica do recorte inteiro, para achar … · ponto_via(), etiqueta()
