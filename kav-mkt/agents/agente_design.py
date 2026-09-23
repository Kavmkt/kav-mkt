"""Agente de Design: escreve o brief de Key Visual (KV) do post e gera a imagem final com
o modelo de imagem da OpenAI (GPT Image 2.5), uma única chamada por post.

Referências enviadas à IA, na mesma chamada de edição (gpt-image-2.5-sunburst):
- **Layout**: uma das (até 10) imagens fixas em clientes/<slug>/referencias/, sorteada a
  cada post — a IA reproduz a estrutura do layout com o produto e os textos novos.
- **Produto**: a foto real do produto no catálogo, para ele aparecer igual ao anúncio.

Sem nenhuma referência disponível (ou se a chamada com referências falhar), gera do zero
a partir do brief (gpt-image-2.5-flare) e avisa.

A chamada e o selo do produto são desenhados pela própria IA na cena. O logo NÃO: a IA
deixa livre a área onde o logo fica naquele layout (referencias.json) e o logo é
aplicado depois por código (utils.image_overlay), para sair idêntico ao arquivo.
"""
import base64
import random
from pathlib import Path
from typing import Optional

from utils import image_overlay, openai_client
from utils.openai_client import chamar_ia

AREAS_LOGO = {
    "superior-esquerdo": "top-left corner",
    "superior-centro": "top center",
    "superior-direito": "top-right corner",
    "inferior-esquerdo": "bottom-left corner",
    "inferior-centro": "bottom center",
    "inferior-direito": "bottom-right corner",
}

# Placeholders substituídos com .replace() (e não .format()): o texto da skill do cliente
# pode ter chaves {} que quebrariam o .format().
SYSTEM_PROMPT = """Você é o Diretor de Arte da Kav (@kav.mkt). Sua função é escrever o
brief de Key Visual (KV) de UM post de produto, pronto para ser enviado direto a um
gerador de imagem por IA — sem chance de retrabalho, então precisa ser completo e
específico logo na primeira vez.

DIRETRIZES DE MARCA E KV DO CLIENTE:
__SKILL__

Contexto de produção (o gerador de imagem recebe junto com o seu brief):
__CONTEXTO_LAYOUT__
- quando existir, a foto real do produto, que ele vai manter fiel.

RECORTE POSTERIOR: depois de gerada, a imagem perde cerca de __MARGEM__% do topo e
__MARGEM__% do rodapé (ajuste para o formato final do post). Nada importante — texto,
produto, rostos — pode ficar nessas faixas.

LOGO: o logo do cliente é aplicado depois, por código, na área __AREA_LOGO__ da imagem.
Deixe essa área livre de texto e de elementos importantes (fundo simples ali), e NÃO
desenhe nenhum logotipo, nome de loja, tagline ou marca do cliente na imagem.

O brief (em inglês) deve definir, em um único parágrafo denso:
- a cena fotográfica (situação do dia a dia, carro, ambiente, enquadramento) pensada
  para formato VERTICAL (retrato);
- o produto em destaque e como ele aparece na cena;
- iluminação e mood;
- a headline e o selo do produto, com o tratamento gráfico previsto no KV do cliente.

Regras de texto na imagem:
- Renderize a headline e o selo EXATAMENTE como informados, palavra por palavra, em
  português — sem traduzir, resumir ou acrescentar palavras.
- Nenhum outro texto além deles (sem preço, sem slogan inventado).
- Letras grandes e legíveis, inteiras dentro da área segura.

Retorne APENAS o brief em texto corrido, em inglês — exceto a headline e o selo, citados
entre aspas exatamente em português. Sem explicações, sem markdown, sem listas.
"""


CONTEXTO_COM_REFERENCIA = (
    "- uma imagem de referência de layout do cliente, que ele vai reproduzir em estrutura —\n"
    "  então descreva a CENA e o CONTEÚDO do post novo, e não um layout novo do zero;"
)
CONTEXTO_SEM_REFERENCIA = (
    "- nenhuma referência de layout: descreva também o layout (posição e forma da\n"
    "  headline, do selo e das faixas) seguindo o KV do cliente;"
)


def escolher_referencia(cliente: dict) -> Optional[dict]:
    """Sorteia uma das referências de layout do cliente (ou None se não houver)."""
    return random.choice(cliente["referencias"]) if cliente["referencias"] else None


def gerar_brief(copy: dict, produto: dict, cliente: dict, referencia: Optional[dict]) -> str:
    contexto = CONTEXTO_COM_REFERENCIA if referencia else CONTEXTO_SEM_REFERENCIA
    _, posicao_logo = _logo(cliente, referencia)
    system = (
        SYSTEM_PROMPT.replace("__SKILL__", cliente["skill"])
        .replace("__CONTEXTO_LAYOUT__", contexto)
        .replace("__MARGEM__", str(_margem_corte_vertical()))
        .replace("__AREA_LOGO__", AREAS_LOGO.get(posicao_logo, "bottom-left corner"))
    )
    partes = [f"Produto: {produto.get('nome')}"]
    if produto.get("categoria"):
        partes.append(f"Categoria: {produto['categoria']}")
    if produto.get("fallback_usado"):
        partes.append("Não há foto real deste produto — descreva-o de forma genérica e reconhecível.")
    partes.append(f'Headline (renderizar exatamente): "{copy.get("headline_imagem")}"')
    if copy.get("selo_produto"):
        partes.append(f'Selo do produto (renderizar exatamente): "{copy["selo_produto"]}"')
    return chamar_ia(system=system, prompt="\n".join(partes), max_tokens=600, temperature=0.8)


def gerar_imagem(brief: str, produto: dict, cliente: dict, referencia: Optional[dict]) -> dict:
    """Gera a imagem do post e devolve a versão final (recortada + logo) e a versão sem
    logo (usada como base para ajustes pontuais depois)."""
    imagens = [referencia["arquivo"].read_bytes()] if referencia else []
    avisos = []
    layout_usado = referencia["arquivo"].name if referencia else None

    tem_foto = False
    if produto.get("foto_url") and not produto.get("fallback_usado"):
        try:
            imagens.append(openai_client.baixar_imagem_referencia(produto["foto_url"]))
            tem_foto = True
        except Exception as exc:  # segue sem a foto, com aviso
            avisos.append(f"Não consegui baixar a foto do produto ({exc}); a IA desenhou o produto a partir do nome.")

    bruta = None
    if imagens:
        try:
            bruta = openai_client.gerar_imagem_com_referencias(
                _prompt_com_referencias(brief, referencia is not None, tem_foto), imagens
            )
        except Exception as exc:  # cai para a geração sem referências, com aviso
            avisos.append(f"A geração com referências falhou ({exc}); gerei sem elas.")
    if not bruta or not bruta.get("imagem_b64"):
        if bruta is not None:
            avisos.append("A geração com referências não retornou imagem; gerei sem elas.")
        bruta = openai_client.gerar_imagem(brief)
        layout_usado, tem_foto = None, False
    if not bruta.get("imagem_b64"):
        raise RuntimeError("A API de imagem não retornou nenhuma imagem.")

    return {
        **_finalizar(base64.b64decode(bruta["imagem_b64"]), cliente, referencia),
        "modelo": bruta.get("modelo"),
        "qualidade": bruta.get("qualidade"),
        "referencia_layout": layout_usado,
        "com_foto_produto": tem_foto,
        "aviso": " ".join(avisos) or None,
    }


def ajustar_imagem(imagem_sem_logo: bytes, instrucao: str, cliente: dict, referencia: Optional[dict]) -> dict:
    """Aplica um ajuste pontual pedido pelo usuário (ex: 'deixe o céu ao entardecer')
    sobre a imagem já gerada, com o modelo de edição (gpt-image-2.5-sunburst, indicado
    para manter fidelidade). Parte da versão SEM logo, para o logo reaplicado por código
    não sair duplicado."""
    prompt = (
        "Apply ONLY the following adjustment to the reference image, keeping everything "
        "else (composition, product, text, colors) exactly the same unless the instruction "
        "explicitly says otherwise:\n" + instrucao.strip()
    )
    # size="auto": a imagem de entrada já está no formato final — pedir o IMAGE_SIZE
    # padrão distorceria a proporção.
    bruta = openai_client.gerar_imagem_com_referencias(prompt, [imagem_sem_logo], size="auto")
    if not bruta.get("imagem_b64"):
        raise RuntimeError("A API de imagem não retornou nenhuma imagem para esse ajuste.")
    return {
        **_finalizar(base64.b64decode(bruta["imagem_b64"]), cliente, referencia),
        "modelo": bruta.get("modelo"),
        "qualidade": bruta.get("qualidade"),
    }


def _finalizar(imagem_bytes: bytes, cliente: dict, referencia: Optional[dict]) -> dict:
    sem_logo = image_overlay.recortar_formato_final(imagem_bytes)
    final = image_overlay.aplicar_logo(sem_logo, *_logo(cliente, referencia))
    return {
        "imagem_b64": base64.b64encode(final).decode("ascii"),
        "imagem_sem_logo_b64": base64.b64encode(sem_logo).decode("ascii"),
        "tamanho": f"{image_overlay.LARGURA_PADRAO}x{image_overlay.ALTURA_PADRAO}",
    }


def _prompt_com_referencias(brief: str, tem_layout: bool, tem_foto: bool) -> str:
    partes = []
    if tem_layout:
        partes.append(
            "The FIRST reference image is this brand's layout template. Reproduce its layout "
            "structure closely — placement and shape of the headline block, the product tag, "
            "color bands, graphic elements and typography style — but with the new photo "
            "scene, product and texts described below. Ignore any text, prices or logos that "
            "appear in it."
        )
    if tem_foto:
        partes.append(
            "The LAST reference image is the real product being advertised — keep its exact "
            "shape, colors, materials and details as photographed; do not redesign it."
        )
    partes.append("Post to create:\n" + brief)
    return "\n\n".join(partes)


def _logo(cliente: dict, referencia: Optional[dict]) -> tuple:
    """(arquivo do logo, posição) para o layout sorteado: posição e versão (fundo claro
    ou escuro) vêm de referencias.json; sem isso, a posição padrão do config.json e o
    logo para fundo escuro."""
    referencia = referencia or {}
    posicao = referencia.get("logo_posicao") or cliente["config"].get("logo_posicao", "inferior-esquerdo")
    versao = referencia.get("logo_versao", "fundo-escuro")
    arquivo: Optional[Path] = cliente["logos"].get(versao) or cliente["logos"].get("fundo-escuro")
    return arquivo, posicao


def _margem_corte_vertical() -> int:
    """Quanto (%) do topo e do rodapé o recorte para o formato final remove, com +2 pontos
    de folga — para avisar a IA a deixar essa faixa sem nada importante."""
    try:
        largura, altura = (int(v) for v in openai_client.IMAGE_SIZE.lower().split("x"))
    except (ValueError, AttributeError):
        return 10  # tamanho não numérico (ex: "auto") — margem conservadora
    razao_final = image_overlay.LARGURA_PADRAO / image_overlay.ALTURA_PADRAO
    if largura / altura >= razao_final:
        return 0  # nesse caso o recorte é nas laterais, não no topo/rodapé
    corte_total = 1 - (largura / razao_final) / altura
    return round(corte_total / 2 * 100) + 2
