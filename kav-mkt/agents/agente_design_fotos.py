"""Agente de Design (Fotos): escreve o brief e gera a imagem final para clientes "de
fotos" (config.json com "tipo": "fotos") — hoje só o NN Restaurante.

DIRETRIZ DE ARTE: PRESERVAÇÃO DA COMIDA REAL DO CLIENTE (SEM CARA DE IA)
1. A comida mostrada na foto real de referência (foto['arquivo']) é a comida autêntica do cliente.
2. A IA NUNCA gera comida sintética com IA nem troca os ingredientes reais por render 3D.
3. A IA PODE isolar/recortar o prato com a comida original de verdade do cliente e inseri-lo
   em um novo cenário esteticamente mais coerente, bonito, organizado e diagramável (mesa de
   madeira rústica, iluminação natural suave, fundo aconchegante de restaurante).
4. Aplica a diagramação editorial limpa: headline de impacto em Playfair Display, selo minimalista
   em Montserrat ('Almoço do Dia', 'Comida Caseira' - PROIBIDO 'executivo'), e o logotipo oficial da
   N&N Restaurante no cabeçalho/topo com respiro e contraste.
5. Imagem final nítida e limpa, sem pós-processamento artificial de ruído/grão.
"""
from __future__ import annotations

import base64
from typing import Optional

from agents.agente_design import AREAS_LOGO, MARGEM_SEGURANCA_BORDA, _margem_corte_vertical
from utils import image_overlay, openai_client
from utils.openai_client import chamar_ia

SYSTEM_PROMPT = """Você é o Diretor de Arte sênior da Kav (@kav.mkt). Sua função é escrever o
brief de UMA peça do Instagram para o NN Restaurante, pronto para ser enviado direto a um gerador de
imagem por IA de alta qualidade.

DIRETRIZES DE MARCA E KV DO CLIENTE:
__SKILL__

DIREÇÃO DE ARTE — PRESERVAÇÃO RIGOROSA DA COMIDA REAL DO CLIENTE:
- BASE DA CENA OBRIGATÓRIA: A comida mostrada na Referência 1 é a FOTO REAL E AUTÊNTICA do prato do cliente. Os alimentos, porções, texturas reais e o prato com a refeição autêntica DEVEM ser preservados com máxima fidelidade.
- PROIBIÇÃO TERMINANTE DE COMIDA ARTIFICIAL (SEM CARA DE IA): NUNCA substitua, redesenhe ou altere a comida da foto real por render 3D, CGI, ilustrações digitais ou texturas emborrachadas de IA.
- ELEVAÇÃO DE CENÁRIO E RECORTE DO PRATO: Você pode isolar/recortar o prato com a comida original de verdade do cliente e posicioná-lo sobre um novo cenário de restaurante aconchegante e bonito: mesa de madeira rústica com textura agradável, iluminação quente e natural de almoço e fundo suavemente desfocado (sem mãos amadoras ou fundos improvisados).
__CONTEXTO_LAYOUT__
- LOGOTIPO OFICIAL DA MARCA: uma das imagens de referência fornecidas é o logotipo oficial da empresa. Você DEVE reproduzir esse logotipo exatamente (mesma tipografia, símbolo/emblema, cores e proporções) integrado com nitidez no cabeçalho ou área de branding indicada (__AREA_LOGO__), com margens de respiro de cerca de 5% das bordas.

REGRAS RÍGIDAS DE DIAGRAMAÇÃO E ANTI-AMADORISMO:
1. PROIBIDO O TERMO "EXECUTIVO": NUNCA escreva ou renderize a palavra "EXECUTIVO" ou "ALMOÇO EXECUTIVO" na arte (nem na headline, nem no selo, nem em badges). O restaurante trabalha com preços populares de R$ 26 a R$ 35. Use "ALMOÇO DO DIA", "COMIDA CASEIRA", "PRATO FEITO" ou o próprio nome do prato.
2. PROIBIDO CONTORNO BRANCO / GLOW: NUNCA crie letras com sombra branca difusa, contorno branco grosso (stroke) ou glow esfumado atrás do texto. Tipografia sólida, nítida e sofisticada.
3. PROIBIDO SELO EM ELIPSE / CARIMBO REDONDO COM TALHERES: NUNCA desenhe selos circulares ou carimbos com garfo e faca. Use etiquetas retangulares limpas ou integre o texto de forma minimalista.
4. MARGENS DE SEGURANÇA:
   - Deixe pelo menos __MARGEM__% de respiro livre no topo e no rodapé.
   - Mantenha texto e logo a pelo menos __MARGEM_LATERAL__% de distância das bordas.

Retorne APENAS o brief em texto corrido, em inglês — exceto a headline e o selo, citados entre aspas exatamente em português. Sem explicações, sem markdown, sem listas.
"""


def gerar_brief_foto(copy: dict, foto: dict, cliente: dict, referencia: Optional[dict]) -> str:
    _, posicao_logo = _logo(cliente, referencia)
    nome_prato = foto.get("nome") or foto["arquivo"].stem
    desc_prato = foto.get("descricao") or ""

    system = (
        SYSTEM_PROMPT.replace("__SKILL__", cliente["skill"])
        .replace("__CONTEXTO_LAYOUT__", "- REFERÊNCIA DE LAYOUT: siga o alinhamento editorial sofisticado da marca;")
        .replace("__MARGEM__", str(_margem_corte_vertical()))
        .replace("__MARGEM_LATERAL__", str(MARGEM_SEGURANCA_BORDA))
        .replace("__AREA_LOGO__", AREAS_LOGO.get(posicao_logo, "top header / branding area"))
    )
    partes = [
        f"Prato real do cliente na foto de referência: {nome_prato}",
        f"Detalhes: {desc_prato}" if desc_prato else "",
        f'Headline da arte: "{copy.get("headline_imagem")}"',
    ]
    if copy.get("selo_produto"):
        selo_limpo = copy["selo_produto"].replace("Executivo", "do Dia").replace("executivo", "do Dia")
        partes.append(f'Selo do prato: "{selo_limpo}"')

    partes.append(
        f"DIRETRIZ DE COMPOSIÇÃO: Mantenha a comida original da foto de referência de '{nome_prato}' rigorosamente intacta. "
        "Isole ou recorte o prato com a comida real do cliente e posicione-o sobre um novo cenário de mesa de madeira rústica, "
        "com iluminação natural de restaurante acolhedor. Diagramar headline, selo e o logotipo oficial da N&N no cabeçalho com alto contraste. "
        "NUNCA use a palavra executivo e NUNCA substitua a comida por render de IA."
    )

    return chamar_ia(system=system, prompt="\n".join(p for p in partes if p), max_tokens=750, temperature=0.7)


def gerar_imagem_foto(brief: str, foto: dict, cliente: dict, referencia: Optional[dict]) -> dict:
    """Gera a imagem do post diagramando e elevando o cenário sobre a foto REAL do cliente."""
    avisos = []
    referencias_imagem = [
        (
            foto["arquivo"].read_bytes(),
            "the REAL photograph showing the authentic food/dish of N&N Restaurante. "
            "You MUST preserve this authentic dish and its genuine ingredients with 100% fidelity. "
            "You may isolate or crop the plate with the real food and stage it cleanly on a beautiful, warm rustic wooden dining table "
            "with natural lunch lighting and soft background bokeh, without altering the food into 3D CGI.",
        )
    ]

    if referencia:
        referencias_imagem.append((
            referencia["arquivo"].read_bytes(),
            "this brand's layout reference template. Emulate its professional graphic design hierarchy only: "
            "the refined typography styling, spacing, clean alignment, and balance. "
            "Do NOT copy the specific food items depicted in this template.",
        ))

    logo_arquivo, posicao_logo = _logo(cliente, referencia)
    if logo_arquivo:
        referencias_imagem.append((
            logo_arquivo.read_bytes(),
            "the official BRAND LOGO of N&N Restaurante. You must reproduce this exact logo "
            "(typography, symbols, monogram, and colors) into the graphic layout of the post. "
            "Position it cleanly in the header or designated branding zone with strong contrast and breathing room.",
        ))

    bruta = None
    try:
        imagens = [dados for dados, _ in referencias_imagem]
        prompt = _prompt_com_referencias(brief, [desc for _, desc in referencias_imagem])
        bruta = openai_client.gerar_imagem_com_referencias(prompt, imagens)
    except Exception as exc:
        raise RuntimeError(f"A geração da imagem sobre a foto real falhou ({exc}).") from exc

    if not bruta or not bruta.get("imagem_b64"):
        raise RuntimeError("A API de imagem não retornou nenhuma imagem.")

    if bruta.get("tamanho_pedido") and bruta.get("tamanho_real") and bruta["tamanho_pedido"] != bruta["tamanho_real"]:
        avisos.append(
            f"A API pediu {bruta['tamanho_pedido']} mas devolveu {bruta['tamanho_real']} — "
            "o tamanho final ainda sai certo (1080x1440, sem cortar nada)."
        )

    return {
        **_finalizar(base64.b64decode(bruta["imagem_b64"])),
        "modelo": bruta.get("modelo"),
        "qualidade": bruta.get("qualidade"),
        "tamanho_gerado": bruta.get("tamanho_real"),
        "referencia_layout": referencia["arquivo"].name if referencia else None,
        "com_foto_real": True,
        "aviso": " ".join(avisos) or None,
    }


def _finalizar(imagem_bytes: bytes) -> dict:
    final = image_overlay.recortar_formato_final(imagem_bytes)
    return {
        "imagem_b64": base64.b64encode(final).decode("ascii"),
        "tamanho": f"{image_overlay.LARGURA_PADRAO}x{image_overlay.ALTURA_PADRAO}",
    }


def _prompt_com_referencias(brief: str, descricoes: list) -> str:
    partes = [f"Reference image {i + 1} is {desc}" for i, desc in enumerate(descricoes)]
    partes.append("Post to create:\n" + brief)
    return "\n\n".join(partes)


def _logo(cliente: dict, referencia: Optional[dict]):
    referencia = referencia or {}
    posicao = referencia.get("logo_posicao") or cliente["config"].get("logo_posicao", "superior-esquerdo")
    versao = referencia.get("logo_versao", "fundo-escuro")
    logos = cliente.get("logos", {})
    arquivo = (
        cliente.get("logo")
        or (cliente.get("logo_referencias")[0] if cliente.get("logo_referencias") else None)
        or logos.get(versao)
        or logos.get("fundo-escuro")
        or logos.get("principal")
    )
    return arquivo, posicao
