---
name: transito-3d
description: Animações de trânsito em mapa 3D real (OpenStreetMap) vistas de cima, com simulação de tráfego e câmera planejada, no Blender. Use SEMPRE para criar, ajustar, renderizar ou continuar uma cena de trânsito, mapa, tráfego, fila, "onda de freada"/efeito sanfona, câmera de topo, carros coloridos por velocidade, roteiro curto sobre trânsito, ou para conferir colisão, piscadas e movimento de câmera. Manda achar a peça pronta no kit antes de escrever código (poupa token).
---

# Trânsito 3D em mapa real

A raiz do plugin é duas pastas acima desta skill: `kit/` (código), `CATALOGO.md` + `catalogo/` (índice), `dados/estaiada.json` (trecho da Marginal Pinheiros com a Ponte Estaiada, São Paulo), `memoria/` (regras e histórico). Se não achar: `find ~/.claude/plugins ~/.codex/plugins -name gera_catalogo.py` (a raiz é a pasta acima de `bin/`). No projeto do usuário, `.transito3d.env` guarda `TRANSITO3D_PROJETO` e `TRANSITO3D_KIT`.

**Antes de começar, o plugin está instalado para todas as pastas?** Se a pessoa instalou só para uma pasta, ele some quando ela abre o Claude Code em outra. Confira, sem instalar nada ainda:

1. **Claude Code:** rode `claude plugin list --json` e procure o item `transito-3d@transito-3d`. Com `"scope": "user"` e `"enabled": true`, está **global**: siga. Só com `"scope": "project"` ou `"local"` (vem junto o `projectPath`): **não está global**; diga isso numa frase e ofereça `claude plugin install transito-3d@transito-3d --scope user`, que só roda com o sim da pessoa. Se não aparece, o plugin foi carregado de uma pasta avulsa: diga que **não está instalado** e mostre os comandos do `README.md`.
2. **Codex:** rode `codex plugin list` e procure `transito-3d@transito-3d`: tem de dizer `installed, enabled`. Se não disser, ofereça `codex plugin add transito-3d@transito-3d`.
3. Se o comando `claude` ou `codex` não existir, ignore aquele item.

## Reaproveite, não regere
1. Leia `CATALOGO.md` (curto), abra só o arquivo do assunto em `catalogo/` e use `grep -n '^def \|^class ' kit/<modulo>.py` para as assinaturas. Não leia módulos inteiros nem cole código do kit na conversa: importe (`sys.path.insert(0, KIT); import tb_trafego as TT`).
2. Cena nova = copiar `tb_sanfona.py` (simulação + câmera + render) ou os planos de `anim_ep1c_planos.py` e mudar só os parâmetros e a tabela de planos.
3. Teste com 3 quadros antes de renderizar tudo. Rascunho em meia resolução (`--escala 0.5`); cheio (1080×1920, 24 qps) só depois do OK.

## Peças
- `tb_osm.py` OSM → JSON em metros (`dados/estaiada.json` já vem pronto). Se o Overpass estiver lotado, baixe da API 0.6 (`api.openstreetmap.org/api/0.6/map?bbox=`); para planos maiores baixe uma área maior, senão a borda aparece vazia.
- `tb_mapa.py` vias na largura real, pontes com rampa, prédios na altura do OSM; estilo `didatico` (mapa claro, só o foco em asfalto escuro).
- `tb_trafego.py` faixas + simulação IDM (`Trafego(cor="velocidade"|"tipo", folga=, tempo=, mix=, reacao=)`). Determinística e igual com ou sem objetos (cores num RNG separado).
- `tb_assets.py` 15 veículos, poste, régua dos 2 segundos, aro, seta no chão, pílulas.
- `tb_camera_suave.py` + `tb_mede_camera.py` câmera PLANEJADA (Hermite + filtro gaussiano) e medidores (velocidade, aceleração, jerk, trancos, paradas).
- `tb_sanfona.py` cena pronta (`-- sim|quadro|anim|camlog PASTA`, `--vista perspectiva|topo|baixa|diagonal`); `tb_compoe_sanfona.py` legenda; `tb_colisao.py` sobreposições.
- `anim_ep1c*.py`, `compoe_ep1c.py`, `render_ep1c.sh`, `monta_ep1c.sh`: o rascunho do ep. 1 ("Por que o trânsito trava do nada?"), de roteiro a vídeo. `voz_monta_transito2.py` monta a voz sem mexer no tom.

## Regras (cada uma veio de uma recusa)
1. **Rode `tb_colisao.py` e `tb_sanfona.py -- sim` antes de qualquer render.** Só circula trânsito em faixas que nunca se cruzam. Z-fighting vinha de `clip_start` alto com camadas de 1 cm.
2. **Mecânica vista do alto:** câmera ortográfica reta para baixo, fluxo para cima na imagem, sem câmera na lateral; poucos planos longos, nunca takes aleatórios. Marcações no chão (aro, barra, faixa verde, seta) em vez de legenda explicando o óbvio.
3. **Contraste forte:** carros saturados sobre asfalto escuro e chão claro; cor pela velocidade (verde andando, amarelo devagar, vermelho parado); só a faixa em foco cheia.
4. **Câmera nunca reativa:** caminho planejado, uma onda só (duas ondas que se encontram zeram a velocidade). Meça com `camlog` + `tb_mede_camera.py`.
5. **Clareza antes de tudo:** poucos carros grandes, câmera fixa enquadrando a fila inteira, uma causa e um efeito por vez, em câmera lenta com o intervalo visível; o espectador é um carro marcado ("você"). Roteiro direto: a pergunta e a freada nos 2 primeiros segundos.
6. **Honestidade da simulação:** freada firme e curta sustenta uma fila; freada leve não vira fila; folga só encurta a fila. Fale só o que a simulação prova e diga "simulação ilustrativa". Pode espaçar mais que o real, só como exemplo.
7. O render do Blender é limitado pela GPU: processos em paralelo não aceleram muito; renderize em partes e pule quadros já feitos.
8. Voz (ElevenLabs) e música gastam crédito: só depois do roteiro aprovado. Nunca mude o tom da voz; só EQ, nível e `atempo`.

## Histórico e decisões
`memoria/` tem uma regra por arquivo (o que foi recusado e por quê) e o estado do ep. 1. Aprendeu uma regra nova? Acrescente um arquivo curto lá (regra, porquê, como aplicar).

## Pré-requisitos do usuário
Blender 5.2, Python 3 com Pillow e numpy, ffmpeg. Opcionais: ElevenLabs (voz), `mlx_whisper` (conferir a voz no mix). Dados do mapa © colaboradores do OpenStreetMap (ODbL).
