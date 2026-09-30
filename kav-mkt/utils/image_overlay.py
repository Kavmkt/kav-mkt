"""Pós-processamento de imagens geradas pela IA: redimensionamento, aplicação de logo e guias visuais."""
from __future__ import annotations

import io
from pathlib import Path
from typing import Optional
from PIL import Image, ImageDraw

LARGURA_PADRAO = 1080
ALTURA_PADRAO = 1350  # 4:5 vertical feed Instagram (1080x1440 para campanhas quando especificado)
LOGO_LARGURA = 0.30  # fração da largura do canvas
LOGO_MARGEM = 0.08   # fração da largura do canvas a partir das bordas
COR_MARCADOR_GUIA = (255, 0, 255, 255)  # magenta pura para guia visual


def _png(imagem: Image.Image) -> bytes:
    buf = io.BytesIO()
    imagem.save(buf, format="PNG")
    return buf.getvalue()


def dimensoes(imagem_bytes: bytes) -> tuple[int, int]:
    """Largura e altura reais de uma imagem."""
    im = Image.open(io.BytesIO(imagem_bytes))
    return im.size


def recortar_formato_final(
    imagem_bytes: bytes, largura: int = LARGURA_PADRAO, altura: int = ALTURA_PADRAO
) -> bytes:
    """Redimensiona/ajusta a imagem gerada pela IA para o tamanho final exato."""
    im = Image.open(io.BytesIO(imagem_bytes)).convert("RGB")
    im_final = im.resize((largura, altura), Image.LANCZOS)
    return _png(im_final)


def guia_posicao_logo(
    caminho_logo: Path,
    posicao: str,
    largura: int = LARGURA_PADRAO,
    altura: int = ALTURA_PADRAO,
    margem_extra_vertical: float = 0.0,
) -> bytes:
    """Canvas transparente do MESMO tamanho do post final, com o logo já
    posicionado onde deve aparecer. Enviado como referência para a IA copiar posição e
    escala exatas do logo — e, de quebra, dar a ela mais um sinal visual (junto com a
    referência de layout) da proporção de saída esperada.

    `margem_extra_vertical` (fração 0-1, só quando `posicao` é superior/inferior): soma à
    margem de respiro vertical do logo a mesma folga usada para avisar a IA sobre o corte
    de topo/rodapé (ver `agents.agente_design._margem_corte_vertical`).
    """
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

    margem_vertical = margem + int(altura * margem_extra_vertical)
    y = margem_vertical if (posicao.startswith("superior") or posicao.startswith("topo")) else altura - logo.height - margem_vertical

    canvas.paste(logo, (x, y), logo)
    return _png(canvas)


def guia_zona_cta(
    largura: int = LARGURA_PADRAO,
    altura: int = ALTURA_PADRAO,
    margem_extra_vertical: float = 0.0,
    altura_fracao: float = 0.10,
) -> bytes:
    """Canvas transparente do MESMO tamanho do post final, com um retângulo sólido
    marcando a área exata onde a faixa de CTA (localização + WhatsApp) de uma peça de
    campanha deve ficar — mesma ideia de `guia_posicao_logo`, adaptada pra um elemento
    novo."""
    canvas = Image.new("RGBA", (largura, altura), (0, 0, 0, 0))
    margem_lateral = int(largura * LOGO_MARGEM)
    margem_vertical = int(largura * LOGO_MARGEM) + int(altura * margem_extra_vertical)
    altura_zona = int(altura * altura_fracao)
    caixa = (
        margem_lateral,
        altura - margem_vertical - altura_zona,
        largura - margem_lateral,
        altura - margem_vertical,
    )
    desenho = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ImageDraw.Draw(desenho).rounded_rectangle(caixa, radius=altura_zona // 3, fill=COR_MARCADOR_GUIA)
    canvas.alpha_composite(desenho)
    return _png(canvas)


def aplicar_logo(
    imagem_bytes: bytes, caminho_logo: Optional[Path], posicao: str = "inferior-direito"
) -> bytes:
    """Aplica o logotipo oficial do cliente com nitidez vetorial e transparência perfeita.
    Evita que a IA generativa desenhe logos distorcidos ou com letras trocadas.
    """
    if not caminho_logo or not Path(caminho_logo).exists():
        return imagem_bytes

    im = Image.open(io.BytesIO(imagem_bytes)).convert("RGBA")
    logo = Image.open(caminho_logo).convert("RGBA")

    largura_logo = int(im.width * 0.22)
    altura_logo = max(1, int(logo.height * largura_logo / logo.width))
    logo_redim = logo.resize((largura_logo, altura_logo), Image.LANCZOS)

    margem = int(im.width * 0.06)

    if "esquerdo" in posicao:
        x = margem
    elif "centro" in posicao:
        x = (im.width - logo_redim.width) // 2
    else:
        x = im.width - logo_redim.width - margem

    if "superior" in posicao or "topo" in posicao:
        y = margem
    else:
        y = im.height - logo_redim.height - margem

    im.paste(logo_redim, (x, y), logo_redim)
    buf = io.BytesIO()
    im.convert("RGB").save(buf, format="PNG")
    return buf.getvalue()
