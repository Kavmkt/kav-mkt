"""Kav — Automação de Marketing Multi-Agente (interface web).

App Streamlit que expõe a esteira Pauta -> Produto -> Design em uma interface visual,
pronta para publicação gratuita (ex: Streamlit Community Cloud). Não faz nenhuma
postagem em redes sociais — o resultado é sempre para revisão e publicação manual.
"""
from __future__ import annotations

import base64
import json
import os
from datetime import date
from pathlib import Path

import streamlit as st

from agents.agente_design import gerar_imagem, gerar_prompt_imagem
from agents.agente_pauta import gerar_pauta
from agents.agente_produto import buscar_produto, registrar_produto_usado
from utils.skill_loader import carregar_skill, listar_clientes, nome_exibicao

BASE_DIR = Path(__file__).resolve().parent

st.set_page_config(page_title="Kav — Automação de Marketing", page_icon="🧠", layout="wide")


# ---------------------------------------------------------------------------
# Segredos: no Streamlit Community Cloud, os "Secrets" configurados na interface
# só ficam disponíveis via st.secrets (não viram variável de ambiente sozinhos).
# No uso local (.env), eles já chegam via os.environ. Esta ponte faz o mesmo código
# funcionar nos dois casos sem duplicar lógica.
# ---------------------------------------------------------------------------
try:
    if "OPENAI_API_KEY" in st.secrets and not os.environ.get("OPENAI_API_KEY"):
        os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]
except Exception:
    pass  # nenhum secrets.toml configurado (ex: rodando local só com .env) — tudo bem


def _senha_configurada() -> str | None:
    """Senha opcional de acesso ao app (recomendada quando o app fica com URL pública),
    para evitar que outra pessoa gere posts (e gaste sua cota de API) só por ter o link.
    Configure um secret chamado APP_PASSWORD para ativar; se não configurar, o app fica
    aberto para quem tiver o link."""
    try:
        return st.secrets.get("APP_PASSWORD") or os.environ.get("APP_PASSWORD")
    except Exception:
        return os.environ.get("APP_PASSWORD")


def _api_key_configurada() -> bool:
    return bool(os.environ.get("OPENAI_API_KEY"))


def _pasta_saida(cliente: str) -> Path:
    pasta = BASE_DIR / "output" / cliente / date.today().isoformat()
    pasta.mkdir(parents=True, exist_ok=True)
    return pasta


def _salvar_json(pasta: Path, nome: str, dados: dict) -> None:
    (pasta / nome).write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")


def _caminho_historico(cliente: str) -> Path:
    pasta = BASE_DIR / "data" / cliente
    pasta.mkdir(parents=True, exist_ok=True)
    return pasta / "historico_manual.txt"


def _ler_historico(cliente: str) -> str:
    caminho = _caminho_historico(cliente)
    return caminho.read_text(encoding="utf-8") if caminho.exists() else ""


def _montar_resumo(
    cliente: str,
    pauta: dict,
    produto: dict | None,
    prompt_imagem: str,
    imagem_gerada: bool,
) -> str:
    linhas = [
        f"# Resumo da execução — {cliente} ({date.today().isoformat()})",
        "",
        "## Pauta",
        f"- **Tema:** {pauta.get('tema')}",
        f"- **Formato:** {pauta.get('formato', '—')}",
        f"- **Objetivo:** {pauta.get('objetivo')}",
        f"- **Descrição:** {pauta.get('descricao')}",
        f"- **Legenda sugerida:** {pauta.get('legenda_sugerida')}",
        f"- **Hashtags:** {' '.join(pauta.get('hashtags', []))}",
        "",
    ]
    if produto:
        linhas += [
            "## Produto",
            f"- **Nome:** {produto.get('nome')}",
            f"- **Fonte:** {produto.get('fonte')}",
        ]
        if produto.get("fallback_usado"):
            linhas.append(f"- **ATENÇÃO:** {produto.get('aviso')}")
        linhas.append("")
    linhas += [
        "## Brief de imagem (Key Visual)",
        "```",
        prompt_imagem,
        "```",
        f"Imagem gerada: {'sim (ver imagem.png)' if imagem_gerada else 'não'}",
        "",
        "> Nenhuma postagem foi feita automaticamente. Revise o material acima e publique manualmente.",
    ]
    return "\n".join(linhas)


def _historico_execucoes(cliente: str) -> list[Path]:
    pasta_cliente = BASE_DIR / "output" / cliente
    if not pasta_cliente.exists():
        return []
    return sorted(pasta_cliente.glob("*/resumo.md"), reverse=True)


# ---------------------------------------------------------------------------
# Portão de senha (opcional — só ativa se você configurar o secret APP_PASSWORD)
# ---------------------------------------------------------------------------

senha_configurada = _senha_configurada()
if senha_configurada and not st.session_state.get("autenticado"):
    st.title("🧠 Kav — acesso restrito")
    senha_digitada = st.text_input("Senha de acesso", type="password")
    if st.button("Entrar"):
        if senha_digitada == senha_configurada:
            st.session_state.autenticado = True
            st.rerun()
        else:
            st.error("Senha incorreta.")
    st.stop()

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

st.sidebar.title("🧠 Kav")
st.sidebar.caption("@kav.mkt — automação de marketing multi-agente")

clientes = listar_clientes()
if not clientes:
    st.sidebar.error("Nenhuma skill de cliente encontrada em /skills.")
    st.stop()

cliente = st.sidebar.selectbox("Cliente", clientes, format_func=lambda c: c.replace("-", " ").title())
skill = carregar_skill(cliente)

with st.sidebar.expander("📚 Referências de posts anteriores (opcional)"):
    st.caption(
        "Cole aqui exemplos de posts que você já publicou (tema + legenda, um por "
        "linha ou parágrafo). O Agente de Pauta usa isso pra não repetir ideias e pra "
        "aprender o estilo que já funcionou. Fica salvo pra esse cliente."
    )
    historico_texto = st.text_area(
        "Posts anteriores",
        value=st.session_state.get(f"historico_{cliente}", _ler_historico(cliente)),
        height=150,
        label_visibility="collapsed",
        key=f"historico_input_{cliente}",
    )
    if st.button("💾 Salvar referências", key=f"salvar_historico_{cliente}"):
        _caminho_historico(cliente).write_text(historico_texto, encoding="utf-8")
        st.session_state[f"historico_{cliente}"] = historico_texto
        st.success("Salvo.")

st.sidebar.divider()

if _api_key_configurada():
    st.sidebar.success("Chave da API configurada ✅")
else:
    st.sidebar.error(
        "OPENAI_API_KEY não configurada.\n\n"
        "Configure em **Settings → Secrets** (Streamlit Community Cloud) "
        "ou no arquivo `.env` (uso local)."
    )

gerar_imagem_tambem = st.sidebar.checkbox(
    "🎨 Gerar imagem também",
    value=True,
    help="Desmarque para só gerar o texto (pauta) e economizar créditos enquanto estiver testando.",
)

gerar = st.sidebar.button("🚀 Gerar novo post", type="primary", use_container_width=True, disabled=not _api_key_configurada())

with st.sidebar.expander("ℹ️ Como funciona / limitações"):
    st.markdown(
        """
- Nenhuma postagem é feita automaticamente — tudo aqui é para você revisar e publicar
  manualmente.
- A busca de produto na Shopee não é automática nesta versão web (a Shopee bloqueia
  navegação automática comum). Quando a pauta pedir um produto específico, você pode
  colar as informações manualmente, ou deixar em branco para usar um **produto coringa**
  da skill do cliente.
- A imagem sai no formato vertical 1080x1440. A IA gera só a cena (sem texto nenhum) —
  a chamada em português é sobreposta depois por código, com fonte e posição garantidas,
  pra não sair cortada nem embaralhada. É gerada de uma vez só, sem repetir tentativas.
- Desmarque "Gerar imagem também" pra só testar o texto sem gastar crédito de imagem.
- Este é um protótipo: o armazenamento pode ser reiniciado quando o servidor gratuito
  reinicia (é esperado nesta fase).
        """
    )

# ---------------------------------------------------------------------------
# Estado da geração em andamento
# ---------------------------------------------------------------------------

if "cliente_atual" not in st.session_state or st.session_state.cliente_atual != cliente:
    st.session_state.cliente_atual = cliente
    st.session_state.pauta = None
    st.session_state.produto = None
    st.session_state.etapa = None
    st.session_state.prompt_imagem = None
    st.session_state.imagem = None
    st.session_state.imagem_erro = None

if gerar:
    with st.spinner("Agente de Pauta pensando..."):
        st.session_state.pauta = gerar_pauta(skill, historico=historico_texto.strip() or None)
    st.session_state.produto = None
    st.session_state.prompt_imagem = None
    st.session_state.imagem = None
    st.session_state.imagem_erro = None
    st.session_state.gerar_imagem_desta_vez = gerar_imagem_tambem
    st.session_state.etapa = (
        "produto" if st.session_state.pauta.get("requer_produto_especifico") else "design"
    )

# ---------------------------------------------------------------------------
# Corpo principal
# ---------------------------------------------------------------------------

st.title(nome_exibicao(skill["texto_completo"]))
st.caption("Pauta → Produto (se necessário) → Design — gerado com OpenAI (gpt-4o-mini)")

pauta = st.session_state.get("pauta")

if not pauta:
    st.info("Clique em **🚀 Gerar novo post** na barra lateral para começar.")
    st.stop()

# --- Card: Pauta -------------------------------------------------------
with st.container(border=True):
    st.subheader("📋 Pauta do dia")
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"**Tema:** {pauta.get('tema')}")
        if pauta.get("formato"):
            st.caption(f"Ângulo/formato: {pauta['formato']}")
        st.markdown(f"**Descrição:** {pauta.get('descricao')}")
        st.markdown(f"**Legenda sugerida:**")
        st.code(pauta.get("legenda_sugerida", ""), language=None)
        st.markdown(" ".join(pauta.get("hashtags", [])))
        if pauta.get("headline_imagem"):
            st.markdown(f"**Chamada para a imagem:** {pauta['headline_imagem']}")
    with col2:
        st.metric("Objetivo", pauta.get("objetivo", "—"))
        st.metric("Requer produto?", "Sim" if pauta.get("requer_produto_especifico") else "Não")

# --- Card: Produto -------------------------------------------------------
produto = st.session_state.get("produto")

if st.session_state.etapa == "produto" and produto is None:
    with st.container(border=True):
        st.subheader("📦 Produto")
        st.write(
            f"Esta pauta pede um produto da categoria **{pauta.get('categoria_produto')}**. "
            "Se você já sabe qual produto usar (ex: olhou na loja da Shopee), preencha abaixo. "
            "Se deixar em branco, o sistema usa automaticamente um produto coringa da skill."
        )
        with st.form("form_produto"):
            nome_produto = st.text_input("Nome do produto")
            foto_url = st.text_input("URL da foto (opcional)")
            url_produto = st.text_input("Link do produto na Shopee (opcional)")
            col_a, col_b = st.columns(2)
            usar_manual = col_a.form_submit_button("✅ Usar este produto", use_container_width=True)
            usar_coringa = col_b.form_submit_button("🎲 Usar produto coringa", use_container_width=True)

        if usar_manual or usar_coringa:
            produto_manual = (
                {"nome": nome_produto, "foto_url": foto_url or None, "url_produto": url_produto or None}
                if usar_manual and nome_produto
                else None
            )
            with st.spinner("Agente de Produto..."):
                produto = buscar_produto(
                    cliente=cliente,
                    categoria_produto=pauta.get("categoria_produto") or "não especificada",
                    skill=skill,
                    produto_manual=produto_manual,
                )
                registrar_produto_usado(cliente, produto, pauta)
            st.session_state.produto = produto
            st.session_state.etapa = "design"
            st.rerun()
    st.stop()

if produto:
    with st.container(border=True):
        st.subheader("📦 Produto")
        if produto.get("fallback_usado"):
            st.warning(produto.get("aviso"))
        else:
            st.success(f"Produto definido: **{produto.get('nome')}** (fonte: {produto.get('fonte')})")
        if produto.get("foto_url"):
            st.image(produto["foto_url"], width=200)
        if produto.get("url_produto"):
            st.markdown(f"[Ver produto na Shopee]({produto['url_produto']})")

# --- Geração do Design (automática assim que produto/pauta estiverem prontos) ---
if st.session_state.etapa == "design" and st.session_state.prompt_imagem is None:
    with st.spinner("Agente de Design escrevendo o brief da imagem..."):
        prompt_imagem = gerar_prompt_imagem(pauta, produto, skill)
    st.session_state.prompt_imagem = prompt_imagem

    imagem_bytes = None
    if st.session_state.get("gerar_imagem_desta_vez", True):
        try:
            with st.spinner("Gerando a imagem (uma única chamada)..."):
                resultado_imagem = gerar_imagem(prompt_imagem, pauta.get("headline_imagem"), skill, produto)
            if resultado_imagem.get("imagem_b64"):
                imagem_bytes = base64.b64decode(resultado_imagem["imagem_b64"])
                st.session_state.imagem = resultado_imagem
            elif resultado_imagem.get("imagem_url"):
                st.session_state.imagem = resultado_imagem
            else:
                st.session_state.imagem_erro = "A API não retornou nem imagem nem URL."
        except Exception as exc:  # noqa: BLE001 — mostramos o erro real na tela
            st.session_state.imagem_erro = str(exc)

    st.session_state.etapa = "concluido"

    pasta = _pasta_saida(cliente)
    _salvar_json(pasta, "pauta.json", pauta)
    if produto:
        _salvar_json(pasta, "produto.json", produto)
    (pasta / "prompt_imagem.txt").write_text(prompt_imagem, encoding="utf-8")
    if imagem_bytes:
        (pasta / "imagem.png").write_bytes(imagem_bytes)
    resumo = _montar_resumo(cliente, pauta, produto, prompt_imagem, imagem_gerada=bool(imagem_bytes))
    (pasta / "resumo.md").write_text(resumo, encoding="utf-8")
    st.rerun()

# --- Card: Design -------------------------------------------------------
if st.session_state.get("prompt_imagem"):
    with st.container(border=True):
        st.subheader("🎨 Imagem")
        imagem_info = st.session_state.get("imagem")
        if imagem_info:
            if imagem_info.get("imagem_b64"):
                imagem_bytes = base64.b64decode(imagem_info["imagem_b64"])
                st.image(imagem_bytes, use_container_width=True)
                st.download_button(
                    "⬇️ Baixar imagem (.png)",
                    data=imagem_bytes,
                    file_name=f"imagem_{cliente}_{date.today().isoformat()}.png",
                    mime="image/png",
                )
            elif imagem_info.get("imagem_url"):
                st.image(imagem_info["imagem_url"], use_container_width=True)
            if imagem_info.get("com_referencia"):
                st.caption("✅ Gerada a partir da foto real do produto (referência).")
            st.caption(f"Modelo: {imagem_info.get('modelo')} · {imagem_info.get('tamanho')} · qualidade {imagem_info.get('qualidade')}")
        elif st.session_state.get("imagem_erro"):
            st.error(
                f"Não consegui gerar a imagem: {st.session_state.imagem_erro}\n\n"
                "Verifique se sua conta OpenAI tem acesso ao modelo de imagem configurado "
                "e se o billing está ativo. O texto do brief abaixo continua disponível "
                "pra você usar em outra ferramenta, se quiser."
            )
        else:
            st.caption("Geração de imagem desmarcada nesta execução (só texto).")

        with st.expander("Brief de imagem (texto usado para gerar)"):
            st.code(st.session_state.prompt_imagem, language=None)

    resumo_final = _montar_resumo(
        cliente, pauta, produto, st.session_state.prompt_imagem, imagem_gerada=bool(imagem_info)
    )
    st.download_button(
        "⬇️ Baixar resumo (.md)",
        data=resumo_final,
        file_name=f"resumo_{cliente}_{date.today().isoformat()}.md",
        mime="text/markdown",
    )
    st.success("Concluído. Nenhuma postagem foi feita automaticamente — revise e publique manualmente.")

# ---------------------------------------------------------------------------
# Histórico
# ---------------------------------------------------------------------------

st.divider()
st.subheader("🕘 Histórico de gerações")
historico = _historico_execucoes(cliente)
if not historico:
    st.caption("Nenhuma execução anterior encontrada para este cliente.")
else:
    for caminho in historico[:20]:
        data_pasta = caminho.parent.name
        with st.expander(f"{data_pasta}"):
            st.markdown(caminho.read_text(encoding="utf-8"))
