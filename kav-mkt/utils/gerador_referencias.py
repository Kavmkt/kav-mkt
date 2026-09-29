"""Gerador automático dos templates de referência oficiais e do logo da Kav.

Gera os 5 layouts oficiais da Kav e o logotipo oficial caso ainda não existam no disco,
garantindo que qualquer máquina que clone ou dê git pull tenha as referências prontas.
"""
from __future__ import annotations

import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1350
C_BG = (0, 20, 36)            # #001424
C_CARD = (3, 30, 52)          # #031E34
C_CARD_ERR = (28, 14, 18)     # #1C0E12 (card de erro sutil)
C_GOLD = (238, 183, 48)       # #EEB730 (Dourado Kav)
C_WHITE = (255, 255, 255)     # #FFFFFF
C_SLATE = (148, 163, 184)     # #94A3B8
C_MUTED = (80, 95, 125)       # #505F7D
C_BORDER = (18, 52, 82)       # #123452
C_GREEN = (37, 211, 102)      # Verde WhatsApp


VERSAO_REFERENCIAS = "v2_contrastes_radicais"

def garantir_referencias_kav(pasta_referencias: Path) -> None:
    pasta_referencias.mkdir(parents=True, exist_ok=True)
    arquivo_versao = pasta_referencias / ".versao"
    arquivos_esperados = [
        "ref_afirmacao_tweet_box.png",
        "ref_quebra_objecao_card.png",
        "ref_destaque_dourado.png",
        "ref_impacto_condensado_grid.png",
        "ref_manifesto_palavra_dourada.png",
    ]
    precisa_gerar = False
    if not arquivo_versao.exists() or arquivo_versao.read_text(encoding="utf-8").strip() != VERSAO_REFERENCIAS:
        precisa_gerar = True
    elif any(not (pasta_referencias / arq).exists() for arq in arquivos_esperados):
        precisa_gerar = True

    if precisa_gerar:
        _gerar_todas(pasta_referencias)
        try:
            arquivo_versao.write_text(VERSAO_REFERENCIAS, encoding="utf-8")
        except Exception:
            pass


def garantir_logo_kav(pasta_cliente: Path) -> Path:
    """Garante a existência do arquivo de logotipo da Kav caso não exista fisicamente."""
    pasta_logo = pasta_cliente / "logo"
    pasta_logo.mkdir(parents=True, exist_ok=True)

    candidatos = [
        pasta_logo / "logo_kav.png",
        pasta_logo / "logo.png",
        pasta_logo / "logo-fundo-escuro.png",
        pasta_cliente / "logos" / "logo-fundo-escuro.png",
        pasta_cliente / "logos" / "logo.png",
        pasta_cliente / "logo-fundo-escuro.png",
        pasta_cliente / "logo.png",
        pasta_cliente / "logo-fundo-claro.png",
    ]
    for c in candidatos:
        if c.exists():
            return c

    for p_busca in [pasta_cliente / "logo", pasta_cliente / "logos", pasta_cliente]:
        if p_busca.is_dir():
            for arq in sorted(p_busca.glob("*")):
                if arq.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp", ".svg"} and "logo" in arq.name.lower():
                    return arq

    destino = pasta_logo / "logo_kav.png"
    w, h = 800, 220
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(im)

    f_huge, _, _, f_bold, _, _, _ = _obter_fontes()
    draw.text((w / 2, 70), "KAV", fill=(238, 183, 48, 255), font=f_huge, anchor="mm")
    draw.text((w / 2, 145), "MARKETING & PERFORMANCE", fill=(255, 255, 255, 220), font=f_bold, anchor="mm")

    im.save(destino)
    return destino


def _obter_fontes():
    font_bold_path = None
    for p in [
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/System/Library/Fonts/SFNS.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "C:\\Windows\\Fonts\\arialbd.ttf",
    ]:
        if Path(p).exists():
            font_bold_path = p
            break

    font_reg_path = None
    for p in [
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/System/Library/Fonts/SFNS.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "C:\\Windows\\Fonts\\arial.ttf",
    ]:
        if Path(p).exists():
            font_reg_path = p
            break

    if font_bold_path:
        f_huge = ImageFont.truetype(font_bold_path, 68)
        f_big = ImageFont.truetype(font_bold_path, 44)
        f_med = ImageFont.truetype(font_bold_path, 32)
        f_bold = ImageFont.truetype(font_bold_path, 24)
        f_small_b = ImageFont.truetype(font_bold_path, 20)
    else:
        f_huge = f_big = f_med = f_bold = f_small_b = ImageFont.load_default()

    if font_reg_path:
        f_reg = ImageFont.truetype(font_reg_path, 24)
        f_small = ImageFont.truetype(font_reg_path, 18)
    else:
        f_reg = f_small = ImageFont.load_default()

    return f_huge, f_big, f_med, f_bold, f_reg, f_small, f_small_b


def _criar_base(com_grid=False):
    im = Image.new("RGB", (W, H), C_BG)
    draw = ImageDraw.Draw(im)
    for y in range(H):
        t = y / H
        g = int(22 * (1 - t * 0.4) + 12 * (t * 0.4))
        b = int(40 * (1 - t * 0.4) + 20 * (t * 0.4))
        draw.line([(0, y), (W, y)], fill=(0, g, b))
    if com_grid:
        step = 80
        for x in range(0, W, step):
            draw.line([(x, 0), (x, H)], fill=(7, 32, 54), width=1)
        for y in range(0, H, step):
            draw.line([(0, y), (W, y)], fill=(7, 32, 54), width=1)
    return im, draw


def _gerar_todas(pasta: Path):
    f_huge, f_big, f_med, f_bold, f_reg, f_small, f_small_b = _obter_fontes()

    # 1. Tweet Box / Card Flutuante
    im1, d1 = _criar_base()
    d1.rounded_rectangle([(90, 320), (990, 960)], radius=28, fill=C_CARD, outline=C_BORDER, width=2)
    d1.ellipse([(140, 370), (210, 440)], fill=C_GOLD)
    d1.text((175, 405), "K", fill=C_BG, font=f_big, anchor="mm")
    d1.text((230, 385), "Kav Marketing", fill=C_WHITE, font=f_bold)
    d1.text((230, 420), "@kav.mkt · Tráfego Local", fill=C_SLATE, font=f_small)
    d1.text((140, 500), "Não é trabalho do seu cliente\nse lembrar que você existe.", fill=C_WHITE, font=f_big)
    d1.text((140, 640), "É obrigação da sua empresa\naparecer todos os dias no\nfeed de quem mora no bairro.", fill=C_SLATE, font=f_med)
    d1.line([(140, 830), (940, 830)], fill=C_BORDER, width=1)
    d1.text((140, 875), "Leia a legenda completa", fill=C_GOLD, font=f_bold)
    d1.text((920, 875), "↘", fill=C_GOLD, font=f_big, anchor="rm")
    im1.save(pasta / "ref_afirmacao_tweet_box.png")

    # 2. Comparativo Duplo: Erro vs Método Kav
    im2, d2 = _criar_base()
    d2.text((540, 160), "POR QUE SUA EMPRESA NÃO VENDE?", fill=C_SLATE, font=f_med, anchor="mm")
    d2.rounded_rectangle([(90, 240), (990, 560)], radius=24, fill=C_CARD_ERR, outline=(100, 30, 40), width=2)
    d2.text((140, 290), "✕  COMO A MAIORIA FAZ:", fill=(240, 80, 90), font=f_bold)
    d2.text((140, 350), "Cria um post qualquer, aperta o\nbotão 'Impulsionar' e espera o\nmilagre das vendas acontecer.", fill=C_WHITE, font=f_med)
    d2.rounded_rectangle([(90, 630), (990, 1020)], radius=24, fill=C_CARD, outline=C_GOLD, width=3)
    d2.text((140, 680), "✓  COM O MÉTODO KAV:", fill=C_GOLD, font=f_bold)
    d2.text((140, 750), "Anúncios ultra-segmentados em\num raio de 5 km direto para o seu\nWhatsApp com oferta irresistível.", fill=C_WHITE, font=f_med)
    d2.rounded_rectangle([(320, 1120), (760, 1190)], radius=35, fill=C_CARD, outline=C_BORDER)
    d2.text((540, 1155), "Arrasta pra entender  →", fill=C_WHITE, font=f_bold, anchor="mm")
    im2.save(pasta / "ref_quebra_objecao_card.png")

    # 3. Notificação WhatsApp / Alerta de Venda
    im3, d3 = _criar_base()
    d3.text((540, 220), "ISSO É O QUE DEVERIA ESTAR", fill=C_SLATE, font=f_med, anchor="mm")
    d3.text((540, 280), "ACONTECENDO NO SEU WHATSAPP:", fill=C_WHITE, font=f_big, anchor="mm")
    d3.rounded_rectangle([(90, 440), (990, 780)], radius=28, fill=C_CARD, outline=C_BORDER, width=2)
    d3.ellipse([(140, 480), (195, 535)], fill=C_GREEN)
    d3.text((167, 507), "💬", fill=C_WHITE, font=f_small, anchor="mm")
    d3.text((215, 490), "WHATSAPP BUSINESS", fill=C_SLATE, font=f_small)
    d3.text((930, 490), "agora", fill=C_SLATE, font=f_small, anchor="ra")
    d3.text((140, 565), "Novo Cliente Local:", fill=C_GOLD, font=f_bold)
    d3.text((140, 620), '"Olá! Vi seu anúncio aqui na região\\ne queria agendar um horário hoje!"', fill=C_WHITE, font=f_med)
    d3.text((540, 940), "Se seu direct está parado, o erro está na rota.", fill=C_SLATE, font=f_reg, anchor="mm")
    d3.text((540, 1010), "DOMINE AS VENDAS DO SEU BAIRRO.", fill=C_GOLD, font=f_big, anchor="mm")
    im3.save(pasta / "ref_destaque_dourado.png")

    # 4. Dashboard de Métricas & Performance
    im4, d4 = _criar_base(com_grid=True)
    d4.rounded_rectangle([(90, 220), (990, 980)], radius=28, fill=C_CARD, outline=C_BORDER, width=2)
    d4.text((140, 280), "DASHBOARD DE PERFORMANCE LOCAL", fill=C_SLATE, font=f_small)
    d4.text((140, 360), "+340%", fill=C_GOLD, font=f_huge)
    d4.text((140, 450), "CRESCIMENTO EM LEADS NO BAIRRO", fill=C_WHITE, font=f_bold)
    pontos = [(140, 780), (280, 740), (440, 690), (600, 620), (760, 560), (920, 480)]
    for i in range(len(pontos) - 1):
        d4.line([pontos[i], pontos[i + 1]], fill=C_GOLD, width=6)
    for p in pontos:
        d4.ellipse([(p[0] - 10, p[1] - 10), (p[0] + 10, p[1] + 10)], fill=C_GOLD)
    d4.line([(140, 840), (940, 840)], fill=C_BORDER, width=1)
    d4.text((140, 880), "ROAS: 5.4x  ·  Custo por Conversão: R$ 2,10  ·  Raio: 5 km", fill=C_SLATE, font=f_small)
    d4.text((540, 1100), "TRÁFEGO NÃO É GASTO. É MÁQUINA DE CLIENTES.", fill=C_WHITE, font=f_med, anchor="mm")
    im4.save(pasta / "ref_impacto_condensado_grid.png")

    # 5. Manifesto Editorial Tipográfico
    im5, d5 = _criar_base()
    d5.text((100, 420), "Improviso", fill=C_WHITE, font=f_huge)
    d5.text((100, 520), "não constrói", fill=C_GOLD, font=f_huge)
    d5.line([(100, 615), (550, 615)], fill=C_GOLD, width=4)
    d5.text((100, 650), "empresa sólida.", fill=C_WHITE, font=f_huge)
    d5.text((100, 800), "Ou você domina os anúncios da sua região,\\nou seu concorrente domina por você.", fill=C_SLATE, font=f_reg)
    d5.rounded_rectangle([(390, 1100), (690, 1165)], radius=32, outline=C_SLATE, width=2)
    d5.text((520, 1132), "→  Leia a legenda", fill=C_WHITE, font=f_reg, anchor="mm")
    im5.save(pasta / "ref_manifesto_palavra_dourada.png")
