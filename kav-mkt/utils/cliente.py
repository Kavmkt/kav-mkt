"""Carrega tudo de um cliente a partir da pasta clientes/<slug>/ (ver clientes/README.md).

Um cliente novo = uma pasta nova; nenhum código precisa mudar.
"""
from __future__ import annotations
import json
from pathlib import Path
import re
from typing import Optional, Tuple

CLIENTES_DIR = Path(__file__).resolve().parent.parent / "clientes"
EXTENSOES_IMAGEM = {".png", ".jpg", ".jpeg", ".webp"}
EXTENSOES_LOGO = {".png", ".jpg", ".jpeg", ".webp", ".svg"}
MAX_REFERENCIAS = 5
MAX_FOTOS = 30


def carregar_cliente(slug: str) -> dict:
    """Lê a pasta clientes/<slug>/ e monta o dicionário completo do cliente."""
    pasta = CLIENTES_DIR / slug
    if not pasta.is_dir():
        raise FileNotFoundError(f"Cliente '{slug}' não encontrado em {pasta}")

    skill_path = pasta / "skill.md"
    skill = skill_path.read_text(encoding="utf-8") if skill_path.exists() else ""
    config = _ler_json(pasta / "config.json", {})
    logos, logo_principal, logo_referencias = _carregar_logos(pasta)

    return {
        "slug": slug,
        "nome": config.get("nome", slug),
        "config": config,
        "tipo": config.get("tipo", "estatico"),
        "skill": skill,
        "catalogo": _ler_json(pasta / "catalogo.json", {}),
        "pautas": _ler_json(pasta / "pautas.json", []),
        "produtos_coringa": _ler_json(pasta / "produtos_coringa.json", []),
        "legenda_padrao": _ler_texto(pasta / "legenda.md"),
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
            p for p in pasta_logo.glob("*") if p.suffix.lower() in EXTENSOES_LOGO
        )

    for ext in EXTENSOES_LOGO:
        logo_raiz = pasta / f"logo{ext}"
        if logo_raiz.exists() and logo_raiz not in arquivos_logo:
            arquivos_logo.append(logo_raiz)

    logos = {p.name: p for p in arquivos_logo}
    logo_principal = arquivos_logo[0] if arquivos_logo else None
    logo_referencias = arquivos_logo

    return logos, logo_principal, logo_referencias


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
    if not caminho.exists():
        return ""
    return caminho.read_text(encoding="utf-8")


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


def tipo_cliente(cliente: dict) -> str:
    tipo = cliente.get("config", {}).get("tipo")
    if tipo:
        return tipo
    if cliente.get("fotos"):
        return "fotos"
    if cliente.get("referencias"):
        return "estatico"
    return "produto"
