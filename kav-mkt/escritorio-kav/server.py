"""Servidor HTTP simples para o Escritório Virtual da Kav (@kav.mkt).

Serve os arquivos estáticos de `escritorio-kav/` (HTML, CSS, JS, imagens) e fornece a API
para a interface interagir com a esteira real de agentes de IA:

Rotas:
- GET  /              -> Serve index.html
- GET  /api/clientes  -> Lista clientes disponíveis em clientes/ (nome, slug, tipo)
- GET  /api/estado    -> Retorna estado_agentes.json atualizado
- POST /api/executar  -> Dispara a esteira real do orchestrator.py e devolve o post completo

Execução:
    cd /Users/kesley/Documents/kav-mkt/kav-mkt
    source .venv/bin/activate
    python3 escritorio-kav/server.py
"""
import http.server
import json
import os
import socketserver
import sys
from pathlib import Path

# Garante que imports como 'orchestrator' e 'utils' funcionem a partir da raiz do kav-mkt
BASE_DIR = Path(__file__).resolve().parent
RAIZ_PROJETO = BASE_DIR.parent
if str(RAIZ_PROJETO) not in sys.path:
    sys.path.insert(0, str(RAIZ_PROJETO))

# Carrega variáveis de ambiente automaticamente (.env)
try:
    from dotenv import load_dotenv
    load_dotenv(RAIZ_PROJETO / ".env")
    load_dotenv(RAIZ_PROJETO.parent / ".env")
    load_dotenv()
except Exception:
    pass

PORTA = int(os.environ.get("PORT", 8080))


class KavRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Handler HTTP customizado com suporte a API JSON e arquivos estáticos."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(BASE_DIR), **kwargs)

    def do_GET(self):
        caminho = self.path.split("?")[0]
        if caminho == "/api/clientes":
            self._resposta_json(self._listar_clientes())
            return
        elif caminho == "/api/estado":
            self._resposta_json(self._obter_estado())
            return
        return super().do_GET()

    def do_POST(self):
        caminho = self.path.split("?")[0]
        if caminho == "/api/executar":
            try:
                length = int(self.headers.get("Content-Length", 0))
                corpo = self.rfile.read(length).decode("utf-8") if length > 0 else "{}"
                params = json.loads(corpo) if corpo else {}
                slug = params.get("slug", "nn-restaurante")
                com_imagem = params.get("com_imagem", True)
                modo = params.get("modo", "campanha")

                resultado = self._executar_agentes(slug, com_imagem=com_imagem, modo=modo)
                self._resposta_json(resultado, status=200 if resultado.get("sucesso") else 400)
            except Exception as exc:
                import traceback
                traceback.print_exc()
                self._resposta_json({"sucesso": False, "erro": str(exc)}, status=500)
            return

        self.send_error(404, "Endpoint não encontrado")

    def _resposta_json(self, dados, status=200):
        conteudo = json.dumps(dados, ensure_ascii=False, indent=2, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(conteudo)))
        self.end_headers()
        self.wfile.write(conteudo)

    def _listar_clientes(self):
        clientes_dir = RAIZ_PROJETO / "clientes"
        lista = []
        if clientes_dir.exists():
            for pasta in sorted(clientes_dir.iterdir()):
                if pasta.is_dir() and not pasta.name.startswith("."):
                    cfg_file = pasta / "config.json"
                    nome = pasta.name
                    tipo = "produto"
                    if cfg_file.exists():
                        try:
                            cfg = json.loads(cfg_file.read_text(encoding="utf-8"))
                            nome = cfg.get("nome", pasta.name)
                            tipo = cfg.get("tipo", "produto")
                        except Exception:
                            pass
                    lista.append({"slug": pasta.name, "nome": nome, "tipo": tipo})
        return {"clientes": lista}

    def _obter_estado(self):
        arquivo_estado = BASE_DIR / "estado_agentes.json"
        if arquivo_estado.exists():
            try:
                return json.loads(arquivo_estado.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {}

    def _executar_agentes(self, slug, com_imagem=True, modo="campanha"):
        print(f"\n🚀 [Execução Iniciada] Disparando esteira de agentes ({modo.upper()}) para o cliente '{slug}'...")
        try:
            import orchestrator
            from utils.cliente import carregar_cliente
            from utils import estado_agentes
            cliente = carregar_cliente(slug)
            tipo = cliente.get("config", {}).get("tipo", "produto")

            if modo == "campanha":
                post = orchestrator.gerar_campanha(slug, com_imagem=com_imagem)
            elif tipo == "fotos":
                post = orchestrator.gerar_post_fotos(slug, com_imagem=com_imagem)
            elif tipo == "carrossel":
                num_paginas = cliente.get("config", {}).get("paginas_padrao", 5)
                post = orchestrator.gerar_carrossel(slug, num_paginas=num_paginas, com_imagem=com_imagem)
            else:
                post = orchestrator.gerar_post(slug, com_imagem=com_imagem)

            try:
                estado_agentes.registrar_post_produzido(post, slug)
            except Exception:
                pass

            print(f"🎉 Entrega concluída para {cliente['nome']}!\n")
            return {"sucesso": True, "post": post}
        except Exception as exc:
            print("\n❌ ERRO NA EXECUÇÃO DOS AGENTES:")
            import traceback
            traceback.print_exc()
            return {"sucesso": False, "erro": str(exc)}


def main():
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORTA), KavRequestHandler) as httpd:
        print("=" * 60)
        print("🏢  KAV MARKETING — ESCRITÓRIO VIRTUAL DE AGENTES DE IA")
        print("=" * 60)
        print(f"📡  Servidor HTTP ativo em: http://localhost:{PORTA}")
        print(f"📂  Diretório base: {BASE_DIR}")
        print("⌨️   Pressione Ctrl+C para encerrar o servidor.")
        print("=" * 60 + "\n")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Servidor encerrado.")


if __name__ == "__main__":
    main()
