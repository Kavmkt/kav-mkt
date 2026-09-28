"""Módulo de Pós-Processamento Fotográfico Anti-CGI.

Reduz o aspecto artificial de IA (texturas plásticas, brilhos sintéticos e saturação excessiva)
aplicando técnicas clássicas de tratamento fotográfico com Pillow e NumPy:
1. Micro-ruído óptico de sensor (film grain sutil) para quebrar a textura lisa de IA.
2. Calibração natural de saturação (remove o tom fluorescente sem esmaecer a comida).
3. Ajuste de contraste e realce de micro-textura (Unsharp Mask sutil no prato).
4. Preservação estrita de dimensões (1080x1440), tipografia e logotipo oficial.
"""
from __future__ import annotations

import io
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter


def aplicar_pos_processamento_fotografico(imagem_bytes: bytes) -> bytes:
    """Aplica tratamento de textura fotográfica realista sobre a imagem final gerada.
    Se houver qualquer falha, retorna os bytes originais de forma transparente e segura."""
    if not imagem_bytes:
        return imagem_bytes

    try:
        im = Image.open(io.BytesIO(imagem_bytes)).convert("RGB")
        w, h = im.size

        # 1. Calibrar saturação (reduz levemente os tons hiper-saturados de IA)
        enhancer_sat = ImageEnhance.Color(im)
        im = enhancer_sat.enhance(0.95)

        # 2. Leve calibração de contraste
        enhancer_con = ImageEnhance.Contrast(im)
        im = enhancer_con.enhance(1.02)

        # 3. Adicionar textura tátil / micro-granulação óptica de sensor (quebra aspecto emborrachado)
        arr = np.array(im, dtype=np.int16)
        ruido = np.random.randint(-4, 5, size=(h, w, 3), dtype=np.int16)
        arr = np.clip(arr + ruido, 0, 255).astype(np.uint8)
        im_grao = Image.fromarray(arr)

        # 4. Realce de micro-textura na comida (nitidez limpa)
        im_final = im_grao.filter(ImageFilter.UnsharpMask(radius=1.0, percent=110, threshold=3))

        out = io.BytesIO()
        im_final.save(out, format="PNG")
        return out.getvalue()
    except Exception as exc:
        print(f"[Pós-Processamento Fotográfico]: Fallback seguro ativado ({exc})")
        return imagem_bytes
