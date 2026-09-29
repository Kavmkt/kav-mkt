"""Orquestrador do motor de conteúdo da Kav (@kav.mkt).

Fluxos de produção suportados:
1. Produto (Ponto do Car): Escolha por histórico -> Legenda -> Brief -> Imagem -> Diretor de Arte (validação visual);
2. Fotos Reais (N&N Restaurante): Foto de prato real -> Estratégia de Performance -> Layout de Campanha -> Geração com Logo -> Diretor de Arte;
3. Post Estático Kav (@kav.mkt): Pauta Inédita Dinâmica -> Sorteio de Layout -> Copywriter de Autoridade -> Geração 4:5 -> Diretor de Arte;
4. Carrossel: Pauta -> Roteiro estruturado -> Geração de N páginas conectadas.
"""
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

from agents.agente_carrossel import gerar_roteiro_carrossel
from agents.agente_catalogo import escolher_produto
from agents.agente_design import gerar_brief, gerar_imagem
from agents.agente_design_fotos import escolher_foto, gerar_brief_foto, gerar_imagem_com_foto
from agents.agente_legenda import gerar_legenda
from agents.agente_legenda_fotos import gerar_legenda_fotos
from utils import historico
from utils.cliente import carregar_cliente


def gerar_post(slug: str, com_imagem: bool = True, etapa: Optional[Callable[[str], None]] = None) -> dict:
    """Gera um post completo com verificação automática do tipo de cliente."""
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
                modo="feed",
                callback_status=avisar,
            )
        except Exception as exc:
            avisos.append(f"Supervisão do Diretor de Arte ignorada ({exc}).")

    try:
        historico.registrar(slug, {
            "tipo": "post_feed",
            "produto_id": produto.get("id"),
            "produto_nome": produto.get("nome"),
            "headline": copy.get("headline_imagem"),
            "referencia": post["referencia"]["arquivo"].name if post["referencia"] else None,
        })
    except Exception as exc:
        avisos.append(f"Aviso: não foi possível salvar no histórico ({exc})")

    return post


def escolher_referencia(cliente: dict) -> Optional[dict]:
    """Seleciona uma referência de layout mantendo rotação contínua sem repetição."""
    return historico.escolher_referencia_sem_repetir(cliente)


def gerar_post_fotos(
    slug: str, com_imagem: bool = True, etapa: Optional[Callable[[str], None]] = None
) -> dict:
    """Gera post no formato fotos reais."""
    avisar = etapa or (lambda _texto: None)
    cliente = carregar_cliente(slug)
    avisos = []

    avisar("Escolhendo prato do dia do restaurante...")
    foto = escolher_foto(cliente)
    avisos.extend(foto.pop("avisos", []))

    avisar(f"Escrevendo chamada e legenda para: {foto.get('nome')}")
    copy = gerar_legenda_fotos(foto, cliente)

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
    avisar("Montando o brief visual...")
    post["brief"] = gerar_brief_foto(copy, foto, cliente, post["referencia"])
    avisar("Gerando a imagem com a foto real (pode levar até 1 minuto)...")
    post["imagem"] = gerar_imagem_com_foto(post["brief"], foto, cliente, post["referencia"])
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
                modo="feed",
                callback_status=avisar,
            )
        except Exception as exc:
            avisos.append(f"Supervisão do Diretor de Arte ignorada ({exc}).")

    try:
        historico.registrar(slug, {
            "tipo": "post_feed",
            "foto_id": foto.get("id"),
            "foto_nome": foto.get("nome"),
            "headline": copy.get("headline_imagem"),
            "referencia": post["referencia"]["arquivo"].name if post["referencia"] else None,
        })
    except Exception as exc:
        avisos.append(f"Aviso: não foi possível salvar no histórico ({exc})")

    return post


def gerar_carrossel(
    slug: str,
    num_paginas: int = 5,
    tema_personalizado: Optional[str] = None,
    com_imagem: bool = False,
    etapa: Optional[Callable[[str], None]] = None,
) -> dict:
    """Gera um roteiro completo de carrossel educativo/estratégico."""
    avisar = etapa or (lambda _texto: None)
    cliente = carregar_cliente(slug)

    avisar("Planejando pauta e tema do carrossel...")
    pauta = tema_personalizado or (
        cliente.get("pautas", {}).get("pautas", [{}])[0].get("tema")
        if cliente.get("pautas")
        else "Dicas de Especialista"
    )

    avisar(f"Criando roteiro com {num_paginas} páginas...")
    roteiro = gerar_roteiro_carrossel(pauta, cliente, num_paginas=num_paginas)

    return {
        "cliente": cliente["nome"],
        "tipo_producao": "carrossel",
        "tema": pauta,
        "num_paginas": len(roteiro.get("paginas", [])),
        "roteiro": roteiro,
        "avisos": ["Carrossel gerado com sucesso."],
    }


def gerar_campanha(
    slug: str, com_imagem: bool = True, etapa: Optional[Callable[[str], None]] = None
) -> dict:
    """Produz uma peça de anúncio de alta conversão (Meta Ads)."""
    avisar = etapa or (lambda _texto: None)
    cliente = carregar_cliente(slug)
    tipo = cliente.get("config", {}).get("tipo", "produto")

    if slug == "kav" or tipo == "estatico":
        return gerar_post_estatico_kav(slug, com_imagem=com_imagem, etapa=etapa)
    avisos = []

    avisar("1/4 [Curador]: Selecionando foto real de prato do cliente...")
    foto = escolher_foto(cliente)
    avisos.extend(foto.pop("avisos", []))

    from agents.agente_estrategia_campanha import criar_estrategia_campanha
    avisar(f"2/4 [Estrategista]: Analisando concorrência e desenhando estratégia para '{foto.get('nome')}'...")
    estrategia = criar_estrategia_campanha(cliente, foto_escolhida=foto)

    from agents.agente_layout_campanha import montar_brief_layout, gerar_arte_campanha
    h_destaque = estrategia.get("hierarquia_visual", {}).get("headline_destaque", "ALMOÇO DE QUALIDADE")
    avisar(f"3/4 [Diretor de Arte]: Projetando layout com hierarquia visual e headline '{h_destaque}'...")
    brief = montar_brief_layout(estrategia, foto, cliente)

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
                callback_status=avisar,
            )
        except Exception as exc:
            avisos.append(f"Supervisão do Diretor de Arte ignorada ({exc}).")
    else:
        avisos.append("Modo teste sem imagem ativado.")

    resultado = {
        "cliente": cliente["nome"],
        "tipo_producao": "campanha",
        "foto": foto,
        "estrategia": estrategia,
        "brief": brief,
        "imagem": imagem,
        "avisos": avisos,
    }

    try:
        historico.registrar(slug, {
            "tipo": "campanha",
            "foto_id": foto.get("id"),
            "foto_nome": foto.get("nome"),
            "headline": estrategia["hierarquia_visual"]["headline_destaque"],
            "angulo": estrategia.get("angulo_anuncio"),
        })
    except Exception as exc:
        avisos.append(f"Aviso: não foi possível salvar no histórico ({exc})")

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
                callback_status=avisar,
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
        )
    except Exception:
        pass

    return resultado
