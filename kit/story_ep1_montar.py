"""Monta as pranchas do storyboard do ep. 1 e a decupagem em texto a partir dos quadros de personagem/transito/story-ep1 e da tabela story_ep1_planos.py.
    python3 kit3d/story_ep1_montar.py"""
import os, sys, textwrap
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw, ImageFont
import story_ep1_planos as SP

RAIZ = SP.RAIZ; PAST = os.path.join(RAIZ, "personagem", "transito")
F = lambda n: ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Rounded Bold.ttf', n)
FN = lambda n: ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', n)
FB = lambda n: ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Bold.ttf', n)

INTENCAO = {
 1: "Situar: a Marginal Pinheiros, em São Paulo, com o trânsito andando normal (tudo verde). A câmera desliza devagar para trás.",
 2: "A causa está lá na frente: o aro amarelo marca o carro que vai frear. Baixa, por trás: a causa é pequena e distante, como a pessoa a vê.",
 3: "A freada: o carro pisa forte no freio (palavra 'pisa', 18,5 s), a luz acende e ele vira vermelho, e o resto da pista segue andando.",
 4: "O de trás reage atrasado e freia mais forte: baixa, na altura das luzes de freio; o carro da frente já está parado, o de trás passa de verde a amarelo e a vermelho.",
 5: "Em poucos segundos há carros parados no meio da pista: de cima reto, a fila é uma coluna de vermelhos (3 a 4 carros).",
 6: "O primeiro carro (o do aro) já foi embora e a fila continua: diagonal larga, com o carro saindo no fundo e os parados em primeiro plano.",
 7: "A fila anda pra trás: topo plano com o painel do diagrama (cada linha é um carro) e o selo EFEITO SANFONA. A câmera desce com a cauda.",
 8: "'Você anda um pouco, para, anda de novo': a câmera passa pela cauda da fila, atravessando carros andando, parando e andando.",
 9: "'Pista cheia, carros colados': diagonal bem aberta, fila longa; tempo acelerado (~2x).",
 10: "Espaço: baixa, por trás de um carro com vão de uns 2 s à frente (aro verde); a luz de freio do de trás acende fraca. CENA ESPECIAL a construir: um carro com vão maior que o resto.",
 11: "Regra dos 2 segundos: topo plano, poste ao lado da pista e régua no chão a partir do carro da frente; o de trás dentro da régua fica amarelo/vermelho, depois abre o vão e fica verde. CENA ESPECIAL.",
 12: "Fecho: perspectiva no ponto onde tudo começou, já livre (verde); a fila vermelha segue para trás, longe. 'O motivo já passou.'",
 13: "Pergunta ao público: topo plano que sobe e abre sobre a pista, com a coluna vermelha pequena entre os verdes; pergunta na tela.",
}
PEDE = {3: "aro amarelo no carro", 4: "luzes de freio", 7: "painel do diagrama (xt) na parte de baixo e selo EFEITO SANFONA", 10: "aro verde no carro de trás", 11: "poste + régua de 2 s no chão"}

def vel_sim(t0, t1): return (SP.sim_de(t1) - SP.sim_de(t0)) / (t1 - t0)

# ------------------------------------------------ pranchas
STILLS = os.path.join(PAST, "story-ep1")
LINHAS_POR_PRANCHA = [5, 4, 4]
ordem = [p[0] for p in SP.PLANOS]; pranchas = []; i = 0
for n in LINHAS_POR_PRANCHA:
    pranchas.append(ordem[i:i + n]); i += n
W = 1900; RH = 450; TW = 560
for k, ids in enumerate(pranchas, 1):
    img = Image.new('RGB', (W, 70 + RH * len(ids)), '#0e1115'); d = ImageDraw.Draw(img)
    d.text((24, 16), f"STORYBOARD | TRÂNSITO BRASIL 3D EP. 1 | prancha {k}/{len(pranchas)}", font=F(34), fill='white')
    for r, pid in enumerate(ids):
        pl = [p for p in SP.PLANOS if p[0] == pid][0]; _, fala, vista, anc, o0, o1, d0, d1, e0, e1, a0, a1, leg = pl
        t0, t1 = SP.FALA_T[fala - 1]; y = 70 + r * RH
        d.rectangle((0, y, W, y + RH - 6), fill='#161b22')
        d.text((24, y + 10), f"PLANO {pid} | fala {fala} | {t0:.1f}-{t1:.1f} s ({t1 - t0:.1f} s)", font=F(28), fill='#ffd21f')
        d.text((24, y + 46), f"{vista.upper()}" + (f" | lente {SP.LENTE[vista]} mm" if vista != 'topo' else " | ortográfica"), font=F(24), fill='#7fd1ff')
        yy = y + 82
        for l in textwrap.wrap("“" + SP.FALA_TXT[fala - 1] + "”", width=46):
            d.text((24, yy), l, font=FB(22), fill='white'); yy += 27
        yy += 6
        for l in textwrap.wrap(INTENCAO[pid], width=60):
            d.text((24, yy), l, font=FN(19), fill='#c8d0da'); yy += 23
        yy += 4
        d.text((24, yy), f"âncora: {anc} | câmera {o0:+d}→{o1:+d} m | {'altura' if vista == 'topo' else 'dist'} {d0}→{d1} m", font=FN(18), fill='#8b96a5'); yy += 22
        vs = vel_sim(t0, t1) if not pid in (10, 11) else 1.0
        d.text((24, yy), f"simulação {SP.sim_de(t0):.0f}→{SP.sim_de(t1):.0f} s (x{vs:.2f}) | na tela: {leg or '—'}", font=FN(18), fill='#8b96a5')
        for c, u in enumerate((0, 50, 100)):
            f = os.path.join(STILLS, f"p{pid:02d}_u{u:03d}.png")
            if os.path.exists(f):
                im = Image.open(f).convert('RGB'); im = im.resize((int(im.width * (RH - 24) / im.height), RH - 24))
                img.paste(im, (TW + 20 + c * (im.width + 10), y + 6))
    img.save(os.path.join(PAST, f"storyboard-ep1-{k}.png")); print("prancha", k, img.size)

# ------------------------------------------------ decupagem em texto
L = ["# Decupagem das quatro vistas, ep. 1: \"Por que o trânsito trava do nada na Marginal?\"", "",
     "**Status: esperando aprovação (26/10/2026).** Voz aprovada nas medidas: `roteiros/voz-transito/` (85,9 s, 3,1 palavras/s). Storyboard renderizado: `storyboard-ep1-1..3.png`; quadros em `story-ep1/`.", "",
     "## Regras desta decupagem", "",
     "- **Mesma simulação em todos os planos.** As quatro vistas são câmeras diferentes sobre a mesma pista; o corte muda o ponto de vista e a hora da simulação continua de onde parou (continuidade de cinema).",
     "- **Corte com a câmera andando.** Cada plano tem UMA onda de câmera (início → fim) que entra e sai devagar, mas **sem zerar**: velocidade de ponta de ~60% da média (`tb_camera_suave.valor` com tangente de ponta), para o corte juntar dois movimentos e não duas paradas. Nenhum plano muda de sentido no meio.",
     "- **Tempo da simulação ≠ tempo do filme.** Antes da freada, 1x; logo depois, câmera lenta (~0,45x, a freada cai na palavra \"pisa\", 18,5 s); depois 0,7x a 2x (`story_ep1_planos.MAPA`), com a velocidade variando devagar (sem degrau).",
     "- **Nenhum plano repete a vista do anterior.** Sequência: " + " → ".join(p[2] for p in SP.PLANOS) + ".",
     "- **Texto na tela** só em pílula escura com texto claro; \"efeito sanfona\" só na tela; fonte e rodapé \"simulação ilustrativa\" em todos os planos.",
     "- **Medido antes de animar:** `tb_colisao.py` (0 carros atravessados) e `tb_mede_camera.py` (0 trancos, 0 paradas) em cada plano.", "",
     "## Tabela de planos", "",
     "| # | fala | filme | vista | âncora e câmera | simulação | na tela | mensagem |", "|---|---|---|---|---|---|---|---|"]
for pl in SP.PLANOS:
    pid, fala, vista, anc, o0, o1, d0, d1, e0, e1, a0, a1, leg = pl; t0, t1 = SP.FALA_T[fala - 1]
    L.append(f"| {pid} | {fala} | {t0:.1f}–{t1:.1f} s | {vista}{'' if vista == 'topo' else f', {SP.LENTE[vista]} mm'} | {anc} {o0:+d}→{o1:+d} m; {'altura' if vista == 'topo' else 'dist'} {d0}→{d1} m" + ("" if vista == 'topo' else f"; elev {e0}→{e1}°; azim {a0}→{a1}°") + f" | {SP.sim_de(t0):.0f}→{SP.sim_de(t1):.0f} s | {leg or '—'} | {INTENCAO[pid]} |")
L += ["", "## Pontos de atenção vistos no storyboard (para decidir)", "",
      "- **O trecho filmado fica ao norte da Marginal (y = 800 m no mapa), sem a Ponte Estaiada.** No trecho da ponte a fila andava para trás direto para debaixo do viaduto e os tabuleiros e cabos invadiam o quadro (visto no primeiro storyboard). Contrapartida: ao norte quase não há prédio, então o mapa fica pálido e **não diz \"São Paulo\"**. Sugestão: abrir (plano 1) ou fechar (plano 13) com uma vista aérea da Estaiada e da Marginal sem carros, só para situar. Decidir.",
      "- **Plano 4 (baixa):** um carro de outra faixa passa colado na câmera no começo e tapa a ação. Na animação a câmera precisa de um vão livre (mudar o ponto de vista em 3 a 4 m).",
      "- **Plano 10 (baixa):** o aro verde pega o carro mais perto da câmera. Na cena especial, enquadrar o par (carro da frente + carro de trás) e mostrar o vão entre eles.",
      "- **Plano 11 (topo):** o poste fica pequeno de cima. Fazer um ícone grande e uma linha amarela atravessando a pista no poste (é a linha onde a régua começa).",
      "- **Planos 12 e 13:** a fila fica a uns 300 a 450 m do ponto da freada. O plano 13 abre até ~260 m de altura visível e mostra o rio ao lado: serve de abertura para o próximo episódio.",
      "- **Cores:** a contagem \"carros lentos\" oscila, mas a cor de cada carro é contínua; as legendas usam só texto fixo.",
      ]
L += ["", "## Cenas especiais (precisam ser construídas antes da animação)", "",
      "- **Planos 10 e 11 (cena do espaço):** a simulação atual só tem carros a 1,7–2,1 s uns dos outros. Falta (a) um carro de trás com vão de uns 3 s e a luz de freio fraca quando o da frente freia (carro com T maior), e (b) o mesmo carro entrando na régua e abrindo o vão. A régua e o poste já existem (`tb_assets.regua_tempo`, `tb_assets.poste`).",
      "- **Painel do diagrama no plano 7:** `tb_xt.py` + `tb_compoe_sanfona.py` já fazem; falta ajustar para o tempo remapeado do filme.", "",
      "## Pendências técnicas", "",
      "- A onda real da simulação anda para trás a ~13 km/h (frente) e ~18 km/h (cauda); a fonte mede ~20 km/h. A fala não cita o número.",
      "- Os planos 5 e 6 mostram 3 a 4 carros lentos; o limiar da contagem é velocidade < 30% da velocidade de cruzeiro e oscila de um quadro a outro: usar a cor (já contínua), não o contador, para o selo.",
      "- Planejar a câmera de cada plano em pré-passagem (como na sanfona v7): o storyboard usa âncoras ao vivo, que servem para ver o enquadramento, mas dão tranco se usadas na animação. Nos planos 2 e 3 a câmera acompanha o carro que freia; na animação, o caminho é o do carro filtrado (gaussiana), para a câmera não frear junto com ele.",
      "- Voz: o trecho 12 saiu a 100 Hz (a queda natural da última frase). Não foi processado; se o Paulo quiser, refazer só esse trecho."]
open(os.path.join(PAST, "decupagem-ep1.md"), "w").write("\n".join(L)); print("decupagem-ep1.md ok")
