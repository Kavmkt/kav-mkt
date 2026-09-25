"""Agente de Legenda (Fotos): a partir da foto escolhida pelo Agente de Repositório de
Fotos, escreve a chamada da imagem, o selo do prato e a legenda completa do post,
seguindo à risca o padrão de legenda do cliente (clientes/<slug>/legenda.md).

Cópia isolada de agents/agente_legenda.py, adaptada para dados de foto (prato/ambiente)
em vez de dados de produto de loja — nenhum cliente de catálogo (ex: ponto-car) passa
por este arquivo, e vice-versa. Isso é intencional: evita que um ajuste feito aqui para
o NN Restaurante afete o fluxo de legenda dos outros clientes, e vice-versa.
"""
import random

from utils.openai_client import chamar_ia, extrair_json

# Sorteado a cada post só para variar o gancho — a estrutura da legenda vem do padrão.
ANGULOS_GANCHO = [
    "fome de fim de tarde / hora do almoço",
    "fartura e tempero caseiro, de dar água na boca",
    "convite pra sextar ou pro fim de semana com comida boa",
    "praticidade de pedir sem sair de casa (entrega própria na região)",
    "cuidado e carinho no preparo, comida feita como em casa",
    "pergunta direta pro público (ex: 'já sabe o que vai comer hoje?')",
    "clima e ocasião do dia (dia de chuva, dia corrido, fim de semana em família)",
]

# Placeholders substituídos com .replace() (e não .format()): o padrão de legenda do
# cliente pode ter chaves {} de exemplo que quebrariam o .format().
SYSTEM_PROMPT = """Você é o redator da Kav (@kav.mkt), uma operação de marketing digital.
Sua função é escrever o texto de UM post do NN Restaurante, a partir da foto real
escolhida do repositório do cliente (um prato, o buffet ou o ambiente da casa).

DIRETRIZES DE MARCA DO CLIENTE:
__SKILL__

PADRÃO DE LEGENDA DO CLIENTE (siga à risca a estrutura, a ordem, os textos fixos, emojis
e hashtags definidos aqui — o que muda de um post para outro é só o conteúdo do
prato/ambiente):
__PADRAO__

Regras:
- Use somente informações que estão nos dados da foto abaixo. Nunca invente ingrediente,
  preço, promoção ou detalhe que não esteja informado.
- Se não houver preço informado, não cite preço na legenda.
- Tom de voz e regras de "pode / não pode" da skill valem para tudo.

Responda APENAS com um objeto JSON, sem texto antes ou depois:
{
  "headline_imagem": "chamada principal da imagem: 2 a 6 palavras, em português, sem emoji, citando o prato ou o diferencial (ex: 'Sabor de casa', 'Feijoada completa')",
  "selo_produto": "nome curto do prato para o selo da imagem, até ~40 caracteres (ex: 'Feijoada completa'), ou null se a foto for de ambiente/equipe sem prato específico",
  "legenda": "legenda completa, pronta pra colar no Instagram, seguindo o padrão"
}
"""

PADRAO_AUSENTE = (
    "(sem padrão definido — use: gancho, descrição do prato/ambiente, chamada para "
    "pedir/visitar, hashtags)"
)


def gerar_legenda_foto(foto: dict, cliente: dict) -> dict:
    system = SYSTEM_PROMPT.replace("__SKILL__", cliente["skill"]).replace(
        "__PADRAO__", cliente["legenda_padrao"] or PADRAO_AUSENTE
    )
    prompt = (
        f"Dados da foto:\n{_descrever(foto)}\n\n"
        f"Ângulo sugerido para o gancho: {random.choice(ANGULOS_GANCHO)}"
    )
    resposta = chamar_ia(system=system, prompt=prompt, max_tokens=900, temperature=0.9, json_mode=True)
    return extrair_json(resposta)


def _descrever(foto: dict) -> str:
    campos = [
        ("Nome/prato", foto.get("nome")),
        ("Categoria", foto.get("categoria")),
        ("Preço", foto.get("preco")),
        ("Descrição", foto.get("descricao")),
    ]
    descricao = "\n".join(f"- {rotulo}: {valor}" for rotulo, valor in campos if valor)
    return descricao or f"- Arquivo: {foto['arquivo'].name} (sem metadados cadastrados em fotos.json)"
