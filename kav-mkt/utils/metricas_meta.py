"""Coletor de metricas do Meta (Instagram Organico + Meta Ads) via Graph API / Marketing API.

Apenas leitura: nao cria, nao pausa e nao altera nenhuma campanha ou anuncio.

Padrao de autenticacao:
Token por cliente em variavel de ambiente:
META_ACCESS_TOKEN__<SLUG_EM_MAIUSCULO_COM_UNDERSCORE>
Exemplo: META_ACCESS_TOKEN__NN_RESTAURANTE
Os IDs da conta de anuncio e da conta do Instagram ficam em clientes/<slug>/config.json.
"""
import os
from datetime import datetime, timedelta
from typing import Dict, Optional
from zoneinfo import ZoneInfo

import requests

GRAPH_API_VERSION = "v20.0"
GRAPH_API_BASE = f"https://graph.facebook.com/{GRAPH_API_VERSION}"
FUSO = ZoneInfo("America/Sao_Paulo")


def obter_token_cliente(slug: str) -> Optional[str]:
    """Recupera o token de acesso do Meta para o cliente específico a partir do .env."""
    slug_formatado = slug.upper().replace("-", "_")
    return os.environ.get(f"META_ACCESS_TOKEN__{slug_formatado}")


def insights_organicos(instagram_account_id: str, token: str, dias: int = 30) -> dict:
    """Coleta métricas da conta do Instagram: seguidores, postagens recentes e alcance."""
    if not token or not instagram_account_id:
        return {
            "disponivel": False,
            "motivo": "Token ou Instagram Account ID ausente.",
        }

    resultado = {"disponivel": True, "plataforma": "instagram_organico"}

    # 1. Informações básicas da conta
    try:
        url_conta = f"{GRAPH_API_BASE}/{instagram_account_id}"
        resp_conta = requests.get(
            url_conta,
            params={
                "fields": "username,name,followers_count,media_count",
                "access_token": token,
            },
            timeout=15,
        )
        resp_conta.raise_for_status()
        dados_conta = resp_conta.json()
        resultado["perfil"] = {
            "username": dados_conta.get("username"),
            "nome": dados_conta.get("name"),
            "seguidores": dados_conta.get("followers_count", 0),
            "total_posts": dados_conta.get("media_count", 0),
        }
    except Exception as exc:
        resultado["perfil"] = {"erro": f"Não foi possível ler perfil: {exc}"}

    # 2. Últimos posts publicados para verificar cadência
    try:
        url_midia = f"{GRAPH_API_BASE}/{instagram_account_id}/media"
        resp_midia = requests.get(
            url_midia,
            params={
                "fields": "id,caption,media_type,timestamp,like_count,comments_count,permalink",
                "limit": 10,
                "access_token": token,
            },
            timeout=15,
        )
        resp_midia.raise_for_status()
        posts_data = resp_midia.json().get("data", [])

        limite_data = datetime.now(FUSO) - timedelta(days=dias)
        posts_periodo = []
        for p in posts_data:
            ts_str = p.get("timestamp")
            if ts_str:
                dt_post = datetime.fromisoformat(ts_str.replace("Z", "+00:00")).astimezone(FUSO)
                if dt_post >= limite_data:
                    posts_periodo.append({
                        "id": p.get("id"),
                        "data": dt_post.isoformat(),
                        "tipo": p.get("media_type"),
                        "curtidas": p.get("like_count", 0),
                        "comentarios": p.get("comments_count", 0),
                    })

        post_mais_recente = posts_data[0].get("timestamp") if posts_data else None
        resultado["atividade_recente"] = {
            "posts_no_periodo": len(posts_periodo),
            "data_post_mais_recente": post_mais_recente,
            "ultimos_posts": posts_periodo,
        }
    except Exception as exc:
        resultado["atividade_recente"] = {"erro": f"Não foi possível ler publicações: {exc}"}

    return resultado


def insights_pagos(ad_account_id: str, token: str, dias: int = 30) -> dict:
    """Coleta métricas da conta de anúncios (Meta Ads): investimento, cliques, conversas."""
    if not token or not ad_account_id:
        return {
            "disponivel": False,
            "motivo": "Token ou Ad Account ID ausente.",
        }

    conta_id = ad_account_id if ad_account_id.startswith("act_") else f"act_{ad_account_id}"

    hoje = datetime.now(FUSO).date()
    data_inicio = hoje - timedelta(days=dias)
    data_fim = hoje - timedelta(days=1)

    url_insights = f"{GRAPH_API_BASE}/{conta_id}/insights"
    params = {
        "access_token": token,
        "level": "campaign",
        "time_range": f"{{'since':'{data_inicio.isoformat()}','until':'{data_fim.isoformat()}'}}",
        "fields": "campaign_id,campaign_name,spend,impressions,clicks,ctr,cpm,actions",
    }

    try:
        resp = requests.get(url_insights, params=params, timeout=20)
        resp.raise_for_status()
        dados_campanhas = resp.json().get("data", [])
    except Exception as exc:
        return {
            "disponivel": False,
            "motivo": f"Erro na requisição ao Meta Marketing API: {exc}",
        }

    total_gasto = 0.0
    total_impressoes = 0
    total_cliques = 0
    total_conversas = 0
    campanhas = []

    for c in dados_campanhas:
        gasto = float(c.get("spend", 0.0))
        impressoes = int(c.get("impressions", 0))
        cliques = int(c.get("clicks", 0))
        ctr = float(c.get("ctr", 0.0))
        cpm = float(c.get("cpm", 0.0))

        conversas_campanha = 0
        for action in c.get("actions", []):
            tipo = action.get("action_type", "")
            if any(k in tipo for k in ["messaging_conversation_started", "messaging_first_reply", "onsite_conversion.messaging"]):
                conversas_campanha += int(action.get("value", 0))

        total_gasto += gasto
        total_impressoes += impressoes
        total_cliques += cliques
        total_conversas += conversas_campanha

        campanhas.append({
            "id": c.get("campaign_id"),
            "nome": c.get("campaign_name"),
            "gasto_reais": round(gasto, 2),
            "impressoes": impressoes,
            "cliques": cliques,
            "ctr_percentual": round(ctr, 2),
            "cpm_reais": round(cpm, 2),
            "conversas_iniciadas": conversas_campanha,
        })

    ctr_geral = round((total_cliques / total_impressoes * 100), 2) if total_impressoes > 0 else 0.0
    cpc_geral = round((total_gasto / total_cliques), 2) if total_cliques > 0 else 0.0

    return {
        "disponivel": True,
        "plataforma": "meta_ads",
        "periodo_dias": dias,
        "data_inicio": data_inicio.isoformat(),
        "data_fim": data_fim.isoformat(),
        "resumo": {
            "gasto_total_reais": round(total_gasto, 2),
            "impressoes": total_impressoes,
            "cliques": total_cliques,
            "conversas_iniciadas": total_conversas,
            "ctr_percentual": ctr_geral,
            "cpc_medio_reais": cpc_geral,
        },
        "campanhas": campanhas,
    }
