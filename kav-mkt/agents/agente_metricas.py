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
            consolidado["canais"]["meta_ads"] = metricas_meta.insights_anuncios(
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
        consolidado["canais"]["meta_ads"] = {
            "disponivel": False,
            "motivo": "Token de acesso do Meta não configurado no cliente ou secrets.",
        }
        consolidado["canais"]["instagram_organico"] = {
            "disponivel": False,
            "motivo": "Token de acesso do Meta não configurado no cliente ou secrets.",
        }

    # 2. Google Ads
    if google_config.get("customer_id"):
        consolidado["canais"]["google_ads"] = metricas_google_ads.obter_insights(
            customer_id=google_config["customer_id"],
            dias=dias,
        )
    else:
        consolidado["canais"]["google_ads"] = {
            "disponivel": False,
            "motivo": "Google Ads não configurado para este cliente.",
        }

    return consolidado


def obter_status_operacao(slug: str) -> dict:
    """Obtém o status da operação e métricas para o cliente (compatibilidade com app.py e supervisor)."""
    try:
        from utils.cliente import carregar_cliente
        cliente = carregar_cliente(slug)
    except Exception:
        cliente = {"slug": slug, "nome": slug.replace("-", " ").title(), "config": {}}

    try:
        dados = coletar(cliente)
    except Exception as exc:
        dados = {"canais": {}, "erro": str(exc)}

    canais = dados.get("canais", {})
    meta_ads = canais.get("meta_ads", {})
    insta = canais.get("instagram_organico", {})

    gasto_total = 0.0
    conversas_whatsapp = 0
    if meta_ads.get("disponivel") and meta_ads.get("totais"):
        totais = meta_ads["totais"]
        gasto_total = float(totais.get("gasto", 0.0) or 0.0)
        conversas_whatsapp = int(totais.get("conversas_whatsapp", 0) or 0)

    seguidores = "N/D"
    total_posts = "N/D"
    if insta.get("disponivel"):
        seguidores = insta.get("seguidores", "N/D")
        total_posts = insta.get("total_posts", "N/D")

    return {
        "cliente": cliente.get("nome", slug),
        "slug": slug,
        "dados_brutos": dados,
        "metricas": {
            "gasto_total": gasto_total,
            "conversas_whatsapp": conversas_whatsapp,
        },
        "instagram": {
            "seguidores": seguidores,
            "total_posts": total_posts,
        },
    }
