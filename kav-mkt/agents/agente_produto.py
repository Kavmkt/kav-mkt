"""Agente de Produto: busca informações e foto de um produto específico do catálogo do
cliente na Shopee, para ilustrar a pauta gerada pelo Agente de Pauta.

COMO FUNCIONA A BUSCA NA SHOPEE NESTA FASE
-------------------------------------------
A Shopee não pode ser navegada de forma automática e confiável por um servidor comum
(renderiza via JavaScript e tem proteção anti-bot). Por isso o agente é dividido em
camadas, na ordem em que são tentadas:

  1. Camada manual (`produto_manual`): quando você já sabe qual produto quer usar,
     informe nome/foto/link — na versão web isso é um formulário simples na tela; ao
     rodar localmente via CLI, também é possível fornecer esses dados através do arquivo
     output/<cliente>/<data>/produto_pesquisado.json (útil se um dia isso for
     preenchido com ajuda de navegação assistida, ex: Claude in Chrome).
  2. Camada automática best-effort: uma tentativa de requisição HTTP simples à loja.
     Na prática isso tende a falhar, pois a Shopee renderiza a listagem via JavaScript e
     tem proteção anti-bot — é esperado, e por isso existe o Plano B abaixo.

PLANO B (obrigatório, sempre ativo)
------------------------------------
Se nenhuma das camadas acima funcionar (captcha, layout mudou, sessão expirada, produto
não encontrado, etc.), o agente:
  a) Registra a falha em logs/<cliente>/falhas_produto.log com data, motivo e tentativas.
  b) Usa um "produto coringa" da skill do cliente como alternativa.
  c) Sinaliza claramente no retorno (`fallback_usado=True` + `aviso`) que o produto usado
     é um fallback, não o produto pesquisado originalmente.
  d) Nunca lança exceção que travaria o orchestrator — o fluxo sempre segue adiante.
"""
import json
import logging
from datetime import date, datetime
from pathlib import Path
from typing import Optional

import requests

BASE_DIR = Path(__file__).resolve().parent.parent

# URL base da loja de cada cliente na Shopee.
URLS_LOJA = {
    "ponto-car": "https://shopee.com.br/pontocarborrachas",
}


def _logger_falhas(cliente: str) -> logging.Logger:
    log_dir = BASE_DIR / "logs" / cliente
    log_dir.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger(f"falhas_produto.{cliente}")
    if not logger.handlers:
        handler = logging.FileHandler(log_dir / "falhas_produto.log", encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s | %(message)s"))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


def _tentar_arquivo_assistido(cliente: str, data_execucao: str) -> Optional[dict]:
    """Camada 1: produto já pesquisado manualmente (ou via Claude in Chrome)."""
    caminho = BASE_DIR / "output" / cliente / data_execucao / "produto_pesquisado.json"
    if not caminho.exists():
        return None
    try:
        dados = json.loads(caminho.read_text(encoding="utf-8"))
        if dados.get("nome"):
            return dados
    except (json.JSONDecodeError, OSError):
        pass
    return None


def _tentar_scraping_direto(url_loja: str) -> Optional[dict]:
    """Camada 2: tentativa best-effort via HTTP simples (sem JS). Tende a falhar na Shopee."""
    try:
        resp = requests.get(url_loja, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
    except requests.RequestException:
        return None
    # A listagem de produtos da Shopee é renderizada via JavaScript no client-side;
    # uma requisição HTTP simples não traz o HTML com os dados do produto, então não há
    # extração confiável possível aqui. Retorna None de propósito -> cai no Plano B.
    return None


def _ultimos_coringa_usados(cliente: str, limite: int) -> set:
    caminho = BASE_DIR / "data" / cliente / "produtos_usados.json"
    if not caminho.exists():
        return set()
    try:
        historico = json.loads(caminho.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return set()
    recentes = [item.get("nome") for item in historico[-limite:] if item.get("fallback_usado")]
    return set(recentes)


def _produto_coringa(skill: dict, cliente: str) -> dict:
    coringas = skill.get("produtos_coringa") or ["produto coringa não configurado na skill"]
    usados_recentemente = _ultimos_coringa_usados(cliente, limite=len(coringas))
    disponiveis = [c for c in coringas if c not in usados_recentemente] or coringas
    return {
        "nome": disponiveis[0],
        "categoria": None,
        "foto_url": None,
        "url_produto": None,
        "fonte": "fallback_coringa",
    }


def buscar_produto(
    cliente: str,
    categoria_produto: str,
    skill: dict,
    produto_manual: Optional[dict] = None,
    data_execucao: Optional[str] = None,
) -> dict:
    """Busca um produto do catálogo do cliente na Shopee, com fallback automático.

    Args:
        produto_manual: quando informado (ex: vindo de um formulário na interface web,
            preenchido por alguém que olhou a loja manualmente), tem prioridade sobre
            qualquer outra camada — deve conter ao menos a chave "nome".
        data_execucao: usado apenas pela camada de arquivo assistido (fluxo local via
            Claude in Chrome); não é necessário na versão web.

    Retorna um dicionário com, no mínimo: nome, categoria, foto_url, url_produto, fonte,
    fallback_usado (bool) e, quando houve fallback, aviso (str).
    """
    if produto_manual and produto_manual.get("nome"):
        produto = dict(produto_manual)
        produto.setdefault("categoria", categoria_produto)
        produto.setdefault("foto_url", None)
        produto.setdefault("url_produto", None)
        produto["fonte"] = "manual"
        produto["fallback_usado"] = False
        return produto

    data_execucao = data_execucao or date.today().isoformat()
    logger = _logger_falhas(cliente)
    url_loja = URLS_LOJA.get(cliente)
    tentativas = []

    produto = _tentar_arquivo_assistido(cliente, data_execucao)
    if produto:
        produto.setdefault("fonte", "claude_in_chrome")
        produto["fallback_usado"] = False
        return produto
    tentativas.append("arquivo assistido (produto_pesquisado.json) não encontrado ou inválido")

    if url_loja:
        produto = _tentar_scraping_direto(url_loja)
        if produto:
            produto["fallback_usado"] = False
            return produto
        tentativas.append(f"scraping direto de {url_loja} não retornou dado confiável (esperado: página é JS)")
    else:
        tentativas.append(f"nenhuma URL de loja configurada em URLS_LOJA para o cliente '{cliente}'")

    motivo = (
        f"Não foi possível obter produto da categoria '{categoria_produto}' na Shopee. "
        f"Tentativas: {'; '.join(tentativas)}."
    )
    logger.info("cliente=%s categoria=%r motivo=%s", cliente, categoria_produto, motivo)

    produto = _produto_coringa(skill, cliente)
    produto["fallback_usado"] = True
    produto["aviso"] = (
        "Produto de FALLBACK (coringa) usado no lugar do produto pesquisado "
        f"('{categoria_produto}'), pois a busca na Shopee falhou. Detalhes em "
        f"logs/{cliente}/falhas_produto.log."
    )
    return produto


def registrar_produto_usado(cliente: str, produto: dict, pauta: dict) -> None:
    """Acrescenta o produto usado nesta execução em data/<cliente>/produtos_usados.json,
    para servir de controle e permitir evitar reuso em execuções futuras."""
    data_dir = BASE_DIR / "data" / cliente
    data_dir.mkdir(parents=True, exist_ok=True)
    caminho = data_dir / "produtos_usados.json"

    historico = []
    if caminho.exists():
        try:
            historico = json.loads(caminho.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            historico = []

    historico.append(
        {
            "data": datetime.now().isoformat(timespec="seconds"),
            "tema_pauta": pauta.get("tema"),
            **produto,
        }
    )
    caminho.write_text(json.dumps(historico, ensure_ascii=False, indent=2), encoding="utf-8")
