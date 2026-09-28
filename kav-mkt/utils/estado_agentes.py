from __future__ import annotations
"""Mantém o estado dos agentes do Escritório Virtual (avatares, falas e histórico).

Salva e lê o arquivo `escritorio-kav/estado_agentes.json`, que é consumido pelo frontend
do escritório via fetch. Permite atualizar a fala, atividade e status de qualquer agente
(Augusto, Vicente, Clarice, Joaquim, Otavio, Benedito) durante a execução do pipeline.
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from zoneinfo import ZoneInfo

FUSO = ZoneInfo("America/Sao_Paulo")

ESTADO_FILE_RELATIVO = "escritorio-kav/estado_agentes.json"

# Definição padrão inicial dos agentes no escritório
FUNCIONARIOS_INICIAIS = {
    "supervisor": {
        "id": "supervisor",
        "nome": "Augusto",
        "cargo": "Head de Inteligência & Estratégia",
        "departamento": "Diretoria",
        "avatar": "supervisor",
        "status": "alerta",
        "fala_atual": "53 conversas no WhatsApp nos últimos 30 dias. Feed precisa de novos posts urgentes!",
        "atividade_atual": "Supervisionando alinhamento de tráfego pago vs. presença orgânica",
        "historico_atividades": [
            {
                "timestamp": "2026-09-26T21:15:00",
                "atividade": "Alerta emitido: Meta Ads ativo com R$ 260,79 gastos e zero posts no feed há 6 meses.",
                "fala": "Feed desatualizado detectado.",
            }
        ],
    },
    "metricas": {
        "id": "metricas",
        "nome": "Vicente",
        "cargo": "Analista de Tráfego & Performance",
        "departamento": "Performance",
        "avatar": "metricas",
        "status": "trabalhando",
        "fala_atual": "Meta Ads coletado: 594 cliques, CTR 2,1%, 53 conversas no WhatsApp iniciadas.",
        "atividade_atual": "Conectado à Graph API do Meta (Conta: CA - N&N Alimentos)",
        "historico_atividades": [
            {
                "timestamp": "2026-09-26T21:12:00",
                "atividade": "Coleta Meta Marketing API: R$ 260,79 gastos em 30 dias.",
                "fala": "Métricas sincronizadas.",
            }
        ],
    },
    "copywriter": {
        "id": "copywriter",
        "nome": "Clarice",
        "cargo": "Redatora de Conteúdo & Copywriter",
        "departamento": "Criação",
        "avatar": "copywriter",
        "status": "online",
        "fala_atual": "Padrão de legenda 'Sabor de Casa' carregado. Ganchos de almoço prontos!",
        "atividade_atual": "Escrevendo headlines e selos de pratos para o feed",
        "historico_atividades": [
            {
                "timestamp": "2026-09-26T21:10:00",
                "atividade": "Copy gerada: Headline Feijoada Completa com gancho de almoço.",
                "fala": "Copy pronta para revisão.",
            }
        ],
    },
    "designer": {
        "id": "designer",
        "nome": "Joaquim",
        "cargo": "Designer Júnior",
        "departamento": "Criação",
        "avatar": "designer",
        "status": "trabalhando",
        "fala_atual": "Compondo headline sobre a foto real do buffet em 1080x1440.",
        "atividade_atual": "Diagramando arte gráfica sobre foto real (sem alterar a comida)",
        "historico_atividades": [
            {
                "timestamp": "2026-09-26T21:05:00",
                "atividade": "Tratamento gráfico aplicado sobre foto real do buffet executivo.",
                "fala": "Arte finalizada em 1080x1440.",
            }
        ],
    },
    "diretor": {
        "id": "diretor",
        "nome": "Otávio",
        "cargo": "Diretor de Arte Sênior & Head Visual",
        "departamento": "Criação",
        "avatar": "designer",
        "status": "online",
        "fala_atual": "Supervisionando estética, tipografia refinada e integridade do logo oficial.",
        "atividade_atual": "Inspecionando e refinando peças do Joaquim com visão computacional",
        "historico_atividades": [
            {
                "timestamp": "2026-09-27T21:00:00",
                "atividade": "Inspeção visual e aprovação com visão computacional.",
                "fala": "Padrão de arte aprovado.",
            }
        ],
    },
    "pesquisador": {
        "id": "pesquisador",
        "nome": "Benedito",
        "cargo": "Curador de Acervo & Catálogo",
        "departamento": "Planejamento",
        "avatar": "pesquisador",
        "status": "online",
        "fala_atual": "33 fotos no acervo. Próximo prato sorteado sem repetição em 45 dias.",
        "atividade_atual": "Gerenciando fotos reais de pratos em clientes/nn-restaurante/fotos/",
        "historico_atividades": [
            {
                "timestamp": "2026-09-26T21:00:00",
                "atividade": "Foto selecionada: buffet_saladas_02.jpg (não usada há 50 dias).",
                "fala": "Curadoria do prato concluída.",
            }
        ],
    },
}


def _resolver_caminho_estado() -> Path:
    """Procura o caminho do estado_agentes.json considerando execução na raiz ou em subpastas."""
    possiveis = [
        Path.cwd() / ESTADO_FILE_RELATIVO,
        Path.cwd() / "kav-mkt" / ESTADO_FILE_RELATIVO,
        Path.cwd() / "estado_agentes.json",
        Path(__file__).resolve().parent.parent / "escritorio-kav" / "estado_agentes.json",
        Path(__file__).resolve().parent.parent.parent / "escritorio-kav" / "estado_agentes.json",
    ]
    for p in possiveis:
        if p.exists():
            return p
    # Fallback padrão
    p_padrao = Path(__file__).resolve().parent.parent / "escritorio-kav" / "estado_agentes.json"
    p_padrao.parent.mkdir(parents=True, exist_ok=True)
    return p_padrao


def carregar_estado() -> dict:
    caminho = _resolver_caminho_estado()
    if not caminho.exists():
        estado_inicial = {
            "ultima_atualizacao": datetime.now(FUSO).isoformat(),
            "funcionarios": FUNCIONARIOS_INICIAIS,
            "producao_recente": [],
        }
        salvar_estado(estado_inicial)
        return estado_inicial

    try:
        with open(caminho, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {
            "ultima_atualizacao": datetime.now(FUSO).isoformat(),
            "funcionarios": FUNCIONARIOS_INICIAIS,
            "producao_recente": [],
        }


def salvar_estado(dados: dict) -> None:
    caminho = _resolver_caminho_estado()
    dados["ultima_atualizacao"] = datetime.now(FUSO).isoformat()
    try:
        with open(caminho, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
    except Exception as exc:
        print(f"Não foi possível salvar estado dos agentes: {exc}")


def atualizar_agente(agente_id: str, status: Optional[str] = None, fala: Optional[str] = None, atividade: Optional[str] = None) -> None:
    estado = carregar_estado()
    funcs = estado.setdefault("funcionarios", FUNCIONARIOS_INICIAIS)
    if agente_id not in funcs:
        funcs[agente_id] = {
            "id": agente_id,
            "nome": agente_id.title(),
            "cargo": "Especialista",
            "departamento": "Operações",
            "status": "online",
            "fala_atual": "",
            "atividade_atual": "",
            "historico_atividades": [],
        }

    ag = funcs[agente_id]
    if status:
        ag["status"] = status
    if fala:
        ag["fala_atual"] = fala
    if atividade:
        ag["atividade_atual"] = atividade

    if fala or atividade:
        hist = ag.setdefault("historico_atividades", [])
        hist.insert(0, {
            "timestamp": datetime.now(FUSO).strftime("%Y-%m-%d %H:%M:%S"),
            "atividade": atividade or ag.get("atividade_atual", ""),
            "fala": fala or ag.get("fala_atual", ""),
        })
        ag["historico_atividades"] = hist[:10]  # Limita aos últimos 10

    salvar_estado(estado)


def registrar_post_produzido(post: dict, slug: str) -> None:
    estado = carregar_estado()
    lista = estado.setdefault("producao_recente", [])
    agora = datetime.now(FUSO)

    item_nome = (
        post.get("foto", {}).get("nome")
        or post.get("produto", {}).get("nome")
        or post.get("pauta", {}).get("tema")
        or "Post Pronto"
    )

    novo_registro = {
        "id": f"post-{int(agora.timestamp())}",
        "data": agora.strftime("%d/%m %H:%M"),
        "cliente": slug,
        "prato": item_nome,
        "categoria": post.get("foto", {}).get("categoria") or post.get("tipo_producao", "Almoço Executivo"),
        "headline": post.get("copy", {}).get("headline_imagem", "NOVO POST"),
        "selo": post.get("copy", {}).get("selo_produto", "Destaque"),
        "legenda": post.get("copy", {}).get("legenda", ""),
        "imagem_b64": post.get("imagem", {}).get("imagem_b64") if post.get("imagem") else None,
        "criadores": "Curadoria: Benedito · Texto: Clarice · Arte: Joaquim · Direção de Arte: Otávio",
    }

    lista.insert(0, novo_registro)
    estado["producao_recente"] = lista[:20]
    salvar_estado(estado)

    atualizar_agente(
        "designer",
        status="trabalhando",
        fala=f"Layout 1080x1440 pronto para {item_nome}.",
        atividade=f"Tratamento gráfico aplicado para {item_nome}",
    )
    atualizar_agente(
        "diretor",
        status="online",
        fala=f"Layout aprovado e inspecionado para {item_nome}!",
        atividade=f"Direção de Arte e supervisão visual concluída",
    )
