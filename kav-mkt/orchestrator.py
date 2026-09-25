"""Orquestrador da Kav (@kav.mkt): cria um post completo para um cliente, sem intervenção.

Catálogo (escolhe o produto) → Legenda (chamada, selo e legenda no padrão do cliente) →
Design (brief + imagem com referência de layout, foto real do produto e logo).

Nenhuma postagem é feita em redes sociais — o resultado é para revisão e publicação
manual. Usado pelo app (app.py) e também pela linha de comando:

    python orchestrator.py --cliente ponto-car
"""
import argparse
import base64
import json
from typing import Callable, Optional

from agents.agente_carrossel import gerar_imagens_carrossel, gerar_roteiro
from agents.agente_catalogo import escolher_produto
from agents.agente_design import escolher_referencia, gerar_brief, gerar_imagem
from agents.agente_design_fotos import gerar_brief_foto, gerar_imagem_foto
from agents.agente_foto import escolher_foto
from agents.agente_legenda import gerar_legenda
from agents.agente_legenda_fotos import gerar_legenda_foto
from agents.agente_pauta import escolher_pauta
from utils import historico
from utils.cliente import CLIENTES_DIR, carregar_cliente


def gerar_post(slug: str, com_imagem: bool = True, etapa: Optional[Callable[[str], None]] = None) -> dict:
    """Cria o post. `etapa` recebe o nome de cada passo (o app usa para mostrar progresso).

    Só posts completos (com imagem) entram no histórico — assim, testes de texto não
    "gastam" produtos da janela de 30 dias.
    """
    avisar = etapa or (lambda _texto: None)
    cliente = carregar_cliente(slug)

    avisar("Escolhendo o produto no catálogo...")
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

    # Sorteada antes do brief: a posição do logo depende do layout escolhido.
    post["referencia"] = escolher_referencia(cliente)
    avisar("Montando o brief visual...")
    post["brief"] = gerar_brief(copy, produto, cliente, post["referencia"])
    avisar("Gerando a imagem (pode levar até 1 minuto)...")
    post["imagem"] = gerar_imagem(post["brief"], produto, cliente, post["referencia"])
    if post["imagem"].get("aviso"):
        avisos.append(post["imagem"]["aviso"])

    try:
        historico.registrar(slug, {
            "produto_id": produto["id"],
            "produto_nome": produto.get("nome"),
            "headline": copy.get("headline_imagem"),
            "legenda": copy.get("legenda"),
            "referencia_layout": post["imagem"].get("referencia_layout"),
        })
    except Exception as exc:  # o post já está pronto — só avisa
        avisos.append(f"Não consegui salvar no histórico ({exc}); este produto pode se repetir nos próximos posts.")
    return post


def gerar_carrossel(
    slug: str, num_paginas: int = 5, com_imagem: bool = True, etapa: Optional[Callable[[str], None]] = None
) -> dict:
    """Cria um carrossel (1 a 7 páginas) para um cliente de conteúdo (config.json com
    "tipo": "carrossel") — mesmo espírito do `gerar_post`, mas com Pauta no lugar de
    Catálogo e N imagens (uma por página) no lugar de uma só. Não é chamada pelo fluxo
    de clientes de produto (ex: ponto-car), que continua em `gerar_post`.
    """
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
    post["slides"] = gerar_imagens_carrossel(
        roteiro, cliente, pauta.get("tema", ""), post["referencia"], cta=pauta.get("cta"), etapa=avisar
    )

    try:
        historico.registrar(slug, {
            "produto_id": pauta["id"],
            "produto_nome": pauta.get("tema"),
            "headline": roteiro["paginas"][0].get("titulo") if roteiro.get("paginas") else None,
            "legenda": roteiro.get("legenda"),
        })
    except Exception as exc:  # o carrossel já está pronto — só avisa
        avisos.append(f"Não consegui salvar no histórico ({exc}); esta pauta pode se repetir nos próximos carrosséis.")
    return post


def gerar_post_fotos(slug: str, com_imagem: bool = True, etapa: Optional[Callable[[str], None]] = None) -> dict:
    """Cria o post para um cliente "de fotos" (config.json com "tipo": "fotos") — mesmo
    espírito do `gerar_post`, mas com o Agente de Repositório de Fotos no lugar do
    Agente de Catálogo: em vez de um produto de loja, sorteia uma foto real do cliente
    (clientes/<slug>/fotos/) e monta a peça em cima dela, sem gerar uma cena do zero.
    Isolado de `gerar_post`: nenhum cliente de catálogo passa por aqui, e vice-versa.
    """
    avisar = etapa or (lambda _texto: None)
    cliente = carregar_cliente(slug)

    avisar("Escolhendo uma foto do repositório...")
    foto = escolher_foto(cliente)
    avisos = list(foto.pop("avisos", []))

    avisar(f"Escrevendo chamada e legenda para: {foto.get('nome') or foto['arquivo'].name}")
    copy = gerar_legenda_foto(foto, cliente)
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

    # Sorteada antes do brief: a posição do logo depende do layout escolhido.
    post["referencia"] = escolher_referencia(cliente)
    avisar("Montando o brief visual...")
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
    except Exception as exc:  # o post já está pronto — só avisa
        avisos.append(f"Não consegui salvar no histórico ({exc}); esta foto pode se repetir nos próximos posts.")
    return post


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()
    parser = argparse.ArgumentParser(description="Cria um post completo para um cliente da Kav.")
    parser.add_argument("--cliente", required=True, help="Pasta do cliente em clientes/ (ex: ponto-car)")
    parser.add_argument("--sem-imagem", action="store_true", help="Só gera o texto (não entra no histórico).")
    args = parser.parse_args()

    resultado = gerar_post(args.cliente, com_imagem=not args.sem_imagem, etapa=print)
    pasta = CLIENTES_DIR.parent / "output" / args.cliente / historico.agora().strftime("%Y-%m-%d_%H%M%S")
    pasta.mkdir(parents=True, exist_ok=True)
    (pasta / "legenda.txt").write_text(resultado["copy"].get("legenda") or "", encoding="utf-8")
    (pasta / "post.json").write_text(
        json.dumps({k: v for k, v in resultado.items() if k != "imagem"}, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    if resultado["imagem"]:
        (pasta / "imagem.png").write_bytes(base64.b64decode(resultado["imagem"]["imagem_b64"]))
    for aviso in resultado["avisos"]:
        print(f"⚠️  {aviso}")
    print(f"\nPronto: {pasta}")
