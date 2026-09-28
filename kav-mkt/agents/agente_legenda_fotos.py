"""Agente de Legenda (Fotos): a partir da foto/prato escolhido pelo Curador,
escreve a chamada da imagem, o selo do prato e a legenda completa do post,
seguindo rigorosamente as diretrizes da marca (clientes/<slug>/legenda.md).

REGRAS RÍGIDAS DE ALINHAMENTO:
1. Proibido o uso da palavra "executivo" ou "almoço executivo" (preços de R$ 26 a R$ 35).
2. Feijoada é permitida exclusivamente às quartas-feiras e sábados.
3. Coerência total entre a copy e o prato do dia informado.
"""
from __future__ import annotations

import random
from datetime import datetime
from typing import Tuple
from zoneinfo import ZoneInfo

from utils.openai_client import chamar_ia, extrair_json

FUSO_SP = ZoneInfo("America/Sao_Paulo")

DIAS_SEMANA = {
    0: "Segunda-feira",
    1: "Terça-feira",
    2: "Quarta-feira",
    3: "Quinta-feira",
    4: "Sexta-feira",
    5: "Sábado",
    6: "Domingo",
}


def obter_contexto_temporal() -> Tuple[str, str, int]:
    """Retorna o nome do dia em português, a data formatada e o índice do dia (0=segunda)."""
    agora = datetime.now(FUSO_SP)
    dia_idx = agora.weekday()
    nome_dia = DIAS_SEMANA[dia_idx]
    data_formatada = agora.strftime("%d/%m/%Y")
    return nome_dia, data_formatada, dia_idx


GANCHOS_POR_DIA = {
    0: [  # Segunda
        "começar a semana com energia e um almoço farto de verdade",
        "almoço caseiro e reconfortante pra começar a segunda-feira com o pé direito",
        "comida saborosa e sem complicação pra encarar a volta da rotina",
    ],
    1: [  # Terça
        "pausa revigorante no meio do dia de trabalho com tempero de casa",
        "aquele prato farto e suculento pra recarregar as energias na terça-feira",
        "sabor de comida feita na hora que alegra a rotina",
    ],
    2: [  # Quarta
        "metade da semana pede um almoço caprichado e com fartura",
        "aquele tempero caseiro inconfundível que dá água na boca na hora do almoço",
        "almoço rápido, quentinho e com gostinho caseiro",
    ],
    3: [  # Quinta
        "o almoço que você merece pra dar aquele fôlego na reta final da semana",
        "prato cheio e sabor de casa pra quebrar a rotina do trabalho",
        "comida farta e acolhedora no meio do dia",
    ],
    4: [  # Sexta
        "fechar a semana de trabalho com chave de ouro e um almoço especial",
        "sexta-feira com aquele prato caprichado que comemora o fim de semana",
        "almoço de sexta farto, saboroso e com gostinho de recompensa",
    ],
    5: [  # Sábado
        "sábado de folga pra comer bem sem ter trabalho na cozinha",
        "almoço em família com fartura, variedade e muito sabor",
        "reunir quem você gosta em volta de uma mesa caseira no sábado",
    ],
    6: [  # Domingo
        "domingo de descanso e aconchego com comida caseira de verdade",
        "almoço de domingo quentinho pra relaxar com a família",
        "fartura e sabor de almoço de domingo sem sujar panela",
    ],
}

GANCHOS_GERAIS = [
    "fartura e tempero caseiro, de dar água na boca",
    "prato fumegante feito no capricho com ingredientes frescos",
    "praticidade de comer no salão aconchegante ou pedir em casa (raio de 3 km)",
    "cuidado e carinho no preparo, comida feita como em casa",
    "aquele feijão temperado na hora e carne suculenta",
]

SYSTEM_PROMPT = """Você é o redator sênior da Kav (@kav.mkt), responsável pelo conteúdo do Instagram do NN Restaurante.
Sua missão é criar uma headline impactante para a arte e uma legenda extremamente apetitosa (appetite appeal), a partir do prato do dia escolhido: "__NOME_PRATO__".

CONTEXTO TEMPORAL OBRIGATÓRIO:
Hoje é __DIA_SEMANA__, dia __DATA__.

REGRAS RÍGIDAS DE NEGÓCIO E ALINHAMENTO:
1. PROIBIDO USAR A PALAVRA "EXECUTIVO":
   - NUNCA use "executivo", "almoço executivo", "buffet executivo" ou "prato executivo".
   - O restaurante trabalha na faixa acessível de R$ 26 a R$ 35. Use termos como: "Almoço do Dia", "Comida Caseira", "Prato Feito", "Almoço Comercial" ou o próprio nome do prato.
2. REGRA DA FEIJOADA (QUARTAS E SÁBADOS):
   - Feijoada é servida EXCLUSIVAMENTE às quartas-feiras e sábados.
   - Hoje é __DIA_SEMANA__. Se hoje NÃO for quarta ou sábado, é TERMINANTEMENTE PROIBIDO citar feijoada. Fale estritamente do prato do dia informado (__NOME_PRATO__).
3. COERÊNCIA TOTAL COM O PRATO DO DIA:
   - Toda a copy (headline, gancho e descrição) DEVE focar no prato do dia: "__NOME_PRATO__" (__DESCRICAO_PRATO__).

DIRETRIZES DE MARCA DO CLIENTE:
__SKILL__

PADRÃO DE LEGENDA DO CLIENTE:
__PADRAO__

DIRETRIZES DE COPY E HEADLINE:
1. HEADLINE DA IMAGEM (chamada principal sobre a foto):
   - De 2 a 6 palavras, em português, sem pontuação exagerada e sem emojis.
   - Foque no apetite real de __NOME_PRATO__ (ex: para frango ao molho: "Frango ao molho no capricho" ou "Aquele frango ao molho caseiro").
   - NUNCA use clichês vazios ("Sabor de casa", "Comida de verdade").
2. SELO/TAG DO PRATO (opcional):
   - Use uma tag funcional como "Almoço do Dia", "Feito na Hora", ou o nome da receita. NUNCA use "Executivo".
3. LEGENDA DO POST:
   - Estrutura de 3 parágrafos curtos + 4 hashtags locais.
   - Primeiro parágrafo: gancho apetitoso compatível com __DIA_SEMANA__.
   - Segundo parágrafo: destaque para o sabor e os acompanhamentos do prato (__NOME_PRATO__).

Responda APENAS com um objeto JSON, sem markdown ou texto antes/depois:
{
  "headline_imagem": "Chamada apetitosa e específica para __NOME_PRATO__ (2 a 6 palavras)",
  "selo_produto": "Nome curto/categoria funcional (ex: Almoço do Dia) ou null",
  "legenda": "Legenda completa formatada conforme o padrão"
}
"""

PADRAO_AUSENTE = (
    "(sem padrão definido — use: gancho, descrição do prato/ambiente, chamada para "
    "pedir/visitar, hashtags)"
)


def gerar_legenda_foto(foto: dict, cliente: dict) -> dict:
    nome_dia, data_fmt, dia_idx = obter_contexto_temporal()
    ganchos_candidatos = GANCHOS_POR_DIA.get(dia_idx, []) + GANCHOS_GERAIS
    gancho_sugerido = random.choice(ganchos_candidatos)

    nome_prato = foto.get("nome") or (foto["arquivo"].stem if foto.get("arquivo") else "Prato do Dia")
    desc_prato = foto.get("descricao") or ""

    system = (
        SYSTEM_PROMPT.replace("__SKILL__", cliente["skill"])
        .replace("__PADRAO__", cliente["legenda_padrao"] or PADRAO_AUSENTE)
        .replace("__DIA_SEMANA__", nome_dia)
        .replace("__DATA__", data_fmt)
        .replace("__NOME_PRATO__", nome_prato)
        .replace("__DESCRICAO_PRATO__", desc_prato)
    )
    prompt = (
        f"Dia da semana atual: {nome_dia} ({data_fmt})\n"
        f"Prato do dia oficial: {nome_prato}\n"
        f"Dados do prato:\n{_descrever(foto)}\n\n"
        f"Sugestão de ângulo para o gancho: {gancho_sugerido}\n"
        f"Lembre-se: foque no apetite real de '{nome_prato}', NUNCA use a palavra 'executivo' e respeite o dia da semana ({nome_dia})."
    )
    resposta = chamar_ia(system=system, prompt=prompt, max_tokens=900, temperature=0.7, json_mode=True)
    return extrair_json(resposta)


# Alias para retrocompatibilidade no orchestrator
gerar_copy_foto = gerar_legenda_foto


def _descrever(foto: dict) -> str:
    campos = [
        ("Nome/prato", foto.get("nome")),
        ("Categoria", foto.get("categoria")),
        ("Preço", foto.get("preco")),
        ("Descrição", foto.get("descricao")),
    ]
    descricao = "\n".join(f"- {rotulo}: {valor}" for rotulo, valor in campos if valor)
    if descricao:
        return descricao
    if foto.get("arquivo"):
        return f"- Arquivo: {foto['arquivo'].name} (sem metadados cadastrados em fotos.json)"
    return f"- Prato: {foto.get('nome', 'Prato do Dia')}"
