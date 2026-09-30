"""Agente Diretor de Arte (Otávio): inteligência de supervisão estética e refino de layout.

Atua como o supervisor e aprovador de arte da Kav (@kav.mkt).
Analisa visualmente (usando visão computacional multimodal) a imagem gerada pelo
designer para:
1. Posts da agência Kav (@kav.mkt) - feed estático de autoridade em marketing local;
2. Posts de restaurantes/fotos reais (N&N Restaurante) - preservação de comida real autêntica;
3. Peças de anúncio (campanha).

Se o layout tiver nota baixa (< 8) ou falhas críticas (ex: cópia cega de referências como cadeiras,
ausência de subtítulo ou excesso de texto, logo genérico em Arial), o Diretor de Arte
solicita melhorias cirúrgicas e devolve à API da OpenAI para refino imediato.
"""
from __future__ import annotations

import base64
from pathlib import Path
from typing import Callable, Optional

from utils import image_overlay, openai_client
from utils.openai_client import chamar_ia_visao, extrair_json

SYSTEM_PROMPT_DIRETOR_KAV = """Você é o Diretor de Arte Sênior da Kav (@kav.mkt).
Sua responsabilidade é avaliar com altíssimo rigor estético, olhar crítico de design e autoridade visual a peça estática de feed (Vertical 4:5, 1080x1350) criada pelo designer para a agência Kav.

DIRETRIZES DA MARCA DA KAV:
__SKILL__

CHECKLIST CRÍTICO DE AVALIAÇÃO DA KAV:
1. HIERARQUIA DE COPY EQUILIBRADA (HEADLINE + SUBTÍTULO DE CONTEXTO):
   - A arte DEVE conter duas camadas de texto balanceadas:
     * Headline imponente em destaque (3 a 6 palavras em Gotham Bold, Sentence Case);
     * Subtítulo curto de apoio e contexto (exatamente entre 8 e 14 palavras) logo abaixo da headline;
     * Botão pill '[ → Leia a legenda ]' na base.
   - REPROVE se a imagem contiver parágrafos longos, blocos explicativos ou historinhas (mais de 14 palavras de texto secundário).
   - REPROVE se a imagem estiver vazia demais contendo apenas a headline solta sem o subtítulo de contexto.
2. FILTRO ANTI-CÓPIA DA REFERÊNCIA (ZERO CÓPIA LITERAL / SEM CADEIRAS):
   - REPROVE IMEDIATAMENTE (pontuação <= 4, precisa_refino=true) se a imagem tiver copiado objetos literais da referência original (ex: cadeiras da referência original).
   - As referências são DIRECIONAIS de estética e qualidade, NUNCA para cópia cega.
   - A cena deve utilizar metáforas visuais originais de performance da Kav (xadrez estratégico dourado, gráfico 3D ascendente de ROI, balão 3D de WhatsApp, bússola local de geofencing).
3. USO OBRIGATÓRIO DO LOGOTIPO GEOMÉTRICO OFICIAL KAV (SEM TEXTO ARIAL / SEM SLOGAN):
   - REPROVE IMEDIATAMENTE (pontuação <= 3, precisa_refino=true) se o logo for apenas texto digitado 'KAV' em fonte comum (Arial/Helvetica) ou se contiver o slogan 'Marketing & Performance' embaixo.
   - O logo DEVE ser a marca tipográfica geométrica oficial da Kav (as letras chanfradas em ângulo conforme a Referência 2), posicionado com amplo respiro (mínimo 60px) e proporção 1:1 travada sem distorção.
4. CORES OFICIAIS DA KAV (TEMAS ESCURO E CLARO INVERTIDO):
   - Se tema escuro: Fundo Azul Marinho Noturno Profundo (#001424 ou #001D32) com textos em branco puro e destaque em dourado. REPROVE se for preto puro (#000000).
   - Se tema claro invertido: Fundo Branco Puro (#FFFFFF) no topo em degradê suave para cinza-azulado super claro (#EBF1F6) na base, com textos em Azul Marinho Noturno (#001424) e destaque em Dourado Kav (#EEB730).
5. PROIBIÇÃO ABSOLUTA DE 'ARRASTA PRA ENTENDER' E CARROSSEL:
   - REPROVE IMEDIATAMENTE se a imagem contiver 'Arrasta pra entender', 'Arraste para o lado' ou setas duplas (>>).
6. TOPO LIMPO:
   - REPROVE se o topo tiver caixa, tag ou selo escrito 'PERFORMANCE LOCAL'. O cabeçalho deve ser limpo e elegante.

Responda EXCLUSIVAMENTE com um objeto JSON, sem markdown ou texto antes/depois:
{
  "aprovado": true,
  "pontuacao": 8,
  "diagnostico": "Resumo crítico e direto da avaliação em 1 ou 2 frases em português",
  "precisa_refino": false,
  "instrucoes_de_correcao": "Instruções cirúrgicas em inglês para a IA de edição caso precisa_refino seja true. Especifique com clareza: (1) O que PRESERVAR e (2) O que CORRIGIR (ex: substituir a cadeira por peça de xadrez dourada ou gráfico 3D de ROI; adicionar subtítulo curto de contexto de 10 palavras abaixo da headline; aplicar o logo geométrico oficial KAV de Reference 2 sem slogan, etc.). Se aprovado, deixe string vazia."
}
"""

SYSTEM_PROMPT_DIRETOR_GERAL = """Você é o Diretor de Arte Sênior da Kav (@kav.mkt).
Sua responsabilidade é avaliar com alto senso estético e rigor visual a peça criada pelo designer júnior para o cliente.

DIRETRIZES DA MARCA:
__SKILL__

MODO DE PRODUÇÃO: __MODO__

CHECKLIST CRÍTICO DE AVALIAÇÃO:
1. PRESERVAÇÃO DA COMIDA REAL (SEM CARA DE IA):
   - A peça DEVE preservar a comida autêntica da foto real do cliente (isolada/recortada e integrada na mesa).
   - REPROVE IMEDIATAMENTE (pontuação <= 4, precisa_refino=true) se a comida tiver aspecto de render 3D artificial, desenho, brilho de silicone ou pele plástica/grotesca de IA. A comida deve ter aparência 100% fotográfica natural de câmera.
2. COERÊNCIA GASTRONÔMICA OBRIGATÓRIA (PRATO vs IMAGEM):
   - A chamada e a comida devem ser rigorosamente condizentes com o prato informado.
   - REPROVE IMEDIATAMENTE se a peça for sobre um prato (ex: Frango ao Molho) e a imagem estiver mostrando outro prato incompatível.
3. PROIBIÇÃO DE "ALMOÇO DO DIA", "EXECUTIVO" E RODAPÉ POLUÍDO:
   - REPROVE (pontuação <= 5, precisa_refino=true) se a imagem contiver a palavra "EXECUTIVO", "ALMOÇO DO DIA" ou termos presos estritamente ao almoço na headline ou selo.
   - REPROVE IMEDIATAMENTE se houver frases pequenas no rodapé (ex: "Boa comida faz bons encontros").
4. LOGO OFICIAL DA MARCA:
   - O logo oficial do cliente deve estar presente, nítido e legível no cabeçalho/topo.
5. TIPOGRAFIA & CONTRASTE:
   - A headline deve estar perfeitamente legível, elegante e com hierarquia clara.
   - REPROVE se o texto tiver contorno branco grosso (stroke), glow branco esfumado ou sombra difusa artificial.

Responda EXCLUSIVAMENTE com um objeto JSON, sem markdown ou texto antes/depois:
{
  "aprovado": true,
  "pontuacao": 8,
  "diagnostico": "Resumo crítico e direto da avaliação em 1 ou 2 frases em português",
  "precisa_refino": false,
  "instrucoes_de_correcao": "Instruções cirúrgicas em inglês para a IA de edição caso precisa_refino seja true. Especifique com clareza: (1) O que PRESERVAR e (2) O que CORRIGIR. Se aprovado, deixe string vazia."
}
"""


def revisar_e_aprovar_layout(
    imagem_dict: dict,
    copy: dict,
    foto: Optional[dict] = None,
    cliente: Optional[dict] = None,
    referencia: Optional[dict] = None,
    modo: str = "feed",
    callback_status: Optional[Callable[[str], None]] = None,
    etapa: Optional[Callable[[str], None]] = None,
) -> dict:
    """Supervisiona o layout final gerado pelo designer: avalia visualmente e, se necessário,
    executa uma rodada cirúrgica de refino via IA."""
    def avisar(msg: str):
        cb = callback_status or etapa
        if cb:
            cb(msg)

    if not imagem_dict or not imagem_dict.get("imagem_b64"):
        return imagem_dict

    cliente = cliente or {}
    slug = cliente.get("slug", "")
    eh_kav = (slug == "kav" or modo == "estatico_kav")

    avisar("🎨 [Diretor de Arte]: Inspecionando hierarquia de copy, filtro anti-cópia e logo oficial...")

    if eh_kav:
        system = SYSTEM_PROMPT_DIRETOR_KAV.replace("__SKILL__", cliente.get("skill", ""))
        tema = imagem_dict.get("tema_fundo", "escuro")
        prompt = (
            f"Avalie esta peça criada para a agência 'Kav Marketing & Performance' (@kav.mkt).\n"
            f"Modo de produção: {modo}\n"
            f"Tema esperado: {tema.upper()}\n"
            f"Headline esperada: \"{copy.get('headline_imagem')}\"\n"
            f"Subtítulo de contexto esperado: \"{copy.get('subtitulo_imagem') or copy.get('headline_apoio') or ''}\"\n"
            f"Arquétipo de layout aplicado: {imagem_dict.get('estilo_nome', 'Padrão Kav')}\n\n"
            f"CHECKLIST DE INSPEÇÃO VISUAL:\n"
            f"1. HIERARQUIA DE COPY: Há a headline em destaque e o subtítulo curto de contexto logo abaixo? Se estiver vazia demais sem subtítulo ou cheia de parágrafos/textão, REPROVE!\n"
            f"2. FILTRO ANTI-CÓPIA: A imagem copiou objetos literais da referência (ex: cadeiras)? Se tiver copiado a cadeira em vez de criar uma metáfora original de negócios (xadrez, gráfico 3D, balão WhatsApp, etc.), REPROVE IMEDIATAMENTE!\n"
            f"3. LOGOTIPO OFICIAL: Está usando o logotipo geométrico oficial KAV (Reference 2) ou apenas texto digitado em Arial/Helvetica com 'Marketing & Performance'? Se for texto genérico com slogan, REPROVE IMEDIATAMENTE!\n"
            f"4. A tipografia está em Gotham Sentence Case com respiro de 20-25% nas laterais?\n"
            f"5. O fundo respeita o Azul Marinho Noturno (#001424) para tema escuro OU Branco com degradê suave cinza-azulado para tema claro?\n"
            f"6. Há ausência total de 'Arrasta pra entender' e setas de deslizar?\n\n"
            f"Inspecione com olhar crítico e devolva o JSON de avaliação."
        )
    else:
        nome_prato = foto.get("nome") if foto else "Prato do Dia"
        system = (
            SYSTEM_PROMPT_DIRETOR_GERAL.replace("__SKILL__", cliente.get("skill", ""))
            .replace("__MODO__", modo)
        )
        prompt = (
            f"Avalie esta peça criada para o cliente '{cliente.get('nome')}'.\n"
            f"Modo de produção: {modo}\n"
            f"Headline esperada na peça: \"{copy.get('headline_imagem')}\"\n"
            f"Prato/Foto base: {nome_prato}\n\n"
            f"Inspecione a imagem fornecida com olhar crítico e devolva o JSON de avaliação."
        )

    try:
        resp_json = chamar_ia_visao(
            system=system,
            prompt=prompt,
            imagem_b64=imagem_dict["imagem_b64"],
            max_tokens=600,
            temperature=0.3,
            json_mode=True,
        )
        avaliacao = extrair_json(resp_json)
    except Exception as exc:
        avisar(f"⚠️ [Diretor de Arte]: Falha ao inspecionar visualmente ({exc}). Mantendo layout original.")
        return imagem_dict

    pontuacao = avaliacao.get("pontuacao", 8)
    diagnostico = avaliacao.get("diagnostico", "Layout avaliado.")
    precisa_refino = avaliacao.get("precisa_refino", False)
    instrucoes = avaliacao.get("instrucoes_de_correcao", "")

    if not precisa_refino or pontuacao >= 8 or not instrucoes.strip():
        avisar(f"✅ [Diretor de Arte]: Layout aprovado! Nota {pontuacao}/10 — {diagnostico}")
        imagem_dict["diretor_arte"] = {
            "aprovado": True,
            "refinado": False,
            "pontuacao": pontuacao,
            "diagnostico": diagnostico,
        }
        return imagem_dict

    avisar(f"🔧 [Diretor de Arte]: Layout reprovado (Nota {pontuacao}/10). Refinando arte: {diagnostico}")

    try:
        imagem_bytes_atual = base64.b64decode(imagem_dict["imagem_b64"])
        referencias_refino = [
            (
                imagem_bytes_atual,
                "the current draft layout of the post to correct.",
            )
        ]

        if eh_kav:
            from agents.agente_estatico_kav import _logo_kav, AREAS_LOGO
            logo_arquivo, posicao_logo = _logo_kav(cliente, referencia)
            area_logo = AREAS_LOGO.get(posicao_logo, "header or corner area")
            if logo_arquivo and logo_arquivo.exists():
                referencias_refino.append((
                    logo_arquivo.read_bytes(),
                    f"the official BRAND LOGOTYPE MARK of Kav Marketing & Performance ('KAV'). Correctly position this exact geometric mark in the {area_logo} without any slogan beneath it, with strict 1:1 aspect ratio lock (ZERO DISTORTION) and generous margins.",
                ))
            prompt_refino = (
                "You are executing an art direction revision on this post design for Kav Marketing & Performance. Apply ONLY the following corrections:\n"
                f"{instrucoes}\n\n"
                "STRICT KAV BRAND DIRECTIVES:\n"
                "- NO COPIED CHAIRS: If the draft contains literal chairs copied from the reference, REMOVE THEM IMMEDIATELY and replace with an original Kav performance 3D metaphor (e.g. golden chess piece victory or 3D financial growth chart).\n"
                "- COPY HIERARCHY: Ensure the prominent Headline is accompanied by the short contextual Subtitle (8-14 words) directly below. NO PARAGRAPHS OR ESSAYS!\n"
                "- OFFICIAL LOGO MARK ONLY: Use ONLY the official geometric 'KAV' mark from Reference 2. Remove any plain Arial text or 'Marketing & Performance' slogans underneath!\n"
                "- ZERO LOGO DISTORTION: Ensure the official Kav logo mark is mathematically level with strict 1:1 aspect ratio lock. Never stretch or flatten it!\n"
                "- FONT SIZE RESTRAINT: Scale down headlines to restrained, refined proportions (~55% width with 20-25% breathing margins on the sides).\n"
                "- TYPOGRAPHY: STRICTLY Gotham font in Sentence Case (NO ALL CAPS!).\n"
                "- COLOR PALETTE: Respect the theme. If dark: deep nocturnal navy (#001424). If light: white with soft bluish-gray (#EBF1F6) gradient and navy text.\n"
                "- ELIMINATE all swipe/carousel text ('Arrasta pra entender'). This is a single static feed post (1080x1350)."
            )
        else:
            prompt_refino = (
                "You are executing an art direction revision on this post design. Apply ONLY the following corrections:\n"
                f"{instrucoes}\n\n"
                "STRICT RULES:\n"
                "- Restore authentic real food textures from the real camera photo.\n"
                "- Deliver a polished, crisp, photographic piece in 1080x1440 portrait format."
            )

        imagens_input = [d for d, _ in referencias_refino]
        descricoes_input = [desc for _, desc in referencias_refino]
        prompt_final = (
            "\n\n".join(f"Reference image {i + 1} is {desc}" for i, desc in enumerate(descricoes_input))
            + "\n\nTask:\n" + prompt_refino
        )

        bruta = openai_client.gerar_imagem_com_referencias(prompt_final, imagens_input, size="auto")
        if not bruta or not bruta.get("imagem_b64"):
            raise RuntimeError("API de imagem não retornou resultado no refino.")

        nova_imagem_bytes = image_overlay.recortar_formato_final(base64.b64decode(bruta["imagem_b64"]))
        avisar("✨ [Diretor de Arte]: Layout refinado e aprovado com sucesso!")

        return {
            **imagem_dict,
            "imagem_b64": base64.b64encode(nova_imagem_bytes).decode("ascii"),
            "modelo": bruta.get("modelo") or imagem_dict.get("modelo"),
            "diretor_arte": {
                "aprovado": True,
                "refinado": True,
                "pontuacao_inicial": pontuacao,
                "diagnostico_inicial": diagnostico,
                "correcoes_aplicadas": instrucoes,
            },
        }
    except Exception as exc:
        avisar(f"⚠️ [Diretor de Arte]: Falha na etapa de refino ({exc}). Mantendo layout original.")
        imagem_dict["diretor_arte"] = {
            "aprovado": False,
            "refinado": False,
            "erro_refino": str(exc),
            "diagnostico": diagnostico,
        }
        return imagem_dict
