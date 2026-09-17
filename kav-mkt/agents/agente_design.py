"""Agente de Design: monta o brief de Key Visual (KV) do post — composição, direção de
arte, cores da marca e a chamada (headline) em português — e gera a imagem final
chamando o modelo de imagem da OpenAI (GPT Image 2.5) uma única vez por execução.

O texto é desenhado pela PRÓPRIA IA de imagem, como parte da cena (não é mais sobreposto
por código depois). O GPT Image 2.5 é bem melhor em texto do que o modelo anterior
(gpt-image-1), então isso passou a ser viável — se erros de texto cortado/embaralhado
voltarem a aparecer, dá pra reverter para o desenho por código em
`utils.image_overlay.compor_imagem_final` (a função continua lá, só não é mais chamada
com uma headline).

Como a imagem gerada é recortada depois para o formato final (ver `_margem_corte_vertical`
e `utils.image_overlay`), o brief avisa a IA — com o percentual exato calculado a partir
dos tamanhos configurados — para manter texto/logo fora da faixa de topo/rodapé que será
cortada, em vez de arriscar colar esses elementos na borda.

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

ATENÇÃO — RECORTE POSTERIOR: depois de gerada, a imagem passa por um recorte automático
que remove cerca de {margem_corte}% do topo e outros {margem_corte}% do rodapé da tela
(pra ajustar a proporção ao formato final do post). Isso significa que QUALQUER
texto, logotipo, rosto ou elemento importante posicionado nesses {margem_corte}% mais
próximos da borda de cima ou de baixo será cortado. Planeje a composição já contando com
isso: trate a faixa de {margem_corte}% no topo e no rodapé como uma margem de segurança
— pode ter fundo/cenário ali, mas nada que precise aparecer inteiro.

O brief (em inglês, pronto para o gerador de imagem) deve definir, em um único parágrafo
denso:
- Cena/composição principal (o que aparece, enquadramento, plano), pensada para um
  formato VERTICAL (retrato, mais alto do que largo), com todo elemento essencial
  centralizado verticalmente, respeitando a margem de segurança de topo/rodapé acima
- Produto em destaque (quando houver) e como ele aparece na cena
- Paleta de cores (use as cores da marca do cliente)
- Estilo/direção de arte (fotografia realista, ilustração, etc. — escolha o que combine
  com o público e o tom do cliente)
- Iluminação e humor/mood
- Um tratamento gráfico para a HEADLINE informada abaixo (quando houver): um bloco
  sólido (faixa ou retângulo) numa cor da marca, com o texto em letras grandes, em
  negrito/caixa alta, numa cor de alto contraste — como um pôster/anúncio real,
  posicionado bem dentro da área segura (nunca colado nas bordas de cima ou de baixo)

Regras para a headline (quando houver uma):
- O texto renderizado deve ser EXATAMENTE a headline informada, palavra por palavra, em
  português — não traduza, não resuma, não invente palavras extras.
- Letras grandes, fonte bold/condensada, inteiramente dentro da área segura descrita
  acima — nunca cortada, nunca saindo do quadro, nunca dentro da margem de topo/rodapé.
- Se imagens de referência de posts anteriores forem fornecidas e tiverem texto nelas,
  IGNORE o texto que aparece nelas — use só a headline informada abaixo, não o texto das
  referências.
- Se nenhuma headline for informada, não inclua nenhum texto na imagem.

Outras regras:
- Se nenhum produto foi informado (post institucional/educativo), descreva uma cena
  genérica coerente com o segmento do cliente, sem inventar produtos.
- Retorne APENAS o brief em texto corrido, em inglês — exceto a headline em si, que deve
  aparecer citada entre aspas exatamente em português — sem explicações, sem markdown,
  sem listas. É o prompt final que vai direto para o gerador de imagem.
"""


def _margem_corte_vertical() -> int:
    """Calcula (em %) quanto do topo/rodapé da imagem gerada é removido pelo recorte
    para o formato final, para avisar a IA a deixar uma margem de segurança na
    composição. Soma uma folga extra (2 pontos percentuais) por segurança."""
    try:
        largura_gerada, altura_gerada = (int(v) for v in openai_client.IMAGE_SIZE.lower().split("x"))
    except (ValueError, AttributeError):
        return 10  # tamanho não numérico (ex: "auto") — usa uma margem conservadora
    razao_gerada = largura_gerada / altura_gerada
    razao_final = image_overlay.LARGURA_PADRAO / image_overlay.ALTURA_PADRAO
    if razao_gerada >= razao_final:
        return 0  # o recorte nesse caso seria nas laterais, não no topo/rodapé
    altura_apos_corte = largura_gerada / razao_final
    corte_total = 1 - (altura_apos_corte / altura_gerada)
    return round((corte_total / 2) * 100) + 2


def gerar_prompt_imagem(pauta: dict, produto: Optional[dict], skill: dict) -> str:
    system = SYSTEM_PROMPT.format(
        skill=skill["texto_completo"],
        margem_corte=_margem_corte_vertical(),
    )
    partes = [
        f"Tema do post: {pauta.get('tema')}",
        f"Descrição: {pauta.get('descricao')}",
        f"Objetivo: {pauta.get('objetivo')}",
    ]
    headline = pauta.get("headline_imagem")
    if headline:
        partes.append(f'Headline a renderizar na imagem (em português, exatamente): "{headline}"')
    else:
        partes.append("Nenhuma headline definida — não inclua texto na imagem.")
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
            "posts. Do not copy their specific subject, product or on-image text — only "
            "the visual style/layout."
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
    skill: dict,
    produto: Optional[dict] = None,
    usar_referencias_layout: bool = True,
) -> dict:
    """Gera a imagem (com foto real do produto e/ou estilo dos últimos posts, quando
    disponíveis) — a headline já vem desenhada pela própria IA, como parte do brief.
    Corta/redimensiona para o formato final (1080x1440 por padrão) e cola o logo do
    cliente, se existir. Guarda o resultado como referência de layout para a próxima
    execução."""
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
        headline="",  # a headline já foi desenhada pela IA na própria cena
        cores_hex=skill.get("cores_hex") or [],
        cliente=cliente,
    )
    bruta["imagem_b64"] = base64.b64encode(imagem_final_bytes).decode("ascii")
    bruta["tamanho"] = f"{image_overlay.LARGURA_PADRAO}x{image_overlay.ALTURA_PADRAO}"

    if cliente:
        salvar_referencia_layout(cliente, imagem_final_bytes)

    return bruta
