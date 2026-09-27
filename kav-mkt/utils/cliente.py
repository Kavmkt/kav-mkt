"""Carrega a pasta de um cliente (clientes/<slug>/) e devolve um dict padronizado com
todas as informações necessárias para os agentes trabalharem."""
from pathlib import Path
import json

CLIENTES_DIR = Path(__file__).resolve().parent.parent / "clientes"
EXTENSOES_IMAGEM = {".png", ".jpg", ".jpeg", ".webp"}
MAX_REFERENCIAS = 10
MAX_FOTOS = 500


def listar_clientes() -> list:
    """Lista os slugs dos clientes disponíveis na pasta clientes/."""
    if not CLIENTES_DIR.exists():
        return []
    return sorted(
        p.name for p in CLIENTES_DIR.iterdir()
        if p.is_dir() and not p.name.startswith(".") and (p / "skill.md").exists()
    )


def carregar_cliente(slug: str) -> dict:
    pasta = CLIENTES_DIR / slug
    if not pasta.exists():
        raise FileNotFoundError(f"Pasta do cliente não encontrada: {pasta}")
    caminho_skill = pasta / "skill.md"
    if not caminho_skill.exists():
        raise FileNotFoundError(
            f"Arquivo skill.md não encontrado para o cliente '{slug}'. "
            f"Crie {caminho_skill} (veja clientes/README.md)."
        )
    skill = caminho_skill.read_text(encoding="utf-8")
    config = _ler_json(pasta / "config.json", {})
    logo_generico = _existente(pasta / "logo.png")
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
        "logo_referencias": _carregar_logos(pasta / "logo"),
        # Versão do logo por cor de fundo; logo.png serve de reserva para as duas.
        "logos": {
            "fundo-escuro": _existente(pasta / "logo-fundo-escuro.png") or logo_generico,
            "fundo-claro": _existente(pasta / "logo-fundo-claro.png") or logo_generico,
        },
    }


def _carregar_referencias(pasta: Path) -> list:
    """Lista de {"arquivo", "logo_posicao", "logo_versao"} — os dois últimos vêm de
    referencias.json (onde o logo fica em cada layout) e podem faltar."""
    metadados = _ler_json(pasta / "referencias.json", {})
    arquivos = sorted(p for p in pasta.glob("*") if p.suffix.lower() in EXTENSOES_IMAGEM)[:MAX_REFERENCIAS]
    return [{**metadados.get(p.name, {}), "arquivo": p} for p in arquivos]


def _carregar_fotos(pasta: Path) -> list:
    """Lista de {"arquivo", "categoria", "nome", "descricao", "preco", ...} do
    repositório de fotos reais do cliente (clientes/<slug>/fotos/)."""
    if not pasta.exists():
        return []
    metadados = _ler_json(pasta / "fotos.json", {})
    arquivos = sorted(p for p in pasta.glob("*") if p.suffix.lower() in EXTENSOES_IMAGEM)[:MAX_FOTOS]
    return [{**metadados.get(p.name, {}), "arquivo": p} for p in arquivos]


def _carregar_logos(pasta: Path) -> list:
    """Carrega as imagens de referência da marca/logotipo na pasta clientes/<slug>/logo/
    para serem enviadas como referência visual direta à IA."""
    if not pasta.exists():
        return []
    return sorted(p for p in pasta.glob("*") if p.suffix.lower() in EXTENSOES_IMAGEM)


def _ler_json(caminho: Path, padrao: dict) -> dict:
    if not caminho.exists():
        return padrao
    try:
        return json.loads(caminho.read_text(encoding="utf-8"))
    except Exception:
        return padrao


def _ler_texto(caminho: Path) -> str:
    if not caminho.exists():
        return ""
    return caminho.read_text(encoding="utf-8")


def _existente(caminho: Path) -> Path | None:
    return caminho if caminho.exists() else None


def _itens_da_secao(texto: str, titulo_secao: str) -> list:
    linhas = texto.splitlines()
    itens = []
    dentro = False
    for linha in linhas:
        if linha.startswith("## ") and titulo_secao.lower() in linha.lower():
            dentro = True
            continue
        if dentro and linha.startswith("## "):
            break
        if dentro and linha.strip().startswith("- "):
            itens.append(linha.strip()[2:].strip())
    return itens
