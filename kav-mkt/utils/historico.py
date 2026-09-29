"""Módulo de Persistência e Anti-Repetição Histórica.

Garante que nenhuma pauta ou layout seja repetido consecutivamente para o mesmo cliente,
respeitando a janela configurada em dias_sem_repetir_pauta e dias_sem_repetir_layout.
"""
from datetime import datetime, timedelta
import json
from pathlib import Path
import random
from typing import Optional

BASE_DIR = Path(__file__).resolve().parent.parent
CLIENTES_DIR = BASE_DIR / "clientes"


def caminho_historico(slug: str) -> Path:
    return CLIENTES_DIR / slug / "historico.json"


def carregar_historico(slug: str) -> dict:
    caminho = caminho_historico(slug)
    if not caminho.exists():
        return {"posts": []}
    try:
        return json.loads(caminho.read_text(encoding="utf-8"))
    except Exception:
        return {"posts": []}


def salvar_historico(slug: str, dados: dict) -> None:
    caminho = caminho_historico(slug)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")


def registrar_post(
    slug: str,
    pauta: dict,
    copy: dict,
    referencia_nome: Optional[str] = None,
    formato: str = "estatico",
) -> dict:
    """Registra uma publicação no histórico do cliente para alimentar o filtro anti-repetição."""
    dados = carregar_historico(slug)
    agora_iso = datetime.now().isoformat()

    registro = {
        "id": f"post_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "data": agora_iso,
        "pauta_id": pauta.get("id"),
        "pauta_tema": pauta.get("tema"),
        "pilar": pauta.get("pilar"),
        "headline": copy.get("headline_imagem") or copy.get("headline"),
        "referencia": referencia_nome,
        "formato": formato,
    }

    dados["posts"].append(registro)
    salvar_historico(slug, dados)
    return registro


def listar_posts_cliente(slug: str) -> list[dict]:
    return carregar_historico(slug).get("posts", [])


def escolher_pauta_sem_repetir(cliente: dict, pautas: list[dict]) -> dict:
    """Seleciona uma pauta da lista excluindo aquelas usadas dentro da janela de anti-repetição."""
    if not pautas:
        raise ValueError(f"Nenhuma pauta cadastrada para o cliente {cliente.get('slug')}.")

    slug = cliente.get("slug", "")
    config = cliente.get("config", {})
    dias_limite = int(config.get("dias_sem_repetir_pauta", 30))
    limite_dt = datetime.now() - timedelta(days=dias_limite)

    historico_posts = listar_posts_cliente(slug)
    pautas_bloqueadas = set()

    for p in historico_posts:
        data_str = p.get("data")
        if data_str:
            try:
                dt = datetime.fromisoformat(data_str)
                if dt >= limite_dt:
                    if p.get("pauta_id"):
                        pautas_bloqueadas.add(p["pauta_id"])
                    if p.get("pauta_tema"):
                        pautas_bloqueadas.add(p["pauta_tema"])
            except ValueError:
                pass

    disponiveis = [p for p in pautas if p.get("id") not in pautas_bloqueadas and p.get("tema") not in pautas_bloqueadas]

    if disponiveis:
        return random.choice(disponiveis)

    # Se todas as pautas foram usadas no período, pega a usada há mais tempo
    ultima_data_por_id = {}
    for p in historico_posts:
        pid = p.get("pauta_id") or p.get("pauta_tema")
        if pid and p.get("data"):
            ultima_data_por_id[pid] = p["data"]

    pautas_ordenadas = sorted(
        pautas,
        key=lambda item: ultima_data_por_id.get(item.get("id") or item.get("tema"), "1970-01-01"),
    )
    return pautas_ordenadas[0]


def escolher_referencia_sem_repetir(cliente: dict) -> Optional[dict]:
    """Seleciona um layout de referência do cliente realizando rodízio contínuo sem repetições consecutivas."""
    referencias = cliente.get("referencias", [])
    if not referencias:
        return None

    slug = cliente.get("slug", "")
    config = cliente.get("config", {})
    dias_limite = int(config.get("dias_sem_repetir_layout", 15))
    limite_dt = datetime.now() - timedelta(days=dias_limite)

    historico_posts = listar_posts_cliente(slug)
    layouts_usados_recentes = set()

    for p in historico_posts:
        data_str = p.get("data")
        ref = p.get("referencia")
        if data_str and ref:
            try:
                dt = datetime.fromisoformat(data_str)
                if dt >= limite_dt:
                    layouts_usados_recentes.add(ref)
            except ValueError:
                pass

    disponiveis = [r for r in referencias if r["arquivo"].name not in layouts_usados_recentes]

    if disponiveis:
        return random.choice(disponiveis)

    # Se todos já foram usados, pega o layout usado há mais tempo (round-robin)
    ultima_data_por_ref = {}
    for p in historico_posts:
        ref = p.get("referencia")
        if ref and p.get("data"):
            ultima_data_por_ref[ref] = p["data"]

    referencias_ordenadas = sorted(
        referencias,
        key=lambda item: ultima_data_por_ref.get(item["arquivo"].name, "1970-01-01"),
    )
    return referencias_ordenadas[0]


def agora() -> datetime:
    return datetime.now()


def carregar(slug: str) -> list:
    return listar_posts_cliente(slug)


def usa_github() -> bool:
    """Compatibilidade com telas antigas: o histórico agora é sempre local (clientes/<slug>/historico.json)."""
    return False


def ultimo_uso_por_produto(slug: str) -> dict:
    """Retorna {id_do_produto_ou_pauta: data de uso mais recente}, para checar repetição."""
    ultimo: dict = {}
    for registro in listar_posts_cliente(slug):
        produto_id = registro.get("produto_id") or registro.get("pauta_id")
        data_str = registro.get("data")
        if not produto_id or not data_str:
            continue
        try:
            quando = datetime.fromisoformat(data_str)
        except ValueError:
            continue
        if quando > ultimo.get(produto_id, datetime.min):
            ultimo[produto_id] = quando
    return ultimo


def registrar(slug: str, registro: dict) -> dict:
    """Registra um evento genérico (produto/foto usados) no histórico do cliente."""
    dados = carregar_historico(slug)
    novo = {"data": datetime.now().isoformat(), **registro}
    dados.setdefault("posts", []).append(novo)
    salvar_historico(slug, dados)
    return novo
