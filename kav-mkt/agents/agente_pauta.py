"""Agente de Pauta: gera o tema/pauta de conteúdo do dia para um cliente, seguindo sua
skill de marca (tom de voz, público, regras do que pode e não pode).

Este é o primeiro agente da esteira (Pauta -> Produto -> Design). A função `gerar_pauta`
já recebe um parâmetro opcional `historico`, pensado para receber futuramente um resumo
de posts anteriores do cliente (vindo de um arquivo ou de uma API de histórico), sem
precisar reescrever este agente. Nesta fase o parâmetro simplesmente não é usado se
omitido.
"""
import random
from datetime import date
from typing import Optional

from utils.openai_client import chamar_ia, extrair_json

# Ângulos de conteúdo para variar o formato da pauta e evitar respostas genéricas
# repetidas. A cada execução, alguns são sorteados como inspiração — o modelo pode
# combinar, adaptar ou até fugir deles se tiver uma ideia melhor.
FORMATOS = [
    "Mito vs. Verdade sobre cuidar do carro",
    "Antes e depois de uma peça gasta trocada pela nova",
    "\"Você sabia que...\" — dica rápida e prática",
    "Storytelling de um perrengue comum de quem tem carro popular",
    "Humor/meme sobre economizar cuidando do próprio carro",
    "Pergunta direta pro público, pra puxar comentário",
    "Bastidores do dia a dia da loja",
    "Comparação de custo: resolver sozinho vs. pagar oficina",
    "Alerta de manutenção sazonal (chuva, calor, viagem, fim de ano)",
    "Depoimento representativo de um cliente satisfeito",
    "Curiosidade / fun fact sobre carro popular",
    "Post de urgência/promoção com prazo curto",
]

SYSTEM_PROMPT = """Você é o Agente de Pauta da Kav (@kav.mkt), uma operação de marketing digital.
Sua função é gerar UMA pauta de conteúdo por execução para o cliente descrito abaixo,
seguindo estritamente as diretrizes de marca (tom de voz, público, regras do que pode e
não pode dizer).

DIRETRIZES DE MARCA DO CLIENTE:
{skill}

Para não cair no óbvio, aqui vão alguns ângulos de inspiração (use um deles, combine
mais de um, ou proponha algo diferente se tiver uma ideia melhor — o importante é fugir
de frases genéricas tipo "cuide bem do seu carro"):
{formatos}

Seja específico e concreto: em vez de um conselho genérico, ancore a ideia numa situação
real do dia a dia do público (classe C/D, dono de carro popular 2000-2015). A descrição
deve ler como o rascunho de um post de verdade, não como um resumo de briefing.

Responda APENAS com um objeto JSON, sem nenhum texto antes ou depois, no formato:
{{
  "tema": "string curta com o tema/gancho do post",
  "objetivo": "engajamento | venda | educativo | institucional",
  "formato": "qual ângulo/formato foi usado (livre, pode citar um da lista ou descrever o seu)",
  "descricao": "4-6 frases desenvolvendo a ideia com uma situação concreta, não genérica",
  "legenda_sugerida": "rascunho de legenda pronta pra publicar, no tom de voz do cliente, com pelo menos 3-4 frases",
  "requer_produto_especifico": true ou false,
  "categoria_produto": "categoria ou nome do produto necessário, ou null se requer_produto_especifico for false",
  "hashtags": ["#exemplo1", "#exemplo2", "#exemplo3"]
}}
"""


def gerar_pauta(skill: dict, historico: Optional[str] = None) -> dict:
    """Gera a pauta do dia para o cliente.

    Args:
        skill: dicionário retornado por utils.skill_loader.carregar_skill.
        historico: (reservado para uso futuro) resumo de posts anteriores do cliente,
            vindo de um arquivo ou API, usado para evitar repetição de temas. Não
            utilizado nesta fase — deixe None.
    """
    formatos_sorteados = random.sample(FORMATOS, k=4)
    system = SYSTEM_PROMPT.format(
        skill=skill["texto_completo"],
        formatos="\n".join(f"- {f}" for f in formatos_sorteados),
    )
    prompt = f"Data de hoje: {date.today().isoformat()}. Gere a pauta do dia."
    if historico:
        prompt += f"\n\nHistórico de posts recentes do cliente (evite repetir temas):\n{historico}"

    resposta = chamar_ia(system=system, prompt=prompt, max_tokens=900, temperature=0.95, json_mode=True)
    pauta = extrair_json(resposta)
    pauta.setdefault("requer_produto_especifico", False)
    pauta.setdefault("categoria_produto", None)
    return pauta
