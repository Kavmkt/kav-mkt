"""Módulo de utilitários para resolução de clientes da Kav.

Carrega configurações, pautas, histórico, logos e fotos reais dos clientes.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional, Tuple

CLIENTES_DIR = Path(__file__).resolve().parent.parent / "clientes"
EXTENSOES_IMAGEM = {".jpg", ".jpeg", ".png", ".webp"}
MAX_REFERENCIAS = 5
MAX_FOTOS = 20


def carregar_cliente(slug: str) -> dict:
    pasta = CLIENTES_DIR / slug
    if not pasta.exists():
        raise FileNotFoundError(f"Pasta do cliente '{slug}' não encontrada em {pasta}")

    logos, logo_principal, logo_referencias = _carregar_logos(pasta)

    return {
        "slug": slug,
        "pasta": pasta,
        "nome": _ler_json(pasta / "config.json", {}).get("nome", slug),
        "config": _ler_json(pasta / "config.json", {}),
        "skill": _ler_texto(pasta / "skill.md"),
        "legenda_padrao": _ler_texto(pasta / "legenda.md"),
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


def _existente(caminho: Path) -> Optional[Path]:
    return caminho if caminho.exists() else None


def _ler_json(caminho: Path, padrao):
    if not caminho.exists():
        return padrao
    try:
        return json.loads(caminho.read_text(encoding="utf-8"))
    except Exception:
        return padrao


def _ler_texto(caminho: Path, padrao: str = "") -> str:
    if not caminho.exists():
        return padrao
    try:
        return caminho.read_text(encoding="utf-8")
    except Exception:
        return padrao
