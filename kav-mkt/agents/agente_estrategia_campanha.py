"""Agente Estrategista de Performance (Gestor de Tráfego / Mídia Paga).

Responsável por analisar o cliente, a concorrência local mapeada em
clientes/<slug>/concorrentes_e_mercado.json e o momento da conta para conceber
o conceito estratégico de campanhas de alta conversão no Meta Ads.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from utils.openai_client import chamar_ia, extrair_json

SYSTEM_PROMPT = """Você é o Estrategista de Performance e Mídia Paga Sênior da Kav (@kav.mkt).
Sua missão é desenhar a estratégia completa de UMA peça de anúncio no Meta Ads (Feed do Instagram, 4:5) para o cliente NN Restaurante.

CONTEXTO DO CLIENTE:
- O cliente é o NN RESTAURANTE: salão próprio acolhedor, comida caseira brasileira saborosa na Av. Tenente Marques, 4131 - Vila Poupança (Santana de Parnaíba / Cajamar).
- PÚBLICO REAL E FAIXA DE PREÇO: Comida farta de R$ 26 a R$ 35. Trabalhadores, comerciantes, famílias e moradores da região que querem almoço farto, saboroso e com preço justo.
- PROIBIDO USAR A PALAVRA "EXECUTIVO": NUNCA use "executivo" ou "almoço executivo" em headlines, copies ou selos. Use "Almoço do Dia", "Comida Caseira", "Prato Feito" ou o nome do prato.

DIRETRIZES DA MARCA:
__SKILL__

PESQUISA DE MERCADO E CONCORRENTES LOCAIS:
__CONCORRENTES__

FOTO/PRATO SELECIONADO PARA O ANÚNCIO:
__FOTO_INFO__

REGRAS DE CONVERSÃO E PERFORMANCE:
1. **Headline de Alto Impacto (3 a 6 palavras)**:
   - Apelo direto de apetite farto e praticidade para o almoço.
   - NUNCA use clichês vazios ("Sabor de casa", "Comida de verdade").
   - NUNCA use a palavra "executivo".
2. **Hierarquia Visual**:
   - Headline Destaque: Curta, direta, apetitosa.
   - Frase de Apoio: Complemento com benefício tangível (ex: "Arroz soltinho, feijão no capricho e salada à vontade").
   - Selo: Badge de autoridade (ex: "Almoço do Dia", "Feito na Hora", "Prato Feito").
   - CTA Visual: Endereço claro ("Av. Ten. Marques, 4131 — Santana de Parnaíba").

Responda EXCLUSIVAMENTE com um objeto JSON válido, sem texto ou markdown antes ou depois:
{
  "angulo_estrategico": "Nome do ângulo (ex: Almoço Presencial Rápido & Farto)",
  "objetivo_meta_ads": "Tráfego para Salão / Engajamento Local",
  "diferencial_vs_concorrentes": "Explicação objetiva de como este anúncio se destaca",
  "hierarquia_visual": {
    "headline_destaque": "HEADLINE PRINCIPAL IMPACTANTE",
    "headline_apoio": "Frase de apoio secundária com benefício",
    "selo": "Almoço do Dia",
    "cta_visual": "Av. Ten. Marques, 4131 — Santana de Parnaíba"
  },
  "copy_anuncio": {
    "gancho_linha_1": "Linha 1 da legenda do anúncio que para o scroll no feed",
    "corpo": "Texto persuasivo de 2 parágrafos destacando comida fresca, salão acolhedor e preço justo (R$ 26 a R$ 35)",
    "cta_final": "Chamada para ação clara"
  },
  "diretriz_designer": "Instruções cirúrgicas para o Diretor de Arte diagramar a peça sem poluição visual e sem a palavra executivo"
}
"""


def criar_estrategia_campanha(cliente: dict, foto_escolhida: Optional[dict] = None) -> dict:
    pasta = Path(cliente["pasta"])
    arq_mercado = pasta / "concorrentes_e_mercado.json"
    dados_mercado = arq_mercado.read_text(encoding="utf-8") if arq_mercado.exists() else "{}"

    nome_foto = foto_escolhida.get("nome") if foto_escolhida else "Almoço do Dia"
    desc_foto = foto_escolhida.get("descricao", "") if foto_escolhida else ""
    categoria_foto = foto_escolhida.get("categoria") if foto_escolhida else "Almoço do Dia"

    foto_info = (
        f"Prato/Foto: {nome_foto}\n"
        f"Categoria: {categoria_foto}\n"
        f"Detalhes: {desc_foto}"
    )

    system = (
        SYSTEM_PROMPT.replace("__SKILL__", cliente.get("skill", ""))
        .replace("__CONCORRENTES__", dados_mercado)
        .replace("__FOTO_INFO__", foto_info)
    )

    prompt = (
        f"Crie a estratégia completa de anúncio para o prato '{nome_foto}'.\n"
        f"Lembre-se: público popular de R$ 26 a R$ 35, NÃO use a palavra executivo.\n"
        f"Gere o JSON estratégico de performance."
    )

    resposta = chamar_ia(system=system, prompt=prompt, max_tokens=1000, temperature=0.7, json_mode=True)
    return extrair_json(resposta)
