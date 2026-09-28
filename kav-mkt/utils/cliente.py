"""Carrega tudo de um cliente a partir da pasta clientes/<slug>/ (ver clientes/README.md).

Um cliente novo = uma pasta nova; nenhum código precisa mudar.
"""
import json
import re
from pathlib import Path
from typing import Optional, Tuple

CLIENTES_DIR = Path(__file__).resolve().parent.parent / "clientes"
EXTENSOES_IMAGEM = {".png", ".jpg", ".jpeg", ".webp"}
MAX_REFERENCIAS = 10
MAX_FOTOS = 500


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
    logos, logo_principal, logo_referencias = _carregar_logos(pasta)

    return {
        "slug": slug,
        "nome": config.get("nome") or slug.replace("-", " ").title(),
        "config": config,
        "skill": skill,
        "legenda_padrao": _ler_texto(pasta / "legenda.md"),
        "catalogo": _ler_json(pasta / "catalogo.json", {"produtos": []}),
        "produtos_coringa": _itens_da_secao(skill, "Produtos Coringa"),
        "pautas": _ler_json(pasta / "pautas.json", {"pautas": []}),
        "carrossel_padrao": _ler_texto(pasta / "carrossel.md"),
        "referencias": _carregar_referencias(pasta / "referencias"),
        "fotos": _carregar_fotos(pasta / "fotos"),
        "logos": logos,
        "logo": logo_principal,
        "logo_referencias": logo_referencias,
    }


def _carregar_logos(pasta: Path) -> Tuple[dict, Optional[Path], list]:
    """Carrega o logotipo do cliente com suporte a arquivos raiz e à pasta logo/."""
    pasta_logo = pasta / "logo"
    arquivos_logo = []
    if pasta_logo.is_dir():
        arquivos_logo = sorted(
            p for p in pasta_logo.glob("*") if p.suffix.lower() in EXTENSOES_IMAGEM
        )

    logo_pasta = arquivos_logo[0] if arquivos_logo else None
    logo_generico = _existente(pasta / "logo.png") or logo_pasta
    fundo_escuro = _existente(pasta / "logo-fundo-escuro.png") or logo_generico
    fundo_claro = _existente(pasta / "logo-fundo-claro.png") or logo_generico
    principal = fundo_escuro or fundo_claro or logo_generico or logo_pasta

    logos = {
        "fundo-escuro": fundo_escuro,
        "fundo-claro": fundo_claro,
        "principal": principal,
    }
    return logos, principal, arquivos_logo


def _carregar_referencias(pasta: Path) -> list:
    if not pasta.exists():
        return []
    metadados = _ler_json(pasta / "referencias.json", {})
    arquivos = sorted(p for p in pasta.glob("*") if p.suffix.lower() in EXTENSOES_IMAGEM)[:MAX_REFERENCIAS]
    return [{**metadados.get(p.name, {}), "arquivo": p} for p in arquivos]


def _carregar_fotos(pasta: Path) -> list:
    if not pasta.exists():
        return []
    metadados = _ler_json(pasta / "fotos.json", {})
    arquivos = sorted(p for p in pasta.glob("*") if p.suffix.lower() in EXTENSOES_IMAGEM)[:MAX_FOTOS]
    return [{**metadados.get(p.name, {}), "arquivo": p} for p in arquivos]


def _ler_json(caminho: Path, padrao: dict) -> dict:
    if not caminho.exists():
        return padrao
    return json.loads(caminho.read_text(encoding="utf-8"))


def _ler_texto(caminho: Path) -> str:
    return caminho.read_text(encoding="utf-8") if caminho.exists() else ""


def _existente(caminho: Path) -> Optional[Path]:
    return caminho if caminho.exists() and caminho.is_file() else None


def _itens_da_secao(texto: str, titulo: str) -> list:
    m = re.search(rf"##\s*{re.escape(titulo)}\s*\n(.*?)(?=\n##|\Z)", texto, re.DOTALL | re.IGNORECASE)
    if not m:
        return []
    return [item.strip() for item in re.findall(r"^\s*-\s*(.+)$", m.group(1), re.MULTILINE) if item.strip()]
