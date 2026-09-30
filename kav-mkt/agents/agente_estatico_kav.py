"""Agente de Criação de Post Estático da Kav (@kav.mkt).

Gera posts estáticos únicos de altíssimo impacto para o feed da própria agência,
com foco em Tráfego Pago Local para PMEs e Marketing Descomplicado.
Alterna dinamicamente entre os 5 arquétipos de layout oficiais da marca com anti-repetição contínua:
1. Card Flutuante / Tweet Box (Estilo Tweet de autoridade com avatar e arroba)
2. Comparativo Duplo (Dois blocos: Erro da maioria vs Método Kav)
3. Notificação de Celular / WhatsApp Alert (Simulação realista de mensagem de lead)
4. Dashboard de Métricas & Performance (Grid técnico, métrica gigante e gráfico ascendente)
5. Manifesto Editorial Monumental (100% tipográfico com palavra dourada sublinhada)

Envia o logotipo oficial da Kav como referência de imagem para a IA renderizá-lo organicamente
com proporções e respiro perfeitos, sem sobreposições e sem termos de carrossel.
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
        "instrucao_copy": "\n".join([
            "ESTRUTURA DA COPY PARA ARQUÉTIPO TWEET BOX:",
            "- headline_imagem: Frase afiada e provocativa de abertura (4 a 8 palavras, caixa alta).",
            "- texto_card: Frase reflexiva e direta para o interior do card (2 a 3 linhas curtas).",
            "- destaque_dourado: 1 termo chave para brilhar em dourado.",
            "- cta_card: 'Leia a legenda completa ↘'",
        ]),
        "diretriz_cena": (
            "ARQUÉTIPO VISUAL: CARD FLUTUANTE DE REDE SOCIAL (ESTILO TWEET DE AUTORIDADE / BOX). "
            "No centro da tela, renderize um elegante CARD RETANGULAR FLUTUANTE em tom azul noturno escuro (#031E34) "
            "com cantos suavemente arredondados e borda sutil translúcida (#123452). "
            "Dentro do topo do card: um pequeno avatar circular com ícone dourado 'K', ao lado o nome 'Kav Marketing' "
            "em tipografia branca, seguido do handle '@kav.mkt' em cinza e selo de verificado. "
            "No corpo do card: a tese de autoridade em tipografia geométrica neo-grotesca branca e dourada. "
            "No rodapé interno do card: linha divisória fina e a chamada 'Leia a legenda completa ↘' com seta dourada. "
            "Fora do card: fundo profundo (#001424) com leve desfoque dark bokeh. "
            "PROIBIÇÃO RIGOROSA: PROIBIDO bloco no topo ('PERFORMANCE LOCAL'). Topo limpo! "
            "PROIBIÇÃO RIGOROSA: NUNCA escreva 'Arrasta pra entender' ou termos de carrossel. "
            "PROIBIDO mapas 3D ou pins de GPS."
        ),
    },
    {
        "id": "quebra_objecao_card",
        "arquivo_referencia": "ref_quebra_objecao_card.png",
        "nome": "Comparativo Duplo (Erro vs Método Kav)",
        "posicao_logo": "superior-esquerdo",
        "instrucao_copy": "\n".join([
            "ESTRUTURA DA COPY PARA ARQUÉTIPO COMPARATIVO (DOIS BLOCOS):",
            "- titulo_topo: 'POR QUE SUA EMPRESA NÃO VENDE?' ou pergunta provocativa similar.",
            "- headline_imagem: O grande contraste da tese (ex: 'O ERRO vs A VIRADA').",
            "- bloco_erro: '✕ COMO A MAIORIA FAZ: [Descrever o erro amador, ex: apertar impulsionar e esperar milagre]'",
            "- bloco_solucao: '✓ COM O MÉTODO KAV: [Descrever a estratégia lucrativa, ex: tráfego geolocalizado raio 5km direto no WhatsApp]'",
            "- cta_pill: '→ Leia a legenda'",
        ]),
        "diretriz_cena": (
            "ARQUÉTIPO VISUAL: COMPARATIVO EM DOIS BLOCOS VERTICAIS CONTRASTANTES (ERRO vs MÉTODO KAV). "
            "A arte é estruturada claramente em DOIS CARDS/CAIXAS RETANGULARES empilhados verticalmente: "
            "1. Card Superior (O Erro): Fundo escuro com tom carmesim sutil (#1C0E12) e borda discreta, encabeçado por ícone vermelho '✕', "
            "mostrando o erro amador da concorrência em tipografia branca/cinza. "
            "2. Card Inferior (O Método Kav): Card em destaque premium com contorno Dourado Kav (#EEB730, borda nítida de 3px) "
            "e fundo marinho escuro (#031E34), encabeçado por ícone dourado '✓', destacando a solução da Kav em tipografia branca. "
            "Abaixo dos cards, botão pill fino centralizado: '[ →  Leia a legenda ]'. "
            "PROIBIÇÃO RIGOROSA: NUNCA escreva 'Arrasta pra entender' ou 'Arraste para o lado'. É uma peça estática única de feed! "
            "PROIBIÇÃO RIGOROSA: PROIBIDO bloco no topo ('PERFORMANCE LOCAL'). Topo limpo! "
            "PROIBIDO mapas 3D ou pins de GPS. O layout deve ser inconfundivelmente um comparativo de dois blocos!"
        ),
    },
    {
        "id": "destaque_dourado",
        "arquivo_referencia": "ref_destaque_dourado.png",
        "nome": "Notificação de WhatsApp / Smartphone Alert",
        "posicao_logo": "inferior-direito",
        "instrucao_copy": "\n".join([
            "ESTRUTURA DA COPY PARA ARQUÉTIPO NOTIFICAÇÃO SMARTPHONE:",
            "- frase_topo: 'ISSO É O QUE DEVERIA ESTAR ACONTECENDO NO SEU WHATSAPP:'",
            "- headline_imagem: Simulação de mensagem de cliente real (ex: Novo Cliente: 'Olá! Vi seu anúncio e quero agendar hoje!').",
            "- headline_conclusao: Frase de autoridade da Kav sobre dominar o raio local.",
            "- destaque_dourado: 1 termo da conclusão em Dourado Kav.",
        ]),
        "diretriz_cena": (
            "ARQUÉTIPO VISUAL: NOTIFICAÇÃO REALISTA DE SMARTPHONE (PUSH NOTIFICATION / WHATSAPP ALERT). "
            "No centro da tela, renderize com alta fidelidade visual uma NOTIFICAÇÃO DE MENSAGEM DE CELULAR (estilo push notification): "
            "Um card horizontal elegante com cantos arredondados, fundo escuro translúcido (#031E34) e borda fina. "
            "No topo do card: ícone circular verde com balão de mensagem, o texto 'WHATSAPP BUSINESS' e timestamp 'agora' no canto direito. "
            "Dentro do card: texto destacado simulando a mensagem de um cliente real: 'Novo Cliente Local: Olá! Vi seu anúncio na região e quero agendar...'. "
            "Acima da notificação: frase provocativa em tipografia cinza e branca. "
            "Abaixo da notificação: conclusão de autoridade em Dourado Kav (#EEB730) sobre anúncios no raio do negócio. "
            "PROIBIÇÃO RIGOROSA: NUNCA escreva 'Arrasta pra entender'. "
            "PROIBIÇÃO RIGOROSA: PROIBIDO bloco no topo ('PERFORMANCE LOCAL'). Topo limpo! "
            "PROIBIDO mapas 3D ou pins de GPS. O foco é a notificação realista de mensagem de celular!"
        ),
    },
    {
        "id": "impacto_condensado_grid",
        "arquivo_referencia": "ref_impacto_condensado_grid.png",
        "nome": "Dashboard de Métricas & Performance",
        "posicao_logo": "superior-direito",
        "instrucao_copy": "\n".join([
            "ESTRUTURA DA COPY PARA ARQUÉTIPO DASHBOARD DE MÉTRICAS:",
            "- metrica_destaque: Um número/percentual de alto impacto (ex: '+340%', 'ROAS 5.4X', 'R$ 2,10 / LEAD').",
            "- rotulo_metrica: 'CRESCIMENTO EM VENDAS LOCAIS' ou similar em caixa alta.",
            "- headline_imagem: A conclusão estratégica (ex: 'TRÁFEGO NÃO É GASTO. É MÁQUINA DE CLIENTES.').",
            "- submetricas: Termos técnicos da Kav (ex: 'ROAS 5.4x · Custo por Mensagem: R$ 2,10 · Raio 5km').",
            "- destaque_dourado: A métrica ou palavra em dourado.",
        ]),
        "diretriz_cena": (
            "ARQUÉTIPO VISUAL: DASHBOARD DE ANALYTICS & MÉTRICAS COM GRÁFICO ASCENDENTE. "
            "Fundo: Fundo azul noturno escuro com MICRO-GRADE TÉCNICA VETORIAL sutil (grid de coordenadas técnicas em #072036). "
            "No centro da arte: um CARD DE DASHBOARD ESTILO SAAS/META ADS em #031E34 com borda técnica. "
            "Elemento de destaque: UM NÚMERO MONUMENTAL GIGANTE EM DOURADO KAV (#EEB730) como '+340%' ou '5.4X', acompanhado de um "
            "GRÁFICO LINEAR ASCENDENTE VETORIAL EM DOURADO com pontos de dados brilhantes mostrando curva de crescimento. "
            "Na base do card: indicadores técnicos de performance separados por pontos ('ROAS 5.4x · Custo Lead: R$ 2,10 · Raio: 5 km'). "
            "Abaixo do card: frase de impacto em tipografia branca limpa. "
            "PROIBIÇÃO RIGOROSA: NUNCA escreva 'Arrasta pra entender'. "
            "PROIBIÇÃO RIGOROSA: PROIBIDO bloco no topo ('PERFORMANCE LOCAL'). Topo limpo! "
            "PROIBIDO mapas 3D ou pins de GPS. O foco é analytics, números e gráfico de crescimento!"
        ),
    },
    {
        "id": "manifesto_palavra_dourada",
        "arquivo_referencia": "ref_manifesto_palavra_dourada.png",
        "nome": "Manifesto Editorial Monumental",
        "posicao_logo": "inferior-direito",
        "instrucao_copy": "\n".join([
            "ESTRUTURA DA COPY PARA ARQUÉTIPO MANIFESTO EDITORIAL:",
            "- headline_imagem: Frase monumental de 3 a 5 palavras em caixa alta.",
            "- destaque_dourado: 1 a 2 palavras centrais em Dourado Kav com sublinhado.",
            "- headline_apoio: Frase reflexiva sóbria de 1 a 2 linhas.",
            "- cta_pill: '→ Leia a legenda'",
        ]),
        "diretriz_cena": (
            "ARQUÉTIPO VISUAL: MANIFESTO EDITORIAL MINIMALISTA MONUMENTAL (100% TIPOGRÁFICO). "
            "A arte é estritamente tipográfica, sóbria, sem cards, sem gráficos de dashboard e sem notificações de celular. "
            "Na metade superior e centro: TIPOGRAFIA MONUMENTAL GIGANTE em Plus Jakarta Sans 900 (Black) ocupando a largura com peso brutal. "
            "A palavra-chave central brilha em Dourado Kav (#EEB730) sublinhada por um traço fino elegante de ouro. "
            "Abaixo da headline: frase curta de apoio reflexivo em cinza ardósia (#94A3B8). "
            "No rodapé: botão pill fino arredondado minimalista contendo estritamente '[ →  Leia a legenda ]'. "
            "Fundo: Gradiente sutil azul noturno puro (#001424). "
            "PROIBIÇÃO RIGOROSA: NUNCA escreva 'Arrasta pra entender'. "
            "PROIBIÇÃO RIGOROSA: PROIBIDO caixas no topo ('PERFORMANCE LOCAL'), mapas 3D ou pins de GPS."
        ),
    },
]

SYSTEM_COPY_KAV = """Você é a Redatora Sênior & Copywriter da Kav (@kav.mkt).
Sua missão é escrever o conteúdo visual e a legenda completa para um post estático de Instagram da Kav,
formatado sob medida para o ARQUÉTIPO DE LAYOUT selecionado.

DIRETRIZES DE MARCA DA KAV:
__SKILL__

PADRÃO DE LEGENDA DA KAV:
__PADRAO_LEGENDA__

ARQUÉTIPO DE LAYOUT ESCOLHIDO: __NOME_ESTILO__
__INSTRUCAO_COPY__

REGRAS RÍGIDAS DE COPYWRITING:
0. NUNCA use termos de carrossel como "Arrasta pra entender", "Arraste para o lado" ou setas duplas (>>). Todos os posts da Kav são peças estáticas individuais de feed.
1. HEADLINE DA IMAGEM: Curta, magnética, de 2 a 7 palavras. Deve parar imediatamente o scroll do empresário de PME.
   Foque na dor real do negócio local (atrair clientes na região, mensagens no WhatsApp, parar de queimar verba no botão impulsionar).
   NUNCA escreva a palavra "Kav", "Cave" ou o nome da agência na headline da imagem — a chamada deve focar no cliente e no negócio dele.
2. DESTAQUE DOURADO: Indique 1 a 2 palavras que devem receber o Dourado Kav (#EEB730) para quebra de padrão visual.
3. ADAPTAÇÃO AO FORMATO: Preencha com rigor os campos estruturais do arquétipo solicitado (ex: bloco de erro vs solução, ou texto do card, ou notificação do whatsapp, ou métrica).
4. LEGENDA DO POST:
   - Gancho provocativo na 1ª linha.
   - 2 a 3 parágrafos objetivos explicando o conceito com analogia simples do comércio/serviço.
   - Chamada para ação (CTA) convidando para enviar um direct.
   - Hashtags oficiais da agência.

Responda APENAS com um objeto JSON:
{
  "headline_imagem": "HEADLINE FORTE EM CAIXA ALTA (2 A 7 PALAVRAS)",
  "destaque_dourado": "PALAVRA EM DOURADO",
  "headline_apoio": "Frase de apoio complementar de 1 linha com benefício direto",
  "texto_card": "Texto para dentro do card (se aplicável ao formato)",
  "bloco_erro": "✕ COMO A MAIORIA FAZ: ... (se aplicável ao formato)",
  "bloco_solucao": "✓ COM O MÉTODO KAV: ... (se aplicável ao formato)",
  "notificacao_lead": "Texto de mensagem do lead (se aplicável ao formato)",
  "metrica_destaque": "+340% ou ROAS 5.4X (se aplicável ao formato)",
  "rotulo_metrica": "CRESCIMENTO EM VENDAS LOCAIS (se aplicável ao formato)",
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
3. LOGO INTEGRATION & SAFE ZONES:
   - Faithfully incorporate the official Kav logo from the logo reference image into the __AREA_LOGO__.
   - Ensure generous padding and negative space around the logo so it NEVER touches, collides with, or overlaps any headline, text box, or border.
   - NO TOP BADGE: DO NOT render any box, pill, tag, or label at the top (NO 'PERFORMANCE LOCAL', NO badges). The top area must be completely clean!
4. STRICT PROHIBITIONS:
   - ABSOLUTELY NO CAROUSEL / SWIPE TEXT: NEVER write 'Arrasta pra entender', 'Arraste para o lado', or draw swipe buttons. This is a single static feed post!
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


def gerar_copy_kav(pauta: dict, cliente: dict, estilo: Optional[dict] = None) -> dict:
    """Gera os textos do post estático da Kav adaptados rigorosamente ao arquétipo visual sorteado."""
    estilo = estilo or ESTILOS_LAYOUT_KAV[0]
    skill = cliente.get("skill", "")
    padrao = cliente.get("legenda_padrao", "") or "(Padrão Kav: gancho, explicação prática para PME, CTA no direct, hashtags)"

    system = (
        SYSTEM_COPY_KAV.replace("__SKILL__", skill)
        .replace("__PADRAO_LEGENDA__", padrao)
        .replace("__NOME_ESTILO__", estilo["nome"])
        .replace("__INSTRUCAO_COPY__", estilo.get("instrucao_copy", ""))
    )

    prompt = (
        f"Pauta selecionada:\n"
        f"- Tema: {pauta.get('tema')}\n"
        f"- Pilar: {pauta.get('pilar', 'Tráfego Pago Local')}\n"
        f"- Dor/Desejo do Empresário: {pauta.get('dor_ou_desejo', '')}\n"
        f"- Analogia Prática: {pauta.get('analogia_pratica', '')}\n"
        f"- Headline sugerida pela pauta: {pauta.get('headline_sugerida', '')}\n"
        f"- Subtítulo sugerido: {pauta.get('subtitulo_apoio', '')}\n"
        f"- CTA sugerido: {pauta.get('cta', 'Mande um direct')}\n\n"
        f"ATENÇÃO: Escreva a copy formatada rigorosamente para o arquétipo '{estilo['nome']}'."
    )

    try:
        resposta = chamar_ia(system=system, prompt=prompt, max_tokens=850, temperature=0.75, json_mode=True)
        dados = extrair_json(resposta)
    except Exception:
        dados = {
            "headline_imagem": pauta.get("headline_sugerida", "TRÁFEGO LOCAL DE ALTA PERFORMANCE"),
            "destaque_dourado": "PERFORMANCE",
            "headline_apoio": pauta.get("subtitulo_apoio", "Mais clientes da sua região direto no seu WhatsApp."),
            "legenda": "Legenda padrão da Kav para o post de teste.",
        }

    headline = dados.get("headline_imagem", "")
    headline = re.sub(r"\b(KAV|CAVE|WAV)\b", "", headline, flags=re.IGNORECASE).strip()
    dados["headline_imagem"] = headline
    dados["estilo_layout"] = estilo["id"]
    dados["estilo_nome"] = estilo["nome"]

    return dados


def gerar_brief_arte_kav(
    copy: dict, pauta: dict, cliente: dict, referencia: Optional[dict], estilo: Optional[dict] = None
) -> tuple[str, dict]:
    """Monta o briefing em inglês para a IA de geração de imagem com diretrizes contrastantes por estilo."""
    estilo = estilo or obter_estilo_kav(referencia)
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
        f"MANDATORY ARCHETYPE DIRECTIVE:\n{estilo['diretriz_cena']}",
        f'Main Headline: "{copy.get("headline_imagem")}"',
        f'Kav Gold Highlight Term: "{copy.get("destaque_dourado", "")}"',
    ]

    if copy.get("texto_card"):
        partes.append(f'Card Body Text: "{copy.get("texto_card")}"')
    if copy.get("bloco_erro") and copy.get("bloco_solucao"):
        partes.append(f'Box 1 (Amateur Mistake): "{copy.get("bloco_erro")}"')
        partes.append(f'Box 2 (Kav Solution): "{copy.get("bloco_solucao")}"')
    if copy.get("notificacao_lead"):
        partes.append(f'Phone Push Notification Text: "{copy.get("notificacao_lead")}"')
    if copy.get("metrica_destaque"):
        partes.append(f'Huge Metric Number: "{copy.get("metrica_destaque")}"')
        partes.append(f'Metric Label: "{copy.get("rotulo_metrica", "CRESCIMENTO EM VENDAS LOCAIS")}"')
    if copy.get("headline_apoio"):
        partes.append(f'Support Headline: "{copy.get("headline_apoio")}"')

    partes.extend([
        (
            "STRICT LOGO INTEGRATION MANDATE: "
            f"Reproduce the official Kav logo faithfully into the {area_logo}. "
            "Ensure ample breathing room and safe margins around the logo. "
            "DO NOT allow the logo to collide with or touch any text elements!"
        ),
        (
            "STRICT ANTI-CAROUSEL MANDATE: "
            "NEVER write 'Arrasta pra entender', 'Arraste para o lado' or draw swipe buttons. "
            "This is a single static feed post (1080x1350)!"
        ),
        (
            "STRICT ANTI-CLICHE MANDATE: ABSOLUTELY DO NOT RENDER generic 3D miniature city maps, "
            "radar grids, or glowing yellow GPS location pins! Follow the specific archetype composition."
        ),
    ])

    brief_gerado = chamar_ia(system=system, prompt="\n".join(partes), max_tokens=750, temperature=0.7)
    return brief_gerado, estilo


def gerar_imagem_estatica_kav(
    brief: str, cliente: dict, referencia: Optional[dict], estilo: Optional[dict] = None
) -> dict:
    """Gera a imagem estática 4:5 usando a referência de layout e o logotipo oficial como imagens de referência para a IA."""
    estilo = estilo or obter_estilo_kav(referencia)
    referencias_imagem = []

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
    area_logo = AREAS_LOGO.get(posicao_logo, "header or corner area")

    # Envia o logotipo oficial da Kav como referência de imagem para a IA renderizar perfeitamente
    if logo_arquivo and logo_arquivo.exists():
        referencias_imagem.append((
            logo_arquivo.read_bytes(),
            (
                "the official BRAND LOGO of Kav Marketing & Performance ('KAV'). "
                "You MUST faithfully reproduce this exact logo (precise geometric typography 'KAV') into the layout. "
                f"Position it cleanly in the {area_logo} with generous margins and breathing room. "
                "ABSOLUTE PROHIBITION: The logo MUST NEVER collide with, touch, or overlap any headlines, text boxes, or cards!"
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

    # A imagem já vem com o logo da Kav organicamente integrado pela IA a partir da referência oficial (sem sobreposição cega via Pillow)
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
        f"- SPECIFIC SCENE REQUIREMENT:\n{estilo['diretriz_cena']}\n",
        "- LOGO INTEGRATION: Reproduce the official Kav logo from the logo reference image cleanly in its designated branding zone. Ensure generous margins around the logo so it NEVER touches, collides with, or overlaps any headline, text box, or card.\n",
        "- NO TOP BADGES: DO NOT draw any box or tag at the top saying 'PERFORMANCE LOCAL'. Keep the top clean.\n",
        "- NO CAROUSEL / SWIPE TEXT: ABSOLUTELY DO NOT write 'Arrasta pra entender', 'Arraste para o lado', or draw swipe buttons. This is a single static feed post (1080x1350).\n",
        "- STRICT PROHIBITIONS: ABSOLUTELY NO generic 3D miniature city maps, radar grids, or yellow GPS pins!\n",
    ]
    for i, desc in enumerate(descricoes):
        partes.append(f"Reference image {i + 1}: {desc}")
    partes.append("Art Direction Brief:\n" + brief)
    return "\n\n".join(partes)
