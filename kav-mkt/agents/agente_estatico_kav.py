"""Agente de Criação de Post Estático da Kav (@kav.mkt).

Gera posts estáticos únicos de altíssimo impacto para o feed da própria agência,
com foco em Tráfego Pago Local para PMEs e Marketing Descomplicado.
Usa as referências visuais de clientes/kav/referencias/ com rotação contínua (anti-repetição)
e aplica o crivo do Diretor de Arte (Otávio) com visão computacional.
"""
import base64
from typing import Optional

from utils import image_overlay, openai_client
from utils.openai_client import chamar_ia, extrair_json

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
   - Card/Pill containers: Dark nocturnal card (#031E34) with thin subtle stroke borders (#123452).
3. COMPOSITION & SAFE ZONES:
   - Minimum 6% to 8% breathing room margin from all 4 borders.
   - Prominent official branding: @kav.mkt handle tag or logo reproduced faithfully without distortion.

__CONTEXTO_LAYOUT__

Strict rules:
- No cartoonish 3D figures or generic cliparts. Pure, high-end, editorial B2B dark-mode authority.
- Render the headline, supporting text, and badges exactly as provided, word for word, in Portuguese.

Write ONLY the brief in dense English text (with Portuguese quotes for headlines). No markdown, no bullet lists.
"""


def gerar_copy_kav(pauta: dict, cliente: dict) -> dict:
    """Gera os textos do post estático da Kav a partir da pauta sorteada."""
    skill = cliente.get("skill", "")
    padrao = cliente.get("legenda_padrao", "") or "(Padrão Kav: gancho, explicação prática para PME, CTA no direct, hashtags)"

    system = SYSTEM_COPY_KAV.replace("__SKILL__", skill).replace("__PADRAO_LEGENDA__", padrao)

    prompt = (
        f"Pauta selecionada:\\n"
        f"- Tema: {pauta.get('tema')}\\n"
        f"- Pilar: {pauta.get('pilar', 'Tráfego Pago Local')}\\n"
        f"- Dor/Desejo do Empresário: {pauta.get('dor_ou_desejo', '')}\\n"
        f"- Analogia Prática: {pauta.get('analogia_pratica', '')}\\n"
        f"- Headline sugerida pela pauta: {pauta.get('headline_sugerida', '')}\\n"
        f"- Subtítulo sugerido: {pauta.get('subtitulo_apoio', '')}\\n"
        f"- CTA sugerido: {pauta.get('cta', 'Mande um direct')}\\n"
    )

    resposta = chamar_ia(system=system, prompt=prompt, max_tokens=750, temperature=0.75, json_mode=True)
    return extrair_json(resposta)


def gerar_brief_arte_kav(copy: dict, pauta: dict, cliente: dict, referencia: Optional[dict]) -> str:
    """Monta o briefing em inglês para a IA de geração de imagem."""
    if referencia:
        nome_ref = referencia["arquivo"].name
        contexto = (
            f"Reference image 1 is a brand layout template ('{nome_ref}'). "
            "Faithfully replicate its visual structure, spacing balance, font proportions and composition hierarchy, "
            "adapting it to the new headline and copy provided below."
        )
    else:
        contexto = "Create a custom high-authority static creative adhering strictly to Kav's official Key Visual."

    system = SYSTEM_DESIGN_KAV.replace("__CONTEXTO_LAYOUT__", contexto)

    partes = [
        f"Post Topic: {pauta.get('tema')}",
        f"Category: {pauta.get('pilar', 'Local Performance Marketing')}",
        f'Headline to render in large bold type: "{copy.get("headline_imagem")}"',
        f'Kav Gold (#EEB730) Highlighted Term: "{copy.get("destaque_dourado", "")}"',
        f'Support text to render in smaller type: "{copy.get("headline_apoio")}"',
        f'Institutional Badge: "{copy.get("selo_produto", "KAV · PERFORMANCE")}"',
        "Composition: Vertical 4:5 format with nocturnal navy background, gold highlights and white typography.",
        "Brand Logo: The Kav logo must be reproduced faithfully with clean safe margins.",
    ]

    return chamar_ia(system=system, prompt="\\n".join(partes), max_tokens=650, temperature=0.7)


def gerar_imagem_estatica_kav(brief: str, cliente: dict, referencia: Optional[dict]) -> dict:
    """Gera a imagem estática 4:5 passando a referência de layout sorteada e o logo da Kav."""
    referencias_imagem = []

    # 1. Adiciona a referência de layout se existir
    if referencia and referencia.get("arquivo") and referencia["arquivo"].exists():
        referencias_imagem.append((
            referencia["arquivo"].read_bytes(),
            "the brand layout design reference template. Emulate its professional graphic design hierarchy and typography style."
        ))

    # 2. Adiciona o logotipo oficial da Kav
    logo_arquivo = cliente.get("logo") or (cliente.get("logos", {}).get("fundo-escuro"))
    if logo_arquivo and logo_arquivo.exists():
        guia_logo = image_overlay.guia_posicao_logo(logo_arquivo, "inferior-direito")
        referencias_imagem.append((
            guia_logo,
            "a transparent guide showing the official Kav logo. Reproduce this exact logo in the lower-right corner."
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
        "modelo": bruta.get("modelo"),
    }


def _montar_prompt_final(brief: str, descricoes: list) -> str:
    partes = [f"Reference {i+1} is {desc}" for i, desc in enumerate(descricoes)]
    partes.append("High-Performance Instagram Post to create (Vertical 4:5):\\n" + brief)
    return "\\n\\n".join(partes)
