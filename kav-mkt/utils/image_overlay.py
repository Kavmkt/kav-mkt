"""Pós-processamento da imagem gerada pela IA: recorte para o formato final exato e
aplicação do logo do cliente por código (o logo nunca é desenhado pela IA, para sair
sempre idêntico ao arquivo original).
"""
from io import BytesIO
from pathlib import Path
from typing import Optional

from PIL import Image

LARGURA_PADRAO = 1080
ALTURA_PADRAO = 1440
LOGO_LARGURA = 0.24  # fração da largura da imagem
LOGO_MARGEM = 0.05  # fração da largura da imagem, a partir das bordas


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


def aplicar_logo(imagem_bytes: bytes, caminho_logo: Optional[Path], posicao: str) -> bytes:
    """Cola o logo no canto indicado. Sem logo configurado, devolve a imagem como veio."""
    if not caminho_logo:
        return imagem_bytes
    imagem = Image.open(BytesIO(imagem_bytes)).convert("RGB")
    logo = Image.open(caminho_logo).convert("RGBA")
    largura_logo = int(imagem.width * LOGO_LARGURA)
    logo = logo.resize((largura_logo, max(1, int(logo.height * largura_logo / logo.width))), Image.LANCZOS)
    margem = int(imagem.width * LOGO_MARGEM)
    x = margem if posicao.endswith("esquerdo") else imagem.width - logo.width - margem
    y = margem if posicao.startswith("superior") else imagem.height - logo.height - margem
    imagem.paste(logo, (x, y), logo)
    return _png(imagem)


def _png(imagem: Image.Image) -> bytes:
    saida = BytesIO()
    imagem.save(saida, format="PNG")
    return saida.getvalue()
