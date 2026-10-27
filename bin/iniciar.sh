#!/bin/bash
# Prepara a pasta do SEU projeto: pastas de trabalho, dados do mapa, caminhos do kit e um CLAUDE.md curto.
#   bash bin/iniciar.sh [PASTA_DO_PROJETO]     (padrão: a pasta atual)
set -e
RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROJ="$(cd "${1:-$PWD}" && pwd)"
mkdir -p "$PROJ"/{roteiros,personagem/transito,render_transito,entregas,transito/dados_osm}
[ -f "$PROJ/transito/dados_osm/estaiada.json" ] || cp "$RAIZ/dados/estaiada.json" "$PROJ/transito/dados_osm/estaiada.json"
printf 'TRANSITO3D_PROJETO="%s"\nTRANSITO3D_KIT="%s/kit"\n' "$PROJ" "$RAIZ" > "$PROJ/.transito3d.env"
if [ ! -f "$PROJ/CLAUDE.md" ]; then
  sed -e "s#__KIT__#$RAIZ/kit#g" -e "s#__RAIZ__#$RAIZ#g" -e "s#__PROJ__#$PROJ#g" "$RAIZ/modelo/CLAUDE.md" > "$PROJ/CLAUDE.md"
  echo "CLAUDE.md criado em $PROJ"
else
  echo "CLAUDE.md já existe, não mexi. Veja $RAIZ/modelo/CLAUDE.md."
fi
{ command -v blender >/dev/null || [ -x /Applications/Blender.app/Contents/MacOS/Blender ]; } || echo "AVISO: Blender não encontrado (precisa do 5.2)."
command -v ffmpeg >/dev/null || echo "AVISO: ffmpeg não encontrado."
python3 -c "import PIL, numpy" 2>/dev/null || echo "AVISO: faltam Pillow e numpy (pip3 install pillow numpy)."
echo "Pronto. Projeto: $PROJ | Kit: $RAIZ/kit"
