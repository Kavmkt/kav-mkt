from __future__ import annotations
"""Agente de Estratégia de Campanha (Estrategista de Performance): decide o ângulo de
conversão de maior potencial para UMA peça de tráfego pago (Meta Ads) local, cruzando as
diretrizes de marca do cliente com a inteligência de mercado/concorrência cadastrada em
clientes/<slug>/concorrentes_e_mercado.json (quando existir), e escreve a copy persuasiva
do anúncio (headline de impacto, selo, copy completa com gancho, localização e CTA de
WhatsApp/visita).

Isolado dos agentes de legenda orgânica (agente_legenda_fotos.py e agente_legenda.py):
uma campanha paga tem objetivo diferente de um post de feed — não é sobre engajamento e
sim sobre conversão imediata (pedido/visita hoje), então o tom, a urgência e a estrutura
da copy são outros.
"""
import json

from utils.openai_client import chamar_ia, extrair_json

SYSTEM_PROMPT = """Você é o Estrategista de Performance (tráfego pago) da Kav (@kav.mkt).
Sua função é definir o ângulo de conversão de maior potencial para UM anúncio de Meta Ads
(Instagram/Facebook) de tráfego local, e escrever a copy completa do anúncio.

DIRETRIZES DE MARCA DO CLIENTE:
__SKILL__

INTELIGÊNCIA DE MERCADO E CONCORRÊNCIA (use para diferenciar o anúncio da concorrência
local — se estiver vazia ou marcada como modelo/placeholder, baseie-se só nas diretrizes
de marca acima e não invente concorrente nenhum):
__MERCADO__

Isto é um ANÚNCIO PAGO, não um post orgânico de feed: o objetivo é conversão imediata (o
cliente pedir pelo WhatsApp ou visitar hoje), não curtidas ou engajamento. A copy precisa:
- Abrir com um gancho de alta retenção nos primeiros segundos (dor, desejo ou urgência do
  público local);
- Diferenciar do concorrente local usando a inteligência de mercado, SEM citar nome de
  concorrente nenhum;
- Deixar claro onde fica (bairro/cidade) e como pedir agora (WhatsApp) ou visitar;
- Terminar com uma chamada para ação direta e sem ambiguidade.

Regras:
- Use somente informações reais da foto e das diretrizes de marca. Nunca invente preço,
  ingrediente ou promoção que não esteja informado.
- Localização e forma de pedido devem vir exatamente como estão nas diretrizes de marca.

Responda APENAS com um objeto JSON, sem texto antes ou depois:
{
  "angulo_conversao": "nome curto do ângulo escolhido (ex: 'Fartura a preço justo perto do trabalho')",
  "motivo_estrategico": "1-2 frases explicando por que esse ângulo converte mais para este público/região",
  "headline_impacto": "chamada principal do anúncio: até 8 palavras, sem emoji, focada em conversão",
  "selo_produto": "nome curto do prato para o selo da imagem, até ~40 caracteres, ou null se não houver prato específico",
  "copy_anuncio": "copy completa do anúncio, pronta pra usar como texto do Meta Ads: gancho + diferencial + endereço/região + CTA de WhatsApp/localização",
  "cta": "texto curto e direto da chamada para ação, pra render na própria imagem (ex: 'Peça agora no WhatsApp')"
}
"""

MERCADO_AUSENTE = (
    "(sem inteligência de concorrência cadastrada para este cliente — baseie-se só nas "
    "diretrizes de marca acima)"
)


def definir_estrategia_campanha(cliente: dict, foto: dict) -> dict:
    mercado = _carregar_mercado(cliente["slug"])
    system = SYSTEM_PROMPT.replace("__SKILL__", cliente["skill"]).replace(
        "__MERCADO__", mercado or MERCADO_AUSENTE
    )
    prompt = f"Dados da foto/prato para este anúncio:\n{_descrever(foto)}"
    resposta = chamar_ia(system=system, prompt=prompt, max_tokens=1100, temperature=0.85, json_mode=True)
    return extrair_json(resposta)


def _carregar_mercado(slug: str) -> str:
    from utils.cliente import CLIENTES_DIR

    caminho = CLIENTES_DIR / slug / "concorrentes_e_mercado.json"
    if not caminho.exists():
        return ""
    try:
        dados = json.loads(caminho.read_text(encoding="utf-8"))
    except Exception:
        return ""
    if not isinstance(dados, dict) or "_atencao" in dados:
        # Ainda é o modelo/placeholder (ninguém preencheu com pesquisa real) — ignora,
        # em vez de deixar a IA tratar campos vazios como "sem concorrência nenhuma".
        return ""
    return json.dumps(dados, ensure_ascii=False, indent=2)


def _descrever(foto: dict) -> str:
    campos = [
        ("Nome/prato", foto.get("nome")),
        ("Categoria", foto.get("categoria")),
        ("Preço", foto.get("preco")),
        ("Descrição", foto.get("descricao")),
    ]
    descricao = "\n".join(f"- {rotulo}: {valor}" for rotulo, valor in campos if valor)
    return descricao or f"- Arquivo: {foto['arquivo'].name} (sem metadados cadastrados em fotos.json)"
