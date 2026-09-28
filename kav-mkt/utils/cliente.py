import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
CLIENTES_DIR = BASE_DIR / "clientes"

EXTENSOES_IMAGEM = {".jpg", ".jpeg", ".png", ".webp"}
MAX_FOTOS = 50
MAX_REFERENCIAS = 10


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

    return {
        "slug": slug,
        "nome": config.get("nome") or slug.replace("-", " ").title(),
        "config": config,
        "tipo": config.get("tipo", "estatico"),
        "skill": skill,
        "legenda_padrao": _ler_texto(pasta / "legenda.md"),
        "catalogo": _ler_json(pasta / "catalogo.json", {"produtos": []}),
        "produtos_coringa": _itens_da_secao(skill, "Produtos Coringa"),
        "pautas": _ler_json(pasta / "pautas.json", []),
        "fotos": _carregar_fotos(pasta / "fotos"),
        "referencias": _carregar_referencias(pasta / "referencias"),
        "logos": logos,
        "logo": logo_principal,
        "logo_referencias": logo_referencias,
    }


def _carregar_logos(pasta: Path) -> tuple[dict, Path | None, Path | None]:
    pasta_logos = pasta / "logos"
    if not pasta_logos.exists():
        return {}, None, None

    logos = {}
    for p in pasta_logos.iterdir():
        if p.suffix.lower() in EXTENSOES_IMAGEM:
            logos[p.stem] = p

    logo_principal = (
        logos.get("principal")
        or logos.get("fundo-escuro")
        or logos.get("fundo-claro")
        or next(iter(logos.values()), None)
    )

    logo_referencias = logos.get("referencias") or logo_principal

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


def _itens_da_secao(texto: str, titulo: str) -> list[str]:
    linhas = texto.splitlines()
    coletando = False
    itens = []
    for linha in linhas:
        if linha.startswith("##") and titulo.lower() in linha.lower():
            coletando = True
            continue
        if coletando and linha.startswith("##"):
            break
        if coletando and linha.strip().startswith("-"):
            itens.append(linha.strip().lstrip("-").strip())
    return itens
