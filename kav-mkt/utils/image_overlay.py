"""Pós-processamento da imagem gerada pela IA: recorte para o formato final exato.

O logo do cliente NÃO é mais colado aqui por código — ele é enviado como imagem de
referência para o gerador de imagem (ver agents/agente_design.py), que o desenha na cena
junto com o resto. Isso substituiu a abordagem anterior (IA deixa a área livre, código
cola o logo por cima), que tinha dificuldade em acertar margens/posição de forma
confiável.
"""
from io import BytesIO

from PIL import Image

LARGURA_PADRAO = 1080
ALTURA_PADRAO = 1440


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


def _png(imagem: Image.Image) -> bytes:
    saida = BytesIO()
    imagem.save(saida, format="PNG")
    return saida.getvalue()
