"""Gerador automático dos templates de referência oficiais e do logo da Kav.

Gera os 5 layouts oficiais da Kav baseados fielmente nas referências enviadas:
- Tipografia Gotham em Sentence Case (sem caixa alta);
- Cores da Kav (Fundo Azul Marinho Noturno #001424, Dourado Kav #EEB730 - PROIBIDO preto puro);
- Ausência de termos de carrossel ("Arrasta pra entender");
- Destaque para metáforas visuais, tweet boxes, blueprints e manifestos.
"""
from __future__ import annotations

import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1350
C_BG = (0, 20, 36)            # #001424 (Azul Marinho Noturno Profundo da Kav)
C_CARD = (3, 30, 52)          # #031E34 (Superfície escura de card)
C_CARD_ERR = (28, 14, 18)     # #1C0E12 (Card de erro sutil)
C_GOLD = (238, 183, 48)       # #EEB730 (Dourado Kav Oficial)
C_WHITE = (255, 255, 255)     # #FFFFFF
C_SLATE = (148, 163, 184)     # #94A3B8
C_MUTED = (80, 95, 125)       # #505F7D
C_BORDER = (18, 52, 82)       # #123452
C_GREEN = (37, 211, 102)      # Verde WhatsApp

VERSAO_REFERENCIAS = "v4_gotham_sentence_case_cores_kav"


def garantir_referencias_kav(pasta_referencias: Path) -> None:
    pasta_referencias.mkdir(parents=True, exist_ok=True)
    arquivo_versao = pasta_referencias / ".versao"
    arquivos_esperados = [
        "ref_afirmacao_tweet_box.png",
        "ref_destaque_dourado.png",
        "ref_manifesto_palavra_dourada.png",
        "ref_impacto_condensado_grid.png",
        "ref_quebra_objecao_card.png",
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
    """Garante a existência do arquivo de logotipo oficial da Kav."""
    pasta_logo = pasta_cliente / "logo"
    pasta_logo.mkdir(parents=True, exist_ok=True)

    candidatos = [
        pasta_cliente / "logo-fundo-escuro.png",
        pasta_logo / "logo-fundo-escuro.png",
        pasta_logo / "logo_kav.png",
        pasta_logo / "logo.png",
        pasta_cliente / "logos" / "logo-fundo-escuro.png",
        pasta_cliente / "logos" / "logo.png",
        pasta_cliente / "logo.png",
        pasta_cliente / "logo-fundo-claro.png",
    ]
    for c in candidatos:
        if c.exists():
            return c

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
        f_huge = ImageFont.truetype(font_bold_path, 64)
        f_big = ImageFont.truetype(font_bold_path, 42)
        f_med = ImageFont.truetype(font_bold_path, 30)
        f_bold = ImageFont.truetype(font_bold_path, 22)
        f_small_b = ImageFont.truetype(font_bold_path, 18)
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

    # 1. Arquétipo Samuel Reis: Tweet Box de Autoridade (Sentence Case)
    im1, d1 = _criar_base()
    d1.text((100, 160), "Tráfego", fill=C_SLATE, font=f_small)
    d1.text((540, 160), "Estratégia", fill=C_SLATE, font=f_small, anchor="mm")
    d1.text((980, 160), "Kav", fill=C_SLATE, font=f_small, anchor="ra")
    d1.rounded_rectangle([(100, 260), (280, 310)], radius=22, fill=C_CARD, outline=C_BORDER)
    d1.ellipse([(110, 270), (145, 305)], fill=C_GOLD)
    d1.text((127, 287), "K", fill=C_BG, font=f_small_b, anchor="mm")
    d1.text((215, 287), "@kav.mkt", fill=C_WHITE, font=f_small_b, anchor="mm")
    d1.text((100, 390), "Não é trabalho\\ndo seu cliente se\\nlembrar de você.", fill=C_WHITE, font=f_huge, spacing=16)
    d1.rounded_rectangle([(95, 780), (985, 930)], radius=24, outline=C_BORDER, fill=C_CARD)
    d1.text((135, 825), "É sua obrigação ter a certeza de que ele não vai te esquecer.", fill=C_WHITE, font=f_med)
    d1.text((135, 875), "Com tráfego local no raio certo, sua marca aparece todos os dias.", fill=C_SLATE, font=f_small)
    d1.text((100, 1030), "Leia a legenda  ↘", fill=C_GOLD, font=f_med)
    im1.save(pasta / "ref_afirmacao_tweet_box.png")

    # 2. Arquétipo Well.dsg & ORB: Metáfora Visual / Cadeira de Destaque
    im2, d2 = _criar_base()
    d2.text((540, 180), "Você não precisa fazer igual.", fill=C_WHITE, font=f_big, anchor="mm")
    d2.text((540, 240), "Nem pensar igual.", fill=C_WHITE, font=f_big, anchor="mm")
    cx, cy = 540, 620
    for row in range(-2, 3):
        for col in range(-3, 4):
            px = cx + col * 95
            py = cy + row * 95
            if row == 0 and col == 0:
                d2.rounded_rectangle([(px - 36, py - 36), (px + 36, py + 36)], radius=14, fill=C_GOLD)
                d2.text((px, py), "★", fill=C_BG, font=f_big, anchor="mm")
            else:
                d2.rounded_rectangle([(px - 26, py - 26), (px + 26, py + 26)], radius=10, fill=C_BORDER)
    d2.text((540, 940), "Faça diferente. Seja estratégico.", fill=C_WHITE, font=f_big, anchor="mm")
    d2.text((540, 1010), "O marketing que copia, some.", fill=C_SLATE, font=f_med, anchor="mm")
    d2.line([(100, 1200), (980, 1200)], fill=C_BORDER, width=1)
    d2.text((100, 1240), "@kav.mkt", fill=C_MUTED, font=f_small)
    d2.text((980, 1240), "2026", fill=C_MUTED, font=f_small, anchor="ra")
    im2.save(pasta / "ref_destaque_dourado.png")

    # 3. Arquétipo Focus: Manifesto Editorial Tipográfico
    im3, d3 = _criar_base()
    d3.text((540, 160), "KAV", fill=C_GOLD, font=f_big, anchor="mm")
    d3.text((100, 460), "Improviso", fill=C_WHITE, font=f_huge)
    d3.text((100, 560), "não constrói", fill=C_GOLD, font=f_huge)
    d3.line([(100, 655), (550, 655)], fill=C_GOLD, width=4)
    d3.text((100, 690), "empresa.", fill=C_WHITE, font=f_huge)
    d3.rounded_rectangle([(390, 1100), (690, 1165)], radius=32, outline=C_SLATE, width=2)
    d3.text((540, 1132), "→  Leia a legenda", fill=C_WHITE, font=f_reg, anchor="mm")
    im3.save(pasta / "ref_manifesto_palavra_dourada.png")

    # 4. Arquétipo Agencia Workspace: Blueprint Grid Técnico
    im4, d4 = _criar_base(com_grid=True)
    d4.text((100, 140), "kavmarketing", fill=C_SLATE, font=f_small)
    d4.text((980, 140), "performance", fill=C_SLATE, font=f_small, anchor="ra")
    d4.rounded_rectangle([(100, 280), (380, 335)], radius=24, fill=C_CARD, outline=C_GOLD, width=2)
    d4.text((240, 307), "📈  Quer crescer?", fill=C_GOLD, font=f_small, anchor="mm")
    d4.text((100, 480), "Então pare de\\ntratar marketing\\ncomo um gasto! ↘", fill=C_WHITE, font=f_huge, spacing=18)
    termos = "Tráfego Local · Performance · PMEs · Geofencing · Conversão · WhatsApp · ROI · Escala"
    d4.text((100, 1140), termos, fill=C_MUTED, font=f_small)
    im4.save(pasta / "ref_impacto_condensado_grid.png")

    # 5. Arquétipo Geovane Rocha: Quebra de Objeção / Tensão de Valor
    im5, d5 = _criar_base()
    d5.rounded_rectangle([(100, 150), (330, 205)], radius=24, outline=C_BORDER, fill=C_CARD)
    d5.text((215, 177), "@kav.mkt", fill=C_SLATE, font=f_small, anchor="mm")
    d5.text((100, 360), "Você não precisa\\nabaixar o seu preço.", fill=C_WHITE, font=f_huge, spacing=16)
    d5.rounded_rectangle([(95, 660), (985, 860)], radius=24, outline=C_GOLD, fill=C_CARD, width=2)
    d5.text((135, 715), "Preço baixo atrai cliente difícil.", fill=C_GOLD, font=f_med)
    d5.text((135, 780), "Posicionamento e tráfego certo atraem quem valoriza seu serviço.", fill=C_WHITE, font=f_reg)
    d5.rounded_rectangle([(390, 1100), (690, 1165)], radius=32, outline=C_BORDER, fill=C_CARD)
    d5.text((540, 1132), "→  Leia a legenda", fill=C_WHITE, font=f_bold, anchor="mm")
    im5.save(pasta / "ref_quebra_objecao_card.png")
