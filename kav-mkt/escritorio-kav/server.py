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
        if self.path == "/api/clientes":
            self._resposta_json(self._listar_clientes())
            return
        elif self.path == "/api/estado":
            self._resposta_json(self._obter_estado())
            return
        return super().do_GET()

    def do_POST(self):
        if self.path == "/api/executar":
            length = int(self.headers.get("Content-Length", 0))
            corpo = self.rfile.read(length).decode("utf-8") if length > 0 else "{}"
            params = json.loads(corpo) if corpo else {}
            slug = params.get("slug", "nn-restaurante")
            com_imagem = params.get("com_imagem", True)
            modo = params.get("modo", "organico")

            resultado = self._executar_agentes(slug, com_imagem, modo)
            self._resposta_json(resultado, status=200 if resultado.get("sucesso") else 400)
            return

        self.send_error(404, "Endpoint não encontrado")

    def _resposta_json(self, dados, status=200):
        conteudo = json.dumps(dados, ensure_ascii=False, indent=2, default=str).encode("utf-8")
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

    def _executar_agentes(self, slug, com_imagem=True, modo="organico"):
        rotulo_modo = "CAMPANHA (Meta Ads)" if modo == "campanha" else "orgânico"
        print(f"\n🚀 [Execução Iniciada] Disparando esteira de agentes ({rotulo_modo}) para o cliente '{slug}'...")
        try:
            from utils.cliente import carregar_cliente
            from utils import estado_agentes
            cliente = carregar_cliente(slug)
            tipo = cliente.get("config", {}).get("tipo", "produto")

            if modo == "campanha":
                import orchestrator
                print("🎯 Modo campanha: estratégia de performance + arte de anúncio (Meta Ads)...")
                post = orchestrator.gerar_campanha(slug, com_imagem=com_imagem)
            elif tipo == "fotos":
                from agents.agente_design import escolher_referencia
                from agents.agente_design_fotos import gerar_brief_foto, gerar_imagem_foto

                try:
                    from agents.agente_legenda_fotos import gerar_legenda_foto as gerar_copy_foto
                except ImportError:
                    from agents.agente_legenda_fotos import gerar_copy_foto

                fotos = cliente.get("fotos") or []
                if not fotos:
                    print("ℹ️ Nenhuma foto real encontrada na pasta fotos/ — gerando foto base de prato para teste...")
                    pasta_cli = BASE_DIR.parent / "clientes" / slug / "fotos"
                    pasta_cli.mkdir(parents=True, exist_ok=True)
                    foto_padrao = pasta_cli / "buffet_executivo.jpg"
                    if not foto_padrao.exists():
                        try:
                            from PIL import Image, ImageDraw
                            img = Image.new("RGB", (1080, 1440), (45, 42, 40))
                            draw = ImageDraw.Draw(img)
                            draw.ellipse([140, 320, 940, 1120], fill=(245, 243, 238), outline=(210, 205, 195), width=16)
                            draw.ellipse([200, 380, 880, 1060], fill=(160, 50, 30))
                            img.save(foto_padrao, format="JPEG", quality=90)
                        except Exception:
                            pass
                    cliente["fotos"] = [{
                        "arquivo": foto_padrao,
                        "nome": "Buffet Executivo Completo",
                        "categoria": "Almoço Presencial",
                        "descricao": "Buffet farto e variado com comida caseira e saladas frescas",
                        "preco": "R$ 29,90"
                    }]

                from agents.agente_foto import escolher_foto
                foto = escolher_foto(cliente)
                print(f"📸 1/3: Foto selecionada: {foto.get('nome') or foto['arquivo'].name}")

                copy = gerar_copy_foto(foto, cliente)
                print(f"✍️ 2/3: Copy gerada: \"{copy.get('headline_imagem')}\"")

                referencia = escolher_referencia(cliente)
                brief = gerar_brief_foto(copy, foto, cliente, referencia)
                print("🎨 3/3: Brief visual montado. Chamando API de imagem da OpenAI...")

                imagem = gerar_imagem_foto(brief, foto, cliente, referencia) if com_imagem else None
                print("✅ Imagem gerada com sucesso!")

                post = {
                    "cliente": cliente["nome"],
                    "foto": foto,
                    "copy": copy,
                    "referencia": referencia,
                    "brief": brief,
                    "imagem": imagem,
                    "avisos": []
                }
            elif tipo == "carrossel":
                import orchestrator
                num_paginas = cliente.get("config", {}).get("paginas_padrao", 5)
                post = orchestrator.gerar_carrossel(slug, num_paginas=num_paginas, com_imagem=com_imagem)
            else:
                import orchestrator
                post = orchestrator.gerar_post(slug, com_imagem=com_imagem)

            try:
                estado_agentes.registrar_post_produzido(post, slug)
            except Exception:
                pass

            print(f"🎉 Entrega concluída com sucesso para {cliente['nome']}!\n")
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
