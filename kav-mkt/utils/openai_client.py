"""Cliente compartilhado para chamadas à API da OpenAI: texto (gpt-4o-mini) e imagem
(GPT Image 2.5).

Centralizado aqui para que os agentes (Legenda, Design) não dupliquem a leitura da chave
de API nem a lógica de extração de JSON da resposta.
"""
import base64
import json
import os
import re
from io import BytesIO
from typing import Optional

import requests
from openai import OpenAI
from PIL import Image

MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
# "flare" = geração rápida do zero. "sunburst" = mais precisa, usada quando há imagens de
# referência (layout do cliente e/ou foto real do produto), onde fidelidade importa mais.
IMAGE_MODEL = os.environ.get("OPENAI_IMAGE_MODEL", "gpt-image-2.5-flare")
IMAGE_EDIT_MODEL = os.environ.get("OPENAI_IMAGE_EDIT_MODEL", "gpt-image-2.5-sunburst")
# Tamanho pedido à API. Escolhido o mais próximo possível da proporção final (1080x1440 =
# 0.75) porque o recorte final (utils.image_overlay.recortar_formato_final) sempre corta
# uma faixa do topo/rodapé (ou dos lados) pra chegar nessa proporção — quanto mais
# parecida a proporção pedida for da final, MENOR essa faixa cortada, e menos qualquer
# margem de segurança (por menor imprecisão da IA) acaba sendo engolida pelo corte.
# "1024x1536" (0.667) tinha ~5.6% de corte no topo E no rodapé — quase do tamanho da
# própria margem de segurança pedida (6-8%), então bastava a IA errar por pouco pra
# cortar o logo/texto (bug visto em 2026-09-23). "1072x1440" (0.744, múltiplo de 16 nos
# dois lados) deixa esse corte em ~0.4% — folga bem maior.
IMAGE_SIZE = os.environ.get("OPENAI_IMAGE_SIZE", "1072x1440")
# Tamanho "oficial" da API (documentado, sempre aceito) — usado como fallback automático
# se o tamanho customizado acima for rejeitado por algum motivo.
TAMANHO_IMAGEM_SEGURO = "1024x1536"
# "low" gasta bem menos crédito que "high" — "medium" é o meio-termo padrão.
IMAGE_QUALITY = os.environ.get("OPENAI_IMAGE_QUALITY", "medium")

_client = None


def get_client() -> OpenAI:
    global _client
    if _client is None:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "OPENAI_API_KEY não definida. Configure a variável de ambiente "
                "(veja .env.example) antes de rodar o orchestrator."
            )
        _client = OpenAI(api_key=api_key)
    return _client


def chamar_ia(
    system: str,
    prompt: str,
    max_tokens: int = 1024,
    temperature: float = 0.7,
    json_mode: bool = False,
) -> str:
    """Faz uma chamada de texto simples ao modelo da OpenAI e retorna o texto da resposta.

    Args:
        json_mode: quando True, pede ao modelo para responder em JSON estruturado (usa o
            recurso nativo `response_format` da OpenAI), reduzindo a chance de a resposta
            vir com texto extra ao redor do JSON.
    """
    client = get_client()
    kwargs = {}
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}
    resposta = client.chat.completions.create(
        model=MODEL,
        max_tokens=max_tokens,
        temperature=temperature,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        **kwargs,
    )
    return (resposta.choices[0].message.content or "").strip()


def _chamar_com_fallback_tamanho(chamar, tamanho_pedido: str, usar_fallback: bool):
    """Executa `chamar(tamanho)`; se falhar e `tamanho_pedido` for o tamanho customizado
    (não o oficial), tenta de novo com `TAMANHO_IMAGEM_SEGURO` antes de desistir — a API
    pode rejeitar um tamanho fora da lista documentada, e sem esse fallback a chamada
    inteira falharia (perdendo as referências) por causa só do `size`."""
    try:
        return chamar(tamanho_pedido), tamanho_pedido
    except Exception:
        if not usar_fallback or tamanho_pedido == TAMANHO_IMAGEM_SEGURO:
            raise
        return chamar(TAMANHO_IMAGEM_SEGURO), TAMANHO_IMAGEM_SEGURO


def gerar_imagem(prompt: str) -> dict:
    """Gera a imagem do zero a partir de um brief de imagem já pronto e bem definido.

    Faz UMA única chamada à API de imagem da OpenAI (duas só se o tamanho customizado for
    rejeitado, ver `_chamar_com_fallback_tamanho`) — o prompt deve chegar completo e
    específico, sem necessidade de iteração, para não gastar créditos à toa com
    tentativas repetidas.
    """
    client = get_client()
    resposta, tamanho_usado = _chamar_com_fallback_tamanho(
        lambda tam: client.images.generate(
            model=IMAGE_MODEL, prompt=prompt, size=tam, quality=IMAGE_QUALITY, n=1
        ),
        IMAGE_SIZE,
        usar_fallback=True,
    )
    return _resultado_imagem(resposta.data[0], IMAGE_MODEL, tamanho_usado)


def baixar_imagem_referencia(url: str) -> bytes:
    """Baixa os bytes da foto de um produto do catálogo para usar como referência na
    geração com edição. Lança exceção se a URL não for uma imagem válida/acessível — o
    chamador deve tratar isso com um fallback."""
    resposta = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
    resposta.raise_for_status()
    content_type = resposta.headers.get("Content-Type", "")
    if "image" not in content_type and not url.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
        raise ValueError(f"O link não parece ser uma imagem direta (Content-Type: {content_type!r}).")
    return resposta.content


def gerar_imagem_com_referencias(prompt: str, imagens_bytes: list, size: Optional[str] = None) -> dict:
    """Gera a imagem usando uma ou mais imagens como referência (layout do cliente, foto
    real do produto, e/ou a própria imagem atual para um ajuste pontual), em vez de
    descrever tudo só por texto.

    Faz UMA única chamada à API de edição de imagem da OpenAI, com todas as referências
    enviadas juntas (a API do GPT Image aceita até 16 imagens numa única edição).

    Args:
        size: normalmente omitido (usa IMAGE_SIZE). Passe "auto" quando a imagem de
            referência já estiver no formato final (ex: ajuste pontual sobre uma imagem
            já composta), pra API não tentar redimensionar/distorcer pra IMAGE_SIZE.
    """
    client = get_client()
    pngs = [_como_png(dados) for dados in imagens_bytes]

    def _chamar(tam):
        # Reconstrói os arquivos a cada tentativa — um BytesIO já lido (tentativa
        # anterior) chegaria vazio na chamada de retry.
        arquivos = []
        for indice, dados in enumerate(pngs):
            arquivo = BytesIO(dados)
            arquivo.name = f"referencia_{indice}.png"
            arquivos.append(arquivo)
        return client.images.edit(
            model=IMAGE_EDIT_MODEL, image=arquivos, prompt=prompt, size=tam, quality=IMAGE_QUALITY
        )

    tamanho_pedido = size or IMAGE_SIZE
    resposta, tamanho_usado = _chamar_com_fallback_tamanho(
        _chamar, tamanho_pedido, usar_fallback=(size is None)
    )
    return _resultado_imagem(resposta.data[0], IMAGE_EDIT_MODEL, tamanho_usado)


def _resultado_imagem(dado, modelo: str, tamanho_pedido: str) -> dict:
    """Monta o dicionário de retorno padrão — incluindo `tamanho_real`, medido na imagem
    que veio de verdade, nunca assumido a partir do que foi pedido. A API às vezes não
    devolve exatamente o `size` pedido (principalmente com múltiplas imagens de
    referência de proporções diferentes), e um código que assume "pedido = real" gera
    margens de segurança erradas para a IA — foi exatamente esse o bug que cortava texto
    no topo das imagens (visto em 2026-09-23)."""
    b64 = getattr(dado, "b64_json", None)
    tamanho_real = None
    if b64:
        try:
            largura, altura = Image.open(BytesIO(base64.b64decode(b64))).size
            tamanho_real = f"{largura}x{altura}"
        except Exception:
            tamanho_real = None
    return {
        "imagem_b64": b64,
        "imagem_url": getattr(dado, "url", None),
        "modelo": modelo,
        "tamanho_pedido": tamanho_pedido,
        "tamanho_real": tamanho_real,
        "qualidade": IMAGE_QUALITY,
    }


def _como_png(dados: bytes, lado_max: int = 1536) -> bytes:
    """Converte qualquer imagem (JPG/WEBP da Shopee, referências grandes) para PNG de no
    máximo `lado_max` px — formato aceito pela API e envio mais leve."""
    imagem = Image.open(BytesIO(dados))
    imagem = imagem.convert("RGBA" if imagem.mode in ("RGBA", "LA", "P") else "RGB")
    imagem.thumbnail((lado_max, lado_max))
    saida = BytesIO()
    imagem.save(saida, format="PNG")
    return saida.getvalue()


def extrair_json(texto: str) -> dict:
    """Extrai um objeto JSON de uma resposta da IA, mesmo se vier com texto/markdown ao redor."""
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", texto, re.DOTALL)
    bruto = match.group(1) if match else texto
    inicio = bruto.find("{")
    fim = bruto.rfind("}")
    if inicio == -1 or fim == -1:
        raise ValueError(f"Não foi possível localizar JSON na resposta da IA: {texto[:200]!r}")
    return json.loads(bruto[inicio : fim + 1])
