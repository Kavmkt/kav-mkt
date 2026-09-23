# Referências de layout

Até 10 imagens de posts da Ponto Car que representam o layout a seguir (PNG, JPG ou
WEBP). A cada post, o Agente de Design sorteia uma delas e pede para a IA reproduzir a
estrutura do layout com o novo produto. Se houver mais de 10, só as 10 primeiras em
ordem alfabética são usadas.

`referencias.json` diz, para cada imagem, onde o logo fica naquele layout e qual versão
do logo usar — o logo é aplicado por código nesse ponto, e a IA deixa a área livre:

- `logo_posicao`: `superior-esquerdo`, `superior-centro`, `superior-direito`,
  `inferior-esquerdo`, `inferior-centro` ou `inferior-direito`.
- `logo_versao`: `fundo-escuro` (usa `logo-fundo-escuro.png`, o logo claro) ou
  `fundo-claro` (usa `logo-fundo-claro.png`, o logo escuro).

Ao trocar uma referência, atualize a linha dela nesse arquivo. Imagem sem linha usa a
posição padrão de `config.json` e o logo para fundo escuro.
