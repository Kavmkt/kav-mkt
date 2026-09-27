"""Histórico de snapshots de métricas de marketing por cliente (Meta Ads, Instagram orgânico
e Google Ads) — usado pelo Supervisor para comparar períodos, identificar tendências e
emitir alertas estratégicos ao longo do tempo.

Espelha a arquitetura de utils/historico.py:
No Streamlit Community Cloud o disco é efêmero ao reiniciar, então os snapshots de métricas
ficam salvos no repositório do GitHub, na branch "dados", sob a pasta metricas/<cliente>.json.
Ative configurando GITHUB_TOKEN e GITHUB_REPO no ambiente (.env ou Secrets); sem eles, os
snapshots são gravados em arquivo local (data/<cliente>/metricas.json).
"""
import base64
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Tuple
from zoneinfo import ZoneInfo

import requests

BASE_DIR = Path(__file__).resolve().parent.parent
API_GITHUB = "https://api.github.com"
FUSO = ZoneInfo("America/Sao_Paulo")

# Mantemos até 180 dias de snapshots para permitir análises trimestrais e semestrais
# sem exceder o limite de arquivo da API do GitHub.
RETER_DIAS = 180


def agora() -> datetime:
    return datetime.now(FUSO).replace(tzinfo=None)


def usa_github() -> bool:
    return bool(os.environ.get("GITHUB_TOKEN") and os.environ.get("GITHUB_REPO"))


def carregar(cliente: str) -> list:
    """Carrega todos os snapshots de métricas salvos para o cliente."""
    registros, _ = _ler(cliente)
    return registros


def obter_ultimo_snapshot(cliente: str) -> Optional[dict]:
    """Retorna o snapshot mais recente salvo para o cliente, ou None se não houver."""
    registros = carregar(cliente)
    if not registros:
        return None
    return max(registros, key=_data)


def obter_historico_recente(cliente: str, limite: int = 5) -> list:
    """Retorna os últimos N snapshots ordenados do mais recente para o mais antigo."""
    registros = carregar(cliente)
    ordenados = sorted(registros, key=_data, reverse=True)
    return ordenados[:limite]


def registrar_snapshot(cliente: str, metricas: dict, periodo_dias: int = 30) -> None:
    """Salva um novo snapshot de métricas para o cliente.
    
    Remove registros anteriores ao limite de retenção (180 dias) para manter o arquivo leve.
    """
    registros, sha = _ler(cliente)
    corte = agora() - timedelta(days=RETER_DIAS)
    registros = [r for r in registros if _data(r) >= corte]

    novo_registro = {
        "timestamp": agora().isoformat(timespec="seconds"),
        "periodo_dias": periodo_dias,
        "dados": metricas,
    }
    registros.append(novo_registro)

    _escrever(cliente, json.dumps(registros, ensure_ascii=False, indent=2), sha)


def _data(registro: dict) -> datetime:
    try:
        campo_data = registro.get("timestamp") or registro.get("data")
        return datetime.fromisoformat(campo_data)
    except (KeyError, ValueError, TypeError):
        return datetime.min


# --- Armazenamento (Local vs GitHub branch 'dados') -----------------------------------

def _arquivo_local(cliente: str) -> Path:
    return BASE_DIR / "data" / cliente / "metricas.json"


def _ler(cliente: str) -> Tuple[list, Optional[str]]:
    if usa_github():
        return _ler_github(cliente)
    arquivo = _arquivo_local(cliente)
    if not arquivo.exists():
        return [], None
    try:
        return json.loads(arquivo.read_text(encoding="utf-8")), None
    except Exception:
        return [], None


def _escrever(cliente: str, conteudo: str, sha: Optional[str]) -> None:
    if usa_github():
        _escrever_github(cliente, conteudo, sha)
        return
    arquivo = _arquivo_local(cliente)
    arquivo.parent.mkdir(parents=True, exist_ok=True)
    arquivo.write_text(conteudo, encoding="utf-8")


def _config_github() -> Tuple[str, str, str]:
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


def _url_arquivo(repo: str, cliente: str) -> str:
    return f"{API_GITHUB}/repos/{repo}/contents/metricas/{cliente}.json"


def _ler_github(cliente: str) -> Tuple[list, Optional[str]]:
    token, repo, branch = _config_github()
    resposta = requests.get(
        _url_arquivo(repo, cliente), params={"ref": branch}, headers=_headers(token), timeout=20
    )
    if resposta.status_code == 404:
        return [], None
    resposta.raise_for_status()
    dados = resposta.json()
    conteudo_json = json.loads(base64.b64decode(dados["content"]).decode("utf-8"))
    return conteudo_json, dados.get("sha")


def _escrever_github(cliente: str, conteudo: str, sha: Optional[str]) -> None:
    token, repo, branch = _config_github()
    _garantir_branch(token, repo, branch)
    corpo = {
        "message": f"metricas: snapshot de {cliente}",
        "content": base64.b64encode(conteudo.encode("utf-8")).decode("ascii"),
        "branch": branch,
    }
    if sha:
        corpo["sha"] = sha
    requests.put(_url_arquivo(repo, cliente), json=corpo, headers=_headers(token), timeout=20).raise_for_status()


def _garantir_branch(token: str, repo: str, branch: str) -> None:
    """Cria a branch de dados se ela ainda não existir."""
    resposta = requests.get(f"{API_GITHUB}/repos/{repo}/git/ref/heads/{branch}", headers=_headers(token), timeout=20)
    if resposta.status_code == 200:
        return
    if resposta.status_code != 404:
        resposta.raise_for_status()
    info = requests.get(f"{API_GITHUB}/repos/{repo}", headers=_headers(token), timeout=20)
    info.raise_for_status()
    principal = info.json()["default_branch"]
    base = requests.get(f"{API_GITHUB}/repos/{repo}/git/ref/heads/{principal}", headers=_headers(token), timeout=20)
    base.raise_for_status()
    requests.post(
        f"{API_GITHUB}/repos/{repo}/git/refs",
        json={"ref": f"refs/heads/{branch}", "sha": base.json()['object']['sha']},
        headers=_headers(token),
        timeout=20,
    ).raise_for_status()
