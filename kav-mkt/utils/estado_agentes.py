"""Gerenciador de Estado do Escritório Virtual da Kav (@kav.mkt).

Registra em tempo real a atividade, status e mensagens de cada agente (avatar/funcionário)
para que o front-end visual (escritório estilo Habbo/isométrico) leia e exiba dinamicamente
o time trabalhando.

Desacoplado por dados: os agentes apenas chamam `atualizar_agente()`, e o front-end lê
o arquivo de estado (localmente ou via branch 'dados' do GitHub).
"""
import base64
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from zoneinfo import ZoneInfo

import requests

BASE_DIR = Path(__file__).resolve().parent.parent
API_GITHUB = "https://api.github.com"
FUSO = ZoneInfo("America/Sao_Paulo")

FUNCIONARIOS_PADRAO = {
    "supervisor": {
        "id": "supervisor",
        "nome": "Sofia",
        "cargo": "Head de Inteligência & Estratégia",
        "departamento": "Diretoria",
        "avatar": "supervisor",
        "status": "alerta",
        "fala_atual": "53 conversas no WhatsApp nos últimos 30 dias. Feed precisa de novos posts urgentes!",
        "atividade_atual": "Supervisionando alinhamento de tráfego pago vs. presença orgânica",
        "historico_atividades": [
            {
                "timestamp": "2026-09-26T21:30:00",
                "atividade": "Alerta emitido: Meta Ads ativo com R$ 260,79 gastos e zero posts no feed há 6 meses.",
                "fala": "Feed parado precisa de atenção imediata."
            }
        ],
    },
    "metricas": {
        "id": "metricas",
        "nome": "Marcos",
        "cargo": "Analista de Tráfego & Performance",
        "departamento": "Performance",
        "avatar": "metricas",
        "status": "trabalhando",
        "fala_atual": "Meta Ads coletado: 594 cliques, CTR 2,1%, 53 conversas no WhatsApp.",
        "atividade_atual": "Conectado à Graph API do Meta (Conta: CA - N&N Alimentos)",
        "historico_atividades": [
            {
                "timestamp": "2026-09-26T21:25:00",
                "atividade": "Coleta Meta Marketing API: R$ 260,79 gastos em 30 dias.",
                "fala": "Campanhas de WhatsApp Ads ativas."
            }
        ],
    },
    "copywriter": {
        "id": "copywriter",
        "nome": "Beatriz",
        "cargo": "Redatora de Conteúdo & Copywriter",
        "departamento": "Criação",
        "avatar": "copywriter",
        "status": "online",
        "fala_atual": "Padrão de legenda Sabor de Casa carregado. Ganchos prontos!",
        "atividade_atual": "Escrevendo headlines e selos de pratos para o feed",
        "historico_atividades": [
            {
                "timestamp": "2026-09-26T21:10:00",
                "atividade": "Copy gerada: Headline Feijoada Completa com gancho de almoço.",
                "fala": "Copy pronta para revisão."
            }
        ],
    },
    "designer": {
        "id": "designer",
        "nome": "Lucas",
        "cargo": "Diretor de Arte & Designer",
        "departamento": "Criação",
        "avatar": "designer",
        "status": "trabalhando",
        "fala_atual": "Compondo headline e selo sobre a foto real do buffet em 1080x1440.",
        "atividade_atual": "Diagramando arte gráfica sobre foto real (sem alterar a comida)",
        "historico_atividades": [
            {
                "timestamp": "2026-09-26T21:05:00",
                "atividade": "Tratamento gráfico aplicado sobre foto real do buffet executivo.",
                "fala": "Arte finalizada em 1080x1440."
            }
        ],
    },
    "pesquisador": {
        "id": "pesquisador",
        "nome": "Enzo",
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
                "fala": "Curadoria do prato concluída."
            }
        ],
    },
}


def agora() -> datetime:
    return datetime.now(FUSO).replace(tzinfo=None)


def usa_github() -> bool:
    return bool(os.environ.get("GITHUB_TOKEN") and os.environ.get("GITHUB_REPO"))


def _arquivo_local() -> Path:
    return BASE_DIR / "data" / "estado_agentes.json"


def carregar_estado() -> dict:
    estado, _ = _ler()
    if not estado or "funcionarios" not in estado:
        return _inicializar_estado()
    return estado


def atualizar_agente(
    agente_id: str,
    status: str,
    fala: str,
    atividade: str,
    detalhes: Optional[dict] = None,
) -> None:
    estado, sha = _ler()
    if not estado or "funcionarios" not in estado:
        estado = _inicializar_estado()

    funcionarios = estado["funcionarios"]
    if agente_id not in funcionarios:
        funcionarios[agente_id] = {
            "id": agente_id,
            "nome": agente_id.capitalize(),
            "cargo": "Especialista de IA",
            "departamento": "Operações",
            "avatar": agente_id,
            "status": status,
            "fala_atual": fala,
            "atividade_atual": atividade,
            "historico_atividades": [],
        }

    agente = funcionarios[agente_id]
    agente["status"] = status
    agente["fala_atual"] = fala
    agente["atividade_atual"] = atividade
    agente["atualizado_em"] = agora().isoformat(timespec="seconds")

    novo_log = {
        "timestamp": agora().isoformat(timespec="seconds"),
        "atividade": atividade,
        "fala": fala,
    }
    if detalhes:
        novo_log["detalhes"] = detalhes

    historico_agente = agente.get("historico_atividades", [])
    historico_agente.insert(0, novo_log)
    agente["historico_atividades"] = historico_agente[:5]

    estado["ultima_atualizacao"] = agora().isoformat(timespec="seconds")
    _escrever(json.dumps(estado, ensure_ascii=False, indent=2), sha)


def _inicializar_estado() -> dict:
    return {
        "agencia": "Kav (@kav.mkt)",
        "versao": "1.0",
        "ultima_atualizacao": agora().isoformat(timespec="seconds"),
        "funcionarios": FUNCIONARIOS_PADRAO.copy(),
    }


def _ler() -> tuple:
    if usa_github():
        try:
            return _ler_github()
        except Exception:
            pass
    arquivo = _arquivo_local()
    if not arquivo.exists():
        return {}, None
    try:
        return json.loads(arquivo.read_text(encoding="utf-8")), None
    except Exception:
        return {}, None


def _escrever(conteudo: str, sha: Optional[str]) -> None:
    arquivo = _arquivo_local()
    arquivo.parent.mkdir(parents=True, exist_ok=True)
    arquivo.write_text(conteudo, encoding="utf-8")

    pasta_escritorio = BASE_DIR.parent / "escritorio-kav"
    if pasta_escritorio.exists():
        (pasta_escritorio / "estado_agentes.json").write_text(conteudo, encoding="utf-8")

    if usa_github():
        try:
            _escrever_github(conteudo, sha)
        except Exception:
            pass


def _config_github() -> tuple:
    return (
        os.environ["GITHUB_TOKEN"],
        os.environ["GITHUB_REPO"],
        os.environ.get("GITHUB_BRANCH_DADOS", "dados"),
    )


def _headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def _ler_github() -> tuple:
    token, repo, branch = _config_github()
    url = f"{API_GITHUB}/repos/{repo}/contents/escritorio/estado_agentes.json"
    resposta = requests.get(url, params={"ref": branch}, headers=_headers(token), timeout=15)
    if resposta.status_code == 404:
        return {}, None
    resposta.raise_for_status()
    dados = resposta.json()
    conteudo_json = json.loads(base64.b64decode(dados["content"]).decode("utf-8"))
    return conteudo_json, dados.get("sha")


def _escrever_github(conteudo: str, sha: Optional[str]) -> None:
    token, repo, branch = _config_github()
    url = f"{API_GITHUB}/repos/{repo}/contents/escritorio/estado_agentes.json"
    corpo = {
        "message": "escritorio: atualiza estado dos agentes",
        "content": base64.b64encode(conteudo.encode("utf-8")).decode("ascii"),
        "branch": branch,
    }
    if sha:
        corpo["sha"] = sha
    requests.put(url, json=corpo, headers=_headers(token), timeout=15)
