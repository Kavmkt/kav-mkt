"""Agente de Catálogo: escolhe sozinho o produto do post a partir do catálogo da loja do
cliente (clientes/<slug>/catalogo.json), priorizando os mais vendidos e sem repetir
produtos usados nos últimos N dias (padrão 30, em config.json).

O catálogo é preenchido por sincronização via Claude in Chrome (ver clientes/README.md).
Planos B, sem nunca travar o fluxo:
- todos os produtos já usados no período → reaproveita o usado há mais tempo, com aviso;
- catálogo vazio → usa um produto coringa da skill (sem foto real), com aviso.
"""
import random
from datetime import datetime, timedelta

from utils import historico

# Sorteio entre os N mais vendidos ainda disponíveis, com peso maior para quem vende mais:
# prioriza os campeões de venda sem virar sempre o mesmo produto.
TOP_VENDIDOS = 15
CATALOGO_VELHO_DIAS = 30


def id_produto(produto: dict) -> str:
    return str(produto.get("id") or produto.get("url") or produto.get("nome"))


def escolher_produto(cliente: dict) -> dict:
    catalogo = cliente["catalogo"]
    produtos = catalogo.get("produtos") or []
    dias = cliente["config"].get("dias_sem_repetir_produto", 30)
    avisos = []

    if produtos:
        aviso_idade = _aviso_catalogo_velho(catalogo.get("atualizado_em"))
        if aviso_idade:
            avisos.append(aviso_idade)
        candidatos = produtos
    else:
        avisos.append(
            "O catálogo deste cliente está vazio — usei um produto coringa (sem foto real). "
            "Peça ao Claude para sincronizar o catálogo (ver clientes/README.md)."
        )
        candidatos = [
            {"id": f"coringa:{nome}", "nome": nome, "fallback_usado": True}
            for nome in cliente["produtos_coringa"]
        ]
        if not candidatos:
            raise RuntimeError("Catálogo vazio e nenhum produto coringa na skill do cliente.")

    try:
        ultimo_uso = historico.ultimo_uso_por_produto(cliente["slug"])
    except Exception as exc:  # sem histórico, escolhe mesmo assim — com aviso
        ultimo_uso = {}
        avisos.append(f"Não consegui ler o histórico ({exc}); escolhi sem checar repetições.")
    limite = historico.agora() - timedelta(days=dias)
    disponiveis = [p for p in candidatos if ultimo_uso.get(id_produto(p), datetime.min) < limite]

    if disponiveis:
        mais_vendidos = sorted(disponiveis, key=lambda p: p.get("vendidos") or 0, reverse=True)[:TOP_VENDIDOS]
        pesos = [len(mais_vendidos) - i for i in range(len(mais_vendidos))]
        escolhido = random.choices(mais_vendidos, weights=pesos, k=1)[0]
    else:
        escolhido = min(candidatos, key=lambda p: ultimo_uso.get(id_produto(p), datetime.min))
        avisos.append(
            f"Todos os {len(candidatos)} produtos já foram usados nos últimos {dias} dias — "
            "reaproveitei o usado há mais tempo. Sincronize o catálogo com mais produtos."
        )

    return {**escolhido, "id": id_produto(escolhido), "avisos": avisos}


def _aviso_catalogo_velho(atualizado_em) -> str:
    try:
        data = datetime.fromisoformat(str(atualizado_em))
    except ValueError:
        return "O catálogo não tem data de atualização — confira se está em dia."
    idade = (historico.agora() - data).days
    if idade > CATALOGO_VELHO_DIAS:
        return f"O catálogo foi atualizado há {idade} dias — vale sincronizar de novo (preços e mais vendidos mudam)."
    return ""
