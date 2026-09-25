# Repositório de fotos

Este é o cliente "de fotos" — em vez de escolher um produto de catálogo, o Agente de
Repositório de Fotos (`agents/agente_foto.py`) sorteia uma **foto real** desta pasta a
cada post: prato, buffet, salão, fachada, equipe fardada etc. Essa foto vira a base da
peça — a IA de imagem **não desenha uma cena nova**, ela aplica um tratamento gráfico
(headline, selo do prato e o logo pequeno) por cima da foto real, no estilo definido em
`../skill.md` e (quando houver) na referência de layout sorteada em `../referencias/`.

Suba aqui fotos reais do cliente (PNG, JPG ou WEBP) — pratos prontos, o buffet montado,
o salão, a fachada, a equipe trabalhando, etc. Sem limite de 10 como em
`referencias/`: quanto mais fotos, menos repetição.

## `fotos.json`

Metadados de cada foto (chave = nome do arquivo). Todos os campos são opcionais, mas
preencher `nome` e `descricao` melhora muito a legenda gerada — o Agente de Legenda só
usa o que estiver aqui, nunca inventa prato ou preço que não conste:

```json
{
  "feijoada-completa.jpg": {
    "categoria": "prato",
    "nome": "Feijoada completa",
    "descricao": "Feijoada com arroz branco, couve refogada, farofa e laranja",
    "preco": "R$ 32,90"
  },
  "salao-01.jpg": {
    "categoria": "ambiente",
    "nome": "Salão da casa",
    "descricao": "Salão amplo, mesas para comer no local"
  }
}
```

- `categoria`: livre, sugestões: `prato`, `buffet`, `ambiente`, `equipe`, `entrega`.
- `nome`: nome do prato ou do que a foto mostra — usado na headline/selo.
- `descricao`: detalhes que ajudam a legenda (ingredientes, ocasião, diferencial).
- `preco`: só quando fizer sentido citar (a legenda não inventa preço sem isso).

Foto sem entrada em `fotos.json` ainda é usada — só entra sem nome/descrição/preço, e a
IA descreve de forma mais genérica a partir do nome do arquivo.

## Como a foto é usada na geração de imagem

Na chamada ao gerador de imagem (GPT Image), a foto real sorteada é enviada como
referência **obrigatória**, com instrução explícita de manter o prato/ambiente
praticamente inalterado — mesmo enquadramento, mesma comida, mesma iluminação. Quando
há uma referência de layout sorteada em `../referencias/`, ela também é enviada, só
para copiar a estrutura gráfica (onde vai a headline, o selo, as faixas de cor) — nunca
para substituir a cena da foto real. O logo entra por último, pequeno, na posição
definida em `../referencias/referencias.json` ou na posição padrão do `config.json`.
