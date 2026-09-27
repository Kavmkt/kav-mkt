"""Agente de Métricas: coleta e consolida dados quantitativos de canais de marketing
(Meta Ads, Instagram Orgânico e Google Ads) para o cliente.

DECISÃO DE ARQUITETURA:
Este agente NÃO faz chamadas de IA e NÃO gera análises em linguagem natural.
Sua função é puramente coletar, filtrar e estruturar os dados brutos e organizados.
A interpretação, alertas e cruzamento estratégico ficam exclusivamente a cargo do
Agente Supervisor (agents/agente_supervisor.py).
"""
from typing import Dict

from utils import metricas_google_ads, metricas_meta


def coletar(cliente: dict, dias: int = 30) -> dict:
    """Coleta e agrega as métricas de marketing do cliente no período especificado.
    
    Args:
        cliente: Dicionário carregado do cliente.
        dias: Quantidade de dias para retroagir a análise (padrão: 30).
        
    Returns:
        Dicionário consolidado com status e números de cada plataforma.
    """
    slug = cliente["slug"]
    config = cliente.get("config", {})
    meta_config = config.get("meta", {})
    google_config = config.get("google_ads", {})

    consolidado = {
        "cliente": cliente.get("nome", slug),
        "slug": slug,
        "periodo_dias": dias,
        "canais": {},
    }

    # 1. Meta (Instagram Orgânico + Anúncios Pagos)
    token_meta = metricas_meta.obter_token_cliente(slug)
    ad_account_id = meta_config.get("ad_account_id")
    instagram_id = meta_config.get("instagram_account_id")

    if token_meta:
        if instagram_id:
            consolidado["canais"]["instagram_organico"] = metricas_meta.insights_organicos(
                instagram_account_id=instagram_id,
                token=token_meta,
                dias=dias,
            )
        else:
            consolidado["canais"]["instagram_organico"] = {
                "disponivel": False,
                "motivo": "Campo 'meta.instagram_account_id' não configurado em config.json.",
            }

        if ad_account_id:
            consolidado["canais"]["meta_ads"] = metricas_meta.insights_pagos(
                ad_account_id=ad_account_id,
                token=token_meta,
                dias=dias,
            )
        else:
            consolidado["canais"]["meta_ads"] = {
                "disponivel": False,
                "motivo": "Campo 'meta.ad_account_id' não configurado em config.json.",
            }
    else:
        consolidado["canais"]["meta"] = {
            "disponivel": False,
            "motivo": f"Variável de ambiente META_ACCESS_TOKEN__{slug.upper().replace('-', '_')} não encontrada no .env.",
        }

    # 2. Google Ads (canal opcional com graceful fallback)
    customer_id = google_config.get("customer_id")
    if customer_id and metricas_google_ads.credenciais_configuradas():
        consolidado["canais"]["google_ads"] = metricas_google_ads.buscar_metricas_campanhas(
            customer_id=customer_id,
            dias=dias,
        )
    else:
        consolidado["canais"]["google_ads"] = {
            "disponivel": False,
            "motivo": "Google Ads inativo (aguardando credenciais futuras).",
        }

    return consolidado
