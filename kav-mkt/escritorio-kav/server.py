#!/usr/bin/env python3
"""Servidor HTTP simples para o Escritório Virtual Kav.

Serve os arquivos estáticos da pasta escritorio-kav/ e expõe endpoints
de API para disparar a execução dos agentes no backend.
"""
from http.server import HTTPServer, SimpleHTTPRequestHandler
import json
import os
from pathlib import Path
import sys
import threading
import urllib.parse

# Adiciona a raiz do projeto ao path para importar orchestrator e utils
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import orchestrator
from utils import estado_agentes, historico
from utils.cliente import carregar_cliente, listar_clientes, tipo_cliente

PORTA = int(os.environ.get("PORTA_ESCRITORIO", 8080))
DIRETORIO_STATIC = Path(__file__).resolve().parent


class EscritorioHandler(SimpleHTTPRequestHandler):
    """Handler HTTP customizado para servir static files e rotas de API."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DIRETORIO_STATIC), **kwargs)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)

        if parsed.path == "/api/status":
            self._responder_json(200, {
                "online": True,
                "logs": estado_agentes.obter_logs(),
                "porta": PORTA
            })
            return

        if parsed.path == "/api/clientes":
            self._responder_json(200, self._listar_clientes())
            return

        if parsed.path.startswith("/api/historico/"):
            slug = parsed.path.replace("/api/historico/", "").strip()
            self._responder_json(200, historico.listar_posts_cliente(slug))
            return

        # Rota raiz ou arquivos estáticos
        if parsed.path in ("/", ""):
            self.path = "/index.html"

        return super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)

        if parsed.path == "/api/executar":
            tamanho = int(self.headers.get("Content-Length", 0))
            corpo = self.rfile.read(tamanho) if tamanho > 0 else b"{}"

            try:
                dados = json.loads(corpo.decode("utf-8"))
            except Exception:
                dados = {}

            slug = dados.get("slug", "nn-restaurante")
            com_imagem = bool(dados.get("com_imagem", True))
            modo = dados.get("modo", "organico")

            try:
                resultado = self._executar_agentes(slug, com_imagem, modo)
                self._responder_json(200, {
                    "sucesso": True,
                    "post": resultado
                })
            except Exception as exc:
                self._responder_json(400, {
                    "sucesso": False,
                    "erro": str(exc),
                    "logs": estado_agentes.obter_logs()
                })
            return

        self._responder_json(404, {"erro": "Rota não encontrada"})

    def _responder_json(self, status: int, payload: dict | list):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8"))

    def _listar_clientes(self) -> list:
        slugs = listar_clientes()
        clientes = []
        for s in slugs:
            try:
                c = carregar_cliente(s)
                tipo = tipo_cliente(c)
                icone = "🍽️" if tipo == "fotos" else ("🚀" if tipo == "estatico" else ("🧠" if tipo == "carrossel" else "🚗"))
                clientes.append({
                    "slug": s,
                    "nome": c.get("nome", s),
                    "tipo": tipo,
                    "icone": icone
                })
            except Exception:
                continue
        return clientes

    def _executar_agentes(self, slug: str, com_imagem: bool, modo: str) -> dict:
        cliente = carregar_cliente(slug)
        tipo = tipo_cliente(cliente)

        if slug == "kav" or tipo == "estatico":
            post = orchestrator.gerar_post_estatico_kav(slug, com_imagem=com_imagem)
            return {
                "cliente": slug,
                "prato": post.get("pauta", {}).get("tema"),
                "headline": post.get("copy", {}).get("headline_imagem"),
                "selo": post.get("copy", {}).get("selo_produto"),
                "legenda": post.get("copy", {}).get("legenda"),
                "imagem_b64": post.get("imagem", {}).get("imagem_b64") if post.get("imagem") else None,
                "criadores": "Pauta IA: Benedito · Texto: Clarice · Arte: Joaquim · Direção: Otávio",
                "referencia": post.get("referencia"),
                "aprovacao": post.get("aprovacao"),
                "logs": post.get("logs", [])
            }
        elif tipo == "fotos":
            post = orchestrator.gerar_post_fotos(slug, com_imagem=com_imagem)
            return {
                "cliente": slug,
                "prato": post.get("foto", {}).get("prato"),
                "headline": post.get("copy", {}).get("headline_imagem"),
                "selo": post.get("copy", {}).get("selo_produto"),
                "legenda": post.get("copy", {}).get("legenda"),
                "imagem_b64": post.get("imagem", {}).get("imagem_b64") if post.get("imagem") else None,
                "criadores": "Curadoria: Benedito · Texto: Clarice · Arte: Joaquim · Direção: Otávio",
                "referencia": post.get("referencia"),
                "aprovacao": post.get("aprovacao"),
                "logs": post.get("logs", [])
            }
        else:
            post = orchestrator.gerar_post_campanha(slug, com_imagem=com_imagem)
            return {
                "cliente": slug,
                "prato": post.get("estrategia", {}).get("angulo"),
                "headline": post.get("copy", {}).get("headline"),
                "selo": "CAMPANHA META ADS",
                "legenda": post.get("copy", {}).get("texto_principal"),
                "imagem_b64": None,
                "criadores": "Estratégia: Benedito · Texto: Clarice · Arte: Joaquim · Direção: Otávio",
                "referencia": post.get("referencia"),
                "logs": post.get("logs", [])
            }


def iniciar_servidor():
    print(f"🚀 Iniciando Escritório Virtual Kav em http://localhost:{PORTA}")
    print(f"📁 Servindo estáticos de: {DIRETORIO_STATIC}")
    httpd = HTTPServer(("0.0.0.0", PORTA), EscritorioHandler)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Servidor encerrado.")
        httpd.server_close()


if __name__ == "__main__":
    iniciar_servidor()
