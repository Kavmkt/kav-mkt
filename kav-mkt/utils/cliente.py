"""Carrega tudo de um cliente a partir da pasta clientes/<slug>/ (ver clientes/README.md).

Um cliente novo = uma pasta nova; nenhum código precisa mudar.
"""
import json
import re
from pathlib import Path
from typing import Optional

CLIENTES_DIR = Path(__file__).resolve().parent.parent / "clientes"
EXTENSOES_IMAGEM = {".png", ".jpg", ".jpeg", ".webp"}
MAX_REFERENCIAS = 10


def listar_clientes() -> list:
    return sorted(p.name for p in CLIENTES_DIR.iterdir() if (p / "skill.md").exists())


def carregar_cliente(slug: str) -> dict:
    pasta = CLIENTES_DIR / slug
    caminho_skill = pasta / "skill.md"
    if not caminho_skill.exists():
        raise FileNotFoundError(
            f"Cliente '{slug}' não encontrado: falta {caminho_skill}. "
            "Copie a pasta clientes/ponto-car/ como modelo."
        )
    skill = caminho_skill.read_text(encoding="utf-8")
    config = _ler_json(pasta / "config.json", {})
    referencias = sorted(
        p for p in (pasta / "referencias").glob("*") if p.suffix.lower() in EXTENSOES_IMAGEM
    )[:MAX_REFERENCIAS]
    return {
        "slug": slug,
        "nome": config.get("nome") or slug.replace("-", " ").title(),
        "config": config,
        "skill": skill,
        "legenda_padrao": _ler_texto(pasta / "legenda.md"),
        "catalogo": _ler_json(pasta / "catalogo.json", {"produtos": []}),
        "produtos_coringa": _itens_da_secao(skill, "Produtos Coringa"),
        "referencias": referencias,
        "logo": _existente(pasta / "logo.png"),
    }


def _ler_json(caminho: Path, padrao: dict) -> dict:
    if not caminho.exists():
        return padrao
    return json.loads(caminho.read_text(encoding="utf-8"))


def _ler_texto(caminho: Path) -> str:
    return caminho.read_text(encoding="utf-8") if caminho.exists() else ""


def _existente(caminho: Path) -> Optional[Path]:
    return caminho if caminho.exists() else None


def _itens_da_secao(texto: str, titulo: str) -> list:
    m = re.search(rf"##\s*{re.escape(titulo)}\s*\n(.*?)(?=\n##|\Z)", texto, re.DOTALL | re.IGNORECASE)
    if not m:
        return []
    return [item.strip() for item in re.findall(r"^\s*-\s*(.+)$", m.group(1), re.MULTILINE) if item.strip()]
