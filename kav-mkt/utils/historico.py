"""Histórico de posts criados por cliente — usado para não repetir produtos dentro de um
período (padrão 30 dias, configurável por cliente em config.json).

No Streamlit Community Cloud o disco é apagado quando o servidor reinicia, então o
histórico fica salvo no próprio repositório do GitHub, na branch "dados". O Streamlit só
acompanha a branch principal, por isso gravar lá não reinicia o app. Ative configurando
GITHUB_TOKEN e GITHUB_REPO nos Secrets; sem eles, o histórico vai para um arquivo local
(só serve para rodar no próprio computador).
"""
import base64
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import requests

BASE_DIR = Path(__file__).resolve().parent.parent
API_GITHUB = "https://api.github.com"
FUSO = ZoneInfo("America/Sao_Paulo")
# Registros mais antigos que isso são descartados ao gravar, pra o arquivo não crescer
# além do limite de leitura da API do GitHub (1 MB).
RETER_DIAS = 90


def agora() -> datetime:
    return datetime.now(FUSO).replace(tzinfo=None)


def usa_github() -> bool:
    return bool(os.environ.get("GITHUB_TOKEN") and os.environ.get("GITHUB_REPO"))


def carregar(cliente: str) -> list:
    registros, _ = _ler(cliente)
    return registros


def ultimo_uso_por_produto(cliente: str) -> dict:
    """Retorna {id_do_produto: data do uso mais recente}."""
    ultimo = {}
    for registro in carregar(cliente):
        produto_id = registro.get("produto_id")
        quando = _data(registro)
        if produto_id and quando > ultimo.get(produto_id, datetime.min):
            ultimo[produto_id] = quando
    return ultimo


def registrar(cliente: str, registro: dict) -> None:
    registros, sha = _ler(cliente)
    corte = agora() - timedelta(days=RETER_DIAS)
    registros = [r for r in registros if _data(r) >= corte]
    registros.append({"data": agora().isoformat(timespec="seconds"), **registro})
    _escrever(cliente, json.dumps(registros, ensure_ascii=False, indent=2), sha)


def _data(registro: dict) -> datetime:
    try:
        return datetime.fromisoformat(registro["data"])
    except (KeyError, ValueError):
        return datetime.min


# --- Armazenamento ------------------------------------------------------------------

def _arquivo_local(cliente: str) -> Path:
    return BASE_DIR / "data" / cliente / "historico.json"


def _ler(cliente: str) -> tuple:
    if usa_github():
        return _ler_github(cliente)
    arquivo = _arquivo_local(cliente)
    if not arquivo.exists():
        return [], None
    return json.loads(arquivo.read_text(encoding="utf-8")), None


def _escrever(cliente: str, conteudo: str, sha) -> None:
    if usa_github():
        _escrever_github(cliente, conteudo, sha)
        return
    arquivo = _arquivo_local(cliente)
    arquivo.parent.mkdir(parents=True, exist_ok=True)
    arquivo.write_text(conteudo, encoding="utf-8")


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


def _url_arquivo(repo: str, cliente: str) -> str:
    return f"{API_GITHUB}/repos/{repo}/contents/historico/{cliente}.json"


def _ler_github(cliente: str) -> tuple:
    token, repo, branch = _config_github()
    resposta = requests.get(
        _url_arquivo(repo, cliente), params={"ref": branch}, headers=_headers(token), timeout=20
    )
    if resposta.status_code == 404:  # arquivo (ou a própria branch) ainda não existe
        return [], None
    resposta.raise_for_status()
    dados = resposta.json()
    return json.loads(base64.b64decode(dados["content"]).decode("utf-8")), dados["sha"]


def _escrever_github(cliente: str, conteudo: str, sha) -> None:
    token, repo, branch = _config_github()
    _garantir_branch(token, repo, branch)
    corpo = {
        "message": f"historico: {cliente}",
        "content": base64.b64encode(conteudo.encode("utf-8")).decode("ascii"),
        "branch": branch,
    }
    if sha:
        corpo["sha"] = sha
    requests.put(_url_arquivo(repo, cliente), json=corpo, headers=_headers(token), timeout=20).raise_for_status()


def _garantir_branch(token: str, repo: str, branch: str) -> None:
    """Cria a branch de dados a partir da branch principal na primeira gravação."""
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
        json={"ref": f"refs/heads/{branch}", "sha": base.json()["object"]["sha"]},
        headers=_headers(token),
        timeout=20,
    ).raise_for_status()
