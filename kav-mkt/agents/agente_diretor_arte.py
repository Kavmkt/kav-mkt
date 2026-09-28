"""Agente Diretor de Arte (Otávio): inteligência de supervisão estética e refino de layout.

Atua como o supervisor e aprovador de arte da Kav (@kav.mkt).
Analisa visualmente (usando visão computacional multimodal) a imagem gerada pelo
designer júnior (Joaquim) para posts de feed (orgânico) e peças de anúncio (campanha).

Avalia com extremo rigor:
1. COERÊNCIA GASTRONÔMICA: O prato na imagem DEVE ser estritamente o prato do dia esperado!
   Se o post for sobre Frango ao Molho e a imagem mostrar Feijoada ou bife, REPROVA imediatamente!
2. REGRA DA FEIJOADA: Feijoada é permitida exclusivamente às quartas-feiras e sábados.
3. PROIBIÇÃO DO TERMO "EXECUTIVO": O restaurante do Nico não usa "almoço executivo" (preço de R$ 26 a R$ 35).
   Se houver "executivo" escrito, REPROVA e manda trocar por "Almoço do Dia" ou "Comida Caseira".
4. Presença e integridade do logo oficial da marca (sem sumir ou deformar).
5. Tipografia, legibilidade e ausência de amadorismos (sem contorno/sombra branca borrada).
6. Ausência de elementos gráficos proibidos (sem elipses/carimbos repetitivos com talheres).
"""
from __future__ import annotations

import base64
from typing import Callable, Optional

from utils import image_overlay, openai_client
from utils.openai_client import chamar_ia_visao, extrair_json

SYSTEM_PROMPT_DIRETOR = """Você é o Diretor de Arte Sênior da Kav (@kav.mkt).
Sua responsabilidade é avaliar com alto senso estético, rigor visual e precisão gastronômica a peça criada para o restaurante NN Restaurante.

DIRETRIZES DA MARCA:
__SKILL__

PRATO DO DIA ESPERADO NA PEÇA: "__PRATO_ESPERADO__"
DIA DA SEMANA: __DIA_SEMANA__

CHECKLIST CRÍTICO DE AVALIAÇÃO (REPROVAÇÃO AUTOMÁTICA):
1. COERÊNCIA GASTRONÔMICA OBRIGATÓRIA (PRATO vs IMAGEM):
   - A comida mostrada na imagem DEVE ser rigorosamente "__PRATO_ESPERADO__".
   - REPROVE IMEDIATAMENTE (pontuação <= 4, precisa_refino=true) se a peça for sobre '__PRATO_ESPERADO__' (ex: Frango ao Molho) e a imagem estiver mostrando Feijoada, bife de carne vermelha ou qualquer outro prato diferente.
   - REGRA DA FEIJOADA: Feijoada é servida EXCLUSIVAMENTE às quartas-feiras e aos sábados. Hoje é __DIA_SEMANA__. Se hoje NÃO for quarta-feira ou sábado e a imagem estiver mostrando feijoada, REPROVE SUMARIAMENTE!
2. PROIBIÇÃO ABSOLUTA DA PALAVRA "EXECUTIVO":
   - REPROVE (pontuação <= 5, precisa_refino=true) se a imagem contiver a palavra "EXECUTIVO" ou "ALMOÇO EXECUTIVO" escrita na headline, no selo ou em qualquer lugar. Os pratos custam entre R$ 26 e R$ 35 e o termo executivo passa impressão de restaurante caro. Deve ser trocado por "ALMOÇO DO DIA" ou "COMIDA CASEIRA".
3. LOGO OFICIAL DA MARCA:
   - O logo oficial do cliente (N&N Restaurante) deve estar presente, nítido e legível no cabeçalho/topo.
   - REPROVE se o logo estiver ausente, distorcido ou trocado por ícone genérico.
4. TIPOGRAFIA & CONTRASTE (ANTI-AMADORISMO):
   - A headline deve estar perfeitamente legível, elegante e com hierarquia clara.
   - REPROVE se o texto tiver contorno branco grosso (stroke), glow branco esfumado ou sombra difusa artificial (WordArt amador).
5. PROIBIÇÃO DE ELIPSE / CARIMBO CLICHÊ:
   - REPROVE se houver carimbos redondos, elipses com garfo/faca ou selos amadores colados nos cantos.
6. AMBIENTAÇÃO & APRESENTAÇÃO CULINÁRIA:
   - Comida farta e apetitosa de almoço comercial brasileiro (arroz soltinho, feijão, guarnições).
   - Louça comercial branca tradicional ou marmitex, mesa de madeira clara com textura levemente esbranquiçada.

Responda EXCLUSIVAMENTE com um objeto JSON, sem markdown ou texto antes/depois:
{
  "aprovado": true,
  "pontuacao": 8,
  "diagnostico": "Resumo crítico e direto da avaliação em 1 ou 2 frases em português",
  "precisa_refino": false,
  "instrucoes_de_correcao": "Instruções cirúrgicas em inglês para a IA de edição caso precisa_refino seja true. Especifique com clareza: (1) O que PRESERVAR e (2) O que CORRIGIR (ex: substituir feijoada por frango ao molho com arroz e feijão, remover a palavra EXECUTIVO e substituir por ALMOÇO DO DIA, reinserir logo oficial, etc.). Se aprovado, deixe string vazia."
}
"""


def revisar_e_aprovar_layout(
    imagem_dict: dict,
    copy: dict,
    foto: dict,
    cliente: dict,
    referencia: Optional[dict] = None,
    modo: str = "organico",
    etapa: Optional[Callable[[str], None]] = None,
) -> dict:
    """Inspeciona visualmente a imagem gerada e, se necessário, executa um refino de arte."""
    avisar = etapa or (lambda _texto: None)
    if not imagem_dict or not imagem_dict.get("imagem_b64"):
        return imagem_dict

    nome_prato = foto.get("nome") or (foto["arquivo"].stem if foto.get("arquivo") else "Prato do Dia")
    avisar(f"🎨 [Diretor de Arte]: Inspecionando layout de '{nome_prato}' com visão computacional...")

    from agents.agente_legenda_fotos import obter_contexto_temporal
    nome_dia, _, _ = obter_contexto_temporal()

    # 1. Avaliação multimodal com GPT-4o-mini
    system = (
        SYSTEM_PROMPT_DIRETOR.replace("__SKILL__", cliente.get("skill", ""))
        .replace("__PRATO_ESPERADO__", nome_prato)
        .replace("__DIA_SEMANA__", nome_dia)
    )
    prompt = (
        f"Avalie esta peça criada para o cliente '{cliente.get('nome')}'.\n"
        f"Dia da semana: {nome_dia}\n"
        f"Prato do dia esperado: \"{nome_prato}\"\n"
        f"Headline na copy: \"{copy.get('headline_imagem')}\"\n"
        f"Selo esperado: \"{copy.get('selo_produto') or 'nenhum'}\"\n\n"
        f"Verifique especialmente se a comida na imagem corresponde a '{nome_prato}' (não pode ser feijoada se o prato for frango) "
        f"e se a palavra 'EXECUTIVO' foi evitada. Devolva o JSON de avaliação."
    )

    try:
        resp_json = chamar_ia_visao(
            system=system,
            prompt=prompt,
            imagem_b64=imagem_dict["imagem_b64"],
            max_tokens=650,
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

    # Se aprovado ou nota alta (>= 8) sem necessidade crítica de refino:
    if not precisa_refino or pontuacao >= 8 or not instrucoes.strip():
        avisar(f"✅ [Diretor de Arte]: Layout aprovado! Nota {pontuacao}/10 — {diagnostico}")
        imagem_dict["diretor_arte"] = {
            "aprovado": True,
            "refinado": False,
            "pontuacao": pontuacao,
            "diagnostico": diagnostico,
        }
        return imagem_dict

    # 2. Refino de Arte solicitado pelo Diretor
    avisar(f"🔧 [Diretor de Arte]: Layout reprovado (Nota {pontuacao}/10). Refinando arte: {diagnostico}")

    try:
        imagem_bytes_atual = base64.b64decode(imagem_dict["imagem_b64"])
        referencias_refino = [
            (
                imagem_bytes_atual,
                "the current draft layout of the post. Keep the authentic restaurant dining staging.",
            )
        ]

        # Logotipo oficial como guia visual prioritário
        from agents.agente_design_fotos import _logo
        logo_arquivo, posicao_logo = _logo(cliente, referencia)
        if logo_arquivo:
            referencias_refino.append((
                logo_arquivo.read_bytes(),
                "the official authentic client BRAND LOGO. Reproduce this exact logo with absolute fidelity, clean typography, correct colors and sharp contrast.",
            ))

        # Se for campanha, guia de zona de CTA
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
            "You are executing an art direction revision on this post design. Apply ONLY the following corrections:\n"
            f"{instrucoes}\n\n"
            "STRICT RULES:\n"
            f"- Ensure the food depicted is strictly '{nome_prato}'. Never display feijoada or red meat if the dish is chicken.\n"
            "- Never include the word 'EXECUTIVO' or 'ALMOÇO EXECUTIVO'; replace with 'ALMOÇO DO DIA' or 'COMIDA CASEIRA'.\n"
            "- Ensure the official client logo is clearly and cleanly reproduced from the authentic logo reference.\n"
            "- NEVER add white glow, blurry white outlines, or diffuse halos around text letters.\n"
            "- Do NOT add circular stamp badges, fork/knife ellipses, or amateur clutter.\n"
            "- Deliver a polished, crisp, editorial-quality piece in 1080x1440 portrait format."
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
