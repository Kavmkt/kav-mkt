"""Cliente compartilhado para chamadas à API da OpenAI: texto (gpt-4o-mini) e imagem
(GPT Image 2.5).

Centralizado aqui para que os agentes (Pauta, Design) não dupliquem a leitura da chave
de API nem a lógica de extração de JSON da resposta.
"""
import json
import os
import re
from io import BytesIO

import requests
from openai import OpenAI

MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
# "flare" = geração rápida do zero. "sunburst" = mais precisa, usada quando há uma foto
# de referência real do produto (edição/composição), onde manter fidelidade importa mais.
IMAGE_MODEL = os.environ.get("OPENAI_IMAGE_MODEL", "gpt-image-2.5-flare")
IMAGE_EDIT_MODEL = os.environ.get("OPENAI_IMAGE_EDIT_MODEL", "gpt-image-2.5-sunburst")
# Tamanho pedido à API (o recorte exato pro formato final de 1080x1440 acontece depois,
# em utils.image_overlay — isso aqui só evita gerar numa proporção muito diferente).
IMAGE_SIZE = os.environ.get("OPENAI_IMAGE_SIZE", "1024x1536")
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


def gerar_imagem(prompt: str) -> dict:
    """Gera a imagem do zero a partir de um brief de imagem já pronto e bem definido.

    Faz UMA única chamada à API de imagem da OpenAI — o prompt deve chegar completo e
    específico, sem necessidade de iteração, para não gastar créditos à toa com
    tentativas repetidas.
    """
    client = get_client()
    resposta = client.images.generate(
        model=IMAGE_MODEL,
        prompt=prompt,
        size=IMAGE_SIZE,
        quality=IMAGE_QUALITY,
        n=1,
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
    """Baixa os bytes de uma foto de produto (ex: link colado no formulário) para usar
    como referência na geração com edição. Lança exceção se a URL não for uma imagem
    válida/acessível — o chamador deve tratar isso com um fallback."""
    resposta = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
    resposta.raise_for_status()
    content_type = resposta.headers.get("Content-Type", "")
    if "image" not in content_type and not url.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
        raise ValueError(f"O link não parece ser uma imagem direta (Content-Type: {content_type!r}).")
    return resposta.content


def gerar_imagem_com_referencia(prompt: str, foto_bytes: bytes) -> dict:
    """Gera a imagem usando a FOTO REAL do produto como referência (edição/composição),
    em vez de descrever o produto só por texto — preserva a aparência real dele.

    Faz UMA única chamada à API de edição de imagem da OpenAI.
    """
    client = get_client()
    arquivo = BytesIO(foto_bytes)
    arquivo.name = "produto_referencia.png"
    resposta = client.images.edit(
        model=IMAGE_EDIT_MODEL,
        image=[arquivo],
        prompt=prompt,
        size=IMAGE_SIZE,
        quality=IMAGE_QUALITY,
    )
    dado = resposta.data[0]
    return {
        "imagem_b64": getattr(dado, "b64_json", None),
        "imagem_url": getattr(dado, "url", None),
        "modelo": IMAGE_EDIT_MODEL,
        "tamanho": IMAGE_SIZE,
        "qualidade": IMAGE_QUALITY,
        "com_referencia": True,
    }


def extrair_json(texto: str) -> dict:
    """Extrai um objeto JSON de uma resposta da IA, mesmo se vier com texto/markdown ao redor."""
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", texto, re.DOTALL)
    bruto = match.group(1) if match else texto
    inicio = bruto.find("{")
    fim = bruto.rfind("}")
    if inicio == -1 or fim == -1:
        raise ValueError(f"Não foi possível localizar JSON na resposta da IA: {texto[:200]!r}")
    return json.loads(bruto[inicio : fim + 1])
