# Instruções para o Gemini neste projeto (kav-mkt)

Leia isto por completo antes de alterar qualquer arquivo. Este projeto já quebrou
várias vezes por causa de refatorações feitas sem checar todos os lugares que
usavam a função alterada. Siga as regras abaixo à risca.

## O que é o projeto

Esteira multi-agente de marketing/performance rodando localmente em Python 3.9.

- `escritorio-kav/`: interface visual (Habbo isométrico 2.5D) — `index.html`,
  `style.css`, `app.js` — servida por `escritorio-kav/server.py` na porta 8080.
- `orchestrator.py`: orquestrador central. Roteia a execução por `tipo` de
  cliente (`fotos`, `produto`, `carrossel`, `estatico`).
- `agents/`: agentes autônomos (um por etapa: pauta, catálogo, foto, design,
  legenda, etc.).
- `clientes/<slug>/`: dados de cada cliente (`config.json`, `catalogo.json` ou
  `pautas.json`, `fotos/`, `referencias/`, `historico.json` gerado em runtime).
- `utils/`: módulos de suporte (`cliente.py`, `historico.py`,
  `openai_client.py`, `image_overlay.py`, `cardapio_olaclick.py`).

Clientes ativos hoje: `kav` (tipo `estatico`, artes 4:5 verticais),
`nn-restaurante` (tipo `fotos`), `ponto-car` (tipo `produto`).

## REGRA #1 — Nunca renomeie ou remova uma função sem buscar todos os usos

Isso já causou **todos** os bugs corrigidos nesta sessão:
`orchestrator.py` chamava `escolher_pauta`, `historico.registrar`,
`historico.agora`, `historico.ultimo_uso_por_produto` — funções que foram
removidas/renomeadas em `utils/historico.py` e `agents/agente_pauta.py` sem
atualizar quem as chamava. Resultado: `AttributeError` / `ImportError`
quebrando a esteira inteira para clientes que não foram testados na hora.

Antes de renomear, remover ou mudar a assinatura de qualquer função:

```bash
grep -rn "nome_da_funcao" --include="*.py" .
```

Atualize **todos** os call sites encontrados, não só o que você está testando
na hora. Depois do grep, rode o smoke test abaixo.

## REGRA #2 — O formato de dados que o backend devolve precisa bater com o que o frontend espera

`app.js` (função `formatarPostParaModal`) lê o post retornado por
`/api/executar` em um formato específico:

```
post.copy.headline_imagem   → headline
post.copy.selo_produto      → selo
post.copy.legenda           → legenda
post.imagem.imagem_b64      → imagem (base64 do PNG final)
```

Se você mudar a estrutura do dicionário `post` em qualquer função de
`orchestrator.py` (`gerar_post`, `gerar_post_fotos`, `gerar_post_estatico_kav`,
`gerar_carrossel`, `gerar_campanha`), **atualize `formatarPostParaModal` em
`escritorio-kav/app.js` também**. Já aconteceu do backend devolver
`"sucesso": true` com todos os dados certos e a tela ficar completamente vazia
("NOVO POST" / "Qualidade Garantida" / legenda em branco) só porque o
mapeamento de campos ficou desatualizado.

## REGRA #3 — Sempre teste de ponta a ponta antes de dizer que terminou

Não basta o código importar sem erro. Teste a rota real:

```bash
# backend
python3 -c "import orchestrator, utils.historico"   # pega ImportError/AttributeError na hora

# esteira completa, sem gastar créditos de imagem
curl -s -X POST http://localhost:8080/api/executar \
  -H "Content-Type: application/json" \
  -d '{"slug":"kav","com_imagem":false,"modo":"organico"}' | python3 -m json.tool

# repita trocando slug para "nn-restaurante" e "ponto-car"
```

Confira que `"sucesso": true` e que `post.copy.headline_imagem` /
`post.copy.legenda` vêm preenchidos, para os **três** clientes — não só o que
você mexeu.

## REGRA #4 — Reinicie o servidor depois de mexer em arquivo `.py`

`server.py` roda com `python3 escritorio-kav/server.py` e **não recarrega
módulos Python editados**. Depois de editar qualquer `.py` (orchestrator,
agents/, utils/), mate o processo antigo e suba de novo antes de testar:

```bash
kill $(lsof -t -i:8080) 2>/dev/null
cd /Users/kesley/Documents/kav-mkt/kav-mkt
python3 escritorio-kav/server.py
```

Arquivos estáticos (`app.js`, `style.css`, `index.html`) **não** precisam de
restart — só dar refresh completo (Cmd+Shift+R) no navegador, porque o
navegador pode ter a aba aberta com o JS antigo em memória.

## REGRA #5 — Sempre sincronize local e GitHub no final

Depois de qualquer alteração testada e funcionando, **sempre**:

```bash
git add -A
git status        # confira o que vai entrar — nunca suba .env ou segredos
git commit -m "mensagem clara do que mudou e por quê"
git push origin main
```

Não deixe alterações só na máquina local sem subir pro GitHub, e não deixe o
GitHub com uma versão diferente do que está rodando localmente. Se `git
status` mostrar mudanças que não foram feitas por você nesta tarefa (ex:
`escritorio-kav/estado_agentes.json` alterado só por causa de testes locais),
não commite esse ruído — reverta com `git checkout -- <arquivo>` antes do
commit.

## Histórico de bugs já corrigidos (não repita)

1. `orchestrator.py` importava `escolher_pauta` de `agents/agente_pauta.py`,
   mas essa função virou `gerar_pauta_kav`. Corrigido.
2. `orchestrator.py` chamava `historico.registrar(slug, dict)` com uma API
   antiga; a função nova é `historico.registrar_post(slug, pauta, copy, ...)`.
   Corrigido no fluxo da Kav; os outros fluxos (produto/fotos/carrossel) usam
   `historico.registrar(slug, dict)` genérico, que foi restaurado em
   `utils/historico.py`.
3. `utils/historico.py` não tinha mais `agora()`, `ultimo_uso_por_produto()`,
   `registrar()`, `carregar()`, `usa_github()` — usados por
   `agents/agente_foto.py` e `agents/agente_catalogo.py`. Restaurados sobre o
   novo modelo de armazenamento (`clientes/<slug>/historico.json`).
4. `escritorio-kav/server.py` quebrava a resposta JSON quando o post continha
   um `Path` (ex: caminho de foto), com `TypeError: Object of type PosixPath
   is not JSON serializable`. Corrigido com `default=str` no `json.dumps`.
5. `escritorio-kav/app.js` esperava campos planos (`item.headline`,
   `item.legenda`, `item.imagem_b64`) mas o backend sempre devolveu campos
   aninhados (`post.copy.headline_imagem`, `post.imagem.imagem_b64`). Corrigido
   com a função `formatarPostParaModal()`.
