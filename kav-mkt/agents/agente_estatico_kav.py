"""Agente de Criação de Post Estático da Kav (@kav.mkt).

Gera posts estáticos únicos de altíssimo impacto para o feed da própria agência,
com foco em Tráfego Pago Local para PMEs e Marketing Descomplicado.
Usa as referências visuais de clientes/kav/referencias/ com rotação contínua (anti-repetição)
e envia o logotipo oficial da Kav diretamente como referência de imagem para a IA,
exatamente como é feito no fluxo do N&N Restaurante.
"""
from __future__ import annotations

import base64
from pathlib import Path
from typing import Optional

from utils import image_overlay, openai_client
from utils.openai_client import chamar_ia, extrair_json

AREAS_LOGO = {
    "superior-esquerdo": "top-left corner",
    "superior-direito": "top-right corner",
    "inferior-esquerdo": "bottom-left corner",
    "inferior-direito": "bottom-right corner",
    "topo-centro": "top-center header area",
    "superior-centro": "top-center header area",
}

SYSTEM_COPY_KAV = """Você é a Redatora Sênior & Copywriter da Kav (@kav.mkt).
Sua missão é escrever a chamada visual (headline e apoio) e a legenda completa para um post estático de Instagram da Kav.

DIRETRIZES DE MARCA DA KAV:
__SKILL__

PADRÃO DE LEGENDA DA KAV:
__PADRAO_LEGENDA__

REGRAS DE COPYWRITING:
1. HEADLINE DA IMAGEM: Curta, magnética, de 2 a 6 palavras. Deve parar imediatamente o scroll do empresário de PME.
   Foque na dor real do negócio local (atrair clientes na região, mensagens no WhatsApp, parar de queimar verba no botão impulsionar).
2. DESTAQUE DOURADO: Indique 1 a 2 palavras da headline que devem receber o Dourado Kav (#EEB730) para quebra de padrão visual.
3. HEADLINE DE APOIO: 1 frase complementar direta que explica a tese sem jargões desnecessários.
4. SELO INSTITUCIONAL: "KAV · PERFORMANCE PME" ou "KAV · TRÁFEGO LOCAL" ou "KAV · MKT DESCOMPLICADO".
5. LEGENDA DO POST:
   - Gancho provocativo na 1ª linha.
   - 2 a 3 parágrafos objetivos explicando o conceito com analogia simples do comércio/serviço.
   - Chamada para ação (CTA) convidando para enviar um direct.
   - Hashtags oficiais da agência.

Responda APENAS com um objeto JSON:
{
  "headline_imagem": "HEADLINE FORTE EM CAIXA ALTA (2 A 6 PALAVRAS)",
  "destaque_dourado": "PALAVRA EM DOURADO",
  "headline_apoio": "Frase de apoio complementar de 1 linha com benefício direto",
  "selo_produto": "KAV · TRÁFEGO LOCAL",
  "legenda": "Legenda completa formatada"
}
"""

SYSTEM_DESIGN_KAV = """You are the Senior Art Director of Kav (@kav.mkt), a premier digital performance marketing agency.
Your task is to write a comprehensive, professional graphic design brief for a single static Instagram feed post (Vertical 4:5 ratio, 1080x1350).

DEFINITIVE BRAND IDENTITY & KEY VISUAL:
1. DEFINITIVE TYPOGRAPHY:
   - Primary Font: Plus Jakarta Sans (or Inter).
   - High-contrast geometric neo-grotesque styling with tight, modern letter spacing.
   - Headline Weight: ExtraBold (800) or Black (900), clean and punchy.
   - Subtitle/Card Weight: Medium (500) to Regular (400), perfectly legible.
   - UI elements, badges and pills: SemiBold (600).
2. DEFINITIVE COLOR PALETTE:
   - Background: Deep nocturnal navy (#001D32 and #001424) with subtle radial vignette depth or micro-technical performance grid.
   - Accent & Highlight: Exclusively Kav Gold / Solar Amber (#EEB730). Used for highlighted words in the headline, subtle underline accents, CTA arrows (↘, →), and badge outlines. Never use generic orange or red.
   - Primary Text: Crisp pure white (#FFFFFF) for absolute contrast and readability on dark screens.
   - Secondary Text: Metallic Slate Gray (#94A3B8).
   - Card/Pill containers: Dark nocturnal card (#031E34) with thin subtle stroke borders (#123452).\n3. COMPOSITION & SAFE ZONES:
   - Minimum 6% to 8% breathing room margin from all 4 borders.
4. LOGOTIPO OFICIAL DA MARCA KAV:
   - One of the reference images provided is the official brand logo of Kav Marketing & Performance (@kav.mkt).
   - You MUST reproduce this logo faithfully (exact typography, letterforms, and proportions) integrated cleanly into the design in the designated branding area (__AREA_LOGO__), with strong contrast against the background and safe breathing margins (>= 6% from borders).

__CONTEXTO_LAYOUT__

Strict rules:
- No cartoonish 3D figures or generic cliparts. Pure, high-end, editorial B2B dark-mode authority.
- Render the headline, supporting text, and badges exactly as provided, word for word, in Portuguese.

Write ONLY the brief in dense English text (with Portuguese quotes for headlines). No markdown, no bullet lists.
"""


def _logo_kav(cliente: dict, referencia: Optional[dict] = None) -> tuple[Optional[Path], str]:
    """Localiza o arquivo de logotipo da Kav e determina a posição correta no layout."""
    referencia = referencia or {}
    posicao = (
        referencia.get("posicao_logo")
        or cliente.get("config", {}).get("logo_posicao", "inferior-direito")
    )
    if isinstance(posicao, str):
        posicao = posicao.replace("_", "-")
    else:
        posicao = "inferior-direito"

    versao = referencia.get("logo_versao", "fundo-escuro")
    logos = cliente.get("logos", {})
    arquivo = (
        logos.get(versao)
        or logos.get("fundo-escuro")
        or logos.get("principal")
        or logos.get("fundo-claro")
        or cliente.get("logo")
    )

    if not arquivo and cliente.get("logo_referencias"):
        arquivo = cliente["logo_referencias"][0]

    if not arquivo or not Path(arquivo).exists():
        pasta_cliente = Path(__file__).resolve().parent.parent / "clientes" / cliente.get("slug", "kav")
        candidatos = [
            pasta_cliente / "logo" / "logo_kav.png",
            pasta_cliente / "logo" / "logo.png",
            pasta_cliente / "logo" / "logo-fundo-escuro.png",
            pasta_cliente / "logos" / "logo-fundo-escuro.png",
            pasta_cliente / "logos" / "logo.png",
            pasta_cliente / "logo-fundo-escuro.png",
            pasta_cliente / "logo.png",
            pasta_cliente / "logo-fundo-claro.png",
        ]
        for c in candidatos:
            if c.exists():
                arquivo = c
                break

        if not arquivo or not Path(arquivo).exists():
            for pasta_busca in [pasta_cliente / "logo", pasta_cliente / "logos", pasta_cliente]:
                if pasta_busca.is_dir():
                    for arq in sorted(pasta_busca.glob("*")):
                        if arq.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp", ".svg"} and "logo" in arq.name.lower():
                            arquivo = arq
                            break
                    if arquivo:
                        break

    return (Path(arquivo) if arquivo and Path(arquivo).exists() else None, posicao)


def gerar_copy_kav(pauta: dict, cliente: dict) -> dict:
    """Gera os textos do post estático da Kav a partir da pauta sorteada."""
    skill = cliente.get("skill", "")
    padrao = cliente.get("legenda_padrao", "") or "(Padrão Kav: gancho, explicação prática para PME, CTA no direct, hashtags)"

    system = SYSTEM_COPY_KAV.replace("__SKILL__", skill).replace("__PADRAO_LEGENDA__", padrao)

    prompt = (
        f"Pauta selecionada:\n"
        f"- Tema: {pauta.get('tema')}\n"
        f"- Pilar: {pauta.get('pilar', 'Tráfego Pago Local')}\n"
        f"- Dor/Desejo do Empresário: {pauta.get('dor_ou_desejo', '')}\n"
        f"- Analogia Prática: {pauta.get('analogia_pratica', '')}\n"
        f"- Headline sugerida pela pauta: {pauta.get('headline_sugerida', '')}\n"
        f"- Subtítulo sugerido: {pauta.get('subtitulo_apoio', '')}\n"
        f"- CTA sugerido: {pauta.get('cta', 'Mande um direct')}\n"
    )

    resposta = chamar_ia(system=system, prompt=prompt, max_tokens=750, temperature=0.75, json_mode=True)
    return extrair_json(resposta)


def gerar_brief_arte_kav(copy: dict, pauta: dict, cliente: dict, referencia: Optional[dict]) -> str:
    """Monta o briefing em inglês para a IA de geração de imagem."""
    logo_arquivo, posicao_logo = _logo_kav(cliente, referencia)
    area_logo = AREAS_LOGO.get(posicao_logo, "bottom-right corner")

    if referencia:
        nome_ref = referencia["arquivo"].name
        contexto = (
            f"Reference image 1 is a brand layout template ('{nome_ref}'). "
            "Faithfully replicate its visual structure, spacing balance, font proportions and composition hierarchy, "
            "adapting it to the new headline and copy provided below."
        )
    else:
        contexto = "Create a custom high-authority static creative adhering strictly to Kav's official Key Visual."

    system = SYSTEM_DESIGN_KAV.replace("__CONTEXTO_LAYOUT__", contexto).replace("__AREA_LOGO__", area_logo)

    partes = [
        f"Post Topic: {pauta.get('tema')}",
        f"Category: {pauta.get('pilar', 'Local Performance Marketing')}",
        f'Headline to render in large bold type: "{copy.get("headline_imagem")}"',
        f'Kav Gold (#EEB730) Highlighted Term: "{copy.get("destaque_dourado", "")}"',
        f'Support text to render in smaller type: "{copy.get("headline_apoio")}"',
        f'Institutional Badge: "{copy.get("selo_produto", "KAV · PERFORMANCE")}"',
        "Composition: Vertical 4:5 format with nocturnal navy background, gold highlights and white typography.",
    ]

    if logo_arquivo:
        partes.append(
            "Aplicação rigorosa da marca (seguir a referência do LOGOTIPO OFICIAL DA KAV): "
            f"Reproduzir com MÁXIMA FIDELIDADE o logotipo oficial da Kav Marketing & Performance (@kav.mkt) na posição '{area_logo}', "
            "garantindo contraste evidente sobre o fundo noturno, proporções originais da marca sem distorção e margens de respiro de pelo menos 6% das bordas."
        )
    else:
        partes.append(
            f"Aplicação da marca: Reproduzir a assinatura da marca Kav (@kav.mkt / KAV) na posição '{area_logo}' com respiro de borda."
        )

    return chamar_ia(system=system, prompt="\n".join(partes), max_tokens=650, temperature=0.7)


def gerar_imagem_estatica_kav(brief: str, cliente: dict, referencia: Optional[dict]) -> dict:
    """Gera a imagem estática 4:5 passando a referência de layout e a referência do logo da Kav."""
    referencias_imagem = []

    # 1. Adiciona a referência de layout se existir
    if referencia and referencia.get("arquivo") and referencia["arquivo"].exists():
        referencias_imagem.append((
            referencia["arquivo"].read_bytes(),
            "the brand layout design reference template. Emulate its professional graphic design hierarchy, typography styling, and spacing balance.",
        ))

    # 2. Adiciona o logotipo oficial da Kav diretamente como referência de imagem (mesmo padrão do N&N Restaurante)
    logo_arquivo, posicao_logo = _logo_kav(cliente, referencia)
    area_logo_desc = AREAS_LOGO.get(posicao_logo, "designated branding area")

    if logo_arquivo and logo_arquivo.exists():
        referencias_imagem.append((
            logo_arquivo.read_bytes(),
            "the official BRAND LOGO of Kav Marketing & Performance (@kav.mkt). "
            "You must follow and reproduce this logo EXACTLY (same typography, clean letterforms, wordmark, and colors) into the graphic layout of the post. "
            f"Position it cleanly in the {area_logo_desc} with strong contrast, breathing margins (~6% from borders), and perfect integration into the overall piece, without distorting or redesigning the brand.",
        ))

    try:
        imagens = [dados for dados, _ in referencias_imagem]
        descricoes = [desc for _, desc in referencias_imagem]
        prompt = _montar_prompt_final(brief, descricoes)

        if imagens:
            bruta = openai_client.gerar_imagem_com_referencias(prompt, imagens)
        else:
            bruta = openai_client.gerar_imagem(prompt)

    except Exception as exc:
        raise RuntimeError(f"Falha na geração de imagem da Kav: {exc}") from exc

    if not bruta or not bruta.get("imagem_b64"):
        raise RuntimeError("A API de imagem não retornou nenhuma imagem.")

    final_bytes = image_overlay.recortar_formato_final(base64.b64decode(bruta["imagem_b64"]))

    return {
        "imagem_b64": base64.b64encode(final_bytes).decode("ascii"),
        "tamanho": f"{image_overlay.LARGURA_PADRAO}x{image_overlay.ALTURA_PADRAO}",
        "referencia_layout": referencia["arquivo"].name if referencia else None,
        "referencia_logo": logo_arquivo.name if logo_arquivo else None,
        "modelo": bruta.get("modelo"),
    }


def _montar_prompt_final(brief: str, descricoes: list) -> str:
    partes = [
        "TASK: High-authority static social media post design (1080x1350 vertical 4:5 ratio) for Kav Marketing & Performance (@kav.mkt).",
        "MANDATORY EXECUTION DIRECTIVES:\n"
        "- KEY VISUAL: Deep nocturnal navy (#001D32 and #001424) background with high contrast, sharp Plus Jakarta Sans typography, and Kav Gold (#EEB730) accents.\n"
        "- LOGO FIDELITY: When the official brand logo reference is provided, reproduce the exact official logo into the layout with crisp edges and proper margins.\n",
    ]
    for i, desc in enumerate(descricoes):
        partes.append(f"Reference image {i + 1}: {desc}")
    partes.append("Art Direction Brief:\n" + brief)
    return "\n\n".join(partes)
