# Kav — Automação de Marketing Multi-Agente

Sistema de criação de posts da Kav (@kav.mkt). Um clique cria um post completo para o
cliente: escolhe um produto campeão de vendas da loja dele na Shopee (sem repetir nos
últimos 30 dias), escreve a legenda no padrão do cliente e gera a imagem no layout de
referência dele, com a foto real do produto e o logo. **Nada é postado
automaticamente** — o post fica pronto para você revisar e publicar.

Texto com `gpt-4o-mini` e imagem com o GPT Image 2.5, ambos pela API da OpenAI.

## Como funciona

```
Catálogo  →  escolhe o produto: sorteio entre os 15 mais vendidos ainda não usados em 30 dias
Legenda   →  chamada da imagem + selo do produto + legenda seguindo clientes/<cliente>/legenda.md
Design    →  sorteia 1 das 10 referências de layout do cliente + foto real do produto
             → imagem 1080x1440 → logo aplicado por código na posição daquele layout
Histórico →  registra o produto usado (branch "dados" do GitHub) para não repetir
```

Depois da imagem pronta, o campo **"🔧 Pedir uma alteração nesta imagem"** aplica ajustes
pontuais (ex: "deixe o céu ao entardecer") com o `gpt-image-2.5-sunburst`, mantendo o
resto da imagem fiel. Cada ajuste é mais uma chamada de imagem.

## Estrutura

```
kav-mkt/
├── app.py                    # interface web (Streamlit)
├── orchestrator.py           # o fluxo completo (usado pelo app e pela linha de comando)
├── agents/
│   ├── agente_catalogo.py    # escolhe o produto do post
│   ├── agente_legenda.py     # chamada, selo e legenda no padrão do cliente
│   └── agente_design.py      # brief visual + imagem + ajustes pontuais
├── utils/
│   ├── cliente.py            # carrega a pasta do cliente
│   ├── historico.py          # histórico de posts (GitHub ou arquivo local)
│   ├── image_overlay.py      # recorte 1080x1440 + logo
│   └── openai_client.py      # chamadas à API da OpenAI
└── clientes/
    ├── README.md             # como adicionar cliente e atualizar o catálogo
    └── ponto-car/            # skill, legenda, config, catálogo, logo, referências
```

## Publicar / atualizar no Streamlit Community Cloud

O app já está no ar no Streamlit Cloud, ligado ao repositório do GitHub. Para atualizar:

1. No repositório do GitHub, **apague** as pastas e arquivos que não existem mais (abra
   cada um → menu **⋯** → **Delete file / Delete directory**):
   `skills/`, `assets/`, `data/`, `logs/`, `agents/agente_pauta.py`,
   `agents/agente_produto.py`, `utils/skill_loader.py`.
2. **Add file → Upload files** e arraste o conteúdo novo da pasta `kav-mkt/`
   (incluindo a pasta `clientes/`). Commit.
3. No Streamlit Cloud, em **Settings → Secrets**, confira que tem estas linhas:

   ```toml
   OPENAI_API_KEY = "sua-chave-da-openai"
   GITHUB_TOKEN = "seu-token-do-github"
   GITHUB_REPO = "seu-usuario/kav-mkt"
   APP_PASSWORD = "senha-de-acesso-ao-app"
   ```

### Criar o `GITHUB_TOKEN` (para o histórico de 30 dias)

O disco do Streamlit gratuito é apagado quando o servidor reinicia, então o histórico de
produtos usados fica salvo no próprio repositório, numa branch chamada `dados` (criada
sozinha na primeira vez). O Streamlit só acompanha a branch principal, então gravar lá
não reinicia o app.

1. Acesse [github.com/settings/personal-access-tokens/new](https://github.com/settings/personal-access-tokens/new).
2. **Token name:** `kav-mkt historico`. **Expiration:** o maior prazo disponível.
3. **Repository access:** *Only select repositories* → escolha o repositório do app.
4. **Permissions → Repository permissions → Contents:** *Read and write*.
5. **Generate token**, copie e cole nos Secrets do Streamlit como `GITHUB_TOKEN`
   (não compartilhe o token em chat nem e-mail).

Sem o token o app funciona, mas o histórico some a cada reinício (e produtos podem se
repetir). A barra lateral mostra qual dos dois modos está ativo.

## O que cada cliente precisa ter

Tudo fica em `clientes/<cliente>/` — ver [clientes/README.md](clientes/README.md) para
os detalhes e para adicionar um cliente novo (copiar a pasta e editar).

| Arquivo | Para quê | Ponto Car |
|---|---|---|
| `skill.md` | tom de voz, regras, KV | ✅ pronto (KV descrito a partir das referências) |
| `legenda.md` | padrão de legenda | ✅ pronto (baseado no exemplo do Versa) |
| `config.json` | loja, posição padrão do logo, dias sem repetir | ✅ pronto |
| `catalogo.json` | produtos da loja | ⚠️ vazio — sincronizar via Claude in Chrome |
| `logo-fundo-escuro.png` / `logo-fundo-claro.png` | logo em PNG transparente | ✅ pronto (amarelo/branco e grafite/azul) |
| `referencias/` | até 10 posts de referência de layout | ✅ 10 imagens + posição do logo em cada |

A barra lateral do app mostra esse mesmo checklist para o cliente selecionado.

## Atualizar o catálogo de produtos

O app não navega na Shopee sozinho (a loja bloqueia navegação automática de servidores).
O catálogo é atualizado pedindo ao Claude, no Claude Code, para ler a loja pelo seu
Chrome — o passo a passo e o formato do arquivo estão em
[clientes/README.md](clientes/README.md#atualizar-o-catálogo-claude-in-chrome).

## Rodar no próprio computador (opcional)

```bash
pip install -r requirements.txt
cp .env.example .env   # preencha OPENAI_API_KEY (os demais são opcionais)
streamlit run app.py
```

Ou pela linha de comando: `python orchestrator.py --cliente ponto-car` (salva em `output/`).

## Limitações atuais

- Sem postagem automática — sempre manual.
- O catálogo não se atualiza sozinho: depende de você pedir a sincronização ao Claude.
- A API/Claude não traz a descrição de todos os produtos; sem descrição, a legenda se
  limita ao que está no nome do produto (e nunca inventa compatibilidade).
- A IA de imagem desenha a chamada e o selo; em casos raros o texto pode sair com erro —
  use o campo de ajuste ou crie outro post.
