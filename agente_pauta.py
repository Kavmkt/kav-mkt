"""Agente de Pauta: gera o tema/pauta de conteúdo do dia para um cliente, seguindo sua
skill de marca (tom de voz, público, regras do que pode e não pode).

Este é o primeiro agente da esteira (Pauta -> Produto -> Design). A função `gerar_pauta`
já recebe um parâmetro opcional `historico`, pensado para receber futuramente um resumo
de posts anteriores do cliente (vindo de um arquivo ou de uma API de histórico), sem
precisar reescrever este agente. Nesta fase o parâmetro simplesmente não é usado se
omitido.

Para evitar temas repetidos, o agente combina duas fontes de variedade a cada execução:
um ângulo/formato de conteúdo (FORMATOS) e uma sugestão de produto do catálogo
(CATALOGO_PRODUTOS) — ambos sorteados aleatoriamente e oferecidos como inspiração (não
obrigatórios), multiplicando as combinações possíveis entre chamadas.
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

# Catálogo de produtos da Ponto Car — usado como inspiração pra variar o assunto entre
# execuções (o agente tende a girar sempre em torno dos mesmos 2-3 produtos se não
# receber essa lista completa). Ajuste esta lista se o catálogo real mudar.
CATALOGO_PRODUTOS = [
    "Calotas",
    "Tapetes (diversos tipos: carpete, borracha, PVC)",
    "Bandejas organizadoras/porta-objetos",
    "Grade de para-choque com emblema",
    "Grade de para-choque sem emblema",
    "Lanternas",
    "Faróis",
    "Retrovisores",
    "Para-barros (paralamas)",
    "Borracha de porta",
    "Borracha de porta-malas",
    "Palhetas (limpador de para-brisa)",
    "Par de amortecedores",
]

SYSTEM_PROMPT = """Você é o Agente de Pauta da Kav (@kav.mkt), uma operação de marketing digital.
Sua função é gerar UMA pauta de conteúdo por execução para o cliente descrito abaixo,
seguindo estritamente as diretrizes de marca (tom de voz, público, regras do que pode e
não pode dizer).

DIRETRIZES DE MARCA DO CLIENTE:
{skill}

CATÁLOGO DE PRODUTOS DO CLIENTE (varie entre eles ao longo das execuções — não fique
sempre preso aos mesmos 2-3 produtos mais óbvios):
{catalogo}

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
  "headline_imagem": "chamada BEM curta (2 a 5 palavras), em português, para aparecer escrita sobre a imagem do post (ex: 'BORRACHA NOVA, CARRO NOVO'). Maiúsculas ou não, sem emoji. Se não fizer sentido ter uma chamada (ex: post mais institucional/sutil), retorne null.",
  "requer_produto_especifico": true ou false,
  "categoria_produto": "quando true, use um item do catálogo informado acima (ou algo bem próximo); null se requer_produto_especifico for false",
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
        catalogo="\n".join(f"- {p}" for p in CATALOGO_PRODUTOS),
        formatos="\n".join(f"- {f}" for f in formatos_sorteados),
    )
    prompt = f"Data de hoje: {date.today().isoformat()}. Gere a pauta do dia."

    # Sorteia um produto específico como sugestão em ~70% das vezes, pra forçar variedade
    # de assunto entre execuções; nos outros ~30%, pede um ângulo institucional/educativo
    # sem produto, pra não virar sempre um post de venda.
    if random.random() < 0.7:
        produto_sorteado = random.choice(CATALOGO_PRODUTOS)
        prompt += (
            f"\n\nSugestão de produto do catálogo pra inspirar esta pauta específica "
            f"(não é obrigatório usar se não fizer sentido, mas ajuda a variar o assunto "
            f"entre execuções): {produto_sorteado}."
        )
    else:
        prompt += (
            "\n\nPara esta pauta, prefira um ângulo institucional/educativo, sem focar "
            "em um produto específico do catálogo."
        )

    if historico:
        prompt += f"\n\nHistórico de posts recentes do cliente (evite repetir temas):\n{historico}"

    resposta = chamar_ia(system=system, prompt=prompt, max_tokens=900, temperature=0.95, json_mode=True)
    pauta = extrair_json(resposta)
    pauta.setdefault("requer_produto_especifico", False)
    pauta.setdefault("categoria_produto", None)
    return pauta
