# Referências de layout

Até 10 imagens de posts da Ponto Car que representam o layout a seguir (PNG, JPG ou
WEBP). A cada post, o Agente de Design sorteia uma delas e pede para a IA reproduzir a
estrutura do layout com o novo produto. Se houver mais de 10, só as 10 primeiras em
ordem alfabética são usadas.

Só ficam aqui referências com o **logo atual** da Ponto Car. As 5 antigas (com o logo
"Borrachas e Acessórios Automotivos") foram removidas em 23/09/2026 — suba mais posts no
visual novo quando tiver.

`referencias.json` diz, para cada imagem, onde o logo fica naquele layout e qual versão
usar — a IA recebe o arquivo do logo como referência e desenha ele mesma nessa posição
(o código só recorta a imagem no final; não cola mais o logo por cima):

- `logo_posicao`: `superior-esquerdo`, `superior-centro`, `superior-direito`,
  `inferior-esquerdo`, `inferior-centro` ou `inferior-direito`.
- `logo_versao`: `fundo-escuro` (usa `logo-fundo-escuro.png`, o logo claro) ou
  `fundo-claro` (usa `logo-fundo-claro.png`, o logo escuro).

Ao trocar uma referência, atualize a linha dela nesse arquivo. Imagem sem linha usa a
posição padrão de `config.json` e o logo para fundo escuro.
