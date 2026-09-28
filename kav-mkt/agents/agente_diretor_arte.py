"""Agente Diretor de Arte (Otávio): inteligência de supervisão estética e refino de layout.

Atua como o supervisor e aprovador de arte da Kav (@kav.mkt).
Analisa visualmente (usando visão computacional multimodal) a imagem gerada pelo
designer júnior (Joaquim) para posts de feed (orgânico) e peças de anúncio (campanha).

Avalia rigorosamente:
1. Preservação da comida real (sem cara de IA, sem texturas plásticas, waxy ou 3D CGI);
2. Coerência gastronômica com o prato esperado do dia (e regra da feijoada);
3. Proibição absoluta dos termos "Almoço do Dia" e "Executivo" no layout;
4. Rodapé 100% limpo: sem frases pequenas soltas embaixo e sem ícones com texto minúsculo;
5. Selo discreto com "Qualidade Garantida" (se houver selo);
6. Presença e integridade do logo oficial da marca (sem sumir, deformar ou ficar ilegível);
7. Tipografia, legibilidade e ausência de amadorismos (sem contorno/sombra branca borrada).

Se o layout tiver nota baixa ou falhas críticas, o Diretor de Arte aciona UMA rodada de
refino com gpt-image-2.5-sunburst enviando o rascunho atual + foto real + guia oficial de logo.
"""
import base64
from typing import Callable, Optional

from utils import image_overlay, openai_client
from utils.openai_client import chamar_ia_visao, extrair_json

SYSTEM_PROMPT_DIRETOR = """Você é o Diretor de Arte Sênior da Kav (@kav.mkt).
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
   - O logo oficial do cliente (N&N Restaurante) deve estar presente, nítido e legível no cabeçalho/topo.
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
  "instrucoes_de_correcao": "Instruções cirúrgicas em inglês para a IA de edição caso precisa_refino seja true. Especifique com clareza: (1) O que PRESERVAR e (2) O que CORRIGIR (ex: remover frases pequenas do rodapé, remover 'Almoço do Dia' e usar 'Qualidade Garantida', etc.). Se aprovado, deixe string vazia."
}
"""


def revisar_e_aprovar_layout(
    imagem_dict: dict,
    copy: dict,
    foto: dict,
    cliente: dict,
    referencia: Optional[dict] = None,
    modo: str = "feed",
    callback_status: Optional[Callable[[str], None]] = None,
) -> dict:
    """Supervisiona o layout final gerado pelo designer: avalia visualmente e, se necessário,
    executa uma rodada cirúrgica de refino via IA."""
    def avisar(msg: str):
        if callback_status:
            callback_status(msg)

    if not imagem_dict or not imagem_dict.get("imagem_b64"):
        return imagem_dict

    avisar("🎨 [Diretor de Arte]: Inspecionando layout e fidelidade fotográfica...")

    nome_prato = foto.get("nome") or (foto["arquivo"].stem if foto.get("arquivo") else "Prato do Dia")

    system = (
        SYSTEM_PROMPT_DIRETOR.replace("__SKILL__", cliente["skill"])
        .replace("__MODO__", modo)
    )
    prompt = (
        f"Avalie esta peça criada para o cliente '{cliente.get('nome')}'.\n"
        f"Modo de produção: {modo}\n"
        f"Headline esperada na peça: \"{copy.get('headline_imagem')}\"\n"
        f"Selo/tag esperado (se houver): \"{copy.get('selo_produto') or 'nenhum'}\"\n"
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
                "the current draft layout of the post to correct.",
            )
        ]

        # Inclui a foto real do cliente para restaurar texturas autênticas de comida
        if foto and foto.get("arquivo") and hasattr(foto["arquivo"], "read_bytes"):
            try:
                referencias_refino.append((
                    foto["arquivo"].read_bytes(),
                    "the authentic client camera photograph of the real dish. Use this to restore genuine food textures and eliminate artificial waxy AI appearance.",
                ))
            except Exception:
                pass

        # Template do Logo oficial como guia visual prioritário
        from agents.agente_design_fotos import _logo
        logo_arquivo, posicao_logo = _logo(cliente, referencia)
        if logo_arquivo:
            guia_logo = image_overlay.guia_posicao_logo(logo_arquivo, posicao_logo)
            referencias_refino.append((
                guia_logo,
                "the official client logo guide template. Reproduce the client's official logo exactly "
                "from this template at this scale and position.",
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
            "- Restore and keep the authentic real food textures from the real camera photo, eliminating any artificial 3D CGI gloss, waxy skin, or silicone sheen.\n"
            "- Ensure the official client logo is clearly and cleanly reproduced from the logo guide template in the header.\n"
            "- NEVER use 'ALMOÇO DO DIA', 'EXECUTIVO' or lunch-restricted phrasing; use timeless appetizing calls or 'Qualidade Garantida'.\n"
            "- REMOVE any small footer phrases, taglines, or tiny icon rows from the bottom of the image. Keep the lower area completely clean and breathing.\n"
            "- If a badge/seal is present, it must say strictly 'Qualidade Garantida'.\n"
            "- NEVER add white glow, blurry white outlines, or diffuse halos around text letters.\n"
            "- Do NOT add circular stamp badges, fork/knife ellipses, or amateur clutter.\n"
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
