"""Agente de Carrossel: escreve o roteiro (texto de cada página) e gera as imagens de um
carrossel de Instagram (1 a 7 páginas) para clientes de conteúdo (config.json com
"tipo": "carrossel"), a partir de uma pauta escolhida pelo Agente de Pauta.

Direção de arte baseada num carrossel real aprovado pelo cliente (25/09/2026): fundo
100% chapado (sem gradiente/glow/grid), alternando claro/escuro ao longo do carrossel
(a maioria das páginas clara, as últimas ~40% escuras, sempre fechando escuro no CTA),
texto sempre alinhado à esquerda, cabeçalho/rodapé pequenos e fixos em toda página
(@kav.mkt / KAV / kavoficial.com.br), e só a última página leva o logo desenhado por
extenso + botão de CTA.
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

ESTRUTURA DE CADA PÁGINA (baseada num carrossel real aprovado pelo cliente):
- "eyebrow": uma linha pequena e curta ANTES do título, só de contexto/transição (ex:
  "Seja honesto.", "Tudo bem, eu também uso todo dia."). Opcional, null se não precisar.
  A CAPA (página 1) NUNCA tem eyebrow — vai direto pro título.
- "titulo": a afirmação principal da página. Curto e direto (até ~10 palavras).
- "apoio": 1 frase complementar, mais leve, logo abaixo do título. Opcional, null se não
  precisar.

Regras:
- Página 1 é a capa: o título é a afirmação MAIS forte e direta de todo o carrossel,
  precisa parar o scroll sozinho.
- A ÚLTIMA página é o fechamento: título e/ou apoio formam uma CHAMADA PRA AÇÃO clara e
  direta (ex: convite pra falar com a Kav, clicar no link da bio), coerente com o CTA da
  legenda — nunca deixe o carrossel "solto" num ponto de desenvolvimento. É a única
  página com botão de CTA e logo.
- Cada página tem POUCO texto (é imagem, não postagem de blog).
- Não invente dado, número ou fato que não esteja no tema/objetivo/CTA informados —
  isso vale também para frases genéricas de resultado ("resultados reais", "comprovado",
  "transformou tudo") quando não há nenhum número/fato concreto informado: nesse caso,
  fale em termos de processo ("ajudamos a abrir novos canais"), nunca afirme resultado.

Responda APENAS com um objeto JSON, sem texto antes ou depois:
{
  "paginas": [
    {"eyebrow": null, "titulo": "texto curto da página 1 (capa)", "apoio": "frase de apoio opcional ou null"}
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

DIRETRIZES DE MARCA DO CLIENTE:
__SKILL__

Contexto: esta é a página __INDICE__ de __PAGINAS__ (papel: __PAPEL__) de um carrossel
sobre "__TEMA__".

DIREÇÃO DE ARTE — ESTILO FIXO, baseado num carrossel real aprovado pelo cliente, siga à
risca (isso NÃO é opcional nem um "norte" solto):
- FUNDO: cor 100% CHAPADA, sólida, uma única cor plana — SEM gradiente, SEM glow, SEM
  grid, SEM textura, SEM nenhum efeito de luz ou decoração no fundo. Cor desta página:
  __FUNDO_DESC__.
- ALINHAMENTO: TODO o texto (eyebrow, título, apoio) alinhado à ESQUERDA, começando na
  mesma margem esquerda — nunca centralizado, nunca à direita.
- HIERARQUIA: eyebrow (se houver) é uma linha pequena e mais fina/apagada, acima do
  título. Título é grande e dominante, o elemento principal da página. Apoio (se houver)
  vem abaixo do título, texto corrido normal, mais claro/discreto — solto na página, sem
  caixa, pílula ou bloco de fundo atrás dele.
- ESPAÇO: espaço negativo generoso — bastante respiro entre eyebrow/título/apoio e nas
  margens. Só os elementos de texto listados abaixo, nada mais no fundo.

FONTES:
- Eyebrow, apoio e a maior parte do título: fonte geométrica sans-serif bold/black no
  estilo da família Gotham.
- UMA palavra ou expressão de maior impacto dentro do título (a de mais peso emocional):
  fonte serifada itálica elegante (estilo Playfair Display/Didot itálico), na cor de
  destaque dourada da marca — é a assinatura visual da Kav; só nessa palavra, nunca no
  título inteiro nem no eyebrow/apoio.

CABEÇALHO E RODAPÉ — fixos e discretos, em TODA página, texto pequeno em caixa alta
(small caps), na cor de texto desta página só que mais apagada/com menos contraste:
- Canto superior esquerdo: "@KAV.MKT"
- Canto superior direito: "KAV"
- Canto inferior esquerdo: "KAV"
- Canto inferior direito: "KAVOFICIAL.COM.BR"

CORES — regra rígida: use SOMENTE os tons hexadecimais da paleta da Kav listados nas
diretrizes de marca acima, na combinação indicada em FUNDO acima. Garanta contraste forte
entre o texto principal e o fundo (o cabeçalho/rodapé podem ter menos contraste, são
discretos de propósito).

MARGENS DE SEGURANÇA — nenhum elemento pode invadir estas faixas:
- Topo e rodapé: cerca de __MARGEM__% de cada lado é cortado no ajuste final da imagem —
  trate essa faixa como fora dos limites (o cabeçalho/rodapé ficam DENTRO da área válida,
  não nessa faixa cortada).
- Todas as bordas: mantenha todo elemento a pelo menos __MARGEM_LATERAL__% de distância
  de qualquer borda.

__PAPEL_INSTRUCAO__

O brief (em inglês) deve definir, em um parágrafo denso: a cor de fundo chapada exata, o
cabeçalho/rodapé fixos, como eyebrow/título/apoio aparecem (sempre alinhados à esquerda,
tipografia, qual palavra do título vai em itálico serifado dourado) e, se for a página de
fechamento, o botão de CTA e a reprodução do logo.

Texto desta página (renderizar exatamente, palavra por palavra, em português):
__EYEBROW__
- Título: "__TITULO__"
__APOIO__

Retorne APENAS o brief em texto corrido, em inglês — exceto os textos citados entre
aspas, exatamente em português. Sem explicações, sem markdown, sem listas.
"""

_DESC_LOGO = (
    "a template the exact same pixel dimensions as the final image, transparent everywhere "
    "except where the client's logo sits — reproduce that logo pixel-for-pixel, at that "
    "exact scale and position, without redrawing, recoloring or distorting it."
)

_FUNDO_CLARO = (
    "flat solid background color #EBEFFA (Kav's light color) — no gradient, no texture. "
    "Main text in dark navy #001D32. The italic accent word inside the headline in the "
    "brand's gold #EEB730."
)
_FUNDO_ESCURO = (
    "flat solid background color #001D32 (Kav's dark color) — no gradient, no texture. "
    "Main text in the light color #EBEFFA or white. The italic accent word inside the "
    "headline in the brand's gold #EEB730."
)


def _fundo_pagina(indice: int, total: int) -> str:
    """Claro na maior parte do carrossel, escuro só no fechamento (~últimos 40% das
    páginas, sempre pelo menos 1) — mesmo ritmo claro→escuro visto na referência real."""
    escuras = max(1, round(total * 0.4))
    return _FUNDO_ESCURO if indice > total - escuras else _FUNDO_CLARO


def _papel_pagina(indice: int, total: int) -> str:
    if indice == 1:
        return "capa"
    if indice == total:
        return "fechamento"
    return "desenvolvimento"


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
    resposta = chamar_ia(system=system, prompt=prompt, max_tokens=1300, temperature=0.9, json_mode=True)
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
    roteiro: dict, cliente: dict, tema: str, referencia: Optional[dict], cta: Optional[str] = None, etapa=None
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
    for indice, pagina in enumerate(paginas, start=1):
        eh_ultima = indice == total
        avisar(f"Gerando página {indice}/{total} do carrossel...")
        brief = _gerar_brief_pagina(
            pagina, cliente, tema, indice, total, posicao_logo_final, eh_ultima, cta, bool(guia_logo_final)
        )

        referencias_imagem = []
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

        slides.append({
            "indice": indice,
            "eyebrow": pagina.get("eyebrow"),
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
    posicao_logo_final: str,
    eh_ultima: bool,
    cta: Optional[str],
    tem_logo: bool,
) -> str:
    papel = _papel_pagina(indice, total)
    if eh_ultima:
        partes_papel = [
            "Esta é a ÚLTIMA página (fechamento) do carrossel. Além do título/apoio, "
            "inclua um BOTÃO de chamada pra ação: um retângulo com cantos bem "
            "arredondados (pílula), preenchido com a cor de destaque dourada da marca, "
            f"com o texto \"{cta or 'Fala com a gente'}\" em negrito, cor escura, "
            "centralizado dentro do botão, e um pequeno ícone de seta ao lado do texto."
        ]
        if tem_logo:
            partes_papel.append(
                "Há um guia de logo entre as referências desta chamada: reproduza-o "
                "pixel a pixel (mesma escala, cores e posição), centralizado "
                f"horizontalmente, na área indicada "
                f"({AREAS_LOGO.get(posicao_logo_final, 'bottom center')}), com espaço "
                "vazio ao redor dele — é a ÚNICA página do carrossel com o logo."
            )
        else:
            partes_papel.append("Não há logo disponível — não desenhe nenhum logo.")
        papel_instrucao = " ".join(partes_papel)
    elif papel == "capa":
        papel_instrucao = (
            "Esta é a CAPA (abertura) do carrossel — sem logo e sem botão de CTA "
            "nesta página. O título é a afirmação mais forte e maior de todo o "
            "carrossel; não há eyebrow nesta página."
        )
    else:
        papel_instrucao = (
            "Esta é uma página de desenvolvimento — sem logo e sem botão de CTA "
            "nesta página."
        )

    system = (
        SYSTEM_IMAGEM.replace("__SKILL__", cliente["skill"])
        .replace("__PAPEL__", papel)
        .replace("__FUNDO_DESC__", _fundo_pagina(indice, total))
        .replace("__PAPEL_INSTRUCAO__", papel_instrucao)
        .replace("__MARGEM__", str(_margem_corte_vertical()))
        .replace("__MARGEM_LATERAL__", str(MARGEM_SEGURANCA_BORDA))
        .replace("__INDICE__", str(indice))
        .replace("__PAGINAS__", str(total))
        .replace("__TEMA__", tema)
        .replace("__TITULO__", pagina.get("titulo") or "")
        .replace("__EYEBROW__", f'- Eyebrow: "{pagina["eyebrow"]}"' if pagina.get("eyebrow") else "")
        .replace("__APOIO__", f'- Apoio: "{pagina["apoio"]}"' if pagina.get("apoio") else "")
    )
    return chamar_ia(system=system, prompt="Escreva o brief desta página.", max_tokens=550, temperature=0.8)


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
