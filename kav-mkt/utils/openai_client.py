"""Cliente compartilhado para chamadas à API da OpenAI: texto (gpt-4o-mini) e imagem
(GPT Image 2.5).

A chave de API precisa estar na variável de ambiente OPENAI_API_KEY (ou nos secrets do
Streamlit Cloud).
"""
import base64
from io import BytesIO
import json
import os
from pathlib import Path
import re
from typing import Optional

from openai import OpenAI
from PIL import Image
import requests

# Carrega variáveis de ambiente automaticamente a partir do arquivo .env
try:
    from dotenv import load_dotenv
    _raiz_kav = Path(__file__).resolve().parent.parent
    load_dotenv(_raiz_kav / ".env")
    load_dotenv(_raiz_kav.parent / ".env")
    load_dotenv()
except Exception:
    pass

MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
# "flare" = geração rápida do zero. "sunburst" = mais precisa, usada quando há imagens de
# referência (layout do cliente e/ou foto real do produto), onde fidelidade importa mais.
IMAGE_MODEL = os.environ.get("OPENAI_IMAGE_MODEL", "gpt-image-2.5-flare")
IMAGE_EDIT_MODEL = os.environ.get("OPENAI_IMAGE_EDIT_MODEL", "gpt-image-2.5-sunburst")
# Tamanho pedido à API (o recorte exato pro formato final de 1080x1440 acontece depois,
# em utils/image_overlay.py; a API aceita 1024x1024, 1024x1536 ou 1536x1024).
IMAGE_SIZE = os.environ.get("OPENAI_IMAGE_SIZE", "1024x1536")
TAMANHO_IMAGEM_SEGURO = "1024x1536"
IMAGE_QUALITY = os.environ.get("OPENAI_IMAGE_QUALITY", "medium")

_client: Optional[OpenAI] = None


def get_client() -> OpenAI:
    """Retorna a instância singleton do cliente OpenAI. Lança RuntimeError se a chave
    de API não estiver configurada no ambiente nem nos secrets do Streamlit."""
    global _client
    if _client is not None:
        return _client
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        try:
            from dotenv import load_dotenv
            _raiz_kav = Path(__file__).resolve().parent.parent
            load_dotenv(_raiz_kav / ".env")
            load_dotenv(_raiz_kav.parent / ".env")
            load_dotenv()
            key = os.environ.get("OPENAI_API_KEY")
        except Exception:
            pass
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


def gerar_imagem(prompt: str) -> dict:
    """Gera uma imagem do zero a partir do brief em texto."""
    client = get_client()
    resposta = client.images.generate(
        model=IMAGE_MODEL,
        prompt=prompt,
        size=IMAGE_SIZE,
        quality=IMAGE_QUALITY,
    )
    dado = resposta.data[0]
    return {
        "imagem_b64": getattr(dado, "b64_json", None),
        "imagem_url": getattr(dado, "url", None),
        "modelo": IMAGE_MODEL,
        "tamanho": IMAGE_SIZE,
        "qualidade": IMAGE_QUALITY,
    }


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
    real do produto, e/ou a própria imagem atual para um ajuste pontual), em vez de
    descrever tudo só por texto."""
    client = get_client()
    pngs = [_como_png(dados) for dados in imagens_bytes]

    def _chamar(tam):
        arquivos = []
        for indice, dados in enumerate(pngs):
            arquivo = BytesIO(dados)
            arquivo.name = f"referencia_{indice}.png"
            arquivos.append(arquivo)
        return client.images.edit(
            model=IMAGE_EDIT_MODEL,
            image=arquivos,
            prompt=prompt,
            size=tam,
            quality=IMAGE_QUALITY,
        )

    tamanho_usado = size or IMAGE_SIZE
    resposta = _chamar(tamanho_usado)
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
            with Image.open(BytesIO(base64.b64decode(b64))) as img:
                tamanho_real = f"{img.width}x{img.height}"
        except Exception:
            pass
    return {
        "imagem_b64": b64,
        "imagem_url": getattr(dado, "url", None),
        "modelo": modelo,
        "tamanho_pedido": tamanho_pedido,
        "tamanho_real": tamanho_real,
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
