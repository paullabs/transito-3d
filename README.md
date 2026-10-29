# transito-3d

**Animações de trânsito em mapa 3D real, no Blender, para o Claude Code.**
Mapa do OpenStreetMap em 3D visto de cima, carros numa simulação de tráfego, câmera planejada e conferências automáticas. O Claude **reaproveita o kit pronto** em vez de gerar tudo de novo a cada vídeo, e isso poupa token.

Primeiro caso: **"Por que o trânsito trava do nada?"** (efeito sanfona, a onda de freada na Marginal Pinheiros, São Paulo).

## O que vem dentro
| Pasta | O que é |
|---|---|
| `kit/` | 33 módulos: `tb_osm` (mapa → metros), `tb_mapa` (vias, pontes, prédios), `tb_trafego` (simulação IDM), `tb_assets` (15 veículos, poste, régua dos 2 s, aro, seta), `tb_camera_suave` e `tb_mede_camera` (câmera planejada e medida), `tb_colisao`, `tb_sanfona` (cena pronta), voz e montagem do ep. 1 |
| `dados/estaiada.json` | Trecho da Marginal com a Ponte Estaiada (2,1 × 2,3 km), já em metros |
| `CATALOGO.md` + `catalogo/` | Índice curto + uma linha por módulo. É o que o Claude lê antes de escrever qualquer coisa |
| `skills/transito-3d` | O passo a passo e as regras (cada uma veio de uma recusa) |
| `memoria/` | Regras e histórico do ep. 1, um arquivo por assunto |
| `commands/` | `/transito-3d:iniciar` (prepara seu projeto), `/transito-3d:catalogo` (acha a peça certa) |

## Instalar
No Claude Code:
```
/plugin marketplace add paullabs/transito-3d
/plugin install transito-3d@transito-3d
```
Se o Claude perguntar o escopo, escolha o de usuário (`user`). Pelo terminal, o mesmo: `claude plugin marketplace add paullabs/transito-3d` e `claude plugin install transito-3d@transito-3d --scope user`.

No Codex:
```bash
codex plugin marketplace add paullabs/transito-3d
codex plugin add transito-3d@transito-3d
```
`--scope user` instala para todas as suas pastas (é o padrão do Claude Code). Para conferir, `claude plugin list` tem de mostrar `Scope: user` e `codex plugin list` tem de mostrar `installed, enabled`. Se o Claude mostrar `project` ou `local`, o plugin só vale naquela pasta: rode o `install` de novo com `--scope user`. Os comandos `/transito-3d:iniciar` e `/transito-3d:catalogo` são do Claude Code; no Codex peça as mesmas coisas em palavras.

Depois, na pasta do SEU projeto:
```
/transito-3d:iniciar
```
Cria as pastas, copia o mapa para `transito/dados_osm/`, grava onde o kit está e deixa um `CLAUDE.md` curto.

## Pré-requisitos
Blender 5.2, Python 3 com `pillow` e `numpy`, ffmpeg. Opcionais: ElevenLabs (voz) e `mlx_whisper` (conferir a voz no mix).

## Como poupa token
1. O Claude lê um índice de 1 KB, abre só o arquivo do assunto e usa `grep` nas assinaturas.
2. Cena nova = partir de `tb_sanfona.py` ou dos planos do `anim_ep1c_planos.py` e mudar só os parâmetros.
3. As conferências (colisão, simulação, câmera) são scripts: o Claude lê um número em vez de olhar quadro por quadro.
4. Rascunho em meia resolução; voz e música pagas só depois do roteiro aprovado.

## Regras principais
Mecânica sempre vista de cima; contraste forte e cor pela velocidade; câmera planejada, nunca reativa; poucos carros grandes e uma causa por vez; simulação honesta ("simulação ilustrativa"). Detalhes em `skills/transito-3d/SKILL.md`.

## Aviso honesto
Nasceu num canal de vídeos e foi corrigido por crítica; o último rascunho ainda está em revisão. Testado só em macOS com Blender 5.2. Os módulos `anim_ep1*` são o exemplo de como montar um episódio. Abra uma issue se algo quebrar.

## Licença e dados
Código sob MIT. Dados do mapa © colaboradores do OpenStreetMap, licença ODbL ([openstreetmap.org/copyright](https://www.openstreetmap.org/copyright)).
