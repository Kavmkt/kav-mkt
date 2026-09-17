"""Agente de Design: monta o brief de Key Visual (KV) do post — composição, direção de
arte, cores da marca e eventual texto de destaque — e gera a imagem final chamando o
modelo de imagem da OpenAI (gpt-image-1) uma única vez por execução.

O brief é pensado para sair completo e específico já na primeira chamada de texto, para
que a chamada de imagem (mais cara) não precise ser repetida por falta de direção.
"""
from typing import Optional

from utils import openai_client
from utils.openai_client import chamar_ia

SYSTEM_PROMPT = """Você é o Diretor de Arte da Kav (@kav.mkt). Sua função é escrever o
brief de Key Visual (KV) de UM post, pronto para ser enviado direto a um gerador de
imagem por IA — sem chance de retrabalho, então precisa ser completo e específico logo
na primeira vez.

DIRETRIZES DE MARCA E VISUAL DO CLIENTE:
{skill}

O brief (em inglês, pronto para o gerador de imagem) deve definir, em um único parágrafo
denso:
- Cena/composição principal (o que aparece, enquadramento, plano)
- Produto em destaque (quando houver) e como ele aparece na cena
- Paleta de cores (use as cores da marca do cliente)
- Estilo/direção de arte (fotografia realista, ilustração, etc. — escolha o que combine
  com o público e o tom do cliente)
- Iluminação e humor/mood
- Espaço de respiro (negative space) pensado para uma eventual sobreposição de
  logo/texto do post por cima da imagem

Regras:
- No máximo uma frase curta de texto embutido na imagem (3-4 palavras), e só se agregar
  de verdade (ex: uma chamada tipo "-20% HOJE"); IA de imagem erra textos longos, então
  na dúvida não inclua nenhum texto.
- Se nenhum produto foi informado (post institucional/educativo), descreva uma cena
  genérica coerente com o segmento do cliente, sem inventar produtos.
- Retorne APENAS o brief em texto corrido, em inglês, sem explicações, sem markdown,
  sem listas — é o prompt final que vai direto para o gerador de imagem.
"""


def gerar_prompt_imagem(pauta: dict, produto: Optional[dict], skill: dict) -> str:
    system = SYSTEM_PROMPT.format(skill=skill["texto_completo"])
    partes = [
        f"Tema do post: {pauta.get('tema')}",
        f"Descrição: {pauta.get('descricao')}",
        f"Objetivo: {pauta.get('objetivo')}",
    ]
    if produto and produto.get("nome"):
        partes.append(f"Produto a destacar na imagem: {produto['nome']}")
        if produto.get("fallback_usado"):
            partes.append(
                "Observação: este é um produto coringa (fallback), descreva-o de forma "
                "genérica e reconhecível, sem depender de detalhes visuais exatos de uma "
                "foto específica que não temos."
            )
    else:
        partes.append("Nenhum produto específico foi definido — crie uma cena genérica do segmento.")

    prompt = "\n".join(partes)
    return chamar_ia(system=system, prompt=prompt, max_tokens=500, temperature=0.8)


def gerar_imagem(prompt_imagem: str) -> dict:
    """Gera a imagem final a partir do brief de KV (uma única chamada, sem iteração)."""
    return openai_client.gerar_imagem(prompt_imagem)
