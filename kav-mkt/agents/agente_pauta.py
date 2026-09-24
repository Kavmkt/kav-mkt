"""Agente de Pauta: escolhe sozinho o tema do carrossel a partir de
clientes/<slug>/pautas.json, sem repetir temas usados nos últimos N dias
(config: dias_sem_repetir_pauta, padrão 30).

Equivalente ao Agente de Catálogo (agente_catalogo.py), mas para clientes de conteúdo
(carrossel, config.json com "tipo": "carrossel") — aqui não existe produto de loja, o
"produto" do post é o tema.
"""
import random
from datetime import datetime, timedelta

from utils import historico


def id_pauta(pauta: dict) -> str:
    return str(pauta.get("id") or pauta.get("tema"))


def escolher_pauta(cliente: dict) -> dict:
    pautas = cliente["pautas"].get("pautas") or []
    dias = cliente["config"].get("dias_sem_repetir_pauta", 30)
    avisos = []

    if not pautas:
        raise RuntimeError(
            "Nenhuma pauta cadastrada em clientes/<cliente>/pautas.json — adicione ao menos uma."
        )

    try:
        ultimo_uso = historico.ultimo_uso_por_produto(cliente["slug"])
    except Exception as exc:  # sem histórico, escolhe mesmo assim — com aviso
        ultimo_uso = {}
        avisos.append(f"Não consegui ler o histórico ({exc}); escolhi sem checar repetições.")
    limite = historico.agora() - timedelta(days=dias)
    disponiveis = [p for p in pautas if ultimo_uso.get(id_pauta(p), datetime.min) < limite]

    if disponiveis:
        escolhida = random.choice(disponiveis)
    else:
        escolhida = min(pautas, key=lambda p: ultimo_uso.get(id_pauta(p), datetime.min))
        avisos.append(
            f"Todas as {len(pautas)} pautas já foram usadas nos últimos {dias} dias — "
            "reaproveitei a usada há mais tempo. Cadastre mais pautas em pautas.json."
        )

    return {**escolhida, "id": id_pauta(escolhida), "avisos": avisos}
