"""Agente de Design (Fotos): escreve o brief e gera a imagem final para clientes "de
fotos" (config.json com "tipo": "fotos") — hoje só o NN Restaurante.

Isolado de agents/agente_design.py (usado por ponto-car e pelo agente_carrossel de kav):
nenhum ajuste feito aqui afeta o fluxo dos outros clientes, e vice-versa. Só importa
dali `escolher_referencia`, `AREAS_LOGO`, `MARGEM_SEGURANCA_BORDA` e
`_margem_corte_vertical` — utilidades genéricas e sem estado (não são reescritas, só
lidas), reaproveitadas pra não duplicar geometria/constantes que não têm nada de
específico de cliente.

DIRETRIZ CENTRAL DE ARTE:
A comida mostrada na foto real (escolhida por agents/agente_foto.py em clientes/<slug>/fotos/)
é a comida autêntica do restaurante — mantenha a fidelidade aos ingredientes reais do prato,
mas ELEVE a apresentação visual: ambientação gastronômica profissional (mesa de madeira rústica,
iluminação quente de restaurante, fundo desfocado aconchegante), eliminando elementos amadores
da foto crua de celular (como mãos segurando potes plásticos ou fundos domésticos improvisados).
Sobre essa fotografia profissional, aplica-se diagramação limpa, sofisticada e sem clichês.
"""
import base64
from typing import Optional

from agents.agente_design import AREAS_LOGO, MARGEM_SEGURANCA_BORDA, _margem_corte_vertical
from utils import image_overlay, openai_client
from utils.openai_client import chamar_ia

# Placeholders substituídos com .replace() (e não .format()): a skill do cliente pode ter
# chaves {} que quebrariam o .format().
SYSTEM_PROMPT = """Você é o Diretor de Arte sênior da Kav (@kav.mkt). Sua função é escrever o
brief de UMA peça do Instagram para o NN Restaurante, pronto para ser enviado direto a um gerador de
imagem por IA de alta qualidade.

DIRETRIZES DE MARCA E KV DO CLIENTE:
__SKILL__

DIREÇÃO DE ARTE E FOTOGRAFIA CULINÁRIA:
- BASE DA CENA: a comida da foto real de referência é o herói da imagem. Os ingredientes, carnes,
  acompanhamentos e porção real devem ser preservados com fidelidade.
- AMBIENTAÇÃO E ELEVAÇÃO DO CENÁRIO: eleve a foto amadora de celular para um padrão editorial
  de fotografia de comida. O prato deve estar ambientado com elegância sobre uma mesa de madeira
  rústica de restaurante, com iluminação quente, natural e apetitosa. Se a foto original tiver
  uma mão segurando uma embalagem plástica ou fundo doméstico/parede com planta, ELIMINE a mão
  e a embalagem plástica e apresente a refeição servida de forma impecável sobre a mesa.
__CONTEXTO_LAYOUT__
- GUIA DE LOGO: um template do MESMO formato/proporção da imagem final, transparente
  exceto onde o logo oficial do cliente está posicionado — reproduza o logo pixel a pixel dali
  (mesmas cores, proporções e detalhes, sem redesenhar ou distorcer) na MESMA ESCALA e na mesma
  faixa vertical mostrada no guia.

REGRAS RÍGIDAS DE DIAGRAMAÇÃO E TIPOGRAFIA (ANTI-AMADORISMO):
1. PROIBIDO CONTORNO BRANCO / GLOW: NUNCA crie letras com sombra branca difusa, contorno branco
   grosso (stroke) ou glow esfumado atrás do texto. Isso parece arte amadora dos anos 2000.
   A tipografia (Playfair Display para headline) deve ser sólida, nítida e sofisticada.
   Para garantir contraste limpo sobre a foto:
   - Posicione o texto em uma área limpa e com respiro da foto, OU
   - Aplique um degradê sutil e natural escurecendo o fundo na região do texto (vignette suave), OU
   - Utilize uma tarja/bloco retangular sólido e elegante em uma das cores oficiais da marca
     (#2A2A2E cinza escuro ou #A31D1D vermelho) com tipografia em off-white quente (#F5EFE6).
2. PROIBIDO SELO EM ELIPSE / CARIMBO REDONDO COM TALHERES: NUNCA desenhe selos circulares, elipses
   com contorno ou carimbos de garfo e faca nos cantos da imagem. Se houver selo do prato,
   desenhe-o como uma etiqueta retangular minimalista, uma fita sutil ou integre o texto de forma
   limpa. Se não houver selo, NÃO adicione nenhum elemento gráfico circular.
3. MARGENS DE SEGURANÇA:
   - Deixe pelo menos __MARGEM__% de respiro livre no topo e no rodapé.
   - Mantenha texto e logo a pelo menos __MARGEM_LATERAL__% de distância de qualquer borda lateral.
   - O logo vai na faixa indicada no guia (__AREA_LOGO__) com área de respiro ao redor.

O brief (em inglês) deve definir, em um parágrafo denso e direto:
- Que a comida da foto real deve ser reproduzida fielmente em seus ingredientes, mas ambientada
  em fotografia gastronômica profissional sobre mesa de madeira rústica, sem mãos ou fundos improvisados;
- A headline exata, com tipografia serifada de alto impacto (Playfair Display), nítida e sem contornos
  brancos esfumados;
- A ausência total de elipses/selos circulares amadores;
- A reprodução precisa do logo a partir do guia oficial na escala e posição indicadas.

Retorne APENAS o brief em texto corrido, em inglês — exceto a headline e o selo, citados
entre aspas exatamente em português. Sem explicações, sem markdown, sem listas.
"""

CONTEXTO_COM_REFERENCIA = (
    "- REFERÊNCIA DE LAYOUT DA MARCA: uma imagem de layout do cliente que define a ESTRUTURA\n"
    "  GRÁFICA a reproduzir (proporção da headline, equilíbrio visual, sobriedade e estilo). Emule\n"
    "  esse alinhamento editorial sofisticado por cima da foto gastronômica ambientada;"
)
CONTEXTO_SEM_REFERENCIA = (
    "- SEM TEMPLATE ESPECÍFICO: siga o KV oficial do cliente com diagramação moderna, clean e\n"
    "  equilibrada, sem poluição visual ou elementos decorativos desnecessários;"
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
        partes.append(
            f'Selo/tag do prato (se renderizar, use formato retangular minimalista, NUNCA elipse/círculo): "{copy["selo_produto"]}"'
        )
    else:
        partes.append("Selo do prato: NENHUM (não desenhe nenhum selo, carimbo ou elipse — foque na foto e na headline)")
    return chamar_ia(system=system, prompt="\n".join(partes), max_tokens=650, temperature=0.7)


def gerar_imagem_foto(brief: str, foto: dict, cliente: dict, referencia: Optional[dict]) -> dict:
    """Gera a imagem do post a partir da foto REAL escolhida (referência obrigatória) +,
    quando houver, a referência de layout do cliente + o guia de logo — tudo na mesma
    chamada de edição, seguindo exatamente o que o cliente pediu: enviar ao gerador de
    imagem a referência de layout selecionada junto com a foto a ser usada."""
    avisos = []
    referencias_imagem = [(
        foto["arquivo"].read_bytes(),
        "the reference photo showing the authentic dish/food served by the restaurant. "
        "Preserve this exact meal, ingredients, and culinary richness faithfully, but ELEVATE the "
        "presentation into professional food photography: stage the dish in an appetizing "
        "restaurant dining setting (on a warm rustic wooden table, natural warm restaurant lighting, "
        "soft background dining room bokeh). If the original photo has awkward hands holding a container "
        "or a distracting domestic wall/plant background, remove the hands and domestic clutter, "
        "and present the delicious food cleanly and appetisingly on the table.",
    )]

    if referencia:
        referencias_imagem.append((
            referencia["arquivo"].read_bytes(),
            "this brand's layout reference template. Emulate its professional graphic design hierarchy: "
            "the refined typography styling, letter spacing, clean alignment, and balance. "
            "Do NOT invent ugly circular stamp graphics or fuzzy white glowing outlines around the text.",
        ))

    logo_arquivo, posicao_logo = _logo(cliente, referencia)
    if logo_arquivo:
        guia_logo = image_overlay.guia_posicao_logo(logo_arquivo, posicao_logo)
        referencias_imagem.append((
            guia_logo,
            "a template the exact same pixel dimensions as the final image, transparent "
            "everywhere except where the client's logo sits — reproduce that logo "
            "pixel-for-pixel, at that exact SCALE, keeping its exact colors, proportions "
            "and details (do not redraw, recolor or distort it). Its vertical position "
            "(top/bottom band) and default side are shown here, but its horizontal "
            "position within that band is only a suggestion: place it wherever that band "
            "is emptiest over the real photo — centered if the middle of the band is "
            "free, kept to this side only if the middle is occupied by the dish or "
            "another important part of the photo. Everywhere else in this template is "
            "transparent guidance only, not part of the visible scene.",
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
            "o tamanho final ainda sai certo (1080x1440, sem cortar nada), mas pode ter "
            "uma distorção leve de proporção nesse post."
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
