# Kav — Automação de Marketing Multi-Agente (protótipo)

Sistema de automação de conteúdo da Kav (@kav.mkt), orquestrando agentes independentes
que usam a API da OpenAI: texto com `gpt-4o-mini` (pauta, legenda, brief de imagem) e a
imagem final com o GPT Image 2.5 da OpenAI, gerada de uma vez só a partir de um brief completo (cores
da marca, direção de arte, composição). **Não posta nada automaticamente** — a postagem
final é sempre manual, feita por você.

A interface web (`app.py`) é a forma recomendada de usar o sistema — não exige instalar
nada no seu computador, só publicar no Streamlit Community Cloud (gratuito). Veja o
passo a passo em **"Publicar de graça, sem instalar nada"** abaixo.

## Estrutura

```
kav-mkt/
├── app.py                          # interface web (Streamlit) — use esta
├── orchestrator.py                 # versão em linha de comando (opcional, uso local)
├── skills/ponto-car.md             # diretrizes de marca do cliente (edite aqui)
├── agents/
│   ├── agente_pauta.py             # gera a pauta do dia via OpenAI (gpt-4o-mini)
│   ├── agente_produto.py           # resolve produto (manual ou coringa), com fallback
│   └── agente_design.py            # brief de KV (gpt-4o-mini) + imagem final (GPT Image 2.5)
├── utils/
│   ├── openai_client.py            # wrapper único para chamadas à API da OpenAI
│   ├── image_overlay.py            # recorte 1080x1440 + sobreposição da chamada (headline)
│   └── skill_loader.py             # lê e faz parse do arquivo de skill do cliente (inclui cores)
├── assets/fonts/                   # fontes bold (Anton, Archivo Black) para a chamada na imagem
├── assets/logos/<cliente>.png      # logo do cliente (opcional — ver assets/logos/README.md)
├── data/<cliente>/produtos_usados.json   # controle de produtos já usados
├── data/<cliente>/historico_manual.txt   # referências de posts anteriores — texto (opcional)
├── data/<cliente>/referencias_layout/    # últimas imagens geradas, usadas como referência visual
├── logs/<cliente>/falhas_produto.log     # log de falhas na busca de produto
├── output/<cliente>/<AAAA-MM-DD>/        # artefatos gerados por execução
├── .streamlit/config.toml          # tema visual do app
├── .env.example
└── requirements.txt
```

## Publicar de graça, sem instalar nada (Streamlit Community Cloud)

> Nota: inicialmente eu tinha indicado o Hugging Face Spaces, mas eles mudaram a
> política e hoje só o SDK "Static" (sites sem servidor) é gratuito lá — rodar um app
> Python como este agora exige o plano PRO pago. O Streamlit Community Cloud continua
> gratuito para esse tipo de app, então é o caminho recomendado.

Isso publica o app numa URL própria (ex: `https://kav-mkt-xxxx.streamlit.app`),
acessível de qualquer navegador, sem você instalar Python nem nada parecido. É gratuito;
os únicos cadastros necessários são GitHub (para guardar o código) e Streamlit (para
publicar), e o login no Streamlit é feito com a própria conta do GitHub — não precisa
criar outra senha.

### 1. Suba o código para o GitHub (pelo navegador, sem git)

1. Crie uma conta gratuita em [github.com/signup](https://github.com/signup) (se já
   tiver uma, só entre).
2. Clique em **"New repository"** (ou acesse
   [github.com/new](https://github.com/new)).
   - **Repository name:** `kav-mkt`
   - Deixe marcado **Public** (não há nenhuma chave nem senha dentro do código — elas
     ficam à parte, nos "Secrets" do Streamlit, no passo 2) ou escolha **Private**, se
     preferir.
   - Não marque nenhuma opção de "Add a README" (para não dar conflito) e clique em
     **Create repository**.
3. Na página do repositório recém-criado, clique no link **"uploading an existing
   file"**. Extraia o `kav-mkt.zip` que te enviei e arraste **todos os arquivos e pastas**
   da pasta `kav-mkt/` para essa tela (incluindo `agents/`, `utils/`, `skills/`, `app.py`
   e `requirements.txt`). Role para baixo e clique em **Commit changes**.

   > Atenção: pastas que começam com ponto (`.streamlit/`, `.gitignore`, `.env.example`)
   > podem ficar escondidas pelo seu sistema operacional ao arrastar. Não é grave se
   > elas não subirem — são só configurações opcionais (tema visual, etc.), o app
   > funciona sem elas.

### 2. Publique no Streamlit Community Cloud

1. Acesse [share.streamlit.io](https://share.streamlit.io) e clique em **"Sign in with
   GitHub"** (autoriza com um clique, sem precisar criar senha nova).
2. Clique em **"Create app"** (ou "New app").
3. Selecione o repositório `kav-mkt`, branch `main`, e no campo do arquivo principal
   digite `app.py`.
4. Antes de clicar em Deploy, abra **"Advanced settings"** e, no campo **Secrets**, cole:

   ```toml
   OPENAI_API_KEY = "sua-chave-da-api-aqui"
   ```

   (Cole você mesmo sua chave real da OpenAI aqui — é um campo seguro do próprio
   Streamlit, só você tem acesso a ele.)

   Se quiser proteger o app com uma senha simples (recomendado, já que a URL pode ficar
   pública — assim ninguém além de você gasta sua cota de API só por ter o link), pode
   adicionar mais uma linha:

   ```toml
   APP_PASSWORD = "escolha-uma-senha-aqui"
   ```

5. Clique em **Deploy**. Em 1–3 minutos o app fica no ar na URL que o Streamlit gerar.
   Sempre que quiser gerar um post, é só abrir essa URL.

Pronto — isso é tudo. Não é preciso terminal, Python local, nem editor de código.

> Quer trocar o modelo de texto (ex: para `gpt-4o` se notar que o `gpt-4o-mini` não está
> dando conta)? Adicione mais uma linha nos Secrets: `OPENAI_MODEL = "gpt-4o"`. Sem essa
> linha, o padrão é `gpt-4o-mini`. Também dá pra ajustar a imagem com `OPENAI_IMAGE_SIZE`
> (padrão `1024x1024`) e `OPENAI_IMAGE_QUALITY` (`low`, `medium` ou `high` — padrão
> `medium`; `low` gasta bem menos crédito).

Para atualizar o app no futuro (ex: editar a skill de um cliente), volte no repositório
do GitHub, abra o arquivo pela interface web, clique no ícone de lápis para editar, e
salve (**Commit changes**) — o Streamlit Cloud redetecta e atualiza o app sozinho em
seguida.

## Rodando localmente (opcional, para quem tem Python instalado)

```bash
cd kav-mkt
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # edite e cole sua OPENAI_API_KEY
streamlit run app.py
```

Também existe uma versão em linha de comando (`orchestrator.py`), útil para automação
via cron/agendador no futuro:

```bash
python orchestrator.py --cliente ponto-car
```

## Busca de produto na Shopee

A Shopee não pode ser navegada de forma automática e confiável por um app hospedado
comum (a listagem é renderizada via JavaScript e há proteção anti-bot). Por isso, quando
a pauta pedir um produto específico, a interface web mostra um formulário simples para
você colar nome/foto/link do produto (depois de olhar rapidamente na loja) — ou você
pode simplesmente clicar em **"Usar produto coringa"** para pular essa etapa.

Camadas, na ordem em que são tentadas:

1. **Manual** — o que você digitar no formulário da interface (tem prioridade).
2. **Automática best-effort** — uma tentativa simples via HTTP, que na prática quase
   sempre falha (esperado).
3. **Plano B (fallback, sempre ativo)** — se nada acima funcionar, o agente:
   - registra a falha em `logs/<cliente>/falhas_produto.log` (data, motivo, tentativas);
   - usa um **produto coringa** da skill do cliente, evitando repetir o último usado;
   - marca `fallback_usado: true` e mostra um aviso amarelo na tela, para você saber que
     aquele post não usa o produto pesquisado originalmente;
   - nunca trava o app — o fluxo sempre segue até o Agente de Design.

Todo produto usado (real ou fallback) é registrado em
`data/<cliente>/produtos_usados.json`, para controle e para evitar reuso nas próximas
execuções.

> Nota sobre hospedagem gratuita: no plano gratuito do Streamlit Community Cloud, o
> armazenamento em disco não é permanente — pode ser resetado quando o app reinicia
> (ex: após ficar muito tempo sem uso, ou ao atualizar o código). Para este protótipo
> isso é aceitável; se no futuro o histórico precisar ser 100% confiável, dá para plugar
> um armazenamento externo (ex: uma planilha ou banco de dados) sem mudar a lógica dos
> agentes.

## Adicionar/ajustar produtos coringa

Edite a seção `## Produtos Coringa` em `skills/<cliente>.md` — é uma lista simples em
markdown (`- Nome do produto`). O `skill_loader.py` faz o parse automaticamente; não é
necessário mexer em código. Edite o arquivo direto pela interface do GitHub (ícone de
lápis) — o app atualiza sozinho.

## Adicionar um novo cliente

1. Crie `skills/<novo-cliente>.md` seguindo as mesmas seções de `skills/ponto-car.md`
   (Segmento, Público-alvo, Cores, Tom de voz, Regras, Produtos Coringa). Na seção
   `## Cores da marca`, use nomes simples em português (preto, branco, amarelo, azul,
   azul petróleo, vermelho, verde, laranja, cinza, rosa, roxo, marrom) — são os nomes
   que `utils/skill_loader.py` reconhece pra colorir a barra de texto da imagem. Nomes
   fora dessa lista são ignorados nesse ponto específico (o resto do skill funciona
   normalmente).
2. Se o cliente também tiver loja na Shopee, adicione a URL no dicionário `URLS_LOJA` em
   `agents/agente_produto.py` (opcional — a busca manual funciona sem isso).
3. Envie o novo arquivo de skill para o repositório no GitHub. Ele aparece
   automaticamente no seletor de cliente da interface.

## Evoluir o histórico de posts no futuro (Agente de Pauta)

Hoje o histórico é preenchido manualmente colando exemplos na barra lateral (ver seção
"Referências de posts anteriores" acima), salvo em
`data/<cliente>/historico_manual.txt`. Quando no futuro você tiver uma fonte organizada
(planilha, API do Instagram, etc.), basta montar um resumo em texto dos posts recentes e
passar para `gerar_pauta(skill, historico=resumo)` no lugar do texto lido do arquivo —
o parâmetro já existe e o agente já injeta esse conteúdo no prompt da IA pedindo para
evitar repetir temas. Nenhuma mudança é necessária dentro do `agente_pauta.py`.

## Segurança do app publicado

- A chave `OPENAI_API_KEY` fica nos "Secrets" do Streamlit Cloud, nunca no código —
  ninguém que vir o repositório no GitHub consegue ver sua chave.
- Se o app ficar com URL pública, qualquer pessoa com o link poderia gerar posts e
  consumir sua cota da API. Configure o secret opcional `APP_PASSWORD` (explicado no
  passo a passo acima) para exigir uma senha simples antes de usar o app.

## Geração de imagem (GPT Image 2.5)

O modelo usado é o **GPT Image 2.5** — o mais recente da OpenAI (sucessor do
`gpt-image-1`), em duas variantes:
- `gpt-image-2.5-flare`: geração rápida do zero (usada quando não há foto real do
  produto).
- `gpt-image-2.5-sunburst`: mais precisa para edição/composição com imagem de
  referência (usada quando HÁ foto real do produto — ver abaixo).

O Agente de Design funciona em etapas, mas com uma única chamada de imagem por execução
(pra não gastar crédito repetindo tentativas):

1. Um brief de "Key Visual" (KV) é escrito por texto (`gpt-4o-mini`), incorporando as
   cores da marca, direção de arte, composição **e a headline (chamada) em português**
   vinda da Pauta — instruindo a própria IA de imagem a desenhar esse texto exatamente
   como está, dentro de um bloco/faixa numa cor da marca, com boa margem das bordas. O
   GPT Image 2.5 renderiza texto bem melhor que o modelo anterior (gpt-image-1), então
   isso passou a ser viável diretamente na cena, sem precisar de composição por código.
   Se ainda assim o texto sair cortado ou errado com frequência, dá pra reativar o
   desenho por código (mais prático e sem depender de sorte): edite
   `agents/agente_design.py`, passando `headline=headline` (em vez de `headline=""`) na
   chamada de `image_overlay.compor_imagem_final(...)`.

   **Margem de segurança para o recorte:** como a etapa 3 abaixo recorta a imagem
   gerada para caber exatamente no formato final, o brief avisa a IA (com o percentual
   exato calculado em `_margem_corte_vertical()`, a partir dos tamanhos configurados)
   para não colar texto/logo bem na borda de cima ou de baixo, já que essa faixa é
   cortada depois. Se mesmo assim algo continuar sendo cortado, aumente a folga extra
   somada em `_margem_corte_vertical()` (hoje +2 pontos percentuais) para um valor
   maior.
2. Duas fontes de referência visual são combinadas quando disponíveis, ambas enviadas
   juntas numa única chamada de edição ao `gpt-image-2.5-sunburst` (a API aceita várias
   imagens de referência ao mesmo tempo):
   - **Layout**: as últimas imagens já geradas por este app para o cliente (até 3),
     guardadas automaticamente em `data/<cliente>/referencias_layout/` — usadas para
     manter um estilo/composição visual consistente entre os posts, sem precisar
     configurar nada. Também dá pra alimentar essa pasta com posts antigos, enviando
     pelo expansor **"🖼️ Referências de layout"** na barra lateral.
   - **Produto**: se o produto tiver uma foto real (link colado no formulário da etapa
     Produto, e não caiu no fallback coringa), ela é baixada e enviada como referência,
     preservando a aparência real do produto (forma, cor, rótulo) em vez de "inventar"
     um genérico a partir do nome.

   Se nada disso estiver disponível, ou a tentativa falhar por qualquer motivo (link não
   é imagem direta, API recusa, etc.), cai automaticamente para a geração comum a partir
   do texto (`gpt-image-2.5-flare`) — nunca trava o fluxo. A tela mostra qual(is)
   referência(s) foram usadas de verdade.
3. A imagem final é cortada/redimensionada em código para exatamente **1080x1440**
   (vertical), e o logo do cliente é colado no canto superior direito, se existir em
   `assets/logos/<cliente>.png` (ver `assets/logos/README.md`).

Se a geração de imagem falhar (ex: conta sem acesso ao modelo, billing não configurado),
o app mostra o erro claramente na tela mas **não trava** — o brief de texto continua
disponível pra você usar manualmente em outra ferramenta. Desmarque "Gerar imagem
também" na barra lateral quando quiser só testar o texto sem gastar crédito de imagem.

> A OpenAI muda a nomenclatura dos modelos de tempos em tempos. Se `gpt-image-2.5-flare`
> ou `gpt-image-2.5-sunburst` pararem de existir no futuro, ajuste `OPENAI_IMAGE_MODEL` e
> `OPENAI_IMAGE_EDIT_MODEL` nos Secrets — nenhum código precisa mudar.

## Referências de posts anteriores

Na barra lateral, o expansor **"📚 Referências de posts anteriores"** deixa você colar
exemplos de posts que já publicou (tema + legenda). Isso é salvo em
`data/<cliente>/historico_manual.txt` e passado automaticamente para o Agente de Pauta a
cada geração, para ele não repetir temas e aprender o estilo que já funcionou. É o
parâmetro `historico` que já estava previsto desde o início — agora com uma forma
simples de preencher, sem precisar organizar uma base de dados externa ainda.

## Limitações desta fase (de propósito)

- Sem postagem automática em redes sociais — sempre manual.
- Busca de produto na Shopee é manual (via formulário) ou cai no produto coringa — não é
  automática nesta fase.
- Armazenamento do app gratuito não é permanente (ver nota acima) — isso inclui as
  referências de layout e o histórico de texto: se o servidor gratuito reiniciar, elas
  são perdidas e o "estilo" volta a ser aprendido do zero a partir do próximo post
  gerado (ou você reenvia manualmente exemplos antigos).
- A imagem é gerada numa única tentativa por execução — se não gostar do resultado, a
  forma de "tentar de novo" hoje é gerar um novo post inteiro (não há botão de
  "regerar só a imagem" ainda).

## Próximos passos sugeridos

1. Validar com o cliente a lista de produtos coringa da Ponto Car (`skills/ponto-car.md`).
2. Organizar uma fonte de histórico de posts e plugar no Agente de Pauta via `historico`.
3. Adicionar um Agente de Legenda dedicado (hoje a legenda é só um rascunho vindo da pauta).
4. Adicionar um botão de "regerar só a imagem" sem precisar gerar uma pauta nova.
5. Trocar o armazenamento em arquivo por algo persistente (planilha/banco), já que o
   disco do plano gratuito não é permanente.
6. Adicionar um segundo cliente para validar que a estrutura de skills/agentes generaliza bem.
