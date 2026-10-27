# Meu projeto de trânsito 3D

Este projeto usa o plugin **transito-3d**. Não gere de novo o que já existe.

- **Kit de código (pronto):** `__KIT__`
- **Índice do que existe:** `__RAIZ__/CATALOGO.md` (abra só o arquivo do assunto, em `__RAIZ__/catalogo/`)
- **Regras e histórico:** `__RAIZ__/memoria/` e a skill `transito-3d`
- **Variável:** `TRANSITO3D_PROJETO=__PROJ__` (roteiros, quadros e entregas ficam aqui; o mapa está em `transito/dados_osm/`)

## Como trabalhar (poupa token)
1. Procure no catálogo antes de escrever código; importe o módulo.
2. Cena nova = parta de `tb_sanfona.py` ou dos planos do `anim_ep1c_planos.py` e mude só parâmetros e tabela de planos.
3. Fases com aprovação do usuário: roteiro → voz → ficha → decupagem/storyboard → rascunho animado → som → render cheio → pós.
4. Antes de renderizar: `tb_colisao.py`, `tb_sanfona.py -- sim` e a medição de câmera (`camlog` + `tb_mede_camera.py`).
5. Rascunho em meia resolução; voz e música pagas só depois do roteiro aprovado.
