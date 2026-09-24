# Clientes

Cada cliente é uma pasta aqui dentro. Tudo o que é específico do cliente mora nela, então
**um cliente novo do mesmo nicho = copiar a pasta de um existente e editar**.

```
clientes/<slug-do-cliente>/
├── skill.md        # tom de voz, público, regras (pode/não pode), KV, produtos coringa
├── legenda.md      # padrão de legenda que o Agente de Legenda segue à risca
├── config.json     # nome, loja da Shopee, posição do logo, dias sem repetir produto
├── catalogo.json   # produtos da loja (sincronizado via Claude in Chrome — ver abaixo)
├── logo-fundo-escuro.png  # logo claro, para layouts de fundo escuro (PNG transparente)
├── logo-fundo-claro.png   # logo escuro, para layouts de fundo claro (PNG transparente)
└── referencias/    # até 10 posts de referência de layout + referencias.json
```

Se o cliente só tiver uma versão do logo, salve como `logo.png` — ela é usada nos dois
casos. `referencias/referencias.json` diz onde fica o logo em cada layout e qual versão
usar (ver `referencias/README.md`).

## Cliente de carrossel (ex: `kav/`)

Além do cliente "de produto" (Catálogo → Legenda → Imagem, ex: `ponto-car/`), o app
também suporta cliente "de conteúdo" — carrossel de 1 a 7 páginas (Pauta → Roteiro →
Imagens), usado hoje pelo cliente `kav/` (posts da própria Kav no Instagram). O que
muda:

| Arquivo | No cliente de produto | No cliente de carrossel |
|---|---|---|
| `config.json` | — | tem `"tipo": "carrossel"` (é isso que o app usa pra saber qual fluxo mostrar) |
| `catalogo.json` | produtos da loja | não usado |
| `pautas.json` | não usado | temas do carrossel (ver `clientes/kav/pautas.json` como exemplo) |
| `legenda.md` | padrão de legenda de produto | não usado |
| `carrossel.md` | não usado | padrão de estrutura do carrossel + legenda |
| `referencias/` | opcional | opcional (sem elas, a 1ª página/capa define o estilo e as seguintes seguem ela) |

O seletor de cliente na barra lateral do app funciona igual para os dois tipos — só a
tela muda de acordo com `config.json`.

## Adicionar um cliente novo

1. Copie a pasta `ponto-car/` com o novo nome (ex: `clientes/auto-pecas-silva/`).
2. Edite `skill.md`, `legenda.md` e `config.json` com os dados do novo cliente.
3. Troque os logos e as imagens de `referencias/` (e as linhas de `referencias.json`).
4. Esvazie a lista de `produtos` em `catalogo.json` e faça a primeira sincronização.

O cliente aparece sozinho no seletor do app — nenhum código precisa mudar.

### `config.json`

| Campo | O que é |
|---|---|
| `nome` | Nome exibido no app |
| `loja_shopee` | Link da loja do cliente na Shopee |
| `shopee_shopid` | ID numérico da loja na Shopee (ajuda o Claude na sincronização) |
| `logo_posicao` | Posição padrão do logo, usada quando a referência sorteada não define uma: `superior-esquerdo`, `superior-centro`, `superior-direito`, `inferior-esquerdo`, `inferior-centro` ou `inferior-direito` |
| `dias_sem_repetir_produto` | Janela em que um produto já usado não volta a ser escolhido (padrão 30) |

## Atualizar o catálogo (Claude in Chrome)

O app não navega na Shopee sozinho — a loja bloqueia navegação automática feita por
servidores. Quem captura os produtos é o Claude, pelo seu Chrome, quando você pede.
Recomendado: uma vez por mês, ou sempre que o cliente lançar produtos.

1. Deixe o Chrome aberto com a extensão Claude in Chrome conectada (e logado na Shopee,
   se a loja pedir login).
2. Abra o Claude Code e peça, trocando o nome do cliente:

   > Atualiza o catálogo da Ponto Car: abre a loja dela na Shopee pelo Claude in Chrome,
   > vai em "Todos os produtos" ordenado por "Mais vendidos", lê os cards da página como
   > um usuário (sem chamar a API interna da Shopee em sequência), captura os 40
   > primeiros e salva em `clientes/ponto-car/catalogo.json` no formato do
   > `clientes/README.md`.

3. Suba o `catalogo.json` atualizado no GitHub (substituindo o antigo).

**Anti-robô da Shopee:** chamadas diretas e seguidas à API interna da loja disparam uma
verificação de captcha (visto na primeira sincronização, em 22/09/2026). O Claude não
resolve captcha: se aparecer um, ele para, e você resolve manualmente no Chrome antes de
pedir de novo. Ler a página como um usuário, com calma, evita o problema.

Com 30 dias sem repetir e um post por dia, o catálogo precisa de pelo menos ~30
produtos. Se todos já tiverem sido usados no período, o app reaproveita o usado há
mais tempo e mostra um aviso.

### Formato do `catalogo.json`

```json
{
  "atualizado_em": "2026-09-22",
  "fonte": "claude_in_chrome",
  "loja": "https://shopee.com.br/pontocarborrachas",
  "produtos": [
    {
      "id": "22393847561",
      "nome": "Palheta Limpador Para-brisa 18 Polegadas Corsa 94/02 Classic - Par",
      "preco": "R$ 39,90",
      "vendidos": 1200,
      "vendidos_texto": "1,2mil vendidos",
      "avaliacao": 4.8,
      "categoria": "Palhetas",
      "descricao": "Texto da descrição do anúncio (opcional, só dos mais vendidos)",
      "foto_url": "https://down-br.img.susercontent.com/file/....",
      "url": "https://shopee.com.br/...-i.123456.22393847561"
    }
  ]
}
```

- `id`: o número depois do último ponto no link do produto (identifica o produto no
  histórico de repetição).
- `vendidos`: número inteiro (ex: "1,2mil vendidos" → 1200). É o que define a prioridade.
- `foto_url`: link direto da foto principal — é enviada à IA de imagem como referência,
  para o produto aparecer igual ao real.
- `descricao`: opcional. Quando existe, a legenda usa dela para aplicação/medidas; sem
  ela, a IA se limita ao que está no nome do produto.
