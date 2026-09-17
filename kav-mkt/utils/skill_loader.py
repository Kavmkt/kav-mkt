"""Carrega a skill (diretrizes de marca) de um cliente a partir de /skills/<cliente>.md.

Para adicionar um novo cliente, basta criar um novo arquivo /skills/<slug>.md seguindo
o mesmo formato de seções do ponto-car.md — nenhum código precisa mudar.
"""
import re
from pathlib import Path

SKILLS_DIR = Path(__file__).resolve().parent.parent / "skills"


def listar_clientes() -> list:
    """Lista os slugs de cliente disponíveis (um por arquivo skills/<slug>.md)."""
    return sorted(p.stem for p in SKILLS_DIR.glob("*.md"))


def nome_exibicao(texto_completo: str) -> str:
    """Extrai um nome de exibição a partir do título H1 do markdown da skill."""
    m = re.search(r"^#\s*Skill de Marca\s*—\s*(.+)$", texto_completo, re.MULTILINE)
    return m.group(1).strip() if m else texto_completo.splitlines()[0].lstrip("# ").strip()


def carregar_skill(cliente: str) -> dict:
    caminho = SKILLS_DIR / f"{cliente}.md"
    if not caminho.exists():
        raise FileNotFoundError(
            f"Skill não encontrada para o cliente '{cliente}': {caminho}. "
            f"Crie o arquivo skills/{cliente}.md seguindo o modelo de skills/ponto-car.md."
        )
    texto = caminho.read_text(encoding="utf-8")
    produtos_coringa = re.findall(r"^\s*-\s*(.+)$", _secao(texto, "Produtos Coringa"), re.MULTILINE)
    return {
        "cliente": cliente,
        "texto_completo": texto,
        "produtos_coringa": [p.strip() for p in produtos_coringa if p.strip()],
    }


def _secao(texto: str, titulo: str) -> str:
    padrao = rf"##\s*{re.escape(titulo)}\s*\n(.*?)(?=\n##|\Z)"
    m = re.search(padrao, texto, re.DOTALL | re.IGNORECASE)
    return m.group(1) if m else ""
