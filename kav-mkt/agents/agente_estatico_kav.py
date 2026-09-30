"""Agente de Criação de Post Estático da Kav (@kav.mkt).

Gera posts estáticos minimalistas e modernos de altíssimo impacto para o feed da agência,
com foco em Tráfego Pago Local para PMEs e Marketing Descomplicado.
Segue com rigor absoluto as diretrizes oficiais da marca:
- ESTRUTURA DE COPY BALANCEADA: Headline imponente em destaque (3 a 6 palavras) +
  Subtítulo curto de contexto (8 a 15 palavras) logo abaixo + Botão pill '[ → Leia a legenda ]'.
  ZERO parágrafos ou blocos longos de texto na imagem!
- REFERÊNCIA 1 COMO DIRECIONAL (ZERO CÓPIA E COLA): A referência visual guia apenas
  a estética, iluminação e qualidade gráfica. A IA transmuta o tema em metáforas visuais
  originais da Kav (xadrez estratégico dourado, gráficos 3D de ROI, balão 3D de WhatsApp, bússola local);
- LOGOTIPO OFICIAL KAV (REFERENCE 2): Reprodução fiel do logotipo geométrico inclinado oficial
  da Kav (marca vetorial autêntica, NUNCA texto digitado em Arial e sem slogans embaixo);
- Alternância entre Temas Escuros (Azul Marinho #001424) e Temas Claros Invertidos (Branco com degradê #FFFFFF para #EBF1F6);
- Tipografia Gotham em Sentence Case contida e elegante;
- Histórico de 120 dias (4 meses) para anti-repetição de temas e layouts.
"""
from __future__ import annotations

import base64
from pathlib import Path
import random
import re
from typing import Optional

from utils import historico, image_overlay, openai_client
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

# Metáforas Visuais Originais da Kav (substituem cópias literais como cadeiras)
METAFORAS_VISUAIS_KAV = [
    {
        "id": "xadrez_estrategico",
        "palavras_chave": ["estratégia", "posicionamento", "preço", "concorrência", "diferença", "improviso"],
        "nome": "Xeque-Mate Estratégico em Xadrez Minimalista",
        "descricao_prompt": (
            "An original modern 3D visual metaphor representing strategic supremacy over local competitors: "
            "A sleek, polished luxury chess board in dark obsidian/marble, where a single magnificent chess King piece "
            "sculpted in mirror-finish Kav Gold (#EEB730) stands triumphant and illuminated by dramatic studio rim lighting, "
            "delivering checkmate against dark minimalist pawns. "
            "CRITICAL: Absolutely NO chairs! This is a powerful, modern chess metaphor for paid traffic strategy."
        ),
    },
    {
        "id": "grafico_roi_3d",
        "palavras_chave": ["resultado", "vendas", "faturamento", "gasto", "dinheiro", "lucro", "métrica", "escala"],
        "nome": "Gráfico 3D Ascendente de Retorno Financeiro & Escala",
        "descricao_prompt": (
            "An original modern 3D financial growth metaphor: "
            "Minimalist geometric 3D bar columns ascending steeply in polished Kav Gold (#EEB730) with refined laser-thin "
            "vector light trajectories shooting upwards, symbolizing exponential return on ad spend (ROAS) and revenue growth. "
            "Crisp, premium architectural design finish with deep cinematic depth. "
            "CRITICAL: Absolutely NO chairs! This is a modern performance financial growth visual."
        ),
    },
    {
        "id": "whatsapp_conversao_3d",
        "palavras_chave": ["atendimento", "rápido", "whatsapp", "mensagem", "cliente", "lead", "contato"],
        "nome": "Balão 3D Iluminado de Conversão no WhatsApp",
        "descricao_prompt": (
            "An original modern 3D customer acquisition metaphor: "
            "A glossy, floating 3D message speech bubble sculpted in radiant Kav Gold (#EEB730) with a subtle glowing "
            "pulse of light, surrounded by soft optical flares representing new hot customer leads arriving instantly on WhatsApp. "
            "Clean, elegant, floating above a dark architectural reflective pedestal. "
            "CRITICAL: Absolutely NO chairs! This represents instant customer conversations that drive sales."
        ),
    },
    {
        "id": "bussola_geofencing",
        "palavras_chave": ["raio", "local", "bairro", "região", "geofencing", "cidade", "alcance"],
        "nome": "Bússola de Precisão Local & Geofencing 3D",
        "descricao_prompt": (
            "An original modern 3D local precision navigation metaphor: "
            "A high-tech minimalist navigation compass instrument crafted in Kav Gold (#EEB730) with a razor-sharp magnetic "
            "needle locked precisely onto the local radius coordinates, symbolizing hyper-targeted 5km local traffic ads. "
            "Sophisticated metallic textures, zero clutter. "
            "CRITICAL: Absolutely NO chairs! This represents precise local market domination."
        ),
    },
]


def curar_metafora_visual_kav(pauta: dict, estilo: dict) -> dict:
    """Seleciona uma metáfora visual 3D original sob medida para o tema da pauta,
    evitando que a IA faça cópia literal dos objetos da referência (ex: cadeiras).
    """
    texto_busca = f"{pauta.get('tema', '')} {pauta.get('pilar', '')} {pauta.get('dor_ou_desejo', '')}".lower()
    for meta in METAFORAS_VISUAIS_KAV:
        if any(kw in texto_busca for kw in meta["palavras_chave"]):
            return meta

    return random.choice(METAFORAS_VISUAIS_KAV)


ESTILOS_LAYOUT_KAV = [
    {
        "id": "manifesto_palavra_dourada",
        "tema": "escuro",
        "arquivo_referencia": "ref_manifesto_palavra_dourada.png",
        "nome": "Manifesto Editorial Focus (Tema Escuro)",
        "posicao_logo": "topo-centro",
        "cor_fundo": "Azul Marinho Noturno Profundo (#001424)",
        "cor_destaque": "Dourado Kav (#EEB730) na palavra central sublinhada",
        "cor_texto": "Branco Puro (#FFFFFF) e Cinza Metálico (#94A3B8)",
        "descricao_layout": "Composição minimalista moderna: logo KAV oficial no topo, headline imponente em destaque, subtítulo curto de contexto logo abaixo em tamanho menor e botão pill 'Leia a legenda' na base.",
        "diretriz_cena": (
            "ARQUÉTIPO VISUAL: MANIFESTO EDITORIAL MINIMALISTA FOCUS (TEMA ESCURO). "
            "A arte é estritamente moderna, limpa e espaçosa (75% de espaço livre/respiro), inspirando-se no layout Focus como direcional. "
            "Topo centro: Logotipo oficial KAV (Reference 2) em proporção 1:1 rigorosa, sem slogan em texto embaixo, com respiro generoso. "
            "Centro da tela: "
            "1. Headline imponente em tipografia Gotham Bold em Sentence Case (3 a 6 palavras), com termo de destaque em Dourado Kav (#EEB730) sublinhado por traço fino elegante. "
            "2. Logo abaixo da headline: Subtítulo curto de contexto (1 a 2 linhas curtas, 8 a 14 palavras) em tipografia Gotham Book/Regular mais leve em cinza metálico (#94A3B8), contextualizando perfeitamente a frase. "
            "Base: Botão pill minimalista e refinado '[ →  Leia a legenda ]'. "
            "Fundo: Azul Marinho Noturno Profundo (#001424) com iluminação sutil no centro. "
            "PROIBIDO PARÁGRAFOS OU TEXTÃO. PROIBIDO COPIAR ELEMENTOS LITERAIS DA REFERÊNCIA."
        ),
    },
    {
        "id": "manifesto_claro",
        "tema": "claro",
        "arquivo_referencia": "ref_manifesto_claro.png",
        "nome": "Manifesto Editorial Focus (Tema Claro Invertido)",
        "posicao_logo": "topo-centro",
        "cor_fundo": "Branco Puro no topo com degradê suave para cinza-azulado super claro na base (#FFFFFF para #EBF1F6)",
        "cor_destaque": "Dourado Kav Solar (#EEB730 / #D99B00) na palavra central sublinhada",
        "cor_texto": "Azul Marinho Noturno Profundo (#001424) e Cinza Slate (#475569)",
        "descricao_layout": "Fundo claro invertido em degradê, logo KAV oficial em azul marinho no topo, headline destacada em Azul Marinho, subtítulo curto de contexto e botão pill na base.",
        "diretriz_cena": (
            "ARQUÉTIPO VISUAL: MANIFESTO EDITORIAL FOCUS EM TEMA CLARO INVERTIDO. "
            "Fundo: Gradiente ultra suave e refinado, iniciando em Branco Puro (#FFFFFF) no topo e transicionando suavemente para Cinza-Azulado Super Claro (#EBF1F6) na base. "
            "Topo centro: Logotipo oficial KAV (Reference 2) em Azul Marinho Noturno Profundo (#001424), perfeitamente nítido e geométrico, sem slogans embaixo, com respiro generoso. "
            "Centro: "
            "1. Headline em tipografia Gotham Bold em Sentence Case em Azul Marinho (#001424), com palavra de destaque em Dourado Kav (#EEB730) com traço sublinhado dourado sutil. "
            "2. Subtítulo curto de contexto (8 a 14 palavras) logo abaixo em cinza slate (#475569) em tamanho menor e elegante. "
            "Base: Botão pill minimalista '[ →  Leia a legenda ]' com borda fina e texto em azul marinho. "
            "PROIBIDO CAIXAS COM PARÁGRAFOS. PROIBIDO COPIAR ELEMENTOS LITERAIS."
        ),
    },
    {
        "id": "metafora_3d_destaque",
        "tema": "escuro",
        "arquivo_referencia": "ref_destaque_dourado.png",
        "nome": "Metáfora Visual 3D Estratégica (Estilo Well.dsg / Objeto Herói)",
        "posicao_logo": "superior-centro",
        "cor_fundo": "Azul Petróleo Escuro (#001424 a #001D32)",
        "cor_destaque": "Dourado Kav Solar (#EEB730) no objeto 3D herói",
        "cor_texto": "Branco Puro (#FFFFFF) e Cinza Slate (#94A3B8)",
        "descricao_layout": "Composição com objeto 3D conceitual no centro (xadrez dourado, gráfico de ROI ou balão WhatsApp), headline no topo com subtítulo e rodapé clean. ZERO cadeiras.",
        "diretriz_cena": (
            "ARQUÉTIPO VISUAL: METÁFORA VISUAL 3D MODERNA DA KAV (ESTILO OBJETO HERÓI DE IMPACTO). "
            "DIRETRIZ CRÍTICA ANTI-CÓPIA: Use a Referência 1 APENAS como direcional de qualidade de luz, profundidade e acabamento premium. "
            "NUNCA DESENHE CADEIRAS! O objeto central 3D herói DEVE ser a metáfora personalizada de performance da Kav (__METAFORA_DESCRICAO__). "
            "No topo: Headline afiada em Gotham Bold em Sentence Case (3 a 5 palavras) com subtítulo curto de apoio (8 a 12 palavras) logo abaixo. "
            "No centro: O objeto 3D escultural em Dourado Kav brilhante (#EEB730) com iluminação dramática de estúdio e reflexos refinados. "
            "Na base: Linha divisória fina com '@kav.mkt' e botão '[ → Leia a legenda ]'. "
            "Fundo: Gradiente rico Azul Marinho Noturno Profundo (#001424). "
            "PROIBIDO CADEIRAS. PROIBIDO PARÁGRAFOS."
        ),
    },
    {
        "id": "metafora_3d_claro",
        "tema": "claro",
        "arquivo_referencia": "ref_destaque_dourado.png",
        "nome": "Metáfora Visual 3D Clean Studio (Tema Claro Invertido)",
        "posicao_logo": "superior-centro",
        "cor_fundo": "Branco Puro no topo com degradê suave para cinza-azulado super claro (#FFFFFF para #EBF1F6)",
        "cor_destaque": "Dourado Kav Solar (#EEB730)",
        "cor_texto": "Azul Marinho Noturno Profundo (#001424) e Cinza Slate (#475569)",
        "descricao_layout": "Fundo claro estúdio clean, objeto 3D herói em Dourado Kav (xadrez ou gráfico), headline em azul marinho com subtítulo e botão pill.",
        "diretriz_cena": (
            "ARQUÉTIPO VISUAL: METÁFORA 3D CLEAN STUDIO EM TEMA CLARO INVERTIDO. "
            "Fundo: Gradiente estúdio fotográfico clean, partindo de Branco Puro (#FFFFFF) no topo para Cinza-Azulado Super Claro (#EBF1F6) na base com sombra de contato suave. "
            "Topo: Logotipo oficial KAV em Azul Marinho Noturno (#001424), seguido de headline destacada em Gotham Bold e subtítulo curto de contexto em cinza slate (#475569). "
            "Centro: O objeto 3D herói da Kav (__METAFORA_DESCRICAO__) em acabamento Dourado Kav reluzente (#EEB730). "
            "CRÍTICO: NUNCA desenhe cadeiras! Apenas a metáfora original de negócios. "
            "Base: Botão pill fino '[ → Leia a legenda ]'. "
            "PROIBIDO CAIXA ALTA. PROIBIDO TEXTÃO."
        ),
    },
    {
        "id": "afirmacao_tweet_box",
        "tema": "escuro",
        "arquivo_referencia": "ref_afirmacao_tweet_box.png",
        "nome": "Tweet Box de Autoridade (Estilo Samuel Reis - Tema Escuro)",
        "posicao_logo": "superior-esquerdo",
        "cor_fundo": "Azul Marinho Noturno Profundo (#001424)",
        "cor_destaque": "Dourado Kav Solar (#EEB730)",
        "cor_texto": "Branco Puro (#FFFFFF) e Cinza Slate (#94A3B8)",
        "descricao_layout": "Card retangular flutuante escuro (#031E34) no centro com perfil @kav.mkt, headline tese em destaque, subtítulo curto de contexto e chamada sutil. Sem textão.",
        "diretriz_cena": (
            "ARQUÉTIPO VISUAL: CARD FLUTUANTE DE REDE SOCIAL (ESTILO SAMUEL REIS - TEMA ESCURO). "
            "No centro da tela, renderize um elegante CARD RETANGULAR FLUTUANTE em tom azul noturno escuro (#031E34) "
            "com cantos suavemente arredondados e borda sutil translúcida (#123452). "
            "Topo do card: badge de perfil com pequeno avatar circular com 'K' dourado e handle '@kav.mkt'. "
            "Corpo do card: Headline tese de autoridade em tipografia Gotham Bold em Sentence Case, seguida logo abaixo por subtítulo curto de contexto (8 a 14 palavras). "
            "Rodapé interno: chamada sutil 'Leia a legenda completa ↘' em Dourado Kav (#EEB730). "
            "Fundo: Azul Marinho Noturno Profundo (#001424). "
            "PROIBIDO PARÁGRAFOS OU HISTÓRIAS LONGAS NA IMAGEM."
        ),
    },
    {
        "id": "quebra_objecao_claro",
        "tema": "claro",
        "arquivo_referencia": "ref_quebra_objecao_claro.png",
        "nome": "Quebra de Objeção / Tensão de Valor (Tema Claro Invertido)",
        "posicao_logo": "superior-esquerdo",
        "cor_fundo": "Branco com degradê suave para cinza-azulado super claro (#FFFFFF para #EBF1F6)",
        "cor_destaque": "Dourado Kav (#EEB730 / #D99B00) no card da virada de chave",
        "cor_texto": "Azul Marinho Noturno Profundo (#001424) e Cinza Slate (#475569)",
        "descricao_layout": "Fundo claro em degradê, headline afiada em Gotham Sentence case em Azul Marinho, subtítulo curto de virada de chave e botão pill.",
        "diretriz_cena": (
            "ARQUÉTIPO VISUAL: QUEBRA DE OBJEÇÃO EM TEMA CLARO INVERTIDO. "
            "Fundo: Branco Puro (#FFFFFF) no topo com degradê suave para Cinza-Azulado Super Claro (#EBF1F6) na base. "
            "Topo: Badge sutil de perfil com avatar e identificação '@kav.mkt'. "
            "Corpo superior: Grande headline afiada em tipografia Gotham Bold em Sentence Case em Azul Marinho Noturno (#001424). "
            "Corpo inferior: Subtítulo curto de virada de chave em card fino com borda em Dourado Kav (#EEB730). "
            "Abaixo do card: botão pill fino '[ →  Leia a legenda ]'. "
            "PROIBIDO CAIXA ALTA. PROIBIDO PARÁGRAFOS LONGOS."
        ),
    },
]

SYSTEM_COPY_KAV = """Você é a Redatora Sênior & Copywriter da Kav (@kav.mkt).
Sua missão é escrever a HIERARQUIA DE COPY COMPLETA para o post de Instagram da Kav:
1. Para a IMAGEM: A dupla perfeita de autoridade:
   - headline_imagem: Headline principal em destaque imponente (3 a 6 palavras em Gotham Sentence Case, ex: 'Atendimento rápido gera mais vendas.', 'Você não precisa abaixar o seu preço.').
   - destaque_dourado: 1 a 2 palavras centrais da headline para receber o Dourado Kav (#EEB730) com traço sublinhado.
   - subtitulo_imagem: Frase curta de apoio e contexto (1 a 2 linhas, exatamente entre 8 e 14 palavras) posicionada logo abaixo da headline, dando o contexto e a justificativa da tese de forma afiada. Ex: 'Demorar para responder no WhatsApp é entregar o cliente direto para o concorrente da rua de trás.'
2. Para a LEGENDA (CAPTION):
   - É AQUI na legenda que você desenvolve todo o conteúdo rico, a história, analogias práticas (ex: analogia do garçom no restaurante), explicação técnica para o empresário, CTA para direct e hashtags.

DIRETRIZES DE MARCA DA KAV:
__SKILL__

PADRÃO DE LEGENDA DA KAV:
__PADRAO_LEGENDA__

ARQUÉTIPO DE LAYOUT ESCOLHIDO: __NOME_ESTILO__
TEMA DO LAYOUT: __TEMA_LAYOUT__

__BACKUP_HISTORICO__

REGRAS RÍGIDAS DE COPYWRITING:
0. OBRIGATÓRIO: Sentence Case em tudo (primeira letra maiúscula e minúsculas naturais). PROIBIDO ALL CAPS!
1. A IMAGEM NÃO PODE TER PARÁGRAFO OU TEXTÃO: Apenas a Headline (3-6 palavras) + Subtítulo curto (8-14 palavras) + CTA '[ → Leia a legenda ]'.
2. NUNCA use termos de carrossel ('Arrasta pra entender', 'Arraste para o lado'). É post estático individual!

Responda APENAS com um objeto JSON:
{
  "headline_imagem": "Headline afiada em Gotham Sentence Case (3 a 6 palavras)",
  "destaque_dourado": "Palavra central em dourado",
  "subtitulo_imagem": "Frase curta de apoio e contexto (8 a 14 palavras)",
  "descricao_layout": "Resumo em 1 linha da estrutura visual",
  "legenda": "Legenda completa formatada com a explicação rica, parágrafos, analogia, CTA e hashtags"
}
"""

SYSTEM_DESIGN_KAV = """You are the Senior Art Director of Kav (@kav.mkt), a premier digital performance marketing agency.
Your task is to write a comprehensive, professional graphic design brief for a single static Instagram feed post (Vertical 4:5 ratio, 1080x1350).

DEFINITIVE BRAND IDENTITY & KEY VISUAL RULES:

1. REFERENCE 1 IS PURELY DIRECTIONAL (STRICT ANTI-COPYCAT MANDATE):
   - Reference image 1 is attached EXCLUSIVELY as a graphic design direction for composition balance, lighting sophistication, refined spacing, and modern design quality.
   - YOU ARE STRICTLY PROHIBITED FROM COPYING THE LITERAL OBJECTS IN REFERENCE 1! (NEVER DRAW CHAIRS OR DUPLICATE LITERAL PROPS FROM REFERENCE 1!).
   - Instead, the scene must be translated into this ORIGINAL 3D visual metaphor representing Kav Performance:
     >> __METAFORA_DESCRICAO__ <<

2. OFFICIAL KAV LOGO MARK (REFERENCE 2):
   - Reference image 2 is the OFFICIAL KAV BRAND LOGOTYPE (the custom geometric slanted 'KAV' vector symbol with custom angular letterforms).
   - You MUST replicate this EXACT geometric logo mark as shown in Reference 2 in the header area.
   - ABSOLUTE PROHIBITION ON PLAIN TEXT / SLOGANS:
     * DO NOT type the word 'KAV' in standard generic font (no Arial/Helvetica/Impact)!
     * DO NOT write 'Marketing & Performance' or add plain slogans underneath!
     * Use ONLY the official geometric mark 'KAV' with its exact cut stems and angles from Reference 2.
   - Position this exact geometric logo mark cleanly in the __AREA_LOGO__ with at least 70px breathing room and aspect ratio lock (ZERO DISTORTION).

3. COPY HIERARCHY ON CANVAS (PROMINENT HEADLINE + CONTEXTUAL SHORT SUBTITLE):
   - Render ONLY two text blocks on the canvas:
     a) Prominent Headline in Gotham Bold, Sentence Case ('{headline}').
     b) Short Contextual Subtitle directly underneath in smaller, refined Gotham Book/Regular ('{subtitulo}').
     c) Minimal bottom CTA pill button '[ → Leia a legenda ]'.
   - ABSOLUTELY NO PARAGRAPHS, ESSAYS, OR DENSE TEXT BOXES ON THE CANVAS!

4. COLOR PALETTE:
   - Current Target Theme: __TEMA_LAYOUT__
   - If DARK THEME: Deep nocturnal navy background (#001424). PROHIBITED PURE BLACK (#000000). Highlights in Kav Gold (#EEB730). Primary text in Pure White (#FFFFFF), subtitle in Slate Gray (#94A3B8).
   - If LIGHT INVERTED THEME: Pure White (#FFFFFF) at the top with a subtle, ultra-soft gradient transitioning gently into a very faint bluish-gray (#EBF1F6) at the bottom. Primary text in Deep Nocturnal Navy (#001424). Subtitle in Slate Gray (#475569). Highlights in Kav Gold (#EEB730 / #D99B00) with thin gold underline.

5. STRICT PROHIBITIONS:
   - NO CAROUSEL / SWIPE TEXT: ABSOLUTELY NEVER write 'Arrasta pra entender', 'Arraste para o lado', or draw swipe buttons.
   - NO TOP BADGE: DO NOT render any box or pill at the top saying 'PERFORMANCE LOCAL'. Keep the top clean.

LAYOUT ARCHETYPE TO EMULATE: __NOME_ESTILO__
ARCHETYPE COMPOSITION:
__DIRETRIZ_CENA__

__BACKUP_HISTORICO__

Write ONLY the brief in dense English text (with Portuguese quotes for headlines and subtitles). No markdown, no bullet lists.
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
    """Localiza o arquivo de logotipo OFICIAL autêntico da Kav (o arquivo com a marca geométrica real)."""
    referencia = referencia or {}
    estilo = obter_estilo_kav(referencia)
    posicao = estilo.get("posicao_logo") or referencia.get("posicao_logo") or cliente.get("config", {}).get("logo_posicao", "superior-centro")

    if isinstance(posicao, str):
        posicao = posicao.replace("_", "-")
    else:
        posicao = "superior-centro"

    tema = estilo.get("tema", "escuro")
    pasta_cliente = Path(__file__).resolve().parent.parent / "clientes" / cliente.get("slug", "kav")

    # Prioriza SEMPRE os arquivos oficiais autênticos na raiz da pasta do cliente (117KB e 188KB)
    if tema == "claro":
        candidatos = [
            pasta_cliente / "logo-fundo-claro.png",
            pasta_cliente / "logos" / "logo-fundo-claro.png",
            pasta_cliente / "logo" / "logo-fundo-claro.png",
        ]
    else:
        candidatos = [
            pasta_cliente / "logo-fundo-escuro.png",
            pasta_cliente / "logos" / "logo-fundo-escuro.png",
            pasta_cliente / "logo" / "logo-fundo-escuro.png",
        ]

    arquivo = None
    # Prioriza arquivos oficiais com tamanho real (> 25KB) para nunca pegar logos falsos gerados por script
    for c in candidatos:
        if c.exists() and c.stat().st_size > 25000:
            arquivo = c
            break

    if not arquivo:
        for c in candidatos:
            if c.exists():
                arquivo = c
                break

    return (Path(arquivo) if arquivo and Path(arquivo).exists() else None, posicao)


def gerar_copy_kav(pauta: dict, cliente: dict, estilo: Optional[dict] = None) -> dict:
    """Gera os textos do post da Kav: Headline em destaque + Subtítulo curto de contexto para a arte, e Legenda completa."""
    estilo = estilo or ESTILOS_LAYOUT_KAV[0]
    skill = cliente.get("skill", "")
    padrao = cliente.get("legenda_padrao", "") or "(Padrão Kav: gancho, explicação prática para PME, CTA no direct, hashtags)"
    backup_historico = historico.obter_backup_historico_layouts("kav", limite=5)

    system = (
        SYSTEM_COPY_KAV.replace("__SKILL__", skill)
        .replace("__PADRAO_LEGENDA__", padrao)
        .replace("__NOME_ESTILO__", estilo["nome"])
        .replace("__TEMA_LAYOUT__", estilo.get("tema", "escuro").upper())
        .replace("__BACKUP_HISTORICO__", backup_historico)
    )

    prompt = (
        f"""Pauta selecionada:
- Tema: {pauta.get('tema')}
- Pilar: {pauta.get('pilar', 'Tráfego Pago Local')}
- Dor/Desejo do Empresário: {pauta.get('dor_ou_desejo', '')}
- Analogia Prática: {pauta.get('analogia_pratica', '')}
- Headline sugerida pela pauta: {pauta.get('headline_sugerida', '')}

ATENÇÃO RIGOROSA:
1. Para a IMAGEM:
   - headline_imagem: Frase de alto impacto (3 a 6 palavras em Sentence Case).
   - destaque_dourado: 1 termo da headline em Dourado Kav (#EEB730).
   - subtitulo_imagem: UMA frase curta de apoio e contexto (exatamente entre 8 e 14 palavras) logo abaixo da headline.
   - NUNCA escreva parágrafos longos na imagem!
2. Para a LEGENDA: Desenvolva o texto completo e rico da postagem (com gancho, analogia prática, explicação para o empresário e CTA)."""
    )

    try:
        resposta = chamar_ia(system=system, prompt=prompt, max_tokens=850, temperature=0.75, json_mode=True)
        dados = extrair_json(resposta)
    except Exception:
        dados = {
            "headline_imagem": pauta.get("headline_sugerida", "Você não precisa abaixar o seu preço."),
            "destaque_dourado": "abaixar o seu preço",
            "subtitulo_imagem": "Preço baixo atrai cliente difícil. O tráfego certo atrai quem valoriza seu serviço.",
            "descricao_layout": estilo.get("descricao_layout", "Composição minimalista em Gotham Sentence case"),
            "legenda": "Legenda padrão da Kav para o post de teste.",
        }

    headline = dados.get("headline_imagem", "")
    headline = re.sub(r"\\b(KAV|CAVE|WAV)\\b", "", headline, flags=re.IGNORECASE).strip()
    dados["headline_imagem"] = headline

    subtitulo = dados.get("subtitulo_imagem") or dados.get("headline_apoio") or ""
    dados["subtitulo_imagem"] = subtitulo
    dados["headline_apoio"] = subtitulo
    dados["texto_card"] = ""
    dados["estilo_layout"] = estilo["id"]
    dados["estilo_nome"] = estilo["nome"]
    dados["tema_fundo"] = estilo.get("tema", "escuro")
    dados["descricao_layout"] = estilo.get("descricao_layout", "")
    dados["cor_fundo"] = estilo.get("cor_fundo", "Azul Marinho Noturno Profundo (#001424)")
    dados["cor_destaque"] = estilo.get("cor_destaque", "Dourado Kav (#EEB730)")
    dados["cor_texto"] = estilo.get("cor_texto", "Branco Puro e Cinza Slate")
    dados["posicao_logo"] = estilo.get("posicao_logo", "superior-centro")

    return dados


def gerar_brief_arte_kav(
    copy: dict, pauta: dict, cliente: dict, referencia: Optional[dict], estilo: Optional[dict] = None
) -> tuple[str, dict]:
    """Monta o briefing em inglês para a IA com a hierarquia de Headline + Subtítulo de contexto,
    metáfora visual original (zero cópia de referências) e uso estrito do logo oficial."""
    estilo = estilo or obter_estilo_kav(referencia)
    posicao_logo = estilo.get("posicao_logo", "superior-centro")
    area_logo = AREAS_LOGO.get(posicao_logo, "header area")
    backup_historico = historico.obter_backup_historico_layouts("kav", limite=5)

    # Curadoria da metáfora visual 3D original para evitar cópia de cadeiras
    metafora = curar_metafora_visual_kav(pauta, estilo)
    diretriz_cena_ajustada = estilo["diretriz_cena"].replace("__METAFORA_DESCRICAO__", metafora["descricao_prompt"])

    system = (
        SYSTEM_DESIGN_KAV.replace("__NOME_ESTILO__", estilo["nome"])
        .replace("__TEMA_LAYOUT__", estilo.get("tema", "escuro").upper())
        .replace("__DIRETRIZ_CENA__", diretriz_cena_ajustada)
        .replace("__AREA_LOGO__", area_logo)
        .replace("__METAFORA_DESCRICAO__", metafora["descricao_prompt"])
        .replace("__BACKUP_HISTORICO__", backup_historico)
    )

    partes = [
        f"Chosen Layout Archetype: {estilo['nome']} (Theme: {estilo.get('tema')})",
        f"Topic: {pauta.get('tema')}",
        "MANDATORY ARCHETYPE DIRECTIVE: " + diretriz_cena_ajustada,
        f'Main Headline to render: "{copy.get("headline_imagem")}"',
        f'Contextual Subtitle to render directly below headline: "{copy.get("subtitulo_imagem", "")}"',
        f'Kav Gold Highlight Term: "{copy.get("destaque_dourado", "")}"',
        "STRICT COPY HIERARCHY: Render the bold Headline ('" + copy.get("headline_imagem", "") + "') and the short contextual Subtitle ('" + copy.get("subtitulo_imagem", "") + "') directly below it in refined smaller font. Bottom CTA pill '[ → Leia a legenda ]'. ZERO PARAGRAPHS OR STORY CARDS ALLOWED.",
        f"ORIGINAL 3D VISUAL METAPHOR (ANTI-COPYCAT): {metafora['descricao_prompt']}",
        "STRICT TYPOGRAPHY: Gotham font ONLY in elegant Sentence Case (NO ALL CAPS).",
        f"STRICT COLOR PALETTE: Background must be {estilo.get('cor_fundo')}. Highlights in Kav Gold ({estilo.get('cor_destaque')}). Texts in {estilo.get('cor_texto')}.",
    ]

    partes.extend([
        (
            "STRICT REFERENCE IMAGES INSTRUCTION: "
            "Reference image 1 is the brand layout template. Use it STRICTLY as a directional guide for composition quality and layout spacing. "
            "NEVER COPY OR DRAW LITERAL CHAIRS OR LITERAL PROPS FROM REFERENCE 1! "
            f"Reference image 2 is the OFFICIAL BRAND LOGOTYPE MARK of Kav Marketing & Performance ('KAV'). Emulate this exact geometric logotype mark from Reference 2 into the {area_logo}. "
            "CRITICAL: DO NOT type the word 'KAV' with generic Arial/Helvetica font! Replicate the exact geometric mark with its angular cut letterforms from Reference 2. "
            "DO NOT write 'Marketing & Performance' or add plain Arial slogans beneath it! "
            "ABSOLUTE ZERO-DISTORTION MANDATE: DO NOT stretch, squash, slant, skew, or deform the logo in any way! Maintain strict 1:1 aspect ratio lock."
        ),
        (
            "STRICT ANTI-CAROUSEL MANDATE: "
            "NEVER write 'Arrasta pra entender', 'Arraste para o lado' or draw swipe buttons. "
            "This is a single static feed post (1080x1350)!"
        ),
    ])

    brief_gerado = chamar_ia(system=system, prompt="\\n".join(partes), max_tokens=750, temperature=0.7)
    return brief_gerado, estilo


def gerar_imagem_estatica_kav(
    brief: str, cliente: dict, referencia: Optional[dict], estilo: Optional[dict] = None
) -> dict:
    """Gera a imagem estática 4:5 enviando OBRIGATORIAMENTE o Template de Layout E o Logotipo Oficial como referências."""
    estilo = estilo or obter_estilo_kav(referencia)
    referencias_imagem = []

    # 1. Referência 1: Template de Layout do arquétipo sorteado (direcional, não cópia)
    if referencia and referencia.get("arquivo") and referencia["arquivo"].exists():
        referencias_imagem.append((
            referencia["arquivo"].read_bytes(),
            (
                f"Reference 1: Directional layout template for archetype '{estilo['nome']}' ({estilo.get('tema')}). "
                "Use this strictly as an aesthetic direction for hierarchy, lighting, and negative space. "
                "DO NOT copy literal chairs or props from this template!"
            ),
        ))

    # 2. Referência 2: Logotipo Oficial da Kav (Marca geométrica autêntica)
    logo_arquivo, posicao_logo = _logo_kav(cliente, referencia)
    area_logo = AREAS_LOGO.get(posicao_logo, "header area")

    if logo_arquivo and logo_arquivo.exists():
        referencias_imagem.append((
            logo_arquivo.read_bytes(),
            (
                "Reference 2: The OFFICIAL BRAND LOGOTYPE MARK of Kav Marketing & Performance ('KAV'). "
                "You MUST faithfully incorporate this EXACT geometric logotype mark into the layout. "
                f"Position it cleanly in the {area_logo} with generous margins and breathing room. "
                "CRITICAL: This is a proprietary geometric vector logotype. Do NOT type plain font 'KAV'! "
                "Do NOT write 'Marketing & Performance' or add plain slogans underneath. Use ONLY the official geometric mark 'KAV'. "
                "CRITICAL ZERO-DISTORTION MANDATE: DO NOT stretch, squash, skew, or distort the logo! Keep strict 1:1 aspect ratio lock. "
                "The logo MUST NEVER collide with, touch, or overlap any headlines or text cards!"
            ),
        ))

    backup_historico = historico.obter_backup_historico_layouts("kav", limite=4)

    try:
        imagens = [dados for dados, _ in referencias_imagem]
        descricoes = [desc for _, desc in referencias_imagem]
        prompt = _montar_prompt_final(brief, descricoes, estilo, backup_historico)

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
        "tema_fundo": estilo.get("tema", "escuro"),
        "descricao_layout": estilo.get("descricao_layout"),
        "cor_fundo": estilo.get("cor_fundo"),
        "cor_destaque": estilo.get("cor_destaque"),
        "cor_texto": estilo.get("cor_texto"),
        "posicao_logo": estilo.get("posicao_logo"),
        "modelo": bruta.get("modelo"),
    }


def _montar_prompt_final(brief: str, descricoes: list, estilo: dict, backup_historico: str = "") -> str:
    tema = estilo.get("tema", "escuro")
    partes = [
        f"TASK: High-authority static social media post design (1080x1350 vertical 4:5 ratio) for Kav Marketing & Performance in archetype '{estilo['nome']}' ({tema.upper()}).",
        "MANDATORY EXECUTION DIRECTIVES:",
        f"- LAYOUT ARCHETYPE: Strictly emulate the visual structure of '{estilo['nome']}'.",
        f"- SPECIFIC SCENE REQUIREMENT: {estilo['diretriz_cena']}",
        "- COPY HIERARCHY: Prominent Headline in Gotham Bold (Sentence Case) + Short Contextual Subtitle (8 to 14 words) directly below + '[ → Leia a legenda ]' pill button at the bottom. ZERO paragraphs or walls of text!",
        "- ANTI-COPYCAT RULE: Reference 1 is DIRECTIONAL ONLY. DO NOT copy literal objects from Reference 1 (NO CHAIRS!). Render an original Kav performance 3D metaphor (e.g. golden chess victory, 3D financial growth chart, WhatsApp lead beacon, local compass).",
        "- TYPOGRAPHY: STRICTLY use Gotham font in elegant Sentence Case (e.g. 'Atendimento rápido gera mais vendas.'). NO ALL CAPS.",
        "- FONT SIZE RESTRAINT: The headline must NOT be oversized or monstrous. Maintain moderate, restrained proportions (~55% to 65% canvas width with 20-25% breathing margins on the sides).",
        f"- COLOR PALETTE: Background must be {estilo.get('cor_fundo')}. Highlights in Kav Gold ({estilo.get('cor_destaque')}). Texts in {estilo.get('cor_texto')}.",
        "- LOGO INTEGRATION & ZERO DISTORTION: Reproduce the official Kav geometric logo mark from Reference 2 cleanly in its designated branding zone with generous margins. DO NOT type generic Arial letters! DO NOT write 'Marketing & Performance' underneath! ZERO DISTORTION: Maintain strict 1:1 aspect ratio.",
        "- NO TOP BADGES: DO NOT draw any box or tag at the top saying 'PERFORMANCE LOCAL'. Keep the top clean.",
        "- NO CAROUSEL / SWIPE TEXT: ABSOLUTELY DO NOT write 'Arrasta pra entender', 'Arraste para o lado', or draw swipe buttons. This is a single static feed post (1080x1350).",
    ]
    if backup_historico:
        partes.append("RECENT POSTS HISTORY (MAKE THIS DESIGN NOTICEABLY DIFFERENT FROM THESE):\\n" + backup_historico)

    for i, desc in enumerate(descricoes):
        partes.append(f"Input Reference Image {i + 1}: {desc}")
    partes.append("Art Direction Brief:\\n" + brief)
    return "\\n\\n".join(partes)
