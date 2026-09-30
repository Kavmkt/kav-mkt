"""Agente Diretor de Arte (Otávio): inteligência de supervisão estética e refino de layout.

Atua como o supervisor e aprovador de arte da Kav (@kav.mkt).
Analisa visualmente (usando visão computacional multimodal) a imagem gerada pelo
designer para:
1. Posts da agência Kav (@kav.mkt) - feed estático de autoridade em marketing local;
2. Posts de restaurantes/fotos reais (N&N Restaurante) - preservação de comida real autêntica;
3. Peças de anúncio (campanha).

Se o layout tiver nota baixa (< 8) ou falhas críticas (ex: logo sobrepondo texto,
"Arrasta pra entender" em post estático, comida com aspecto 3D/plástico), o Diretor de Arte
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
1. INTEGRIDADE E POSIÇÃO DO LOGOTIPO KAV:
   - O logo oficial da Kav ('KAV') DEVE estar presente, perfeitamente nítido, proporcional e posicionado com área de respiro generosa no topo ou no canto designado.
   - REPROVE IMEDIATAMENTE (pontuação <= 5, precisa_refino=true) se o logotipo estiver sobrepondo o título, colidindo com qualquer texto, cortado, distorcido (letras trocadas, "WAV") ou gigante ocupando espaço indevido.
2. PROIBIÇÃO ABSOLUTA DE 'ARRASTA PRA ENTENDER' E CARROSSEL:
   - REPROVE IMEDIATAMENTE (pontuação <= 4, precisa_refino=true) se a imagem contiver 'Arrasta pra entender', 'Arraste para o lado', 'Passe para o lado' ou botões com setas de arrastar. Os posts da Kav são 100% estáticos de feed único!
3. PROIBIÇÃO DE BLOCO / BADGE NO TOPO ('PERFORMANCE LOCAL'):
   - REPROVE se o topo tiver caixa, tag ou selo escrito 'PERFORMANCE LOCAL'. O cabeçalho deve ser limpo e elegante.
4. HIERARQUIA TIPOGRÁFICA E LEGIBILIDADE:
   - A headline deve estar em destaque imponente (Plus Jakarta Sans 900 / ExtraBold), perfeitamente legível sobre o fundo escuro azul noturno (#001424).
   - REPROVE se textos estiverem embolados, com letras truncadas, ou sobrepondo caixas/cards.
5. ESTRUTURA DO ARQUÉTIPO VISUAL:
   - Se for Comparativo: deve haver dois blocos distintos (O Erro em card escuro/carmesim com ✕ vs A Solução Kav em card dourado com ✓).
   - Se for Notificação WhatsApp: deve haver um card nítido simulando notificação de mensagem de celular.
   - Se for Dashboard: deve haver o número gigante e o gráfico em linha ascendente.
   - Se for Tweet Box: deve haver o card flutuante centralizado com avatar e @kav.mkt.
   - Se for Manifesto: deve ser puramente tipográfico, sem caixas poluídas.
6. PROIBIÇÃO DE CLICHÊS GENÉRICOS DE IA:
   - REPROVE se houver miniaturas de cidades 3D, radares, ou pins amarelos de GPS.

Responda EXCLUSIVAMENTE com um objeto JSON, sem markdown ou texto antes/depois:
{
  "aprovado": true,
  "pontuacao": 8,
  "diagnostico": "Resumo crítico e direto da avaliação em 1 ou 2 frases em português",
  "precisa_refino": false,
  "instrucoes_de_correcao": "Instruções cirúrgicas em inglês para a IA de edição caso precisa_refino seja true. Especifique com clareza: (1) O que PRESERVAR e (2) O que CORRIGIR (ex: separar o logotipo Kav do título dando respiro no topo, remover o botão 'Arrasta pra entender', etc.). Se aprovado, deixe string vazia."
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
   - REGRA DA FEIJOADA: Feijoada é servida EXCLUSIVAMENTE às quartas-feiras e aos sábados. Se não for dia de feijoada e a imagem mostrar feijoada, REPROVE.
3. PROIBIÇÃO DE "ALMOÇO DO DIA", "EXECUTIVO" E RODAPÉ POLUÍDO:
   - REPROVE (pontuação <= 5, precisa_refino=true) se a imagem contiver a palavra "EXECUTIVO", "ALMOÇO DO DIA" ou termos presos estritamente ao almoço na headline ou selo. O restaurante publica posts à tarde/noite para alcançar mais pessoas.
   - REPROVE IMEDIATAMENTE se houver frases pequenas no rodapé (ex: "Boa comida faz bons encontros") ou barras de ícones com texto minúsculo na parte inferior. O rodapé deve ser 100% limpo.
   - Se houver selo, deve conter a frase menor "Qualidade Garantida".
4. LOGO OFICIAL DA MARCA:
   - O logo oficial do cliente deve estar presente, nítido e legível no cabeçalho/topo.
   - REPROVE se o logo estiver ausente, distorcido ou trocado por ícone genérico.
5. TIPOGRAFIA & CONTRASTE (ANTI-AMADORISMO):
   - A headline deve estar perfeitamente legível, elegante e com hierarquia clara (Playfair Display).
   - REPROVE se o texto tiver contorno branco grosso (stroke), glow branco esfumado ou sombra difusa artificial (WordArt amador).
6. PROIBIÇÃO DE ELIPSE / CARIMBO CLICHÊ:
   - REPROVE se houver carimbos redondos, elipses com garfo/faca ou selos amadores colados nos cantos.
7. AMBIENTAÇÃO & RECORTE DO PRATO:
   - O prato real com a comida autêntica do cliente deve estar bem integrado sobre a mesa de madeira rústica, com visual apetitoso e limpo.

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

    avisar("🎨 [Diretor de Arte]: Inspecionando layout, proporções e alinhamento visual...")

    if eh_kav:
        system = SYSTEM_PROMPT_DIRETOR_KAV.replace("__SKILL__", cliente.get("skill", ""))
        prompt = (
            f"Avalie esta peça criada para a agência 'Kav Marketing & Performance' (@kav.mkt).\\n"
            f"Modo de produção: {modo}\\n"
            f"Headline esperada na peça: \\\"{copy.get('headline_imagem')}\\\"\\n"
            f"Frase de apoio / dados esperados: \\\"{copy.get('headline_apoio') or copy.get('texto_card') or ''}\\\"\\n"
            f"Arquétipo de layout aplicado: {imagem_dict.get('estilo_nome', 'Padrão Kav')}\\n\\n"
            f"CHECKLIST DE INSPEÇÃO VISUAL:\\n"
            f"1. O logo oficial KAV está visível e com RESPIRO? Ele NUNCA pode sobrepor o título ou colidir com textos!\\n"
            f"2. Há algum botão ou texto 'Arrasta pra entender'? Se houver, REPROVE IMEDIATAMENTE (é post estático individual)!\\n"
            f"3. O topo está limpo, sem caixas de 'PERFORMANCE LOCAL'?\\n"
            f"4. A hierarquia tipográfica está nítida e profissional?\\n\\n"
            f"Inspecione a imagem fornecida com olhar crítico e devolva o JSON de avaliação."
        )
    else:
        nome_prato = foto.get("nome") if foto else "Prato do Dia"
        system = (
            SYSTEM_PROMPT_DIRETOR_GERAL.replace("__SKILL__", cliente.get("skill", ""))
            .replace("__MODO__", modo)
        )
        prompt = (
            f"Avalie esta peça criada para o cliente '{cliente.get('nome')}'.\\n"
            f"Modo de produção: {modo}\\n"
            f"Headline esperada na peça: \\\"{copy.get('headline_imagem')}\\\"\\n"
            f"Selo/tag esperado (se houver): \\\"{copy.get('selo_produto') or 'nenhum'}\\\"\\n"
            f"Prato/Foto base: {nome_prato}\\n"
            f"Estilo de layout aplicado: {imagem_dict.get('estilo_nome', 'Padrão Editorial')}\\n\\n"
            f"DIRETRIZES DO ESTILO:\\n"
            f"- Se for estilo Marmita Delivery: A comida deve estar em marmita redonda de isopor de entrega e NÃO pode ter talheres em volta (sem garfos/facas).\\n"
            f"- Se for estilo Minimalista: Foco na fotografia da comida com texto enxuto e logo discreto. Não reprove por concisão.\\n\\n"
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

    # Se aprovado com nota alta (>= 8) sem necessidade crítica de refino:
    if not precisa_refino or pontuacao >= 8 or not instrucoes.strip():
        avisar(f"✅ [Diretor de Arte]: Layout aprovado! Nota {pontuacao}/10 — {diagnostico}")
        imagem_dict["diretor_arte"] = {
            "aprovado": True,
            "refinado": False,
            "pontuacao": pontuacao,
            "diagnostico": diagnostico,
        }
        return imagem_dict

    # 2. Refino de Arte solicitado pelo Diretor de Arte
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
                    f"the official BRAND LOGO of Kav Marketing & Performance ('KAV'). Correctly position this exact logo in the {area_logo} with generous margins and breathing room, without overlapping any text.",
                ))
            prompt_refino = (
                "You are executing an art direction revision on this post design for Kav Marketing & Performance. Apply ONLY the following corrections:\\n"
                f"{instrucoes}\\n\\n"
                "STRICT KAV BRAND DIRECTIVES:\\n"
                "- Ensure the official Kav logo ('KAV') is seamlessly integrated with generous breathing room and safe padding. NEVER collide with, touch, or overlap any headline or text box!\\n"
                "- ABSOLUTELY ELIMINATE and DO NOT write 'Arrasta pra entender', 'Arraste para o lado', or any carousel/swipe instruction. This is a single static feed post (1080x1350).\\n"
                "- Keep the top area clean: NO 'PERFORMANCE LOCAL' boxes or badges.\\n"
                "- Deliver a polished, high-contrast, razor-sharp masterpiece in 1080x1350 vertical format."
            )
        else:
            # Fluxo Restaurante / Fotos reais
            if foto and foto.get("arquivo") and hasattr(foto["arquivo"], "read_bytes"):
                try:
                    referencias_refino.append((
                        foto["arquivo"].read_bytes(),
                        "the authentic client camera photograph of the real dish. Use this to restore genuine food textures and eliminate artificial waxy AI appearance.",
                    ))
                except Exception:
                    pass

            from agents.agente_design_fotos import _logo
            logo_arquivo, posicao_logo = _logo(cliente, referencia)
            if logo_arquivo:
                guia_logo = image_overlay.guia_posicao_logo(logo_arquivo, posicao_logo)
                referencias_refino.append((
                    guia_logo,
                    "the official client logo guide template. Reproduce the client's official logo exactly from this template at this scale and position.",
                ))

            if modo == "campanha":
                try:
                    guia_cta = image_overlay.guia_zona_cta()
                    referencias_refino.append((
                        guia_cta,
                        "the exact rectangular area reserved for the call-to-action bar.",
                    ))
                except Exception:
                    pass

            prompt_refino = (
                "You are executing an art direction revision on this post design. Apply ONLY the following corrections:\\n"
                f"{instrucoes}\\n\\n"
                "STRICT RULES:\\n"
                "- Restore and keep the authentic real food textures from the real camera photo, eliminating any artificial 3D CGI gloss, waxy skin, or silicone sheen.\\n"
                "- Ensure the official client logo is clearly and cleanly reproduced from the logo guide template in the header.\\n"
                "- Never use the word 'EXECUTIVO' or 'ALMOÇO EXECUTIVO'; replace with 'ALMOÇO DO DIA' or 'COMIDA CASEIRA'.\\n"
                "- NEVER add white glow, blurry white outlines, or diffuse halos around text letters.\\n"
                "- Do NOT add circular stamp badges, fork/knife ellipses, or amateur clutter.\\n"
                "- Deliver a polished, crisp, photographic piece in 1080x1440 portrait format."
            )

        imagens_input = [d for d, _ in referencias_refino]
        descricoes_input = [desc for _, desc in referencias_refino]
        prompt_final = (
            "\\n\\n".join(f"Reference image {i + 1} is {desc}" for i, desc in enumerate(descricoes_input))
            + "\\n\\nTask:\\n" + prompt_refino
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
