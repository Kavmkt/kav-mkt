"""Agente Supervisor: inteligência observadora e consultiva da Kav (@kav.mkt).

Cruza o histórico de publicações criadas (utils/historico.py) com os dados reais de
métricas consolidadas (Instagram orgânico, Meta Ads e Google Ads) e o histórico de
snapshots anteriores (utils/metricas_historico.py).

DECISÃO DE ARQUITETURA E REGRA INEGOCIÁVEL:
O Supervisor NUNCA age sozinho. Ele não pausa campanhas, não altera orçamentos, não cria
nem publica posts por conta própria. Sua responsabilidade é diagnosticar friamente o
cenário, detectar desvios (ex: verba gasta em anúncios de WhatsApp sem nenhuma postagem
orgânica de apoio no Instagram há meses), comparar períodos e sugerir ações prioritárias
para que Kesley e a equipe da Kav tomem a decisão.
"""
from typing import Optional

from utils import historico, metricas_historico
from utils.openai_client import chamar_ia, extrair_json

SYSTEM_PROMPT = """Você é o Supervisor de Inteligência da Kav (@kav.mkt), uma agência de marketing digital de alta performance.
Sua função é atuar como o cérebro analítico e consultor estratégico de marketing para a conta do cliente.

DIRETRIZES DA MARCA DO CLIENTE:
__SKILL__

SUA POSTURA E LIMITES OPERACIONAIS:
- Você é estritamente consultivo e analítico. NUNCA simule nem afirme que executou ações em plataformas reais.
- Seja sincero, direto e crítico nos números. Identifique desperdícios, inconsistências entre mídia paga e comunicação orgânica, e gargalos de conversão.
- Use tom profissional, técnico e propositivo.

FORMATO OBRIGATÓRIO DE SAÍDA:
Retorne ESTRITAMENTE um objeto JSON válido, sem texto antes ou depois, com a seguinte estrutura:
{
  "status_geral": "saudavel" | "atencao" | "critico",
  "resumo_executivo": "1 parágrafo denso e direto resumindo a saúde do marketing e o principal ponto de atenção.",
  "alertas": [
    {
      "nivel": "critico" | "atencao" | "informativo",
      "titulo": "Título curto do alerta",
      "descricao": "Explicação detalhada com números reais",
      "impacto": "O que isso acarreta no negócio do cliente"
    }
  ],
  "cruzamento_midia_e_conteudo": {
    "diagnostico_organico": "Avaliação do ritmo de publicação e engajamento orgânico recente.",
    "diagnostico_pago": "Avaliação da eficiência das campanhas de tráfego pago (CTR, CPC/CPM, conversas/vendas).",
    "alinhamento": "Como a mídia paga e o conteúdo orgânico estão conversando (ou se estão desconectados)."
  },
  "comparativo_periodos": "Análise da evolução frente aos snapshots anteriores (se houver histórico).",
  "recomendacoes_prioritarias": [
    {
      "prioridade": 1,
      "acao": "O que o gestor deve fazer",
      "justificativa": "Por que fazer isso agora com base nos números"
    }
  ]
}
"""


def supervisionar(cliente: dict, metricas_atuais: Optional[dict] = None) -> dict:
    """Executa a análise do Supervisor para um cliente.
    
    Args:
        cliente: Dicionário carregado do cliente (com skill, config, slug, etc.).
        metricas_atuais: Dicionário com os dados de métricas coletados no período.
            Se omitido, tenta buscar o coletor do agente_metricas ou o último snapshot.
            
    Returns:
        Dicionário com a análise estruturada em JSON.
    """
    slug = cliente["slug"]

    # 1. Carrega histórico de posts criados
    posts_recentes = historico.carregar(slug)
    
    # 2. Carrega snapshots anteriores de métricas para comparação
    historico_snapshots = metricas_historico.obter_historico_recente(slug, limite=3)
    
    # 3. Resolve as métricas atuais
    if not metricas_atuais:
        # Tenta coletar sob demanda se o agente_metricas estiver disponível
        try:
            from agents import agente_metricas
            metricas_atuais = agente_metricas.coletar(cliente)
        except Exception:
            ultimo = metricas_historico.obter_ultimo_snapshot(slug)
            metricas_atuais = ultimo.get("dados", {}) if ultimo else {}

    # 4. Registra snapshot se houver métricas reais coletadas
    if metricas_atuais:
        try:
            metricas_historico.registrar_snapshot(slug, metricas_atuais)
        except Exception:
            pass  # Não trava a análise se a gravação do snapshot falhar

    # 5. Monta o prompt de análise
    system = SYSTEM_PROMPT.replace("__SKILL__", cliente.get("skill", ""))
    
    prompt = _montar_prompt_analise(
        cliente=cliente,
        metricas=metricas_atuais,
        posts=posts_recentes,
        snapshots_anteriores=historico_snapshots,
    )

    resposta = chamar_ia(system=system, prompt=prompt, max_tokens=1500, temperature=0.5, json_mode=True)
    return extrair_json(resposta)


def _montar_prompt_analise(cliente: dict, metricas: dict, posts: list, snapshots_anteriores: list) -> str:
    partes = [
        f"CLIENTE: {cliente.get('nome', cliente.get('slug'))} (Tipo: {cliente.get('config', {}).get('tipo')})",
        "",
        "--- DADOS DE MÉTRICAS DO PERÍODO ATUAL ---",
        str(metricas) if metricas else "Nenhum dado de métrica coletado para o período.",
        "",
        f"--- HISTÓRICO DE POSTS GERADOS/REGISTRADOS ({len(posts)} registros recentes) ---",
    ]

    if posts:
        for p in posts[-5:]:
            partes.append(f"- Data: {p.get('criado_em', 'N/D')} | Produto/Pauta: {p.get('produto_nome') or p.get('pauta_tema')} | Headline: {p.get('headline')}")
    else:
        partes.append("Nenhum post registrado no histórico para este cliente até o momento.")

    partes.append("")
    partes.append(f"--- HISTÓRICO DE SNAPSHOTS ANTERIORES ({len(snapshots_anteriores)} snapshots) ---")
    if snapshots_anteriores:
        for snap in snapshots_anteriores:
            partes.append(f"- Data Snapshot: {snap.get('data')} | Canais: {list(snap.get('dados', {}).get('canais', {}).keys())}")
    else:
        partes.append("Sem histórico anterior registrado (este é o primeiro snapshot).")

    return "\n".join(partes)


def analisar_alinhamento_cliente(slug: str, status_ops: Optional[dict] = None) -> dict:
    """Analisa o alinhamento de marketing e tráfego pago para exibição no dashboard do app.py."""
    try:
        from utils.cliente import carregar_cliente
        cliente = carregar_cliente(slug)
    except Exception:
        cliente = {"slug": slug, "nome": slug.replace("-", " ").title(), "config": {}, "skill": ""}

    try:
        metricas = status_ops.get("dados_brutos") if status_ops else None
        resultado = supervisionar(cliente, metricas_atuais=metricas)
        
        alertas = resultado.get("alertas", [])
        alerta_principal = alertas[0].get("mensagem") if alertas else None
        
        cruzamento = resultado.get("cruzamento_midia_e_conteudo", {})
        texto_diag = []
        if resultado.get("resumo_executivo"):
            texto_diag.append(f"**Resumo:** {resultado['resumo_executivo']}")
        if cruzamento.get("alinhamento"):
            texto_diag.append(f"**Alinhamento:** {cruzamento['alinhamento']}")
        if cruzamento.get("diagnostico_pago"):
            texto_diag.append(f"**Tráfego Pago:** {cruzamento['diagnostico_pago']}")
        if cruzamento.get("diagnostico_organico"):
            texto_diag.append(f"**Orgânico:** {cruzamento['diagnostico_organico']}")

        recs = [
            f"**{r.get('acao')}:** {r.get('justificativa')}"
            for r in resultado.get("recomendacoes_prioritarias", [])
        ]

        return {
            "alerta_principal": alerta_principal,
            "diagnostico_completo": "\n\n".join(texto_diag) or "Operação monitorada com sucesso.",
            "recomendacoes": recs,
            "detalhes": resultado,
        }
    except Exception as exc:
        return {
            "alerta_principal": "Métricas em fase de coleta ou configuração.",
            "diagnostico_completo": f"O supervisor está monitorando a conta (Detalhamento operacional: {exc}).",
            "recomendacoes": [
                "Manter o ritmo de publicações no feed do Instagram para alimentar o público das campanhas de WhatsApp.",
                "Configurar os tokens de acesso do Meta Graph API em config.json para sincronizar métricas em tempo real."
            ],
        }
