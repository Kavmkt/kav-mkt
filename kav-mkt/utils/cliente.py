"""Carrega tudo de um cliente a partir da pasta clientes/<slug>/ (ver clientes/README.md).

Um cliente novo = uma pasta nova; nenhum código precisa mudar.
"""
from __future__ import annotations
import json
import re
from pathlib import Path
from typing import Optional, Tuple

CLIENTES_DIR = Path(__file__).resolve().parent.parent / "clientes"
EXTENSOES_IMAGEM = {".png", ".jpg", ".jpeg", ".webp"}
MAX_REFERENCIAS = 10
MAX_FOTOS = 500


def listar_clientes() -> list:
    encontrados = set()
    if CLIENTES_DIR.exists():
        for p in CLIENTES_DIR.iterdir():
            if (p / "skill.md").exists():
                encontrados.add(p.name)
        for slug in ["nn-restaurante", "kav", "ponto-car"]:
            if (CLIENTES_DIR / slug / "skill.md").exists():
                encontrados.add(slug)
    return sorted(encontrados)


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

    catalogo = _ler_json(pasta / "catalogo.json", {"produtos": []})
    if not isinstance(catalogo, dict):
        catalogo = {"produtos": []}

    return {
        "slug": slug,
        "nome": config.get("nome") or slug.replace("-", " ").title(),
        "config": config,
        "tipo": config.get("tipo", "produto" if (pasta / "catalogo.json").exists() else "estatico"),
        "skill": skill,
        "legenda_padrao": _ler_texto(pasta / "legenda.md"),
        "catalogo": catalogo,
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
    """Carrega o logotipo do cliente, priorizando rigorosamente os arquivos oficiais na raiz."""
    # 1. Prioriza SEMPRE arquivos oficiais autênticos na raiz da pasta do cliente
    fundo_escuro = _existente(pasta / "logo-fundo-escuro.png") or _existente(pasta / "logo_fundo_escuro.png")
    fundo_claro = _existente(pasta / "logo-fundo-claro.png") or _existente(pasta / "logo_fundo_claro.png")
    logo_generico = _existente(pasta / "logo.png")

    pasta_logo = pasta / "logo"
    if not pasta_logo.is_dir() and (pasta / "logos").is_dir():
        pasta_logo = pasta / "logos"

    arquivos_logo = []
    if pasta_logo.is_dir():
        arquivos_logo = sorted(
            p for p in pasta_logo.glob("*") if p.suffix.lower() in EXTENSOES_IMAGEM
        )

    logo_pasta = arquivos_logo[0] if arquivos_logo else None
    principal = fundo_escuro or fundo_claro or logo_generico or logo_pasta

    if not arquivos_logo and principal:
        arquivos_logo = [principal]

    logos = {
        "fundo-escuro": fundo_escuro or principal,
        "fundo-claro": fundo_claro or principal,
        "principal": principal,
    }
    return logos, principal, arquivos_logo


def _carregar_referencias(pasta: Path) -> list:
    if pasta.parent.name == "kav":
        try:
            from utils.gerador_referencias import garantir_referencias_kav
            garantir_referencias_kav(pasta)
        except Exception:
            pass
    if not pasta.exists():
        return []
    metadados = _ler_json(pasta / "referencias.json", {})
    meta_dict = {item["arquivo"]: item for item in metadados if "arquivo" in item} if isinstance(metadados, list) else metadados
    arquivos_map = {p.name: p for p in pasta.glob("*") if p.suffix.lower() in EXTENSOES_IMAGEM}
    for nome in meta_dict.keys():
        p = pasta / nome
        if p.exists() and p.suffix.lower() in EXTENSOES_IMAGEM:
            arquivos_map[nome] = p
    return [{**meta_dict.get(nome, {}), "arquivo": p} for nome, p in sorted(arquivos_map.items())[:MAX_REFERENCIAS]]


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
