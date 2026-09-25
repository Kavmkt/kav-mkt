# Referências de layout

Até 10 imagens de posts da NN Restaurante que representam o layout a seguir (PNG, JPG
ou WEBP). A cada post, o Agente de Design sorteia uma delas e pede para a IA reproduzir
a estrutura gráfica do layout (posição da headline, do selo do prato, faixas e cores)
**sobre a foto real** escolhida do repositório em `../fotos/` — a referência de layout
aqui não define a cena, só o tratamento gráfico por cima dela.

Ainda não há referências cadastradas — o cliente é novo. Sem elas, o Agente de Design
usa só o KV descrito em `skill.md` para montar o layout. Suba posts reais aprovados
aqui assim que o cliente aprovar as primeiras peças.

`referencias.json` diz, para cada imagem, onde o logo fica naquele layout e qual
versão usar — a IA recebe o arquivo do logo como referência e desenha ele mesma nessa
posição:

- `logo_posicao`: `superior-esquerdo`, `superior-centro`, `superior-direito`,
  `inferior-esquerdo`, `inferior-centro` ou `inferior-direito`.
- `logo_versao`: `fundo-escuro` (usa `logo-fundo-escuro.png`, o logo claro) ou
  `fundo-claro` (usa `logo-fundo-claro.png`, o logo escuro).

Ao trocar uma referência, atualize a linha dela nesse arquivo. Imagem sem linha usa a
posição padrão de `config.json` (`inferior-direito`) e o logo para fundo escuro.
