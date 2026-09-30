"""Agente de Criação de Post Estático da Kav (@kav.mkt).

Gera posts estáticos únicos de altíssimo impacto para o feed da própria agência,
com foco em Tráfego Pago Local para PMEs e Marketing Descomplicado.
Segue com fidelidade as referências oficiais da marca com:
- Fonte Gotham em Sentence Case (sempre sem caixa alta / sem gritar em maiúsculas);
- Cores nobres da Kav (Azul Marinho Noturno Profundo #001424 / #001D32 e Dourado Kav #EEB730 - PROIBIDO preto puro);
- Envio obrigatório de AMBAS as referências visuais para a IA (Template de Layout + Logotipo Oficial da Kav);
- Backup Inteligente de Layouts: histórico descritivo injetado no prompt informando à IA as cores e estruturas
  das peças recentes para garantir variedade contínua e um feed extremamente versátil.
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
        "id": "afirmacao_tweet_box",
        "arquivo_referencia": "ref_afirmacao_tweet_box.png",
        "nome": "Tweet Box de Autoridade (Estilo Samuel Reis)",
        "posicao_logo": "superior-esquerdo",
        "cor_fundo": "Azul Marinho Noturno Profundo (#001424)",
        "cor_destaque": "Dourado Kav Solar (#EEB730)",
        "cor_texto": "Branco Puro (#FFFFFF) e Cinza Slate (#94A3B8)",
        "descricao_layout": "Card retangular flutuante escuro (#031E34) no centro com perfil @kav.mkt, tese reflexiva e suporte em card",
        "instrucao_copy": "\n".join([
            "ESTRUTURA DA COPY PARA ARQUÉTIPO TWEET BOX:",
            "- headline_imagem: Frase afiada e reflexiva em Sentence Case (ex: 'Não é trabalho do seu cliente se lembrar de você.').",
            "- texto_card: Frase de suporte elegante em Sentence Case para o interior do card (ex: 'É obrigação da sua empresa aparecer todos os dias.').",
            "- destaque_dourado: 1 termo chave para brilhar em Dourado Kav.",
            "- cta_card: 'Leia a legenda completa ↘'",
        ]),
        "diretriz_cena": (
            "ARQUÉTIPO VISUAL: CARD FLUTUANTE DE REDE SOCIAL (ESTILO SAMUEL REIS / TWEET BOX). "
            "No centro da tela, renderize um elegante CARD RETANGULAR FLUTUANTE em tom azul noturno escuro (#031E34) "
            "com cantos suavemente arredondados e borda sutil translúcida (#123452). "
            "Topo do card: badge de perfil com pequeno avatar circular com 'K' dourado, nome 'Kav Marketing' e handle '@kav.mkt'. "
            "Corpo do card: tese de autoridade em tipografia Gotham em Sentence Case (apenas a inicial maiúscula, NUNCA em caixa alta). "
            "Caixa interna de apoio: card menor translúcido com texto explicativo. "
            "Rodapé interno: chamada sutil 'Leia a legenda ↘' com seta em Dourado Kav (#EEB730). "
            "Fundo da imagem: Azul Marinho Noturno Profundo (#001424) com leve iluminação central. "
            "PROIBIÇÃO RIGOROSA: PROIBIDO PRETO PURO (#000000). Use a paleta azul noturno da Kav. "
            "PROIBIÇÃO RIGOROSA: PROIBIDO CAIXA ALTA (ALL CAPS). Use Gotham em Sentence Case. "
            "PROIBIÇÃO RIGOROSA: NUNCA escreva 'Arrasta pra entender'. "
            "PROIBIDO caixas de 'PERFORMANCE LOCAL' no topo."
        ),
    },
    {
        "id": "destaque_dourado",
        "arquivo_referencia": "ref_destaque_dourado.png",
        "nome": "Metáfora Visual 3D / Objeto de Destaque (Estilo Well.dsg & ORB)",
        "posicao_logo": "superior-centro",
        "cor_fundo": "Azul Petróleo Escuro (#001424 a #001D32)",
        "cor_destaque": "Dourado Kav Solar (#EEB730) no objeto herói",
        "cor_texto": "Branco Puro (#FFFFFF) e Cinza Slate (#94A3B8)",
        "descricao_layout": "Objeto físico 3D central em Dourado Kav como metáfora de destaque, com textos divididos no topo e na base em Sentence case",
        "instrucao_copy": "\n".join([
            "ESTRUTURA DA COPY PARA ARQUÉTIPO METÁFORA VISUAL 3D:",
            "- headline_imagem: Frase superior de abertura em Gotham Sentence Case (ex: 'Você não precisa fazer igual. Nem pensar igual.').",
            "- headline_apoio: Frase inferior de fechamento em Gotham Sentence Case (ex: 'Faça diferente. Seja estratégico.').",
            "- subtitulo: Frase curta reflexiva (ex: 'O marketing que copia, some.').",
            "- destaque_dourado: O objeto central herói da cena.",
        ]),
        "diretriz_cena": (
            "ARQUÉTIPO VISUAL: OBJETO FÍSICO 3D DE DESTAQUE CENTRAL (ESTILO WELL.DSG / ORB / CADEIRA LARANJA). "
            "No centro da cena, renderize um OBJETO FÍSICO 3D REALISTA ISOLADO E IMPACTANTE que represente a metáfora do tema "
            "(exemplo: uma elegante cadeira de design moderno em Dourado Kav brilhante #EEB730 posicionada no meio de cadeiras escuras, "
            "ou um holofote iluminando um ponto único, ou uma bússola dourada minimalista). "
            "Metade superior: Frase reflexiva de abertura em tipografia Gotham em Sentence Case (sem caixa alta). "
            "Metade inferior: Frase de conclusão impactante em tipografia Gotham branca pura e cinza slate. "
            "Rodapé: Linha divisória fina com '@kav.mkt' na esquerda e ano na direita. "
            "Fundo: Gradiente rico Azul Marinho Noturno Profundo (#001424 para #000E1A com iluminação focal no objeto dourado). "
            "PROIBIÇÃO RIGOROSA: PROIBIDO PRETO PURO (#000000). Use a paleta azul da Kav. "
            "PROIBIÇÃO RIGOROSA: PROIBIDO CAIXA ALTA (ALL CAPS). Use Gotham em Sentence Case. "
            "PROIBIÇÃO RIGOROSA: NUNCA escreva 'Arrasta pra entender'."
        ),
    },
    {
        "id": "manifesto_palavra_dourada",
        "arquivo_referencia": "ref_manifesto_palavra_dourada.png",
        "nome": "Manifesto Editorial (Estilo Focus)",
        "posicao_logo": "topo-centro",
        "cor_fundo": "Azul Marinho Noturno Profundo (#001424)",
        "cor_destaque": "Dourado Kav (#EEB730) na palavra central sublinhada",
        "cor_texto": "Branco Puro (#FFFFFF) e Cinza Metálico (#94A3B8)",
        "descricao_layout": "Composição 100% tipográfica monumental em Gotham Sentence case, com palavra central em Dourado Kav e traço de destaque",
        "instrucao_copy": "\n".join([
            "ESTRUTURA DA COPY PARA ARQUÉTIPO MANIFESTO EDITORIAL:",
            "- headline_imagem: Frase monumental de 3 a 5 palavras em Gotham Sentence Case (ex: 'Improviso não constrói empresa.').",
            "- destaque_dourado: 1 a 2 palavras centrais em Dourado Kav que recebem o traço sublinhado (ex: 'não constrói').",
            "- headline_apoio: Frase curta de apoio reflexivo em Sentence Case.",
            "- cta_pill: '→ Leia a legenda'",
        ]),
        "diretriz_cena": (
            "ARQUÉTIPO VISUAL: MANIFESTO EDITORIAL MINIMALISTA MONUMENTAL (ESTILO FOCUS). "
            "A arte é estritamente tipográfica, imponente e limpa. "
            "No topo centro: Logotipo oficial da Kav perfeitamente nítido e proporcionado com respiro. "
            "No centro: Headline forte em tipografia Gotham em Sentence Case (primeira letra maiúscula, NÃO em caixa alta), "
            "com a palavra central destacada em Dourado Kav (#EEB730) acompanhada de um traço fino elegante dourado sublinhado. "
            "Abaixo da headline: botão pill fino arredondado minimalista contendo estritamente '[ →  Leia a legenda ]'. "
            "Fundo: Gradiente nobre Azul Marinho Noturno Profundo (#001424). "
            "PROIBIÇÃO RIGOROSA: PROIBIDO PRETO PURO (#000000). "
            "PROIBIÇÃO RIGOROSA: PROIBIDO CAIXA ALTA (ALL CAPS). Use Gotham em Sentence Case. "
            "PROIBIÇÃO RIGOROSA: NUNCA escreva 'Arrasta pra entender'. Topo limpo sem caixas de 'PERFORMANCE LOCAL'."
        ),
    },
    {
        "id": "impacto_condensado_grid",
        "arquivo_referencia": "ref_impacto_condensado_grid.png",
        "nome": "Grid Técnico Blueprint (Estilo Agencia Workspace)",
        "posicao_logo": "superior-direito",
        "cor_fundo": "Azul Marinho com Micro-Grid Blueprint (#001424 / linhas em #072036)",
        "cor_destaque": "Dourado Kav Solar (#EEB730)",
        "cor_texto": "Branco Puro (#FFFFFF) e Nuvem Cinza Muted (#505F7D)",
        "descricao_layout": "Fundo com micro-grade técnica blueprint, badge de tendência, headline maciça em Gotham e nuvem de dados de performance",
        "instrucao_copy": "\n".join([
            "ESTRUTURA DA COPY PARA ARQUÉTIPO GRID TÉCNICO WORKSPACE:",
            "- tag_topo: '📈 Quer crescer?'",
            "- headline_imagem: Frase de impacto direto em Gotham (ex: 'Então pare de tratar marketing como um gasto! ↘').",
            "- termos_performance: Nuvem de termos técnicos de performance local separados por pontos.",
            "- destaque_dourado: Termo chave em Dourado Kav.",
        ]),
        "diretriz_cena": (
            "ARQUÉTIPO VISUAL: BLUEPRINT TÉCNICO & DADOS DE PERFORMANCE (ESTILO AGENCIA WORKSPACE). "
            "Fundo: Superfície Azul Marinho Profunda (#001424) com uma MICRO-GRADE TÉCNICA GEOMÉTRICA nítida e sutil "
            "(linhas vetoriais milimétricas em azul técnico #072036 formando um blueprint de coordenadas de tráfego local). "
            "No topo: Pequeno badge pill escuro com ícone de gráfico em Dourado Kav: '📈 Quer crescer?'. "
            "No centro: Headline maciça em tipografia Gotham com forte peso visual e seta inclinada '↘'. "
            "Na base da imagem: Nuvem densa e elegante de palavras-chave da agência Kav separadas por pontos e traços "
            "('Tráfego Local · Performance · PMEs · Geofencing · Conversão · WhatsApp · ROI · Escala') em cinza azulado sutil. "
            "PROIBIÇÃO RIGOROSA: PROIBIDO PRETO PURO (#000000). Use o azul marinho técnico da Kav. "
            "PROIBIÇÃO RIGOROSA: NUNCA escreva 'Arrasta pra entender'."
        ),
    },
    {
        "id": "quebra_objecao_card",
        "arquivo_referencia": "ref_quebra_objecao_card.png",
        "nome": "Quebra de Objeção / Tensão de Valor (Estilo Geovane Rocha)",
        "posicao_logo": "superior-esquerdo",
        "cor_fundo": "Azul Noturno Profundo (#001424)",
        "cor_destaque": "Dourado Kav (#EEB730) no card da virada de chave",
        "cor_texto": "Branco Puro (#FFFFFF) e Cinza Slate (#94A3B8)",
        "descricao_layout": "Headline afiada em Gotham Sentence case, elemento visual de valor e card contrastante com a virada do Método Kav",
        "instrucao_copy": "\n".join([
            "ESTRUTURA DA COPY PARA ARQUÉTIPO QUEBRA DE OBJEÇÃO (GEOVANE ROCHA):",
            "- headline_imagem: Frase provocativa de quebra de objeção em Gotham Sentence Case (ex: 'Você não precisa abaixar o seu preço.').",
            "- texto_card: Tese de sustentação da Kav (ex: 'Preço baixo atrai cliente difícil. Posicionamento e tráfego certo atraem quem valoriza seu serviço.').",
            "- cta_pill: '→ Leia a legenda'",
            "- destaque_dourado: 1 termo da virada em Dourado Kav.",
        ]),
        "diretriz_cena": (
            "ARQUÉTIPO VISUAL: QUEBRA DE OBJEÇÃO COM ELEMENTO DE VALOR (ESTILO GEOVANE ROCHA). "
            "Topo: Badge sutil de perfil com avatar e identificação '@kav.mkt'. "
            "Corpo superior: Grande headline afiada em tipografia Gotham em Sentence Case (apenas a inicial maiúscula, ex: 'Você não precisa abaixar o seu preço'). "
            "Corpo inferior: Card retangular elegante em azul escuro (#031E34) com borda nítida em Dourado Kav (#EEB730) "
            "apresentando a tese de sustentação da agência Kav em tipografia branca limpa. "
            "Abaixo do card: botão pill fino '[ →  Leia a legenda ]'. "
            "Fundo: Azul Marinho Noturno Profundo (#001424) com iluminação difusa sutil. "
            "PROIBIÇÃO RIGOROSA: PROIBIDO PRETO PURO (#000000). "
            "PROIBIÇÃO RIGOROSA: PROIBIDO CAIXA ALTA (ALL CAPS). Use Gotham em Sentence Case. "
            "PROIBIÇÃO RIGOROSA: NUNCA escreva 'Arrasta pra entender'. É uma peça estática de feed único!"
        ),
    },
]

SYSTEM_COPY_KAV = """Você é a Redatora Sênior & Copywriter da Kav (@kav.mkt).
Sua missão é escrever o conteúdo visual e a legenda completa para um post estático de Instagram da Kav,
formatado sob medida para o ARQUÉTIPO DE LAYOUT selecionado e garantindo variedade com base no histórico recente.

DIRETRIZES DE MARCA DA KAV:
__SKILL__

PADRÃO DE LEGENDA DA KAV:
__PADRAO_LEGENDA__

ARQUÉTIPO DE LAYOUT ESCOLHIDO: __NOME_ESTILO__
__INSTRUCAO_COPY__

__BACKUP_HISTORICO__

REGRAS RÍGIDAS DE COPYWRITING:
0. OBRIGATÓRIO: Use SEMPRE Sentence Case (primeira letra maiúscula e o resto em minúsculas normais, ex: 'Você não precisa abaixar o seu preço', 'Improviso não constrói empresa'). PROIBIDO CAIXA ALTA / ALL CAPS!
1. NUNCA use termos de carrossel como "Arrasta pra entender", "Arraste para o lado" ou setas duplas (>>). Todos os posts da Kav são peças estáticas individuais de feed.
2. HEADLINE DA IMAGEM: Curta, magnética, de 3 a 7 palavras. Deve parar imediatamente o scroll do empresário de PME.
   Foque na dor real do negócio local (atrair clientes na região, mensagens no WhatsApp, parar de queimar verba no botão impulsionar).
   NUNCA escreva a palavra "Kav", "Cave" ou o nome da agência na headline da imagem — a chamada deve focar no cliente e no negócio dele.
3. DESTAQUE DOURADO: Indique 1 a 2 palavras que devem receber o Dourado Kav (#EEB730) para quebra de padrão visual.
4. ADAPTAÇÃO AO FORMATO: Preencha com rigor os campos estruturais do arquétipo solicitado.
5. LEGENDA DO POST:
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
1. DEFINITIVE TYPOGRAPHY:
   - Primary Font: STRICTLY Gotham (clean, geometric, modern neo-grotesque).
   - STRICT PROHIBITION: NO ALL CAPS! All text, headlines, and callouts MUST be rendered in elegant, modern Sentence Case (natural capitalization like 'Você não precisa abaixar o seu preço', 'Improviso não constrói empresa'). NEVER shout in uppercase!
   - Headline Weight: Bold or Medium Gotham, clean, sophisticated, punchy.
   - Subtitle/Card Weight: Book or Regular (400), perfectly legible.
2. DEFINITIVE COLOR PALETTE (OFFICIAL KAV BRAND COLORS):
   - STRICT PROHIBITION: The background MUST NOT be pure black (#000000).
   - Background: Deep nocturnal navy / petroleum blue (#001424 and #001D32) with soft radial illumination or subtle blueprint grid.
   - Accent & Highlight: Exclusively Kav Gold / Solar Amber (#EEB730). Used for highlighted words, subtle underline accents, CTA arrows (↘, →), or hero 3D objects.
   - Primary Text: Crisp pure white (#FFFFFF) for absolute contrast and readability on dark screens.
   - Secondary Text: Metallic Slate Gray (#94A3B8).
   - Card containers: Dark nocturnal card (#031E34) with thin subtle stroke borders (#123452).
3. REFERENCE IMAGES SUPPLIED:
   - Reference image 1 is the chosen brand layout reference template. Strictly follow its composition, visual layout, and graphic hierarchy.
   - Reference image 2 is the official brand logo of Kav Marketing & Performance ('KAV'). Seamlessly incorporate this exact logo into the composition with dedicated breathing room and safe margins in the __AREA_LOGO__.
4. STRICT PROHIBITIONS:
   - NO CAROUSEL / SWIPE TEXT: ABSOLUTELY NEVER write 'Arrasta pra entender', 'Arraste para o lado', or draw swipe buttons. This is a single static feed post!
   - NO TOP BADGE: DO NOT render any box or pill at the top saying 'PERFORMANCE LOCAL'.
   - NO TEXT OVERLAP: The Kav logo must NEVER overlap or collide with the headline or text cards.
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
    """Localiza o arquivo de logotipo da Kav e determina a posição correta no layout."""
    referencia = referencia or {}
    estilo = obter_estilo_kav(referencia)
    posicao = estilo.get("posicao_logo") or referencia.get("posicao_logo") or cliente.get("config", {}).get("logo_posicao", "superior-centro")

    if isinstance(posicao, str):
        posicao = posicao.replace("_", "-")
    else:
        posicao = "superior-centro"

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
            pasta_cliente / "logo-fundo-escuro.png",
            pasta_cliente / "logo" / "logo-fundo-escuro.png",
            pasta_cliente / "logo" / "logo_kav.png",
            pasta_cliente / "logo" / "logo.png",
            pasta_cliente / "logos" / "logo-fundo-escuro.png",
            pasta_cliente / "logos" / "logo.png",
            pasta_cliente / "logo.png",
            pasta_cliente / "logo-fundo-claro.png",
        ]
        for c in candidatos:
            if c.exists():
                arquivo = c
                break

    return (Path(arquivo) if arquivo and Path(arquivo).exists() else None, posicao)


def gerar_copy_kav(pauta: dict, cliente: dict, estilo: Optional[dict] = None) -> dict:
    """Gera os textos do post estático da Kav adaptados ao arquétipo visual e ao histórico recente."""
    estilo = estilo or ESTILOS_LAYOUT_KAV[0]
    skill = cliente.get("skill", "")
    padrao = cliente.get("legenda_padrao", "") or "(Padrão Kav: gancho, explicação prática para PME, CTA no direct, hashtags)"
    backup_historico = historico.obter_backup_historico_layouts("kav", limite=4)

    system = (
        SYSTEM_COPY_KAV.replace("__SKILL__", skill)
        .replace("__PADRAO_LEGENDA__", padrao)
        .replace("__NOME_ESTILO__", estilo["nome"])
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

ATENÇÃO OBRIGATÓRIA: Escreva a copy formatada para o arquétipo '{estilo['nome']}' usando estritamente Sentence Case (primeira letra maiúscula, NUNCA ALL CAPS). Varie a tese para não repetir as peças anteriores do histórico."""
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
    headline = re.sub(r"\b(KAV|CAVE|WAV)\b", "", headline, flags=re.IGNORECASE).strip()
    dados["headline_imagem"] = headline
    dados["estilo_layout"] = estilo["id"]
    dados["estilo_nome"] = estilo["nome"]
    dados["descricao_layout"] = estilo.get("descricao_layout", "")
    dados["cor_fundo"] = estilo.get("cor_fundo", "Azul Marinho Noturno Profundo (#001424)")
    dados["cor_destaque"] = estilo.get("cor_destaque", "Dourado Kav (#EEB730)")
    dados["cor_texto"] = estilo.get("cor_texto", "Branco Puro e Cinza Slate")
    dados["posicao_logo"] = estilo.get("posicao_logo", "superior-centro")

    return dados


def gerar_brief_arte_kav(
    copy: dict, pauta: dict, cliente: dict, referencia: Optional[dict], estilo: Optional[dict] = None
) -> tuple[str, dict]:
    """Monta o briefing em inglês para a IA de geração de imagem com diretrizes de Gotham, paleta Kav e histórico recente."""
    estilo = estilo or obter_estilo_kav(referencia)
    posicao_logo = estilo.get("posicao_logo", "superior-centro")
    area_logo = AREAS_LOGO.get(posicao_logo, "header area")
    backup_historico = historico.obter_backup_historico_layouts("kav", limite=4)

    system = (
        SYSTEM_DESIGN_KAV.replace("__NOME_ESTILO__", estilo["nome"])
        .replace("__DIRETRIZ_CENA__", estilo["diretriz_cena"])
        .replace("__AREA_LOGO__", area_logo)
        .replace("__BACKUP_HISTORICO__", backup_historico)
    )

    partes = [
        f"Chosen Layout Archetype: {estilo['nome']} (ID: {estilo['id']})",
        f"Topic: {pauta.get('tema')}",
        "MANDATORY ARCHETYPE DIRECTIVE: " + estilo["diretriz_cena"],
        f'Main Headline to render: "{copy.get("headline_imagem")}"',
        f'Kav Gold Highlight Term: "{copy.get("destaque_dourado", "")}"',
        "STRICT TYPOGRAPHY: Gotham font ONLY. MUST BE in elegant Sentence Case (natural casing, NO ALL CAPS).",
        f"STRICT COLOR PALETTE: Deep nocturnal navy background ({estilo.get('cor_fundo')}). PROHIBITED PURE BLACK (#000000). Highlight with Kav Gold ({estilo.get('cor_destaque')}).",
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
            "DO NOT allow the logo to touch or collide with any text!"
        ),
        (
            "STRICT ANTI-CAROUSEL MANDATE: "
            "NEVER write 'Arrasta pra entender', 'Arraste para o lado' or draw swipe buttons. "
            "This is a single static feed post (1080x1350)!"
        ),
        (
            "STRICT FEED DIVERSITY MANDATE: "
            "Review the recent posts history above and make this layout noticeably unique and refreshing for the Instagram feed."
        ),
    ])

    brief_gerado = chamar_ia(system=system, prompt="\n".join(partes), max_tokens=750, temperature=0.7)
    return brief_gerado, estilo


def gerar_imagem_estatica_kav(
    brief: str, cliente: dict, referencia: Optional[dict], estilo: Optional[dict] = None
) -> dict:
    """Gera a imagem estática 4:5 enviando OBRIGATORIAMENTE o Template de Layout E o Logotipo Oficial como referências de imagem."""
    estilo = estilo or obter_estilo_kav(referencia)
    referencias_imagem = []

    # 1. Referência 1: Template de Layout do arquétipo sorteado
    if referencia and referencia.get("arquivo") and referencia["arquivo"].exists():
        referencias_imagem.append((
            referencia["arquivo"].read_bytes(),
            (
                f"Reference 1: The brand layout design reference template for archetype '{estilo['nome']}'. "
                "Emulate this exact graphic design structure, typography hierarchy in Gotham Sentence case, and spacing balance. "
                "The background must be deep nocturnal navy (#001424), NOT pure black."
            ),
        ))

    # 2. Referência 2: Logotipo Oficial da Kav (OBRIGATÓRIO)
    logo_arquivo, posicao_logo = _logo_kav(cliente, referencia)
    area_logo = AREAS_LOGO.get(posicao_logo, "header area")

    if logo_arquivo and logo_arquivo.exists():
        referencias_imagem.append((
            logo_arquivo.read_bytes(),
            (
                "Reference 2: The OFFICIAL BRAND LOGO of Kav Marketing & Performance ('KAV'). "
                "You MUST faithfully incorporate this exact logo (precise geometric typography 'KAV') into the layout. "
                f"Position it cleanly in the {area_logo} with generous margins and breathing room. "
                "ABSOLUTE PROHIBITION: The logo MUST NEVER collide with, touch, or overlap any headlines or text cards!"
            ),
        ))

    backup_historico = historico.obter_backup_historico_layouts("kav", limite=3)

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
        "descricao_layout": estilo.get("descricao_layout"),
        "cor_fundo": estilo.get("cor_fundo"),
        "cor_destaque": estilo.get("cor_destaque"),
        "cor_texto": estilo.get("cor_texto"),
        "posicao_logo": estilo.get("posicao_logo"),
        "modelo": bruta.get("modelo"),
    }


def _montar_prompt_final(brief: str, descricoes: list, estilo: dict, backup_historico: str = "") -> str:
    partes = [
        f"TASK: High-authority static social media post design (1080x1350 vertical 4:5 ratio) for Kav Marketing & Performance in archetype '{estilo['nome']}'.",
        "MANDATORY EXECUTION DIRECTIVES:",
        f"- LAYOUT ARCHETYPE: Strictly emulate the visual structure of '{estilo['nome']}'.",
        f"- SPECIFIC SCENE REQUIREMENT: {estilo['diretriz_cena']}",
        "- TYPOGRAPHY: STRICTLY use Gotham font. STRICT PROHIBITION: NO ALL CAPS! All headlines and copy must be in elegant Sentence Case (e.g. 'Você não precisa abaixar o seu preço').",
        "- COLOR PALETTE: Background must be deep nocturnal navy (#001424 or #001D32). PROHIBITED PURE BLACK (#000000). Highlight with Kav Gold (#EEB730). Texts in Pure White (#FFFFFF) and Slate Gray (#94A3B8).",
        "- LOGO INTEGRATION: Reproduce the official Kav logo from Reference 2 cleanly in its designated branding zone with generous margins so it NEVER touches or overlaps any headline or text box.",
        "- NO TOP BADGES: DO NOT draw any box or tag at the top saying 'PERFORMANCE LOCAL'. Keep the top clean.",
        "- NO CAROUSEL / SWIPE TEXT: ABSOLUTELY DO NOT write 'Arrasta pra entender', 'Arraste para o lado', or draw swipe buttons. This is a single static feed post (1080x1350).",
        "- STRICT PROHIBITIONS: ABSOLUTELY NO generic 3D miniature city maps, radar grids, or yellow GPS pins!",
    ]
    if backup_historico:
        partes.append("RECENT POSTS HISTORY (MAKE THIS DESIGN NOTICEABLY DIFFERENT FROM THESE):\n" + backup_historico)

    for i, desc in enumerate(descricoes):
        partes.append(f"Input Reference Image {i + 1}: {desc}")
    partes.append("Art Direction Brief:\n" + brief)
    return "\n\n".join(partes)
