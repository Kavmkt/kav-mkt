"""Agente Diretor de Arte & Layout de Campanha.

Especialista em design visual de anúncios de alta performance para redes sociais.
Recebe o briefing estratégico do Agente de Performance e projeta uma peça publicitária
de altíssimo nível em formato 4:5 (1080x1440), aplicando rigorosa hierarquia visual:
- Texto com destaque principal em tamanho imponente (Headline)
- Texto secundário de apoio elegante e de alta legibilidade
- Selo/Badge do prato em cor de destaque (âmbar/dourado #EEB730 ou vermelho #A31D1D)
- Logotipo oficial da N&N diagramado com respiro e fidelidade total
- A comida real como grande protagonista apetitosa da cena.
"""
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
3. **SELO DE OFERTA/AUTORIDADE**: O selo "__SELO__" fica em formato de badge ou etiqueta elegante nas cores de destaque da marca (#EEB730 Dourado ou #A31D1D Vermelho).
4. **LOCALIZAÇÃO**: Indicação limpa e legível de endereço: "__CTA_LOCAL__".
5. **MARCA OFICIAL**: O logotipo oficial da empresa (fornecido na imagem de referência de logo) deve ser diagramado no topo/cabeçalho, integrado com harmonia e respirando confortavelmente (mínimo de 5% de distância de qualquer borda).

CENA E FOTO REAL:
- A foto real enviada como referência é a BASE da peça: a comida/buffet deve permanecer suculenta, apetitosa e autêntica.
- O tratamento gráfico (faixas, blocos de texto, selo) envolve a foto sem nunca tampar o prato principal.

Retorne APENAS um único parágrafo denso em inglês com o brief de direção de arte detalhado, pronto para o modelo de geração de imagem.
"""


def montar_brief_layout(estrategia: dict, foto: dict, cliente: dict) -> str:
    hierarquia = estrategia.get("hierarquia_visual", {})
    headline = hierarquia.get("headline_destaque", "SABOR DE CASA")
    apoio = hierarquia.get("headline_apoio", "Comida caseira no capricho")
    selo = hierarquia.get("selo", "Buffet Executivo")
    cta_local = hierarquia.get("cta_visual", "Alameda das Garças, 45 — Santana de Parnaíba")

    system = (
        SYSTEM_PROMPT.replace("__SKILL__", cliente.get("skill", ""))
        .replace("__HEADLINE__", headline)
        .replace("__APOIO__", apoio)
        .replace("__SELO__", selo)
        .replace("__CTA_LOCAL__", cta_local)
    )

    partes = [
        f"Prato/Foto Herói: {foto.get('nome') or foto['arquivo'].name}",
        f"Ângulo Estratégico: {estrategia.get('angulo_estrategico', 'Almoço Presencial')}",
        f"Instruções de Performance: {estrategia.get('diretriz_designer', '')}",
        f'Renderizar Headline em destaque: "{headline}"',
        f'Renderizar Apoio secundário: "{apoio}"',
        f'Renderizar Selo: "{selo}"',
        f'Renderizar Endereço: "{cta_local}"',
        "Garantir hierarquia perfeita entre o texto principal grande e o apoio menor.",
        "Reproduzir fielmente o logotipo oficial fornecido na imagem de referência no topo/cabeçalho.",
    ]

    return chamar_ia(system=system, prompt="\n".join(partes), max_tokens=700, temperature=0.7)


def gerar_arte_campanha(brief: str, foto: dict, cliente: dict, estrategia: dict) -> dict:
    """Renderiza a arte final de campanha com foto real e logo oficial do cliente."""
    referencias = [(
        foto["arquivo"].read_bytes(),
        "the REAL food photograph to be used as the base scene. Keep the dish and food completely authentic, delicious and recognizable; apply the high-contrast graphic design and typography layout over it.",
    )]

    # Inclui o logotipo oficial do cliente se disponível
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

    imagens = [bytes_data for bytes_data, _ in referencias]
    prompt_completo = (
        f"Reference 1 is the authentic dish photo. Reference 2 is the official brand logo.\n\n"
        f"High-Performance Ad Creative for Instagram/Meta Ads (Vertical 4:5):\n{brief}"
    )

    bruta = openai_client.gerar_imagem_com_referencias(prompt_completo, imagens)
    final_bytes = image_overlay.recortar_formato_final(base64.b64decode(bruta["imagem_b64"]))

    return {
        "imagem_b64": base64.b64encode(final_bytes).decode("ascii"),
        "tamanho": f"{image_overlay.LARGURA_PADRAO}x{image_overlay.ALTURA_PADRAO}",
        "modelo": bruta.get("modelo"),
    }
