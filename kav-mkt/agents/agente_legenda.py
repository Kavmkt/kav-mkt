"""Agente de Legenda: a partir do produto escolhido pelo Agente de Catálogo, escreve a
chamada da imagem, o selo do produto e a legenda completa do post, seguindo à risca o
padrão de legenda do cliente (clientes/<slug>/legenda.md) e as diretrizes da skill.
"""
import random

from utils.openai_client import chamar_ia, extrair_json

# Sorteado a cada post só para variar o gancho — a estrutura da legenda vem do padrão.
ANGULOS_GANCHO = [
    "um perrengue comum de quem tem carro popular",
    "economia: resolver sem gastar muito",
    "antes e depois: peça gasta vs. peça nova",
    "segurança no dia a dia (chuva, noite, estrada)",
    "visual: deixar o carro com cara de novo",
    "pergunta direta pro público",
    "humor leve de quem cuida do próprio carro",
    "alerta sazonal (chuva, calor, viagem de fim de ano)",
]

# Placeholders substituídos com .replace() (e não .format()): o padrão de legenda do
# cliente pode ter chaves {} de exemplo que quebrariam o .format().
SYSTEM_PROMPT = """Você é o redator da Kav (@kav.mkt), uma operação de marketing digital.
Sua função é escrever o texto de UM post de produto para o cliente abaixo.

DIRETRIZES DE MARCA DO CLIENTE:
__SKILL__

PADRÃO DE LEGENDA DO CLIENTE (siga à risca a estrutura, a ordem, os textos fixos, emojis
e hashtags definidos aqui — o que muda de um post para outro é só o conteúdo do produto):
__PADRAO__

Regras:
- Use somente informações que estão nos dados do produto. Nunca invente compatibilidade
  (modelos/anos), medidas, garantia, frete ou preço.
- Se o padrão pedir preço, use o preço dos dados do produto exatamente como está.
- Tom de voz e regras de "pode / não pode" da skill valem para tudo.

Responda APENAS com um objeto JSON, sem texto antes ou depois:
{
  "headline_imagem": "chamada principal da imagem: 2 a 6 palavras, em português, sem emoji, de preferência citando o carro (ex: 'Seu Gol G2 de cara nova!', 'Sua Fiorino merece o melhor!')",
  "selo_produto": "nome curto do produto + aplicação para o selo da imagem, até ~40 caracteres (ex: 'Retrovisor Gol / Parati G2 (95 a 99)'), ou null se não fizer sentido",
  "legenda": "legenda completa, pronta pra colar no Instagram, seguindo o padrão"
}
"""

PADRAO_AUSENTE = "(sem padrão definido — use: gancho, produto e benefício, chamada para compra, hashtags)"


def gerar_legenda(produto: dict, cliente: dict) -> dict:
    system = SYSTEM_PROMPT.replace("__SKILL__", cliente["skill"]).replace(
        "__PADRAO__", cliente["legenda_padrao"] or PADRAO_AUSENTE
    )
    prompt = (
        f"Dados do produto:\n{_descrever(produto, cliente)}\n\n"
        f"Ângulo sugerido para o gancho: {random.choice(ANGULOS_GANCHO)}"
    )
    resposta = chamar_ia(system=system, prompt=prompt, max_tokens=900, temperature=0.9, json_mode=True)
    return extrair_json(resposta)


def _descrever(produto: dict, cliente: dict) -> str:
    atualizado_em = cliente["catalogo"].get("atualizado_em")
    campos = [
        ("Nome", produto.get("nome")),
        ("Categoria", produto.get("categoria")),
        (f"Preço (capturado em {atualizado_em})", produto.get("preco")),
        ("Vendidos", produto.get("vendidos_texto") or produto.get("vendidos")),
        ("Avaliação", produto.get("avaliacao")),
        ("Descrição do anúncio", (produto.get("descricao") or "")[:1500]),
    ]
    return "\n".join(f"- {rotulo}: {valor}" for rotulo, valor in campos if valor)
