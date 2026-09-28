"""Agente Diretor de Arte & Layout de Campanha.

Especialista em design visual de anúncios de alta performance para redes sociais.
Recebe o briefing estratégico do Agente de Performance e projeta uma peça publicitária
de altíssimo nível em formato 4:5 (1080x1440), aplicando rigorosa hierarquia visual:
- Texto com destaque principal em tamanho imponente (Headline)
- Texto secundário de apoio elegante e de alta legibilidade
- Selo/Badge do prato em cor de destaque (âmbar/dourado #EEB730 ou vermelho #A31D1D)
- Logotipo oficial da N&N diagramado com respiro e fidelidade total
- A comida real como grande protagonista apetitosa da cena.
- PROIBIDO o termo "executivo" (preço popular acessível de R$ 26 a R$ 35).
"""
from __future__ import annotations

import base64
from pathlib import Path
from typing import Optional

from agents.agente_design import _margem_corte_vertical, MARGEM_SEGURANCA_BORDA
from utils import image_overlay, openai_client
from utils.openai_client import chamar_ia

SYSTEM_PROMPT = """Você é o Diretor de Arte Sênior de Performance da Kav (@kav.mkt).
Sua especialidade é criar artes para anúncios no Instagram/Meta Ads com altíssima taxa de conversão e estética refinada para o setor de gastronomia.

DIRETRIZES DE MARCA:
__SKILL__

HIERARQUIA TIPOGRÁFICA & CONTRASTE (REGRA INEGOCIÁVEL):
O cliente N&N exige contraste nítido e hierarquia visual bem demarcada:
1. **DESTAQUE PRINCIPAL**: A headline "__HEADLINE__" deve ser desenhada com grande peso visual, letras expressivas e impactantes (estilo fonte serifada clássica/editorial marcante em cor clara de alto contraste). Ela deve saltar aos olhos imediatamente.
2. **TEXTO DE APOIO**: A frase secundária "__APOIO__" deve ter tamanho menor e visual mais discreto e limpo, sem disputar atenção com a headline principal.
3. **SELO DE OFERTA/AUTORIDADE**: O selo "__SELO__" fica em formato de badge ou etiqueta elegante nas cores de destaque da marca (#EEB730 Dourado ou #A31D1D Vermelho). NUNCA use a palavra "executivo".
4. **LOCALIZAÇÃO**: Indicação limpa e legível de endereço: "__CTA_LOCAL__".
5. **MARCA OFICIAL**: O logotipo oficial da empresa (fornecido na imagem de referência de logo) deve ser diagramado no topo/cabeçalho, integrado com harmonia e respirando confortavelmente (mínimo de 5% de distância de qualquer borda).

REGRA DE TERMOS:
- PROIBIDO USAR A PALAVRA "EXECUTIVO": NUNCA use a palavra "executivo" ou "almoço executivo" na arte. O preço médio do restaurante é de R$ 26 a R$ 35. Use "ALMOÇO DO DIA", "COMIDA CASEIRA" ou "PRATO FEITO".

CENA E PRATO:
- O prato real ou do dia enviado como referência é a BASE da peça: a comida deve permanecer farta, suculenta, apetitosa e autêntica.
- O tratamento gráfico (faixas, blocos de texto, selo) envolve a foto sem nunca tampar o prato principal.

Retorne APENAS um único parágrafo denso em inglês com o brief de direção de arte detalhado, pronto para o modelo de geração de imagem.
"""


def montar_brief_layout(estrategia: dict, foto: dict, cliente: dict) -> str:
    hierarquia = estrategia.get("hierarquia_visual", {})
    headline = hierarquia.get("headline_destaque", "SABOR DE CASA")
    apoio = hierarquia.get("headline_apoio", "Comida caseira no capricho")
    selo = hierarquia.get("selo", "Almoço do Dia")
    selo = selo.replace("Executivo", "do Dia").replace("executivo", "do Dia")
    cta_local = hierarquia.get("cta_visual", "Alameda das Garças, 45 — Santana de Parnaíba")

    nome_prato = foto.get("nome") or (foto["arquivo"].stem if foto.get("arquivo") else "Prato do Dia")

    system = (
        SYSTEM_PROMPT.replace("__SKILL__", cliente.get("skill", ""))
        .replace("__HEADLINE__", headline)
        .replace("__APOIO__", apoio)
        .replace("__SELO__", selo)
        .replace("__CTA_LOCAL__", cta_local)
    )

    partes = [
        f"Prato/Foto Herói: {nome_prato}",
        f"Ângulo Estratégico: {estrategia.get('angulo_estrategico', 'Almoço Presencial')}",
        f"Instruções de Performance: {estrategia.get('diretriz_designer', '')}",
        f'Renderizar Headline em destaque: "{headline}"',
        f'Renderizar Apoio secundário: "{apoio}"',
        f'Renderizar Selo (sem palavra executivo): "{selo}"',
        f'Renderizar Endereço: "{cta_local}"',
        "Garantir hierarquia perfeita entre o texto principal grande e o apoio menor.",
        "Reproduzir fielmente o logotipo oficial fornecido na imagem de referência no topo/cabeçalho.",
        "PROIBIDO renderizar a palavra executivo.",
    ]

    return chamar_ia(system=system, prompt="\n".join(partes), max_tokens=700, temperature=0.7)


def gerar_arte_campanha(brief: str, foto: dict, cliente: dict, estrategia: dict) -> dict:
    """Renderiza a arte final de campanha com foto real e logo oficial do cliente."""
    referencias = []

    # 1. Se tiver foto real, inclui
    if foto.get("arquivo") and not foto.get("foto_virtual"):
        referencias.append((
            foto["arquivo"].read_bytes(),
            "the REAL food photograph to be used as the base scene. Keep the dish and food completely authentic, delicious and recognizable; apply the high-contrast graphic design and typography layout over it.",
        ))

    # 2. Logotipo oficial
    logo_arquivo = None
    if cliente.get("logo_referencias"):
        logo_arquivo = cliente["logo_referencias"][0]
    elif cliente.get("logo"):
        logo_arquivo = cliente["logo"]
    else:
        from agents.agente_design_fotos import _logo
        logo_arquivo, _ = _logo(cliente, None)

    if logo_arquivo:
        referencias.append((
            logo_arquivo.read_bytes(),
            "the official client BRAND LOGO. Faithfully reproduce this exact logo into the header/top branding area with clean contrast and safe margins.",
        ))

    if referencias:
        imagens = [bytes_data for bytes_data, _ in referencias]
        prompt_completo = (
            "\n\n".join(f"Reference image {i + 1} is {desc}" for i, desc in enumerate([d for _, d in referencias]))
            + f"\n\nHigh-Performance Ad Creative for Instagram/Meta Ads (Vertical 4:5):\n{brief}"
        )
        bruta = openai_client.gerar_imagem_com_referencias(prompt_completo, imagens)
    else:
        bruta = openai_client.gerar_imagem(brief)

    final_bytes = image_overlay.recortar_formato_final(base64.b64decode(bruta["imagem_b64"]))

    return {
        "imagem_b64": base64.b64encode(final_bytes).decode("ascii"),
        "tamanho": f"{image_overlay.LARGURA_PADRAO}x{image_overlay.ALTURA_PADRAO}",
        "modelo": bruta.get("modelo"),
    }
