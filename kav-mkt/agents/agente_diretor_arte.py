"""Agente Diretor de Arte (Otávio): inteligência de supervisão estética e refino de layout.

Atua como o supervisor e aprovador de arte da Kav (@kav.mkt).
Analisa visualmente (usando visão computacional multimodal) a imagem gerada pelo
designer júnior (Joaquim) para posts de feed (orgânico) e peças de anúncio (campanha).

Avalia rigorosamente:
1. Presença e integridade do logo oficial da marca (sem sumir, deformar ou ficar ilegível);
2. Tipografia, legibilidade e ausência de amadorismos (sem contorno/sombra branca borrada);
3. Ausência de elementos gráficos proibidos (sem elipses/carimbos repetitivos com talheres);
4. Apresentação gastronômica/composição da cena (comida apetitosa em mesa de restaurante).

Se o layout tiver nota baixa ou falhas críticas, o Diretor de Arte aciona UMA rodada de
refino com gpt-image-2.5-sunburst enviando o rascunho atual + logo oficial, instruindo
o que PRESERVAR (a comida) e o que CORRIGIR (logo, tipografia, remoção de elipses).
"""
import base64
from typing import Callable, Optional

from utils import image_overlay, openai_client
from utils.openai_client import chamar_ia_visao, extrair_json

SYSTEM_PROMPT_DIRETOR = """Você é o Diretor de Arte Sênior da Kav (@kav.mkt).
Sua responsabilidade é avaliar com alto senso estético e rigor visual a peça criada pelo designer júnior para o cliente.

DIRETRIZES DA MARCA:
__SKILL__

CHECKLIST CRÍTICO DE AVALIAÇÃO:
1. LOGO OFICIAL DA MARCA:
   - O logo oficial do cliente deve estar presente, nítido e legível.
   - REPROVE se o logo estiver ausente, distorcido, com texto ilegível ou trocado por ícone genérico.
2. TIPOGRAFIA & CONTRASTE (ANTI-AMADORISMO):
   - A chamada/headline deve estar perfeitamente legível, elegante e com hierarquia clara.
   - REPROVE se o texto tiver contorno branco grosso (stroke), glow branco esfumado ou sombra difusa artificial (WordArt amador).
3. PROIBIÇÃO DE ELIPSE / CARIMBO CLICHÊ:
   - REPROVE se houver carimbos redondos, elipses com garfo/faca ou selos amadores ("Comida de Verdade" etc.) colados no canto da imagem. A composição deve ser limpa.
4. AMBIENTAÇÃO & FOTOGRAFIA CULINÁRIA:
   - A comida deve ser apetitosa e estar ambientada como fotografia profissional de gastronomia (mesa de restaurante, iluminação quente, ambiente aconchegante).
   - REPROVE se parecer uma foto crua de celular com mão segurando pote plástico ou fundo doméstico improvisado.
5. CONTEXTO DO MODO (__MODO__):
   - Se for 'campanha': deve conter hierarquia visual de anúncio de alta conversão e faixa/bloco claro de chamada de ação (WhatsApp / localização).
   - Se for 'organico': deve ter composição editorial sofisticada para o feed do Instagram.

Responda EXCLUSIVAMENTE com um objeto JSON, sem markdown ou texto antes/depois:
{
  "aprovado": true,
  "pontuacao": 8,
  "diagnostico": "Resumo crítico e direto da avaliação em 1 ou 2 frases em português",
  "precisa_refino": false,
  "instrucoes_de_correcao": "Instruções cirúrgicas em inglês para a IA de edição caso precisa_refino seja true. Especifique com clareza: (1) O que PRESERVAR (a comida, os pratos reais) e (2) O que CORRIGIR (ex: reinserir o logo oficial a partir do template de guia, remover contornos brancos esfumados, remover selo de elipse, etc.). Se aprovado, deixe string vazia."
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

    avisar("🎨 [Diretor de Arte]: Inspecionando layout do Joaquim com visão computacional...")

    # 1. Avaliação multimodal com GPT-4o-mini
    system = (
        SYSTEM_PROMPT_DIRETOR.replace("__SKILL__", cliente.get("skill", ""))
        .replace("__MODO__", modo)
    )
    prompt = (
        f"Avalie esta peça criada para o cliente '{cliente.get('nome')}'.\n"
        f"Modo de produção: {modo}\n"
        f"Headline esperada na peça: \"{copy.get('headline_imagem')}\"\n"
        f"Selo/tag esperado (se houver): \"{copy.get('selo_produto') or 'nenhum'}\"\n"
        f"Prato/Foto base: {foto.get('nome') or foto.get('arquivo', 'Prato')}\n\n"
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
                "the current draft layout of the post. Keep the authentic food and dish composition.",
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
            "- Keep the authentic food dish, its textures and appetizing culinary presentation unchanged.\n"
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
