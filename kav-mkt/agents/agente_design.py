"""Agente de Design: escreve o brief de Key Visual (KV) do post e gera a imagem final com
o modelo de imagem da OpenAI (GPT Image 2.5), uma única chamada por post.

Referências enviadas à IA, na mesma chamada de edição (gpt-image-2.5-sunburst), quando
disponíveis:
- **Layout**: uma das (até 10) imagens fixas em clientes/<slug>/referencias/, sorteada a
  cada post — a IA reproduz a estrutura do layout com o produto e os textos novos. Já
  está no tamanho final (1080x1440).
- **Produto**: a foto real do produto no catálogo, para ele aparecer igual ao anúncio.
- **Logo**: não é o arquivo do logo sozinho (que tem uma proporção bem diferente — uma
  faixa larga e baixa), e sim um "guia" gerado por código
  (utils.image_overlay.guia_posicao_logo): um canvas transparente do MESMO tamanho final
  (1080x1440) com o logo já colado na posição certa. Mandar uma referência "torta" junto
  com o layout (retrato) parecia confundir o modelo sobre a proporção de saída esperada,
  e foi isso que causava texto cortado no topo/rodapé mesmo com a margem pedida no brief
  (diagnosticado em 2026-09-23) — o guia resolve isso e ainda dá posição/escala exatas
  do logo, não só uma descrição em texto.

Sem nenhuma referência disponível (ou se a chamada com referências falhar), gera do zero
a partir do brief (gpt-image-2.5-flare) e avisa — nesse caso a imagem sai sem logo.
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

# Margem mínima (em % da imagem) que texto e logo devem manter de QUALQUER borda —
# além da faixa de topo/rodapé cortada pelo redimensionamento (ver _margem_corte_vertical).
# 8 (não 6) de propósito: folga extra enquanto validamos se o guia de logo (ver
# utils.image_overlay.guia_posicao_logo) já resolve o corte sozinho.
MARGEM_SEGURANCA_BORDA = 8

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
- quando existir, a foto real do produto, que ele vai manter fiel;
- um guia de logo: um template do MESMO formato/proporção da imagem final, transparente
  exceto onde o logo do cliente já está posicionado — reproduza o logo pixel a pixel
  dali (mesmas cores, proporções, tipografia e detalhes, nunca redesenhado ou
  distorcido), na mesma posição e escala mostradas no guia.

IMPORTANTE: as referências de layout e de logo estão no formato final exato do post
(retrato, mais alto que largo). Gere a cena na MESMA proporção dessas referências — não
em quadrado nem em outro formato.

MARGENS DE SEGURANÇA — valem para TEXTO (headline e selo) e para o LOGO, nenhum dos
dois pode invadir essas faixas:
- Topo e rodapé: depois de gerada, a imagem perde cerca de __MARGEM__% do topo e
  __MARGEM__% do rodapé (ajuste de proporção para o formato final do post). Trate essa
  faixa como fora dos limites — nada importante pode ficar nela.
- TODAS as bordas (topo, rodapé e as duas laterais): mantenha texto e logo a pelo menos
  __MARGEM_LATERAL__% de distância de qualquer borda da imagem. Nunca cole texto ou o
  logo rente à borda, mesmo nas laterais.
- O logo vai no __AREA_LOGO__, respeitando essas margens, com espaço vazio ao redor dele
  (nada de texto, produto ou elemento gráfico encostando nele).

CORES: use somente as cores da marca listadas nas diretrizes acima para os elementos
gráficos (bloco da headline, selo do produto, faixas, fundo atrás do logo) — não invente
cores fora dessa paleta. Garanta contraste forte entre cada texto e o fundo dele.

O brief (em inglês) deve definir, em um único parágrafo denso:
- a cena fotográfica (situação do dia a dia, carro, ambiente, enquadramento) pensada
  para formato VERTICAL (retrato), com todo elemento essencial dentro das margens de
  segurança acima;
- o produto em destaque e como ele aparece na cena;
- iluminação e mood;
- a headline e o selo do produto, com o tratamento gráfico previsto no KV do cliente,
  usando só as cores da marca;
- a reprodução exata do logo a partir do guia de posição, na mesma posição e escala
  mostradas nele.

Regras de texto na imagem:
- Renderize a headline e o selo EXATAMENTE como informados, palavra por palavra, em
  português — sem traduzir, resumir ou acrescentar palavras.
- Nenhum outro texto além deles (sem preço, sem slogan inventado).
- Letras grandes e legíveis, sempre dentro das margens de segurança descritas acima.

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
        .replace("__MARGEM_LATERAL__", str(MARGEM_SEGURANCA_BORDA))
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
    """Gera a imagem do post: sorteia o que estiver disponível (layout, foto real do
    produto, logo do cliente) como referências para a mesma chamada de edição — o logo
    também é desenhado pela IA a partir do arquivo oficial, não mais colado por código."""
    avisos = []
    referencias_imagem = []  # [(bytes, descrição em inglês para o prompt), ...]

    if referencia:
        referencias_imagem.append((
            referencia["arquivo"].read_bytes(),
            "this brand's layout template. Reproduce its layout structure closely — "
            "placement and shape of the headline block, the product tag, color bands, "
            "graphic elements and typography style — but with the new photo scene, "
            "product and texts described below. Ignore any text, logo or product shown "
            "in it.",
        ))

    tem_foto = False
    if produto.get("foto_url") and not produto.get("fallback_usado"):
        try:
            referencias_imagem.append((
                openai_client.baixar_imagem_referencia(produto["foto_url"]),
                "the real product being advertised. Keep its exact shape, colors, "
                "materials and details as photographed; do not redesign it.",
            ))
            tem_foto = True
        except Exception as exc:  # segue sem a foto, com aviso
            avisos.append(f"Não consegui baixar a foto do produto ({exc}); a IA desenhou o produto a partir do nome.")

    logo_arquivo, posicao_logo = _logo(cliente, referencia)
    if logo_arquivo:
        # Canvas do tamanho final (não o arquivo do logo sozinho, que tem proporção bem
        # diferente) — ver docstring do módulo para o porquê.
        guia_logo = image_overlay.guia_posicao_logo(logo_arquivo, posicao_logo)
        referencias_imagem.append((
            guia_logo,
            "a template the exact same pixel dimensions as the final image, transparent "
            "everywhere except where the client's logo already sits — reproduce that "
            "logo pixel-for-pixel, at that same position and scale, keeping its exact "
            "colors, proportions and details (do not redraw, recolor or distort it). "
            "Everywhere else in this template is transparent guidance only, not part of "
            "the visible scene.",
        ))

    bruta = None
    layout_usado = referencia["arquivo"].name if referencia else None
    if referencias_imagem:
        try:
            imagens = [dados for dados, _ in referencias_imagem]
            prompt = _prompt_com_referencias(brief, [desc for _, desc in referencias_imagem])
            bruta = openai_client.gerar_imagem_com_referencias(prompt, imagens)
        except Exception as exc:  # cai para a geração sem referências, com aviso
            avisos.append(f"A geração com referências falhou ({exc}); gerei sem elas (sem logo nesta imagem).")
    if not bruta or not bruta.get("imagem_b64"):
        if bruta is not None:
            avisos.append("A geração com referências não retornou imagem; gerei sem elas (sem logo nesta imagem).")
        bruta = openai_client.gerar_imagem(brief)
        layout_usado, tem_foto = None, False
    if not bruta.get("imagem_b64"):
        raise RuntimeError("A API de imagem não retornou nenhuma imagem.")

    if bruta.get("tamanho_pedido") and bruta.get("tamanho_real") and bruta["tamanho_pedido"] != bruta["tamanho_real"]:
        avisos.append(
            f"A API pediu {bruta['tamanho_pedido']} mas devolveu {bruta['tamanho_real']} — "
            "o recorte final ainda sai certo (1080x1440), mas a margem interna pode não "
            "bater exatamente com o que foi pedido no brief."
        )

    return {
        **_finalizar(base64.b64decode(bruta["imagem_b64"])),
        "modelo": bruta.get("modelo"),
        "qualidade": bruta.get("qualidade"),
        "tamanho_gerado": bruta.get("tamanho_real"),
        "referencia_layout": layout_usado,
        "com_foto_produto": tem_foto,
        "aviso": " ".join(avisos) or None,
    }


def ajustar_imagem(imagem_atual: bytes, instrucao: str) -> dict:
    """Aplica um ajuste pontual pedido pelo usuário (ex: 'deixe o céu ao entardecer')
    sobre a imagem já gerada, com o modelo de edição (gpt-image-2.5-sunburst, indicado
    para manter fidelidade). Parte da imagem final (já com logo e texto), instruindo a
    IA a manter tudo igual exceto o que foi pedido."""
    prompt = (
        "Apply ONLY the following adjustment to the reference image, keeping everything "
        "else (composition, product, text, logo, colors) exactly the same unless the "
        "instruction explicitly says otherwise:\n" + instrucao.strip()
    )
    # size="auto": a imagem de entrada já está no formato final — pedir o IMAGE_SIZE
    # padrão distorceria a proporção.
    bruta = openai_client.gerar_imagem_com_referencias(prompt, [imagem_atual], size="auto")
    if not bruta.get("imagem_b64"):
        raise RuntimeError("A API de imagem não retornou nenhuma imagem para esse ajuste.")
    return {
        **_finalizar(base64.b64decode(bruta["imagem_b64"])),
        "modelo": bruta.get("modelo"),
        "qualidade": bruta.get("qualidade"),
        "tamanho_gerado": bruta.get("tamanho_real"),
    }


def _finalizar(imagem_bytes: bytes) -> dict:
    final = image_overlay.recortar_formato_final(imagem_bytes)
    return {
        "imagem_b64": base64.b64encode(final).decode("ascii"),
        "tamanho": f"{image_overlay.LARGURA_PADRAO}x{image_overlay.ALTURA_PADRAO}",
    }


def _prompt_com_referencias(brief: str, descricoes: list) -> str:
    partes = [f"Reference image {i + 1} is {desc}" for i, desc in enumerate(descricoes)]
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
    """Quanto (%) do topo e do rodapé o recorte para o formato final remove, com +4 pontos
    de folga — para avisar a IA a deixar essa faixa sem nada importante.

    Isso assume que a API devolve o tamanho pedido (IMAGE_SIZE) — nem sempre é verdade
    (ver `openai_client._resultado_imagem`, que mede o tamanho real da imagem que volta).
    A folga extra é por causa dessa incerteza; se `aviso` de "tamanho_real" continuar
    aparecendo com frequência, considere um valor de folga ainda maior aqui."""
    try:
        largura, altura = (int(v) for v in openai_client.IMAGE_SIZE.lower().split("x"))
    except (ValueError, AttributeError):
        return 10  # tamanho não numérico (ex: "auto") — margem conservadora
    razao_final = image_overlay.LARGURA_PADRAO / image_overlay.ALTURA_PADRAO
    if largura / altura >= razao_final:
        return 0  # nesse caso o recorte é nas laterais, não no topo/rodapé
    corte_total = 1 - (largura / razao_final) / altura
    return round(corte_total / 2 * 100) + 4
