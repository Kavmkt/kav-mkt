"""Servidor Interativo do Escritório Virtual Kav (@kav.mkt).
"""
import json
import os
import sys
import traceback
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
PASTAS_KAV = [
    BASE_DIR.parent,
    BASE_DIR.parent / "kav-mkt",
    BASE_DIR / "kav-mkt",
    BASE_DIR.parent.parent,
    Path.cwd(),
    Path.cwd().parent,
]

for p in PASTAS_KAV:
    if p.exists() and str(p) not in sys.path:
        sys.path.insert(0, str(p))

# Carrega a chave OPENAI_API_KEY do arquivo .env
env_encontrado = None
for p in PASTAS_KAV:
    env_file = p / ".env"
    if env_file.exists():
        env_encontrado = env_file
        try:
            for linha in env_file.read_text(encoding="utf-8").splitlines():
                linha = linha.strip()
                if linha and not linha.startswith("#") and "=" in linha:
                    k, v = linha.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip().strip("'\""))
        except Exception:
            pass
        break


class KavOfficeHandler(SimpleHTTPRequestHandler):
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
            length = int(self.headers.get("Content-Length", 0))
            corpo = self.rfile.read(length).decode("utf-8") if length > 0 else "{}"
            params = json.loads(corpo) if corpo else {}
            slug = params.get("slug", "nn-restaurante")
            com_imagem = params.get("com_imagem", True)
            modo = params.get("modo", "campanha")

            resultado = self._executar_agentes(slug, com_imagem=com_imagem, modo=modo)
            self._resposta_json(resultado, status=200 if resultado.get("sucesso") else 400)
            return

        self.send_error(404, "Endpoint não encontrado")

    def _resposta_json(self, dados, status=200):
        conteudo = json.dumps(dados, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(conteudo)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(conteudo)

    def _listar_clientes(self):
        try:
            from utils.cliente import listar_clientes, carregar_cliente
            slugs = listar_clientes()
            lista = []
            for s in slugs:
                try:
                    c = carregar_cliente(s)
                    tipo = c.get("config", {}).get("tipo", "produto")
                    icone = "🍽️" if tipo == "fotos" else ("🧠" if tipo == "carrossel" else "🚗")
                    lista.append({"slug": s, "nome": c.get("nome", s), "tipo": tipo, "icone": icone})
                except Exception:
                    lista.append({"slug": s, "nome": s.replace("-", " ").title(), "tipo": "produto", "icone": "💼"})
            return lista
        except Exception:
            return [
                {"slug": "nn-restaurante", "nome": "NN Restaurante", "tipo": "fotos", "icone": "🍽️"},
                {"slug": "ponto-car", "nome": "Ponto Car", "tipo": "produto", "icone": "🚗"},
                {"slug": "kav", "nome": "Kav (@kav.mkt)", "tipo": "carrossel", "icone": "🧠"},
            ]

    def _obter_estado(self):
        try:
            from utils import estado_agentes
            return estado_agentes.carregar_estado()
        except Exception:
            arquivo = BASE_DIR / "estado_agentes.json"
            if arquivo.exists():
                try:
                    return json.loads(arquivo.read_text(encoding="utf-8"))
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
            traceback.print_exc()
            return {"sucesso": False, "erro": str(exc)}


def main():
    porta = 8080
    servidor = HTTPServer(("0.0.0.0", porta), KavOfficeHandler)
    key = os.environ.get("OPENAI_API_KEY")
    status_key = f"✅ Ativa ({key[:6]}...{key[-4:]})" if key else "⚠️ NÃO ENCONTRADA (Verifique o arquivo .env)"

    print("\n=======================================================")
    print(f"🏢 Escritório Virtual da Kav ativo em: http://localhost:{porta}")
    print(f"🔑 Chave OpenAI: {status_key}")
    if env_encontrado:
        print(f"📄 Arquivo .env carregado de: {env_encontrado}")
    print(f"👉 Abra http://localhost:{porta} no seu navegador!")
    print("=======================================================\n")
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor finalizado.")


if __name__ == "__main__":
    main()
