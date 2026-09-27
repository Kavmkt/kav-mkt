# Kav — Escritório Virtual de Agentes de IA

Ambiente visual interativo da agência **Kav (@kav.mkt)** que representa o sistema multi-agente
como um escritório virtual com avatares e estações de trabalho.

Construído como uma ferramenta de **vendas e apresentação** para impressionar clientes e
demonstrar visualmente o time de inteligência artificial trabalhando em tempo real.

---

## Conceito: Novo Agente = Novo Avatar = Novo Funcionário

Cada especialista no pipeline da Kav possui um posto de trabalho e uma identidade no escritório:

| Avatar | Funcionário | Cargo | Função no Pipeline |
|---|---|---|---|
| 👑 | **Sofia** | Head de Inteligência & Estratégia | Supervisor: cruza métricas com conteúdo e emite alertas |
| 📊 | **Marcos** | Analista de Tráfego & Performance | Métricas: coleta dados do Meta Ads (gasto, cliques, WhatsApp) |
| ✍️ | **Beatriz** | Redatora & Copywriter | Legenda: escreve headlines, selos e copies no padrão da marca |
| 🎨 | **Lucas** | Diretor de Arte & Designer | Design: diagrama layouts 1080x1440 mantendo fotos reais |
| 🗂️ | **Enzo** | Curador de Acervo & Catálogo | Catálogo/Fotos: sorteia fotos/produtos sem repetições |

---

## Como Abrir e Apresentar

O escritório é um aplicativo web 100% estático, desacoplado do Streamlit:

1. **Localmente no seu computador**:
   Basta abrir o arquivo `escritorio-kav/index.html` em qualquer navegador (Chrome, Safari, Edge).
   Ou, se preferir rodar com servidor local:
   ```bash
   cd escritorio-kav
   python3 -m http.server 8080
   ```
   Acesse: `http://localhost:8080`

2. **Em reuniões de vendas**:
   - Clique em **"⚡ Simular Ciclo de Trabalho"** no canto superior direito para demonstrar aos clientes o fluxo em cadeia: a curadoria selecionando o prato, a redação criando o texto, o design montando a arte, a performance monitorando anúncios e a supervisão emitindo diagnósticos.
   - Clique em qualquer mesa/avatar para abrir o **Crachá do Funcionário** com status e histórico detalhado.

---

## Integração com o Motor Python

O escritório é desacoplado do Streamlit: ele lê o estado a partir de `escritorio-kav/estado_agentes.json`.
No Python, o módulo `kav-mkt/utils/estado_agentes.py` permite que qualquer agente atualize sua fala e status em tempo real durante a execução:

```python
from utils import estado_agentes

estado_agentes.atualizar_agente(
    "supervisor",
    status="alerta",
    fala="53 conversas no WhatsApp nos últimos 30 dias!",
    atividade="Supervisionando conta do cliente"
)
```
