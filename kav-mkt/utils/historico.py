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
    estilo_layout: Optional[str] = None,
    estilo_nome: Optional[str] = None,
    descricao_layout: Optional[str] = None,
    cor_fundo: Optional[str] = None,
    cor_destaque: Optional[str] = None,
    cor_texto: Optional[str] = None,
    posicao_logo: Optional[str] = None,
) -> dict:
    """Registra uma publicação no histórico do cliente com backup inteligente de metadados visuais."""
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
        "estilo_layout": estilo_layout,
        "estilo_nome": estilo_nome,
        "descricao_layout": descricao_layout or copy.get("descricao_layout"),
        "cor_fundo": cor_fundo or "Azul Marinho Noturno Profundo (#001424)",
        "cor_destaque": cor_destaque or "Dourado Kav (#EEB730)",
        "cor_texto": cor_texto or "Branco Puro (#FFFFFF) e Cinza Slate (#94A3B8)",
        "posicao_logo": posicao_logo or "superior-centro",
    }

    dados["posts"].append(registro)
    salvar_historico(slug, dados)
    return registro


def obter_backup_historico_layouts(slug: str, limite: int = 5) -> str:
    """Gera o backup inteligente descritivo dos últimos layouts gerados para alimentar a IA,
    informando cores de fundo, cores de texto, estrutura e composição para garantir que a IA
    não repita o mesmo layout e mantenha o feed do Instagram versátil e dinâmico.
    """
    posts = listar_posts_cliente(slug)
    if not posts:
        return "Nenhum layout anterior registrado. Esta é a primeira publicação da marca."

    ultimos = list(reversed(posts))[:limite]
    linhas = [
        "LISTA DE BACKUP INTELIGENTE DE LAYOUTS RECENTES (PROIBIDO REPETIR O MESMO ESTILO, ESTRUTURA OU PALETA):"
    ]
    for i, p in enumerate(ultimos, 1):
        ref = p.get("referencia") or "ref_padrao.png"
        nome = p.get("estilo_nome") or ref.replace("ref_", "").replace(".png", "").replace("_", " ").title()
        headline = p.get("headline") or "Sem headline"
        desc = p.get("descricao_layout") or "Composição tipográfica sóbria com elementos da marca"
        fundo = p.get("cor_fundo") or "Azul Marinho Noturno (#001424)"
        destaque = p.get("cor_destaque") or "Dourado Kav (#EEB730)"
        texto = p.get("cor_texto") or "Branco Puro (#FFFFFF) e Cinza Slate (#94A3B8)"
        pos_logo = p.get("posicao_logo") or "Área de cabeçalho"

        linhas.append(
            f"{i}. Peça anterior: Arquétipo '{nome}' ({ref})\n"
            f"   - Headline usada: \"{headline}\"\n"
            f"   - Estrutura visual: {desc}\n"
            f"   - Cores aplicadas: Fundo [{fundo}] | Acento [{destaque}] | Textos [{texto}]\n"
            f"   - Posição do Logo: {pos_logo}"
        )

    linhas.append(
        "\nDIRETRIZ OBRIGATÓRIA DE VARIAÇÃO CONTÍNUA NO FEED:\n"
        "- A IA DEVE criar uma peça com composição espacial, disposição de blocos e foco visual TOTALMENTE DIFERENTES das peças listadas acima.\n"
        "- Fonte: STRICTLY Gotham em Sentence Case (sem caixa alta/NO ALL CAPS).\n"
        "- Cores: Usar estritamente as cores nobres da Kav (Azul Marinho #001424 / #001D32 e Dourado #EEB730). PROIBIDO PRETO PURO (#000000).\n"
        "- Alternar elementos de destaque (se o anterior usou card flutuante, use objeto 3D de destaque ou manifesto editorial ou blueprint grid)."
    )
    return "\n".join(linhas)


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
    """Seleciona um layout de referência realizando rodízio contínuo e garantindo que nunca repita
    o mesmo layout de posts recentes.
    """
    referencias = cliente.get("referencias", [])
    if not referencias:
        return None

    slug = cliente.get("slug", "")
    historico_posts = listar_posts_cliente(slug)

    # Coleta as últimas referências usadas em ordem reversa (mais recente primeiro)
    ultimas_usadas = []
    for p in reversed(historico_posts):
        ref = p.get("referencia") or p.get("referencia_layout") or p.get("estilo_layout")
        if ref and ref not in ultimas_usadas:
            ultimas_usadas.append(ref)

    # Prioriza as referências que ainda NÃO foram usadas
    disponiveis = [r for r in referencias if r["arquivo"].name not in ultimas_usadas]

    # Se todas já foram usadas, bloqueia as últimas (N-1) usadas para forçar rotação round-robin
    if not disponiveis:
        bloqueadas = set(ultimas_usadas[: max(1, len(referencias) - 1)])
        disponiveis = [r for r in referencias if r["arquivo"].name not in bloqueadas]

    if not disponiveis:
        disponiveis = referencias

    return random.choice(disponiveis)


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
