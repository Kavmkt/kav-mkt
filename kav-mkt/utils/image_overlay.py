"""Pós-processamento da imagem gerada pela IA: recorte para o formato final exato, e
montagem do "guia de logo" enviado à IA como referência.

O logo do cliente NÃO é colado aqui por código — ele é enviado como imagem de
referência para o gerador de imagem (ver agents/agente_design.py), que o desenha na cena
junto com o resto. Mas o arquivo do logo sozinho tem uma proporção bem diferente da
imagem final (uma faixa larga e baixa, contra um retrato 1080x1440) — mandar essa
referência "torta" junto com o layout (que já é 1080x1440) parece confundir o modelo
sobre qual proporção de saída ele deve gerar, e foi isso que causava corte de texto no
topo/rodapé mesmo com a margem pedida no brief (visto em 2026-09-23). Por isso o logo é
colado, por código, num canvas transparente do TAMANHO FINAL antes de virar referência —
assim toda referência de "formato" que a IA recebe já está na proporção certa.
"""
from io import BytesIO
from pathlib import Path

from PIL import Image

LARGURA_PADRAO = 1080
ALTURA_PADRAO = 1440
LOGO_LARGURA = 0.30  # fração da largura do canvas
LOGO_MARGEM = 0.06  # fração da largura do canvas, a partir de cada borda


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


def guia_posicao_logo(caminho_logo: Path, posicao: str, largura: int = LARGURA_PADRAO, altura: int = ALTURA_PADRAO) -> bytes:
    """Canvas transparente do MESMO tamanho do post final (1080x1440), com o logo já
    posicionado onde deve aparecer. Enviado como referência para a IA copiar posição e
    escala exatas do logo — e, de quebra, dar a ela mais um sinal visual (junto com a
    referência de layout) da proporção de saída esperada."""
    canvas = Image.new("RGBA", (largura, altura), (0, 0, 0, 0))
    logo = Image.open(caminho_logo).convert("RGBA")
    largura_logo = int(largura * LOGO_LARGURA)
    logo = logo.resize((largura_logo, max(1, int(logo.height * largura_logo / logo.width))), Image.LANCZOS)
    margem = int(largura * LOGO_MARGEM)
    if posicao.endswith("esquerdo"):
        x = margem
    elif posicao.endswith("centro"):
        x = (largura - logo.width) // 2
    else:
        x = largura - logo.width - margem
    y = margem if posicao.startswith("superior") else altura - logo.height - margem
    canvas.paste(logo, (x, y), logo)
    return _png(canvas)


def dimensoes(imagem_bytes: bytes) -> tuple:
    """Largura e altura reais de uma imagem (para diagnosticar se a API devolveu o
    tamanho que foi pedido — nunca assuma, meça)."""
    return Image.open(BytesIO(imagem_bytes)).size


def _png(imagem: Image.Image) -> bytes:
    saida = BytesIO()
    imagem.save(saida, format="PNG")
    return saida.getvalue()
