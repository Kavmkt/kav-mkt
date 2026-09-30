"""Agente de Criação de Post Estático da Kav (@kav.mkt).

Gera posts estáticos minimalistas de altíssimo impacto para o feed da agência,
com foco em Tráfego Pago Local para PMEs e Marketing Descomplicado.
Segue com rigor absoluto as diretrizes oficiais da marca:
- MINIMALISMO EXTREMO DE TEXTO (Padrão Focus): Apenas o Logo KAV no topo, Headline curta (3 a 6 palavras)
  e botão pill '[ → Leia a legenda ]'. ZERO parágrafos ou blocos de texto explicativo na imagem!
- Logotipo oficial geométrico da Kav (Reference 2): Uso fiel da marca geométrica oficial (sem slogans em Arial);
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
        "descricao_layout": "Composição 100% minimalista e tipográfica estilo Focus: logo KAV oficial no topo, headline curta em Gotham com palavra dourada sublinhada e botão pill 'Leia a legenda' na base. ZERO parágrafos.",
        "instrucao_copy": "\n".join([
            "ESTRUTURA DA COPY PARA MANIFESTO FOCUS (ESCURE):",
            "- headline_imagem: Frase afiada e contida de 3 a 6 palavras em Gotham Sentence Case (ex: 'Improviso não constrói empresa.', 'Atendimento rápido gera mais vendas.').",
            "- destaque_dourado: 1 a 2 palavras centrais em Dourado Kav (#EEB730) com traço fino sublinhado.",
            "- cta_pill: '→ Leia a legenda'",
            "- PROIBIÇÃO ABSOLUTA: NÃO escreva parágrafos, blocos de texto ou explicações para a imagem. Deixe o campo texto_card VAZIO. Toda a explicação vai na LEGENDA do Instagram.",
        ]),
        "diretriz_cena": (
            "ARQUÉTIPO VISUAL: MANIFESTO EDITORIAL MINIMALISTA FOCUS (TEMA ESCURO). "
            "A peça é 100% minimalista, limpa e espaçosa (80% de espaço livre/respiro), espelhando fielmente o layout de referência Focus. "
            "Topo centro: Logotipo oficial KAV (Reference 2) em proporção 1:1 rigorosa, sem slogan em texto embaixo, com respiro generoso. "
            "Centro da tela: Apenas a Headline em tipografia Gotham Sentence Case com tamanho moderado e contido (ocupando ~55% a 65% da largura da tela, com ampla margem de respiro de 20% a 25% nas laterais). "
            "A palavra de destaque em Dourado Kav (#EEB730) recebe um traço fino e elegante dourado sublinhado. "
            "Base: Botão pill minimalista e refinado '[ →  Leia a legenda ]'. "
            "Fundo: Azul Marinho Noturno Profundo (#001424) com iluminação sutil no centro. "
            "PROIBIÇÃO RIGOROSA: NUNCA crie caixas com parágrafos, histórias ou explicações. ZERO texto corrido na imagem!"
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
        "descricao_layout": "Fundo claro invertido em degradê, logo KAV oficial em azul marinho no topo, headline contida em Azul Marinho com destaque dourado e botão pill. ZERO texto secundário.",
        "instrucao_copy": "\n".join([
            "ESTRUTURA DA COPY PARA MANIFESTO FOCUS (CLARO INVERTIDO):",
            "- headline_imagem: Frase afiada de 3 a 6 palavras em Gotham Sentence Case (ex: 'Atendimento rápido gera mais vendas.', 'Você não precisa abaixar o seu preço.').",
            "- destaque_dourado: 1 a 2 palavras centrais em Dourado Kav (#EEB730).",
            "- cta_pill: '→ Leia a legenda'",
            "- PROIBIÇÃO ABSOLUTA: Deixe texto_card VAZIO. ZERO parágrafos na imagem!",
        ]),
        "diretriz_cena": (
            "ARQUÉTIPO VISUAL: MANIFESTO EDITORIAL FOCUS EM TEMA CLARO INVERTIDO. "
            "Fundo: Gradiente ultra suave e refinado, iniciando em Branco Puro (#FFFFFF) no topo e transicionando suavemente para Cinza-Azulado Super Claro (#EBF1F6) na base. "
            "Topo centro: Logotipo oficial KAV (Reference 2) em Azul Marinho Noturno Profundo (#001424), perfeitamente nítido e geométrico, sem slogans embaixo, com respiro generoso. "
            "Centro: Headline em tipografia Gotham em Sentence Case em Azul Marinho (#001424), tamanho moderado e contido (~55% da largura da tela, com ampla margem de respiro). "
            "Palavra de destaque em Dourado Kav (#EEB730) com traço sublinhado dourado sutil. "
            "Base: Botão pill minimalista '[ →  Leia a legenda ]' com borda fina e texto em azul marinho. "
            "PROIBIÇÃO RIGOROSA: NUNCA desenhe caixas de texto com parágrafos ou explicações. ZERO texto corrido na imagem!"
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
        "descricao_layout": "Card retangular flutuante escuro (#031E34) no centro com perfil @kav.mkt, tese reflexiva curta de 1 a 2 frases e chamada sutil. ZERO blocos longos de texto.",
        "instrucao_copy": "\n".join([
            "ESTRUTURA DA COPY PARA TWEET BOX (ESCURE):",
            "- headline_imagem: Frase reflexiva curta em Gotham Sentence Case (ex: 'Não é trabalho do seu cliente se lembrar de você.').",
            "- frase_apoio: No máximo 1 frase afiada de até 10 palavras (ex: 'É sua obrigação ter a certeza de que ele não vai te esquecer.').",
            "- destaque_dourado: 1 termo chave para brilhar em Dourado Kav.",
            "- cta_card: 'Leia a legenda completa ↘'",
            "- PROIBIÇÃO: NÃO escreva parágrafos longos!",
        ]),
        "diretriz_cena": (
            "ARQUÉTIPO VISUAL: CARD FLUTUANTE DE REDE SOCIAL (ESTILO SAMUEL REIS - TEMA ESCURO). "
            "No centro da tela, renderize um elegante CARD RETANGULAR FLUTUANTE em tom azul noturno escuro (#031E34) "
            "com cantos suavemente arredondados e borda sutil translúcida (#123452). "
            "Topo do card: badge de perfil com pequeno avatar circular com 'K' dourado e handle '@kav.mkt'. "
            "Corpo do card: tese de autoridade em tipografia Gotham em Sentence Case com tamanho equilibrado e moderado. "
            "Rodapé interno: chamada sutil 'Leia a legenda completa ↘' em Dourado Kav (#EEB730). "
            "Fundo: Azul Marinho Noturno Profundo (#001424). "
            "PROIBIDO PARÁGRAFOS OU TEXTOS DENSOS. Mantenha a leitura dinâmica em 3 segundos."
        ),
    },
    {
        "id": "afirmacao_tweet_box_claro",
        "tema": "claro",
        "arquivo_referencia": "ref_afirmacao_tweet_box_claro.png",
        "nome": "Tweet Box de Autoridade (Tema Claro Invertido)",
        "posicao_logo": "superior-esquerdo",
        "cor_fundo": "Branco com degradê suave para cinza-azulado super claro (#FFFFFF para #EBF1F6)",
        "cor_destaque": "Dourado Kav Solar (#EEB730)",
        "cor_texto": "Azul Marinho Noturno Profundo (#001424) e Cinza Slate (#475569)",
        "descricao_layout": "Fundo claro invertido, card flutuante branco puro com sombra suave e borda discreta, textos curtos em Azul Marinho e perfil @kav.mkt. Sem textão.",
        "instrucao_copy": "\n".join([
            "ESTRUTURA DA COPY PARA TWEET BOX (CLARO):",
            "- headline_imagem: Frase reflexiva em Gotham Sentence Case em Azul Marinho (3 a 6 palavras).",
            "- frase_apoio: No máximo 1 frase de suporte curta (até 10 palavras).",
            "- cta_card: 'Leia a legenda completa ↘'",
            "- PROIBIÇÃO: ZERO parágrafos na imagem!",
        ]),
        "diretriz_cena": (
            "ARQUÉTIPO VISUAL: TWEET BOX EM TEMA CLARO INVERTIDO. "
            "Fundo: Gradiente sutil do Branco Puro (#FFFFFF) no topo para Cinza-Azulado Super Claro (#EBF1F6) na base. "
            "No centro: Card flutuante retangular branco puro com sombra suave e borda sutil (#CBD5E1). "
            "Topo do card: Avatar @kav.mkt. Corpo do card: tese curta em tipografia Gotham Sentence Case em Azul Marinho Noturno (#001424). "
            "Chamada sutil 'Leia a legenda completa ↘' em Dourado Kav (#EEB730). "
            "PROIBIDO CAIXA ALTA. PROIBIDO PARÁGRAFOS LONGOS."
        ),
    },
    {
        "id": "destaque_dourado",
        "tema": "escuro",
        "arquivo_referencia": "ref_destaque_dourado.png",
        "nome": "Metáfora Visual 3D / Objeto de Destaque (Estilo Well.dsg & ORB)",
        "posicao_logo": "superior-centro",
        "cor_fundo": "Azul Petróleo Escuro (#001424 a #001D32)",
        "cor_destaque": "Dourado Kav Solar (#EEB730) no objeto herói",
        "cor_texto": "Branco Puro (#FFFFFF) e Cinza Slate (#94A3B8)",
        "descricao_layout": "Objeto físico 3D central em Dourado Kav como metáfora de destaque, com frases curtas de 3 a 5 palavras no topo e na base. ZERO texto corrido.",
        "instrucao_copy": "\n".join([
            "ESTRUTURA DA COPY PARA METÁFORA VISUAL 3D (ESCURE):",
            "- headline_imagem: Frase superior de abertura curta (ex: 'Você não precisa fazer igual. Nem pensar igual.').",
            "- headline_apoio: Frase inferior de fechamento curta (ex: 'Faça diferente. Seja estratégico.').",
            "- subtitulo: Frase curta reflexiva (ex: 'O marketing que copia, some.').",
            "- destaque_dourado: O objeto central herói da cena.",
            "- PROIBIÇÃO: ZERO parágrafos!",
        ]),
        "diretriz_cena": (
            "ARQUÉTIPO VISUAL: OBJETO FÍSICO 3D DE DESTAQUE CENTRAL (ESTILO WELL.DSG / CADEIRA DOURADA). "
            "No centro da cena, renderize um OBJETO FÍSICO 3D REALISTA ISOLADO E IMPACTANTE que represente a metáfora do tema "
            "(exemplo: uma elegante cadeira de design moderno em Dourado Kav brilhante #EEB730 posicionada no meio de cadeiras escuras). "
            "Metade superior: Frase reflexiva de abertura curta em tipografia Gotham Sentence Case. "
            "Metade inferior: Frase de conclusão impactante curta em tipografia Gotham branca e cinza slate. "
            "Fundo: Gradiente Azul Marinho Noturno Profundo (#001424). "
            "PROIBIDO QUALQUER PARÁGRAFO OU TEXTO CORRIDO NA IMAGEM."
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
        "descricao_layout": "Fundo claro em degradê, headline afiada em Gotham Sentence case em Azul Marinho e frase curta de virada de chave. Sem textão.",
        "instrucao_copy": "\n".join([
            "ESTRUTURA DA COPY PARA QUEBRA DE OBJEÇÃO (CLARO INVERTIDO):",
            "- headline_imagem: Frase provocativa de quebra de objeção em Gotham Sentence Case (3 a 6 palavras, ex: 'Você não precisa abaixar o seu preço.').",
            "- frase_apoio: Frase curta de virada em até 10 palavras (ex: 'Preço baixo atrai cliente difícil. Posicionamento atrai valor.').",
            "- cta_pill: '→ Leia a legenda'",
            "- PROIBIÇÃO: NÃO escreva parágrafos longos ou histórias na imagem!",
        ]),
        "diretriz_cena": (
            "ARQUÉTIPO VISUAL: QUEBRA DE OBJEÇÃO EM TEMA CLARO INVERTIDO. "
            "Fundo: Branco Puro (#FFFFFF) no topo com degradê suave para Cinza-Azulado Super Claro (#EBF1F6) na base. "
            "Topo: Badge sutil de perfil com avatar e identificação '@kav.mkt'. "
            "Corpo superior: Grande headline afiada em tipografia Gotham Sentence Case em Azul Marinho Noturno (#001424), com tamanho contido e elegante. "
            "Corpo inferior: Card retangular fino com uma única frase curta de virada de chave com borda em Dourado Kav (#EEB730). "
            "Abaixo do card: botão pill fino '[ →  Leia a legenda ]'. "
            "PROIBIDO CAIXA ALTA. PROIBIDO PARÁGRAFOS OU TEXTOS EXPLICATIVOS DENSOS."
        ),
    },
]

SYSTEM_COPY_KAV = """Você é a Redatora Sênior & Copywriter da Kav (@kav.mkt).
Sua missão é escrever a headline visual da arte e a LEGENDA COMPLETA para um post estático de Instagram da Kav,
formatado sob medida para o ARQUÉTIPO DE LAYOUT selecionado.

DIRETRIZES DE MARCA DA KAV:
__SKILL__

PADRÃO DE LEGENDA DA KAV:
__PADRAO_LEGENDA__

ARQUÉTIPO DE LAYOUT ESCOLHIDO: __NOME_ESTILO__
TEMA DO LAYOUT: __TEMA_LAYOUT__
__INSTRUCAO_COPY__

__BACKUP_HISTORICO__

REGRA DE OURO SOBRE QUANTIDADE DE TEXTO (ZERO POLUIÇÃO VISUAL):
1. A IMAGEM DEVE TER O MÍNIMO DE TEXTO POSSÍVEL (Estilo Focus):
   - headline_imagem: Curta, magnética, de 3 a 6 palavras (ex: 'Atendimento rápido gera mais vendas.', 'Improviso não constrói empresa.').
   - destaque_dourado: 1 a 2 palavras centrais da headline para receber o traço dourado sublinhado.
   - frase_apoio: No máximo 1 frase curta de até 8 a 10 palavras (ou string vazia).
   - NUNCA escreva parágrafos, blocos de texto ou historinhas explicativas para a imagem!
   - Deixe o campo 'texto_card' SEMPRE VAZIO ou com no máximo 8 palavras.
2. TODA A EXPLICAÇÃO, ANALOGIA E DETALHES VÃO EXCLUSIVAMENTE NA LEGENDA DO POST (CAPTION):
   - É na LEGENDA do Instagram que você conta a história do garçom, explica como o tráfego local funciona e faz o pitch para mandar direct.
   - A arte do feed é apenas o gancho estético minimalista que para o scroll!

Responda APENAS com um objeto JSON:
{
  "headline_imagem": "Headline afiada em Gotham Sentence Case (3 a 6 palavras)",
  "destaque_dourado": "Palavra central em dourado",
  "headline_apoio": "Frase de apoio curtíssima (máximo 8 palavras) ou string vazia",
  "texto_card": "",
  "descricao_layout": "Resumo em 1 linha da estrutura visual minimalista",
  "legenda": "Legenda completa formatada com a explicação rica, parágrafos, analogia, CTA e hashtags"
}
"""

SYSTEM_DESIGN_KAV = """You are the Senior Art Director of Kav (@kav.mkt), a premier digital performance marketing agency.
Your task is to write a comprehensive, professional graphic design brief for a single static Instagram feed post (Vertical 4:5 ratio, 1080x1350).

DEFINITIVE BRAND IDENTITY & KEY VISUAL:
1. STRICT TEXT MINIMALISM & ZERO POLLUTION MANDATE (FOCUS BENCHMARK):
   - ABSOLUTELY PROHIBITED: NEVER render paragraphs, blocks of explanatory text, multi-line essays, or story text cards on the image!
   - The graphic is strictly minimal and clean, with 75% to 85% negative breathing space.
   - The image must contain ONLY:
     * Reference 2: The official KAV brand logo mark in the header area.
     * Central headline in Gotham Sentence Case (3 to 6 words only).
     * Minimal pill CTA button '[ → Leia a legenda ]' in the bottom area.
   - ALL EXPLANATIONS, STORIES, AND DETAILS BELONG IN THE CAPTION, NOT ON THE IMAGE.
2. OFFICIAL KAV LOGO MARK (REFERENCE 2):
   - Reference image 2 is the OFFICIAL KAV BRAND LOGOTYPE MARK (the iconic geometric slanted 'KAV' mark).
   - You MUST faithfully incorporate this EXACT geometric mark from Reference 2.
   - ABSOLUTE PROHIBITION ON SLOGANS: Do NOT write 'Marketing & Performance' or add plain Arial slogans beneath it. Use ONLY the official geometric mark 'KAV' as provided in Reference 2.
   - ABSOLUTE ZERO-DISTORTION: NEVER stretch, squash, slant, skew, or deform the logo in any way! Maintain strict 1:1 aspect ratio lock.
   - Position the logo in the __AREA_LOGO__ with generous breathing room (at least 60-80px safe padding from any canvas edge or text element).
3. TYPOGRAPHY SCALE & RESTRAINED ELEGANCE:
   - Primary Font: STRICTLY Gotham in elegant Sentence Case (NO ALL CAPS!).
   - Strict size restraint: Moderate, restrained headline size (~55% to 65% canvas width, leaving at least 20-25% breathing margins on the sides).
4. COLOR PALETTE:
   - Current Target Theme: __TEMA_LAYOUT__
   - If DARK THEME: Deep nocturnal navy background (#001424). PROHIBITED PURE BLACK (#000000). Highlights in Kav Gold (#EEB730). Primary text in Pure White (#FFFFFF).
   - If LIGHT INVERTED THEME: Pure White (#FFFFFF) at the top with a subtle, ultra-soft gradient transitioning gently into a very faint bluish-gray (#EBF1F6) at the bottom. Primary text in Deep Nocturnal Navy (#001424). Highlights in Kav Gold (#EEB730 / #D99B00) with thin gold underline.
5. STRICT PROHIBITIONS:
   - NO CAROUSEL / SWIPE TEXT: ABSOLUTELY NEVER write 'Arrasta pra entender', 'Arraste para o lado', or draw swipe buttons.
   - NO TOP BADGE: DO NOT render any box or pill at the top saying 'PERFORMANCE LOCAL'. Keep the top clean.

LAYOUT ARCHETYPE TO EMULATE: __NOME_ESTILO__
ARCHETYPE COMPOSITION:
__DIRETRIZ_CENA__

__BACKUP_HISTORICO__

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
    """Localiza o arquivo de logotipo OFICIAL autêntico da Kav (sem slogans gerados por script)."""
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
    # Prioriza arquivos oficiais com tamanho real (> 25KB)
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
    """Gera os textos do post estático da Kav: headline curta para a arte e legenda completa para o feed."""
    estilo = estilo or ESTILOS_LAYOUT_KAV[0]
    skill = cliente.get("skill", "")
    padrao = cliente.get("legenda_padrao", "") or "(Padrão Kav: gancho, explicação prática para PME, CTA no direct, hashtags)"
    backup_historico = historico.obter_backup_historico_layouts("kav", limite=5)

    system = (
        SYSTEM_COPY_KAV.replace("__SKILL__", skill)
        .replace("__PADRAO_LEGENDA__", padrao)
        .replace("__NOME_ESTILO__", estilo["nome"])
        .replace("__TEMA_LAYOUT__", estilo.get("tema", "escuro").upper())
        .replace("__INSTRUCAO_COPY__", estilo.get("instrucao_copy", ""))
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
1. Para a IMAGEM: Gere APENAS a headline curta e magnética (3 a 6 palavras em Sentence Case) e 1 termo para destaque dourado. Deixe texto_card VAZIO. NÃO crie parágrafos na imagem!
2. Para a LEGENDA: Desenvolva o texto completo e rico da postagem (com gancho, analogia prática, explicação para o empresário e CTA)."""
    )

    try:
        resposta = chamar_ia(system=system, prompt=prompt, max_tokens=850, temperature=0.75, json_mode=True)
        dados = extrair_json(resposta)
    except Exception:
        dados = {
            "headline_imagem": pauta.get("headline_sugerida", "Você não precisa abaixar o seu preço."),
            "destaque_dourado": "abaixar o seu preço",
            "headline_apoio": "",
            "texto_card": "",
            "descricao_layout": estilo.get("descricao_layout", "Composição minimalista em Gotham Sentence case"),
            "legenda": "Legenda padrão da Kav para o post de teste.",
        }

    headline = dados.get("headline_imagem", "")
    headline = re.sub(r"\\b(KAV|CAVE|WAV)\\b", "", headline, flags=re.IGNORECASE).strip()
    dados["headline_imagem"] = headline
    # Força texto_card vazio para nunca poluir a imagem
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
    """Monta o briefing em inglês para a IA com contenção absoluta de texto e uso fiel do logo oficial."""
    estilo = estilo or obter_estilo_kav(referencia)
    posicao_logo = estilo.get("posicao_logo", "superior-centro")
    area_logo = AREAS_LOGO.get(posicao_logo, "header area")
    backup_historico = historico.obter_backup_historico_layouts("kav", limite=5)

    system = (
        SYSTEM_DESIGN_KAV.replace("__NOME_ESTILO__", estilo["nome"])
        .replace("__TEMA_LAYOUT__", estilo.get("tema", "escuro").upper())
        .replace("__DIRETRIZ_CENA__", estilo["diretriz_cena"])
        .replace("__AREA_LOGO__", area_logo)
        .replace("__BACKUP_HISTORICO__", backup_historico)
    )

    partes = [
        f"Chosen Layout Archetype: {estilo['nome']} (Theme: {estilo.get('tema')})",
        f"Topic: {pauta.get('tema')}",
        "MANDATORY ARCHETYPE DIRECTIVE: " + estilo["diretriz_cena"],
        f'Main Headline to render: "{copy.get("headline_imagem")}"',
        f'Kav Gold Highlight Term: "{copy.get("destaque_dourado", "")}"',
        "STRICT TEXT MINIMALISM: Render ONLY the headline ({copy.get('headline_imagem')}) and the pill button '[ → Leia a legenda ]'. ZERO PARAGRAPHS OR STORY CARDS ALLOWED ON THE CANVAS.",
        "STRICT TYPOGRAPHY: Gotham font ONLY in elegant Sentence Case (NO ALL CAPS).",
        f"STRICT COLOR PALETTE: Background must be {estilo.get('cor_fundo')}. Highlights in Kav Gold ({estilo.get('cor_destaque')}). Texts in {estilo.get('cor_texto')}.",
    ]

    partes.extend([
        (
            "STRICT REFERENCE IMAGES INSTRUCTION: "
            "Reference image 1 is the brand layout template. Strictly follow its structure, spacing, and hierarchy. "
            f"Reference image 2 is the OFFICIAL BRAND LOGO MARK of Kav Marketing & Performance ('KAV'). Emulate this exact geometric logotype mark from Reference 2 into the {area_logo}. "
            "DO NOT write 'Marketing & Performance' or add plain Arial text slogans beneath it! Use ONLY the official geometric mark 'KAV' as shown in Reference 2. "
            "ABSOLUTE ZERO-DISTORTION MANDATE: DO NOT stretch, squash, slant, skew, or deform the logo in any way! Maintain strict 1:1 aspect ratio lock."
        ),
        (
            "STRICT ANTI-CAROUSEL MANDATE: "
            "NEVER write 'Arrasta pra entender', 'Arraste para o lado' or draw swipe buttons. "
            "This is a single static feed post (1080x1350)!"
        ),
    ])

    brief_gerado = chamar_ia(system=system, prompt="\n".join(partes), max_tokens=750, temperature=0.7)
    return brief_gerado, estilo


def gerar_imagem_estatica_kav(
    brief: str, cliente: dict, referencia: Optional[dict], estilo: Optional[dict] = None
) -> dict:
    """Gera a imagem estática 4:5 enviando OBRIGATORIAMENTE o Template de Layout E o Logotipo Oficial como referências."""
    estilo = estilo or obter_estilo_kav(referencia)
    referencias_imagem = []

    # 1. Referência 1: Template de Layout do arquétipo sorteado
    if referencia and referencia.get("arquivo") and referencia["arquivo"].exists():
        referencias_imagem.append((
            referencia["arquivo"].read_bytes(),
            (
                f"Reference 1: The brand layout design reference template for archetype '{estilo['nome']}' ({estilo.get('tema')}). "
                "Emulate this exact minimalist graphic design structure, typography hierarchy in restrained Gotham Sentence case, and generous breathing space balance."
            ),
        ))

    # 2. Referência 2: Logotipo Oficial da Kav (Versão clara ou escura de acordo com o tema)
    logo_arquivo, posicao_logo = _logo_kav(cliente, referencia)
    area_logo = AREAS_LOGO.get(posicao_logo, "header area")

    if logo_arquivo and logo_arquivo.exists():
        referencias_imagem.append((
            logo_arquivo.read_bytes(),
            (
                "Reference 2: The OFFICIAL BRAND LOGO MARK of Kav Marketing & Performance ('KAV'). "
                "You MUST faithfully incorporate this EXACT geometric logotype mark into the layout. "
                f"Position it cleanly in the {area_logo} with generous margins and breathing room. "
                "CRITICAL: Do NOT write 'Marketing & Performance' or add plain slogans underneath. Use ONLY the official geometric mark 'KAV'. "
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
        "- STRICT TEXT MINIMALISM: Absolutely NO paragraphs, explanations, or dense text boxes! Only the official KAV logo, the short 3-6 word headline, and the '[ → Leia a legenda ]' pill button.",
        "- TYPOGRAPHY: STRICTLY use Gotham font in elegant Sentence Case (e.g. 'Atendimento rápido gera mais vendas.'). NO ALL CAPS.",
        "- FONT SIZE RESTRAINT: The headline must NOT be oversized or monstrous. Maintain moderate, restrained proportions (~55% to 65% canvas width with 20-25% breathing margins on the sides).",
        f"- COLOR PALETTE: Background must be {estilo.get('cor_fundo')}. Highlights in Kav Gold ({estilo.get('cor_destaque')}). Texts in {estilo.get('cor_texto')}.",
        "- LOGO INTEGRATION & ZERO DISTORTION: Reproduce the official Kav logo mark from Reference 2 cleanly in its designated branding zone with generous margins. DO NOT write 'Marketing & Performance' underneath! ZERO DISTORTION: Never stretch, squash, or warp the logo! Maintain strict 1:1 aspect ratio.",
        "- NO TOP BADGES: DO NOT draw any box or tag at the top saying 'PERFORMANCE LOCAL'. Keep the top clean.",
        "- NO CAROUSEL / SWIPE TEXT: ABSOLUTELY DO NOT write 'Arrasta pra entender', 'Arraste para o lado', or draw swipe buttons. This is a single static feed post (1080x1350).",
    ]
    if backup_historico:
        partes.append("RECENT POSTS HISTORY (MAKE THIS DESIGN NOTICEABLY DIFFERENT FROM THESE):\n" + backup_historico)

    for i, desc in enumerate(descricoes):
        partes.append(f"Input Reference Image {i + 1}: {desc}")
    partes.append("Art Direction Brief:\n" + brief)
    return "\n\n".join(partes)
