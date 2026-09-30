"""Agente de Pauta Dinâmica com IA.

Gera temas e pautas estratégicas sob demanda focadas em Tráfego Pago Local para PMEs
e Marketing Descomplicado, com mecanismo rigoroso de anti-repetição baseado no histórico
dos últimos 120 dias (4 meses).
"""
from datetime import datetime, timedelta
import json
from typing import Optional

from utils import historico
from utils.openai_client import chamar_ia, extrair_json

SYSTEM_GERADOR_PAUTA = """Você é o Estrategista-Chefe de Conteúdo e Pauta da Kav (@kav.mkt).
Sua missão é criar UMA pauta inédita, altamente atrativa e magnética para um post estático de Instagram da Kav.

PÚBLICO-ALVO:
- Donos de pequenas e médias empresas (restaurantes, comércios locais, clínicas, prestadores de serviços).
- Dores: Falta de clientes no balcão/WhatsApp, frustração com 'botão impulsionar', agências lentas, medo de termos difíceis de marketing.

PILARES TEMÁTICOS DA KAV:
1. Tráfego Pago Local na Prática: Como anunciar no raio de 3km a 10km para atrair quem realmente compra hoje.
2. Marketing Sem Complicação: Explicar conceitos técnicos (Pixel, CTR, Funil, Remarketing) usando analogias simples do dia a dia.
3. Erros que Drenam o Caixa: Botão impulsionar, WhatsApp sem atendimento rápido, postar dancinha achando que vai vender.
4. Bastidores & Automação com Agentes de IA: Como a Kav usa tecnologia e agentes para entregar resultados com agilidade.
5. Métricas Reais de Resultado: Por que curtida não paga boleto e o foco deve ser custo por mensagem e faturamento.

REGRA ANTI-REPETIÇÃO RIGOROSA (JANELA DE 120 DIAS / 4 MESES):
É terminantemente PROIBIDO repetir temas, ideias centrais ou headlines presentes no HISTÓRICO DE PAUTAS DOS ÚLTIMOS 120 DIAS.
Crie um ângulo NOVO, um gancho diferente e uma abordagem prática e surpreendente.

REGRA DE TIPOGRAFIA NA HEADLINE SUGERIDA:
Use SEMPRE Sentence Case (primeira letra maiúscula e o resto em minúsculas normais, ex: 'Você não precisa abaixar o seu preço', 'Improviso não constrói empresa'). PROIBIDO CAIXA ALTA / ALL CAPS!

FORMATO DE RESPOSTA:
Responda APENAS com um objeto JSON válido, sem texto antes ou depois:
{
  "id": "slug-curto-em-kebab-case",
  "pilar": "Nome do Pilar Temático",
  "tema": "Título claro e objetivo do tema",
  "dor_ou_desejo": "A dor ou desejo exato do empresário de PME",
  "analogia_pratica": "Uma analogia simples do cotidiano para explicar o conceito",
  "headline_sugerida": "Headline afiada em Sentence Case (2 a 6 palavras contidas, primeira maiúscula e resto minúsculas)",
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
    """Recupera os temas e títulos das pautas usadas nos últimos 120 dias (4 meses)."""
    posts = historico.listar_posts_cliente(slug)
    limite_dt = datetime.now() - timedelta(days=120)
    temas = []
    for p in posts:
        data_str = p.get("data")
        if data_str:
            try:
                dt = datetime.fromisoformat(data_str)
                if dt < limite_dt:
                    continue
            except ValueError:
                pass
        tema = p.get("pauta_tema") or p.get("tema") or p.get("headline")
        if tema and str(tema) not in temas:
            temas.append(str(tema))
    return temas


def _gerar_pauta_dinamica_ia(cliente: dict, pautas_anteriores: list[str]) -> dict:
    """Chama a IA para gerar uma pauta nova respeitando a lista de temas dos últimos 120 dias."""
    historico_texto = "\n".join(f"- {t}" for t in pautas_anteriores) if pautas_anteriores else "Nenhum post registrado ainda nos últimos 120 dias."

    prompt = (
        f"HISTÓRICO DE PAUTAS DOS ÚLTIMOS 120 DIAS / 4 MESES (PROIBIDO REPETIR ESTES TEMAS):\n"
        f"{historico_texto}\n\n"
        f"Instrução: Crie agora uma pauta 100% INÉDITA, provocativa e prática para a Kav. "
        f"Foque em tráfego pago local para PMEs ou marketing descomplicado. "
        f"Headline sugerida estritamente em Sentence Case (sem caixa alta). "
        f"Gere um slug id único baseado na data e tema."
    )

    resposta = chamar_ia(system=SYSTEM_GERADOR_PAUTA, prompt=prompt, max_tokens=600, temperature=0.85, json_mode=True)
    dados = extrair_json(resposta)

    if not dados.get("id"):
        dados["id"] = f"pauta-ia-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    return dados


def _escolher_pauta_fallback(cliente: dict, pautas_anteriores: list[str]) -> dict:
    """Fallback: escolhe uma pauta do arquivo pautas.json que ainda não foi usada nos últimos 120 dias."""
    pautas_raw = cliente.get("pautas", [])
    if isinstance(pautas_raw, dict):
        pautas_banco = pautas_raw.get("pautas", [])
    elif isinstance(pautas_raw, list):
        pautas_banco = pautas_raw
    else:
        pautas_banco = []

    if not pautas_banco:
        return {
            "id": "pauta-padrao-local",
            "pilar": "Tráfego Pago Local",
            "tema": "Tráfego pago no raio certo para PMEs",
            "dor_ou_desejo": "Atrair clientes no WhatsApp",
            "analogia_pratica": "Entregar panfleto só na rua certa",
            "headline_sugerida": "Pare de anunciar pra cidade inteira.",
            "subtitulo_apoio": "Seu cliente ideal está a menos de 10 minutos da sua porta.",
            "cta": "Mande um direct para a Kav",
        }

    ids_usados = set(pautas_anteriores)
    for p in pautas_banco:
        if isinstance(p, dict):
            if p.get("id") not in ids_usados and p.get("tema") not in ids_usados:
                return p

    primeira = pautas_banco[0]
    return primeira if isinstance(primeira, dict) else {"id": "pauta-1", "tema": str(primeira)}
