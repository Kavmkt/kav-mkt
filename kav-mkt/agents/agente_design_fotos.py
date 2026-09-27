from __future__ import annotations
"""Agente de Design (Fotos): escreve o brief e gera a imagem final para clientes "de
fotos" (config.json com "tipo": "fotos") — hoje só o NN Restaurante.

Isolado de agents/agente_design.py (usado por ponto-car e pelo agente_carrossel de kav):
nenhum ajuste feito aqui afeta o fluxo dos outros clientes, e vice-versa. Só importa
dali `escolher_referencia`, `AREAS_LOGO`, `MARGEM_SEGURANCA_BORDA` e
`_margem_corte_vertical` — utilidades genéricas e sem estado (não são reescritas, só
lidas), reaproveitadas pra não duplicar geometria/constantes que não têm nada de
específico de cliente.

DIFERENÇA CENTRAL para o fluxo de produto/carrossel: aqui a cena NÃO é gerada do zero
pela IA. A foto real do prato/ambiente (escolhida por agents/agente_foto.py em
clientes/<slug>/fotos/) é enviada como referência OBRIGATÓRIA e deve permanecer
praticamente inalterada — a IA só aplica um tratamento gráfico diagramado por cima dela
(headline, selo do prato e o logo do cliente), no estilo do KV do cliente e da
referência de layout sorteada (quando houver), exatamente como pedido pelo cliente: a
referência de layout e a foto real vão juntas, na mesma chamada, para o gerador de
imagem.
"""
import base64
from typing import Optional

from agents.agente_design import AREAS_LOGO, MARGEM_SEGURANCA_BORDA, _margem_corte_vertical
from utils import image_overlay, openai_client
from utils.openai_client import chamar_ia

# Placeholders substituídos com .replace() (e não .format()): a skill do cliente pode ter
# chaves {} que quebrariam o .format().
SYSTEM_PROMPT = """Você é o Diretor de Arte da Kav (@kav.mkt). Sua função é escrever o
brief de UMA peça do NN Restaurante, pronto para ser enviado direto a um gerador de
imagem por IA — sem chance de retrabalho, então precisa ser completo e específico logo
na primeira vez.

DIRETRIZES DE MARCA E KV DO CLIENTE:
__SKILL__

Contexto de produção (o gerador de imagem recebe junto com o seu brief):
- a FOTO REAL do prato/buffet/ambiente a ser usada — ela é a base da peça e chega já
  pronta (fotografada de verdade). Ela deve permanecer PRATICAMENTE INALTERADA: mesmo
  enquadramento, mesma comida/ambiente, mesma iluminação original. Você não está
  pedindo uma cena nova nem uma "reimaginação" do prato — está pedindo a aplicação de um
  tratamento gráfico (texto, faixas, selo, logo) por cima dela, como uma arte de post
  montada sobre uma foto real;
__CONTEXTO_LAYOUT__
- a referência oficial do LOGOTIPO DA MARCA N&N: uma imagem contendo o logo oficial do cliente — reproduza esse logotipo com MÁXIMA FIDELIDADE na arte (mesmas formas, tipografia, cores e proporções), perfeitamente diagramado e integrado ao layout do post (no topo ou no cabeçalho em área de destaque), com contraste evidente e margens de respiro confortáveis (~5% das bordas), sem distorcer nem reinventar a marca;

IMPORTANTE: as referências de layout e de logo estão no formato final exato do post
(retrato, mais alto que largo). O resultado final também deve sair nessa MESMA proporção
— não em quadrado nem em outro formato, mesmo que a foto real tenha outra proporção
original (ajuste o enquadramento dela pra caber no formato retrato final, sem inventar
conteúdo novo fora do que já está na foto).

MARGENS DE SEGURANÇA — valem para TEXTO (headline e selo) e para o LOGO, nenhum dos
dois pode invadir essas faixas, e nenhum dos dois pode ser colocado sobre uma parte
importante da foto real (ex: em cima do prato):
- Topo e rodapé: depois de gerada, a imagem perde cerca de __MARGEM__% do topo e
  __MARGEM__% do rodapé (ajuste de proporção para o formato final do post). Trate essa
  faixa como fora dos limites — nada importante pode ficar nela.
- TODAS as bordas (topo, rodapé e as duas laterais): mantenha texto e logo a pelo menos
  __MARGEM_LATERAL__% de distância de qualquer borda da imagem. Nunca cole texto ou o
  logo rente à borda, mesmo nas laterais.
- O logo vai exatamente na posição mostrada no guia de logo (__AREA_LOGO__, no mesmo
  tamanho e escala do guia), nunca cobrindo partes nobres do prato. Não mova o logo para
  outra área da imagem além dessa.

CORES: use somente as cores da marca listadas nas diretrizes acima para os elementos
gráficos (bloco da headline, selo do prato, faixas, fundo atrás do logo) — não invente
cores fora dessa paleta. Garanta contraste forte entre cada texto e a foto por trás.

O brief (em inglês) deve definir, em um único parágrafo denso:
- que a foto de referência é a foto REAL a ser usada como base, sem alterar o
  prato/ambiente nela — só aplicando o tratamento gráfico por cima, encaixado no
  formato retrato final;
- a headline e o selo do prato, com o tratamento gráfico previsto no KV do cliente
  (fonte serifada de destaque na headline, fonte geométrica no selo), usando só as
  cores da marca;
- a aplicação fiel do logo a partir da referência de logotipo, perfeitamente integrado no
  topo/cabeçalho da peça com excelente contraste.

Regras de texto na imagem:
- Renderize a headline e o selo EXATAMENTE como informados, palavra por palavra, em
  português — sem traduzir, resumir ou acrescentar palavras.
- Nenhum outro texto além deles (sem preço inventado, sem slogan não informado).
- Letras grandes e legíveis, sempre dentro das margens de segurança descritas acima, e
  nunca sobrepostas a uma parte importante do prato/ambiente da foto real.

Retorne APENAS o brief em texto corrido, em inglês — exceto a headline e o selo, citados
entre aspas exatamente em português. Sem explicações, sem markdown, sem listas.
"""

CONTEXTO_COM_REFERENCIA = (
    "- uma imagem de referência de layout do cliente, que define só a ESTRUTURA GRÁFICA\n"
    "  a reproduzir (posição e forma da headline, do selo, das faixas de cor) — a CENA em\n"
    "  si vem da foto real, não desta referência: ignore qualquer prato, ambiente, texto\n"
    "  ou logo mostrado nela, copie só o tratamento gráfico;"
)
CONTEXTO_SEM_REFERENCIA = (
    "- nenhuma referência de layout: descreva também o tratamento gráfico (posição e\n"
    "  forma da headline, do selo e das faixas) seguindo o KV do cliente, sempre por\n"
    "  cima da foto real, sem cobrir as partes importantes dela;"
)


def gerar_brief_foto(copy: dict, foto: dict, cliente: dict, referencia: Optional[dict]) -> str:
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
    partes.append(f'Headline (renderizar exatamente): "{copy.get("headline_imagem")}"')
    if copy.get("selo_produto"):
        partes.append(f'Selo do prato (renderizar exatamente): "{copy["selo_produto"]}"')
    partes.append(
        'Aplicação da marca (seguir rigorosamente o guia de logo, não mova para outra área): '
        'Reproduzir fielmente o logotipo oficial da N&N Restaurante exatamente na posição e '
        'escala mostradas no guia de logo, garantindo contraste evidente e margens de respiro '
        'de cerca de 5% das bordas.'
    )
    return chamar_ia(system=system, prompt="\n".join(partes), max_tokens=650, temperature=0.8)


def gerar_imagem_foto(brief: str, foto: dict, cliente: dict, referencia: Optional[dict]) -> dict:
    """Gera a imagem do post a partir da foto REAL escolhida (referência obrigatória) +,
    quando houver, a referência de layout do cliente + a referência de logo do cliente."""
    avisos = []
    referencias_imagem = [(
        foto["arquivo"].read_bytes(),
        "the REAL photo to use as the base of this piece (a real dish, buffet or venue "
        "photo). Keep it essentially unchanged — same framing, same food/venue, same "
        "original lighting. Do not invent a new scene or redesign what's in it; you are "
        "only adding a graphic text/logo treatment on top of it.",
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
        # Canvas do tamanho final (não o arquivo do logo sozinho, que tem proporção bem
        # diferente — ex: uma faixa larga e baixa — e confunde o modelo sobre a
        # proporção de saída esperada; ver docstring de utils/image_overlay). Corrigido
        # em 2026-09-27: antes esta função enviava o arquivo bruto do logo (direto de
        # cliente["logo_referencias"], quando existia) como referência — igual ao
        # agente_design.py fazia antes de adotar esse canvas-guia. É essa a causa mais
        # provável do corte de logo/rodapé visto pelo cliente: com múltiplas referências
        # de proporções bem diferentes (foto real + layout + logo "torto"), o modelo
        # tende a gerar num tamanho mais alto que o pedido, que depois é recortado.
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

    bruta = None
    layout_usado = referencia["arquivo"].name if referencia else None
    try:
        imagens = [dados for dados, _ in referencias_imagem]
        prompt = _prompt_com_referencias(brief, [desc for _, desc in referencias_imagem])
        bruta = openai_client.gerar_imagem_com_referencias(prompt, imagens)
    except Exception as exc:
        raise RuntimeError(
            f"A geração da imagem com a foto real falhou ({exc}). Sem a foto como "
            "referência não é possível montar a peça deste cliente."
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
    partes.append("Post to create:\n" + brief)
    return "\n\n".join(partes)


def _logo(cliente: dict, referencia: Optional[dict]):
    referencia = referencia or {}
    posicao = referencia.get("logo_posicao") or cliente["config"].get("logo_posicao", "inferior-direito")
    versao = referencia.get("logo_versao", "fundo-escuro")
    arquivo = cliente["logos"].get(versao) or cliente["logos"].get("fundo-escuro")
    return arquivo, posicao
