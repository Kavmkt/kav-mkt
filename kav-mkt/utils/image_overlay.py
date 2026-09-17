"""Pós-processamento da imagem gerada pela IA: corta/redimensiona para o formato final
exato e cola o logo do cliente, se houver.

Também sabe sobrepor uma chamada (headline) por código, via `compor_imagem_final(...,
headline=...)` — hoje o Agente de Design não usa mais essa opção por padrão (a própria
IA de imagem desenha o texto na cena, GPT Image 2.5 é bem melhor nisso que o modelo
anterior). Se erros de texto cortado/embaralhado voltarem a acontecer, essa função
continua pronta para reativar o desenho por código como alternativa mais previsível.
"""
from io import BytesIO
from pathlib import Path
from typing import Optional

from PIL import Image, ImageDraw, ImageFont

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets" / "fonts"
FONTE_PADRAO = ASSETS_DIR / "Anton-Regular.ttf"
FONTE_RESERVA = ASSETS_DIR / "ArchivoBlack-Regular.ttf"

LOGOS_DIR = Path(__file__).resolve().parent.parent / "assets" / "logos"

LARGURA_PADRAO = 1080
ALTURA_PADRAO = 1440


def _colar_logo(imagem: Image.Image, cliente: Optional[str]) -> Image.Image:
    """Cola o logo do cliente (assets/logos/<cliente>.png) no canto superior direito,
    se o arquivo existir. Sem arquivo, não faz nada — recurso totalmente opcional."""
    if not cliente:
        return imagem
    caminho = LOGOS_DIR / f"{cliente}.png"
    if not caminho.exists():
        return imagem
    logo = Image.open(caminho).convert("RGBA")
    largura_alvo = int(imagem.width * 0.22)
    proporcao = largura_alvo / logo.width
    logo = logo.resize((largura_alvo, max(1, int(logo.height * proporcao))), Image.LANCZOS)
    margem = int(imagem.width * 0.05)
    posicao = (imagem.width - logo.width - margem, margem)
    imagem.paste(logo, posicao, logo)
    return imagem


def _carregar_fonte(tamanho: int) -> ImageFont.FreeTypeFont:
    caminho = FONTE_PADRAO if FONTE_PADRAO.exists() else FONTE_RESERVA
    if caminho.exists():
        return ImageFont.truetype(str(caminho), tamanho)
    return ImageFont.load_default()


def _luminancia(hex_cor: str) -> float:
    hex_cor = hex_cor.lstrip("#")
    r, g, b = (int(hex_cor[i : i + 2], 16) for i in (0, 2, 4))
    return (0.299 * r + 0.587 * g + 0.114 * b) / 255


def _cor_contraste(hex_fundo: str) -> str:
    return "#000000" if _luminancia(hex_fundo) > 0.6 else "#FFFFFF"


def _cover_resize(imagem: Image.Image, largura: int, altura: int) -> Image.Image:
    """Corta e redimensiona a imagem pra preencher exatamente largura x altura, sem
    distorcer (estilo `object-fit: cover` do CSS)."""
    origem_w, origem_h = imagem.size
    origem_ratio = origem_w / origem_h
    destino_ratio = largura / altura
    if origem_ratio > destino_ratio:
        novo_h = origem_h
        novo_w = int(origem_h * destino_ratio)
    else:
        novo_w = origem_w
        novo_h = int(origem_w / destino_ratio)
    esquerda = (origem_w - novo_w) // 2
    topo = (origem_h - novo_h) // 2
    cortada = imagem.crop((esquerda, topo, esquerda + novo_w, topo + novo_h))
    return cortada.resize((largura, altura), Image.LANCZOS)


def _quebrar_linhas(draw: ImageDraw.ImageDraw, texto: str, fonte: ImageFont.FreeTypeFont, largura_max: int) -> list:
    palavras = texto.split()
    linhas, atual = [], ""
    for palavra in palavras:
        candidato = f"{atual} {palavra}".strip()
        if draw.textlength(candidato, font=fonte) <= largura_max or not atual:
            atual = candidato
        else:
            linhas.append(atual)
            atual = palavra
    if atual:
        linhas.append(atual)
    return linhas


def _ajustar_fonte_e_linhas(draw: ImageDraw.ImageDraw, texto: str, largura_max: int, altura_max: int):
    tamanho = 96
    while tamanho >= 28:
        fonte = _carregar_fonte(tamanho)
        linhas = _quebrar_linhas(draw, texto, fonte, largura_max)
        if len(linhas) > 2:
            tamanho -= 8
            continue
        altura_linha = fonte.getbbox("Ay")[3] + 10
        if altura_linha * len(linhas) <= altura_max:
            return fonte, linhas
        tamanho -= 8
    return _carregar_fonte(28), _quebrar_linhas(draw, texto, _carregar_fonte(28), largura_max)[:2]


def compor_imagem_final(
    imagem_bytes: bytes,
    headline: str,
    cores_hex: list,
    cliente: Optional[str] = None,
    largura: int = LARGURA_PADRAO,
    altura: int = ALTURA_PADRAO,
) -> bytes:
    """Corta/redimensiona a imagem para largura x altura, cola o logo do cliente (se
    existir em assets/logos/<cliente>.png) e sobrepõe a chamada (headline) numa barra
    sólida na base, usando as cores da marca do cliente. Se `headline` vier vazio,
    devolve só a imagem redimensionada (+ logo), sem barra."""
    imagem = Image.open(BytesIO(imagem_bytes)).convert("RGB")
    imagem = _cover_resize(imagem, largura, altura)
    imagem = _colar_logo(imagem, cliente)

    if not headline:
        saida = BytesIO()
        imagem.save(saida, format="PNG")
        return saida.getvalue()

    cor_fundo = cores_hex[0] if cores_hex else "#111111"
    fundo_e_escuro = _luminancia(cor_fundo) <= 0.6

    # Preferimos uma cor de marca de verdade (ex: amarelo) a um preto/branco genérico,
    # desde que ela tenha contraste suficiente contra o fundo escolhido.
    cor_texto = None
    for candidata in cores_hex:
        if candidata == cor_fundo:
            continue
        candidata_e_clara = _luminancia(candidata) > 0.6
        if fundo_e_escuro and candidata_e_clara:
            cor_texto = candidata
            break
        if not fundo_e_escuro and not candidata_e_clara:
            cor_texto = candidata
            break
    if cor_texto is None:
        cor_texto = _cor_contraste(cor_fundo)

    imagem = imagem.convert("RGBA")
    barra_altura = int(altura * 0.18)
    barra = Image.new("RGBA", (largura, barra_altura), (*_hex_para_rgb(cor_fundo), 235))
    draw = ImageDraw.Draw(barra)

    padding = 60
    fonte, linhas = _ajustar_fonte_e_linhas(draw, headline.upper(), largura - 2 * padding, barra_altura - 40)
    altura_linha = fonte.getbbox("Ay")[3] + 12
    altura_bloco = altura_linha * len(linhas)
    y = (barra_altura - altura_bloco) // 2
    for linha in linhas:
        largura_linha = draw.textlength(linha, font=fonte)
        x = (largura - largura_linha) // 2
        draw.text((x, y), linha, font=fonte, fill=cor_texto)
        y += altura_linha

    imagem.paste(barra, (0, altura - barra_altura), barra)
    saida = BytesIO()
    imagem.convert("RGB").save(saida, format="PNG")
    return saida.getvalue()


def _hex_para_rgb(hex_cor: str) -> tuple:
    hex_cor = hex_cor.lstrip("#")
    return tuple(int(hex_cor[i : i + 2], 16) for i in (0, 2, 4))
