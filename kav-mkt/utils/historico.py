"""Módulo de Persistência e Anti-Repetição Histórica.

Garante que nenhuma pauta ou layout seja repetido dentro da janela de 120 dias (4 meses),
e alterna de forma inteligente entre temas escuros e temas claros invertidos para
manter o feed do Instagram diversificado e vibrante.
"""
from datetime import datetime, timedelta
import json
from pathlib import Path
import random
from typing import Optional

BASE_DIR = Path(__file__).resolve().parent.parent
CLIENTES_DIR = BASE_DIR / "clientes"

# Janela padrão solicitada pelo usuário: 120 dias (4 meses)
JANELA_PADRAO_DIAS = 120


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
    tema_fundo: Optional[str] = None,
) -> dict:
    """Registra uma publicação no histórico do cliente com backup de metadados visuais por 120 dias."""
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
        "tema_fundo": tema_fundo or ("claro" if "claro" in (estilo_layout or "") or "Branco" in (cor_fundo or "") else "escuro"),
        "descricao_layout": descricao_layout or copy.get("descricao_layout"),
        "cor_fundo": cor_fundo or "Azul Marinho Noturno Profundo (#001424)",
        "cor_destaque": cor_destaque or "Dourado Kav (#EEB730)",
        "cor_texto": cor_texto or "Branco Puro (#FFFFFF) e Cinza Slate (#94A3B8)",
        "posicao_logo": posicao_logo or "superior-centro",
    }

    dados["posts"].append(registro)
    salvar_historico(slug, dados)
    return registro


def obter_backup_historico_layouts(slug: str, limite: int = 6) -> str:
    """Gera o backup inteligente descritivo dos últimos layouts gerados nos últimos 120 dias (4 meses).
    Informa cores de fundo (escuro vs claro), cores de texto, estrutura e composição para garantir
    que a IA alterne temas, não repita layouts e mantenha o feed do Instagram dinâmico e elegante.
    """
    posts = listar_posts_cliente(slug)
    if not posts:
        return "Nenhum layout anterior registrado nos últimos 120 dias. Esta é a primeira publicação da marca."

    limite_dt = datetime.now() - timedelta(days=JANELA_PADRAO_DIAS)
    posts_validos = []
    for p in reversed(posts):
        data_str = p.get("data")
        if data_str:
            try:
                dt = datetime.fromisoformat(data_str)
                if dt < limite_dt:
                    continue
            except ValueError:
                pass
        posts_validos.append(p)

    if not posts_validos:
        posts_validos = list(reversed(posts))[:limite]
    else:
        posts_validos = posts_validos[:limite]

    ultimo_tema = posts_validos[0].get("tema_fundo", "escuro") if posts_validos else "escuro"
    tema_sugerido = "claro (Branco com degradê para cinza-azulado super claro)" if ultimo_tema == "escuro" else "escuro (Azul Marinho Noturno #001424)"

    linhas = [
        "HISTÓRICO DE PUBLICAÇÕES DOS ÚLTIMOS 120 DIAS (4 MESES) — PROIBIDO REPETIR ESTES TEMAS OU LAYOUTS:",
        f"Aviso de Alternância de Feed: O último post usou tema {ultimo_tema.upper()}. Para este novo post, priorize tema {tema_sugerido.upper()} para evitar que tudo saia monocromático no feed."
    ]

    for i, p in enumerate(posts_validos, 1):
        ref = p.get("referencia") or "ref_padrao.png"
        nome = p.get("estilo_nome") or ref.replace("ref_", "").replace(".png", "").replace("_", " ").title()
        headline = p.get("headline") or "Sem headline"
        desc = p.get("descricao_layout") or "Composição tipográfica sóbria com elementos da marca"
        fundo = p.get("cor_fundo") or "Azul Marinho Noturno (#001424)"
        destaque = p.get("cor_destaque") or "Dourado Kav (#EEB730)"
        texto = p.get("cor_texto") or "Branco Puro (#FFFFFF)"
        pos_logo = p.get("posicao_logo") or "topo-centro"
        tema = p.get("tema_fundo", "escuro")

        linhas.append(
            f"{i}. Peça recente ({tema}): Arquétipo '{nome}' ({ref})\n"
            f"   - Headline: \"{headline}\"\n"
            f"   - Estrutura: {desc}\n"
            f"   - Cores: Fundo [{fundo}] | Destaque [{destaque}] | Texto [{texto}]\n"
            f"   - Posição do Logo: {pos_logo}"
        )

    linhas.append(
        "\nDIRETRIZES OBRIGATÓRIAS DE VARIAÇÃO CONTÍNUA (JANELA DE 4 MESES):\n"
        "- NÃO REPETIR a mesma headline, estrutura visual ou disposição de blocos das peças acima.\n"
        "- FONTE: STRICTLY Gotham em Sentence Case (primeira letra maiúscula e o resto em minúsculas normais, NO ALL CAPS).\n"
        "- TAMANHO DA FONTE CONTIDO (ESTILO FOCUS): Proporção cautelosa, elegante e moderada (48px a 54px equivalentes). O texto deve ocupar cerca de 50% a 65% da largura da tela, com amplas margens de respiro nas laterais. NUNCA faça letras monstruosas que gritam ou estouram a tela!\n"
        "- INTEGRIDADE DO LOGO KAV: O logo 'KAV' DEVE manter proporção 1:1 rigorosa, SEM ESTICAR, SEM ACHATAR, SEM DISTORÇÃO e SEM ERROS de digitação ('KAV'). Margem de respiro mínima de 60-80px.\n"
        "- ALTERNÂNCIA DE TEMA: Se o post anterior for escuro, use fundo CLARO INVERTIDO (Branco #FFFFFF no topo em degradê suave para cinza-azulado super claro #EBF1F6 na base, com texto em Azul Marinho #001424 e destaque Dourado #EEB730). Se for claro, use escuro (#001424)."
    )
    return "\n".join(linhas)


def listar_posts_cliente(slug: str) -> list[dict]:
    return carregar_historico(slug).get("posts", [])


def escolher_pauta_sem_repetir(cliente: dict, pautas: list[dict]) -> dict:
    """Seleciona uma pauta da lista excluindo aquelas usadas dentro da janela de 120 dias (4 meses)."""
    if not pautas:
        raise ValueError(f"Nenhuma pauta cadastrada para o cliente {cliente.get('slug')}.")

    slug = cliente.get("slug", "")
    config = cliente.get("config", {})
    dias_limite = int(config.get("dias_sem_repetir_pauta", JANELA_PADRAO_DIAS))
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
    o mesmo layout de posts dentro da janela de 120 dias (4 meses), alternando entre temas escuros e claros.
    """
    referencias = cliente.get("referencias", [])
    if not referencias:
        return None

    slug = cliente.get("slug", "")
    config = cliente.get("config", {})
    dias_limite = int(config.get("dias_sem_repetir_layout", JANELA_PADRAO_DIAS))
    limite_dt = datetime.now() - timedelta(days=dias_limite)

    historico_posts = listar_posts_cliente(slug)

    ultimo_tema = "escuro"
    if historico_posts:
        ultimo_post = historico_posts[-1]
        ultimo_tema = ultimo_post.get("tema_fundo", "escuro")

    tema_alvo = "claro" if ultimo_tema == "escuro" else "escuro"

    usadas_no_periodo = []
    for p in reversed(historico_posts):
        data_str = p.get("data")
        if data_str:
            try:
                dt = datetime.fromisoformat(data_str)
                if dt < limite_dt:
                    continue
            except ValueError:
                pass
        ref = p.get("referencia") or p.get("referencia_layout") or p.get("estilo_layout")
        if ref and ref not in usadas_no_periodo:
            usadas_no_periodo.append(ref)

    disponiveis = [r for r in referencias if r["arquivo"].name not in usadas_no_periodo]

    if not disponiveis:
        bloqueadas = set(usadas_no_periodo[: max(1, len(referencias) - 1)])
        disponiveis = [r for r in referencias if r["arquivo"].name not in bloqueadas]

    if not disponiveis:
        disponiveis = referencias

    preferidas_tema = [
        r for r in disponiveis
        if r.get("tema") == tema_alvo or (tema_alvo == "claro" and "claro" in r["arquivo"].name) or (tema_alvo == "escuro" and "claro" not in r["arquivo"].name)
    ]
    if preferidas_tema:
        return random.choice(preferidas_tema)

    return random.choice(disponiveis)


def agora() -> datetime:
    return datetime.now()


def carregar(slug: str) -> list:
    return listar_posts_cliente(slug)


def usa_github() -> bool:
    return False


def ultimo_uso_por_produto(slug: str) -> dict:
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
    dados = carregar_historico(slug)
    novo = {"data": datetime.now().isoformat(), **registro}
    dados.setdefault("posts", []).append(novo)
    salvar_historico(slug, dados)
    return novo
