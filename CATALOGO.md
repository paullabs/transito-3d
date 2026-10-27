# Catálogo do kit

**Antes de escrever código novo, procure aqui.** Quase tudo (mapa, simulação de tráfego, carros, câmera planejada, conferências, voz, render) já existe em `kit/`.
Abra só o arquivo do assunto que você precisa: cada um tem uma linha por módulo, com o que faz e as funções públicas.
Assinaturas de um módulo: `grep -n '^def \|^class ' kit/<modulo>.py`. Scripts rodam com `blender -b -P kit/<script>.py -- ARGS` (o cabeçalho de cada um explica os argumentos).

## Mapa, tráfego e cena → `catalogo/01-mapa-trafego-e-cena.md`
`tb_assets`, `tb_brilho`, `tb_cena`, `tb_mapa`, `tb_osm`, `tb_trafego`, `tb_xt`

## Câmera planejada e conferências → `catalogo/02-camera-planejada-e-conferencias.md`
`tb_camera_suave`, `tb_colisao`, `tb_mede_camera`

## Cenas prontas, ficha e testes → `catalogo/03-cenas-prontas-ficha-e-testes.md`
`ficha_ep1_montar`, `story_ep1_montar`, `story_ep1_planos`, `tb_compoe_sanfona`, `tb_ficha`, `tb_ficha_ep1`, `tb_sanfona`, `tb_story_ep1`, `tb_teste`

## Animação do ep. 1 (planos, render, composição) → `catalogo/04-animacao-do-ep-1-planos-render-composicao.md`
`anim_ep1`, `anim_ep1_planos`, `anim_ep1b`, `anim_ep1b_planos`, `anim_ep1c`, `anim_ep1c_planos`, `compoe_ep1`, `compoe_ep1b`, `compoe_ep1c`

## Voz e palavras → `catalogo/05-voz-e-palavras.md`
`palavras`, `voz_eleven`, `voz_medida`, `voz_monta_transito`, `voz_monta_transito2`
