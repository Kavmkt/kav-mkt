"""Agente de Criação de Post Estático da Kav (@kav.mkt).

Gera posts estáticos únicos de altíssimo impacto para o feed da própria agência,
com foco em Tráfego Pago Local para PMEs e Marketing Descomplicado.
Segue com fidelidade as diretrizes oficiais da marca:
- Alternância entre Temas Escuros (Azul Marinho Noturno #001424) e Temas Claros Invertidos
  (Branco com degradê suave para cinza-azulado super claro #FFFFFF para #EBF1F6);
- Tipografia Gotham em Sentence Case com proporção cautelosa, elegante e contida (estilo Focus);
- Preservação matemática do logotipo oficial da Kav (proporção 1:1 travada, sem distorção);
- Histórico Inteligente de 120 dias (4 meses) para anti-repetição de temas e layouts.
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
        "descricao_layout": "Composição 100% tipográfica monumental e contida em Gotham Sentence case (estilo Focus), com palavra central em Dourado Kav e traço de destaque",
        "instrucao_copy": "\n".join([
            "ESTRUTURA DA COPY PARA MANIFESTO EDITORIAL FOCUS (ESCURE):",
            "- headline_imagem: Frase monumental e contida de 3 a 5 palavras em Gotham Sentence Case (ex: 'Improviso não constrói empresa.').",
            "- destaque_dourado: 1 a 2 palavras centrais que recebem o Dourado Kav e o traço fino sublinhado (ex: 'não constrói').",
            "- headline_apoio: Frase curta de apoio reflexivo em Sentence Case.",
            "- cta_pill: '→ Leia a legenda'",
        ]),
        "diretriz_cena": (
            "ARQUÉTIPO VISUAL: MANIFESTO EDITORIAL MINIMALISTA MONUMENTAL (ESTILO FOCUS - TEMA ESCURO). "
            "A arte é estritamente tipográfica, imponente e limpa, espelhando fielmente o layout de referência Focus. "
            "Topo centro: Logotipo oficial KAV perfeitamente proporcional (proporção 1:1 sem esticar ou achatar) com amplo respiro no cabeçalho. "
            "Centro: Headline em tipografia Gotham em Sentence Case com TAMANHO CONTIDO E MODERADO (ocupando ~55% a 65% da largura da tela, com ampla margem de respiro de 20% a 25% nas laterais - NUNCA letras gigantescas que encostam nas bordas). "
            "A palavra de destaque em Dourado Kav (#EEB730) recebe um traço fino e elegante dourado sublinhado. "
            "Abaixo da headline: botão pill fino arredondado minimalista contendo estritamente '[ →  Leia a legenda ]'. "
            "Fundo: Azul Marinho Noturno Profundo (#001424) com iluminação sutil no centro. "
            "PROIBIDO PRETO PURO (#000000). PROIBIDO CAIXA ALTA (ALL CAPS). PROIBIDO 'Arrasta pra entender'."
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
        "descricao_layout": "Fundo claro invertido com degradê suave branco para cinza azulado, tipografia Gotham em Azul Marinho Nobre e destaque Dourado",
        "instrucao_copy": "\n".join([
            "ESTRUTURA DA COPY PARA MANIFESTO EDITORIAL FOCUS (CLARO INVERTIDO):",
            "- headline_imagem: Frase contida e afiada de 3 a 5 palavras em Gotham Sentence Case (ex: 'Improviso não constrói empresa.').",
            "- destaque_dourado: 1 a 2 palavras centrais em Dourado Kav (#EEB730) que recebem o traço fino sublinhado.",
            "- headline_apoio: Frase curta de apoio em Azul Marinho/Slate.",
            "- cta_pill: '→ Leia a legenda'",
        ]),
        "diretriz_cena": (
            "ARQUÉTIPO VISUAL: MANIFESTO EDITORIAL FOCUS EM TEMA CLARO INVERTIDO. "
            "Fundo: Gradiente ultra suave e refinado, iniciando em Branco Puro (#FFFFFF) no topo e transicionando suavemente para um Cinza-Azulado Super Claro (#EBF1F6) na base. "
            "Topo centro: Logotipo oficial KAV em Azul Marinho Noturno Profundo (#001424) com proporção 1:1 rigorosamente preservada e amplo respiro. "
            "Centro: Headline elegante em tipografia Gotham em Sentence Case em Azul Marinho Noturno Profundo (#001424), com tamanho moderado e contido (ocupando ~55% da largura da tela, com ampla margem de respiro nas laterais). "
            "Palavra de destaque em Dourado Kav (#EEB730) com traço sublinhado dourado sutil. "
            "Base: Botão pill minimalista com borda fina e texto em azul marinho '[ →  Leia a legenda ]'. "
            "PROIBIDO CAIXA ALTA (ALL CAPS). PROIBIDO 'Arrasta pra entender'."
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
        "descricao_layout": "Card retangular flutuante escuro (#031E34) no centro com perfil @kav.mkt, tese reflexiva e suporte em card",
        "instrucao_copy": "\n".join([
            "ESTRUTURA DA COPY PARA TWEET BOX (ESCURE):",
            "- headline_imagem: Frase reflexiva em Gotham Sentence Case com tamanho moderado (ex: 'Não é trabalho do seu cliente se lembrar de você.').",
            "- texto_card: Frase de suporte elegante em Sentence Case para o interior do card.",
            "- destaque_dourado: 1 termo chave para brilhar em Dourado Kav.",
            "- cta_card: 'Leia a legenda completa ↘'",
        ]),
        "diretriz_cena": (
            "ARQUÉTIPO VISUAL: CARD FLUTUANTE DE REDE SOCIAL (ESTILO SAMUEL REIS - TEMA ESCURO). "
            "No centro da tela, renderize um elegante CARD RETANGULAR FLUTUANTE em tom azul noturno escuro (#031E34) "
            "com cantos suavemente arredondados e borda sutil translúcida (#123452). "
            "Topo do card: badge de perfil com pequeno avatar circular com 'K' dourado, nome 'Kav Marketing' e handle '@kav.mkt'. "
            "Corpo do card: tese de autoridade em tipografia Gotham em Sentence Case com tamanho equilibrado e cauteloso (não estrondoso). "
            "Rodapé interno: chamada sutil 'Leia a legenda completa ↘' em Dourado Kav (#EEB730). "
            "Fundo: Azul Marinho Noturno Profundo (#001424). "
            "PROIBIDO PRETO PURO. PROIBIDO CAIXA ALTA. PROIBIDO 'Arrasta pra entender'."
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
        "descricao_layout": "Fundo claro invertido, card flutuante branco puro com sombra suave e borda discreta, textos em Azul Marinho e perfil @kav.mkt",
        "instrucao_copy": "\n".join([
            "ESTRUTURA DA COPY PARA TWEET BOX (CLARO):",
            "- headline_imagem: Frase reflexiva em Gotham Sentence Case com tamanho moderado em Azul Marinho (ex: 'Não é trabalho do seu cliente se lembrar de você.').",
            "- texto_card: Frase de suporte elegante em Sentence Case.",
            "- destaque_dourado: 1 termo chave em Dourado Kav.",
            "- cta_card: 'Leia a legenda completa ↘'",
        ]),
        "diretriz_cena": (
            "ARQUÉTIPO VISUAL: TWEET BOX EM TEMA CLARO INVERTIDO. "
            "Fundo: Gradiente sutil do Branco Puro (#FFFFFF) no topo para Cinza-Azulado Super Claro (#EBF1F6) na base. "
            "No centro: Card flutuante retangular branco puro com sombra suave e borda sutil (#CBD5E1). "
            "Topo do card: Avatar @kav.mkt. Corpo do card: tese em tipografia Gotham Sentence Case em Azul Marinho Noturno Profundo (#001424). "
            "Card interno de apoio com texto explicativo e chamada 'Leia a legenda completa ↘' em Dourado Kav (#EEB730). "
            "PROIBIDO CAIXA ALTA. PROIBIDO 'Arrasta pra entender'."
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
        "descricao_layout": "Objeto físico 3D central em Dourado Kav como metáfora de destaque, com textos divididos no topo e na base em Sentence case",
        "instrucao_copy": "\n".join([
            "ESTRUTURA DA COPY PARA METÁFORA VISUAL 3D (ESCURE):",
            "- headline_imagem: Frase superior de abertura em Gotham Sentence Case (ex: 'Você não precisa fazer igual. Nem pensar igual.').",
            "- headline_apoio: Frase inferior de fechamento em Gotham Sentence Case (ex: 'Faça diferente. Seja estratégico.').",
            "- subtitulo: Frase curta reflexiva (ex: 'O marketing que copia, some.').",
            "- destaque_dourado: O objeto central herói da cena.",
        ]),
        "diretriz_cena": (
            "ARQUÉTIPO VISUAL: OBJETO FÍSICO 3D DE DESTAQUE CENTRAL (ESTILO WELL.DSG / ORB / CADEIRA). "
            "No centro da cena, renderize um OBJETO FÍSICO 3D REALISTA ISOLADO E IMPACTANTE que represente a metáfora do tema "
            "(exemplo: uma elegante cadeira de design moderno em Dourado Kav brilhante #EEB730 posicionada no meio de cadeiras escuras). "
            "Metade superior: Frase reflexiva de abertura em tipografia Gotham em Sentence Case com tamanho moderado e contido. "
            "Metade inferior: Frase de conclusão impactante em tipografia Gotham branca e cinza slate. "
            "Fundo: Gradiente Azul Marinho Noturno Profundo (#001424). "
            "PROIBIDO PRETO PURO. PROIBIDO CAIXA ALTA. PROIBIDO 'Arrasta pra entender'."
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
        "descricao_layout": "Fundo claro em degradê, headline afiada em Gotham Sentence case em Azul Marinho e card com a virada do Método Kav",
        "instrucao_copy": "\n".join([
            "ESTRUTURA DA COPY PARA QUEBRA DE OBJEÇÃO (CLARO INVERTIDO):",
            "- headline_imagem: Frase provocativa de quebra de objeção em Gotham Sentence Case (ex: 'Você não precisa abaixar o seu preço.').",
            "- texto_card: Tese de sustentação da Kav em tipografia limpa em Azul Marinho.",
            "- cta_pill: '→ Leia a legenda'",
            "- destaque_dourado: 1 termo da virada em Dourado Kav.",
        ]),
        "diretriz_cena": (
            "ARQUÉTIPO VISUAL: QUEBRA DE OBJEÇÃO EM TEMA CLARO INVERTIDO. "
            "Fundo: Branco Puro (#FFFFFF) no topo com degradê suave para Cinza-Azulado Super Claro (#EBF1F6) na base. "
            "Topo: Badge sutil de perfil com avatar e identificação '@kav.mkt'. "
            "Corpo superior: Grande headline afiada em tipografia Gotham em Sentence Case em Azul Marinho Noturno Profundo (#001424), com tamanho contido e elegante. "
            "Corpo inferior: Card retangular em branco puro com borda nítida em Dourado Kav (#EEB730) e tese da agência Kav. "
            "Abaixo do card: botão pill fino '[ →  Leia a legenda ]'. "
            "PROIBIDO CAIXA ALTA. PROIBIDO 'Arrasta pra entender'."
        ),
    },
    {
        "id": "impacto_condensado_grid",
        "tema": "escuro",
        "arquivo_referencia": "ref_impacto_condensado_grid.png",
        "nome": "Grid Técnico Blueprint (Estilo Workspace - Tema Escuro)",
        "posicao_logo": "superior-direito",
        "cor_fundo": "Azul Marinho com Micro-Grid Blueprint (#001424 / linhas em #072036)",
        "cor_destaque": "Dourado Kav Solar (#EEB730)",
        "cor_texto": "Branco Puro (#FFFFFF) e Nuvem Cinza Muted (#505F7D)",
        "descricao_layout": "Fundo com micro-grade técnica blueprint, badge de tendência, headline maciça em Gotham e nuvem de dados de performance",
        "instrucao_copy": "\n".join([
            "ESTRUTURA DA COPY PARA GRID TÉCNICO WORKSPACE:",
            "- tag_topo: '📈 Quer crescer?'",
            "- headline_imagem: Frase de impacto direto em Gotham Sentence Case com tamanho moderado.",
            "- termos_performance: Nuvem de termos técnicos de performance local separados por pontos.",
            "- destaque_dourado: Termo chave em Dourado Kav.",
        ]),
        "diretriz_cena": (
            "ARQUÉTIPO VISUAL: BLUEPRINT TÉCNICO & DADOS DE PERFORMANCE. "
            "Fundo: Superfície Azul Marinho Profunda (#001424) com MICRO-GRADE TÉCNICA GEOMÉTRICA milimétrica em azul técnico #072036. "
            "No topo: Pequeno badge pill com ícone em Dourado Kav: '📈 Quer crescer?'. "
            "No centro: Headline em tipografia Gotham em Sentence Case (tamanho contido, não estrondoso) com seta inclinada '↘'. "
            "Na base: Nuvem elegante de palavras-chave da Kav ('Tráfego Local · Performance · PMEs · Geofencing · Conversão · WhatsApp · ROI · Escala'). "
            "PROIBIDO PRETO PURO. PROIBIDO 'Arrasta pra entender'."
        ),
    },
]

SYSTEM_COPY_KAV = """Você é a Redatora Sênior & Copywriter da Kav (@kav.mkt).
Sua missão é escrever o conteúdo visual e a legenda completa para um post estático de Instagram da Kav,
formatado sob medida para o ARQUÉTIPO DE LAYOUT selecionado e garantindo variedade com base no histórico recente de 120 dias (4 meses).

DIRETRIZES DE MARCA DA KAV:
__SKILL__

PADRÃO DE LEGENDA DA KAV:
__PADRAO_LEGENDA__

ARQUÉTIPO DE LAYOUT ESCOLHIDO: __NOME_ESTILO__
TEMA DO LAYOUT: __TEMA_LAYOUT__
__INSTRUCAO_COPY__

__BACKUP_HISTORICO__

REGRAS RÍGIDAS DE COPYWRITING:
0. OBRIGATÓRIO: Use SEMPRE Sentence Case (primeira letra maiúscula e o resto em minúsculas normais, ex: 'Você não precisa abaixar o seu preço', 'Improviso não constrói empresa'). PROIBIDO CAIXA ALTA / ALL CAPS!
1. TAMANHO CONTIDO (ESTILO FOCUS): As chamadas devem ser enxutas, elegantes e concisas (3 a 6 palavras). Não sobrecarregue com textos longos.
2. NUNCA use termos de carrossel como 'Arrasta pra entender', 'Arraste para o lado' ou setas duplas (>>). Todos os posts da Kav são peças estáticas individuais de feed.
3. HEADLINE DA IMAGEM: Curta, magnética, de 3 a 6 palavras. Deve parar imediatamente o scroll do empresário de PME.
   Foque na dor real do negócio local (atrair clientes na região, mensagens no WhatsApp, parar de queimar verba no botão impulsionar).
   NUNCA escreva a palavra 'Kav', 'Cave' ou o nome da agência na headline da imagem — a chamada deve focar no cliente e no negócio dele.
4. DESTAQUE DOURADO: Indique 1 a 2 palavras que devem receber o Dourado Kav (#EEB730) para quebra de padrão visual.
5. ADAPTAÇÃO AO FORMATO: Preencha com rigor os campos estruturais do arquétipo solicitado.
6. LEGENDA DO POST:
   - Gancho provocativo na 1ª linha.
   - 2 a 3 parágrafos objetivos explicando o conceito com analogia simples do comércio/serviço.
   - Chamada para ação (CTA) convidando para enviar um direct.
   - Hashtags oficiais da agência.

Responda APENAS com um objeto JSON:
{
  "headline_imagem": "Headline afiada em Gotham Sentence Case (ex: 'Você não precisa abaixar o seu preço')",
  "destaque_dourado": "Palavra central em dourado",
  "headline_apoio": "Frase de apoio complementar de 1 linha em Sentence Case",
  "texto_card": "Texto para dentro do card (se aplicável ao formato)",
  "descricao_layout": "Resumo em 1 linha da estrutura visual gerada para este post",
  "legenda": "Legenda completa formatada"
}
"""

SYSTEM_DESIGN_KAV = """You are the Senior Art Director of Kav (@kav.mkt), a premier digital performance marketing agency.
Your task is to write a comprehensive, professional graphic design brief for a single static Instagram feed post (Vertical 4:5 ratio, 1080x1350).

DEFINITIVE BRAND IDENTITY & KEY VISUAL:
1. TYPOGRAPHY SCALE & RESTRAINED ELEGANCE (FOCUS REFERENCE BENCHMARK):
   - Primary Font: STRICTLY Gotham (clean, geometric, modern neo-grotesque).
   - STRICT PROHIBITION: NO ALL CAPS! All text, headlines, and callouts MUST be rendered in elegant, modern Sentence Case (natural capitalization like 'Você não precisa abaixar o seu preço', 'Improviso não constrói empresa'). NEVER shout in uppercase!
   - STRICT FONT SIZE RESTRAINT: Do NOT make headlines massive, colossal, or screen-dominating. Follow the exact font proportions of the FOCUS reference layout:
     * Moderate, restrained headline size (occupying approximately 55% to 65% of canvas width, leaving at least 20-25% breathing margins on the left and right sides).
     * Headline Weight: Gotham Medium or Bold (NOT ultra-heavy black).
     * Subtitles/Cards: Book or Regular (400), airy and perfectly legible.
     * Generous negative space (breathing room) around the top logo, central headline, and bottom CTA pill.
2. COLOR PALETTE & THEME DIVERSITY:
   - Current Target Theme: __TEMA_LAYOUT__
   - If DARK THEME: Deep nocturnal navy background (#001424 or #001D32). PROHIBITED PURE BLACK (#000000). Highlights in Kav Gold (#EEB730). Primary text in Pure White (#FFFFFF).
   - If LIGHT INVERTED THEME: Pure White (#FFFFFF) at the top with a subtle, ultra-soft gradient transitioning gently into a very faint bluish-gray (#EBF1F6 / #F0F4F8) at the bottom. Primary text in Deep Nocturnal Navy (#001424). Highlights in Kav Gold (#EEB730 / #D99B00) with thin gold underline. Secondary text in Slate Gray (#475569).
3. ABSOLUTE LOGO PROPORTION & ZERO-DISTORTION MANDATE:
   - Reference image 2 is the official brand logo of Kav Marketing & Performance ('KAV').
   - You MUST faithfully incorporate this exact logo into the composition with 100% geometric fidelity.
   - ABSOLUTE PROHIBITION ON DISTORTION: NEVER stretch, squash, slant, skew, warp, or alter the horizontal/vertical aspect ratio of the logo. Keep strict 1:1 aspect ratio lock.
   - NEVER misspell the letters (strictly 'KAV', never 'WAV', 'CAV', or warped glyphs).
   - Position the logo in the __AREA_LOGO__ with generous breathing room (at least 60-80px safe padding from any canvas edge or text element).
   - NEVER allow the logo to touch, collide with, or overlap any headlines or text cards!
4. STRICT PROHIBITIONS:
   - NO CAROUSEL / SWIPE TEXT: ABSOLUTELY NEVER write 'Arrasta pra entender', 'Arraste para o lado', or draw swipe buttons. This is a single static feed post!
   - NO TOP BADGE: DO NOT render any box or pill at the top saying 'PERFORMANCE LOCAL'. Keep the top clean.
   - ABSOLUTELY NO generic 3D miniature city maps, radar grids, or yellow GPS pins!

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
    """Localiza o arquivo de logotipo da Kav e determina a versão correta (fundo claro ou escuro)."""
    referencia = referencia or {}
    estilo = obter_estilo_kav(referencia)
    posicao = estilo.get("posicao_logo") or referencia.get("posicao_logo") or cliente.get("config", {}).get("logo_posicao", "superior-centro")

    if isinstance(posicao, str):
        posicao = posicao.replace("_", "-")
    else:
        posicao = "superior-centro"

    tema = estilo.get("tema", "escuro")
    pasta_cliente = Path(__file__).resolve().parent.parent / "clientes" / cliente.get("slug", "kav")

    if tema == "claro":
        candidatos = [
            pasta_cliente / "logo" / "logo-fundo-claro.png",
            pasta_cliente / "logo-fundo-claro.png",
            pasta_cliente / "logos" / "logo-fundo-claro.png",
            pasta_cliente / "logo" / "logo_kav.png",
        ]
    else:
        candidatos = [
            pasta_cliente / "logo" / "logo-fundo-escuro.png",
            pasta_cliente / "logo-fundo-escuro.png",
            pasta_cliente / "logos" / "logo-fundo-escuro.png",
            pasta_cliente / "logo" / "logo_kav.png",
        ]

    arquivo = None
    for c in candidatos:
        if c.exists():
            arquivo = c
            break

    if not arquivo:
        from utils import gerador_referencias
        esc, cla = gerador_referencias.garantir_logo_kav(pasta_cliente)
        arquivo = cla if tema == "claro" else esc

    return (Path(arquivo) if arquivo and Path(arquivo).exists() else None, posicao)


def gerar_copy_kav(pauta: dict, cliente: dict, estilo: Optional[dict] = None) -> dict:
    """Gera os textos do post estático da Kav adaptados ao arquétipo visual e ao histórico de 120 dias."""
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
- Subtítulo sugerido: {pauta.get('subtitulo_apoio', '')}
- CTA sugerido: {pauta.get('cta', 'Mande um direct')}

ATENÇÃO OBRIGATÓRIA: Escreva a copy formatada para o arquétipo '{estilo['nome']}' ({estilo.get('tema')}) usando estritamente Sentence Case (primeira letra maiúscula, NUNCA ALL CAPS) com tamanho contido estilo Focus. Varie a tese para não repetir as peças anteriores dos últimos 120 dias."""
    )

    try:
        resposta = chamar_ia(system=system, prompt=prompt, max_tokens=850, temperature=0.75, json_mode=True)
        dados = extrair_json(resposta)
    except Exception:
        dados = {
            "headline_imagem": pauta.get("headline_sugerida", "Você não precisa abaixar o seu preço."),
            "destaque_dourado": "abaixar o seu preço",
            "headline_apoio": pauta.get("subtitulo_apoio", "Posicionamento e tráfego certo atraem quem valoriza seu serviço."),
            "descricao_layout": estilo.get("descricao_layout", "Composição tipográfica em Gotham Sentence case"),
            "legenda": "Legenda padrão da Kav para o post de teste.",
        }

    headline = dados.get("headline_imagem", "")
    headline = re.sub(r"\\b(KAV|CAVE|WAV)\\b", "", headline, flags=re.IGNORECASE).strip()
    dados["headline_imagem"] = headline
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
    """Monta o briefing em inglês para a IA com contenção de fontes, paleta adequada e zero distorção de logo."""
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
        f"Chosen Layout Archetype: {estilo['nome']} (ID: {estilo['id']}, Theme: {estilo.get('tema')})",
        f"Topic: {pauta.get('tema')}",
        "MANDATORY ARCHETYPE DIRECTIVE: " + estilo["diretriz_cena"],
        f'Main Headline to render: "{copy.get("headline_imagem")}"',
        f'Kav Gold Highlight Term: "{copy.get("destaque_dourado", "")}"',
        "STRICT TYPOGRAPHY: Gotham font ONLY in elegant Sentence Case (NO ALL CAPS).",
        "STRICT FONT SIZE RESTRAINT: Emulate the exact proportions of the FOCUS reference layout. The headline MUST NOT be massive or screen-filling. Keep it restrained and moderate (~55% width, with 20-25% breathing margins on both sides).",
        f"STRICT COLOR PALETTE: Background must be {estilo.get('cor_fundo')}. Highlights in Kav Gold ({estilo.get('cor_destaque')}). Texts in {estilo.get('cor_texto')}.",
    ]

    if copy.get("texto_card"):
        partes.append(f'Card Body Text: "{copy.get("texto_card")}"')
    if copy.get("headline_apoio"):
        partes.append(f'Support Text: "{copy.get("headline_apoio")}"')

    partes.extend([
        (
            "STRICT REFERENCE IMAGES INSTRUCTION: "
            "Reference image 1 is the brand layout template. Strictly follow its structure, spacing, and hierarchy. "
            f"Reference image 2 is the official Kav brand logo ('KAV'). Faithfully reproduce this exact logo into the {area_logo} with safe margins and breathing room. "
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
                "Emulate this exact graphic design structure, typography hierarchy in restrained Gotham Sentence case, and breathing space balance."
            ),
        ))

    # 2. Referência 2: Logotipo Oficial da Kav (Versão clara ou escura de acordo com o tema)
    logo_arquivo, posicao_logo = _logo_kav(cliente, referencia)
    area_logo = AREAS_LOGO.get(posicao_logo, "header area")

    if logo_arquivo and logo_arquivo.exists():
        referencias_imagem.append((
            logo_arquivo.read_bytes(),
            (
                "Reference 2: The OFFICIAL BRAND LOGO of Kav Marketing & Performance ('KAV'). "
                "You MUST faithfully incorporate this exact logo into the layout. "
                f"Position it cleanly in the {area_logo} with generous margins and breathing room. "
                "CRITICAL ZERO-DISTORTION MANDATE: DO NOT stretch, squash, skew, or distort the logo! Keep strict 1:1 aspect ratio. "
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
        "- TYPOGRAPHY: STRICTLY use Gotham font. STRICT PROHIBITION: NO ALL CAPS! All headlines and copy must be in elegant Sentence Case (e.g. 'Você não precisa abaixar o seu preço').",
        "- FONT SIZE RESTRAINT (FOCUS BENCHMARK): The headline must NOT be oversized or monstrous. Maintain moderate, restrained proportions (~55% to 65% canvas width with 20-25% breathing margins on the sides).",
        f"- COLOR PALETTE: Background must be {estilo.get('cor_fundo')}. Highlights in Kav Gold ({estilo.get('cor_destaque')}). Texts in {estilo.get('cor_texto')}.",
        "- LOGO INTEGRATION & ZERO DISTORTION: Reproduce the official Kav logo from Reference 2 cleanly in its designated branding zone with generous margins. ZERO DISTORTION: Never stretch, squash, or warp the logo! Maintain strict 1:1 aspect ratio.",
        "- NO TOP BADGES: DO NOT draw any box or tag at the top saying 'PERFORMANCE LOCAL'. Keep the top clean.",
        "- NO CAROUSEL / SWIPE TEXT: ABSOLUTELY DO NOT write 'Arrasta pra entender', 'Arraste para o lado', or draw swipe buttons. This is a single static feed post (1080x1350).",
    ]
    if backup_historico:
        partes.append("RECENT POSTS HISTORY (MAKE THIS DESIGN NOTICEABLY DIFFERENT FROM THESE):\n" + backup_historico)

    for i, desc in enumerate(descricoes):
        partes.append(f"Input Reference Image {i + 1}: {desc}")
    partes.append("Art Direction Brief:\n" + brief)
    return "\n\n".join(partes)
