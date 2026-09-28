"""Agente de Design (Fotos): escreve o brief e gera a imagem final para clientes "de
fotos" (config.json com "tipo": "fotos") — hoje só o NN Restaurante.

SINTONIA TOTAL ENTRE AGENTES (COERÊNCIA GASTRONÔMICA):
1. A comida mostrada DEVE ser estritamente o prato informado pelo Curador e pela Redatora.
   Se a legenda for sobre "Frango ao Molho", a imagem DEVE ilustrar frango ao molho,
   NUNCA feijoada, bife ou outro prato.
2. Se houver foto real correspondente, aplica tratamento gráfico diagramado sobre a foto.
3. Se for prato virtual (do OlaClick sem foto no acervo), gera a cena culinária brasileira
   do zero, aplicando os detalhes físicos reais do restaurante do Nico:
   - Louça: prato branco comercial tradicional (sem luxo) ou marmitex bem servida.
   - Comida brasileira: acompanhamentos tradicionais (arroz soltinho, feijão, batata, macarrão, farofa).
   - Mesa: madeira rústica com leve textura clara/esbranquiçada.
   - Fundo desfocado: cadeiras de carvalho envernizadas, piso de cerâmica branca e parede vermelha.
   - Logotipo oficial da N&N da pasta logo/ aplicado no cabeçalho/topo.
4. PROIBIDO USAR A PALAVRA "EXECUTIVO": NUNCA renderize a palavra "executivo" na arte.
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

DIREÇÃO DE ARTE E COERÊNCIA GASTRONÔMICA:
- PRATO PRINCIPAL OBRIGATÓRIO: A comida ilustrada deve ser rigorosamente: "__PRATO_ESPECIFICO__".
  NUNCA mostre feijoada, carne vermelha ou outro prato se a refeição do dia for outra (como frango).
__CONTEXTO_CENA__
__CONTEXTO_LAYOUT__
- LOGOTIPO OFICIAL DA MARCA: uma das imagens de referência fornecidas é o logotipo oficial da
  empresa. Você DEVE reproduzir esse logotipo exatamente (mesma tipografia, símbolo/emblema, cores
  e proporções) integrado com nitidez no cabeçalho ou área de branding indicada (__AREA_LOGO__),
  com margens de respiro de cerca de 5% das bordas.

REGRAS RÍGIDAS DE DIAGRAMAÇÃO E ANTI-AMADORISMO:
1. PROIBIDO O TERMO "EXECUTIVO": NUNCA escreva ou renderize a palavra "EXECUTIVO" ou "ALMOÇO EXECUTIVO"
   na arte (nem na headline, nem no selo, nem em badges). O restaurante trabalha com preços populares
   de R$ 26 a R$ 35. Use "ALMOÇO DO DIA", "COMIDA CASEIRA", "PRATO FEITO" ou o próprio nome do prato.
2. PROIBIDO CONTORNO BRANCO / GLOW: NUNCA crie letras com sombra branca difusa, contorno branco
   grosso (stroke) ou glow esfumado atrás do texto. Tipografia sólida, nítida e sofisticada.
3. PROIBIDO SELO EM ELIPSE / CARIMBO REDONDO COM TALHERES: NUNCA desenhe selos circulares ou
   carimbos com garfo e faca. Use etiquetas retangulares limpas ou integre o texto de forma minimalista.
4. MARGENS DE SEGURANÇA:
   - Deixe pelo menos __MARGEM__% de respiro livre no topo e no rodapé.
   - Mantenha texto e logo a pelo menos __MARGEM_LATERAL__% de distância das bordas.

O brief (em inglês) deve definir, em um parágrafo denso e direto:
- A cena gastronômica precisa exibindo exatamente __PRATO_ESPECIFICO__;
- A headline exata, sem contornos brancos e sem a palavra 'executivo';
- A ausência total de elipses/selos circulares;
- A reprodução fiel do logotipo oficial fornecido como referência na área de branding indicada.

Retorne APENAS o brief em texto corrido, em inglês — exceto a headline e o selo, citados
entre aspas exatamente em português. Sem explicações, sem markdown, sem listas.
"""

CENA_FOTO_REAL = """
- BASE DA CENA: a foto real de referência é o herói da imagem. Os ingredientes, carnes,
  acompanhamentos e porção real devem ser preservados com fidelidade sobre a mesa de madeira rústica,
  sem mãos amadoras ou embalagens plásticas descartáveis.
"""

CENA_PRATO_VIRTUAL = """
- FOTOGRAFIA GASTRONÔMICA BRASILEIRA DO RESTAURANTE DO NICO:
  Crie uma fotografia editorial e apetitosa de comida caseira brasileira recém-servida:
  1. LOUÇA E APRESENTAÇÃO: Servido em prato branco simples de louça de restaurante comercial (louça
     tradicional sem luxo excessivo) OU em uma marmitex brasileira tradicional bem servida e farta.
  2. COMIDA BRASILEIRA REAL E ACOMPANHAMENTOS: A porção é farta, quente e apetitosa.
     O prato principal (__PRATO_ESPECIFICO__) deve vir acompanhado das guarnições clássicas de almoço
     comercial brasileiro: arroz branco soltinho, feijão temperado, batata cozida ou frita douradinha,
     um toque de macarrão ao molho e farofinha crocante. Comida fumegante com brilho natural de comida fresca.
     NUNCA renderize feijoada se o prato do dia não for feijoada.
  3. MESA E AMBIENTAÇÃO DO RESTAURANTE: Mesa de madeira rústica com leve textura clara/esbranquiçada
     (veios da madeira com leve pátina clara). Ao fundo, com profundidade de campo suave (bokeh):
     cadeiras de madeira em tom carvalho escuro envernizado, piso de cerâmica branca e toques sutis de
     parede vermelha aconchegante. Enquadramento fechado e convidativo no prato.
"""

CONTEXTO_COM_REFERENCIA = (
    "- REFERÊNCIA DE LAYOUT DA MARCA: use esta referência apenas como guia de ESTRUTURA GRÁFICA "
    "  (alinhamento e respiro tipográfico). NUNCA copie a comida ou textos que estiverem nela;"
)
CONTEXTO_SEM_REFERENCIA = (
    "- SEM TEMPLATE ESPECÍFICO: siga o KV oficial do cliente com diagramação moderna, clean e equilibrada;"
)


def _gerar_descricao_culinaria_visual(nome_prato: str, descricao: str = "") -> str:
    """Gera uma descrição visual culinária em inglês precisa para evitar alucinações (como feijoada em dia de frango)."""
    nome = nome_prato.lower()
    if "frango" in nome and ("molho" in nome or "ensopado" in nome or "cozido" in nome):
        return (
            "tender chicken thighs and drumsticks slow-cooked in a rich, savory homemade Brazilian tomato and onion sauce "
            "(frango ao molho caseiro), garnished with fresh parsley. Served on a simple white commercial restaurant plate, "
            "accompanied by fluffy white rice, Brazilian brown beans (feijão carioca), sautéed potatoes, a small portion of macaroni pasta with tomato sauce, and golden cassava flour (farofa). "
            "STRICTLY FORBIDDEN: do NOT depict feijoada, black beans stew, beef steaks, or dark stew."
        )
    elif "feijoada" in nome:
        return (
            "traditional Brazilian feijoada with rich black beans, smoked sausage, pork ribs, and jerked beef, "
            "accompanied by white rice, sautéed collard greens (couve), crispy pork rinds (torresmo), and golden farofa."
        )
    elif "bife" in nome or "carne" in nome:
        return (
            "succulent Brazilian sautéed beef steak with golden caramelized onions (bife acebolado), "
            "served on a white restaurant plate with fluffy white rice, savory brown beans, potatoes, macaroni pasta, and farofa."
        )
    elif "picadinho" in nome:
        return (
            "rich Brazilian beef stew in bite-sized cubes with tender carrots and potatoes in a thick rich gravy (picadinho com batata), "
            "served on a white restaurant plate alongside white rice, brown beans, macaroni, and farofa."
        )
    elif "parmegiana" in nome:
        return (
            "crispy golden breaded cutlet (parmegiana) topped with melted mozzarella cheese and fresh homemade tomato sauce, "
            "served with white rice and golden crispy french fries."
        )
    else:
        return (
            f"authentic Brazilian homemade daily special '{nome_prato}' ({descricao}), "
            "generously served on a simple white commercial restaurant plate with fluffy white rice, seasoned brown beans, potatoes, macaroni pasta, and toasted farofa. Fresh, hot, and steaming."
        )


def gerar_brief_foto(copy: dict, foto: dict, cliente: dict, referencia: Optional[dict]) -> str:
    contexto = CONTEXTO_COM_REFERENCIA if (referencia and not foto.get("foto_virtual")) else CONTEXTO_SEM_REFERENCIA
    cena_desc = CENA_PRATO_VIRTUAL if foto.get("foto_virtual") else CENA_FOTO_REAL
    _, posicao_logo = _logo(cliente, referencia)

    nome_prato = foto.get("nome") or (foto["arquivo"].stem if foto.get("arquivo") else "Prato do Dia")
    desc_prato = foto.get("descricao") or ""

    system = (
        SYSTEM_PROMPT.replace("__SKILL__", cliente["skill"])
        .replace("__PRATO_ESPECIFICO__", nome_prato)
        .replace("__CONTEXTO_CENA__", cena_desc)
        .replace("__CONTEXTO_LAYOUT__", contexto)
        .replace("__MARGEM__", str(_margem_corte_vertical()))
        .replace("__MARGEM_LATERAL__", str(MARGEM_SEGURANCA_BORDA))
        .replace("__AREA_LOGO__", AREAS_LOGO.get(posicao_logo, "top header / branding area"))
    )
    partes = [f"Prato do dia obrigatório: {nome_prato}"]
    if foto.get("categoria"):
        partes.append(f"Categoria: {foto['categoria']}")
    if desc_prato:
        partes.append(f"Descrição dos ingredientes: {desc_prato}")
    partes.append(f'Headline da arte: "{copy.get("headline_imagem")}"')
    if copy.get("selo_produto"):
        # Garante que não use 'executivo' no selo
        selo_limpo = copy["selo_produto"].replace("Executivo", "do Dia").replace("executivo", "do Dia")
        partes.append(f'Selo do prato: "{selo_limpo}"')
    else:
        partes.append("Selo do prato: NENHUM (não desenhe selo circular)")

    if foto.get("foto_virtual"):
        culinaria_especifica = _gerar_descricao_culinaria_visual(nome_prato, desc_prato)
        partes.append(
            f"DIRETRIZ VISUAL ESPECÍFICA DESTE PRATO:\n"
            f"- Comida: {culinaria_especifica}\n"
            f"- Cenário do Nico: Prato comercial branco simples sobre mesa de madeira rústica clara. Fundo desfocado com cadeiras de carvalho e parede vermelha.\n"
            f"- Proibição: NUNCA desenhe feijoada ou prato diferente de '{nome_prato}'. NUNCA escreva a palavra 'EXECUTIVO'."
        )
    else:
        partes.append(
            "Aplicação do logotipo oficial: entre as imagens de referência fornecidas, utilize a imagem "
            "oficial do logotipo da empresa, reproduzindo-o fielmente no cabeçalho da peça."
        )

    return chamar_ia(system=system, prompt="\n".join(partes), max_tokens=750, temperature=0.7)


def gerar_imagem_foto(brief: str, foto: dict, cliente: dict, referencia: Optional[dict]) -> dict:
    """Gera a imagem do post garantindo coerência culinária e aplicação do logotipo oficial."""
    avisos = []
    referencias_imagem = []

    # 1. Se houver arquivo de foto real, inclui como referência principal
    if foto.get("arquivo") and not foto.get("foto_virtual"):
        referencias_imagem.append((
            foto["arquivo"].read_bytes(),
            "the reference photo showing the authentic dish/food served by the restaurant. "
            "Preserve this exact meal, ingredients, and culinary richness faithfully, but ELEVATE the "
            "presentation into professional food photography: stage the dish in an appetizing "
            "restaurant dining setting (on a warm rustic wooden table, natural warm restaurant lighting, "
            "soft background dining room bokeh). If the original photo has awkward hands holding a container "
            "or a distracting domestic wall/plant background, remove the hands and domestic clutter, "
            "and present the delicious food cleanly and appetisingly on the table.",
        ))
        # Template de layout só vai se tiver foto real (para não contaminar pratos virtuais com comida do template)
        if referencia:
            referencias_imagem.append((
                referencia["arquivo"].read_bytes(),
                "this brand's layout reference template. Emulate its graphic design hierarchy only: "
                "the typography styling, spacing, clean alignment, and balance. "
                "Do NOT copy the specific food items depicted in this template.",
            ))

    # 2. Logotipo oficial da marca (sempre incluído quando disponível)
    logo_arquivo, posicao_logo = _logo(cliente, referencia)
    if logo_arquivo:
        referencias_imagem.append((
            logo_arquivo.read_bytes(),
            "the official BRAND LOGO of the company. You must reproduce this exact logo "
            "(typography, symbols, monogram, and colors) into the graphic layout of the post. "
            "Position it cleanly in the header or designated branding zone with strong contrast and breathing room.",
        ))

    bruta = None
    layout_usado = referencia["arquivo"].name if (referencia and not foto.get("foto_virtual")) else None
    try:
        if referencias_imagem:
            imagens = [dados for dados, _ in referencias_imagem]
            prompt = _prompt_com_referencias(brief, [desc for _, desc in referencias_imagem])
            bruta = openai_client.gerar_imagem_com_referencias(prompt, imagens)
        else:
            bruta = openai_client.gerar_imagem(brief)
    except Exception as exc:
        raise RuntimeError(f"A geração da imagem falhou ({exc}).") from exc
    if not bruta or not bruta.get("imagem_b64"):
        raise RuntimeError("A API de imagem não retornou nenhuma imagem.")

    if bruta.get("tamanho_pedido") and bruta.get("tamanho_real") and bruta["tamanho_pedido"] != bruta["tamanho_real"]:
        avisos.append(
            f"A API pediu {bruta['tamanho_pedido']} mas devolveu {bruta['tamanho_real']} — "
            "o tamanho final ainda sai certo (1080x1440, sem cortar nada), mas pode ter "
            "uma distorção leve de proporção nesse post."
        )

    return {
        **_finalizar(base64.b64decode(bruta["imagem_b64"])),
        "modelo": bruta.get("modelo"),
        "qualidade": bruta.get("qualidade"),
        "tamanho_gerado": bruta.get("tamanho_real"),
        "referencia_layout": layout_usado,
        "com_foto_real": not foto.get("foto_virtual", False),
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
