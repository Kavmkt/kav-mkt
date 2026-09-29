"""Agente de Criação de Post Estático da Kav (@kav.mkt).

Gera posts estáticos únicos de altíssimo impacto para o feed da própria agência,
com foco em Tráfego Pago Local para PMEs e Marketing Descomplicado.
Alterna dinamicamente entre os 5 arquétipos de layout oficiais da marca com anti-repetição contínua
e aplica o logotipo oficial da Kav diretamente como referência de imagem única,
proibindo estritamente a repetição da marca e clichês visuais (como mapas 3D com pins de GPS).
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
        "id": "manifesto_palavra_dourada",
        "arquivo_referencia": "ref_manifesto_palavra_dourada.png",
        "nome": "Manifesto com Palavra Dourada",
        "posicao_logo": "inferior-direito",
        "diretriz_cena": (
            "Composição de manifesto editorial de altíssima autoridade. "
            "A peça é 100% tipográfica e minimalista. Tipografia monumental em Plus Jakarta Sans "
            "(peso ExtraBold/Black) dominante na metade superior, com 1 a 2 palavras-chave centrais em Dourado Kav "
            "(#EEB730) sublinhadas com traço fino dourado de destaque. "
            "Linha de apoio explicativa curta e objetiva logo abaixo. "
            "No rodapé inferior centralizado, botão pill fino arredondado contendo estritamente '[ →  Leia a legenda ]'. "
            "Fundo: Azul noturno profundo sólido (#001424 com gradiente radial ultra suave para profundidade). "
            "PROIBIÇÃO RIGOROSA: TERMINANTEMENTE PROIBIDO ilustrações 3D, mapas de GPS, radares, alfinetes/pins de localização "
            "ou desenhos literais. Manter design editorial puro, limpo e escuro."
        ),
    },
    {
        "id": "afirmacao_tweet_box",
        "arquivo_referencia": "ref_afirmacao_tweet_box.png",
        "nome": "Card Flutuante / Tweet Box",
        "posicao_logo": "superior-esquerdo",
        "diretriz_cena": (
            "Composição moderna de 'Card Flutuante' (estilo post/tweet de autoridade). "
            "No centro do layout, um CARD RETANGULAR ELEGANTE em tom azul noturno (#031E34) com borda fina translúcida "
            "(#123452) e cantos suavemente arredondados. "
            "Dentro do card, uma afirmação provocativa e marcante em tipografia limpa, com palavras-chave em Dourado Kav (#EEB730). "
            "Abaixo do primeiro card, um segundo box explicativo menor com a tese prática. "
            "No rodapé do card ou da peça, chamada discreta com seta dourada: 'Leia a legenda ↘'. "
            "Fundo: Fundo azul escuro profundo (#00101C) com desfoque suave de profundidade (bokeh noturno dark mode), "
            "criando contraste e destaque para o card em primeiro plano. "
            "PROIBIÇÃO RIGOROSA: PROIBIDO mapas 3D ou pins de localização. Foco total na estrutura do card flutuante."
        ),
    },
    {
        "id": "impacto_condensado_grid",
        "arquivo_referencia": "ref_impacto_condensado_grid.png",
        "nome": "Impacto Condensado com Grade Técnica",
        "posicao_logo": "superior-direito",
        "diretriz_cena": (
            "Composição técnica de performance e inteligência de dados. "
            "Fundo: Superfície azul-marinho escura com uma MICRO-GRADE TÉCNICA GEOMÉTRICA (linhas vetoriais milimétricas e finas "
            "em azul técnico #072036 formando um grid de coordenadas ou blueprint de dados). "
            "No topo, um badge retangular minimalista com ícone de crescimento (ex: '[ 📈 PERFORMANCE LOCAL ]' ou '[ 🎯 ESCALA PME ]'). "
            "No corpo da peça, HEADLINE MACIÇA EM LARGURA TOTAL (Full-Width Typography em Plus Jakarta Sans 900) em caixa alta imponente, "
            "ocupando quase toda a largura com peso visual marcante. "
            "Na base da imagem, uma linha/tarja elegante com termos técnicos de performance (ex: 'Tráfego Local · Conversão · WhatsApp · ROI'). "
            "PROIBIÇÃO RIGOROSA: PROIBIDO mapas 3D renderizados ou pins de localização. O grid deve ser puramente técnico, sutil e bidimensional."
        ),
    },
    {
        "id": "destaque_dourado",
        "arquivo_referencia": "ref_destaque_dourado.png",
        "nome": "Destaque Visual de Contraste Dourado",
        "posicao_logo": "inferior-direito",
        "diretriz_cena": (
            "Composição gráfica minimalista e conceitual com metáfora de destaque no mercado local. "
            "Na metade superior, frase provocativa em tipografia média cinza ardósia (#94A3B8). "
            "No CENTRO da arte, uma MATRIZ GEOMÉTRICA MINIMALISTA (grade de pequenos blocos ou pontos translúcidos discretos organizados), "
            "na qual APENAS O ELEMENTO CENTRAL É DIFERENTE: um ícone brilhante de estrela ou bloco em DOURADO SOLAR "
            "(#EEB730 com símbolo '★' e leve aura dourada), simbolizando o negócio que se destaca no raio local enquanto todos os outros são comuns. "
            "Na base inferior, conclusão impactante em tipografia branca forte (ex: 'Domine o raio de 5 km. Seja a referência do seu bairro.'). "
            "Fundo: Azul petróleo profundo (#00101C) com iluminação sutil concentrada no ponto dourado central. "
            "PROIBIÇÃO RIGOROSA: PROIBIDO mapa 3D com radar ou pin de GPS. Manter a metáfora geométrica limpa."
        ),
    },
    {
        "id": "quebra_objecao_card",
        "arquivo_referencia": "ref_quebra_objecao_card.png",
        "nome": "Quebra de Objeção com Card de Solução",
        "posicao_logo": "superior-esquerdo",
        "diretriz_cena": (
            "Composição assimétrica em dois blocos verticais contrastantes. "
            "Metade superior: Headline afiada atacando um erro clássico do empresário (ex: 'Você não precisa abaixar o seu preço') "
            "em tipografia branca limpa de alto impacto. "
            "Metade inferior: Um CARD ELEGANTE DESLOCADO com contorno destacado em Dourado Kav (#EEB730, borda de 2px) e fundo azul escuro "
            "(#031E34), apresentando a virada de chave do método da agência. "
            "Abaixo do card, botão pill arredondado com chamada para ação direta: '[ Arrasta pra entender → ]'. "
            "Fundo: Gradiente institucional noturno sóbrio (#001424 a #000E19), sem elementos gráficos concorrentes. "
            "PROIBIÇÃO RIGOROSA: PROIBIDO mapas 3D ou pins de GPS."
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
4. SELO CONCEITUAL: PROIBIDO usar o nome "KAV" ou "CAVE" no selo!
   O logotipo oficial da agência já é aplicado na arte separadamente. O selo deve ser puramente conceitual.
   Exemplos: "PERFORMANCE LOCAL", "TRÁFEGO PARA PMES", "MARKETING DESCOMPLICADO", "ESCALA & VENDAS", "AQUISIÇÃO NO WHATSAPP".
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
  "selo_produto": "PERFORMANCE LOCAL",
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
   - Background: Deep nocturnal navy (#001D32 and #001424) specific to the chosen archetype.
   - Accent & Highlight: Exclusively Kav Gold / Solar Amber (#EEB730). Used for highlighted words in the headline, subtle underline accents, CTA arrows (↘, →), and badge outlines. Never use generic orange or red.
   - Primary Text: Crisp pure white (#FFFFFF) for absolute contrast and readability on dark screens.
   - Secondary Text: Metallic Slate Gray (#94A3B8).
   - Card/Pill containers: Dark nocturnal card (#031E34) with thin subtle stroke borders (#123452).
3. COMPOSITION & SAFE ZONES:
   - Minimum 6% to 8% breathing room margin from all 4 borders.
4. BRAND LOGO INTEGRATION & ANTI-DUPLICATION RULE:
   - The official brand logo in Reference 2 is the ONLY branding mark allowed on the piece.
   - Position it cleanly in the designated branding area (__AREA_LOGO__) with strong contrast and safe breathing margins (>= 6% from borders).
   - STRICT PROHIBITION: DO NOT write the word "Kav", "Cave", or "Kav Marketing" anywhere in the headline, support text, badges, or background. DO NOT duplicate or redraw the logo.

LAYOUT ARCHETYPE TO FOLLOW: __NOME_ESTILO__
ARCHETYPE DIRECTIVE:
__DIRETRIZ_CENA__

Strict rules:
- ABSOLUTELY NO generic 3D miniature city maps, radars, isometric road navigation grids, or yellow GPS pins!
- Render the headline, supporting text, and badges exactly as provided, word for word, in Portuguese.

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

    # Higienização de segurança: remove repetição da marca no selo e na headline
    selo = dados.get("selo_produto", "PERFORMANCE LOCAL")
    selo_limpo = re.sub(r"\bKAV\s*[·•\-\/]?\s*", "", selo, flags=re.IGNORECASE).strip()
    selo_limpo = re.sub(r"\bCAVE\s*[·•\-\/]?\s*", "", selo_limpo, flags=re.IGNORECASE).strip()
    dados["selo_produto"] = selo_limpo or "PERFORMANCE LOCAL"

    headline = dados.get("headline_imagem", "")
    dados["headline_imagem"] = re.sub(r"\bCAVE\b", "KAV", headline, flags=re.IGNORECASE).strip()

    return dados


def gerar_brief_arte_kav(
    copy: dict, pauta: dict, cliente: dict, referencia: Optional[dict]
) -> tuple[str, dict]:
    """Monta o briefing em inglês para a IA de geração de imagem com diretrizes contrastantes por estilo."""
    estilo = obter_estilo_kav(referencia)
    posicao_logo = estilo.get("posicao_logo", "inferior-direito")
    area_logo = AREAS_LOGO.get(posicao_logo, "bottom-right corner")
    logo_arquivo, _ = _logo_kav(cliente, referencia)

    # Garante selo sem 'Kav'
    selo_texto = copy.get("selo_produto", "PERFORMANCE LOCAL")
    selo_limpo = re.sub(r"\bKAV\s*[·•\-\/]?\s*", "", selo_texto, flags=re.IGNORECASE).strip()
    copy["selo_produto"] = selo_limpo or "PERFORMANCE LOCAL"

    system = (
        SYSTEM_DESIGN_KAV.replace("__NOME_ESTILO__", estilo["nome"])
        .replace("__DIRETRIZ_CENA__", estilo["diretriz_cena"])
        .replace("__AREA_LOGO__", area_logo)
    )

    partes = [
        f"Chosen Layout Archetype: {estilo['nome']} (ID: {estilo['id']})",
        f"Topic: {pauta.get('tema')}",
        f"Category: {pauta.get('pilar', 'Local Performance Marketing')}",
        f'Headline to render in large bold type: "{copy.get("headline_imagem")}"',
        f'Kav Gold (#EEB730) Highlighted Term: "{copy.get("destaque_dourado", "")}"',
        f'Support text to render in smaller type: "{copy.get("headline_apoio")}"',
        f'Top/Category Badge (strictly conceptual, NO brand name): "{copy.get("selo_produto")}"',
        f"MANDATORY ARCHETYPE SCENE DIRECTIVE: {estilo['diretriz_cena']}",
        (
            "STRICT ANTI-CLICHE MANDATE: ABSOLUTELY DO NOT RENDER generic 3D miniature city maps, "
            "radar grids, or glowing yellow GPS location pins! Keep the background and layout strictly faithful "
            f"to the chosen archetype '{estilo['nome']}'."
        ),
        (
            "BRAND NAME & LOGO RULES: The official brand logo provided in Reference 2 will appear once in the "
            f"{area_logo}. ZERO other mentions of 'Kav', 'Cave', or 'Kav Marketing' are allowed in any text element."
        ),
    ]

    brief_gerado = chamar_ia(system=system, prompt="\n".join(partes), max_tokens=700, temperature=0.7)
    return brief_gerado, estilo


def gerar_imagem_estatica_kav(
    brief: str, cliente: dict, referencia: Optional[dict], estilo: Optional[dict] = None
) -> dict:
    """Gera a imagem estática 4:5 passando a referência de layout e a referência do logo da Kav."""
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

    # 2. Adiciona o logotipo oficial da Kav diretamente como referência de imagem
    logo_arquivo, _ = _logo_kav(cliente, referencia)
    posicao_logo = estilo.get("posicao_logo", "inferior-direito")
    area_logo_desc = AREAS_LOGO.get(posicao_logo, "designated branding area")

    if logo_arquivo and logo_arquivo.exists():
        referencias_imagem.append((
            logo_arquivo.read_bytes(),
            (
                "the official BRAND LOGO of Kav Marketing & Performance (@kav.mkt). "
                "You must reproduce this exact logo into the graphic layout in the "
                f"{area_logo_desc} with strong contrast, breathing margins (~6% from borders), "
                "and perfect integration. DO NOT repeat the brand name as written text anywhere else on the image."
            ),
        ))

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

    final_bytes = image_overlay.recortar_formato_final(base64.b64decode(bruta["imagem_b64"]))

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
        "- STRICT PROHIBITIONS: ABSOLUTELY NO generic 3D miniature city maps, radar grids, or yellow GPS pins! The background must follow the archetype.\n"
        "- ZERO BRAND REPETITION: The official logo is applied ONCE via Reference 2 in the designated corner. DO NOT write the words 'Kav', 'Cave', or 'Kav Marketing' anywhere else in headlines, badges, or body copy.\n",
    ]
    for i, desc in enumerate(descricoes):
        partes.append(f"Reference image {i + 1}: {desc}")
    partes.append("Art Direction Brief:\n" + brief)
    return "\n\n".join(partes)
