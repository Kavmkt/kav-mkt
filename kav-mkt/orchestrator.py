"""Orquestrador da Kav (@kav.mkt).

Coordena a esteira multi-agente para os clientes da agência:
- gerar_post: produtos de catálogo (ex: ponto-car)
- gerar_carrossel: pautas de conteúdo educativo/carrossel (ex: kav)
- gerar_post_fotos: fotos reais ou cardápio do dia OlaClick com tratamento diagramado (ex: nn-restaurante)
- gerar_campanha: campanhas de performance com análise de concorrência e layout de anúncios
"""
import json
from typing import Callable, Optional

from agents.agente_carrossel import gerar_imagens_carrossel, gerar_roteiro
from agents.agente_catalogo import escolher_produto
from agents.agente_design import escolher_referencia, gerar_brief, gerar_imagem
from agents.agente_design_fotos import gerar_brief_foto, gerar_imagem_foto
from agents.agente_foto import escolher_foto
from agents.agente_legenda import gerar_legenda
from agents.agente_legenda_fotos import gerar_copy_foto
from agents.agente_pauta import escolher_pauta
from utils import historico
from utils.cliente import CLIENTES_DIR, carregar_cliente


def gerar_post(slug: str, com_imagem: bool = True, etapa: Optional[Callable[[str], None]] = None) -> dict:
    avisar = etapa or (lambda _texto: None)
    cliente = carregar_cliente(slug)

    avisar("Escolhendo o produto campeão de vendas do catálogo...")
    produto = escolher_produto(cliente)
    avisos = list(produto.pop("avisos", []))

    avisar(f"Escrevendo chamada e legenda para: {produto.get('nome')}")
    copy = gerar_legenda(produto, cliente)
    post = {
        "cliente": cliente["nome"],
        "produto": produto,
        "copy": copy,
        "referencia": None,
        "brief": None,
        "imagem": None,
        "avisos": avisos,
    }

    if not com_imagem:
        avisos.append("Modo teste (sem imagem): este produto não entrou no histórico.")
        return post

    post["referencia"] = escolher_referencia(cliente)
    avisar("Montando o brief visual...")
    post["brief"] = gerar_brief(copy, produto, cliente, post["referencia"])
    avisar("Gerando a imagem (pode levar até 1 minuto)...")
    post["imagem"] = gerar_imagem(post["brief"], produto, cliente, post["referencia"])
    if post["imagem"].get("aviso"):
        avisos.append(post["imagem"]["aviso"])

    if com_imagem and post.get("imagem"):
        try:
            from agents.agente_diretor_arte import revisar_e_aprovar_layout
            post["imagem"] = revisar_e_aprovar_layout(
                post["imagem"],
                copy=copy,
                foto=produto,
                cliente=cliente,
                referencia=post["referencia"],
                modo="organico",
                etapa=avisar,
            )
        except Exception as exc:
            avisos.append(f"Direção de Arte automática ignorada ({exc}).")

    try:
        historico.registrar(slug, {
            "produto_id": produto["id"],
            "produto_nome": produto.get("nome"),
            "headline": copy.get("headline_imagem"),
            "legenda": copy.get("legenda"),
            "referencia_layout": post["imagem"].get("referencia_layout"),
        })
    except Exception as exc:
        avisos.append(f"Não consegui salvar no histórico ({exc}); este produto pode se repetir.")

    try:
        from utils import estado_agentes
        estado_agentes.registrar_post_produzido(post, slug)
    except Exception:
        pass

    return post


def gerar_carrossel(
    slug: str, num_paginas: int = 5, com_imagem: bool = True, etapa: Optional[Callable[[str], None]] = None
) -> dict:
    avisar = etapa or (lambda _texto: None)
    cliente = carregar_cliente(slug)
    num_paginas = max(1, min(7, num_paginas))

    avisar("Escolhendo a pauta do carrossel...")
    pauta = escolher_pauta(cliente)
    avisos = list(pauta.pop("avisos", []))

    avisar(f"Escrevendo o roteiro ({num_paginas} páginas): {pauta.get('tema')}")
    roteiro = gerar_roteiro(pauta, cliente, num_paginas)

    post = {
        "cliente": cliente["nome"],
        "pauta": pauta,
        "roteiro": roteiro,
        "referencia": None,
        "slides": None,
        "avisos": avisos,
    }

    if not com_imagem:
        avisos.append("Modo teste (sem imagem): esta pauta não entrou no histórico.")
        return post

    post["referencia"] = escolher_referencia(cliente)
    post["slides"] = gerar_imagens_carrossel(roteiro, cliente, pauta.get("tema", ""), post["referencia"], etapa=avisar)

    try:
        historico.registrar(slug, {
            "produto_id": pauta["id"],
            "produto_nome": pauta.get("tema"),
            "headline": roteiro["paginas"][0].get("titulo") if roteiro.get("paginas") else None,
            "legenda": roteiro.get("legenda"),
        })
    except Exception as exc:
        avisos.append(f"Não consegui salvar no histórico ({exc}); esta pauta pode se repetir.")

    try:
        from utils import estado_agentes
        estado_agentes.registrar_post_produzido(post, slug)
    except Exception:
        pass

    return post


def gerar_post_fotos(slug: str, com_imagem: bool = True, etapa: Optional[Callable[[str], None]] = None) -> dict:
    avisar = etapa or (lambda _texto: None)
    cliente = carregar_cliente(slug)

    avisar("Consultando cardápio do dia no OlaClick e acervo de fotos...")
    foto = escolher_foto(cliente)
    avisos = list(foto.pop("avisos", []))

    nome_prato = foto.get("nome") or (foto["arquivo"].stem if foto.get("arquivo") else "Prato do Dia")
    avisar(f"Escrevendo chamada, selo e legenda para: {nome_prato}")
    copy = gerar_copy_foto(foto, cliente)
    post = {
        "cliente": cliente["nome"],
        "foto": foto,
        "copy": copy,
        "referencia": None,
        "brief": None,
        "imagem": None,
        "avisos": avisos,
    }

    if not com_imagem:
        avisos.append("Modo teste (sem imagem): este prato não entrou no histórico.")
        return post

    post["referencia"] = escolher_referencia(cliente)
    avisar(f"Montando o brief do layout para '{nome_prato}'...")
    post["brief"] = gerar_brief_foto(copy, foto, cliente, post["referencia"])
    avisar("Gerando a imagem da peça (pode levar até 1 minuto)...")
    post["imagem"] = gerar_imagem_foto(post["brief"], foto, cliente, post["referencia"])
    if post["imagem"].get("aviso"):
        avisos.append(post["imagem"]["aviso"])

    if com_imagem and post.get("imagem"):
        try:
            from agents.agente_diretor_arte import revisar_e_aprovar_layout
            post["imagem"] = revisar_e_aprovar_layout(
                post["imagem"],
                copy=copy,
                foto=foto,
                cliente=cliente,
                referencia=post["referencia"],
                modo="organico",
                etapa=avisar,
            )
        except Exception as exc:
            avisos.append(f"Direção de Arte automática ignorada ({exc}).")

    try:
        historico.registrar(slug, {
            "produto_id": foto.get("id") or (foto["arquivo"].stem if foto.get("arquivo") else "prato"),
            "produto_nome": nome_prato,
            "headline": copy.get("headline_imagem"),
            "legenda": copy.get("legenda"),
            "referencia_layout": post["imagem"].get("referencia_layout"),
        })
    except Exception as exc:
        avisos.append(f"Não consegui salvar no histórico ({exc}); este prato pode se repetir.")

    try:
        from utils import estado_agentes
        estado_agentes.registrar_post_produzido(post, slug)
    except Exception:
        pass

    return post


def gerar_campanha(
    slug: str, com_imagem: bool = True, etapa: Optional[Callable[[str], None]] = None
) -> dict:
    """Cria uma peça completa de campanha de tráfego pago (Meta Ads) com pesquisa
    aprofundada de concorrência, inteligência de performance e layout com forte
    hierarquia tipográfica."""
    avisar = etapa or (lambda _texto: None)
    cliente = carregar_cliente(slug)
    avisos = []

    # 1. Escolha do prato/foto (com suporte a OlaClick)
    avisar("1/4 [Curador]: Selecionando prato do dia no OlaClick ou acervo...")
    foto = escolher_foto(cliente)
    avisos.extend(foto.pop("avisos", []))

    # 2. Estrategista de Performance (Gestor de Tráfego)
    from agents.agente_estrategia_campanha import criar_estrategia_campanha
    nome_prato = foto.get("nome") or (foto["arquivo"].stem if foto.get("arquivo") else "Prato")
    avisar(f"2/4 [Estrategista]: Analisando concorrência e desenhando estratégia para '{nome_prato}'...")
    estrategia = criar_estrategia_campanha(cliente, foto_escolhida=foto)

    # 3. Designer de Performance & Layout de Campanha
    from agents.agente_layout_campanha import montar_brief_layout, gerar_arte_campanha
    h_destaque = estrategia.get("hierarquia_visual", {}).get("headline_destaque", "ALMOÇO DE QUALIDADE")
    avisar(f"3/4 [Diretor de Arte]: Projetando layout com hierarquia visual e headline '{h_destaque}'...")
    brief = montar_brief_layout(estrategia, foto, cliente)

    # 4. Geração de Arte
    imagem = None
    if com_imagem:
        avisar("4/4 [Designer]: Renderizando arte 1080x1440 com foto e logo oficial da N&N...")
        imagem = gerar_arte_campanha(brief, foto, cliente, estrategia)
        try:
            from agents.agente_diretor_arte import revisar_e_aprovar_layout
            imagem = revisar_e_aprovar_layout(
                imagem,
                copy={
                    "headline_imagem": estrategia["hierarquia_visual"]["headline_destaque"],
                    "headline_apoio": estrategia["hierarquia_visual"]["headline_apoio"],
                    "selo_produto": estrategia["hierarquia_visual"]["selo"],
                    "cta_local": estrategia["hierarquia_visual"]["cta_visual"],
                },
                foto=foto,
                cliente=cliente,
                referencia=None,
                modo="campanha",
                etapa=avisar,
            )
        except Exception as exc:
            avisos.append(f"Direção de Arte automática ignorada ({exc}).")
    else:
        avisos.append("Modo teste sem imagem ativado.")

    copy_anuncio = estrategia.get("copy_anuncio", {})
    legenda_formatada = (
        f"{copy_anuncio.get('gancho_linha_1', '')}\n\n"
        f"{copy_anuncio.get('corpo', '')}\n\n"
        f"📍 Av. Ten. Marques, 4131 - Vila Poupança, Santana de Parnaíba / Cajamar - SP\n"
        f"⏰ Almoço de Segunda a Sábado, das 11h às 15h\n"
        f"🚗 Estacionamento fácil no entorno · Salão aconchegante\n\n"
        f"{copy_anuncio.get('cta_final', '👉 Venha almoçar hoje ou toque no link para ver a localização exata!')}\n\n"
        f"#SantanaDeParnaiba #AlmocoDoDia #ComidaCaseira #PratoFeito #NNRestaurante"
    )

    resultado = {
        "cliente": cliente["nome"],
        "tipo_producao": "campanha_performance",
        "foto": foto,
        "estrategia": estrategia,
        "brief": brief,
        "imagem": imagem,
        "copy": {
            "headline_imagem": estrategia["hierarquia_visual"]["headline_destaque"],
            "headline_apoio": estrategia["hierarquia_visual"]["headline_apoio"],
            "selo_produto": estrategia["hierarquia_visual"]["selo"],
            "cta_local": estrategia["hierarquia_visual"]["cta_visual"],
            "legenda": legenda_formatada,
        },
        "avisos": avisos,
    }

    try:
        from utils import estado_agentes
        estado_agentes.registrar_post_produzido(resultado, slug)
    except Exception:
        pass

    return resultado
