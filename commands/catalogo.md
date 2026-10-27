---
description: Procura no kit de trânsito a peça pronta para o que você quer animar (evita gerar código de novo)
argument-hint: <o que você precisa, ex.: "carro que freia", "câmera de topo", "fila">
---
O usuário precisa de: $ARGUMENTS

Abra `CATALOGO.md` na raiz do plugin, escolha o arquivo de `catalogo/` do assunto e use `grep` nele. Responda com no máximo 5 módulos candidatos: nome, o que faz, funções para chamar e um exemplo de uso já existente no kit de trânsito (um `story_*`/`anim_*` que o importe). Não escreva código novo se alguma peça cobrir o pedido.
