"""Agente de Repositório de Fotos & Cardápio do Dia (Benedito):
Seleciona o prato e foto para clientes "de fotos" (hoje NN Restaurante).

Integração com a API Pública do OlaClick (GET /v1/menu):
1. Consulta EXCLUSIVAMENTE a linha de cardápio do OlaClick via chave de API.
2. Identifica os pratos disponíveis do dia (ex: Prato do Dia, Almoço, Marmitex).
3. Seleciona o prato do dia sem repetições recentes (via histórico).
4. Se o prato possuir foto estritamente correspondente no acervo local (clientes/nn-restaurante/fotos/),
   usa a foto real.
5. Se não houver foto condizente (ex: Frango ao Molho não deve usar foto de Parmegiana ou Feijoada),
   marca como prato virtual para que o Agente de Design gere a cena gastronômica específica daquele prato.
"""
from __future__ import annotations

import random
from datetime import datetime, timedelta
from typing import Optional

from utils import cardapio_olaclick, historico


def id_foto(foto: dict) -> str:
    if foto.get("foto_virtual"):
        return foto.get("id") or f"olaclick_{foto.get('nome')}"
    return foto["arquivo"].name


def escolher_foto(cliente: dict) -> dict:
    """Busca primeiro o prato do dia no OlaClick; se não disponível, recorre ao acervo."""
    avisos = []

    # 1. Tenta obter o cardápio do dia diretamente do OlaClick
    try:
        prato_olaclick = cardapio_olaclick.selecionar_prato_do_dia(cliente)
        if prato_olaclick:
            # Tenta encontrar foto real estritamente correspondente no acervo
            foto_correspondente = _buscar_foto_no_acervo(prato_olaclick["nome"], cliente)
            if foto_correspondente:
                foto_correspondente["origem"] = "olaclick_com_foto"
                foto_correspondente["prato_olaclick"] = prato_olaclick
                foto_correspondente["foto_virtual"] = False
                foto_correspondente["avisos"] = [
                    f"Prato do dia puxado do OlaClick: '{prato_olaclick['nome']}' (usando foto real correspondente do acervo)."
                ]
                return foto_correspondente
            else:
                # Prato sem foto correspondente -> Geração gastronômica autêntica daquele prato específico
                return {
                    "id": f"olaclick_{prato_olaclick.get('id') or prato_olaclick['nome'].lower().replace(' ', '_')}",
                    "nome": prato_olaclick["nome"],
                    "categoria": prato_olaclick.get("categoria") or "Almoço do Dia",
                    "descricao": prato_olaclick.get("descricao") or "",
                    "preco": prato_olaclick.get("preco") or "",
                    "foto_virtual": True,
                    "arquivo": None,
                    "origem": "olaclick_virtual",
                    "avisos": [
                        f"Prato do dia no OlaClick: '{prato_olaclick['nome']}' (sem foto correspondente no acervo — gerando fotografia gastronômica dedicada)."
                    ],
                }
    except Exception as exc:
        avisos.append(f"Aviso ao consultar OlaClick ({exc}); recorrendo ao acervo de fotos.")

    # 2. Fallback padrão: acervo local de fotos
    fotos = cliente.get("fotos") or []
    dias = cliente["config"].get("dias_sem_repetir_foto", 45)

    if not fotos:
        raise RuntimeError(
            "Nenhuma foto encontrada em clientes/<cliente>/fotos/ e OlaClick indisponível."
        )

    try:
        ultimo_uso = historico.ultimo_uso_por_produto(cliente["slug"])
    except Exception as exc:
        ultimo_uso = {}
        avisos.append(f"Não consegui ler o histórico ({exc}); escolhi sem checar repetições.")

    limite = historico.agora() - timedelta(days=dias)
    disponiveis = [f for f in fotos if ultimo_uso.get(id_foto(f), datetime.min) < limite]

    if disponiveis:
        escolhida = random.choice(disponiveis)
    else:
        escolhida = min(fotos, key=lambda f: ultimo_uso.get(id_foto(f), datetime.min))
        avisos.append(
            f"Todas as {len(fotos)} fotos já foram usadas nos últimos {dias} dias — "
            "reaproveitei a usada há mais tempo."
        )

    escolhida_dict = dict(escolhida)
    escolhida_dict["avisos"] = avisos
    escolhida_dict["foto_virtual"] = False
    return escolhida_dict


def _buscar_foto_no_acervo(nome_prato: str, cliente: dict) -> Optional[dict]:
    """Procura se há foto real no acervo que seja rigorosamente condizente com a receita.
    Evita casamentos errados (ex: 'Frango ao Molho' NÃO deve casar com 'Parmegiana' ou 'Feijoada')."""
    fotos = cliente.get("fotos") or []
    if not fotos:
        return None

    nome_lower = nome_prato.lower()

    # 1. Correspondência exata
    for f in fotos:
        nome_foto = (f.get("nome") or f["arquivo"].stem).lower()
        if nome_foto == nome_lower:
            return dict(f)

    # 2. Correspondência estrita por categoria de receita
    if "feijoada" in nome_lower:
        for f in fotos:
            nome_foto = (f.get("nome") or f["arquivo"].stem).lower()
            if "feijoada" in nome_foto:
                return dict(f)
    elif "parmegiana" in nome_lower:
        for f in fotos:
            nome_foto = (f.get("nome") or f["arquivo"].stem).lower()
            if "parmegiana" in nome_foto:
                return dict(f)
    elif "bife" in nome_lower and "acebolado" in nome_lower:
        for f in fotos:
            nome_foto = (f.get("nome") or f["arquivo"].stem).lower()
            if "bife" in nome_foto or "acebolado" in nome_foto:
                return dict(f)
    elif "frango" in nome_lower and ("molho" in nome_lower or "ensopado" in nome_lower or "cozido" in nome_lower):
        for f in fotos:
            nome_foto = (f.get("nome") or f["arquivo"].stem).lower()
            # Proíbe casar frango ao molho com parmegiana
            if "parmegiana" in nome_foto:
                continue
            if "frango" in nome_foto and ("molho" in nome_foto or "ensopado" in nome_foto or "cozido" in nome_foto):
                return dict(f)

    # Se não houver foto estritamente correspondente ao prato, retorna None para gerar do zero
    return None
