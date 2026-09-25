"""Agente de Carrossel: escreve o roteiro (texto de cada página) e gera as imagens de um
carrossel de Instagram (1 a 7 páginas) para clientes de conteúdo (config.json com
"tipo": "carrossel"), a partir de uma pauta escolhida pelo Agente de Pauta.

Mesma lógica de uma chamada de imagem por página do Agente de Design (agente_design.py),
mas em série: a partir da página 2, a CAPA já gerada entra como referência extra, para
manter a mesma identidade visual (paleta, tipografia, estilo) do início ao fim do
carrossel — sem isso, cada página sairia com um estilo diferente.
"""
import base64
from typing import Optional

from agents.agente_design import AREAS_LOGO, MARGEM_SEGURANCA_BORDA, _margem_corte_vertical
from utils import image_overlay, openai_client
from utils.openai_client import chamar_ia, extrair_json

SYSTEM_ROTEIRO = """Você é o redator e diretor de arte da Kav (@kav.mkt). Sua função é
escrever o ROTEIRO de um carrossel de Instagram de __PAGINAS__ páginas sobre o tema
abaixo, para o cliente descrito a seguir.

DIRETRIZES DE MARCA DO CLIENTE:
__SKILL__

PADRÃO DE CARROSSEL DO CLIENTE (estrutura, tom, textos fixos e hashtags, quando houver):
__PADRAO__

Regras:
- Página 1 é a capa: precisa parar o scroll (gancho forte, curto).
- A ÚLTIMA página é o fechamento: título e/ou apoio precisam formar uma CHAMADA PRA AÇÃO
  clara e direta (ex: convite pra falar com a Kav, clicar no link da bio), coerente com o
  CTA da legenda — nunca deixe o carrossel "solto" num ponto de desenvolvimento. É a
  única página que leva o logo da marca.
- Cada página tem POUCO texto (é imagem, não postagem de blog): título curto (até ~8
  palavras) + no máximo 1 frase de apoio (ou null se não precisar).
- Não invente dado, número ou fato que não esteja no tema/objetivo/CTA informados —
  isso vale também para frases genéricas de resultado ("resultados reais", "comprovado",
  "transformou tudo") quando não há nenhum número/fato concreto informado: nesse caso,
  fale em termos de processo ("ajudamos a abrir novos canais"), nunca afirme resultado.

Responda APENAS com um objeto JSON, sem texto antes ou depois:
{
  "paginas": [
    {"titulo": "texto curto da página 1 (capa)", "apoio": "frase de apoio opcional ou null"}
  ],
  "legenda": "legenda completa do post, pronta pra colar no Instagram, com gancho e CTA"
}
O array "paginas" deve ter exatamente __PAGINAS__ itens, na ordem em que aparecem no
carrossel.
"""

PADRAO_AUSENTE = "(sem padrão definido — use: capa com gancho, desenvolvimento, fechamento com CTA)"

SYSTEM_IMAGEM = """Você é o Diretor de Arte da Kav (@kav.mkt). Escreva o brief de UMA
página de um carrossel de Instagram, pronto para ser enviado direto a um gerador de
imagem por IA — sem chance de retrabalho, então precisa ser completo e específico.

DIRETRIZES DE MARCA E VISUAL DO CLIENTE:
__SKILL__

Contexto: esta é a página __INDICE__ de __PAGINAS__ de um carrossel sobre "__TEMA__".
__CONTEXTO_REFERENCIA__

DIREÇÃO DE ARTE OBRIGATÓRIA (norte de estilo — interprete livremente, não é um template
fixo a repetir igual em toda página):
- FUNDO: nunca um bloco de cor 100% chapado/plano. Use uma das cores escuras da paleta
  como base e adicione UM tratamento de luz — um glow/gradiente radial numa das cores de
  destaque da marca e/ou linhas finíssimas de grid ou um arco/curva decorativo de baixa
  opacidade. Discreto: decora o fundo, nunca compete com o texto. A posição do glow e o
  alinhamento do texto vêm da seção COMPOSIÇÃO DESTA PÁGINA abaixo — varie de página pra
  página, não repita a mesma composição.
- TIPOGRAFIA: veja a seção FONTES abaixo.
- HIERARQUIA: o título é o elemento dominante da página; a frase de apoio (quando
  houver) é bem menor, mais discreta, pode ter um pequeno bloco/pílula de fundo sólido
  atrás de parte dela para destaque pontual — nunca do mesmo peso visual do título.
- ESPAÇO: espaço negativo generoso. Não preencha a página; deixe respiro real nas
  margens e entre os elementos — poucos elementos bem posicionados, não muitos.
- Isso é DIREÇÃO DE ESTILO, não uma imagem a copiar: não repita layout, texto, marca ou
  proporções exatas de nenhuma referência específica — capture só a linguagem visual
  (tratamento de fundo, tipografia, hierarquia, espaço) descrita acima.

FONTES (use estes estilos tipográficos, sempre):
- Texto base (título principal e frase de apoio): fonte geométrica sans-serif bold/black
  no estilo da família Gotham — traços geométricos, alta legibilidade, peso forte.
- Palavra(s) de destaque dentro do título: fonte serifada itálica elegante (estilo
  Playfair Display/Didot itálico) — é a assinatura visual da Kav, use só na palavra ou
  expressão de maior impacto do título, nunca no título inteiro nem na frase de apoio.

COMPOSIÇÃO DESTA PÁGINA (varia página a página — mantenha a paleta e as fontes acima,
mas mude a diagramação; páginas vizinhas do mesmo carrossel NUNCA podem ter o mesmo
fundo/composição):
__COMPOSICAO__

CORES — regra rígida: use SOMENTE os tons hexadecimais da paleta da Kav listados nas
diretrizes de marca acima. NUNCA use as cores de nenhuma imagem de referência de estilo
enviada junto (mesmo que pareçam parecidas) — se a referência tiver outra cor dominante,
ignore-a e aplique a paleta da Kav no lugar. Garanta contraste forte entre texto e fundo.

MARGENS DE SEGURANÇA — texto e logo não podem invadir estas faixas:
- Topo e rodapé: cerca de __MARGEM__% de cada lado é cortado no ajuste final da imagem —
  trate essa faixa como fora dos limites.
- Todas as bordas (topo, rodapé e laterais): mantenha texto e logo a pelo menos
  __MARGEM_LATERAL__% de distância de qualquer borda.

LOGO: __LOGO_INSTRUCAO__

O brief (em inglês) deve definir, em um parágrafo denso: o fundo/cena gráfica da página
seguindo a direção de arte, as fontes e a composição acima (coerente com as outras
páginas do carrossel em paleta/fontes, mas com diagramação própria), como o texto abaixo
aparece nela (bloco, tipografia, tratamento, qual palavra vai em itálico serifado) e a
instrução de logo acima.

Texto desta página (renderizar exatamente, palavra por palavra, em português):
- Título: "__TITULO__"
__APOIO__

Retorne APENAS o brief em texto corrido, em inglês — exceto os textos citados entre
aspas, exatamente em português. Sem explicações, sem markdown, sem listas.
"""

_DESC_LAYOUT = (
    "a LOOSE mood/style reference from a different, unrelated brand — use it ONLY as "
    "inspiration for the general visual language (typography boldness/contrast, use of "
    "light/gradient accents, spacing, overall energy). Do NOT copy its exact layout, "
    "composition, text or content, and completely IGNORE and never reproduce any logo, "
    "handle, watermark, brand name or credit visible in it — none of that belongs to "
    "this client. Reinterpret the style using this client's own colors, logo and copy."
)
_DESC_ESTILO_CARROSSEL = (
    "the cover page of this same carousel, already generated. Keep the SAME visual "
    "identity (color palette, typography style, background treatment) as this cover — "
    "same series, different content — but vary the composition/layout page to page, "
    "don't repeat it identically."
)
_DESC_LOGO = (
    "a template the exact same pixel dimensions as the final image, transparent everywhere "
    "except where the client's logo sits — reproduce that logo pixel-for-pixel, at that "
    "exact scale and position, without redrawing, recoloring or distorting it."
)

# Roda entre composições bem diferentes (alinhamento, posição do glow e — na 3ª — uma
# inversão de contraste) pra páginas vizinhas nunca saírem parecidas, mesmo mantendo a
# mesma paleta/fontes. Ver COMPOSIÇÃO DESTA PÁGINA em SYSTEM_IMAGEM.
_VARIACOES_COMPOSICAO = [
    "Alinhe o texto à ESQUERDA da página. O glow/gradiente de luz fica no canto "
    "superior esquerdo do fundo. Fundo escuro da paleta em toda a página.",
    "CENTRALIZE o texto horizontalmente na página. O glow/gradiente de luz fica no "
    "canto inferior direito do fundo. Fundo escuro da paleta em toda a página.",
    "Alinhe o texto à DIREITA da página. INVERTA o contraste das outras páginas: um "
    "bloco/painel sólido numa das cores de destaque da marca cobre parte da página, com "
    "o texto sobre esse painel (texto escuro sobre painel claro, ou texto claro sobre "
    "painel de cor forte) — o resto da página mantém o fundo escuro da paleta.",
]


def _composicao_pagina(indice: int) -> str:
    return _VARIACOES_COMPOSICAO[(indice - 1) % len(_VARIACOES_COMPOSICAO)]


def _posicao_logo_centralizada(posicao: str) -> str:
    return "superior-centro" if posicao.startswith("superior") else "inferior-centro"


def gerar_roteiro(pauta: dict, cliente: dict, num_paginas: int) -> dict:
    system = (
        SYSTEM_ROTEIRO.replace("__SKILL__", cliente["skill"])
        .replace("__PADRAO__", cliente.get("carrossel_padrao") or PADRAO_AUSENTE)
        .replace("__PAGINAS__", str(num_paginas))
    )
    prompt = "\n".join(
        f"{rotulo}: {valor}"
        for rotulo, valor in (
            ("Tema", pauta.get("tema")),
            ("Objetivo", pauta.get("objetivo")),
            ("Chamada para ação (CTA)", pauta.get("cta")),
        )
        if valor
    )
    resposta = chamar_ia(system=system, prompt=prompt, max_tokens=1200, temperature=0.9, json_mode=True)
    roteiro = extrair_json(resposta)
    roteiro["paginas"] = _normalizar_paginas(roteiro.get("paginas") or [], num_paginas)
    return roteiro


def _normalizar_paginas(paginas: list, num_paginas: int) -> list:
    """Garante exatamente `num_paginas` itens, mesmo se o modelo errar a contagem —
    corta o excesso ou repete o fechamento, pra nunca travar o fluxo por causa disso."""
    if not paginas:
        return []
    if len(paginas) > num_paginas:
        return paginas[:num_paginas]
    while len(paginas) < num_paginas:
        paginas.append(paginas[-1])
    return paginas


def gerar_imagens_carrossel(
    roteiro: dict, cliente: dict, tema: str, referencia: Optional[dict], etapa=None
) -> list:
    avisar = etapa or (lambda _texto: None)
    paginas = roteiro.get("paginas") or []
    total = len(paginas)
    if not total:
        raise RuntimeError("O roteiro do carrossel não tem páginas.")

    # Só a última página leva o logo (fechamento/CTA) — nas demais ele fica de fora
    # tanto do brief quanto da geração, por pedido explícito do cliente.
    logo_arquivo, posicao_logo = _logo(cliente, referencia)
    posicao_logo_final = _posicao_logo_centralizada(posicao_logo)
    guia_logo_final = (
        image_overlay.guia_posicao_logo(logo_arquivo, posicao_logo_final) if logo_arquivo else None
    )

    slides = []
    imagem_capa_bytes = None
    for indice, pagina in enumerate(paginas, start=1):
        eh_ultima = indice == total
        avisar(f"Gerando página {indice}/{total} do carrossel...")
        brief = _gerar_brief_pagina(
            pagina, cliente, tema, indice, total, referencia, posicao_logo_final, eh_ultima
        )

        referencias_imagem = []
        if referencia:
            referencias_imagem.append((referencia["arquivo"].read_bytes(), _DESC_LAYOUT))
        if imagem_capa_bytes:
            referencias_imagem.append((imagem_capa_bytes, _DESC_ESTILO_CARROSSEL))
        if eh_ultima and guia_logo_final:
            referencias_imagem.append((guia_logo_final, _DESC_LOGO))

        avisos_pagina = []
        bruta = None
        if referencias_imagem:
            try:
                imagens = [dados for dados, _ in referencias_imagem]
                prompt = _prompt_com_referencias(brief, [desc for _, desc in referencias_imagem])
                bruta = openai_client.gerar_imagem_com_referencias(prompt, imagens)
            except Exception as exc:  # cai para geração sem referências, com aviso
                avisos_pagina.append(f"Geração com referências falhou ({exc}); gerei sem elas.")
        if not bruta or not bruta.get("imagem_b64"):
            if bruta is not None:
                avisos_pagina.append("A geração com referências não retornou imagem; gerei sem elas.")
            bruta = openai_client.gerar_imagem(brief)
        if not bruta.get("imagem_b64"):
            raise RuntimeError(f"A API de imagem não retornou nenhuma imagem para a página {indice}.")

        final_bytes = image_overlay.recortar_formato_final(base64.b64decode(bruta["imagem_b64"]))
        if indice == 1:
            imagem_capa_bytes = final_bytes  # âncora de estilo para as próximas páginas

        slides.append({
            "indice": indice,
            "titulo": pagina.get("titulo"),
            "apoio": pagina.get("apoio"),
            "imagem_b64": base64.b64encode(final_bytes).decode("ascii"),
            "tamanho": f"{image_overlay.LARGURA_PADRAO}x{image_overlay.ALTURA_PADRAO}",
            "modelo": bruta.get("modelo"),
            "avisos": avisos_pagina,
        })
    return slides


def _gerar_brief_pagina(
    pagina: dict,
    cliente: dict,
    tema: str,
    indice: int,
    total: int,
    referencia: Optional[dict],
    posicao_logo_final: str,
    eh_ultima: bool,
) -> str:
    partes_contexto = []
    if referencia:
        partes_contexto.append(
            "Há uma imagem de referência entre as enviadas — é só um NORTE de estilo de "
            "uma marca diferente (não copie layout/texto/marca dela, só a linguagem "
            "visual: tipografia, uso de luz/gradiente, espaçamento)."
        )
    if indice > 1:
        partes_contexto.append(
            "A capa já gerada deste mesmo carrossel também está entre as referências — "
            "mantenha dela só a PALETA e as FONTES; a composição/diagramação desta "
            "página é diferente, conforme a seção COMPOSIÇÃO DESTA PÁGINA abaixo; o "
            "conteúdo também é novo."
        )
    if not partes_contexto:
        partes_contexto.append(
            "Não há referência visual ainda (esta é a capa): defina você mesmo o estilo "
            "gráfico, seguindo a direção de arte e o KV do cliente acima — as próximas "
            "páginas vão seguir o que você definir aqui."
        )
    contexto = " ".join(partes_contexto)
    if eh_ultima:
        logo_instrucao = (
            "Esta é a ÚLTIMA página (fechamento/CTA) — a ÚNICA do carrossel que leva o "
            "logo da Kav. Há um guia de logo entre as referências: reproduza-o pixel a "
            "pixel (mesma escala, cores e posição), centralizado horizontalmente, na "
            f"área indicada ({AREAS_LOGO.get(posicao_logo_final, 'bottom-center')}), com "
            "espaço vazio ao redor dele."
        )
    else:
        logo_instrucao = "NÃO inclua o logo da Kav nesta página — só a última página do carrossel leva o logo."
    system = (
        SYSTEM_IMAGEM.replace("__SKILL__", cliente["skill"])
        .replace("__CONTEXTO_REFERENCIA__", contexto)
        .replace("__COMPOSICAO__", _composicao_pagina(indice))
        .replace("__LOGO_INSTRUCAO__", logo_instrucao)
        .replace("__MARGEM__", str(_margem_corte_vertical()))
        .replace("__MARGEM_LATERAL__", str(MARGEM_SEGURANCA_BORDA))
        .replace("__INDICE__", str(indice))
        .replace("__PAGINAS__", str(total))
        .replace("__TEMA__", tema)
        .replace("__TITULO__", pagina.get("titulo") or "")
        .replace("__APOIO__", f'- Apoio: "{pagina["apoio"]}"' if pagina.get("apoio") else "")
    )
    return chamar_ia(system=system, prompt="Escreva o brief desta página.", max_tokens=500, temperature=0.8)


def _prompt_com_referencias(brief: str, descricoes: list) -> str:
    partes = [f"Reference image {i + 1} is {desc}" for i, desc in enumerate(descricoes)]
    partes.append("Page to create:\n" + brief)
    return "\n\n".join(partes)


def _logo(cliente: dict, referencia: Optional[dict]) -> tuple:
    referencia = referencia or {}
    posicao = referencia.get("logo_posicao") or cliente["config"].get("logo_posicao", "inferior-direito")
    versao = referencia.get("logo_versao", "fundo-escuro")
    arquivo = cliente["logos"].get(versao) or cliente["logos"].get("fundo-escuro")
    return arquivo, posicao
