"""Módulo de leitura de métricas do Google Ads via API REST e GAQL puro (usando `requests`).

Implementação leve e desacoplada, sem a dependência pesada da biblioteca oficial `google-ads`.
Espelha a simplicidade e a padronização de `utils/metricas_meta.py`.

Credenciais lidas de variáveis de ambiente (.env):
- GOOGLE_ADS_DEVELOPER_TOKEN: Token de desenvolvedor obtido na MCC Kav.
- GOOGLE_ADS_CLIENT_ID: Client ID do OAuth gerado no Google Cloud Console.
- GOOGLE_ADS_CLIENT_SECRET: Client Secret do OAuth gerado no Google Cloud Console.
- GOOGLE_ADS_REFRESH_TOKEN: Token de atualização gerado via OAuth Playground.
- GOOGLE_ADS_LOGIN_CUSTOMER_ID: ID da MCC Kav (790-737-7766, sem hífen).
"""
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from zoneinfo import ZoneInfo

import requests

GOOGLE_OAUTH_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_ADS_API_VERSION = "v17"
FUSO = ZoneInfo("America/Sao_Paulo")


def credenciais_configuradas() -> bool:
    """Verifica se todas as variáveis obrigatórias para o Google Ads estão presentes."""
    chaves = [
        "GOOGLE_ADS_DEVELOPER_TOKEN",
        "GOOGLE_ADS_CLIENT_ID",
        "GOOGLE_ADS_CLIENT_SECRET",
        "GOOGLE_ADS_REFRESH_TOKEN",
    ]
    return all(bool(os.environ.get(k)) for k in chaves)


def obter_access_token() -> str:
    """Gera um access token temporário usando o refresh token configurado."""
    client_id = os.environ.get("GOOGLE_ADS_CLIENT_ID")
    client_secret = os.environ.get("GOOGLE_ADS_CLIENT_SECRET")
    refresh_token = os.environ.get("GOOGLE_ADS_REFRESH_TOKEN")

    if not (client_id and client_secret and refresh_token):
        raise ValueError("Credenciais de OAuth do Google Ads incompletas no ambiente.")

    dados = {
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
    }
    resp = requests.post(GOOGLE_OAUTH_TOKEN_URL, data=dados, timeout=15)
    resp.raise_for_status()
    return resp.json()["access_token"]


def _headers_requisicao(access_token: str) -> dict:
    dev_token = os.environ.get("GOOGLE_ADS_DEVELOPER_TOKEN", "")
    login_mcc = os.environ.get("GOOGLE_ADS_LOGIN_CUSTOMER_ID", "7907377766").replace("-", "")

    headers = {
        "Authorization": f"Bearer {access_token}",
        "developer-token": dev_token,
        "Content-Type": "application/json",
    }
    if login_mcc:
        headers["login-customer-id"] = login_mcc
    return headers


def buscar_metricas_campanhas(customer_id: str, dias: int = 30) -> dict:
    """Coleta métricas agregadas e por campanha do Google Ads para uma conta de cliente.
    
    Args:
        customer_id: ID do cliente no Google Ads (10 dígitos, com ou sem hífen).
        dias: Quantidade de dias retroativos (padrão 30).
        
    Returns:
        Dicionário estruturado com resumo e detalhes por campanha.
    """
    if not credenciais_configuradas():
        return {
            "disponivel": False,
            "motivo": "Credenciais do Google Ads não configuradas no ambiente (.env).",
        }

    clean_id = customer_id.replace("-", "").strip()
    if not clean_id:
        return {
            "disponivel": False,
            "motivo": "Customer ID do cliente não informado.",
        }

    try:
        access_token = obter_access_token()
    except Exception as exc:
        return {
            "disponivel": False,
            "motivo": f"Falha na renovação do token OAuth: {exc}",
        }

    # Define o intervalo de datas no formato YYYY-MM-DD
    hoje = datetime.now(FUSO).date()
    data_inicio = hoje - timedelta(days=dias)
    data_fim = hoje - timedelta(days=1)

    gaql = f"""
    SELECT
      campaign.id,
      campaign.name,
      campaign.status,
      metrics.impressions,
      metrics.clicks,
      metrics.cost_micros,
      metrics.conversions,
      metrics.ctr,
      metrics.average_cpc
    FROM campaign
    WHERE segments.date BETWEEN '{data_inicio.isoformat()}' AND '{data_fim.isoformat()}'
    ORDER BY metrics.cost_micros DESC
    """

    url = f"https://googleads.googleapis.com/{GOOGLE_ADS_API_VERSION}/customers/{clean_id}/googleAds:searchStream"
    headers = _headers_requisicao(access_token)

    try:
        resp = requests.post(url, json={"query": gaql}, headers=headers, timeout=30)
        resp.raise_for_status()
        lotes = resp.json()
    except Exception as exc:
        return {
            "disponivel": False,
            "motivo": f"Erro na requisição GAQL ao Google Ads: {exc}",
        }

    campanhas = []
    total_impressoes = 0
    total_cliques = 0
    total_custo_reais = 0.0
    total_conversoes = 0.0

    for lote in lotes:
        for linha in lote.get("results", []):
            camp = linha.get("campaign", {})
            met = linha.get("metrics", {})

            custo_reais = round(float(met.get("costMicros", 0)) / 1_000_000.0, 2)
            impressoes = int(met.get("impressions", 0))
            cliques = int(met.get("clicks", 0))
            conversoes = float(met.get("conversions", 0.0))
            ctr = round(float(met.get("ctr", 0.0)) * 100, 2)
            cpc_medio = round(float(met.get("averageCpc", 0)) / 1_000_000.0, 2)

            total_impressoes += impressoes
            total_cliques += cliques
            total_custo_reais += custo_reais
            total_conversoes += conversoes

            campanhas.append({
                "id": camp.get("id"),
                "nome": camp.get("name"),
                "status": camp.get("status"),
                "impressoes": impressoes,
                "cliques": cliques,
                "custo_reais": custo_reais,
                "conversoes": conversoes,
                "ctr_percentual": ctr,
                "cpc_medio_reais": cpc_medio,
            })

    ctr_geral = round((total_cliques / total_impressoes * 100), 2) if total_impressoes > 0 else 0.0
    cpc_geral = round((total_custo_reais / total_cliques), 2) if total_cliques > 0 else 0.0

    return {
        "disponivel": True,
        "plataforma": "google_ads",
        "periodo_dias": dias,
        "data_inicio": data_inicio.isoformat(),
        "data_fim": data_fim.isoformat(),
        "resumo": {
            "gasto_total_reais": round(total_custo_reais, 2),
            "impressoes": total_impressoes,
            "cliques": total_cliques,
            "conversoes": round(total_conversoes, 2),
            "ctr_percentual": ctr_geral,
            "cpc_medio_reais": cpc_geral,
        },
        "campanhas": campanhas,
    }
