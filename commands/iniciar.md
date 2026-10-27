---
description: Prepara a pasta do seu projeto de trânsito 3D (pastas, dados do mapa, caminhos do kit e CLAUDE.md)
argument-hint: [pasta-do-projeto]
---
1. Ache a raiz do plugin (a pasta que tem `bin/iniciar.sh`, `kit/` e `CATALOGO.md`): use `${CLAUDE_PLUGIN_ROOT}` se existir; senão `find ~/.claude/plugins -name iniciar.sh -path "*transito-3d*"`.
2. Rode `bash <raiz>/bin/iniciar.sh $ARGUMENTS` (sem argumento, usa a pasta atual).
3. Mostre os avisos do script (Blender, ffmpeg, Pillow/numpy) e diga em duas linhas o próximo passo: escrever o roteiro e pedir aprovação. Não gere nem renderize nada nesta etapa.
