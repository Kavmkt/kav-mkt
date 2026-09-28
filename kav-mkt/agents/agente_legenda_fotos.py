"""Agente de Legenda (Fotos): a partir da foto escolhida pelo Agente de Repositório de
Fotos, escreve a chamada da imagem, o selo do prato e a legenda completa do post,
seguindo à risca o padrão de legenda do cliente (clientes/<slug>/legenda.md).

Cópia isolada de agents/agente_legenda.py, adaptada para dados de foto (prato/ambiente)
em vez de dados de produto de loja — nenhum cliente de catálogo (ex: ponto-car) passa
por este arquivo, e vice-versa. Isso é intencional: evita que um ajuste feito aqui para
o NN Restaurante afete o fluxo de legenda dos outros clientes, e vice-versa.
"""
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
        "começar a semana com energia e um prato farto de verdade",
        "refeição caseira e reconfortante pra começar a segunda-feira com o pé direito",
        "comida saborosa e sem complicação pra encarar a volta da rotina",
    ],
    1: [  # Terça
        "pausa revigorante no meio do dia com tempero de casa",
        "aquele prato farto e suculento pra recarregar as energias na terça-feira",
        "sabor de comida feita na hora que alegra a rotina",
    ],
    2: [  # Quarta
        "metade da semana pede uma refeição caprichada e com fartura",
        "aquele tempero caseiro inconfundível que dá água na boca a qualquer hora",
        "comida quentinha, rápida e com gostinho caseiro",
    ],
    3: [  # Quinta
        "a comida que você merece pra dar aquele fôlego na reta final da semana",
        "prato cheio e sabor de casa pra quebrar a rotina do trabalho",
        "comida farta e acolhedora no meio do dia",
    ],
    4: [  # Sexta
        "fechar a semana de trabalho com chave de ouro e um prato especial",
        "sexta-feira com aquele prato caprichado que comemora o fim de semana",
        "refeição de sexta farta, saborosa e com gostinho de recompensa",
    ],
    5: [  # Sábado
        "sábado de folga pra comer bem sem ter trabalho na cozinha",
        "refeição em família com fartura, variedade e muito sabor",
        "reunir quem você gosta em volta de uma mesa caseira no sábado",
    ],
    6: [  # Domingo
        "domingo de descanso e aconchego com comida caseira de verdade",
        "refeição de domingo quentinha pra relaxar com a família",
        "fartura e sabor de domingo sem sujar panela",
    ],
}

GANCHOS_GERAIS = [
    "fartura e tempero caseiro, de dar água na boca",
    "prato fumegante feito no capricho com ingredientes frescos",
    "praticidade de comer no salão aconchegante ou pedir em casa (raio de 3 km)",
    "cuidado e carinho no preparo, comida feita como em casa",
    "aquele feijão temperado na hora e carne suculenta",
]

# Placeholders substituídos com .replace() (e não .format()): o padrão de legenda do
# cliente pode ter chaves {} de exemplo que quebrariam o .format().
SYSTEM_PROMPT = """Você é o redator sênior da Kav (@kav.mkt), responsável pelo conteúdo do Instagram do NN Restaurante.
Sua missão é criar uma headline impactante para a arte e uma legenda extremamente apetitosa (appetite appeal), a partir da foto real do prato/ambiente escolhida.

CONTEXTO TEMPORAL:
Hoje é __DIA_SEMANA__, dia __DATA__.
REGRA TEMPORAL RÍGIDA:
- NUNCA use "Sextou", "quase sexta" ou menções a fim de semana se hoje NÃO for sexta-feira, sábado ou domingo.
- Adapte o gancho rigorosamente ao momento da semana.

DIRETRIZES DE MARCA DO CLIENTE:
__SKILL__

PADRÃO DE LEGENDA DO CLIENTE:
__PADRAO__

DIRETRIZES DE COPY E HEADLINE:
1. HEADLINE DA IMAGEM (chamada principal sobre a foto):
   - Deve ter de 2 a 6 palavras, em português, sem pontuação final exagerada e sem emojis.
   - FUJA DE CLICHÊS GENÉRICOS: NÃO use frases vazias como "Sabor de casa", "Comida de verdade".
   - PROIBIDO USAR "ALMOÇO DO DIA" OU "ALMOÇO" NA HEADLINE DA IMAGEM: Os posts também serão postados à tarde e à noite para alcançar novos públicos. Foque no prato, no sabor autêntico e no capricho.
     Exemplos excelentes:
     * Para bife acebolado: "Bife acebolado suculento no ponto" ou "Aquele bife acebolado no capricho"
     * Para feijoada: "Feijoada farta e quentinha" ou "A feijoada mais pedida da região"
     * Para pratos especiais: "Feito no capricho pra você" ou "Sabor que acolhe e surpreende"
     * Para frango/carne de panela: "Carne de panela macia e saborosa" ou "Frango douradinho no capricho"

2. SELO/TAG DO PRATO (opcional):
   - Se for utilizar selo, use EXCLUSIVAMENTE "Qualidade Garantida", OU retorne null se a headline já disser tudo com clareza.
   - NUNCA use "Almoço do dia", "Executivo", carimbos ou slogans clichês.

3. LEGENDA DO POST:
   - Siga a estrutura de 3 parágrafos curtos + 4 hashtags.
   - O primeiro parágrafo (gancho) deve abrir o apetite de imediato.
   - Mantenha tom caloroso, honesto e acolhedor.

Responda APENAS com um objeto JSON, sem markdown ou texto antes/depois:
{
  "headline_imagem": "Chamada apetitosa e específica (2 a 6 palavras)",
  "selo_produto": "Qualidade Garantida ou null",
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

    system = (
        SYSTEM_PROMPT.replace("__SKILL__", cliente["skill"])
        .replace("__PADRAO__", cliente["legenda_padrao"] or PADRAO_AUSENTE)
        .replace("__DIA_SEMANA__", nome_dia)
        .replace("__DATA__", data_fmt)
    )
    prompt = (
        f"Dia da semana atual: {nome_dia} ({data_fmt})\n"
        f"Dados da foto selecionada:\n{_descrever(foto)}\n\n"
        f"Sugestão de ângulo para o gancho: {gancho_sugerido}\n"
        f"Lembre-se: foque no prato real e no apetite, sem clichês repetitivos de Sabor de Casa/Comida de Verdade e sem usar 'Almoço do dia' na imagem."
    )
    resposta = chamar_ia(system=system, prompt=prompt, max_tokens=900, temperature=0.8, json_mode=True)
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


# Alias para compatibilidade total com o orchestrator
gerar_copy_foto = gerar_legenda_foto
