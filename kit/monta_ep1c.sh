#!/bin/bash
# compõe a legenda e junta com a voz: rascunho v3 do ep. 1 do trânsito (43 s)
cd "${TRANSITO3D_PROJETO:-$PWD}"; KIT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 $KIT/compoe_ep1c.py render_transito/ep1c_v1 render_transito/ep1c_v1_final || exit 1
mkdir -p personagem/transito/anim
ffmpeg -y -v error -framerate 24 -i render_transito/ep1c_v1_final/%04d.png -i roteiros/voz-transito-v2/narracao.wav \
  -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p -c:a aac -b:a 192k -shortest personagem/transito/anim/ep1-rascunho-v3-curto.mp4
ffprobe -v error -show_entries format=duration -of csv=p=0 personagem/transito/anim/ep1-rascunho-v3-curto.mp4
