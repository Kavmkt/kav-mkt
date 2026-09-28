"""Módulo de integração com a API Pública do OlaClick.

IMPORTANTE: Consulta ESTRITAMENTE a linha de cardápio (GET /v1/menu).
Não acessa pedidos, clientes, relatórios ou qualquer outro módulo.
"""
from __future__ import annotations

import os
from typing import Dict, List, Optional
import requests

OLACLICK_BASE_URL = "https://public-api.olaclick.app/v1"
TIMEOUT_SEGUNDOS = 15


def obter_api_key(cliente: Optional[dict] = None) -> Optional[str]:
    """Recupera a chave de API do OlaClick a partir do config do cliente ou variável de ambiente."""
    if cliente and cliente.get("config", {}).get("olaclick", {}).get("api_key"):
        return cliente["config"]["olaclick"]["api_key"]
    return (
        os.environ.get("OLACLICK_API_KEY__NN_RESTAURANTE")
        or os.environ.get("OLACLICK_API_KEY")
    )


def buscar_cardapio_olaclick(api_key: Optional[str] = None) -> List[Dict]:
    """Consulta EXCLUSIVAMENTE o endpoint GET /v1/menu da API Pública do OlaClick.
    
    Retorna apenas a lista de produtos/pratos do cardápio:
    [{'id': ..., 'nome': ..., 'descricao': ..., 'preco': ..., 'categoria': ..., 'disponivel': True}]
    """
    key = api_key or os.environ.get("OLACLICK_API_KEY")
    if not key:
        return []

    headers = {
        "Authorization": f"Bearer {key}",
        "Accept": "application/json",
        "User-Agent": "KavMarketing/1.0",
    }

    url = f"{OLACLICK_BASE_URL}/menu"
    resp = requests.get(url, headers=headers, timeout=TIMEOUT_SEGUNDOS)
    resp.raise_for_status()
    dados = resp.json()

    return _processar_menu(dados)


def _processar_menu(dados) -> List[Dict]:
    """Extrai estritamente os itens do cardápio do retorno da API."""
    produtos = []
    categorias = []
    if isinstance(dados, dict):
        categorias = dados.get("categories") or dados.get("data") or []
        if not categorias and "products" in dados:
            categorias = [{"name": "Cardápio", "products": dados["products"]}]
    elif isinstance(dados, list):
        categorias = dados

    for cat in categorias:
        if not isinstance(cat, dict):
            continue
        nome_categoria = cat.get("name") or cat.get("title") or "Cardápio"
        itens = cat.get("products") or cat.get("items") or []

        for p in itens:
            if not isinstance(p, dict):
                continue

            disponivel = p.get("available", p.get("is_available", True))
            if not disponivel:
                continue

            preco_val = p.get("price") or p.get("price_cents") or 0
            if isinstance(preco_val, (int, float)) and preco_val > 100:
                preco_fmt = f"R$ {preco_val / 100:.2f}".replace(".", ",")
            elif isinstance(preco_val, (int, float)) and preco_val > 0:
                preco_fmt = f"R$ {preco_val:.2f}".replace(".", ",")
            else:
                preco_fmt = str(preco_val) if preco_val else ""

            nome_prato = (p.get("name") or p.get("title") or "").strip()
            if not nome_prato:
                continue

            produtos.append({
                "id": str(p.get("id", "")),
                "nome": nome_prato,
                "descricao": (p.get("description") or "").strip(),
                "preco": preco_fmt,
                "categoria": nome_categoria,
                "disponivel": True,
                "foto_url": p.get("image_url") or p.get("image") or None,
            })

    return produtos


def selecionar_prato_do_dia(cliente: dict) -> Optional[Dict]:
    """Seleciona o prato do cardápio do dia do OlaClick evitando repetição recente."""
    api_key = obter_api_key(cliente)
    if not api_key:
        return None

    cardapio = buscar_cardapio_olaclick(api_key)
    if not cardapio:
        return None

    termos_prioritarios = ["prato do dia", "almoço", "executivo", "marmitex", "pratos", "refeição", "comida"]
    pratos_prioritarios = [
        p for p in cardapio
        if any(t in p["categoria"].lower() for t in termos_prioritarios)
    ]

    candidatos = pratos_prioritarios if pratos_prioritarios else cardapio

    try:
        from utils import historico
        from datetime import datetime
        ultimo_uso = historico.ultimo_uso_por_produto(cliente.get("slug", "nn-restaurante"))
        candidatos.sort(key=lambda p: ultimo_uso.get(f"olaclick_{p['id']}", datetime.min))
    except Exception:
        pass

    return candidatos[0] if candidatos else None
