"""Kav — Automação de Marketing Multi-Agente (interface web).

Um clique cria um post completo para o cliente: produto escolhido do catálogo, legenda
no padrão do cliente e imagem no layout de referência. Nenhuma postagem é feita em
redes sociais — o resultado é para revisão e publicação manual.
"""
from __future__ import annotations

import base64
import os

import streamlit as st
from dotenv import load_dotenv

st.set_page_config(page_title="Kav — Automação de Marketing", page_icon="🧠", layout="wide")

# Os Secrets do Streamlit Cloud só existem em st.secrets; os módulos do projeto leem
# variáveis de ambiente na importação — por isso a cópia vem antes dos imports abaixo.
load_dotenv()
try:
    for _chave, _valor in st.secrets.items():
        if isinstance(_valor, str) and not os.environ.get(_chave):
            os.environ[_chave] = _valor
except Exception:
    pass  # sem secrets.toml (rodando local só com .env)

from agents.agente_design import ajustar_imagem  # noqa: E402
from orchestrator import gerar_post  # noqa: E402
from utils import historico  # noqa: E402
from utils.cliente import carregar_cliente, listar_clientes  # noqa: E402


def _api_key_configurada() -> bool:
    return bool(os.environ.get("OPENAI_API_KEY"))


@st.cache_data(ttl=300, show_spinner=False)
def _historico_recente(slug: str) -> list:
    return historico.carregar(slug)


def _status_cliente(cliente: dict) -> list:
    produtos = cliente["catalogo"].get("produtos") or []
    atualizado = cliente["catalogo"].get("atualizado_em")
    legenda_provisoria = "PROVISÓRIO" in cliente["legenda_padrao"]
    return [
        (_api_key_configurada(), "Chave da OpenAI"),
        (bool(produtos), f"Catálogo: {len(produtos)} produtos" + (f" ({atualizado})" if atualizado else "")),
        (bool(cliente["referencias"]), f"Referências de layout: {len(cliente['referencias'])}/10"),
        (cliente["logo"] is not None, "Logo"),
        (
            bool(cliente["legenda_padrao"]) and not legenda_provisoria,
            "Padrão de legenda" + (" (provisório)" if legenda_provisoria else ""),
        ),
        (
            historico.usa_github(),
            "Histórico salvo no GitHub" if historico.usa_github() else "Histórico só local (some ao reiniciar)",
        ),
    ]


# ---------------------------------------------------------------------------
# Senha de acesso (opcional — ativa com o secret APP_PASSWORD)
# ---------------------------------------------------------------------------

senha = os.environ.get("APP_PASSWORD")
if senha and not st.session_state.get("autenticado"):
    st.title("🧠 Kav — acesso restrito")
    digitada = st.text_input("Senha de acesso", type="password")
    if st.button("Entrar"):
        if digitada == senha:
            st.session_state.autenticado = True
            st.rerun()
        st.error("Senha incorreta.")
    st.stop()

# ---------------------------------------------------------------------------
# Barra lateral
# ---------------------------------------------------------------------------

st.sidebar.title("🧠 Kav")
st.sidebar.caption("@kav.mkt — automação de marketing multi-agente")

clientes = listar_clientes()
if not clientes:
    st.sidebar.error("Nenhum cliente encontrado em clientes/.")
    st.stop()

slug = st.sidebar.selectbox("Cliente", clientes, format_func=lambda c: c.replace("-", " ").title())
cliente = carregar_cliente(slug)

with st.sidebar.container(border=True):
    for ok, texto in _status_cliente(cliente):
        st.markdown(f"{'✅' if ok else '⚠️'} {texto}")

com_imagem = st.sidebar.checkbox(
    "🎨 Gerar imagem",
    value=True,
    help="Desmarque para testar só o texto: gasta menos crédito e o produto não entra no histórico.",
)
criar = st.sidebar.button(
    "🚀 Criar post", type="primary", use_container_width=True, disabled=not _api_key_configurada()
)

with st.sidebar.expander("ℹ️ Como funciona"):
    st.markdown(
        """
1. **Catálogo** — escolhe um dos mais vendidos da loja que não foi usado nos últimos
   30 dias.
2. **Legenda** — escreve chamada, selo do produto e legenda no padrão do cliente.
3. **Design** — sorteia 1 das referências de layout do cliente e gera a imagem com a
   foto real do produto; o logo é aplicado por cima, idêntico ao original.

Nada é postado automaticamente. O catálogo é atualizado pedindo ao Claude (via Claude
in Chrome) — ver `clientes/README.md`.
        """
    )

# ---------------------------------------------------------------------------
# Criação do post
# ---------------------------------------------------------------------------

if st.session_state.get("post_cliente") != slug:
    st.session_state.post = None
    st.session_state.post_cliente = slug

st.title(cliente["nome"])
st.caption("Catálogo → Legenda → Imagem · texto com gpt-4o-mini, imagem com GPT Image 2.5")

if criar:
    try:
        with st.status("Criando o post...", expanded=True) as status:
            st.session_state.post = gerar_post(slug, com_imagem=com_imagem, etapa=status.write)
            status.update(label="Post criado", state="complete", expanded=False)
        _historico_recente.clear()
    except Exception as exc:
        st.error(f"Não consegui criar o post: {exc}")

post = st.session_state.get("post")
if not post:
    st.info("Clique em **🚀 Criar post** na barra lateral para começar.")
else:
    for aviso in post["avisos"]:
        st.warning(aviso)

    col_imagem, col_texto = st.columns(2)

    with col_imagem, st.container(border=True):
        st.subheader("🎨 Imagem")
        imagem = post["imagem"]
        if not imagem:
            st.caption("Modo teste: imagem não gerada.")
        else:
            final = base64.b64decode(imagem["imagem_b64"])
            st.image(final, use_container_width=True)
            st.download_button(
                "⬇️ Baixar imagem (.png)", data=final, file_name=f"{slug}_{post['produto']['id']}.png", mime="image/png"
            )
            detalhes = [
                f"Layout: {imagem['referencia_layout']}" if imagem.get("referencia_layout") else "Sem referência de layout",
                "com foto real do produto" if imagem.get("com_foto_produto") else None,
                f"{imagem.get('modelo')} · {imagem.get('tamanho')}",
            ]
            st.caption(" · ".join(d for d in detalhes if d))

            with st.form("form_ajuste", clear_on_submit=True):
                instrucao = st.text_input(
                    "🔧 Pedir uma alteração nesta imagem",
                    placeholder="Ex: deixe o céu ao entardecer / aumente o produto",
                )
                aplicar = st.form_submit_button("🪄 Aplicar alteração")
            st.caption("Usa o gpt-image-2.5-sunburst (edição com fidelidade). Cada ajuste é mais uma chamada de imagem.")
            if aplicar and instrucao.strip():
                try:
                    with st.spinner("Aplicando o ajuste..."):
                        novo = ajustar_imagem(base64.b64decode(imagem["imagem_sem_logo_b64"]), instrucao, cliente)
                    post["imagem"] = {**imagem, **novo}
                    st.rerun()
                except Exception as exc:
                    st.error(f"Não consegui aplicar o ajuste: {exc}")

    with col_texto:
        produto = post["produto"]
        with st.container(border=True):
            st.subheader("📦 Produto")
            if produto.get("foto_url"):
                st.image(produto["foto_url"], width=140)
            st.markdown(f"**{produto.get('nome')}**")
            detalhes = [
                produto.get("preco"),
                produto.get("vendidos_texto"),
                f"⭐ {produto['avaliacao']}" if produto.get("avaliacao") else None,
            ]
            if any(detalhes):
                st.caption(" · ".join(str(d) for d in detalhes if d))
            if produto.get("url"):
                st.markdown(f"[Ver na Shopee]({produto['url']})")

        copy = post["copy"]
        with st.container(border=True):
            st.subheader("✍️ Legenda")
            st.markdown(f"**Chamada da imagem:** {copy.get('headline_imagem')}")
            if copy.get("selo_produto"):
                st.markdown(f"**Selo do produto:** {copy['selo_produto']}")
            st.code(copy.get("legenda") or "", language=None, wrap_lines=True)
            st.download_button(
                "⬇️ Baixar legenda (.txt)",
                data=copy.get("legenda") or "",
                file_name=f"{slug}_{produto['id']}.txt",
                mime="text/plain",
            )

        if post["brief"]:
            with st.expander("Brief usado para gerar a imagem"):
                st.code(post["brief"], language=None, wrap_lines=True)

    st.success("Pronto. Nada foi postado automaticamente — revise e publique manualmente.")

# ---------------------------------------------------------------------------
# Histórico
# ---------------------------------------------------------------------------

st.divider()
st.subheader("🕘 Últimos posts deste cliente")
try:
    registros = _historico_recente(slug)
except Exception as exc:
    st.warning(f"Não consegui ler o histórico: {exc}")
    registros = []
if not registros:
    st.caption("Nenhum post registrado ainda.")
for registro in reversed(registros[-15:]):
    quando = (registro.get("data") or "")[:16].replace("T", " ")
    with st.expander(f"{quando} — {registro.get('produto_nome')}"):
        st.markdown(f"**Chamada:** {registro.get('headline')}")
        st.code(registro.get("legenda") or "", language=None, wrap_lines=True)
