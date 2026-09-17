"""Agente de Design: monta o brief de Key Visual (KV) do post — composição, direção de
arte e cores da marca — gera a imagem base chamando o modelo de imagem da OpenAI
(gpt-image-1) uma única vez por execução, e sobrepõe a chamada (headline) por código.

Não pedimos para o próprio modelo de imagem escrever texto na cena: IA de imagem erra
texto com frequência (corta, embaralha letras, ou usa o idioma errado). Em vez disso o
brief pede uma cena limpa, com espaço reservado, e o texto em português entra depois via
`utils.image_overlay`, com fonte e posição garantidas.
"""
import base64
from typing import Optional

from utils import image_overlay, openai_client
from utils.openai_client import chamar_ia

SYSTEM_PROMPT = """Você é o Diretor de Arte da Kav (@kav.mkt). Sua função é escrever o
brief de Key Visual (KV) de UM post, pronto para ser enviado direto a um gerador de
imagem por IA — sem chance de retrabalho, então precisa ser completo e específico logo
na primeira vez.

DIRETRIZES DE MARCA E VISUAL DO CLIENTE:
{skill}

O brief (em inglês, pronto para o gerador de imagem) deve definir, em um único parágrafo
denso:
- Cena/composição principal (o que aparece, enquadramento, plano), pensada para um
  formato VERTICAL (retrato, mais alto do que largo)
- Produto em destaque (quando houver) e como ele aparece na cena
- Paleta de cores (use as cores da marca do cliente)
- Estilo/direção de arte (fotografia realista, ilustração, etc. — escolha o que combine
  com o público e o tom do cliente)
- Iluminação e humor/mood
- O terço inferior da imagem deve ficar visualmente mais simples/limpo (menos elementos
  de destaque ali), pois uma barra sólida com texto será adicionada por cima depois

Regras:
- NÃO inclua nenhum texto, letra, número, logotipo ou palavra na imagem — isso é feito
  à parte depois. A cena deve ser 100% visual, sem tipografia nenhuma.
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


def gerar_imagem(prompt_imagem: str, headline: Optional[str], skill: dict) -> dict:
    """Gera a imagem base (uma única chamada, sem iteração) e sobrepõe a chamada em
    português no formato final (1080x1440 por padrão), usando as cores da marca."""
    bruta = openai_client.gerar_imagem(prompt_imagem)
    if not bruta.get("imagem_b64"):
        # Sem base64 (ex: só veio uma URL) não dá pra compor localmente — devolve como veio.
        return bruta

    imagem_final_bytes = image_overlay.compor_imagem_final(
        imagem_bytes=base64.b64decode(bruta["imagem_b64"]),
        headline=headline or "",
        cores_hex=skill.get("cores_hex") or [],
    )
    bruta["imagem_b64"] = base64.b64encode(imagem_final_bytes).decode("ascii")
    bruta["tamanho"] = f"{image_overlay.LARGURA_PADRAO}x{image_overlay.ALTURA_PADRAO}"
    return bruta
