"""Pós-processamento de imagens geradas pela IA: redimensionamento e aplicação perfeita de logo."""
from __future__ import annotations

import io
from pathlib import Path
from typing import Optional
from PIL import Image

LARGURA_PADRAO = 1080
ALTURA_PADRAO = 1350  # 4:5 vertical feed Instagram


def recortar_formato_final(
    imagem_bytes: bytes, largura: int = LARGURA_PADRAO, altura: int = ALTURA_PADRAO
) -> bytes:
    """Redimensiona/ajusta a imagem gerada pela IA para o tamanho final exato."""
    im = Image.open(io.BytesIO(imagem_bytes)).convert("RGB")
    im_final = im.resize((largura, altura), Image.LANCZOS)
    buf = io.BytesIO()
    im_final.save(buf, format="PNG")
    return buf.getvalue()


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

    # Escala proporcional harmoniosa para o logo (entre 20% e 24% da largura da arte)
    largura_logo = int(im.width * 0.22)
    altura_logo = max(1, int(logo.height * largura_logo / logo.width))
    logo_redim = logo.resize((largura_logo, altura_logo), Image.LANCZOS)

    # Margem de segurança de 6% das bordas
    margem = int(im.width * 0.06)

    # Posicionamento horizontal
    if "esquerdo" in posicao:
        x = margem
    elif "centro" in posicao:
        x = (im.width - logo_redim.width) // 2
    else:
        x = im.width - logo_redim.width - margem

    # Posicionamento vertical
    if "superior" in posicao or "topo" in posicao:
        y = margem
    else:
        y = im.height - logo_redim.height - margem

    # Sobreposição limpa com canal alfa
    im.paste(logo_redim, (x, y), logo_redim)
    buf = io.BytesIO()
    im.convert("RGB").save(buf, format="PNG")
    return buf.getvalue()
