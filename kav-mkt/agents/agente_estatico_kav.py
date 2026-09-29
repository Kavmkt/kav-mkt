"""Agente de Criação de Post Estático da Kav (@kav.mkt).

Gera posts estáticos únicos de altíssimo impacto para o feed da própria agência,
com foco em Tráfego Pago Local para PMEs e Marketing Descomplicado.
Alterna dinamicamente entre os 5 arquétipos de layout oficiais da marca com anti-repetição contínua
e aplica o logotipo oficial da Kav por código (Pillow) com nitidez vetorial e transparência perfeita,
eliminando de vez qualquer distorção de IA (letras trocadas, "WAV", etc.) e blocos desnecessários no topo.
"""
from __future__ import annotations

import base64
from pathlib import Path
import random
import re
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
    "inferior-centro": "bottom-center area",
}

ESTILOS_LAYOUT_KAV = [
    {
        "id": "afirmacao_tweet_box",
        "arquivo_referencia": "ref_afirmacao_tweet_box.png",
        "nome": "Card Flutuante / Tweet Box",
        "posicao_logo": "superior-esquerdo",
        "diretriz_cena": (
            "ARQUÉTIPO: CARD FLUTUANTE CENTRALIZADO (Estilo Tweet de Autoridade / Post em Box). "
            "No centro exato do layout, crie um CARD RETANGULAR ELEGANTE em tom azul noturno escuro (#031E34) "
            "com borda fina translúcida ciano/azulada (#123452) e cantos suavemente arredondados. "
            "Dentro deste card flutuante, a headline provocativa é renderizada em tipografia limpa com palavras em Dourado Kav (#EEB730). "
            "Abaixo, dentro do mesmo card ou em um segundo card menor de apoio, a frase explicativa curta. "
            "No rodapé do card, uma chamada elegante: 'Leia a legenda ↘' com a seta em Dourado Solar. "
            "Fundo da imagem: Azul petróleo muito profundo (#00101C) com suave desfoque dark bokeh para dar destaque total ao card central. "
            "PROIBIÇÃO RIGOROSA: PROIBIDO bloco ou caixa de texto no topo ('PERFORMANCE LOCAL'). O topo deve ser limpo! "
            "PROIBIDO mapas 3D ou pins de GPS."
        ),
    },
    {
        "id": "destaque_dourado",
        "arquivo_referencia": "ref_destaque_dourado.png",
        "nome": "Destaque Visual de Contraste Dourado",
        "posicao_logo": "inferior-direito",
        "diretriz_cena": (
            "ARQUÉTIPO: ELEMENTO GRÁFICO CENTRAL DE DESTAQUE DOURADO (Metáfora de Destaque Local). "
            "No centro vertical da arte, renderize uma MATRIZ GEOMÉTRICA MINIMALISTA: uma grade simétrica de pequenos quadrados "
            "ou pontos translúcidos discretos, onde APENAS O ELEMENTO DO CENTRO se destaca brilhando intensamente em Dourado Solar "
            "(#EEB730 com símbolo de estrela '★' e leve aura luminosa), simbolizando a única empresa que brilha na região. "
            "Na metade superior, acima do gráfico, frase reflexiva em tipografia cinza metálica (#94A3B8). "
            "Na base inferior, abaixo do gráfico, conclusão impactante em tipografia branca forte. "
            "Fundo: Azul petróleo nobre (#00101C) com iluminação sutil e focal concentrada no elemento dourado central. "
            "PROIBIÇÃO RIGOROSA: PROIBIDO bloco no topo ('PERFORMANCE LOCAL'). Topo totalmente limpo. "
            "PROIBIDO mapa 3D com radar ou pin de GPS."
        ),
    },
    {
        "id": "impacto_condensado_grid",
        "arquivo_referencia": "ref_impacto_condensado_grid.png",
        "nome": "Impacto Condensado com Grade Técnica",
        "posicao_logo": "superior-direito",
        "diretriz_cena": (
            "ARQUÉTIPO: GRADE TÉCNICA DE DADOS & TIPOGRAFIA FULL-WIDTH MACIÇA. "
            "Fundo: Superfície azul-marinho profunda com uma MICRO-GRADE TÉCNICA GEOMÉTRICA nítida e sutil (linhas vetoriais "
            "milimétricas em azul técnico #072036 formando um grid de blueprint ou coordenadas de performance). "
            "No corpo da peça, a HEADLINE É GIGANTE E MACIÇA (Full-Width Typography em Plus Jakarta Sans 900), "
            "ocupando de 60% a 70% da área útil em letras maiúsculas monumentais brancas e douradas com peso visual brutal. "
            "Na base da imagem, uma barra/tarja horizontal limpa com termos técnicos de performance separados por pontos. "
            "PROIBIÇÃO RIGOROSA: PROIBIDO bloco de texto no topo ('PERFORMANCE LOCAL'). "
            "PROIBIDO mapas 3D ou pins de GPS. O grid deve ser estritamente técnico e bidimensional."
        ),
    },
    {
        "id": "quebra_objecao_card",
        "arquivo_referencia": "ref_quebra_objecao_card.png",
        "nome": "Quebra de Objeção com Card de Solução",
        "posicao_logo": "superior-esquerdo",
        "diretriz_cena": (
            "ARQUÉTIPO: DOIS BLOCOS ASSIMÉTRICOS COM CARD DE BORDA DOURADA. "
            "A arte é dividida verticalmente em dois blocos contrastantes: "
            "Metade superior: Frase afiada atacando um mito de marketing (em tipografia branca limpa de alto impacto). "
            "Metade inferior: Um CARD RETANGULAR DESTACADO com CONTORNO DOURADO KAV (#EEB730, borda nítida de 2px) e fundo escuro (#031E34), "
            "apresentando a virada de chave do negócio. Abaixo do card, botão pill arredondado: '[ Arrasta pra entender → ]'. "
            "Fundo: Gradiente escuro noturno profundo e minimalista. "
            "PROIBIÇÃO RIGOROSA: PROIBIDO bloco no topo ('PERFORMANCE LOCAL'). Topo limpo! PROIBIDO mapas 3D ou pins de GPS."
        ),
    },
    {
        "id": "manifesto_palavra_dourada",
        "arquivo_referencia": "ref_manifesto_palavra_dourada.png",
        "nome": "Manifesto com Palavra Dourada",
        "posicao_logo": "inferior-direito",
        "diretriz_cena": (
            "ARQUÉTIPO: MANIFESTO EDITORIAL MINIMALISTA MONUMENTAL. "
            "A peça é 100% tipográfica, sóbria e imponente. Tipografia monumental em Plus Jakarta Sans Black na metade superior, "
            "com 1 a 2 palavras centrais em Dourado Kav (#EEB730) sublinhadas com traço fino dourado de destaque. "
            "Frase curta de apoio embaixo e botão pill fino arredondado no rodapé inferior contendo estritamente '[ →  Leia a legenda ]'. "
            "Fundo: Azul noturno escuro puro (#001424 com gradiente radial sutil). "
            "PROIBIÇÃO RIGOROSA: PROIBIDO qualquer bloco ou caixa de texto no topo ('PERFORMANCE LOCAL' está proibido!). "
            "PROIBIDO mapas 3D, radares ou pins de localização."
        ),
    },
]

SYSTEM_COPY_KAV = """Você é a Redatora Sênior & Copywriter da Kav (@kav.mkt).
Sua missão é escrever a chamada visual (headline e apoio) e a legenda completa para um post estático de Instagram da Kav.

DIRETRIZES DE MARCA DA KAV:
__SKILL__

PADRÃO DE LEGENDA DA KAV:
__PADRAO_LEGENDA__

REGRAS RÍGIDAS DE COPYWRITING:
1. HEADLINE DA IMAGEM: Curta, magnética, de 2 a 6 palavras. Deve parar imediatamente o scroll do empresário de PME.
   Foque na dor real do negócio local (atrair clientes na região, mensagens no WhatsApp, parar de queimar verba no botão impulsionar).
   NUNCA escreva a palavra "Kav", "Cave" ou o nome da agência na headline da imagem — a chamada deve focar no cliente e no negócio dele.
2. DESTAQUE DOURADO: Indique 1 a 2 palavras da headline que devem receber o Dourado Kav (#EEB730) para quebra de padrão visual.
3. HEADLINE DE APOIO: 1 frase complementar direta que explica a tese sem jargões desnecessários.
4. LEGENDA DO POST:
   - Gancho provocativo na 1ª linha.
   - 2 a 3 parágrafos objetivos explicando o conceito com analogia simples do comércio/serviço.
   - Chamada para ação (CTA) convidando para enviar um direct.
   - Hashtags oficiais da agência.

Responda APENAS com um objeto JSON:
{
  "headline_imagem": "HEADLINE FORTE EM CAIXA ALTA (2 A 6 PALAVRAS)",
  "destaque_dourado": "PALAVRA EM DOURADO",
  "headline_apoio": "Frase de apoio complementar de 1 linha com benefício direto",
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
2. DEFINITIVE COLOR PALETTE:
   - Background: Deep nocturnal navy (#001D32 and #001424) specific to the chosen archetype.
   - Accent & Highlight: Exclusively Kav Gold / Solar Amber (#EEB730). Used for highlighted words in the headline, subtle underline accents, CTA arrows (↘, →).
   - Primary Text: Crisp pure white (#FFFFFF) for absolute contrast and readability on dark screens.
   - Secondary Text: Metallic Slate Gray (#94A3B8).
   - Card containers: Dark nocturnal card (#031E34) with thin subtle stroke borders (#123452).
3. SAFE ZONES & NEGATIVE SPACE:
   - Leave the __AREA_LOGO__ COMPLETELY CLEAR with empty negative space (NO letters, NO text, NO drawing).
   - NO TOP BADGE: DO NOT render any box, pill, tag, or label at the top (NO 'PERFORMANCE LOCAL', NO badges). The top area must be completely clean!
4. STRICT ANTI-HALLUCINATION & ANTI-DUPLICATION MANDATE:
   - DO NOT ATTEMPT TO DRAW OR REPRODUCE ANY LOGO OR BRAND TEXT BY HAND. The official logo is inserted programmatically after generation.
   - ABSOLUTELY DO NOT write 'Kav', 'WAV', 'Cave', or 'Kav Marketing' anywhere on the canvas!
   - ABSOLUTELY NO generic 3D miniature city maps, radar grids, or yellow GPS pins!

LAYOUT ARCHETYPE TO EMULATE: __NOME_ESTILO__
ARCHETYPE COMPOSITION:
__DIRETRIZ_CENA__

Write ONLY the brief in dense English text (with Portuguese quotes for headlines). No markdown, no bullet lists.
"""


def obter_estilo_kav(referencia: Optional[dict] = None) -> dict:
    """Retorna o estilo visual específico da Kav mapeado a partir da referência ou faz fallback balanceado."""
    if referencia and referencia.get("arquivo"):
        nome = referencia["arquivo"].name
        for est in ESTILOS_LAYOUT_KAV:
            if est["arquivo_referencia"] == nome or est["id"] in nome or referencia.get("estilo") == est["id"]:
                return est

    return random.choice(ESTILOS_LAYOUT_KAV)


def _logo_kav(cliente: dict, referencia: Optional[dict] = None) -> tuple[Optional[Path], str]:
    """Localiza o arquivo de logotipo da Kav e determina a posição correta no layout."""
    referencia = referencia or {}
    estilo = obter_estilo_kav(referencia)
    posicao = estilo.get("posicao_logo") or referencia.get("posicao_logo") or cliente.get("config", {}).get("logo_posicao", "inferior-direito")

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
    """Gera os textos do post estático da Kav a partir da pauta sorteada com higienização estrita."""
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
    dados = extrair_json(resposta)

    # Remove qualquer selo antigo ou menção à marca
    dados.pop("selo_produto", None)

    headline = dados.get("headline_imagem", "")
    headline = re.sub(r"\b(KAV|CAVE|WAV)\b", "", headline, flags=re.IGNORECASE).strip()
    dados["headline_imagem"] = headline

    return dados


def gerar_brief_arte_kav(
    copy: dict, pauta: dict, cliente: dict, referencia: Optional[dict]
) -> tuple[str, dict]:
    """Monta o briefing em inglês para a IA de geração de imagem com diretrizes contrastantes por estilo."""
    estilo = obter_estilo_kav(referencia)
    posicao_logo = estilo.get("posicao_logo", "inferior-direito")
    area_logo = AREAS_LOGO.get(posicao_logo, "bottom-right corner")

    system = (
        SYSTEM_DESIGN_KAV.replace("__NOME_ESTILO__", estilo["nome"])
        .replace("__DIRETRIZ_CENA__", estilo["diretriz_cena"])
        .replace("__AREA_LOGO__", area_logo)
    )

    partes = [
        f"Chosen Layout Archetype: {estilo['nome']} (ID: {estilo['id']})",
        f"Topic: {pauta.get('tema')}",
        f'Headline to render in large bold type: "{copy.get("headline_imagem")}"',
        f'Kav Gold (#EEB730) Highlighted Term: "{copy.get("destaque_dourado", "")}"',
        f'Support text to render in smaller type: "{copy.get("headline_apoio")}"',
        f"MANDATORY ARCHETYPE DIRECTIVE: {estilo['diretriz_cena']}",
        (
            "STRICT NEGATIVE SPACE & NO BADGE MANDATE: "
            "1. NO TOP BOX/BADGE: DO NOT render any box or badge at the top (NO 'PERFORMANCE LOCAL', NO badges). "
            f"2. LOGO AREA: Keep the {area_logo} completely empty and uncluttered (negative space). "
            "3. DO NOT attempt to draw the logo or the word 'Kav' by hand — the official vector logo is applied automatically by code!"
        ),
        (
            "STRICT ANTI-CLICHE MANDATE: ABSOLUTELY DO NOT RENDER generic 3D miniature city maps, "
            "radar grids, or glowing yellow GPS location pins! Follow the specific archetype composition."
        ),
    ]

    brief_gerado = chamar_ia(system=system, prompt="\n".join(partes), max_tokens=700, temperature=0.7)
    return brief_gerado, estilo


def gerar_imagem_estatica_kav(
    brief: str, cliente: dict, referencia: Optional[dict], estilo: Optional[dict] = None
) -> dict:
    """Gera a imagem estática 4:5 e aplica o logotipo oficial por código com perfeição pixel a pixel."""
    estilo = estilo or obter_estilo_kav(referencia)
    referencias_imagem = []

    # 1. Adiciona a referência de layout se existir
    if referencia and referencia.get("arquivo") and referencia["arquivo"].exists():
        referencias_imagem.append((
            referencia["arquivo"].read_bytes(),
            (
                f"the brand layout design template for archetype '{estilo['nome']}'. "
                "Emulate this exact graphic design structure, typography hierarchy, and spacing balance. "
                "DO NOT generate generic 3D maps or GPS pins."
            ),
        ))

    logo_arquivo, posicao_logo = _logo_kav(cliente, referencia)

    try:
        imagens = [dados for dados, _ in referencias_imagem]
        descricoes = [desc for _, desc in referencias_imagem]
        prompt = _montar_prompt_final(brief, descricoes, estilo)

        if imagens:
            bruta = openai_client.gerar_imagem_com_referencias(prompt, imagens)
        else:
            bruta = openai_client.gerar_imagem(prompt)

    except Exception as exc:
        raise RuntimeError(f"Falha na geração de imagem da Kav: {exc}") from exc

    if not bruta or not bruta.get("imagem_b64"):
        raise RuntimeError("A API de imagem não retornou nenhuma imagem.")

    # Redimensiona para 1080x1350
    final_bytes = image_overlay.recortar_formato_final(base64.b64decode(bruta["imagem_b64"]))

    # APLICAÇÃO PERFEITA DO LOGO POR CÓDIGO (PILLOW):
    # Garante que o logotipo oficial da Kav fique 100% nítido, sem distorções de IA (evita "WAV", letras borradas ou tortas)
    if logo_arquivo and logo_arquivo.exists():
        final_bytes = image_overlay.aplicar_logo(final_bytes, logo_arquivo, posicao_logo)

    return {
        "imagem_b64": base64.b64encode(final_bytes).decode("ascii"),
        "tamanho": f"{image_overlay.LARGURA_PADRAO}x{image_overlay.ALTURA_PADRAO}",
        "referencia_layout": referencia["arquivo"].name if referencia else None,
        "referencia_logo": logo_arquivo.name if logo_arquivo else None,
        "estilo_layout": estilo["id"],
        "estilo_nome": estilo["nome"],
        "modelo": bruta.get("modelo"),
    }


def _montar_prompt_final(brief: str, descricoes: list, estilo: dict) -> str:
    partes = [
        f"TASK: High-authority static social media post design (1080x1350 vertical 4:5 ratio) for Kav Marketing & Performance in archetype '{estilo['nome']}'.",
        "MANDATORY EXECUTION DIRECTIVES:\n"
        f"- LAYOUT ARCHETYPE: Strictly emulate the visual structure of '{estilo['nome']}'.\n"
        f"- SPECIFIC SCENE REQUIREMENT:\n{estilo['diretriz_cena']}\n"
        "- NO TOP BADGES: DO NOT draw any box or tag at the top saying 'PERFORMANCE LOCAL'. Keep the top clean.\n"
        "- NO DRAWN LOGOS: DO NOT attempt to write or draw 'Kav', 'WAV', or any brand logo by hand. Leave the logo area empty (clean negative space) so the official logo can be placed cleanly.\n"
        "- STRICT PROHIBITIONS: ABSOLUTELY NO generic 3D miniature city maps, radar grids, or yellow GPS pins!\n",
    ]
    for i, desc in enumerate(descricoes):
        partes.append(f"Reference image {i + 1}: {desc}")
    partes.append("Art Direction Brief:\n" + brief)
    return "\n\n".join(partes)
