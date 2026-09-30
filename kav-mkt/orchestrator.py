"""Orquestrador da Kav (@kav.mkt).

Coordena a esteira multi-agente para os clientes da agência:
- gerar_post: produtos de catálogo (ex: ponto-car)
- gerar_carrossel: pautas de conteúdo educativo/carrossel (ex: kav)
- gerar_post_fotos: fotos reais com tratamento diagramado (ex: nn-restaurante)
- gerar_campanha: campanhas de performance com análise de concorrência e layout de anúncios
"""
from __future__ import annotations
import json
from typing import Callable, Optional

from agents.agente_carrossel import gerar_imagens_carrossel, gerar_roteiro
from agents.agente_catalogo import escolher_produto
from agents.agente_design import escolher_referencia, gerar_brief, gerar_imagem
from agents.agente_design_fotos import gerar_brief_foto, gerar_imagem_foto
from agents.agente_foto import escolher_foto
from agents.agente_legenda import gerar_legenda
from agents.agente_legenda_fotos import gerar_copy_foto
from agents.agente_pauta import gerar_pauta_kav
from utils import historico
from utils.cliente import CLIENTES_DIR, carregar_cliente


def gerar_post(slug: str, com_imagem: bool = True, etapa: Optional[Callable[[str], None]] = None) -> dict:
    avisar = etapa or (lambda _texto: None)
    cliente = carregar_cliente(slug)
    tipo = cliente.get("config", {}).get("tipo", "produto")
    if slug == "kav" or tipo == "estatico":
        return gerar_post_estatico_kav(slug, com_imagem=com_imagem, etapa=etapa)
    elif tipo == "fotos":
        return gerar_post_fotos(slug, com_imagem=com_imagem, etapa=etapa)
    elif tipo == "carrossel":
        return gerar_carrossel(slug, com_imagem=com_imagem, etapa=etapa)

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
    pauta = gerar_pauta_kav(cliente)
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

    avisar("Sorteando uma foto real do repositório do cliente...")
    foto = escolher_foto(cliente)
    avisos = list(foto.pop("avisos", []))

    avisar(f"Escrevendo chamada, selo e legenda para: {foto.get('nome') or foto['arquivo'].name}")
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
        avisos.append("Modo teste (sem imagem): esta foto não entrou no histórico.")
        return post

    post["referencia"] = escolher_referencia(cliente)
    avisar("Montando o brief do tratamento sobre a foto real...")
    post["brief"] = gerar_brief_foto(copy, foto, cliente, post["referencia"])
    avisar("Gerando a imagem (pode levar até 1 minuto)...")
    post["imagem"] = gerar_imagem_foto(post["brief"], foto, cliente, post["referencia"])
    if post["imagem"].get("aviso"):
        avisos.append(post["imagem"]["aviso"])

    try:
        historico.registrar(slug, {
            "produto_id": foto["id"],
            "produto_nome": foto.get("nome") or foto["arquivo"].name,
            "headline": copy.get("headline_imagem"),
            "legenda": copy.get("legenda"),
            "referencia_layout": post["imagem"].get("referencia_layout"),
        })
    except Exception as exc:
        avisos.append(f"Não consegui salvar no histórico ({exc}); esta foto pode se repetir.")

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
    tipo = cliente.get("config", {}).get("tipo", "produto")
    if slug == "kav" or tipo == "estatico":
        return gerar_post_estatico_kav(slug, com_imagem=com_imagem, etapa=etapa)
    avisos = []

    # 1. Escolha da foto real
    avisar("1/4 [Curador]: Selecionando foto real de prato do cliente...")
    foto = escolher_foto(cliente)
    avisos.extend(foto.pop("avisos", []))

    # 2. Estrategista de Performance (Gestor de Tráfego)
    from agents.agente_estrategia_campanha import criar_estrategia_campanha
    avisar(f"2/4 [Estrategista]: Analisando concorrência e desenhando estratégia para '{foto.get('nome')}'...")
    estrategia = criar_estrategia_campanha(cliente, foto_escolhida=foto)

    # 3. Designer de Performance & Layout de Campanha
    from agents.agente_layout_campanha import montar_brief_layout, gerar_arte_campanha
    h_destaque = estrategia.get("hierarquia_visual", {}).get("headline_destaque", "ALMOÇO DE QUALIDADE")
    avisar(f"3/4 [Diretor de Arte]: Projetando layout com hierarquia visual e headline '{h_destaque}'...")
    brief = montar_brief_layout(estrategia, foto, cliente)

    # 4. Geração de Arte
    imagem = None
    if com_imagem:
        avisar("4/4 [Designer]: Renderizando arte 1080x1440 com foto real e logo da N&N...")
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
        f"#SantanaDeParnaiba #AlmocoExecutivo #ComidaCaseira #BuffetDeAlmoco #NNRestaurante"
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


def gerar_post_estatico_kav(
    slug: str = "kav", com_imagem: bool = True, etapa: Optional[Callable[[str], None]] = None
) -> dict:
    """Cria uma peça estática de alto impacto para a Kav (@kav.mkt).
    Foco em Tráfego Pago Local para PMEs e Marketing Descomplicado,
    com geração dinâmica de pauta via IA sem repetição e rotação contínua de layouts.
    """
    avisar = etapa or (lambda _texto: None)
    cliente = carregar_cliente(slug)
    avisos = []

    # 1. Pauta Inédita Dinâmica com IA (anti-repetição)
    avisar("1/4 [Curador & Pauta]: Gerando pauta inédita de Tráfego Pago Local para PMEs...")
    from agents.agente_pauta import gerar_pauta_kav
    pauta = gerar_pauta_kav(cliente)
    avisos.extend(pauta.pop("avisos", []))

    # 2. Sorteio de Layout sem repetição (round-robin) PRIMEIRO!
    avisar("2/4 [Designer]: Sorteando layout de referência sem repetição...")
    from agents.agente_estatico_kav import obter_estilo_kav, gerar_copy_kav, gerar_brief_arte_kav, gerar_imagem_estatica_kav
    referencia = historico.escolher_referencia_sem_repetir(cliente)
    estilo = obter_estilo_kav(referencia)
    if referencia:
        avisar(f"2/4 [Designer]: Arquétipo selecionado: '{estilo['nome']}' ({referencia['arquivo'].name})")

    # 3. Copywriter de Autoridade (Clarice) com formato adaptado ao arquétipo
    avisar(f"3/4 [Copywriter]: Escrevendo copy formatada para o arquétipo '{estilo['nome']}'...")
    copy = gerar_copy_kav(pauta, cliente, estilo=estilo)

    # 4. Geração de Arte Estática 4:5 com identidade visual do arquétipo
    imagem = None
    brief = None
    if com_imagem:
        avisar(f"4/4 [Designer]: Renderizando arte 4:5 (1080x1350) no formato '{estilo['nome']}'...")
        brief, estilo_usado = gerar_brief_arte_kav(copy, pauta, cliente, referencia, estilo=estilo)
        imagem = gerar_imagem_estatica_kav(brief, cliente, referencia, estilo=estilo_usado)

        ref_logo = imagem.get("referencia_logo") if imagem else None
        estilo_l = imagem.get("estilo_layout") if imagem else None
        estilo_n = imagem.get("estilo_nome") if imagem else None
        try:
            from agents.agente_diretor_arte import revisar_e_aprovar_layout
            imagem = revisar_e_aprovar_layout(
                imagem,
                copy=copy,
                foto=None,
                cliente=cliente,
                referencia=referencia,
                modo="estatico_kav",
                etapa=avisar,
            )
            if isinstance(imagem, dict):
                if ref_logo:
                    imagem.setdefault("referencia_logo", ref_logo)
                if estilo_l:
                    imagem.setdefault("estilo_layout", estilo_l)
                if estilo_n:
                    imagem.setdefault("estilo_nome", estilo_n)
        except Exception as exc:
            avisos.append(f"Direção de Arte automática ignorada ({exc}).")
    else:
        avisos.append("Modo teste sem imagem ativado.")

    resultado = {
        "cliente": cliente["nome"],
        "tipo_producao": "post_estatico_kav",
        "pauta": pauta,
        "copy": copy,
        "brief": brief,
        "referencia": referencia["arquivo"].name if referencia else None,
        "referencia_logo": imagem.get("referencia_logo") if isinstance(imagem, dict) else None,
        "imagem": imagem,
        "avisos": avisos,
    }

    try:
        historico.registrar_post(
            slug,
            pauta,
            copy,
            referencia_nome=referencia["arquivo"].name if referencia else None,
            formato="estatico",
            estilo_layout=estilo.get("id"),
            estilo_nome=estilo.get("nome"),
            descricao_layout=estilo.get("descricao_layout"),
            cor_fundo=estilo.get("cor_fundo"),
            cor_destaque=estilo.get("cor_destaque"),
            cor_texto=estilo.get("cor_texto"),
            posicao_logo=estilo.get("posicao_logo"),
        )
    except Exception as exc:
        avisos.append(f"Não consegui salvar no histórico ({exc}).")

    try:
        from utils import estado_agentes
        estado_agentes.registrar_post_produzido(resultado, slug)
    except Exception:
        pass

    return resultado
