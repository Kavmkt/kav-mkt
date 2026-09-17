"""Agente de Design: monta o brief de Key Visual (KV) do post — composição, direção de
arte e cores da marca — gera a imagem base chamando o modelo de imagem da OpenAI (GPT
Image 2.5) uma única vez por execução, e sobrepõe a chamada (headline) por código.

Duas fontes de referência visual, combináveis, ambas via edição de imagem (não geração
do zero):
- **Produto**: quando o produto tem uma foto real (link colado no formulário, não um
  fallback coringa), a foto é baixada e usada como referência, preservando a aparência
  real do produto em vez de descrevê-lo só por texto.
- **Layout**: as últimas imagens geradas por este app para o cliente (guardadas em
  data/<cliente>/referencias_layout/) são reaproveitadas como referência de estilo
  visual/composição para o próximo post, criando consistência entre os posts ao longo do
  tempo. Também é possível alimentar essa pasta manualmente com posts antigos (ver
  `salvar_referencia_layout`, usado pela interface).

Se qualquer tentativa com referência falhar (link não é imagem direta, API recusa,
etc.), cai automaticamente para a geração comum a partir do texto — nunca trava o fluxo.

Não pedimos para o próprio modelo de imagem escrever texto na cena: IA de imagem erra
texto com frequência (corta, embaralha letras, ou usa o idioma errado). Em vez disso o
brief pede uma cena limpa, com espaço reservado, e o texto em português entra depois via
`utils.image_overlay`, com fonte e posição garantidas.
"""
import base64
from datetime import datetime
from pathlib import Path
from typing import Optional

from utils import image_overlay, openai_client
from utils.openai_client import chamar_ia

BASE_DIR = Path(__file__).resolve().parent.parent
MAX_REFERENCIAS_LAYOUT = 3

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


# --- Referências de layout (últimos posts) ---------------------------------------

def _pasta_referencias_layout(cliente: str) -> Path:
    pasta = BASE_DIR / "data" / cliente / "referencias_layout"
    pasta.mkdir(parents=True, exist_ok=True)
    return pasta


def carregar_referencias_layout(cliente: str, limite: int = MAX_REFERENCIAS_LAYOUT) -> list:
    """Retorna os bytes das `limite` imagens de referência de layout mais recentes."""
    if not cliente:
        return []
    pasta = _pasta_referencias_layout(cliente)
    arquivos = sorted(pasta.glob("*.png"), key=lambda p: p.stat().st_mtime, reverse=True)
    return [a.read_bytes() for a in arquivos[:limite]]


def salvar_referencia_layout(cliente: str, imagem_bytes: bytes) -> None:
    """Guarda uma imagem (gerada pelo app, ou enviada manualmente) como referência de
    layout para as próximas gerações desse cliente."""
    pasta = _pasta_referencias_layout(cliente)
    nome = f"{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.png"
    (pasta / nome).write_bytes(imagem_bytes)


def limpar_referencias_layout(cliente: str) -> None:
    """Apaga todas as referências de layout guardadas para o cliente."""
    pasta = _pasta_referencias_layout(cliente)
    for arquivo in pasta.glob("*.png"):
        arquivo.unlink(missing_ok=True)


# --- Geração da imagem -------------------------------------------------------------

def _prompt_para_edicao(prompt_cena: str, tem_layout_refs: bool, tem_produto_real: bool) -> str:
    partes = []
    if tem_layout_refs:
        partes.append(
            "The reference image(s) shown first are examples of this brand's past post "
            "designs. Match their overall visual style, composition, framing, color "
            "treatment and mood as closely as possible, to keep a consistent look across "
            "posts. Do not copy their specific subject or product — only the visual "
            "style/layout."
        )
    if tem_produto_real:
        partes.append(
            "The LAST reference image shown is the real product for this post — keep "
            "its exact shape, colors, materials and label/branding exactly as "
            "photographed, do not redesign it."
        )
    partes.append("New scene to depict:\n" + prompt_cena)
    return "\n\n".join(partes)


def _gerar_imagem_bruta(prompt_imagem: str, produto: Optional[dict], referencias_layout: list) -> dict:
    """Tenta gerar com referências (layout e/ou foto real do produto); se não houver
    nenhuma referência disponível, ou a tentativa falhar por qualquer motivo, cai para a
    geração comum a partir do texto — nunca trava o fluxo."""
    foto_url = (produto or {}).get("foto_url")
    tem_foto_real = bool(foto_url) and not (produto or {}).get("fallback_usado")
    tem_layout_refs = bool(referencias_layout)

    if tem_foto_real or tem_layout_refs:
        try:
            imagens = list(referencias_layout)
            if tem_foto_real:
                imagens.append(openai_client.baixar_imagem_referencia(foto_url))
            prompt_edicao = _prompt_para_edicao(prompt_imagem, tem_layout_refs, tem_foto_real)
            resultado = openai_client.gerar_imagem_com_referencias(prompt_edicao, imagens)
            if resultado.get("imagem_b64"):
                resultado["com_referencia"] = tem_foto_real
                resultado["com_layout_referencia"] = tem_layout_refs
                return resultado
        except Exception:
            pass  # cai para a geração comum abaixo

    resultado = openai_client.gerar_imagem(prompt_imagem)
    resultado["com_referencia"] = False
    resultado["com_layout_referencia"] = False
    return resultado


def gerar_imagem(
    prompt_imagem: str,
    headline: Optional[str],
    skill: dict,
    produto: Optional[dict] = None,
    usar_referencias_layout: bool = True,
) -> dict:
    """Gera a imagem (com foto real do produto e/ou estilo dos últimos posts, quando
    disponíveis) e sobrepõe a chamada em português no formato final (1080x1440 por
    padrão), usando as cores da marca. Guarda o resultado como referência de layout para
    a próxima execução."""
    cliente = skill.get("cliente")
    referencias_layout = (
        carregar_referencias_layout(cliente) if (cliente and usar_referencias_layout) else []
    )

    bruta = _gerar_imagem_bruta(prompt_imagem, produto, referencias_layout)
    if not bruta.get("imagem_b64"):
        # Sem base64 (ex: só veio uma URL) não dá pra compor localmente — devolve como veio.
        return bruta

    imagem_final_bytes = image_overlay.compor_imagem_final(
        imagem_bytes=base64.b64decode(bruta["imagem_b64"]),
        headline=headline or "",
        cores_hex=skill.get("cores_hex") or [],
        cliente=cliente,
    )
    bruta["imagem_b64"] = base64.b64encode(imagem_final_bytes).decode("ascii")
    bruta["tamanho"] = f"{image_overlay.LARGURA_PADRAO}x{image_overlay.ALTURA_PADRAO}"

    if cliente:
        salvar_referencia_layout(cliente, imagem_final_bytes)

    return bruta
