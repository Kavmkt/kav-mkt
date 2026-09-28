import random
from typing import Optional

from agents import (
    agente_design_fotos,
    agente_diretor_arte,
    agente_estrategia_campanha,
    agente_estatico_kav,
    agente_layout_campanha,
    agente_legenda_fotos,
    agente_metricas,
    agente_pauta,
    agente_supervisor,
)
from utils import cliente as cliente_mod
from utils import estado_agentes, historico


def tipo_cliente(cliente: dict) -> str:
    """Retorna o tipo de fluxo do cliente: 'fotos', 'estatico', 'produto' ou 'carrossel'."""
    tipo = cliente.get("config", {}).get("tipo")
    if tipo:
        return tipo
    if cliente.get("fotos"):
        return "fotos"
    if cliente.get("referencias"):
        return "estatico"
    return "produto"


def sortear_foto(cliente: dict) -> dict:
    """Sorteia uma foto que ainda não foi usada recentemente."""
    fotos = cliente.get("fotos", [])
    if not fotos:
        raise ValueError(f"Nenhuma foto cadastrada para o cliente {cliente.get('nome')}.")
    return random.choice(fotos)


def sortear_pauta(slug: str) -> dict:
    """Sorteia ou gera dinamicamente uma pauta inédita para o cliente."""
    cliente = cliente_mod.carregar_cliente(slug)
    if slug == "kav":
        return agente_pauta.gerar_pauta_kav(cliente, forcar_ia=True)
    pautas = cliente.get("pautas", [])
    return historico.escolher_pauta_sem_repetir(cliente, pautas)


def gerar_post_fotos(slug: str, com_imagem: bool = True) -> dict:
    """Fluxo para clientes baseados em fotos reais (ex.: NN Restaurante)."""
    cliente = cliente_mod.carregar_cliente(slug)
    estado_agentes.limpar_logs()

    # 1. Curador (Benedito)
    estado_agentes.iniciar("curador")
    pauta = sortear_pauta(slug)
    foto = sortear_foto(cliente)
    prato_nome = foto.get("prato") or pauta.get("tema")
    estado_agentes.concluir(
        "curador",
        f"Foto selecionada: '{foto['arquivo'].name}'. Prato: '{prato_nome}'.",
    )

    # 2. Redatora (Clarice)
    estado_agentes.iniciar("copywriter")
    copy = agente_legenda_fotos.gerar_copy_completa(foto, cliente)
    estado_agentes.concluir(
        "copywriter",
        f"Headline: \"{copy.get('headline_imagem')}\". Subtítulo: \"{copy.get('subtitulo_imagem')}\".",
    )

    # 3. Designer (Joaquim)
    estado_agentes.iniciar("designer")
    referencia = historico.escolher_referencia_sem_repetir(cliente)
    brief = agente_design_fotos.gerar_brief_arte(copy, foto, cliente, referencia)
    estado_agentes.log("designer", f"Briefing criado. Estilo: {referencia.get('estilo', 'padrão') if referencia else 'padrão'}.")

    resultado_imagem = None
    if com_imagem:
        resultado_imagem = agente_design_fotos.gerar_imagem_com_foto(
            brief, foto, cliente, referencia
        )
        estado_agentes.concluir("designer", "Imagem 4:5 gerada pela IA.")
    else:
        estado_agentes.concluir("designer", "Etapa de imagem pulada (com_imagem=False).")

    # 4. Diretor de Arte (Otávio)
    estado_agentes.iniciar("diretor_arte")
    aprovacao = None
    if resultado_imagem:
        aprovacao = agente_diretor_arte.avaliar_arte(
            resultado_imagem["imagem_b64"], copy, cliente, brief
        )
        estado_agentes.concluir(
            "diretor_arte",
            f"Avaliação: nota {aprovacao.get('nota')}/10. Aprovado: {aprovacao.get('aprovado')}.",
        )
    else:
        estado_agentes.concluir("diretor_arte", "Avaliação pulada (sem imagem).")

    # 5. Salva no histórico para alimentar o anti-repetição
    ref_nome = referencia["arquivo"].name if referencia else None
    historico.registrar_post(slug, pauta, copy, ref_nome, formato="fotos")

    return {
        "cliente": slug,
        "pauta": pauta,
        "foto": foto,
        "copy": copy,
        "brief": brief,
        "imagem": resultado_imagem,
        "aprovacao": aprovacao,
        "referencia": ref_nome,
        "logs": estado_agentes.obter_logs(),
    }


def gerar_post_estatico_kav(slug: str = "kav", com_imagem: bool = True) -> dict:
    """Fluxo para post estático exclusivo da Kav (@kav.mkt)."""
    cliente = cliente_mod.carregar_cliente(slug)
    estado_agentes.limpar_logs()

    # 1. Estrategista de Pauta Dinâmica (Benedito)
    estado_agentes.iniciar("curador")
    pauta = sortear_pauta(slug)
    estado_agentes.concluir(
        "curador",
        f"Pauta selecionada: '{pauta.get('tema')}' [{pauta.get('pilar', 'Geral')}].",
    )

    # 2. Redatora / Copywriter (Clarice)
    estado_agentes.iniciar("copywriter")
    copy = agente_estatico_kav.gerar_copy_kav(pauta, cliente)
    estado_agentes.concluir(
        "copywriter",
        f"Headline: \"{copy.get('headline_imagem')}\". Selo: \"{copy.get('selo_produto')}\".",
    )

    # 3. Designer / Arte (Joaquim)
    estado_agentes.iniciar("designer")
    referencia = historico.escolher_referencia_sem_repetir(cliente)
    brief = agente_estatico_kav.gerar_brief_arte_kav(copy, pauta, cliente, referencia)
    ref_nome = referencia["arquivo"].name if referencia else "Sem layout de referência"
    estado_agentes.log("designer", f"Layout sorteado sem repetição: {ref_nome}.")

    resultado_imagem = None
    if com_imagem:
        resultado_imagem = agente_estatico_kav.gerar_imagem_estatica_kav(brief, cliente, referencia)
        estado_agentes.concluir("designer", "Arte estática 4:5 gerada pela IA.")
    else:
        estado_agentes.concluir("designer", "Etapa de imagem pulada (com_imagem=False).")

    # 4. Diretor de Arte (Otávio)
    estado_agentes.iniciar("diretor_arte")
    aprovacao = None
    if resultado_imagem:
        aprovacao = agente_diretor_arte.avaliar_arte(
            resultado_imagem["imagem_b64"], copy, cliente, brief
        )
        estado_agentes.concluir(
            "diretor_arte",
            f"Avaliação: nota {aprovacao.get('nota')}/10. Aprovado: {aprovacao.get('aprovado')}.",
        )
    else:
        estado_agentes.concluir("diretor_arte", "Avaliação pulada (sem imagem).")

    # 5. Salva no histórico para alimentar o anti-repetição
    historico.registrar_post(slug, pauta, copy, ref_nome, formato="estatico")

    return {
        "cliente": slug,
        "pauta": pauta,
        "copy": copy,
        "brief": brief,
        "imagem": resultado_imagem,
        "aprovacao": aprovacao,
        "referencia": ref_nome,
        "logs": estado_agentes.obter_logs(),
    }


def gerar_post_campanha(slug: str, com_imagem: bool = True) -> dict:
    """Fluxo para campanhas de produto e tráfego pago (ex.: Ponto Car)."""
    cliente = cliente_mod.carregar_cliente(slug)
    estado_agentes.limpar_logs()

    estado_agentes.iniciar("estrategista")
    pauta = sortear_pauta(slug)
    estrategia = agente_estrategia_campanha.planejar_campanha(pauta, cliente)
    estado_agentes.concluir("estrategista", f"Estratégia: {estrategia.get('angulo')}")

    estado_agentes.iniciar("copywriter")
    copy = agente_estrategia_campanha.gerar_copy_anuncio(estrategia, cliente)
    estado_agentes.concluir("copywriter", f"Headline: {copy.get('headline')}")

    estado_agentes.iniciar("designer")
    referencia = historico.escolher_referencia_sem_repetir(cliente)
    layout = agente_layout_campanha.montar_briefing_anuncio(copy, cliente, referencia)
    estado_agentes.concluir("designer", "Briefing de layout montado")

    ref_nome = referencia["arquivo"].name if referencia else None
    historico.registrar_post(slug, pauta, copy, ref_nome, formato="campanha")

    return {
        "cliente": slug,
        "estrategia": estrategia,
        "copy": copy,
        "layout": layout,
        "referencia": ref_nome,
        "logs": estado_agentes.obter_logs(),
    }


def executar_pipeline(slug: str, modo: str = "organico", com_imagem: bool = True) -> dict:
    """Roteador mestre: escolhe o fluxo correto de acordo com a configuração do cliente."""
    cliente = cliente_mod.carregar_cliente(slug)
    tipo = tipo_cliente(cliente)

    if slug == "kav" or tipo == "estatico":
        return gerar_post_estatico_kav(slug, com_imagem=com_imagem)
    elif tipo == "fotos":
        return gerar_post_fotos(slug, com_imagem=com_imagem)
    else:
        return gerar_post_campanha(slug, com_imagem=com_imagem)
