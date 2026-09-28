"""Agente de Design (Fotos): escreve o brief e gera a imagem final para clientes "de
fotos" (config.json com "tipo": "fotos") — hoje só o NN Restaurante.

SISTEMA DE VARIAÇÃO CRIATIVA DE LAYOUTS (SORTEIO DINÂMICO DE COMPOSIÇÃO):
Para evitar peças repetitivas com o mesmo layout rígido (logo sempre no mesmo ponto, texto sempre
no mesmo lugar e prato embaixo), o agente sorteia entre estilos de composição elegantes e coerentes:

1. 'editorial_classico' (padrão preferido):
   - Logo centralizado no topo com respiro, headline em Playfair Display, selo "Qualidade Garantida",
     prato/travessa autêntico sobre a mesa de madeira rústica.
2. 'marmita_delivery' (marmitex redonda de isopor oficial do restaurante):
   - A comida real farta servida na tradicional marmita redonda de isopor branca de entrega.
   - REGRA RÍGIDA: PROIBIDO talheres em volta (é delivery, não mesa de jantar).
   - Headline com foco em comida quentinha em casa ou onde o cliente estiver.
3. 'minimalista_fotografico' (foto hero clean):
   - A fotografia real da comida domina 80%+ do espaço em close apetitoso e suculento.
   - Logo discreto no canto e chamada super curta ou apenas o selo "Qualidade Garantida".
4. 'editorial_lateral_moderno' (diagramação assimétrica com cores da marca):
   - Texto alinhado à esquerda ou em bloco/tarja com cores da marca (#A31D1D vinho/bordô ou #2A2A2E grafite)
     com tipografia em off-white quente ou dourado suave, e prato em ângulo dinâmico à direita.

REGRAS GERAIS INVIOLÁVEIS EM TODOS OS ESTILOS:
- PROIBIDO "Almoço do Dia" ou termos restritos ao almoço (posts saem à tarde/noite).
- RODAPÉ 100% LIMPO: NUNCA colocar frases pequenas embaixo (ex: "Boa comida faz bons encontros")
  nem barras de ícones com texto minúsculo.
- SELO (se houver): EXCLUSIVAMENTE a frase menor "Qualidade Garantida".
- COMIDA REAL INTACTA: 100% sem cara de IA, sem texturas plásticas, enceradas ou 3D CGI.
"""
from __future__ import annotations

import base64
import random
from typing import Optional

from agents.agente_design import AREAS_LOGO, MARGEM_SEGURANCA_BORDA, _margem_corte_vertical
from utils import image_overlay, openai_client
from utils.openai_client import chamar_ia

ESTILOS_LAYOUT_DISPONIVEIS = [
    {
        "id": "editorial_classico",
        "nome": "Clássico Editorial Centralizado",
        "peso": 35,
        "posicao_logo": "superior-centro",
        "cor_destaque": "off-white quente (#F5EFE6)",
        "diretriz_cena": (
            "Composição editorial clássica e sofisticada. O prato/travessa com a comida real é o protagonista "
            "sobre a mesa de madeira nobre rústica com iluminação quente de restaurante e sombra suave de contato sob o prato. "
            "Ao fundo no topo, salão de restaurante acolhedor suavemente desfocado. "
            "Logotipo oficial no cabeçalho centralizado com respiro, e headline em Playfair Display com alto contraste."
        ),
        "regra_marmita": False,
    },
    {
        "id": "marmita_delivery",
        "nome": "Marmita Redonda de Isopor (Delivery)",
        "peso": 25,
        "posicao_logo": "superior-centro",
        "cor_destaque": "amarelo-ouro ou off-white quente",
        "diretriz_cena": (
            "Apresentação da comida autêntica do restaurante servida generosamente dentro da tradicional "
            "MARMITA REDONDA DE ISOPOR BRANCA (embalagem térmica de delivery típica brasileira). A comida vem farta, "
            "quentinha e apetitosa dentro da marmita aberta sobre a bancada rústica. "
            "REGRA RÍGIDA DE DELIVERY: É TERMINANTEMENTE PROIBIDO colocar talheres em volta (sem garfos, facas, "
            "colheres ou taças de mesa de jantar), pois trata-se de um pedido para entrega/delivery! "
            "Ambiente aconchegante ao fundo e chamada com apelo de comodidade e sabor em casa."
        ),
        "regra_marmita": True,
    },
    {
        "id": "minimalista_fotografico",
        "nome": "Minimalista Foto Hero",
        "peso": 20,
        "posicao_logo": "superior-esquerdo",
        "cor_destaque": "dourado suave (#D4AF37)",
        "diretriz_cena": (
            "Layout minimalista e de alto impacto visual onde a fotografia real do prato domina 80%+ da imagem em "
            "close editorial apetitoso e rico em texturas reais. Diagramação ultra clean: apenas o logotipo oficial da "
            "marca no canto superior esquerdo com respiro generoso e uma frase bem curta de 2 a 3 palavras "
            "(ex: 'Feito no Capricho' ou 'Sabor Inconfundível') ou o selo discreto 'Qualidade Garantida'. "
            "Sem blocos longos de texto — pureza fotográfica total."
        ),
        "regra_marmita": False,
    },
    {
        "id": "editorial_lateral_moderno",
        "nome": "Editorial Lateral Assimétrico",
        "peso": 20,
        "posicao_logo": "superior-direito",
        "cor_destaque": "vermelho bordô nobre (#A31D1D) ou dourado",
        "diretriz_cena": (
            "Diagramação assimétrica moderna com variação de cores. O texto e o logo são alinhados em uma coluna ou "
            "área lateral elegante (usando um bloco suave em vermelho bordô da marca #A31D1D ou carvão nobre #2A2A2E "
            "com tipografia em off-white ou dourado), enquanto o prato real fica posicionado em ângulo fotográfico "
            "dinâmico à direita/baixo com iluminação direcional cinematográfica."
        ),
        "regra_marmita": False,
    },
]


def sortear_estilo_layout() -> dict:
    """Sorteia um estilo de layout balanceado para garantir variedade criativa a cada post."""
    pesos = [e["peso"] for e in ESTILOS_LAYOUT_DISPONIVEIS]
    return random.choices(ESTILOS_LAYOUT_DISPONIVEIS, weights=pesos, k=1)[0]


SYSTEM_PROMPT = """Você é o Diretor de Arte sênior da Kav (@kav.mkt). Sua função é escrever o
brief de UMA peça do Instagram para o NN Restaurante, pronto para ser enviado direto ao gerador de
imagem da OpenAI (GPT Image 2.5 Sunburst).

DIRETRIZES DE MARCA E KV DO CLIENTE:
__SKILL__

ESTILO DE COMPOSIÇÃO DESTE POST: __NOME_ESTILO__
DIRETRIZ DE ARTE DO ESTILO:
__DIRETRIZ_ESTILO__

DIREÇÃO DE ARTE — PRESERVAÇÃO DA COMIDA REAL (ZERO CARA DE IA):
- COMIDA 100% REAL E AUTÊNTICA: A comida mostrada na Referência 1 é a foto física real do restaurante.
  NÃO gere comida sintética por IA. Os alimentos e receitas autênticas devem ser isolados/recortados
  e posicionados no cenário definido pelo estilo, preservando 100% das cores, texturas orgânicas e
  imperfeições naturais da fotografia real de câmera.
- PROIBIÇÃO TERMINANTE DE TEXTURAS GROTESCAS / IA: É expressamente proibido acabamento plástico,
  pele de frango encerada ou emborrachada, molho com brilho de silicone ou aspecto de render 3D/CGI.
- PAPEL EXCLUSIVO DA GERAÇÃO POR IA:
  1. AMBIENTAÇÃO DE FUNDO: Gerar a nova superfície de mesa ou bancada com iluminação natural suave e
     sombra de contato fotográfica sob o prato ou marmita, com salão aconchegante desfocado ao fundo.
  2. DIAGRAMAÇÃO: Posicionar headline, selo e o logotipo oficial da marca conforme o estilo sorteado.
__CONTEXTO_LAYOUT__
- LOGOTIPO OFICIAL DA MARCA: uma das imagens de referência fornecidas é o logotipo oficial da empresa.
  Você DEVE reproduzir esse logotipo exatamente (mesma tipografia, símbolo/emblema, cores e proporções)
  integrado com nitidez na área indicada (__AREA_LOGO__), com respiro de borda.

REGRAS RÍGIDAS DE DIAGRAMAÇÃO E ANTI-AMADORISMO (VÁLIDAS PARA TODOS OS POSTS):
1. PROIBIDO "ALMOÇO DO DIA" OU TERMOS DE HORÁRIO RESTRITO:
   - Como os posts serão publicados também durante a tarde e noite para alcançar mais seguidores,
     NUNCA escreva ou renderize "ALMOÇO DO DIA", "ALMOÇO EXECUTIVO" ou a palavra "ALMOÇO" em destaque no layout.
   - Use chamadas atemporais e focadas no sabor e tradição do prato (ex: "Feito no Capricho", "Sabor Inconfundível",
     "Receita Tradicional", "Tradição em Cada Sabor" ou o próprio nome do prato).
2. RODAPÉ 100% LIMPO (PROIBIDO FRASES PEQUENAS E ÍCONES EM BAIXO):
   - NUNCA adicione frases pequenas no rodapé da arte (como "Boa comida faz bons encontros", slogans soltos ou legendas miúdas).
   - NUNCA adicione barras de ícones com textos pequenos (ex: "Ingredientes de qualidade | Mais que comida | Tradição").
   - A parte inferior deve ser totalmente desobstruída e limpa, deixando a mesa rústica e a comida respirarem.
3. SELO "QUALIDADE GARANTIDA" (SE HOUVER SELO):
   - Se for usar algum elemento de selo/etiqueta na arte, use EXCLUSIVAMENTE a frase menor "Qualidade Garantida" (etiqueta retangular minimalista, sóbria e discreta).
   - NUNCA desenhe selos redondos, elipses com garfo e faca ou carimbos clichês.
4. PROIBIDO CONTORNO BRANCO / GLOW: NUNCA crie letras com sombra branca difusa ou contorno grosso. Tipografia sólida em Playfair Display.
5. MARGENS DE SEGURANÇA:
   - Deixe pelo menos __MARGEM__% de respiro livre no topo e no rodapé.
   - Mantenha texto e logo a pelo menos __MARGEM_LATERAL__% de distância das bordas.

Retorne APENAS o brief em texto corrido, em inglês — exceto a headline e o selo, citados entre aspas exatamente em português. Sem explicações, sem markdown, sem listas.
"""


def gerar_brief_foto(
    copy: dict, foto: dict, cliente: dict, referencia: Optional[dict], estilo: Optional[dict] = None
) -> str:
    estilo_escolhido = estilo or foto.get("estilo_layout") or sortear_estilo_layout()
    foto["estilo_layout"] = estilo_escolhido
    posicao_logo_estilo = estilo_escolhido.get("posicao_logo", "superior-centro")
    _, posicao_logo = _logo(cliente, referencia, posicao_override=posicao_logo_estilo)
    nome_prato = foto.get("nome") or foto["arquivo"].stem
    desc_prato = foto.get("descricao") or ""

    system = (
        SYSTEM_PROMPT.replace("__SKILL__", cliente["skill"])
        .replace("__NOME_ESTILO__", estilo_escolhido["nome"])
        .replace("__DIRETRIZ_ESTILO__", estilo_escolhido["diretriz_cena"])
        .replace("__CONTEXTO_LAYOUT__", "- REFERÊNCIA DE LAYOUT: adapte a diagramação respeitando o estilo sorteado;")
        .replace("__MARGEM__", str(_margem_corte_vertical()))
        .replace("__MARGEM_LATERAL__", str(MARGEM_SEGURANCA_BORDA))
        .replace("__AREA_LOGO__", AREAS_LOGO.get(posicao_logo, "top header / branding area"))
    )

    headline = copy.get("headline_imagem", "Feito no Capricho")
    if estilo_escolhido["id"] == "minimalista_fotografico":
        palavras = headline.split()
        if len(palavras) > 3:
            headline = " ".join(palavras[:3])

    partes = [
        f"Estilo de Composição Sorteado: {estilo_escolhido['nome']} (ID: {estilo_escolhido['id']})",
        f"Prato real do cliente na foto de referência: {nome_prato}",
        f"Detalhes da receita: {desc_prato}" if desc_prato else "",
        f'Headline da arte: "{headline}"',
    ]

    selo_texto = "Qualidade Garantida" if copy.get("selo_produto") else "nenhum"
    partes.append(f'Selo do prato (se renderizar, use estritamente formato retangular minimalista com): "{selo_texto}"')

    if estilo_escolhido["regra_marmita"]:
        partes.append(
            f"SPECIAL COMPOSITION DIRECTIVE (DELIVERY STYROFOAM CONTAINER STYLE): "
            f"Present the authentic food meal of '{nome_prato}' from Reference 1 generously served inside a classic round white styrofoam takeout container (marmita redonda de isopor). "
            "STRICT PROHIBITION: DO NOT place dining cutlery around (NO forks, knives, spoons or glassware), as this is an authentic delivery meal ready for delivery. "
            "Keep the food textures authentic and steaming on a rustic wooden or prep counter surface. "
            "Header displays the brand logo and headline in Playfair Display. Bottom third MUST BE COMPLETELY CLEAN with no footer text or small icon bars."
        )
    elif estilo_escolhido["id"] == "minimalista_fotografico":
        partes.append(
            f"SPECIAL COMPOSITION DIRECTIVE (MINIMALIST PHOTO HERO STYLE): "
            f"The authentic camera photograph of '{nome_prato}' from Reference 1 is the HERO of the piece, occupying 80%+ of the frame in stunning, mouth-watering macro detail. "
            "Ultra-clean design: only the brand logo positioned neatly in the top-left and an ultra-short phrase or small 'Qualidade Garantida' badge. "
            "Zero clutter, zero small bottom phrases, zero icon bars."
        )
    elif estilo_escolhido["id"] == "editorial_lateral_moderno":
        partes.append(
            f"SPECIAL COMPOSITION DIRECTIVE (ASYMMETRIC EDITORIAL WITH BRAND COLORS): "
            f"Stage the authentic dish '{nome_prato}' dynamically in the lower right area. Align the headline and brand logo on an elegant left or top-right editorial block "
            "accented with brand tones (#A31D1D deep burgundy or #2A2A2E rich dark charcoal) and refined typography in warm off-white or soft gold. "
            "Keep the bottom completely clean with no small taglines."
        )
    else:
        partes.append(
            f"SPECIAL COMPOSITION DIRECTIVE (CLASSIC EDITORIAL STYLE): "
            f"Stage the authentic plate of '{nome_prato}' on a warm rustic wooden dining table with soft natural contact shadows. "
            "Display the official brand logo centered at the top and the headline in prominent Playfair Display with high contrast. "
            "Bottom third MUST BE COMPLETELY CLEAN with no footer text or small icon bars."
        )

    partes.append(
        "GENERAL MANDATES: NEVER write 'Almoço do Dia' or lunch-specific words. DO NOT add small bottom phrases (no 'Boa comida faz bons encontros') "
        "and DO NOT add small icon rows with text. Keep the food 100% photographic and free of 3D CGI plastic gloss."
    )

    brief_gerado = chamar_ia(system=system, prompt="\n".join(p for p in partes if p), max_tokens=750, temperature=0.7)
    foto["estilo_layout"] = estilo_escolhido
    return brief_gerado


def gerar_imagem_foto(
    brief: str, foto: dict, cliente: dict, referencia: Optional[dict], estilo: Optional[dict] = None
) -> dict:
    """Gera a imagem do post diagramando e elevando o cenário sobre a foto REAL do cliente."""
    avisos = []
    estilo_escolhido = estilo or foto.get("estilo_layout") or sortear_estilo_layout()
    posicao_logo_estilo = estilo_escolhido.get("posicao_logo", "superior-centro")

    desc_foto = (
        "the HERO AUTHENTIC CAMERA PHOTOGRAPH of N&N Restaurante. "
        "CRITICAL RULE: This is the real physical dish served by the client. "
        "DO NOT repaint, redraw, or synthesize the food with AI. "
        "Keep the authentic dish, real meat textures, natural seasonings, and real sauce 100% intact as a photographic element. "
    )
    if estilo_escolhido.get("regra_marmita"):
        desc_foto += (
            "Stage this authentic meal inside a classic round white styrofoam delivery lunch container (marmita redonda de isopor). "
            "STRICT DELIVERY RULE: DO NOT place dining cutlery around (no forks, knives or wine glasses). "
            "Place it cleanly on a rustic wooden or prep counter with natural contact shadows."
        )
    else:
        desc_foto += (
            "Isolate this authentic dish and stage it cleanly on a beautiful, warm rustic wooden dining table with soft contact drop-shadow, "
            "under warm natural daylight with soft restaurant background bokeh, without altering the food into 3D CGI."
        )

    referencias_imagem = [(foto["arquivo"].read_bytes(), desc_foto)]

    if referencia:
        referencias_imagem.append((
            referencia["arquivo"].read_bytes(),
            "this brand's layout reference template. Emulate its graphic design hierarchy only: "
            "the typography styling, spacing, clean alignment, and balance. "
            "Do NOT copy the specific food items depicted in this template.",
        ))

    logo_arquivo, posicao_logo = _logo(cliente, referencia, posicao_override=posicao_logo_estilo)
    if logo_arquivo:
        referencias_imagem.append((
            logo_arquivo.read_bytes(),
            "the official BRAND LOGO of N&N Restaurante. You must reproduce this exact logo "
            "(typography, symbols, monogram, and colors) into the graphic layout of the post. "
            f"Position it cleanly in the {AREAS_LOGO.get(posicao_logo, 'header area')} with strong contrast and breathing room.",
        ))

    bruta = None
    try:
        imagens = [dados for dados, _ in referencias_imagem]
        prompt = _prompt_com_referencias(brief, [desc for _, desc in referencias_imagem], estilo_escolhido)
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
        "estilo_layout": estilo_escolhido["id"],
        "estilo_nome": estilo_escolhido["nome"],
        "com_foto_real": True,
        "aviso": " ".join(avisos) or None,
    }


def _finalizar(imagem_bytes: bytes) -> dict:
    final = image_overlay.recortar_formato_final(imagem_bytes)
    return {
        "imagem_b64": base64.b64encode(final).decode("ascii"),
        "tamanho": f"{image_overlay.LARGURA_PADRAO}x{image_overlay.ALTURA_PADRAO}",
    }


def _prompt_com_referencias(brief: str, descricoes: list, estilo: dict) -> str:
    partes = [
        f"TASK: High-end culinary social media ad design (1080x1440 portrait) for N&N Restaurante in style '{estilo['nome']}'.",
        "MANDATORY EXECUTION DIRECTIVES:\n"
        "- Reference 1 is the AUTHENTIC CLIENT CAMERA PHOTO. DO NOT generate artificial or synthetic food. "
        "Keep the dish and food from Reference 1 intact, preserving genuine culinary textures, authentic roasted chicken skin, "
        "natural herbs, and matte homemade sauce without ANY waxy, plastic, or 3D CGI gloss.\n"
    ]
    if estilo.get("regra_marmita"):
        partes.append(
            "- DELIVER CONTAINER PRESENTATION: Serve the authentic meal inside a classic round white styrofoam lunch container (marmita redonda de isopor). "
            "PROHIBITED: DO NOT add cutlery around it (no forks or knives on the table).\n"
        )
    else:
        partes.append(
            "- Cutout/isolate the authentic dish and stage it seamlessly onto a rustic wooden dining table with realistic soft contact shadows.\n"
        )

    partes.append(
        "- GRAPHIC DESIGN & TYPOGRAPHY: Display prominent Playfair Display headline (NEVER write 'Almoço do Dia' or lunch-restricted phrasing), "
        "optional minimal rectangular badge saying strictly 'Qualidade Garantida', and the authentic brand logo in the header area with clear breathing room.\n"
        "- STRICT CLEAN FOOTER MANDATE: The lower portion and bottom of the image must remain COMPLETELY CLEAN. DO NOT add small footer phrases (no 'Boa comida faz bons encontros'), and DO NOT add icon rows with tiny text. Only the authentic food, rustic wood, and natural shadows."
    )

    for i, desc in enumerate(descricoes):
        partes.append(f"Reference image {i + 1}: {desc}")
    partes.append("Art Direction Brief:\n" + brief)
    return "\n\n".join(partes)


def _logo(cliente: dict, referencia: Optional[dict], posicao_override: Optional[str] = None):
    referencia = referencia or {}
    posicao = posicao_override or referencia.get("logo_posicao") or cliente["config"].get("logo_posicao", "superior-centro")
    versao = referencia.get("logo_versao", "fundo-escuro")
    arquivo = cliente["logos"].get(versao) or cliente["logos"].get("fundo-escuro") or cliente["logos"].get("principal")
    return arquivo, posicao
