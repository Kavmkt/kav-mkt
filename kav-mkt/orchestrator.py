"""Orchestrator do sistema de automação de marketing da Kav (@kav.mkt).

Executa a esteira de agentes para um cliente: Pauta -> Produto (se necessário) -> Design.
Não faz nenhuma postagem em redes sociais — apenas gera e salva os artefatos em
output/<cliente>/<data>/ para revisão e postagem manual.

Uso:
    python orchestrator.py --cliente ponto-car
"""
import argparse
import base64
import json
import logging
from datetime import date
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

from agents.agente_design import gerar_imagem, gerar_prompt_imagem
from agents.agente_produto import buscar_produto, registrar_produto_usado
from agents.agente_pauta import gerar_pauta
from utils.skill_loader import carregar_skill

BASE_DIR = Path(__file__).resolve().parent


def _logger_execucao(cliente: str) -> logging.Logger:
    log_dir = BASE_DIR / "logs" / cliente
    log_dir.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger(f"execucoes.{cliente}")
    if not logger.handlers:
        handler = logging.FileHandler(log_dir / "execucoes.log", encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s | %(message)s"))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


def rodar(
    cliente: str,
    historico: Optional[str] = None,
    gerar_imagem_tambem: bool = True,
    usar_referencias_layout: bool = True,
) -> Path:
    load_dotenv()
    data_execucao = date.today().isoformat()
    pasta_saida = BASE_DIR / "output" / cliente / data_execucao
    pasta_saida.mkdir(parents=True, exist_ok=True)

    logger = _logger_execucao(cliente)
    skill = carregar_skill(cliente)

    if not historico:
        caminho_historico = BASE_DIR / "data" / cliente / "historico_manual.txt"
        if caminho_historico.exists():
            historico = caminho_historico.read_text(encoding="utf-8").strip() or None

    print(f"[1/3] Agente de Pauta ({cliente})...")
    pauta = gerar_pauta(skill, historico=historico)
    (pasta_saida / "pauta.json").write_text(
        json.dumps(pauta, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    logger.info(
        "Pauta gerada: tema=%r requer_produto=%s",
        pauta.get("tema"),
        pauta.get("requer_produto_especifico"),
    )

    produto = None
    if pauta.get("requer_produto_especifico"):
        print(f"[2/3] Agente de Produto (categoria: {pauta.get('categoria_produto')})...")
        produto = buscar_produto(
            cliente=cliente,
            categoria_produto=pauta.get("categoria_produto") or "não especificada",
            skill=skill,
            data_execucao=data_execucao,
        )
        registrar_produto_usado(cliente, produto, pauta)
        (pasta_saida / "produto.json").write_text(
            json.dumps(produto, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        if produto.get("fallback_usado"):
            print(f"  ⚠️  {produto.get('aviso')}")
            logger.info("Produto: FALLBACK usado (%r). Ver falhas_produto.log.", produto.get("nome"))
        else:
            print(f"  Produto encontrado: {produto.get('nome')} (fonte: {produto.get('fonte')})")
            logger.info("Produto encontrado via %r: %s", produto.get("fonte"), produto.get("nome"))
    else:
        print("[2/3] Agente de Produto: pulado (pauta não requer produto específico).")

    print("[3/3] Agente de Design...")
    prompt_imagem = gerar_prompt_imagem(pauta, produto, skill)
    (pasta_saida / "prompt_imagem.txt").write_text(prompt_imagem, encoding="utf-8")
    logger.info("Brief de imagem gerado (%d caracteres).", len(prompt_imagem))

    imagem_gerada = False
    if gerar_imagem_tambem:
        try:
            resultado_imagem = gerar_imagem(prompt_imagem, skill, produto, usar_referencias_layout)
            if resultado_imagem.get("imagem_b64"):
                (pasta_saida / "imagem.png").write_bytes(base64.b64decode(resultado_imagem["imagem_b64"]))
                imagem_gerada = True
                print(f"  Imagem salva em: {pasta_saida / 'imagem.png'}")
            logger.info("Imagem gerada via %s.", resultado_imagem.get("modelo"))
        except Exception as exc:  # noqa: BLE001 — não deve travar o fluxo
            print(f"  ⚠️  Não foi possível gerar a imagem: {exc}")
            logger.info("Falha ao gerar imagem: %s", exc)

    resumo = _montar_resumo(cliente, pauta, produto, prompt_imagem, imagem_gerada)
    (pasta_saida / "resumo.md").write_text(resumo, encoding="utf-8")

    print(f"\nConcluído. Resultados em: {pasta_saida}")
    return pasta_saida


def _montar_resumo(
    cliente: str, pauta: dict, produto: Optional[dict], prompt_imagem: str, imagem_gerada: bool
) -> str:
    linhas = [
        f"# Resumo da execução — {cliente} ({date.today().isoformat()})",
        "",
        "## Pauta",
        f"- **Tema:** {pauta.get('tema')}",
        f"- **Formato:** {pauta.get('formato', '—')}",
        f"- **Objetivo:** {pauta.get('objetivo')}",
        f"- **Descrição:** {pauta.get('descricao')}",
        f"- **Legenda sugerida:** {pauta.get('legenda_sugerida')}",
        f"- **Hashtags:** {' '.join(pauta.get('hashtags', []))}",
        "",
    ]
    if produto:
        linhas += [
            "## Produto",
            f"- **Nome:** {produto.get('nome')}",
            f"- **Fonte:** {produto.get('fonte')}",
        ]
        if produto.get("fallback_usado"):
            linhas.append(f"- **⚠️ ATENÇÃO:** {produto.get('aviso')}")
        linhas.append("")
    linhas += [
        "## Brief de imagem (Key Visual)",
        "```",
        prompt_imagem,
        "```",
        f"Imagem gerada: {'sim (ver imagem.png)' if imagem_gerada else 'não'}",
        "",
        "> Nenhuma postagem foi feita automaticamente. Revise o material acima e publique manualmente.",
    ]
    return "\n".join(linhas)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Orchestrator de automação de marketing — Kav")
    parser.add_argument("--cliente", required=True, help="Slug do cliente (ex: ponto-car)")
    parser.add_argument(
        "--historico",
        default=None,
        help="(opcional, reservado para uso futuro) resumo de posts anteriores do cliente",
    )
    parser.add_argument(
        "--sem-imagem",
        action="store_true",
        help="Só gera o texto (pauta/brief), pula a chamada de geração de imagem (economiza crédito).",
    )
    parser.add_argument(
        "--sem-referencia-layout",
        action="store_true",
        help="Não usa as últimas imagens geradas como referência de estilo/layout para esta execução.",
    )
    args = parser.parse_args()
    rodar(
        cliente=args.cliente,
        historico=args.historico,
        gerar_imagem_tambem=not args.sem_imagem,
        usar_referencias_layout=not args.sem_referencia_layout,
    )
