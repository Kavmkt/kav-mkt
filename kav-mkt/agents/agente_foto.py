"""Agente de Repositório de Fotos & Cardápio do Dia (Benedito):
Seleciona o prato e a foto para clientes "de fotos" (NN Restaurante).

REGRA FUNDAMENTAL: USA SEMPRE FOTOS REAIS DO CLIENTE (NUNCA GERA COMIDA COM IA DO ZERO).
1. Consulta o cardápio do OlaClick via API (GET /v1/menu).
2. Percorre os itens do cardápio e busca no repositório de fotos (clientes/<slug>/fotos/)
   uma foto real que coincida com o prato.
   - Se o prato do OlaClick tiver foto real correspondente no acervo, é um candidato válido.
   - Se o prato do OlaClick NÃO tiver foto no acervo, descarta esse item e passa para o próximo.
3. Dentre os pratos do cardápio que possuem foto real, sorteia evitando repetições recentes (histórico).
4. Se nenhum item do cardápio tiver foto no acervo (ou se a API estiver indisponível),
   sorteia diretamente uma das fotos reais do acervo que não foi usada recentemente.
Assim, 100% dos posts utilizam fotos reais e autênticas da comida do cliente.
"""
from __future__ import annotations

import random
import unicodedata
from datetime import datetime, timedelta
from typing import List, Optional, Tuple

from utils import cardapio_olaclick, historico


def id_foto(foto: dict) -> str:
    return foto["arquivo"].name


def normalizar(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", texto).encode("ASCII", "ignore").decode("ASCII")
    return texto.lower().strip()


def foto_combina_com_prato(nome_prato: str, nome_foto: str) -> bool:
    """Verifica se uma foto real do acervo corresponde de verdade à receita do prato."""
    p_norm = normalizar(nome_prato)
    f_norm = normalizar(nome_foto)

    # 1. Correspondência exata
    if p_norm == f_norm or p_norm in f_norm or f_norm in p_norm:
        if "frango" in p_norm and ("molho" in p_norm or "ensopado" in p_norm or "cozido" in p_norm):
            if "parmegiana" in f_norm:
                return False
        return True

    # 2. Regras específicas para evitar falsos positivos
    if "feijoada" in p_norm:
        return "feijoada" in f_norm
    if "feijoada" in f_norm:
        return "feijoada" in p_norm

    if "parmegiana" in p_norm:
        return "parmegiana" in f_norm
    if "parmegiana" in f_norm:
        return "parmegiana" in p_norm

    if "frango" in p_norm and ("molho" in p_norm or "ensopado" in p_norm or "cozido" in p_norm):
        if "parmegiana" in f_norm or "grelhado" in f_norm:
            return False
        return "frango" in f_norm and ("molho" in f_norm or "ensopado" in f_norm or "cozido" in f_norm)

    if "bife" in p_norm or "acebolado" in p_norm:
        return "bife" in f_norm or "acebolado" in f_norm

    if "picadinho" in p_norm:
        return "picadinho" in f_norm

    termos_p = set(t for t in p_norm.split() if len(t) > 2 and t not in ["prato", "comida", "almoco", "molho", "especial"])
    termos_f = set(t for t in f_norm.split() if len(t) > 2 and t not in ["prato", "comida", "almoco", "molho", "especial"])
    intersecao = termos_p.intersection(termos_f)
    return len(intersecao) >= 1


def escolher_foto(cliente: dict) -> dict:
    """Sorteia e seleciona sempre uma FOTO REAL do cliente, conciliando com o OlaClick."""
    fotos = cliente.get("fotos") or []
    if not fotos:
        raise RuntimeError(
            "Nenhuma foto real encontrada em clientes/<cliente>/fotos/. "
            "Suba ao menos uma imagem real do cliente."
        )

    dias = cliente["config"].get("dias_sem_repetir_foto", 45)
    avisos = []

    try:
        ultimo_uso = historico.ultimo_uso_por_produto(cliente["slug"])
    except Exception as exc:
        ultimo_uso = {}
        avisos.append(f"Aviso ao ler histórico ({exc}); selecionando sem checar repetições.")

    limite = historico.agora() - timedelta(days=dias)

    # 1. Tenta conciliar com os pratos do OlaClick que possuem foto real no acervo
    candidatos_olaclick: List[Tuple[dict, dict]] = []
    try:
        api_key = cardapio_olaclick.obter_api_key(cliente)
        if api_key:
            cardapio = cardapio_olaclick.buscar_cardapio_olaclick(api_key)
            for prato in cardapio:
                nome_p = prato["nome"]
                # Procura se há foto real correspondente no acervo
                for f in fotos:
                    nome_f = f.get("nome") or f["arquivo"].stem
                    if foto_combina_com_prato(nome_p, nome_f):
                        candidatos_olaclick.append((prato, f))
                        break
    except Exception as exc:
        avisos.append(f"Aviso ao consultar OlaClick ({exc}); usando acervo direto.")

    if candidatos_olaclick:
        # Filtra os candidatos do OlaClick que não foram usados recentemente
        disponiveis = [
            (p, f) for (p, f) in candidatos_olaclick
            if ultimo_uso.get(id_foto(f), datetime.min) < limite
        ]
        if disponiveis:
            prato_escolhido, foto_escolhida = random.choice(disponiveis)
        else:
            prato_escolhido, foto_escolhida = min(
                candidatos_olaclick, key=lambda item: ultimo_uso.get(id_foto(item[1]), datetime.min)
            )

        res = dict(foto_escolhida)
        res["nome"] = prato_escolhido["nome"]
        res["descricao"] = prato_escolhido.get("descricao") or res.get("descricao", "")
        res["preco"] = prato_escolhido.get("preco") or res.get("preco", "")
        res["categoria"] = prato_escolhido.get("categoria") or res.get("categoria", "Almoço do Dia")
        res["origem"] = "olaclick_conciliado_com_foto_real"
        res["avisos"] = [
            f"Prato do dia no OlaClick '{prato_escolhido['nome']}' conciliado com a foto real '{foto_escolhida['arquivo'].name}'."
        ]
        return res

    # 2. Se nenhum prato do OlaClick de hoje tiver foto no acervo (ou sem OlaClick):
    # Sorteia diretamente uma das fotos reais do cliente evitando repetição recente
    disponiveis_fotos = [f for f in fotos if ultimo_uso.get(id_foto(f), datetime.min) < limite]
    if disponiveis_fotos:
        escolhida = random.choice(disponiveis_fotos)
    else:
        escolhida = min(fotos, key=lambda f: ultimo_uso.get(id_foto(f), datetime.min))
        avisos.append(
            f"Todas as {len(fotos)} fotos reais já foram usadas nos últimos {dias} dias — reaproveitando a menos recente."
        )

    res = dict(escolhida)
    res["origem"] = "acervo_foto_real"
    res["avisos"] = avisos
    return res
