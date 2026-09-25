"""Agente de Repositório de Fotos: escolhe sozinho uma foto real do repositório do
cliente (clientes/<slug>/fotos/), sem repetir fotos usadas nos últimos N dias (config:
dias_sem_repetir_foto, padrão 45).

Equivalente ao Agente de Catálogo (agente_catalogo.py) e ao Agente de Pauta
(agente_pauta.py), mas para clientes "de fotos" (config.json com "tipo": "fotos") — hoje
só o NN Restaurante. Isolado dos outros dois: nenhum cliente que usa catálogo ou pauta
passa por este arquivo, e vice-versa.
"""
import random
from datetime import datetime, timedelta

from utils import historico


def id_foto(foto: dict) -> str:
    return foto["arquivo"].name


def escolher_foto(cliente: dict) -> dict:
    fotos = cliente.get("fotos") or []
    dias = cliente["config"].get("dias_sem_repetir_foto", 45)
    avisos = []

    if not fotos:
        raise RuntimeError(
            "Nenhuma foto encontrada em clientes/<cliente>/fotos/ — suba ao menos uma "
            "imagem (ver clientes/<cliente>/fotos/README.md)."
        )

    try:
        ultimo_uso = historico.ultimo_uso_por_produto(cliente["slug"])
    except Exception as exc:  # sem histórico, escolhe mesmo assim — com aviso
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
            "reaproveitei a usada há mais tempo. Suba mais fotos em fotos/."
        )

    return {**escolhida, "id": id_foto(escolhida), "avisos": avisos}
