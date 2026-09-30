"""Gerador automático dos templates de referência oficiais e do logo da Kav.

Gera layouts com alternância entre temas escuros e claros invertidos:
- Fundo Escuro: Azul Marinho Noturno Profundo (#001424);
- Fundo Claro Invertido: Branco com degradê suave para cinza-azulado super claro (#FFFFFF para #EBF1F6);
- Tipografia: Gotham em Sentence Case com proporção cautelosa, elegante e contida (estilo Focus);
- Logotipo oficial com preservação rígida de proporção (sem distorções);
- Ausência total de elementos de carrossel.
"""
from __future__ import annotations

import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1350

# Cores Tema Escuro (Kav)
C_DARK_BG = (0, 20, 36)            # #001424 (Azul Marinho Noturno Profundo)
C_DARK_CARD = (3, 30, 52)          # #031E34
C_DARK_BORDER = (18, 52, 82)       # #123452
C_WHITE = (255, 255, 255)
C_SLATE = (148, 163, 184)          # #94A3B8
C_MUTED = (80, 95, 125)            # #505F7D

# Cores Tema Claro Invertido (Kav)
C_LIGHT_TOP = (255, 255, 255)      # #FFFFFF (Branco Puro)
C_LIGHT_BOT = (235, 241, 246)      # #EBF1F6 (Cinza azulado super claro)
C_LIGHT_NAVY = (0, 20, 36)         # #001424 (Texto principal em Azul Marinho Nobre)
C_LIGHT_SLATE = (71, 85, 105)      # #475569 (Texto secundário cinza ardósia)
C_LIGHT_BORDER = (203, 213, 225)   # #CBD5E1 (Borda suave de card e pill)
C_LIGHT_CARD = (255, 255, 255)     # #FFFFFF (Card branco puro)

# Destaques Comuns
C_GOLD = (238, 183, 48)            # #EEB730 (Dourado Kav Oficial)
C_GOLD_DARKER = (217, 155, 0)      # #D99B00 (Dourado com alto contraste no fundo claro)

VERSAO_REFERENCIAS = "v6_minimalismo_total_focus"


def garantir_referencias_kav(pasta_referencias: Path) -> None:
    pasta_referencias.mkdir(parents=True, exist_ok=True)
    arquivo_versao = pasta_referencias / ".versao"
    arquivos_esperados = [
        "ref_manifesto_palavra_dourada.png",
        "ref_manifesto_claro.png",
        "ref_afirmacao_tweet_box.png",
        "ref_afirmacao_tweet_box_claro.png",
        "ref_destaque_dourado.png",
        "ref_quebra_objecao_claro.png",
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


def garantir_logo_kav(pasta_cliente: Path) -> tuple[Optional[Path], Optional[Path]]:
    """Retorna os arquivos de logotipo oficial autênticos da Kav para fundos escuros e claros.
    NUNCA sobrepõe nem gera logos falsos com texto simples se os arquivos oficiais existirem.
    """
    pasta_logo_antiga = pasta_cliente / "logo"
    if pasta_logo_antiga.exists():
        for arq_antigo in pasta_logo_antiga.glob("*.png"):
            if arq_antigo.stat().st_size < 25000:
                try:
                    arq_antigo.unlink()
                except Exception:
                    pass

    dest_escuro = pasta_cliente / "logo-fundo-escuro.png"
    dest_claro = pasta_cliente / "logo-fundo-claro.png"

    if dest_escuro.exists() and dest_claro.exists() and dest_escuro.stat().st_size > 25000 and dest_claro.stat().st_size > 25000:
        return dest_escuro, dest_claro

    return (dest_escuro if dest_escuro.exists() else None, dest_claro if dest_claro.exists() else None)


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
        f_huge = ImageFont.truetype(font_bold_path, 52)
        f_big = ImageFont.truetype(font_bold_path, 36)
        f_med = ImageFont.truetype(font_bold_path, 24)
        f_bold = ImageFont.truetype(font_bold_path, 19)
        f_small_b = ImageFont.truetype(font_bold_path, 15)
    else:
        f_huge = f_big = f_med = f_bold = f_small_b = ImageFont.load_default()

    if font_reg_path:
        f_reg = ImageFont.truetype(font_reg_path, 20)
        f_small = ImageFont.truetype(font_reg_path, 15)
    else:
        f_reg = f_small = ImageFont.load_default()

    return f_huge, f_big, f_med, f_bold, f_reg, f_small, f_small_b


def _criar_base_escuro():
    im = Image.new("RGB", (W, H), C_DARK_BG)
    draw = ImageDraw.Draw(im)
    for y in range(H):
        t = y / H
        g = int(22 * (1 - t * 0.4) + 12 * (t * 0.4))
        b = int(40 * (1 - t * 0.4) + 20 * (t * 0.4))
        draw.line([(0, y), (W, y)], fill=(0, g, b))
    return im, draw


def _criar_base_claro():
    im = Image.new("RGB", (W, H), C_LIGHT_TOP)
    draw = ImageDraw.Draw(im)
    for y in range(H):
        t = y / H
        r = int(C_LIGHT_TOP[0] * (1 - t) + C_LIGHT_BOT[0] * t)
        g = int(C_LIGHT_TOP[1] * (1 - t) + C_LIGHT_BOT[1] * t)
        b = int(C_LIGHT_TOP[2] * (1 - t) + C_LIGHT_BOT[2] * t)
        draw.line([(0, y), (W, y)], fill=(r, g, b))
    return im, draw


def _gerar_todas(pasta: Path):
    f_huge, f_big, f_med, f_bold, f_reg, f_small, f_small_b = _obter_fontes()

    # 1. Manifesto Editorial Focus - TEMA ESCURO (Fiel à imagem anexada)
    im1, d1 = _criar_base_escuro()
    d1.text((540, 150), "KAV", fill=C_GOLD, font=f_big, anchor="mm")
    d1.text((540, 480), "Improviso", fill=C_GOLD, font=f_huge, anchor="mm")
    d1.text((540, 560), "não constrói", fill=C_WHITE, font=f_huge, anchor="mm")
    d1.line([(360, 595), (720, 595)], fill=C_GOLD, width=3)
    d1.text((540, 640), "empresa.", fill=C_WHITE, font=f_huge, anchor="mm")
    d1.rounded_rectangle([(370, 1100), (710, 1160)], radius=30, outline=C_DARK_BORDER, width=2, fill=C_DARK_CARD)
    d1.text((540, 1130), "→   Leia a legenda", fill=C_WHITE, font=f_small, anchor="mm")
    im1.save(pasta / "ref_manifesto_palavra_dourada.png")

    # 2. Manifesto Editorial Focus - TEMA CLARO INVERTIDO (Branco p/ cinza azulado super claro)
    im2, d2 = _criar_base_claro()
    d2.text((540, 150), "KAV", fill=C_LIGHT_NAVY, font=f_big, anchor="mm")
    d2.text((540, 480), "Improviso", fill=C_GOLD_DARKER, font=f_huge, anchor="mm")
    d2.text((540, 560), "não constrói", fill=C_LIGHT_NAVY, font=f_huge, anchor="mm")
    d2.line([(360, 595), (720, 595)], fill=C_GOLD_DARKER, width=3)
    d2.text((540, 640), "empresa.", fill=C_LIGHT_NAVY, font=f_huge, anchor="mm")
    d2.rounded_rectangle([(370, 1100), (710, 1160)], radius=30, outline=C_LIGHT_BORDER, width=2, fill=C_LIGHT_CARD)
    d2.text((540, 1130), "→   Leia a legenda", fill=C_LIGHT_NAVY, font=f_small, anchor="mm")
    im2.save(pasta / "ref_manifesto_claro.png")

    # 3. Tweet Box Samuel Reis - TEMA ESCURO (Minimalista, sem textão)
    im3, d3 = _criar_base_escuro()
    d3.text((100, 150), "Kav", fill=C_SLATE, font=f_small)
    d3.rounded_rectangle([(100, 240), (280, 290)], radius=20, fill=C_DARK_CARD, outline=C_DARK_BORDER)
    d3.ellipse([(110, 250), (145, 285)], fill=C_GOLD)
    d3.text((127, 267), "K", fill=C_DARK_BG, font=f_small_b, anchor="mm")
    d3.text((215, 267), "@kav.mkt", fill=C_WHITE, font=f_small_b, anchor="mm")
    d3.text((100, 380), "Não é trabalho\\ndo seu cliente se\\nlembrar de você.", fill=C_WHITE, font=f_huge, spacing=14)
    d3.text((100, 580), "É obrigação da sua empresa aparecer todos os dias.", fill=C_SLATE, font=f_med)
    d3.text((100, 1000), "Leia a legenda completa  ↘", fill=C_GOLD, font=f_med)
    im3.save(pasta / "ref_afirmacao_tweet_box.png")

    # 4. Tweet Box - TEMA CLARO INVERTIDO (Minimalista, sem textão)
    im4, d4 = _criar_base_claro()
    d4.text((100, 150), "Kav", fill=C_LIGHT_SLATE, font=f_small)
    d4.rounded_rectangle([(100, 240), (280, 290)], radius=20, fill=C_LIGHT_CARD, outline=C_LIGHT_BORDER)
    d4.ellipse([(110, 250), (145, 285)], fill=C_GOLD_DARKER)
    d4.text((127, 267), "K", fill=C_WHITE, font=f_small_b, anchor="mm")
    d4.text((215, 267), "@kav.mkt", fill=C_LIGHT_NAVY, font=f_small_b, anchor="mm")
    d4.text((100, 380), "Não é trabalho\\ndo seu cliente se\\nlembrar de você.", fill=C_LIGHT_NAVY, font=f_huge, spacing=14)
    d4.text((100, 580), "É obrigação da sua empresa aparecer todos os dias.", fill=C_LIGHT_SLATE, font=f_med)
    d4.text((100, 1000), "Leia a legenda completa  ↘", fill=C_GOLD_DARKER, font=f_med)
    im4.save(pasta / "ref_afirmacao_tweet_box_claro.png")

    # 5. Metáfora Visual 3D Cadeira - TEMA ESCURO
    im5, d5 = _criar_base_escuro()
    d5.text((540, 180), "Você não precisa fazer igual.", fill=C_WHITE, font=f_big, anchor="mm")
    d5.text((540, 235), "Nem pensar igual.", fill=C_WHITE, font=f_big, anchor="mm")
    cx, cy = 540, 610
    for row in range(-2, 3):
        for col in range(-3, 4):
            px = cx + col * 90
            py = cy + row * 90
            if row == 0 and col == 0:
                d5.rounded_rectangle([(px - 32, py - 32), (px + 32, py + 32)], radius=12, fill=C_GOLD)
                d5.text((px, py), "★", fill=C_DARK_BG, font=f_big, anchor="mm")
            else:
                d5.rounded_rectangle([(px - 22, py - 22), (px + 22, py + 22)], radius=8, fill=C_DARK_BORDER)
    d5.text((540, 930), "Faça diferente. Seja estratégico.", fill=C_WHITE, font=f_big, anchor="mm")
    d5.text((540, 990), "O marketing que copia, some.", fill=C_SLATE, font=f_med, anchor="mm")
    d5.line([(100, 1180), (980, 1180)], fill=C_DARK_BORDER, width=1)
    d5.text((100, 1220), "@kav.mkt", fill=C_MUTED, font=f_small)
    d5.text((980, 1220), "2026", fill=C_MUTED, font=f_small, anchor="ra")
    im5.save(pasta / "ref_destaque_dourado.png")

    # 6. Quebra de Objeção - TEMA CLARO INVERTIDO (Sem textão)
    im6, d6 = _criar_base_claro()
    d6.rounded_rectangle([(100, 150), (320, 200)], radius=20, outline=C_LIGHT_BORDER, fill=C_LIGHT_CARD)
    d6.text((210, 175), "@kav.mkt", fill=C_LIGHT_SLATE, font=f_small, anchor="mm")
    d6.text((100, 360), "Você não precisa\\nabaixar o seu preço.", fill=C_LIGHT_NAVY, font=f_huge, spacing=14)
    d6.text((100, 560), "Preço baixo atrai cliente difícil. Posicionamento atrai valor.", fill=C_GOLD_DARKER, font=f_med)
    d6.rounded_rectangle([(370, 1100), (710, 1160)], radius=30, outline=C_LIGHT_BORDER, fill=C_LIGHT_CARD)
    d6.text((540, 1130), "→   Leia a legenda", fill=C_LIGHT_NAVY, font=f_bold, anchor="mm")
    im6.save(pasta / "ref_quebra_objecao_claro.png")
