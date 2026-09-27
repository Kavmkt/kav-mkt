from __future__ import annotations
"""Agente de Diretor de Arte de Campanha: escreve o brief e gera a imagem final de uma
peça de ALTA PERFORMANCE (anúncio pago, Meta Ads) para clientes "de fotos" — a mesma foto
real do prato/ambiente é a base, mas o tratamento gráfico é o de um anúncio (headline de
conversão, selo, faixa de CTA com localização/WhatsApp), não o de um post orgânico de
feed.

Isolado de agents/agente_design_fotos.py (posts orgânicos): a diferença central é a
presença da faixa de CTA/localização e um tom visual mais assertivo (urgência), sem
mudar a geometria básica (margens, área do logo) — por isso reaproveita essas constantes
e o helper `_logo` de lá em vez de duplicá-los.
"""
import base64
from typing import Optional

from agents.agente_design import AREAS_LOGO, MARGEM_SEGURANCA_BORDA, _margem_corte_vertical
from agents.agente_design_fotos import _logo
from utils import image_overlay, openai_client
from utils.openai_client import chamar_ia

SYSTEM_PROMPT = """Você é o Diretor de Arte de Campanha da Kav (@kav.mkt). Sua função é
escrever o brief de UMA peça de ANÚNCIO PAGO (Meta Ads) do NN Restaurante, pronto para
ser enviado direto a um gerador de imagem por IA — sem chance de retrabalho, então
precisa ser completo e específico logo na primeira vez.

DIRETRIZES DE MARCA E KV DO CLIENTE:
__SKILL__

Isto é uma peça de TRÁFEGO PAGO (anúncio), não um post orgânico de feed — o tratamento
visual deve comunicar urgência e conversão imediata, com uma faixa/selo extra de chamada
para ação (localização + WhatsApp), além da headline e do selo do prato de um post comum.

Contexto de produção (o gerador de imagem recebe junto com o seu brief):
- a FOTO REAL do prato/buffet/ambiente a ser usada — ela é a base da peça e chega já
  pronta (fotografada de verdade). Ela deve permanecer PRATICAMENTE INALTERADA: mesmo
  enquadramento, mesma comida/ambiente, mesma iluminação original. Você não está pedindo
  uma cena nova nem uma "reimaginação" do prato — está pedindo a aplicação de um
  tratamento gráfico (texto, faixas, selo, logo, faixa de CTA) por cima dela, como uma
  arte de anúncio montada sobre uma foto real;
__CONTEXTO_LAYOUT__
- a referência oficial do LOGOTIPO DA MARCA N&N: uma imagem contendo o logo oficial do cliente — reproduza esse logotipo com MÁXIMA FIDELIDADE na arte (mesmas formas, tipografia, cores e proporções), perfeitamente diagramado e integrado ao layout do post (no topo ou no cabeçalho em área de destaque), com contraste evidente e margens de respiro confortáveis (~5% das bordas), sem distorcer nem reinventar a marca;

IMPORTANTE: as referências de layout e de logo estão no formato final exato do post
(retrato, mais alto que largo). O resultado final também deve sair nessa MESMA proporção
— não em quadrado nem em outro formato, mesmo que a foto real tenha outra proporção
original (ajuste o enquadramento dela pra caber no formato retrato final, sem inventar
conteúdo novo fora do que já está na foto).

MARGENS DE SEGURANÇA — valem para TEXTO (headline, selo e faixa de CTA) e para o LOGO,
nenhum deles pode invadir essas faixas, e nenhum pode ser colocado sobre uma parte
importante da foto real (ex: em cima do prato):
- Topo e rodapé: depois de gerada, a imagem perde cerca de __MARGEM__% do topo e
  __MARGEM__% do rodapé (ajuste de proporção para o formato final do post). Trate essa
  faixa como fora dos limites — nada importante pode ficar nela.
- TODAS as bordas (topo, rodapé e as duas laterais): mantenha texto, selo, faixa de CTA
  e logo a pelo menos __MARGEM_LATERAL__% de distância de qualquer borda da imagem. Nunca
  cole nenhum deles rente à borda, mesmo nas laterais.
- O logo vai exatamente na posição mostrada no guia de logo (__AREA_LOGO__, no mesmo
  tamanho e escala do guia), nunca cobrindo partes nobres do prato. Não mova o logo para
  outra área da imagem além dessa.
- A faixa de CTA (localização + chamada para WhatsApp) ocupa exatamente a área marcada em
  magenta no guia de zona de CTA — nunca ultrapasse esse retângulo (principalmente por
  baixo dele, é a parte mais perto da borda que será cortada). Dentro dele, desenhe um
  bloco de cor sólida (uma das cores da marca, nunca magenta) com contraste forte, curta e
  legível a distância — no estilo de selo/rótulo de anúncio, não como texto corrido.

CORES: use somente as cores da marca listadas nas diretrizes acima para os elementos
gráficos (bloco da headline, selo do prato, faixa de CTA, fundo atrás do logo) — não
invente cores fora dessa paleta. Garanta contraste forte entre cada texto e a foto por
trás.

O brief (em inglês) deve definir, em um único parágrafo denso:
- que a foto de referência é a foto REAL a ser usada como base, sem alterar o
  prato/ambiente nela — só aplicando o tratamento gráfico de anúncio por cima, encaixado
  no formato retrato final;
- a headline de alto impacto e o selo do prato, com o tratamento gráfico previsto no KV
  do cliente (fonte serifada de destaque na headline, fonte geométrica no selo), usando
  só as cores da marca;
- a faixa/selo de CTA na parte inferior com a localização e a chamada para WhatsApp, em
  bloco de cor sólida de alto contraste;
- a aplicação fiel do logo a partir da referência de logotipo, perfeitamente integrado no
  topo/cabeçalho da peça com excelente contraste.

Regras de texto na imagem:
- Renderize a headline, o selo e o texto da faixa de CTA EXATAMENTE como informados,
  palavra por palavra, em português — sem traduzir, resumir ou acrescentar palavras.
- Nenhum outro texto além desses (sem preço inventado, sem slogan não informado).
- Letras grandes e legíveis, sempre dentro das margens de segurança descritas acima, e
  nunca sobrepostas a uma parte importante do prato/ambiente da foto real.

Retorne APENAS o brief em texto corrido, em inglês — exceto a headline, o selo e o texto
da faixa de CTA, citados entre aspas exatamente em português. Sem explicações, sem
markdown, sem listas.
"""

CONTEXTO_COM_REFERENCIA = (
    "- uma imagem de referência de layout do cliente, que define só a ESTRUTURA GRÁFICA\n"
    "  a reproduzir (posição e forma da headline, do selo, das faixas de cor) — a CENA em\n"
    "  si vem da foto real, não desta referência: ignore qualquer prato, ambiente, texto\n"
    "  ou logo mostrado nela, copie só o tratamento gráfico;"
)
CONTEXTO_SEM_REFERENCIA = (
    "- nenhuma referência de layout: descreva também o tratamento gráfico (posição e\n"
    "  forma da headline, do selo, da faixa de CTA e das faixas de cor) seguindo o KV do\n"
    "  cliente, sempre por cima da foto real, sem cobrir as partes importantes dela;"
)


def gerar_brief_campanha(estrategia: dict, foto: dict, cliente: dict, referencia: Optional[dict]) -> str:
    contexto = CONTEXTO_COM_REFERENCIA if referencia else CONTEXTO_SEM_REFERENCIA
    _, posicao_logo = _logo(cliente, referencia)
    system = (
        SYSTEM_PROMPT.replace("__SKILL__", cliente["skill"])
        .replace("__CONTEXTO_LAYOUT__", contexto)
        .replace("__MARGEM__", str(_margem_corte_vertical()))
        .replace("__MARGEM_LATERAL__", str(MARGEM_SEGURANCA_BORDA))
        .replace("__AREA_LOGO__", AREAS_LOGO.get(posicao_logo, "bottom-right corner"))
    )
    partes = [f"Foto/prato: {foto.get('nome') or foto['arquivo'].name}"]
    if foto.get("categoria"):
        partes.append(f"Categoria: {foto['categoria']}")
    if foto.get("descricao"):
        partes.append(f"Descrição: {foto['descricao']}")
    partes.append(f'Headline de alto impacto (renderizar exatamente): "{estrategia.get("headline_impacto")}"')
    if estrategia.get("selo_produto"):
        partes.append(f'Selo do prato (renderizar exatamente): "{estrategia["selo_produto"]}"')
    if estrategia.get("cta"):
        partes.append(f'Texto da faixa de CTA (renderizar exatamente): "{estrategia["cta"]}"')
    partes.append(
        'Aplicação da marca (seguir rigorosamente o guia de logo, não mova para outra área): '
        'Reproduzir fielmente o logotipo oficial da N&N Restaurante exatamente na posição e '
        'escala mostradas no guia de logo, garantindo contraste evidente e margens de respiro '
        'de cerca de 5% das bordas.'
    )
    return chamar_ia(system=system, prompt="\n".join(partes), max_tokens=700, temperature=0.8)


def gerar_imagem_campanha(brief: str, foto: dict, cliente: dict, referencia: Optional[dict]) -> dict:
    """Gera a imagem da peça de campanha a partir da foto REAL escolhida (referência
    obrigatória) +, quando houver, a referência de layout do cliente + a referência de
    logo do cliente. Estrutura igual a agente_design_fotos.gerar_imagem_foto — só o brief
    muda (tom de anúncio, com faixa de CTA)."""
    avisos = []
    referencias_imagem = [(
        foto["arquivo"].read_bytes(),
        "the REAL photo to use as the base of this piece (a real dish, buffet or venue "
        "photo). Keep it essentially unchanged — same framing, same food/venue, same "
        "original lighting. Do not invent a new scene or redesign what's in it; you are "
        "only adding a graphic ad treatment on top of it.",
    )]

    if referencia:
        referencias_imagem.append((
            referencia["arquivo"].read_bytes(),
            "this brand's layout template. Reproduce ONLY its graphic treatment — "
            "placement and shape of the headline block, the dish tag/badge, color bands "
            "and typography style — never its scene, product, photo, text or logo. The "
            "final piece keeps the real dish/venue photo above as the background scene.",
        ))

    logo_arquivo, posicao_logo = _logo(cliente, referencia)
    if logo_arquivo:
        # Canvas do tamanho final, não o arquivo bruto do logo — mesma correção aplicada
        # em agente_design_fotos.py em 2026-09-27 (ver comentário lá para o porquê:
        # mandar o logo "torto", com proporção bem diferente da final, junto com outras
        # referências confunde o modelo sobre a proporção de saída esperada).
        guia_logo = image_overlay.guia_posicao_logo(
            logo_arquivo, posicao_logo, margem_extra_vertical=_margem_corte_vertical() / 100
        )
        referencias_imagem.append((
            guia_logo,
            "a template the exact same pixel dimensions as the final image, transparent "
            "everywhere except where the client's logo sits — reproduce that logo "
            "pixel-for-pixel, at that exact SCALE, keeping its exact colors, proportions "
            "and details (do not redraw, recolor or distort it). Its position (top/bottom "
            "band) is shown here exactly as it must appear in the final piece. Everywhere "
            "else in this template is transparent guidance only, not part of the visible "
            "scene.",
        ))

    # Guia da zona de CTA: criado em 2026-09-27 depois de ver, em teste real, a faixa de
    # CTA sendo cortada mesmo com a margem de segurança pedida só por texto — um guia
    # visual (igual ao do logo) pesa mais pra IA generativa do que uma instrução em
    # palavras.
    guia_cta = image_overlay.guia_zona_cta(margem_extra_vertical=_margem_corte_vertical() / 100)
    referencias_imagem.append((
        guia_cta,
        "a template the exact same pixel dimensions as the final image, transparent "
        "everywhere except a solid MAGENTA rounded rectangle — that magenta rectangle is "
        "a placeholder marking the exact area, size and position for the CTA strip (the "
        "WhatsApp/location call-to-action). Draw the actual CTA strip (a rounded solid "
        "block in one of the brand colors, never magenta, containing a WhatsApp icon and "
        "the CTA text) filling that exact rectangle — nothing belonging to the CTA strip "
        "(background, icon or text) may extend beyond it, especially not below its "
        "bottom edge. The magenta color itself must never appear in the final piece; "
        "everywhere else in this template is transparent guidance only, not part of the "
        "visible scene.",
    ))

    bruta = None
    layout_usado = referencia["arquivo"].name if referencia else None
    try:
        imagens = [dados for dados, _ in referencias_imagem]
        prompt = _prompt_com_referencias(brief, [desc for _, desc in referencias_imagem])
        bruta = openai_client.gerar_imagem_com_referencias(prompt, imagens)
    except Exception as exc:
        raise RuntimeError(
            f"A geração da imagem de campanha com a foto real falhou ({exc}). Sem a foto "
            "como referência não é possível montar a peça deste cliente."
        ) from exc
    if not bruta or not bruta.get("imagem_b64"):
        raise RuntimeError("A API de imagem não retornou nenhuma imagem.")

    if bruta.get("tamanho_pedido") and bruta.get("tamanho_real") and bruta["tamanho_pedido"] != bruta["tamanho_real"]:
        avisos.append(
            f"A API pediu {bruta['tamanho_pedido']} mas devolveu {bruta['tamanho_real']} — "
            "o recorte final ainda sai certo (1080x1440), mas a margem interna pode não "
            "bater exatamente com o que foi pedido no brief."
        )

    return {
        **_finalizar(base64.b64decode(bruta["imagem_b64"])),
        "modelo": bruta.get("modelo"),
        "qualidade": bruta.get("qualidade"),
        "tamanho_gerado": bruta.get("tamanho_real"),
        "referencia_layout": layout_usado,
        "com_foto_real": True,
        "aviso": " ".join(avisos) or None,
    }


def _finalizar(imagem_bytes: bytes) -> dict:
    final = image_overlay.recortar_formato_final(imagem_bytes)
    return {
        "imagem_b64": base64.b64encode(final).decode("ascii"),
        "tamanho": f"{image_overlay.LARGURA_PADRAO}x{image_overlay.ALTURA_PADRAO}",
    }


def _prompt_com_referencias(brief: str, descricoes: list) -> str:
    partes = [f"Reference image {i + 1} is {desc}" for i, desc in enumerate(descricoes)]
    partes.append("Ad piece to create:\n" + brief)
    return "\n\n".join(partes)
