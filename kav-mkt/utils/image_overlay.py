"""Pós-processamento da imagem gerada pela IA: recorte para o formato final exato e
aplicação do logo do cliente por código (o logo nunca é desenhado pela IA, para sair
sempre idêntico ao arquivo original).
"""
from io import BytesIO
from pathlib import Path
from typing import Optional

from PIL import Image, ImageFilter

LARGURA_PADRAO = 1080
ALTURA_PADRAO = 1440
LOGO_LARGURA = 0.30  # fração da largura da imagem (≈ tamanho do logo nas referências)
LOGO_MARGEM = 0.06  # fração da largura da imagem, a partir das bordas (respiro da borda)
# Sombra atrás do logo: garante contraste mínimo mesmo quando a IA não deixou a zona
# 100% limpa. Valores em fração da largura do logo.
SOMBRA_OPACIDADE = 0.55  # 0 = sem sombra; 1 = preto sólido atrás do logo
SOMBRA_DESFOQUE = 0.02  # raio do blur, fração da largura do logo
SOMBRA_OFFSET = 0.012  # deslocamento da sombra (px, px), fração da largura do logo


def recortar_formato_final(imagem_bytes: bytes, largura: int = LARGURA_PADRAO, altura: int = ALTURA_PADRAO) -> bytes:
    """Corta e redimensiona para preencher exatamente largura x altura, sem distorcer
    (como `object-fit: cover` no CSS)."""
    imagem = Image.open(BytesIO(imagem_bytes)).convert("RGB")
    origem_w, origem_h = imagem.size
    destino_ratio = largura / altura
    if origem_w / origem_h > destino_ratio:
        novo_w, novo_h = int(origem_h * destino_ratio), origem_h
    else:
        novo_w, novo_h = origem_w, int(origem_w / destino_ratio)
    esquerda = (origem_w - novo_w) // 2
    topo = (origem_h - novo_h) // 2
    imagem = imagem.crop((esquerda, topo, esquerda + novo_w, topo + novo_h))
    imagem = imagem.resize((largura, altura), Image.LANCZOS)
    return _png(imagem)


def aplicar_logo(
    imagem_bytes: bytes,
    caminho_logo: Optional[Path],
    posicao: str,
    sombra: bool = True,
) -> bytes:
    """Cola o logo na posição indicada (ex: "inferior-esquerdo", "superior-centro"). Sem
    logo configurado, devolve a imagem como veio.

    Aplica uma sombra suave atrás do logo por padrão — é o que garante contraste do logo
    sobre qualquer fundo (claro, escuro, foto, gradiente), mesmo quando a IA não deixou
    a zona totalmente uniforme. Passe sombra=False para desligar.
    """
    if not caminho_logo:
        return imagem_bytes
    imagem = Image.open(BytesIO(imagem_bytes)).convert("RGB")
    logo = Image.open(caminho_logo).convert("RGBA")
    largura_logo = int(imagem.width * LOGO_LARGURA)
    logo = logo.resize(
        (largura_logo, max(1, int(logo.height * largura_logo / logo.width))),
        Image.LANCZOS,
    )
    margem = int(imagem.width * LOGO_MARGEM)
    if posicao.endswith("esquerdo"):
        x = margem
    elif posicao.endswith("centro"):
        x = (imagem.width - logo.width) // 2
    else:
        x = imagem.width - logo.width - margem
    y = margem if posicao.startswith("superior") else imagem.height - logo.height - margem

    if sombra:
        _aplicar_sombra(imagem, logo, x, y)
    imagem.paste(logo, (x, y), logo)
    return _png(imagem)


def _aplicar_sombra(imagem: Image.Image, logo: Image.Image, x: int, y: int) -> None:
    """Compõe uma sombra suave (silhueta preta translúcida e desfocada) atrás do logo,
    deslocada para baixo e para a direita. Cria separação visual do fundo sem alterar a
    arte original — funciona sobre qualquer cor ou foto."""
    alpha = logo.getchannel("A")
    # Reduz a opacidade da silhueta para a sombra ficar sutil.
    alpha_sombra = alpha.point(lambda p: int(p * SOMBRA_OPACIDADE))
    sombra = Image.new("RGBA", logo.size, (0, 0, 0, 0))
    sombra.putalpha(alpha_sombra)
    raio = max(2, int(logo.width * SOMBRA_DESFOQUE))
    sombra = sombra.filter(ImageFilter.GaussianBlur(raio))
    offset = max(1, int(logo.width * SOMBRA_OFFSET))
    # Recorta o que passar das bordas da imagem para não dar erro de paste.
    destino_x = max(0, x + offset)
    destino_y = max(0, y + offset)
    largura_util = min(sombra.width, imagem.width - destino_x)
    altura_util = min(sombra.height, imagem.height - destino_y)
    if largura_util <= 0 or altura_util <= 0:
        return
    sombra = sombra.crop((0, 0, largura_util, altura_util))
    imagem.paste(sombra, (destino_x, destino_y), sombra)


def _png(imagem: Image.Image) -> bytes:
    saida = BytesIO()
    imagem.save(saida, format="PNG")
    return saida.getvalue()