"""Agente de Design: monta o brief de Key Visual (KV) do post — composição, direção de
arte, cores da marca e a chamada (headline) em português — e gera a imagem final
chamando o modelo de imagem da OpenAI (GPT Image 2.5) uma única vez por execução.

O texto é desenhado pela PRÓPRIA IA de imagem, como parte da cena (não é mais sobreposto
por código depois). O GPT Image 2.5 é bem melhor em texto do que o modelo anterior
(gpt-image-1), então isso passou a ser viável — se erros de texto cortado/embaralhado
voltarem a aparecer, dá pra reverter para o desenho por código em
`utils.image_overlay.compor_imagem_final` (a função continua lá, só não é mais chamada
com uma headline).

Como a imagem gerada é redimensionada depois para o formato final (ver
`_redimensionar_para_formato_final` e `utils.image_overlay`), não há perda de topo/rodapé
— a composição é preservada integralmente.

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

from PIL import Image
from io import BytesIO

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

REGRAS NEGATIVAS E DIRETRIZES OBRIGATÓRIAS (o brief DEVE deixar isso explícito para o
gerador de imagem, e o gerador NUNCA deve violar):

1. AMBIENTAÇÃO DO PRODUTO (quando houver produto real):
   - Sempre posicionar o produto em um ambiente profissional, limpo, bem iluminado e
     que favoreça o produto (ex: superfície de trabalho, bancada, cenário de estúdio,
     contexto de aplicação real do produto).
   - NUNCA colocar o produto no chão, jogado em cantos sujos, sobre superfícies
     degradadas, com poeira, manchas, entulho ou qualquer contexto que desvalorize
     o produto.
   - A iluminação deve destacar o produto (luz controlada, sombras suaves, realce
     de textura e acabamento).

2. TIPOGRAFIA:
   - Usar EXCLUSIVAMENTE a família tipográfica "Barlow" (qualquer peso: Regular,
     Medium, SemiBold, Bold, Condensed) em TODOS os textos da imagem.
   - NUNCA usar outras fontes (sem serifadas, sem scripts, sem fontes decorativas).

3. PRESENÇA DO VEÍCULO / CARRO DE REFERÊNCIA:
   - Além do produto aplicado na imagem de forma profissional, incluir ao fundo do
     layout a imagem de um carro/modelo de referência do público-alvo do cliente
     (ex: o carro que o cliente costuma atender), para ancoragem visual e
     identificação imediata por parte do público.
   - O carro NÃO precisa ter o produto aplicado nele — o objetivo é apenas referenciar
     o modelo/veículo que o público reconhece como "o carro dele".
   - O carro deve aparecer integrado à cena, em segundo plano, sem competir com o
     produto principal.

4. TRATAMENTO DE TEXTO E CONTRASTE:
   - NUNCA colocar formas geométricas decorativas (retângulos, círculos, faixas
     arbitrárias) atrás do texto como muleta de contraste.
   - O texto deve ser aplicado SOBRE superfícies reais da cena que já ofereçam
     contraste natural (parede, móvel, área escura da composição, etc.).
   - Se NÃO houver superfície natural favorável para o texto, aplicar um degradê
     sutil na cor preta como fundo de contraste — leve, sem virar bloco preto.
   - NUNCA usar sombra projetada (drop shadow) em texto. Para dar contraste, usar
     exclusivamente o degradê escuro descrito acima.

5. ESCALA E MARGENS DA HEADLINE:
   - Headlines NUNCA devem ter escala exagerada ("texto gigante").
   - Usar escala controlada, com margens de segurança generosas nas bordas do layout.
   - O texto deve respirar — nada colado nas laterais, topo ou rodapé.
   - Priorizar legibilidade e hierarquia visual em vez de tamanho bruto.

6. TEXTURAS E ACABAMENTO:
   - Usar SEMPRE texturas leves, modernas, sutis e sofisticadas.
   - NUNCA usar texturas duras, rugosas, granuladas, "grunge", ou que deem aspecto
     "over"/carregado ao layout.
   - O acabamento geral deve transmitir limpeza, modernidade e profissionalismo.

7. REGRAS GERAIS NEGATIVAS (aplicáveis a TODA geração):
   - NUNCA use texto em inglês na imagem — a headline (quando houver) é sempre em
     português.
   - NUNCA gere rostos deformados, mãos com dedos extras/faltando, olhos tortos ou
     anatomia estranha.
   - NUNCA use marcas d'água, assinaturas, selos de "AI generated", logos de terceiros
     ou elementos genéricos de stock photo.
   - NUNCA coloque elementos importantes (texto, logo, rosto, produto) colados nas
     bordas do layout.
   - NUNCA use fundos brancos vazios sem contexto — sempre uma cena/composição
     intencional.
   - NUNCA misture estilos incompatíveis (ex: 3D realista + ilustração flat no mesmo KV).
   - NUNCA invente texto na imagem além da headline informada.
   - NUNCA use paletas fora das cores da marca do cliente.
   - NUNCA mostre o produto de forma irreconhecível ou alterada (quando houver foto real).
   - NUNCA gere imagens com proporção horizontal/paisagem — sempre vertical (retrato).
"""


def _margem_corte_vertical() -> int:
    """Calcula (em %) quanto do topo/rodapé da imagem gerada é removido pelo recorte
    para o formato final, para avisar a IA a deixar uma margem de segurança na
    composição. Soma uma folga extra (2 pontos percentuais) por segurança.

    IMPORTANTE: agora que a imagem final é obtida por REDIMENSIONAMENTO (não mais por
    corte), não há mais perda de topo/rodapé — então esta função retorna 0 e a IA não
    precisa reservar margem de segurança. Mantida por compatibilidade e para o caso de
    você querer voltar ao modo de corte no futuro.
    """
    return 0


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


def _redimensionar_para_formato_final(imagem_bytes: bytes) -> bytes:
    """Redimensiona a imagem gerada pela IA para o formato final (LARGURA_PADRAO x
    ALTURA_PADRAO, ex: 1080x1440) SEM cortar nada — preserva todo o conteúdo desenhado
    pela IA, apenas ajustando a proporção. A distorção é mínima (a API da OpenAI só
    oferece tamanhos fixos como 1024x1536, cuja razão é próxima da final).

    Isso substitui o recorte que era feito antes (que removia topo/rodapé e podia
    cortar texto/logo). Se quiser voltar ao comportamento antigo, é só usar
    image_overlay.compor_imagem_final em vez desta função.
    """
    largura_final = image_overlay.LARGURA_PADRAO
    altura_final = image_overlay.ALTURA_PADRAO

    img = Image.open(BytesIO(imagem_bytes)).convert("RGB")
    img_redimensionada = img.resize((largura_final, altura_final), Image.LANCZOS)

    buffer = BytesIO()
    img_redimensionada.save(buffer, format="PNG")
    return buffer.getvalue()


def gerar_imagem(
    prompt_imagem: str,
    skill: dict,
    produto: Optional[dict] = None,
    usar_referencias_layout: bool = True,
) -> dict:
    """Gera a imagem (com foto real do produto e/ou estilo dos últimos posts, quando
    disponíveis) — a headline já vem desenhada pela própria IA, como parte do brief.
    Redimensiona para o formato final (1080x1440 por padrão) SEM cortar, e cola o logo
    do cliente, se existir. Guarda o resultado como referência de layout para a próxima
    execução."""
    cliente = skill.get("cliente")
    referencias_layout = (
        carregar_referencias_layout(cliente) if (cliente and usar_referencias_layout) else []
    )

    bruta = _gerar_imagem_bruta(prompt_imagem, produto, referencias_layout)
    if not bruta.get("imagem_b64"):
        # Sem base64 (ex: só veio uma URL) não dá pra compor localmente — devolve como veio.
        return bruta

    # Redimensiona para o formato final SEM cortar (substitui o recorte anterior).
    imagem_final_bytes = _redimensionar_para_formato_final(
        base64.b64decode(bruta["imagem_b64"])
    )

    # Aplica o logo do cliente, se houver (usa a função existente do image_overlay,
    # mas agora sem headline e sem corte — a imagem já está no tamanho final).
    imagem_final_bytes = image_overlay.compor_imagem_final(
        imagem_bytes=imagem_final_bytes,
        headline="",  # a headline já foi desenhada pela IA na própria cena
        cores_hex=skill.get("cores_hex") or [],
        cliente=cliente,
    )

    bruta["imagem_b64"] = base64.b64encode(imagem_final_bytes).decode("ascii")
    bruta["tamanho"] = f"{image_overlay.LARGURA_PADRAO}x{image_overlay.ALTURA_PADRAO}"

    if cliente:
        salvar_referencia_layout(cliente, imagem_final_bytes)

    return bruta