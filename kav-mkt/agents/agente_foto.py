"""Agente de Repositório de Fotos & Cardápio do Dia (Benedito):
Seleciona o prato e foto para clientes "de fotos" (hoje NN Restaurante).

Integração com a API Pública do OlaClick (GET /v1/menu):
1. Consulta EXCLUSIVAMENTE a linha de cardápio do OlaClick via chave de API.
2. Identifica os pratos disponíveis do dia (ex: Prato do Dia, Executivo, Almoço).
3. Seleciona o prato do dia sem repetições recentes (via histórico).
4. Se o prato possuir foto correspondente no acervo local (clientes/nn-restaurante/fotos/),
   usa a foto real para máxima autenticidade.
5. Se não houver foto no acervo, cria a definição detalhada para que o Agente de Design
   gere a cena gastronômica realista com as diretrizes físicas do restaurante.
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
            # Tenta encontrar foto real correspondente no acervo
            foto_correspondente = _buscar_foto_no_acervo(prato_olaclick["nome"], cliente)
            if foto_correspondente:
                foto_correspondente["origem"] = "olaclick_com_foto"
                foto_correspondente["prato_olaclick"] = prato_olaclick
                foto_correspondente["avisos"] = [
                    f"Prato do dia puxado do OlaClick: '{prato_olaclick['nome']}' (usando foto real do acervo)."
                ]
                return foto_correspondente
            else:
                # Prato sem foto no acervo -> Geração gastronômica guiada do zero
                return {
                    "id": f"olaclick_{prato_olaclick.get('id') or prato_olaclick['nome'].lower().replace(' ', '_')}",
                    "nome": prato_olaclick["nome"],
                    "categoria": prato_olaclick.get("categoria") or "Prato do Dia",
                    "descricao": prato_olaclick.get("descricao") or "",
                    "preco": prato_olaclick.get("preco") or "",
                    "foto_virtual": True,
                    "arquivo": None,
                    "origem": "olaclick_virtual",
                    "avisos": [
                        f"Prato do dia puxado do OlaClick: '{prato_olaclick['nome']}' (sem foto prévia no acervo — gerando cena culinária brasileira autêntica)."
                    ],
                }
    except Exception as exc:
        avisos.append(f"Aviso ao consultar OlaClick ({exc}); recorrendo ao acervo de fotos.")

    # 2. Fallback padrão: sorteia do acervo local de fotos
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
    """Procura se há alguma foto no acervo com nome/palavra-chave correspondente ao prato."""
    fotos = cliente.get("fotos") or []
    if not fotos:
        return None

    nome_lower = nome_prato.lower()
    termos = [t for t in nome_lower.split() if len(t) > 3]

    for f in fotos:
        nome_foto = (f.get("nome") or f["arquivo"].stem).lower()
        if any(t in nome_foto for t in termos):
            return dict(f)

    return None
