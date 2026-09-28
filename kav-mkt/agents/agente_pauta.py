"""Agente de Pauta Dinâmica com IA.

Gera temas e pautas estratégicas sob demanda focadas em Tráfego Pago Local para PMEs
e Marketing Descomplicado, com mecanismo rigoroso de anti-repetição baseado no histórico recente.
"""
from datetime import datetime
import json
from typing import Optional

from utils import historico
from utils.openai_client import chamar_ia, extrair_json

SYSTEM_GERADOR_PAUTA = """Você é o Estrategista-Chefe de Conteúdo e Pauta da Kav (@kav.mkt).
Sua missão é criar UMA pauta inédita, altamente atrativa e magnética para um post de Instagram da Kav.

PÚBLICO-ALVO:
- Donos de pequenas e médias empresas (restaurantes, comércios locais, clínicas, prestadores de serviços).
- Dores: Falta de clientes no balcão/WhatsApp, frustração com 'botão impulsionar', agências lentas, medo de termos difíceis de marketing.

PILARES TEMÁTICOS DA KAV (escolha o mais adequado ou o solicitado):
1. Tráfego Pago Local na Prática: Como anunciar no raio de 3km a 10km para atrair quem realmente compra hoje.
2. Marketing Sem Complicação: Explicar conceitos técnicos (Pixel, CTR, Funil, Remarketing) usando analogias simples do dia a dia.
3. Erros que Drenam o Caixa: Botão impulsionar, WhatsApp sem atendimento rápido, postar dancinha achando que vai vender.
4. Bastidores & Automação com Agentes de IA: Como a Kav usa tecnologia e agentes para entregar resultados com agilidade.
5. Métricas Reais de Resultado: Por que curtida não paga boleto e o foco deve ser custo por mensagem e faturamento.

REGRA ANTI-REPETIÇÃO RIGOROSA:
É terminantemente PROIBIDO repetir temas, ideias centrais ou headlines presentes no HISTÓRICO DE PAUTAS RECENTES.
Crie um ângulo NOVO, um gancho diferente e uma abordagem prática e surpreendente.

FORMATO DE RESPOSTA:
Responda APENAS com um objeto JSON válido, sem texto antes ou depois:
{
  "id": "slug-curto-em-kebab-case",
  "pilar": "Nome do Pilar Temático",
  "tema": "Título claro e objetivo do tema",
  "dor_ou_desejo": "A dor ou desejo exato do empresário de PME",
  "analogia_pratica": "Uma analogia simples do cotidiano para explicar o conceito",
  "headline_sugerida": "HEADLINE FORTE EM CAIXA ALTA (2 A 6 PALAVRAS)",
  "subtitulo_apoio": "Subtítulo direto de 1 linha sem jargão",
  "cta": "Chamada para ação direta (ex: Mande um direct para a Kav)"
}
"""


def gerar_pauta_kav(cliente: dict, forcar_ia: bool = True) -> dict:
    """Gera uma pauta inédita para a Kav, preferindo IA dinâmica e usando fallback se necessário."""
    slug = cliente.get("slug", "kav")
    pautas_anteriores = _coletar_historico_pautas(slug)

    if forcar_ia:
        try:
            return _gerar_pauta_dinamica_ia(cliente, pautas_anteriores)
        except Exception as exc:
            print(f"[agente_pauta] Aviso: geração dinâmica via IA falhou ({exc}). Usando fallback de pautas.")

    return _escolher_pauta_fallback(cliente, pautas_anteriores)


def _coletar_historico_pautas(slug: str) -> list[str]:
    """Recupera os temas e títulos das últimas pautas já usadas no histórico do cliente."""
    posts = historico.listar_posts_cliente(slug)
    temas = []
    for p in posts[-25:]:
        tema = p.get("pauta_tema") or p.get("tema") or p.get("headline")
        if tema:
            temas.append(str(tema))
    return temas


def _gerar_pauta_dinamica_ia(cliente: dict, pautas_anteriores: list[str]) -> dict:
    """Chama a IA para gerar uma pauta nova respeitando a lista de temas já abordados."""
    historico_texto = "\\n".join(f"- {t}" for t in pautas_anteriores) if pautas_anteriores else "Nenhum post registrado ainda."

    prompt = (
        f"HISTÓRICO DE PAUTAS RECENTES (NÃO REPETIR ESTES TEMAS):\\n"
        f"{historico_texto}\\n\\n"
        f"Instrução: Crie agora uma pauta 100% INÉDITA, provocativa e prática para a Kav. "
        f"Foque em tráfego pago local para PMEs ou marketing descomplicado. "
        f"Gere um slug id único baseado na data e tema."
    )

    resposta = chamar_ia(system=SYSTEM_GERADOR_PAUTA, prompt=prompt, max_tokens=600, temperature=0.85, json_mode=True)
    dados = extrair_json(resposta)

    if not dados.get("id"):
        dados["id"] = f"pauta-ia-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    return dados


def _escolher_pauta_fallback(cliente: dict, pautas_anteriores: list[str]) -> dict:
    """Fallback: escolhe uma pauta do arquivo pautas.json que ainda não foi usada recentemente."""
    pautas_banco = cliente.get("pautas", [])
    if not pautas_banco:
        return {
            "id": "pauta-padrao-local",
            "pilar": "Tráfego Pago Local",
            "tema": "Tráfego pago no raio certo para PMEs",
            "dor_ou_desejo": "Atrair clientes no WhatsApp",
            "analogia_pratica": "Entregar panfleto só na rua certa",
            "headline_sugerida": "PARE DE ANUNCIAR PRA CIDADE INTEIRA",
            "subtitulo_apoio": "Seu cliente ideal está a menos de 10 minutos da sua porta.",
            "cta": "Mande um direct para a Kav",
        }

    ids_usados = set(pautas_anteriores)
    for p in pautas_banco:
        if p.get("id") not in ids_usados and p.get("tema") not in ids_usados:
            return p

    return pautas_banco[0]
