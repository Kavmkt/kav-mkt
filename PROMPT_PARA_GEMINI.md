# CONTEXTO COMPLETO DO PROJETO KAV MARKETING (kav-mkt) — LEIA TUDO ANTES DE FAZER QUALQUER MUDANÇA

Gemini, este é um projeto real, em produção, de uma agência de marketing (Kav, @kav.mkt) que
atende clientes reais (o principal hoje é o N&N Restaurante). Não é um projeto de estudo. Se
você quebrar algo, o cliente da Kav pode receber uma peça errada ou a aplicação pode simplesmente
parar de funcionar. Por isso este documento é longo e repetitivo de propósito: leia inteiro antes
de tocar em qualquer arquivo, mesmo que pareça óbvio.

Quem escreveu este documento foi outro assistente de IA (Claude, da Anthropic) que trabalhou
nesse projeto com o Kesley (o dono da Kav) durante o dia de hoje, 27/09/2026. A partir de agora,
amanhã, é você quem vai continuar. Este documento existe pra você não perder nenhum contexto do
que já foi decidido e já foi feito.

---

## 1. O QUE É ESTE PROJETO (visão de negócio, não técnica)

A Kav é uma agência de marketing que roda uma "fábrica" automatizada de posts pra redes sociais
usando agentes de IA (cada um com uma função, tipo um funcionário): um escolhe a foto do prato,
outro escreve a legenda, outro monta a arte final, etc. Isso tudo roda em Python e chama a API da
OpenAI (texto com gpt-4o-mini, imagem com GPT Image).

Tem duas formas de operar essa fábrica:
- **App Streamlit** (`kav-mkt/app.py`): painel interno, sério, pra uso do time da Kav.
- **Escritório Virtual** (`kav-mkt/escritorio-kav/`): uma interface visual bonita, estilo
  "escritório isométrico" com avatares dos agentes, feita pra IMPRESSIONAR CLIENTE em reunião de
  vendas — mas que hoje também dispara os agentes de verdade (não é só decoração).

Cliente principal hoje: **NN Restaurante** (`clientes/nn-restaurante/`), comida caseira em Santana
de Parnaíba/SP. Tem mais dois clientes de teste: `ponto-car` e `kav` (a própria Kav).

Hoje foi adicionada uma funcionalidade nova e importante: **campanhas de tráfego pago (Meta Ads)**,
separadas dos posts orgânicos de feed — mais detalhes na seção 6.

---

## 2. ESTRUTURA DE PASTAS — ATENÇÃO, ISSO CONFUNDE

O repositório do GitHub (`github.com/Kavmkt/kav-mkt`, branch `main`) tem uma pasta chamada
`kav-mkt` NA RAIZ. Ou seja, todo caminho de arquivo do código de verdade começa com `kav-mkt/`:

```
(raiz do repositório)
├── PROMPT_PARA_GEMINI.md      ← este arquivo
├── .gitignore
└── kav-mkt/                    ← O PROJETO DE VERDADE FICA AQUI DENTRO
    ├── app.py                  ← painel Streamlit
    ├── orchestrator.py         ← "cérebro" que chama os agentes em sequência
    ├── .env                    ← chaves secretas (NUNCA committar, já está no .gitignore)
    ├── .env.example            ← modelo do .env, sem valores reais
    ├── requirements.txt
    ├── agents/                 ← cada arquivo é UM agente de IA
    │   ├── agente_catalogo.py       (escolhe produto — clientes tipo "produto", ex: ponto-car)
    │   ├── agente_foto.py           (escolhe foto real — clientes tipo "fotos", ex: nn-restaurante)
    │   ├── agente_pauta.py          (escolhe pauta — clientes tipo "carrossel", ex: kav)
    │   ├── agente_legenda.py        (legenda orgânica — produto)
    │   ├── agente_legenda_fotos.py  (legenda orgânica — fotos)
    │   ├── agente_carrossel.py      (roteiro + imagens do carrossel)
    │   ├── agente_design.py         (brief + imagem — produto; TEM utilidades genéricas
    │   │                             reaproveitadas pelos outros arquivos de design, ver seção 7)
    │   ├── agente_design_fotos.py   (brief + imagem — fotos, posts orgânicos)
    │   ├── agente_estrategia_campanha.py  ← NOVO HOJE (campanha, Meta Ads)
    │   ├── agente_layout_campanha.py      ← NOVO HOJE (campanha, Meta Ads)
    │   ├── agente_metricas.py       (lê Meta Ads / Instagram)
    │   └── agente_supervisor.py     (cruza métricas com conteúdo)
    ├── utils/
    │   ├── cliente.py           (lê a pasta clientes/<slug>/ e monta um dict com tudo)
    │   ├── openai_client.py     (toda chamada à API da OpenAI passa por aqui)
    │   ├── image_overlay.py     (recorta a imagem gerada pro tamanho final 1080x1440)
    │   ├── estado_agentes.py    (mantém o estado do Escritório Virtual — quem está fazendo o quê)
    │   └── historico.py         (evita repetir produto/foto nos últimos N dias)
    ├── clientes/
    │   └── nn-restaurante/
    │       ├── skill.md         ← FONTE DA VERDADE da marca (tom de voz, cores, endereço,
    │       │                       o que pode/não pode dizer). Os agentes leem esse arquivo
    │       │                       inteiro a cada execução.
    │       ├── config.json      (tipo do cliente: "fotos", contas do Meta Ads/Instagram)
    │       ├── concorrentes_e_mercado.json  ← NOVO HOJE, ainda VAZIO (ver seção 6)
    │       ├── fotos/           (fotos reais dos pratos, usadas como base da imagem final)
    │       ├── referencias/     (modelos de layout já aprovados)
    │       └── logo/            (logo oficial da marca)
    └── escritorio-kav/
        ├── index.html
        ├── app.js
        ├── style.css
        ├── server.py           ← NOVO HOJE (antes não existia! ver seção 6)
        └── estado_agentes.json (estado ao vivo — não editar na mão, é gerado pelo código)
```

**IMPORTANTE**: até ontem existia uma SEGUNDA pasta `escritorio-kav/` na raiz do repositório
(fora do `kav-mkt/`), com uma versão antiga/demo que nunca chamava os agentes de verdade — ela foi
DELETADA hoje porque só causava confusão. Se você achar qualquer referência a ela no histórico do
git, ignore — não existe mais e não deve ser recriada.

---

## 3. COMO O FLUXO FUNCIONA (de ponta a ponta)

1. Alguém clica em "▶️ Dar o Play" no Escritório Virtual (ou roda o Streamlit).
2. Isso chama `POST /api/executar` no `server.py`, com `{slug, com_imagem, modo}`.
3. `server.py` decide o que fazer com base em `modo` ("campanha" ou "organico") e no tipo do
   cliente (`config.json` → campo `"tipo"`: "fotos", "produto" ou "carrossel").
4. Ele chama funções de `orchestrator.py`, que por sua vez chamam os agentes em sequência:
   escolher foto/produto/pauta → escrever a copy → montar o brief da imagem → gerar a imagem
   (chamando `utils/openai_client.py`, que fala com a API da OpenAI) → recortar a imagem final
   (`utils/image_overlay.py`).
5. O resultado (post completo, com a imagem em base64) volta como JSON pro navegador, que mostra
   num modal (`app.js` função `exibirPostModal`).
6. `utils/estado_agentes.py` grava esse post em `estado_agentes.json`, que é o que dá vida aos
   avatares e à gaveta "Posts & Legendas" na tela.

---

## 4. REGRAS QUE VOCÊ NUNCA PODE QUEBRAR

1. **Nunca invente conteúdo de marca.** Os agentes só podem usar informação que está em
   `clientes/<slug>/skill.md`, `config.json`, `legenda.md`, `catalogo.json` ou nos metadados da
   foto. Nunca invente preço, promoção, ingrediente ou endereço que não esteja lá.
2. **Nunca commite o arquivo `.env`.** Ele tem a chave da API da OpenAI e tokens do Meta Ads.
   Já está no `.gitignore` — não remova essa linha.
3. **`clientes/nn-restaurante/concorrentes_e_mercado.json` está de propósito vazio/placeholder**
   (tem um campo `"_atencao"` avisando isso). O código
   (`agents/agente_estrategia_campanha.py::_carregar_mercado`) já sabe ignorar esse arquivo
   enquanto ele tiver esse campo. NÃO invente concorrentes fictícios pra preencher esse arquivo —
   isso só pode ser preenchido com pesquisa real feita por uma pessoa. Se for pedido pra você
   preencher, avise que precisa de dados reais e pergunte antes de inventar qualquer nome de
   concorrente.
4. **Nunca apague a foto real como referência da imagem.** Nos clientes tipo "fotos" (como o
   NN Restaurante), a foto do prato é sempre real — a IA só aplica um tratamento gráfico por cima
   (texto, selo, logo), nunca "reimagina" o prato do zero. Isso está escrito nos prompts dos
   agentes de design — não mude essa regra.
5. **As cores da marca vêm SÓ de `skill.md`.** Nunca invente cor nova pra um cliente.
6. **Padrão de nomenclatura**: o código é todo em português (nomes de função, variável,
   docstring), mesmo os comentários. Siga esse padrão — não troque pra inglês.
7. **Nunca use `git push --force`, nunca rode `git reset --hard`, nunca apague branch.** Se
   algo der conflito, pare e avise o Kesley em vez de forçar.

---

## 5. SUAS LIMITAÇÕES (você só trabalha pelo GitHub)

O Kesley me contou que você só consegue interagir com este projeto através do GitHub — você não
tem um terminal pra rodar `streamlit run`, não consegue instalar pacotes Python, e não consegue de
fato chamar a API da OpenAI pra ver a imagem sendo gerada. Ou seja: **você não consegue testar de
verdade se uma mudança funciona.**

Por causa disso:
- **Nunca diga "está funcionando" ou "corrigido" sem o Kesley confirmar rodando localmente.**
  O jeito certo de falar é: "Fiz a mudança X pelo motivo Y — pode testar localmente e me dizer se
  funcionou?"
- Se a tarefa pedir pra "testar", o que você PODE fazer é: ler o código com atenção, procurar
  inconsistências lógicas (nomes de função que não existem, parênteses errados, um campo que o
  código lê mas que nunca é escrito em outro lugar), e explicar seu raciocínio — não fingir que
  executou nada.
- Prefira mudanças pequenas e isoladas, uma por vez, cada uma num commit separado com mensagem
  clara — assim, se alguma quebrar algo, é fácil identificar qual foi e desfazer só ela.
- Depois de qualquer mudança, escreva pro Kesley EXATAMENTE quais comandos ele deve rodar no
  terminal dele para testar (ele sabe rodar comandos, só peça de forma explícita e completa,
  igual eu fiz nas seções abaixo).

Comandos que o Kesley pode rodar pra testar localmente (ele já tem o ambiente configurado):
```bash
cd /Users/kesley/Documents/kav-mkt/kav-mkt
source .venv/bin/activate
python3 escritorio-kav/server.py
```
Depois abrir `http://localhost:8080` no navegador.

---

## 6. O QUE FOI FEITO HOJE, 27/09/2026 (para você não se perder)

Tudo isso já está commitado no GitHub, branch `main`, commit `8ca4c03` (pode confirmar rodando
`git log` na raiz do repositório clonado). Se você não encontrar algum desses arquivos, é sinal de
que o push ainda não chegou até você — pergunte ao Kesley antes de continuar.

1. **Ambiente local configurado**: `.env` com a chave da OpenAI de verdade, ambiente virtual
   Python (`.venv/`) criado e dependências instaladas.
2. **`escritorio-kav/server.py` criado do zero** — antes não existia nenhum backend pro
   Escritório Virtual, então o botão "Dar o Play" não fazia nada de real.
3. **Removida a pasta duplicada `escritorio-kav/` da raiz do repositório** (fora de `kav-mkt/`) —
   era uma versão antiga, só demonstrativa, com dados fabricados, que nunca chamava os agentes de
   verdade. Só sobrou `kav-mkt/escritorio-kav/`, que é a de verdade.
4. **Esteira de Campanha de Alta Performance (Meta Ads) implementada**:
   - `orchestrator.gerar_campanha()` JÁ EXISTIA, mas estava QUEBRADA (chamava uma função chamada
     `gerar_copy_foto` que nunca tinha sido importada no arquivo — teria dado erro na primeira vez
     que alguém tentasse usar). Foi reescrita do zero e agora funciona de verdade.
   - Criados dois agentes novos: `agents/agente_estrategia_campanha.py` (decide o ângulo de
     conversão e escreve a copy do anúncio) e `agents/agente_layout_campanha.py` (monta a arte
     1080x1440 com foto real + faixa de call-to-action de WhatsApp).
   - `server.py` agora lê um campo `modo` ("campanha" ou "organico") no corpo do `POST
     /api/executar` e decide qual esteira rodar.
   - `escritorio-kav/index.html` e `app.js` ganharam um seletor `<select id="select-modo">` na
     barra superior, e o modal de entrega do post ganhou um selo "🎯 Peça de Campanha (Meta Ads)"
     e uma seção "Ângulo de Conversão" quando o post é de campanha.
   - Tudo isso foi testado de ponta a ponta (com chamada real à API da OpenAI) e confirmado
     funcionando, incluindo geração de imagem real.
5. **Corrigido um bug de corte de logo e rodapé nas imagens geradas** — ver seção 7, é o assunto
   principal deste documento.

---

## 7. O BUG DO CORTE DE LOGO/RODAPÉ — TRÊS CAUSAS DIFERENTES, TODAS JÁ CORRIGIDAS HOJE

O Kesley relatou que as artes finais estavam chegando com o **logo cortado no topo e o
rodapé/selo cortado na base**. Essa investigação levou o dia inteiro e passou por TRÊS causas
diferentes, encontradas uma depois da outra — cada vez que uma correção parecia resolver, um novo
teste real mostrava que ainda faltava algo. Conto essa história completa porque é bem provável que
você (ou o Kesley, ou eu numa sessão futura) precise investigar de novo se o corte voltar a
aparecer — e cada uma dessas três causas pode voltar a acontecer isoladamente.

### Causa 1 — a margem de segurança avisada à IA era calculada pro tamanho errado

A API de imagem da OpenAI é pedida num tamanho customizado, quase igual ao final ("1072x1440",
`utils/openai_client.py`, variável `IMAGE_SIZE`). Mas ela às vezes cai num tamanho de fallback bem
mais alto: `1024x1536` (variável `TAMANHO_IMAGEM_SEGURO`). O corte final pra chegar em `1080x1440`
é de menos de 1% no primeiro caso, mas de **~11%** no segundo. A função que calcula a margem de
segurança a avisar pra IA (`_margem_corte_vertical()`, em `agents/agente_design.py`) só considerava
o tamanho PEDIDO, então quando a API caía no fallback, a IA recebia a instrução errada (margem
pequena) quando precisava de uma margem bem maior.

**Corrigido**: a função agora calcula a margem pra os dois tamanhos possíveis e usa o maior
(pior caso). Depois de mais investigação (ver Causa 3), a folga fixa somada em cima do cálculo
também subiu de "+4" para "+7" pontos percentuais.

### Causa 2 — o logo dos posts de fotos era enviado "torto", sem guia visual

Esta foi a causa mais séria, e só afetava o NN Restaurante (clientes tipo "fotos"). Existe uma
técnica no projeto (usada desde sempre em `agente_design.py`, o fluxo de produto) chamada "guia de
logo": em vez de mandar o arquivo do logo sozinho (que tem uma proporção bem diferente da imagem
final — uma faixa larga e baixa) como referência pra IA, o código desenha esse logo, já na posição
e escala certas, dentro de um canvas TRANSPARENTE do TAMANHO EXATO do post final. Isso dá à IA um
sinal visual muito mais forte e inequívoco de onde o logo deve ficar.

**O bug**: os arquivos `agents/agente_design_fotos.py` (posts orgânicos) e o novo
`agents/agente_layout_campanha.py` (campanha) NUNCA usavam essa técnica — mandavam o arquivo bruto
do logo (`clientes/nn-restaurante/logo/logo_NN.jpeg`) direto como referência, com só uma frase de
texto dizendo onde colocar. Pior: essa frase de texto dizia hardcoded "no cabeçalho/topo do post",
mesmo quando a posição configurada de verdade (`clientes/nn-restaurante/config.json`, campo
`logo_posicao`) é `"inferior-direito"` — ou seja, duas instruções contraditórias sobre onde
colocar o logo, uma dizendo "topo" e outra (a variável calculada `__AREA_LOGO__`) dizendo
"bottom-right corner". Isso confundia a IA generativa, que às vezes desenhava o logo bem perto da
borda que depois seria cortada.

**Corrigido**: `agente_design_fotos.py` e `agente_layout_campanha.py` agora usam a mesma técnica de
canvas-guia que `agente_design.py` já usava, e a frase de texto contraditória foi removida — agora
o texto só reforça "posição exata mostrada no guia", nunca uma posição fixa.

### Causa 3 — a faixa de CTA (WhatsApp) é um elemento NOVO que nunca teve essa proteção

A faixa de CTA (localização + "Peça agora pelo WhatsApp") foi criada hoje, junto com a campanha —
e, sem querer, teve o MESMO problema da Causa 2: só existia uma instrução em texto dizendo pra
deixar margem de segurança, sem nenhum guia visual. Em teste real, isso se mostrou insuficiente —
mesmo já com as Causas 1 e 2 corrigidas, a faixa de CTA continuou sendo cortada na borda inferior
em vários testes seguidos.

**Corrigido**: criada uma função nova, `guia_zona_cta()` em `utils/image_overlay.py` — desenha um
retângulo sólido numa cor "magenta" (uma cor de marcador, que nunca aparece em foto de comida nem
na paleta de nenhum cliente, pra ficar inequívoco que é só guia) exatamente na área/posição/margem
onde a faixa de CTA deve ficar. `agents/agente_layout_campanha.py` manda esse guia como mais uma
referência de imagem pra IA, com instrução clara: "desenhe a faixa de CTA de verdade dentro deste
retângulo, nunca a cor magenta em si, nunca ultrapasse esse limite".

### Como foi confirmado que funcionou

Foram gerados VÁRIOS posts de teste ao longo do dia (orgânico e campanha), incluindo forçando de
propósito o cenário mais crítico (API caindo no tamanho de fallback `1024x1536`, confirmado no
campo `tamanho_gerado` da resposta). O ÚLTIMO teste, depois das três correções, saiu com logo,
headline, selo E faixa de CTA inteiros, sem nenhum corte, mesmo no cenário de fallback.

### Isto é uma IA generativa — não existe garantia 100%

Mesmo com as três correções, isto é uma IA generativa desenhando uma imagem — ela não é um
template rígido de código, então não há garantia matemática de que ela vá seguir sempre à risca. O
que as correções de hoje garantem é que a instrução certa (texto + guia visual + margem correta)
está sendo dada a ela em TODOS os casos possíveis de tamanho. Se o corte voltar a aparecer
ocasionalmente, isso pode ser só a variância normal de um modelo generativo, não necessariamente
um novo bug de código — por isso a tarefa da seção 8 é de MONITORAMENTO, não de reescrever tudo de
novo.

### Onde olhar se o corte voltar a aparecer

Em ordem de probabilidade:
1. `utils/image_overlay.py`, função `guia_zona_cta()` — pode precisar de uma `altura_fracao` maior
   (hoje 0.10, ou seja 10% da altura do post) se o texto do CTA não estiver cabendo dentro do
   retângulo-guia.
2. `agents/agente_design.py`, função `_margem_corte_vertical()` — pode precisar aumentar ainda mais
   o "+7" pontos percentuais de folga fixa.
3. Confirme que NENHUM lugar do código voltou a ter uma posição de logo/CTA hardcoded em texto que
   contradiga a posição calculada (`__AREA_LOGO__`) — foi exatamente esse tipo de contradição que
   causou a Causa 2.

NÃO mude a lógica de recorte em `utils/image_overlay.py::recortar_formato_final` — o recorte em si
está correto (é um "cover" central, igual ao `object-fit: cover` do CSS); o problema nunca foi o
recorte, foi a IA não receber (ou não seguir) a instrução certa de margem/posição.

---

## 8. SUA PRIMEIRA TAREFA

Como as três causas do bug de corte já foram corrigidas e testadas hoje, sua primeira tarefa não é
corrigi-lo de novo do zero — é **confirmar que você entendeu o raciocínio das três causas (seção 7)
e ajudar a monitorar nos próximos dias**, já que (como explicado acima) uma IA generativa nunca dá
garantia 100%:

1. Leia os arquivos citados na seção 7 antes de fazer qualquer mudança nova:
   `agents/agente_design.py` (funções `_margem_corte_vertical` e `_logo`), `agents/agente_design_fotos.py`
   e `agents/agente_layout_campanha.py` (onde o guia de logo e o guia de CTA são montados e
   enviados como referência), e `utils/image_overlay.py` (funções `guia_posicao_logo`,
   `guia_zona_cta` e `recortar_formato_final`). Confirme pro Kesley, em texto simples, que o
   raciocínio das três causas faz sentido pra você — se achar algo que não bate, avise antes de
   qualquer mudança.
2. Peça ao Kesley pra gerar alguns posts de teste (orgânico e campanha) nos próximos dias e
   conferir visualmente se logo, headline, selo e faixa de CTA aparecem inteiros, sem cortar. Se
   ele disser que ainda cortou em algum caso, colete dele: o `slug` do cliente, o `modo`
   (campanha/organico), e o campo `tamanho_gerado` da resposta (pode pedir pra rodar por `curl`,
   igual descrito na seção 5) — e SALVE a imagem cortada, pra você poder olhar exatamente onde e o
   quanto foi cortado antes de decidir o que ajustar.
3. NÃO toque em `clientes/nn-restaurante/concorrentes_e_mercado.json` além de ler — ele está
   vazio de propósito (ver regra 3 da seção 4).
4. Qualquer mudança que você fizer, explique pro Kesley em português simples o que mudou e por
   quê, e diga exatamente quais comandos ele deve rodar para testar (não assuma que ele lembra os
   comandos — repita sempre, igual eu fiz na seção 5). Se a mudança envolver gerar uma imagem de
   teste de verdade, avise que cada teste custa um pouco de crédito real da API da OpenAI — não
   gere testes em excesso sem necessidade.

---

## 9. CHECKLIST RÁPIDO ANTES DE COMEÇAR

- [ ] Confirmei qual é o commit mais recente na branch `main` do GitHub (pergunte ao Kesley se não
      tiver certeza — este documento foi escrito logo depois do commit `8ca4c03`, mas pode ter
      mudado desde então).
- [ ] Li as seções 4 (regras) e 5 (minhas limitações) inteiras.
- [ ] Entendi a diferença entre `kav-mkt/escritorio-kav/` (a de verdade) e a pasta antiga que foi
      deletada — não vou recriar a antiga.
- [ ] Entendi as TRÊS causas do bug de corte (seção 7) e sei que uma IA generativa nunca dá
      garantia 100% — meu papel agora é monitorar, não reescrever tudo de novo do zero.
- [ ] Sei que não consigo testar rodando o código de verdade, e vou sempre pedir pro Kesley
      confirmar antes de dizer que algo está funcionando.

Fim do documento. Boa sorte — e qualquer dúvida sobre o que está escrito aqui, pergunte ao Kesley
antes de adivinhar.
