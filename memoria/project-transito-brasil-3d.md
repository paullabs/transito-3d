---
name: project-transito-brasil-3d
description: Trânsito Brasil 3D — série nova de mapas 3D vistos de cima sobre trânsito (ep. 1 em São Paulo); testes de estilo feitos em 26/10/2026
metadata:
  node_type: memory
  type: project
  modified: 2026-10-26T17:21:51.752Z
---

Série nova pedida em 26/10/2026: vídeos narrados e didáticos sobre trânsito no Brasil, em mapa 3D visto de cima; ep. 1 em São Paulo. O Paulo acredita em milhões de views e quer primeiro os assets (veículos, pedágio etc.) e testes.

Estado em 26/10/2026 (depois da crítica de contraste e colisão, refeito no mesmo dia: estilo didático, sanfona-v4.mp4, zero carros atravessados): os testes esperam a escolha do estilo pelo Paulo (A maquete, B noite, C real, mais o mapa de cores do trânsito). Pranchas em `personagem/transito/`. Código em `kit/tb_*.py`: `tb_osm.py` (OSM → JSON em metros), `tb_assets.py` (veículos e objetos de via), `tb_mapa.py` (mapa real com pontes e torre da Estaiada), `tb_trafego.py` (faixas + simulação IDM, corredor de motos, gargalo, mapa de cores), `tb_teste.py`, `tb_ficha.py` e `tb_brilho.py`. Os dados ficam em `transito/dados_osm/` (região da Ponte Estaiada, baixada da API 0.6 do OSM; o Overpass estava lotado).

**Why:** é um projeto novo que não aparece no CLAUDE.md antigo.
**How to apply:** siga as fases do canal (roteiro → voz → ficha → decupagem → animação). Ainda falta escolher o estilo e aprovar o roteiro do ep. 1. O efeito sanfona do teste animado ainda não aparece com clareza. Liga com feedback-cinema-acao e feedback-espaco-entre-objetos.
