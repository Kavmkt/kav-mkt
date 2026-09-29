"""Agente Carrossel: gera roteiros e briefs de imagens para carrosséis educativos/estratégicos.

Estrutura padrão de um carrossel de alta retenção (5 a 7 páginas):
1. Capa: Gancho forte + pergunta/provocação + promessa clara;
2. Contexto/Dor: O erro comum ou a situação que o cliente enfrenta;
3. Virada/Insight: A mudança de perspectiva ou o dado que surpreende;
4. Aplicação Prática: O "como fazer" passo a passo ou o framework;
5. Fechamento/CTA: Resumo do aprendizado + chamada para ação (salvar, compartilhar, direct).
"""
from __future__ import annotations
import json
import re
from typing import Callable, Optional

from utils import image_overlay, openai_client
from utils.openai_client import chamar_ia, extrair_json

SYSTEM_ROTEIRO = """Você é o Estrategista de Conteúdo Sênior da Kav (@kav.mkt).
Sua missão é criar roteiros de carrossel para Instagram de altíssimo valor percebido e retenção máxima.

DIRETRIZES DA MARCA:
__SKILL__

PADRÃO DE CARROSSEL DO CLIENTE:
__CARROSSEL_PADRAO__

ESTRUTURA OBRIGATÓRIA (exatamente __NUM_PAGINAS__ páginas):
- Página 1 (Capa): Gancho magnético (máx 8 palavras) + subtítulo que gera curiosidade irresistível + indicação visual para arrastar (->);
- Páginas intermediárias: Desenvolvimento progressivo da tese. Frases curtas, ritmo rápido, sem enrolação. Destaque termos-chave;
- Última Página (CTA): Resumo memorável em 1 frase + CTA claro alinhado ao objetivo (ex: 'Salva pra consultar depois', 'Mande um direct').

LEGENDA DO CARROSSEL:
- Gancho na 1ª linha;
- Contexto curto (2 parágrafos);
- CTA claro;
- Hashtags estratégicas.

Responda APENAS com um objeto JSON válido no formato:
{
  "tema": "Tema do carrossel",
  "num_paginas": __NUM_PAGINAS__,
  "paginas": [
    {
      "numero": 1,
      "tipo": "capa",
      "titulo": "HEADLINE PRINCIPAL",
      "subtitulo": "Subtítulo complementar",
      "destaque": "Palavra ou termo a destacar em cor de acento",
      "diretriz_visual": "Instruções específicas para o designer sobre esta página"
    }
  ],
  "legenda": "Texto completo da legenda do post para o feed"
}
"""

SYSTEM_DESIGN_PAGINA = """Você é o Diretor de Arte da Kav (@kav.mkt).
Sua missão é criar o brief de design para UMA página de um carrossel no formato 4:5 vertical (1080x1350).

DIRETRIZES VISUAIS DA MARCA:
__SKILL__

PÁGINA ATUAL: __NUMERO__ de __TOTAL__ (__TIPO__)
CONTEÚDO DA PÁGINA:
- Título: "__TITULO__"
- Subtítulo: "__SUBTITULO__"
- Destaque: "__DESTAQUE__"

REGRAS DE CONTINUIDADE DO CARROSSEL:
- Todas as páginas devem ter a MESMA identidade visual (paleta, fontes, estilo de fundo);
- Mantenha hierarquia clara: o título deve ser o elemento dominante;
- Tipografia: sem serifa, geométrica, moderna, alto contraste;
- Deixe o canto superior ou inferior limpo para a paginação e o logo;
- Formato vertical 4:5 (1080x1350).

Descreva detalhadamente a composição visual desta página em inglês (para o gerador de imagem).
Responda APENAS com o texto do brief em inglês, sem markdown.
"""


def gerar_roteiro(pauta: dict, cliente: dict, num_paginas: int) -> dict:
    """Gera o roteiro completo de um carrossel com base na pauta e diretrizes do cliente."""
    num_paginas = max(3, min(7, num_paginas))
    skill = cliente.get("skill", "")
    carrossel_padrao = cliente.get("carrossel_padrao", "") or "(Padrão Kav: capas magnéticas, páginas diretas com alto valor, CTA final)"

    system = (
        SYSTEM_ROTEIRO.replace("__SKILL__", skill)
        .replace("__CARROSSEL_PADRAO__", carrossel_padrao)
        .replace("__NUM_PAGINAS__", str(num_paginas))
    )

    prompt = (
        f"Pauta selecionada para o carrossel:\n"
        f"- Tema: {pauta.get('tema')}\n"
        f"- Pilar: {pauta.get('pilar', 'Estratégia')}\n"
        f"- Dor ou Desejo: {pauta.get('dor_ou_desejo', '')}\n"
        f"- Analogia/Exemplo: {pauta.get('analogia_pratica', '')}\n"
        f"- Headline sugerida: {pauta.get('headline_sugerida', '')}\n"
        f"- CTA sugerido: {pauta.get('cta', 'Salva este post')}\n\n"
        f"Crie o roteiro completo com exatamente {num_paginas} páginas."
    )

    resposta = chamar_ia(system=system, prompt=prompt, max_tokens=1500, temperature=0.7, json_mode=True)
    dados = extrair_json(resposta)
    dados["paginas"] = _normalizar_paginas(dados.get("paginas", []), num_paginas)
    return dados


def _normalizar_paginas(paginas: list, num_paginas: int) -> list:
    """Garante que a lista de páginas tenha exatamente num_paginas itens bem formatados."""
    resultado = []
    for i in range(num_paginas):
        if i < len(paginas):
            p = paginas[i]
            p["numero"] = i + 1
            p["tipo"] = "capa" if i == 0 else ("cta" if i == num_paginas - 1 else "conteudo")
            resultado.append(p)
        else:
            resultado.append({
                "numero": i + 1,
                "tipo": "cta" if i == num_paginas - 1 else "conteudo",
                "titulo": f"Ponto {i + 1}",
                "subtitulo": "",
                "destaque": "",
                "diretriz_visual": "Manter consistência com as páginas anteriores.",
            })
    return resultado


def gerar_imagens_carrossel(
    roteiro: dict,
    cliente: dict,
    tema: str,
    referencia: Optional[dict] = None,
    etapa: Optional[Callable[[str], None]] = None,
) -> list[dict]:
    """Gera as imagens de cada página do carrossel mantendo consistência visual entre elas."""
    avisar = etapa or (lambda _texto: None)
    paginas = roteiro.get("paginas", [])
    total = len(paginas)
    slides = []

    referencias_imagem = []
    if referencia and referencia.get("arquivo") and referencia["arquivo"].exists():
        referencias_imagem.append((
            referencia["arquivo"].read_bytes(),
            "the brand layout design template. Maintain this visual identity, color scheme, and typography style across all carousel slides.",
        ))

    logo_arquivo, posicao_logo = _logo(cliente, referencia)

    for p in paginas:
        num = p["numero"]
        avisar(f"Gerando página {num}/{total}: {p.get('titulo', '')[:40]}...")

        brief = _gerar_brief_pagina(p, total, cliente, tema)
        try:
            if referencias_imagem:
                imagens = [dados for dados, _ in referencias_imagem]
                descricoes = [desc for _, desc in referencias_imagem]
                prompt = _prompt_com_referencias(brief, descricoes)
                bruta = openai_client.gerar_imagem_com_referencias(prompt, imagens)
            else:
                bruta = openai_client.gerar_imagem(brief)
        except Exception as exc:
            slides.append({
                "numero": num,
                "erro": str(exc),
                "brief": brief,
            })
            continue

        b64 = bruta.get("imagem_b64")
        if b64:
            import base64
            final_bytes = image_overlay.recortar_formato_final(base64.b64decode(b64))
            if logo_arquivo and logo_arquivo.exists():
                final_bytes = image_overlay.aplicar_logo(final_bytes, logo_arquivo, posicao_logo)
            b64_final = base64.b64encode(final_bytes).decode("ascii")
        else:
            b64_final = None

        slide_dado = {
            "numero": num,
            "tipo": p.get("tipo", "conteudo"),
            "titulo": p.get("titulo"),
            "subtitulo": p.get("subtitulo"),
            "brief": brief,
            "imagem_b64": b64_final,
            "imagem_url": bruta.get("imagem_url"),
            "modelo": bruta.get("modelo"),
        }
        slides.append(slide_dado)

        if b64_final and len(referencias_imagem) == 1:
            import base64
            referencias_imagem.append((
                base64.b64decode(b64_final),
                f"Slide 1 of the same carousel. Match its exact visual style, background, fonts, and colors.",
            ))

    return slides


def _gerar_brief_pagina(pagina: dict, total: int, cliente: dict, tema: str) -> str:
    """Gera o brief em inglês para uma página individual do carrossel."""
    skill = cliente.get("skill", "")
    system = (
        SYSTEM_DESIGN_PAGINA.replace("__SKILL__", skill)
        .replace("__NUMERO__", str(pagina.get("numero", 1)))
        .replace("__TOTAL__", str(total))
        .replace("__TIPO__", pagina.get("tipo", "conteudo"))
        .replace("__TITULO__", pagina.get("titulo", ""))
        .replace("__SUBTITULO__", pagina.get("subtitulo", ""))
        .replace("__DESTAQUE__", pagina.get("destaque", ""))
    )

    prompt = (
        f"Topic: {tema}\n"
        f"Page {pagina.get('numero')} of {total} ({pagina.get('tipo', 'conteudo')})\n"
        f"Title: \"{pagina.get('titulo', '')}\"\n"
        f"Subtitle: \"{pagina.get('subtitulo', '')}\"\n"
        f"Highlight term: \"{pagina.get('destaque', '')}\"\n"
        f"Visual notes: {pagina.get('diretriz_visual', '')}\n\n"
        f"Write the art direction brief for this carousel slide."
    )

    return chamar_ia(system=system, prompt=prompt, max_tokens=500, temperature=0.6)


def _prompt_com_referencias(brief: str, descricoes: list) -> str:
    partes = [
        "TASK: High-retention Instagram Carousel slide design (1080x1350 vertical 4:5 ratio).",
        "Maintain strict visual continuity with the reference images (same color palette, fonts, and dark aesthetic).",
    ]
    for i, desc in enumerate(descricoes):
        partes.append(f"Reference image {i + 1}: {desc}")
    partes.append("Art Direction Brief:\n" + brief)
    return "\n\n".join(partes)


def _logo(cliente: dict, referencia: Optional[dict]) -> tuple:
    referencia = referencia or {}
    posicao = referencia.get("logo_posicao") or cliente.get("config", {}).get("logo_posicao", "inferior-direito")
    if isinstance(posicao, str):
        posicao = posicao.replace("_", "-")
    logos = cliente.get("logos", {})
    arquivo = logos.get("principal") or cliente.get("logo")
    return (arquivo, posicao)


# Alias de compatibilidade
gerar_roteiro_carrossel = gerar_roteiro
