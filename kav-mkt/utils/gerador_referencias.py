"""Gerador automático dos templates de referência oficiais da Kav em 1080x1350.

Gera os 5 layouts oficiais da Kav caso ainda não existam no disco,
garantindo que qualquer máquina que clone ou dê git pull tenha as referências prontas.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1350
C_NAVY_BG = (0, 20, 36)        # #001424
C_NAVY_CARD = (3, 30, 52)      # #031E34
C_GOLD = (238, 183, 48)        # #EEB730 (Dourado Kav)
C_WHITE = (255, 255, 255)      # #FFFFFF
C_SLATE = (148, 163, 184)      # #94A3B8
C_MUTED = (80, 95, 125)        # #505F7D
C_BORDER = (18, 52, 82)        # #123452


def garantir_referencias_kav(pasta_referencias: Path) -> None:
    pasta_referencias.mkdir(parents=True, exist_ok=True)
    arquivos_esperados = [
        "ref_manifesto_palavra_dourada.png",
        "ref_afirmacao_tweet_box.png",
        "ref_impacto_condensado_grid.png",
        "ref_destaque_dourado.png",
        "ref_quebra_objecao_card.png",
    ]
    faltando = [arq for arq in arquivos_esperados if not (pasta_referencias / arq).exists()]
    if not faltando:
        return

    _gerar_todas(pasta_referencias)


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
        f_huge = ImageFont.truetype(font_bold_path, 72)
        f_big = ImageFont.truetype(font_bold_path, 56)
        f_med = ImageFont.truetype(font_bold_path, 44)
        f_bold = ImageFont.truetype(font_bold_path, 30)
        f_small_b = ImageFont.truetype(font_bold_path, 22)
    else:
        f_huge = f_big = f_med = f_bold = f_small_b = ImageFont.load_default()

    if font_reg_path:
        f_reg = ImageFont.truetype(font_reg_path, 28)
        f_small = ImageFont.truetype(font_reg_path, 22)
    else:
        f_reg = f_small = ImageFont.load_default()

    return f_huge, f_big, f_med, f_bold, f_reg, f_small, f_small_b


def _criar_base(com_grid=False):
    im = Image.new("RGB", (W, H), C_NAVY_BG)
    draw = ImageDraw.Draw(im)
    for y in range(H):
        t = y / H
        g = int(24 * (1 - t * 0.5) + 12 * (t * 0.5))
        b = int(44 * (1 - t * 0.5) + 20 * (t * 0.5))
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

    # 1. Manifesto
    im1, d1 = _criar_base()
    d1.rectangle([(440, 140), (640, 190)], outline=C_GOLD, width=2)
    d1.text((540, 165), "KAV · PERFORMANCE", fill=C_GOLD, font=f_small_b, anchor="mm")
    d1.text((100, 480), "Improviso", fill=C_WHITE, font=f_huge)
    d1.text((100, 580), "não constrói", fill=C_GOLD, font=f_huge)
    d1.line([(100, 675), (550, 675)], fill=C_GOLD, width=4)
    d1.text((100, 710), "empresa.", fill=C_WHITE, font=f_huge)
    d1.rounded_rectangle([(390, 1100), (690, 1165)], radius=32, outline=C_SLATE, width=2)
    d1.text((520, 1132), "→  Leia a legenda", fill=C_WHITE, font=f_reg, anchor="mm")
    d1.text((100, 1260), "@kav.mkt", fill=C_MUTED, font=f_small)
    d1.text((980, 1260), "2026", fill=C_MUTED, font=f_small, anchor="ra")
    im1.save(pasta / "ref_manifesto_palavra_dourada.png")

    # 2. Afirmação Tweet Box
    im2, d2 = _criar_base()
    d2.ellipse([(100, 160), (145, 205)], fill=C_GOLD)
    d2.text((122, 182), "K", fill=C_NAVY_BG, font=f_small_b, anchor="mm")
    d2.rounded_rectangle([(160, 160), (330, 205)], radius=22, outline=C_BORDER, fill=C_NAVY_CARD)
    d2.text((245, 182), "@kav.mkt", fill=C_SLATE, font=f_small, anchor="mm")
    d2.text((100, 420), "Não é trabalho\ndo seu cliente se\nlembrar de você.", fill=C_WHITE, font=f_big, spacing=20)
    d2.rounded_rectangle([(95, 780), (985, 930)], radius=24, outline=C_BORDER, fill=C_NAVY_CARD)
    d2.text((130, 825), "É sua obrigação ter a certeza de que ele não vai te esquecer.", fill=C_WHITE, font=f_bold)
    d2.text((130, 875), "Com tráfego local no raio certo, sua marca aparece todos os dias.", fill=C_SLATE, font=f_small)
    d2.text((100, 1020), "Leia a legenda", fill=C_GOLD, font=f_bold)
    d2.text((320, 1020), "↘", fill=C_GOLD, font=f_bold)
    d2.save(pasta / "ref_afirmacao_tweet_box.png")

    # 3. Impacto Grid
    im3, d3 = _criar_base(com_grid=True)
    d3.rounded_rectangle([(100, 160), (380, 215)], radius=28, fill=C_NAVY_CARD, outline=C_GOLD, width=2)
    d3.text((240, 187), "📈 QUER CRESCER?", fill=C_GOLD, font=f_small_b, anchor="mm")
    d3.text((100, 380), "ENTÃO PARE DE\nTRATAR TRÁFEGO\nCOMO UM GASTO!", fill=C_WHITE, font=f_huge, spacing=15)
    d3.rounded_rectangle([(770, 600), (840, 670)], radius=16, fill=C_GOLD)
    d3.text((805, 635), "↘", fill=C_NAVY_BG, font=f_med, anchor="mm")
    termos = "Tráfego Local · Performance · PMEs · Geofencing · Conversão · WhatsApp · ROI"
    d3.text((100, 1100), termos, fill=C_MUTED, font=f_small)
    im3.save(pasta / "ref_impacto_condensado_grid.png")

    # 4. Destaque Dourado
    im4, d4 = _criar_base()
    d4.text((540, 220), "Você não precisa disputar o país todo.", fill=C_SLATE, font=f_bold, anchor="mm")
    d4.text((540, 280), "nem queimar orçamento no escuro.", fill=C_SLATE, font=f_reg, anchor="mm")
    cx, cy = 540, 620
    for row in range(-2, 3):
        for col in range(-3, 4):
            px = cx + col * 90
            py = cy + row * 90
            if row == 0 and col == 0:
                d4.rounded_rectangle([(px - 34, py - 34), (px + 34, py + 34)], radius=12, fill=C_GOLD)
                d4.text((px, py), "★", fill=C_NAVY_BG, font=f_med, anchor="mm")
            else:
                d4.rounded_rectangle([(px - 25, py - 25), (px + 25, py + 25)], radius=8, fill=C_BORDER)
    d4.text((540, 920), "Domine o raio de 5 km.", fill=C_WHITE, font=f_big, anchor="mm")
    d4.text((540, 990), "Seja a referência do seu bairro.", fill=C_GOLD, font=f_big, anchor="mm")
    im4.save(pasta / "ref_destaque_dourado.png")

    # 5. Quebra Objeção
    im5, d5 = _criar_base()
    d5.rounded_rectangle([(100, 150), (340, 200)], radius=25, outline=C_BORDER, fill=C_NAVY_CARD)
    d5.text((220, 175), "@kav.mkt · Estratégia", fill=C_SLATE, font=f_small, anchor="mm")
    d5.text((100, 360), "Você não precisa", fill=C_WHITE, font=f_huge)
    d5.text((100, 460), "abaixar o seu preço.", fill=C_WHITE, font=f_huge)
    d5.rounded_rectangle([(95, 620), (985, 820)], radius=24, outline=C_GOLD, fill=C_NAVY_CARD, width=2)
    d5.text((140, 675), "Preço baixo atrai cliente difícil.", fill=C_GOLD, font=f_med)
    d5.text((140, 740), "Posicionamento e tráfego certo atraem quem valoriza seu serviço.", fill=C_WHITE, font=f_reg)
    d5.rounded_rectangle([(100, 920), (480, 990)], radius=35, fill=C_NAVY_CARD, outline=C_BORDER)
    d5.text((290, 955), "Arrasta pra entender  →", fill=C_WHITE, font=f_bold, anchor="mm")
    im5.save(pasta / "ref_quebra_objecao_card.png")


if __name__ == "__main__":
    import sys
    destino = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("clientes/kav/referencias")
    _gerar_todas(destino)
    print("Todas as referências geradas em:", destino)
