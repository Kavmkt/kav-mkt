from __future__ import annotations
"""Pós-processamento da imagem gerada pela IA: ajuste pro formato final exato, e
montagem dos "guias" (logo, zona de CTA) enviados à IA como referência.

O logo do cliente NÃO é colado aqui por código — ele é enviado como imagem de
referência para o gerador de imagem (ver agents/agente_design.py), que o desenha na cena
junto com o resto. Mas o arquivo do logo sozinho tem uma proporção bem diferente da
imagem final (uma faixa larga e baixa, contra um retrato 1080x1440) — mandar essa
referência "torta" junto com o layout (que já é 1080x1440) parece confundir o modelo
sobre qual proporção de saída ele deve gerar. Por isso o logo é colado, por código, num
canvas transparente do TAMANHO FINAL antes de virar referência — assim toda referência
de "formato" que a IA recebe já está na proporção certa.

BUG CORRIGIDO EM 2026-09-27 (definitivamente, depois de 3 tentativas anteriores só de
ajustar margem/guia — ver histórico de commits): `recortar_formato_final` fazia um corte
"cover" (igual `object-fit: cover` do CSS) sempre que a API devolvia um tamanho diferente
do pedido (o mais comum: pedido "1072x1440", devolvido "1024x1536" — API não respeita o
tamanho customizado com frequência). Não importa quanta margem de segurança se avise a
IA generativa por texto ou por guia visual, ela nunca vai ser 100% precisa — então
QUALQUER corte de verdade sempre tinha chance de cortar logo, headline ou a faixa de CTA
que estivessem perto da borda. A solução definitiva (a mesma já usada num projeto
anterior da Kav — ponto-car original) é simplesmente NÃO CORTAR: em vez de recortar o
excesso, `recortar_formato_final` agora estica/redimensiona a imagem inteira direto pro
tamanho final (1080x1440), sem cortar nada. Isso garante que absolutamente nada do que a
IA desenhou é perdido — o preço é uma distorção leve de proporção quando o tamanho
devolvido é bem diferente do pedido (ex: 1024x1536 → 1080x1440 estica a imagem ~5% na
largura e encolhe ~6% na altura; para fotos de comida isso é imperceptível na prática, e
é sempre preferível a cortar o logo ou o texto de propósito).
"""
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw

LARGURA_PADRAO = 1080
ALTURA_PADRAO = 1440
LOGO_LARGURA = 0.30  # fração da largura do canvas
LOGO_MARGEM = 0.08  # fração da largura do canvas, a partir de cada borda (igual à
# margem de segurança usada no brief em agents/agente_design.py — mesma régua nos dois
# lugares)


def recortar_formato_final(imagem_bytes: bytes, largura: int = LARGURA_PADRAO, altura: int = ALTURA_PADRAO) -> bytes:
    """Redimensiona pro formato final exato SEM cortar nada (ver docstring do módulo pro
    porquê) — estica a imagem inteira pra largura x altura, mesmo que o tamanho de origem
    tenha uma proporção um pouco diferente. Mantém o nome antigo (era um recorte) porque
    é usado em vários agentes; a assinatura (bytes -> bytes) não mudou, só o miolo."""
    imagem = Image.open(BytesIO(imagem_bytes)).convert("RGB")
    imagem = imagem.resize((largura, altura), Image.LANCZOS)
    return _png(imagem)


def guia_posicao_logo(
    caminho_logo: Path,
    posicao: str,
    largura: int = LARGURA_PADRAO,
    altura: int = ALTURA_PADRAO,
    margem_extra_vertical: float = 0.0,
) -> bytes:
    """Canvas transparente do MESMO tamanho do post final (1080x1440), com o logo já
    posicionado onde deve aparecer. Enviado como referência para a IA copiar posição e
    escala exatas do logo — e, de quebra, dar a ela mais um sinal visual (junto com a
    referência de layout) da proporção de saída esperada.

    `margem_extra_vertical` (fração 0-1, só quando `posicao` é superior/inferior): soma à
    margem de respiro vertical do logo a mesma folga usada para avisar a IA sobre o corte
    de topo/rodapé (ver `agents.agente_design._margem_corte_vertical`). Corrigido em
    2026-09-27: antes só o texto do brief avisava essa folga extra, e o guia visual (que
    pesa mais que o texto pra IA generativa) mostrava o logo só com a margem "normal" —
    então mesmo a IA seguindo o guia à risca, o logo ficava perto o bastante da borda pra
    ser cortado quando a API gerava num tamanho mais alto que o pedido. Passar essa folga
    aqui, embutida na própria posição do guia, é mais confiável do que só pedir por
    texto."""
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
    y = margem_vertical if posicao.startswith("superior") else altura - logo.height - margem_vertical
    canvas.paste(logo, (x, y), logo)
    return _png(canvas)


COR_MARCADOR_GUIA = (255, 0, 255, 255)  # magenta pura: nunca aparece numa foto de comida
# ou na paleta de marca de nenhum cliente — inequívoco como "isto é só guia, não desenhe
# essa cor de verdade" para a IA generativa.


def guia_zona_cta(
    largura: int = LARGURA_PADRAO,
    altura: int = ALTURA_PADRAO,
    margem_extra_vertical: float = 0.0,
    altura_fracao: float = 0.10,
) -> bytes:
    """Canvas transparente do MESMO tamanho do post final, com um retângulo sólido
    marcando a área exata onde a faixa de CTA (localização + WhatsApp) de uma peça de
    campanha deve ficar — mesma ideia de `guia_posicao_logo`, adaptada pra um elemento
    novo (não existe arquivo de referência pra desenhar por cima, então o retângulo
    inteiro É o guia).

    Criada em 2026-09-27 depois de ver, em teste real, a faixa de CTA sendo cortada
    (a mesma folga de segurança, quando pedida só por texto no brief, não bastou — a IA
    generativa insiste em colar esse tipo de elemento bem na borda inferior, ignorando a
    instrução em palavras). Um guia visual pesa mais que texto, igual já valia para o
    logo.
    """
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


def dimensoes(imagem_bytes: bytes) -> tuple:
    """Largura e altura reais de uma imagem (para diagnosticar se a API devolveu o
    tamanho que foi pedido — nunca assuma, meça)."""
    return Image.open(BytesIO(imagem_bytes)).size


def _png(imagem: Image.Image) -> bytes:
    saida = BytesIO()
    imagem.save(saida, format="PNG")
    return saida.getvalue()
