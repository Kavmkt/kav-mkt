from __future__ import annotations
"""Gerenciador de Estado do Escritório Virtual da Kav (@kav.mkt).

Registra em tempo real a atividade, status e mensagens de cada agente (avatar/funcionário)
para que o front-end visual (escritório estilo Habbo/isométrico) leia e exiba dinamicamente
o time trabalhando.

Desacoplado por dados: os agentes apenas chamam `atualizar_agente()`, e o front-end lê
o arquivo de estado (localmente ou via branch 'dados' do GitHub).
"""
import base64
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from zoneinfo import ZoneInfo

import requests

BASE_DIR = Path(__file__).resolve().parent.parent
API_GITHUB = "https://api.github.com"
FUSO = ZoneInfo("America/Sao_Paulo")

FUNCIONARIOS_PADRAO = {
    "supervisor": {
        "id": "supervisor",
        "nome": "Augusto",
        "cargo": "Head de Inteligência & Estratégia",
        "departamento": "Diretoria",
        "avatar": "supervisor",
        "status": "alerta",
        "fala_atual": "53 conversas no WhatsApp nos últimos 30 dias. Feed precisa de novos posts urgentes!",
        "atividade_atual": "Supervisionando alinhamento de tráfego pago vs. presença orgânica",
        "historico_atividades": [
            {
                "timestamp": "2026-09-26T21:30:00",
                "atividade": "Alerta emitido: Meta Ads ativo com R$ 260,79 gastos e zero posts no feed há 6 meses.",
                "fala": "Feed parado precisa de atenção imediata.",
            }
        ],
    },
    "metricas": {
        "id": "metricas",
        "nome": "Vicente",
        "cargo": "Analista de Tráfego & Performance",
        "departamento": "Performance",
        "avatar": "metricas",
        "status": "trabalhando",
        "fala_atual": "Meta Ads coletado: 594 cliques, CTR 2,1%, 53 conversas no WhatsApp.",
        "atividade_atual": "Conectado à Graph API do Meta (Conta: CA - N&N Alimentos)",
        "historico_atividades": [
            {
                "timestamp": "2026-09-26T21:25:00",
                "atividade": "Coleta Meta Marketing API: R$ 260,79 gastos em 30 dias.",
                "fala": "Campanhas de WhatsApp Ads ativas.",
            }
        ],
    },
    "copywriter": {
        "id": "copywriter",
        "nome": "Clarice",
        "cargo": "Redatora de Conteúdo & Copywriter",
        "departamento": "Criação",
        "avatar": "copywriter",
        "status": "online",
        "fala_atual": "Padrão de legenda Sabor de Casa carregado. Ganchos prontos!",
        "atividade_atual": "Escrevendo headlines e selos de pratos para o feed",
        "historico_atividades": [
            {
                "timestamp": "2026-09-26T21:10:00",
                "atividade": "Copy gerada: Headline Feijoada Completa com gancho de almoço.",
                "fala": "Copy pronta para revisão.",
            }
        ],
    },
    "designer": {
        "id": "designer",
        "nome": "Joaquim",
        "cargo": "Diretor de Arte & Designer",
        "departamento": "Criação",
        "avatar": "designer",
        "status": "trabalhando",
        "fala_atual": "Compondo headline e selo sobre a foto real do buffet em 1080x1440.",
        "atividade_atual": "Diagramando arte gráfica sobre foto real (sem alterar a comida)",
        "historico_atividades": [
            {
                "timestamp": "2026-09-26T21:05:00",
                "atividade": "Tratamento gráfico aplicado sobre foto real do buffet executivo.",
                "fala": "Arte finalizada em 1080x1440.",
            }
        ],
    },
    "pesquisador": {
        "id": "pesquisador",
        "nome": "Benedito",
        "cargo": "Curador de Acervo & Catálogo",
        "departamento": "Planejamento",
        "avatar": "pesquisador",
        "status": "online",
        "fala_atual": "33 fotos no acervo. Próximo prato sorteado sem repetição em 45 dias.",
        "atividade_atual": "Gerenciando fotos reais de pratos em clientes/nn-restaurante/fotos/",
        "historico_atividades": [
            {
                "timestamp": "2026-09-26T21:00:00",
                "atividade": "Foto selecionada: buffet_saladas_02.jpg (não usada há 50 dias).",
                "fala": "Curadoria do prato concluída.",
            }
        ],
    },
}


def agora() -> datetime:
    return datetime.now(FUSO).replace(tzinfo=None)


def usa_github() -> bool:
    return bool(os.environ.get("GITHUB_TOKEN") and os.environ.get("GITHUB_REPO"))


def _arquivo_local() -> Path:
    return BASE_DIR / "data" / "estado_agentes.json"


def carregar_estado() -> dict:
    estado, _ = _ler()
    if not estado or "funcionarios" not in estado:
        return _inicializar_estado()
    return estado


def atualizar_agente(
    agente_id: str,
    status: str,
    fala: str,
    atividade: str,
    detalhes: Optional[dict] = None,
) -> None:
    estado, sha = _ler()
    if not estado or "funcionarios" not in estado:
        estado = _inicializar_estado()

    funcionarios = estado["funcionarios"]
    if agente_id not in funcionarios:
        funcionarios[agente_id] = {
            "id": agente_id,
            "nome": agente_id.capitalize(),
            "cargo": "Especialista de IA",
            "departamento": "Operações",
            "avatar": agente_id,
            "status": status,
            "fala_atual": fala,
            "atividade_atual": atividade,
            "historico_atividades": [],
        }

    agente = funcionarios[agente_id]
    agente["status"] = status
    agente["fala_atual"] = fala
    agente["atividade_atual"] = atividade
    agente["atualizado_em"] = agora().isoformat(timespec="seconds")

    novo_log = {
        "timestamp": agora().isoformat(timespec="seconds"),
        "atividade": atividade,
        "fala": fala,
    }
    if detalhes:
        novo_log["detalhes"] = detalhes

    historico_agente = agente.get("historico_atividades", [])
    historico_agente.insert(0, novo_log)
    agente["historico_atividades"] = historico_agente[:5]

    estado["ultima_atualizacao"] = agora().isoformat(timespec="seconds")
    _escrever(json.dumps(estado, ensure_ascii=False, indent=2), sha)


def registrar_post_produzido(post: dict, cliente_slug: str) -> None:
    """Registra uma peça recém-produzida no estado do escritório virtual (estado_agentes.json)
    para que apareça imediatamente na gaveta 'Posts & Legendas' do Escritório Virtual e
    atualiza o status e falas dos agentes."""
    try:
        estado, sha = _ler()
        if not estado or "funcionarios" not in estado:
            estado = _inicializar_estado()

        cliente_nome = post.get("cliente") or cliente_slug.replace("-", " ").title()
        estado["cliente_ativo"] = cliente_nome

        data_str = "Hoje · " + agora().strftime("%H:%M")
        prato_nome = "Peça Criativa"
        categoria = "Feed Instagram"
        headline = "NOVO POST"
        selo = "Post Pronto"
        legenda = ""
        imagem_b64 = None

        if "foto" in post:
            foto = post["foto"]
            estrategia = post.get("estrategia")
            prato_nome = foto.get("nome") or getattr(foto.get("arquivo"), "name", "Prato da Casa")
            categoria = foto.get("categoria") or "Almoço Executivo"
            if estrategia:
                # Post de campanha (tráfego pago): usa os campos do Estrategista de
                # Performance em vez dos de copy orgânica.
                headline = estrategia.get("headline_impacto") or prato_nome
                selo = estrategia.get("selo_produto") or "Peça de Campanha"
                legenda = estrategia.get("copy_anuncio", "")
            else:
                copy = post.get("copy", {})
                headline = copy.get("headline_imagem") or prato_nome
                selo = copy.get("selo_produto") or "Prato do Dia"
                legenda = copy.get("legenda", "")
            if post.get("imagem") and post["imagem"].get("imagem_b64"):
                imagem_b64 = post["imagem"]["imagem_b64"]
        elif "produto" in post:
            prod = post["produto"]
            copy = post.get("copy", {})
            prato_nome = prod.get("nome") or "Destaque"
            categoria = prod.get("categoria") or "Oferta"
            headline = copy.get("headline_imagem") or prato_nome
            selo = copy.get("selo_produto") or "Destaque"
            legenda = copy.get("legenda", "")
            if post.get("imagem") and post["imagem"].get("imagem_b64"):
                imagem_b64 = post["imagem"]["imagem_b64"]
        elif "slides" in post:
            pauta = post.get("pauta", {})
            roteiro = post.get("roteiro", {})
            slides = post.get("slides", [])
            prato_nome = pauta.get("tema") or "Carrossel de Conteúdo"
            categoria = "Carrossel Educativo"
            headline = pauta.get("tema") or "Carrossel"
            selo = f"{len(slides)} Páginas"
            legenda = roteiro.get("legenda", "")
            if slides and slides[0].get("imagem_b64"):
                imagem_b64 = slides[0]["imagem_b64"]

        novo_item = {
            "id": f"post-{int(datetime.now().timestamp())}",
            "data": data_str,
            "prato": prato_nome,
            "categoria": categoria,
            "headline": headline,
            "selo": selo,
            "legenda": legenda,
            "imagem_b64": imagem_b64,
            "criadores": "Curadoria: Benedito · Texto: Clarice · Arte: Joaquim",
            "tipo_post": post.get("tipo_post", "organico"),
            "angulo_conversao": (post.get("estrategia") or {}).get("angulo_conversao"),
        }

        producao = estado.get("producao_recente", [])
        producao.insert(0, novo_item)
        estado["producao_recente"] = producao[:10]

        if "funcionarios" in estado:
            f = estado["funcionarios"]
            if "pesquisador" in f:
                f["pesquisador"]["status"] = "online"
                f["pesquisador"]["fala_atual"] = f"Curadoria concluída: '{prato_nome}' selecionado com sucesso!"
                f["pesquisador"]["atividade_atual"] = f"Acervo de {cliente_nome} atualizado."
            if "copywriter" in f:
                f["copywriter"]["status"] = "online"
                f["copywriter"]["fala_atual"] = f"Legenda e headline '{headline}' prontas para publicação!"
                f["copywriter"]["atividade_atual"] = "Copy aprovada no padrão da marca."
            if "designer" in f:
                f["designer"]["status"] = "online"
                f["designer"]["fala_atual"] = "Arte diagramada em 1080x1440 e disponível na gaveta!"
                f["designer"]["atividade_atual"] = "Layout visual 4:5 finalizado."
            if "supervisor" in f:
                f["supervisor"]["status"] = "online"
                f["supervisor"]["fala_atual"] = f"Entrega de {cliente_nome} pronta! Pode copiar a legenda ou baixar a arte."
                f["supervisor"]["atividade_atual"] = "Supervisão de entrega concluída."

        estado["ultima_atualizacao"] = agora().isoformat(timespec="seconds")
        _escrever(json.dumps(estado, ensure_ascii=False, indent=2), sha)
    except Exception as exc:
        print(f"Aviso: não foi possível registrar post no escritório: {exc}")


def _inicializar_estado() -> dict:
    return {
        "agencia": "Kav (@kav.mkt)",
        "versao": "1.0",
        "ultima_atualizacao": agora().isoformat(timespec="seconds"),
        "funcionarios": FUNCIONARIOS_PADRAO.copy(),
        "producao_recente": [],
    }


def _ler() -> tuple:
    if usa_github():
        try:
            return _ler_github()
        except Exception:
            pass
    arquivo = _arquivo_local()
    if not arquivo.exists():
        return {}, None
    try:
        return json.loads(arquivo.read_text(encoding="utf-8")), None
    except Exception:
        return {}, None


def _escrever(conteudo: str, sha: Optional[str]) -> None:
    try:
        arquivo = _arquivo_local()
        arquivo.parent.mkdir(parents=True, exist_ok=True)
        arquivo.write_text(conteudo, encoding="utf-8")
    except Exception:
        pass

    pastas_destino = [
        BASE_DIR / "escritorio-kav",
        BASE_DIR / "data",
    ]
    for p in pastas_destino:
        if p.exists():
            try:
                (p / "estado_agentes.json").write_text(conteudo, encoding="utf-8")
            except Exception:
                pass

    if usa_github():
        try:
            _escrever_github(conteudo, sha)
        except Exception:
            pass


def _config_github() -> tuple:
    return (
        os.environ["GITHUB_TOKEN"],
        os.environ["GITHUB_REPO"],
        os.environ.get("GITHUB_BRANCH_DADOS", "dados"),
    )


def _headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def _ler_github() -> tuple:
    token, repo, branch = _config_github()
    url = f"{API_GITHUB}/repos/{repo}/contents/escritorio/estado_agentes.json"
    resposta = requests.get(url, params={"ref": branch}, headers=_headers(token), timeout=15)
    if resposta.status_code == 404:
        return {}, None
    resposta.raise_for_status()
    dados = resposta.json()
    conteudo_json = json.loads(base64.b64decode(dados["content"]).decode("utf-8"))
    return conteudo_json, dados.get("sha")


def _escrever_github(conteudo: str, sha: Optional[str]) -> None:
    token, repo, branch = _config_github()
    url = f"{API_GITHUB}/repos/{repo}/contents/escritorio/estado_agentes.json"
    corpo = {
        "message": "escritorio: atualiza estado dos agentes",
        "content": base64.b64encode(conteudo.encode("utf-8")).decode("ascii"),
        "branch": branch,
    }
    if sha:
        corpo["sha"] = sha
    requests.put(url, json=corpo, headers=_headers(token), timeout=15)
