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
# 0.75) pra minimizar a distorção de esticar/encolher no ajuste final (ver
# utils.image_overlay.recortar_formato_final — desde 2026-09-27 ela NÃO corta mais, só
# redimensiona pro tamanho final, então quanto mais próxima a proporção pedida for da
# final, menos distorção visível). "1024x1536" (0.667) é o tamanho de fallback oficial,
# bem mais diferente da proporção final; "1072x1440" (0.744, múltiplo de 16 nos dois
# lados) é bem mais parecido — mas mesmo se a API cair no fallback, não tem mais risco de
# cortar nada, só uma distorção leve.
IMAGE_SIZE = os.environ.get("OPENAI_IMAGE_SIZE", "1072x1440")
# Tamanho "oficial" da API (documentado, sempre aceito) — usado como fallback automático
# se o tamanho customizado acima for rejeitado por algum motivo.
TAMANHO_IMAGEM_SEGURO = "1024x1536"
# "high" é essencial para evitar aspecto emborrachado/waxy em texturas orgânicas e alimentos.
IMAGE_QUALITY = os.environ.get("OPENAI_IMAGE_QUALITY", "high")

_client = None


def get_client() -> OpenAI:
    """Retorna a instância singleton do cliente OpenAI. Lança RuntimeError se a chave
    de API não estiver configurada no ambiente nem nos secrets do Streamlit."""
    global _client
    if _client is not None:
        return _client
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        raise RuntimeError(
            "OPENAI_API_KEY não configurada.\n\n"
            "Localmente: adicione OPENAI_API_KEY=sk-... no arquivo .env na raiz.\n"
            "No Streamlit Cloud: adicione OPENAI_API_KEY = \"sk-...\" em Settings > Secrets."
        )
    _client = OpenAI(api_key=key)
    return _client


def chamar_ia(
    system: str, prompt: str, max_tokens: int = 1000, temperature: float = 0.7, json_mode: bool = False
) -> str:
    """Chama o modelo de texto com um system prompt e um user prompt.
    Retorna o texto da resposta sem espaços nas pontas."""
    client = get_client()
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": prompt},
    ]
    kwargs = {
        "model": MODEL,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}
    resposta = client.chat.completions.create(**kwargs)
    return (resposta.choices[0].message.content or "").strip()


def chamar_ia_visao(
    system: str,
    prompt: str,
    imagem_b64: str,
    max_tokens: int = 1000,
    temperature: float = 0.4,
    json_mode: bool = True,
) -> str:
    """Chama a API de chat da OpenAI com capacidade multimodal (visão computacional).
    Envia a imagem em base64 junto com o prompt textual para inspeção visual."""
    client = get_client()
    messages = [
        {"role": "system", "content": system},
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{imagem_b64}",
                        "detail": "high",
                    },
                },
            ],
        },
    ]
    kwargs = {
        "model": MODEL,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}
    resposta = client.chat.completions.create(**kwargs)
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
    """Gera a imagem do zero a partir de um brief de imagem já pronto e bem definido."""
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
    if "image" not in content_type:
        raise ValueError(f"URL não retornou imagem (Content-Type: {content_type})")
    return resposta.content


def gerar_imagem_com_referencias(prompt: str, imagens_bytes: list, size: Optional[str] = None) -> dict:
    """Gera a imagem usando uma ou mais imagens como referência (layout do cliente, foto
    real do produto, e/ou a própria imagem atual para um ajuste pontual), com alta fidelidade."""
    client = get_client()
    pngs = [_como_png(dados) for dados in imagens_bytes]

    def _chamar(tam):
        arquivos = []
        for indice, dados in enumerate(pngs):
            arquivo = BytesIO(dados)
            arquivo.name = f"referencia_{indice}.png"
            arquivos.append(arquivo)
        kwargs = {
            "model": IMAGE_EDIT_MODEL,
            "image": arquivos,
            "prompt": prompt,
            "size": tam,
            "quality": IMAGE_QUALITY,
        }
        # Tenta com input_fidelity="high" para preservar detalhes fotográficos reais e logo oficial
        try:
            return client.images.edit(**kwargs, input_fidelity="high")
        except TypeError:
            return client.images.edit(**kwargs)
        except Exception as exc:
            if "input_fidelity" in str(exc):
                return client.images.edit(**kwargs)
            raise

    tamanho_pedido = size or IMAGE_SIZE
    resposta, tamanho_usado = _chamar_com_fallback_tamanho(
        _chamar, tamanho_pedido, usar_fallback=(size is None)
    )
    return _resultado_imagem(resposta.data[0], IMAGE_EDIT_MODEL, tamanho_usado)


def _como_png(dados: bytes, lado_max: int = 1536) -> bytes:
    """Converte qualquer imagem (JPG/WEBP da Shopee, referências grandes) para PNG de no
    máximo `lado_max` px — formato aceito pela API e envio mais leve."""
    imagem = Image.open(BytesIO(dados))
    imagem = imagem.convert("RGBA" if imagem.mode in ("RGBA", "LA", "P") else "RGB")
    imagem.thumbnail((lado_max, lado_max))
    saida = BytesIO()
    imagem.save(saida, format="PNG")
    return saida.getvalue()


def _resultado_imagem(dado, modelo: str, tamanho_pedido: str) -> dict:
    """Monta o dicionário de retorno padrão — incluindo `tamanho_real`, medido na imagem
    que veio de verdade, nunca assumido a partir do que foi pedido."""
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


def extrair_json(texto: str) -> dict:
    """Extrai um objeto JSON de uma resposta da IA, mesmo se vier com texto/markdown ao redor."""
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", texto, re.DOTALL)
    if match:
        texto = match.group(1)
    else:
        abertura = texto.find("{")
        fechamento = texto.rfind("}")
        if abertura != -1 and fechamento != -1 and fechamento > abertura:
            texto = texto[abertura : fechamento + 1]
    return json.loads(texto)
