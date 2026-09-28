"""Agente de Design (Fotos): escreve o brief e gera a imagem final para clientes "de
fotos" (config.json com "tipo": "fotos") — hoje só o NN Restaurante.

DIRETRIZ CENTRAL DE ARTE — OPÇÃO B (RECORTE & AMBIENTAÇÃO DA FOTO REAL):
1. A comida mostrada na foto real de referência (foto['arquivo']) é a comida física autêntica do restaurante.
2. A IA NUNCA gera comida sintética com IA nem troca os ingredientes reais por render 3D ou texturas plásticas.
3. A IA atua como recortadora e ambientadora: isola/recorta o prato com a comida original de verdade do cliente
   e insere-o em um novo cenário esteticamente impecável (mesa de madeira nobre rústica com iluminação natural
   quente de almoço e sombra suave de contato sob o prato, fundo desfocado de restaurante acolhedor).
4. Aplica a diagramação editorial da marca: headline de impacto em Playfair Display, selo minimalista
   em Montserrat ('Qualidade Garantida' - PROIBIDO 'Almoço do Dia' e 'executivo'), e o logotipo oficial da
   N&N Restaurante no cabeçalho com alto contraste e respiro.
5. Preservação de textura fotográfica: 100% das texturas reais da comida de câmera (fibras reais, temperos,
   molho natural sem brilho de silicone) são mantidas, eliminando qualquer cara de IA.
6. Rodapé 100% limpo: Sem frases pequenas embaixo e sem ícones com texto pequeno.
"""
from __future__ import annotations

import base64
from typing import Optional

from agents.agente_design import AREAS_LOGO, MARGEM_SEGURANCA_BORDA, _margem_corte_vertical
from utils import image_overlay, openai_client
from utils.openai_client import chamar_ia

# Placeholders substituídos com .replace() (e não .format()): a skill do cliente pode ter
# chaves {} que quebrariam o .format().
SYSTEM_PROMPT = """Você é o Diretor de Arte sênior da Kav (@kav.mkt). Sua função é escrever o
brief de UMA peça do Instagram para o NN Restaurante, pronto para ser enviado direto ao gerador de
imagem da OpenAI (GPT Image 2.5 Sunburst).

DIRETRIZES DE MARCA E KV DO CLIENTE:
__SKILL__

DIREÇÃO DE ARTE — OPÇÃO B (RECORTE & COMPOSIÇÃO DA FOTO REAL, ZERO CARA DE IA):
- COMIDA 100% REAL E AUTÊNTICA: A comida mostrada na Referência 1 é a foto física real do restaurante.
  NÃO gere comida sintética por IA. O prato/travessa com a refeição autêntica deve ser isolado/recortado
  e ancorado sobre a nova mesa, preservando rigorosamente as cores, texturas orgânicas e imperfeições
  naturais da fotografia real de câmera.
- PROIBIÇÃO TERMINANTE DE TEXTURAS GROTESCAS / IA: É expressamente proibido qualquer acabamento plástico,
  pele de frango encerada ou emborrachada, molho com brilho de silicone ou aspecto de render 3D/CGI.
- PAPEL EXCLUSIVO DA GERAÇÃO POR IA:
  1. AMBIENTAÇÃO DE FUNDO: Gerar a nova superfície de mesa de madeira rústica acolhedora sob o prato,
     com iluminação natural suave de restaurante e sombra de contato fotográfica realista sob o prato.
     No topo/fundo, um ambiente aconchegante de restaurante suavemente desfocado (bokeh).
  2. DIAGRAMAÇÃO EDITORIAL: Posicionar a headline em tipografia refinada (Playfair Display), o selo
     minimalista retangular e o logotipo oficial da marca no cabeçalho.
__CONTEXTO_LAYOUT__
- LOGOTIPO OFICIAL DA MARCA: uma das imagens de referência fornecidas é o logotipo oficial da empresa.
  Você DEVE reproduzir esse logotipo exatamente (mesma tipografia, símbolo/emblema, cores e proporções)
  integrado com nitidez no cabeçalho ou área de branding indicada (__AREA_LOGO__), com respiro de borda.

REGRAS RÍGIDAS DE DIAGRAMAÇÃO E ANTI-AMADORISMO:
1. PROIBIDO "ALMOÇO DO DIA" OU REFERÊNCIAS A HORÁRIO DE ALMOÇO NO LAYOUT:
   - Como os posts serão publicados também durante a tarde e noite para alcançar mais seguidores,
     NUNCA escreva ou renderize "ALMOÇO DO DIA", "ALMOÇO EXECUTIVO" ou a palavra "ALMOÇO" em destaque no layout.
   - Use chamadas atemporais e focadas no sabor e tradição do prato (ex: "Feito no Capricho", "Sabor Inconfundível", "Receita Tradicional", "Tradição em Cada Sabor" ou o próprio nome do prato).
2. RODAPÉ 100% LIMPO (PROIBIDO FRASES PEQUENAS E ÍCONES EM BAIXO):
   - NUNCA adicione frases pequenas no rodapé da arte (como "Boa comida faz bons encontros", slogans soltos ou legendas miúdas).
   - NUNCA adicione barras de ícones com textos pequenos (ex: "Ingredientes de qualidade | Mais que comida | Tradição").
   - A parte inferior deve ser totalmente desobstruída e limpa, deixando a mesa rústica e o prato brilharem com respiro.
3. SELO "QUALIDADE GARANTIDA" (SE HOUVER SELO):
   - Se for usar algum elemento de selo/etiqueta na arte, use EXCLUSIVAMENTE a frase menor "Qualidade Garantida" (etiqueta retangular minimalista, sóbria e discreta).
   - NUNCA desenhe selos redondos, elipses com garfo e faca ou carimbos clichês.
4. PROIBIDO CONTORNO BRANCO / GLOW: NUNCA crie letras com sombra branca difusa ou contorno grosso. Tipografia sólida em Playfair Display.
5. MARGENS DE SEGURANÇA:
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
        f"Detalhes da receita: {desc_prato}" if desc_prato else "",
        f'Headline da arte (atemporal, sem a palavra almoço): "{copy.get("headline_imagem")}"',
    ]
    selo_texto = "Qualidade Garantida" if copy.get("selo_produto") else "nenhum"
    partes.append(f'Selo do prato (se renderizar, use estritamente formato retangular minimalista com): "{selo_texto}"')

    partes.append(
        f"DIRETRIZ DE EXECUÇÃO (OPÇÃO B - COMPOSIÇÃO FOTOGRÁFICA DO PRATO REAL): "
        f"The authentic food plate of '{nome_prato}' from Reference 1 MUST NOT be resynthesized or repainted by AI. "
        "Treat it as an authentic photographic cutout: preserve the exact real camera textures of the meat, sauce, and garnish without waxy/plastic AI smoothing. "
        "Your task is to generate the surrounding professional environment: stage the cutout dish onto a beautiful rustic wooden dining table with soft realistic contact shadows and natural lunch light. "
        "Behind and above, render a warm, softly blurred restaurant interior. In the header, display the official N&N logo and the headline in elegant Playfair Display with high contrast. "
        "STRICT PROHIBITIONS: NEVER write 'Almoço do Dia' or lunch-bound phrasing (the post will run in the afternoon/evening). "
        "NEVER add small text phrases at the bottom (no footer slogans like 'Boa comida faz bons encontros') and NO icon rows with small text at the bottom. Keep the lower third clean and breathing. "
        "If a badge is added, it must say strictly 'Qualidade Garantida'."
    )

    return chamar_ia(system=system, prompt="\n".join(p for p in partes if p), max_tokens=750, temperature=0.7)


def gerar_imagem_foto(brief: str, foto: dict, cliente: dict, referencia: Optional[dict]) -> dict:
    """Gera a imagem do post diagramando e elevando o cenário sobre a foto REAL do cliente."""
    avisos = []
    referencias_imagem = [
        (
            foto["arquivo"].read_bytes(),
            "the HERO AUTHENTIC CAMERA PHOTOGRAPH of N&N Restaurante. "
            "CRITICAL OPTION B RULE: This is the real physical dish served by the client. "
            "DO NOT repaint, redraw, or synthesize the food with AI. "
            "Keep the authentic dish, real meat textures, natural seasonings, and real sauce 100% intact as a photographic element. "
            "Isolate this authentic dish and stage it cleanly on a beautiful, warm rustic wooden dining table with soft contact drop-shadow, "
            "under warm natural lunch daylight with soft restaurant background bokeh, without altering the food into 3D CGI.",
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
    partes = [
        "TASK: High-end culinary social media ad design (1080x1440 portrait) for N&N Restaurante.",
        "MANDATORY EXECUTION DIRECTIVE (OPTION B - REAL FOOD PRESERVATION & SCENE COMPOSITION):\n"
        "- Reference 1 is the AUTHENTIC CLIENT CAMERA PHOTO. DO NOT generate artificial or synthetic food. "
        "Keep the dish and food from Reference 1 intact, preserving genuine culinary textures, authentic roasted chicken skin, "
        "natural herbs, and matte homemade sauce without ANY waxy, plastic, or 3D CGI gloss.\n"
        "- Cutout/isolate the authentic dish and stage it seamlessly onto a rustic wooden dining table with realistic soft contact shadows.\n"
        "- In the upper portion, create a softly blurred, warm ambient restaurant dining background.\n"
        "- Graphic design rules: Display prominent Playfair Display headline at the top/center (focus on dish flavor and craftsmanship; NEVER write 'Almoço do Dia' or lunch-restricted phrasing), optional minimal rectangular badge saying strictly 'Qualidade Garantida', and the authentic brand logo in the header.",
        "- STRICT CLEAN FOOTER MANDATE: The lower portion and bottom of the image must remain COMPLETELY CLEAN. DO NOT add small footer phrases (no 'Boa comida faz bons encontros'), and DO NOT add icon rows with tiny text. Only the authentic dish, rustic wood, and natural shadows.",
    ]
    for i, desc in enumerate(descricoes):
        partes.append(f"Reference image {i + 1}: {desc}")
    partes.append("Art Direction Brief:\n" + brief)
    return "\n\n".join(partes)


def _logo(cliente: dict, referencia: Optional[dict]):
    referencia = referencia or {}
    posicao = referencia.get("logo_posicao") or cliente["config"].get("logo_posicao", "superior-centro")
    versao = referencia.get("logo_versao", "fundo-escuro")
    arquivo = cliente["logos"].get(versao) or cliente["logos"].get("fundo-escuro") or cliente["logos"].get("principal")
    return arquivo, posicao
