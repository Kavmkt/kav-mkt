/**
 * Escritório Virtual dos Agentes de IA — Kav Marketing & Performance
 * Frontend interativo estilo Habbo Hotel com animações isométricas,
 * balões de fala, terminal de logs e visualizador de posts.
 */

document.addEventListener("DOMContentLoaded", () => {
  const selectCliente = document.getElementById("select-cliente");
  const btnProduzir = document.getElementById("btn-produzir");
  const btnDemo = document.getElementById("btn-demo");
  const btnLimparChat = document.getElementById("btn-limpar-chat");
  const chatStream = document.getElementById("chat-stream");
  const labelStatus = document.getElementById("label-status");

  const previewImage = document.getElementById("preview-image-container");
  const previewHeadline = document.getElementById("preview-headline");
  const previewCaption = document.getElementById("preview-caption");
  const previewTagStatus = document.getElementById("preview-tag-status");

  const modalEntrega = document.getElementById("modal-entrega");
  const btnFecharModal = document.getElementById("btn-fechar-modal");
  const modalConteudo = document.getElementById("modal-conteudo");

  let emExecucao = false;

  // Carrega lista de clientes do backend
  carregarClientes();

  // Polling de status do servidor a cada 3 segundos
  setInterval(atualizarStatusServidor, 3000);

  // ==========================================
  // EVENTOS DE BOTÃO
  // ==========================================

  btnProduzir.addEventListener("click", () => {
    if (emExecucao) return;
    executarProducaoReal();
  });

  btnDemo.addEventListener("click", () => {
    if (emExecucao) return;
    executarDemoHabbo();
  });

  btnLimparChat.addEventListener("click", () => {
    chatStream.innerHTML = "";
    adicionarLogChat("Sistema", "Histórico de diálogo limpo.", "system");
  });

  btnFecharModal.addEventListener("click", () => {
    modalEntrega.classList.add("hidden");
  });

  // ==========================================
  // FUNÇÕES DE COMUNICAÇÃO COM O BACKEND
  // ==========================================

  async function carregarClientes() {
    try {
      const resp = await fetch("/api/clientes");
      if (!resp.ok) return;
      const clientes = await resp.json();
      if (!Array.isArray(clientes) || clientes.length === 0) return;

      selectCliente.innerHTML = "";
      clientes.forEach((c) => {
        const opt = document.createElement("option");
        opt.value = c.slug;
        opt.textContent = `${c.icone || "💼"} ${c.nome}`;
        selectCliente.appendChild(opt);
      });
    } catch (err) {
      console.warn("Não foi possível carregar clientes dinamicamente:", err);
    }
  }

  async function atualizarStatusServidor() {
    try {
      const resp = await fetch("/api/status");
      if (resp.ok) {
        labelStatus.textContent = "4 AGENTES ONLINE";
        labelStatus.classList.remove("status-offline");
      } else {
        labelStatus.textContent = "AGENTS OFF";
        labelStatus.classList.add("status-offline");
      }
    } catch {
      labelStatus.textContent = "MODO LOCAL / DEMO";
      labelStatus.classList.add("status-offline");
    }
  }

  async function executarProducaoReal() {
    emExecucao = true;
    bloquearBotoes(true);
    resetarVisualizadores();

    const slug = selectCliente.value;
    adicionarLogChat("Sistema", `Disparando ordem de produção para: ${slug.toUpperCase()}...`, "system");

    // Inicia a encenação visual dos avatares no escritório
    iniciarSequenciaAvatares();

    try {
      const resp = await fetch("/api/executar", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ slug, com_imagem: true, modo: "organico" }),
      });

      const data = await resp.json();

      if (data.sucesso && data.post) {
        finalizarProducaoComSucesso(data.post);
      } else {
        finalizarProducaoComErro(data.erro || "Falha desconhecida na execução dos agentes.");
      }
    } catch (err) {
      adicionarLogChat("Sistema", `Erro de conexão: ${err.message}. Ativando modo de demonstração.`, "error");
      setTimeout(() => executarDemoHabbo(), 1000);
    } finally {
      emExecucao = false;
      bloquearBotoes(false);
    }
  }

  // ==========================================
  // SIMULAÇÃO VISUAL COMPLETA (MODO DEMO)
  // ==========================================

  function executarDemoHabbo() {
    emExecucao = true;
    bloquearBotoes(true);
    resetarVisualizadores();

    const slug = selectCliente.value;
    adicionarLogChat("Sistema", `Modo Simulação ativado para: ${slug.toUpperCase()}`, "system");

    // Etapa 1: Benedito
    animarAgente("curador", "Benedito", "Curador", "Selecionando foto do prato mais apetitoso...", 0);

    // Etapa 2: Clarice
    setTimeout(() => {
      animarAgente("copywriter", "Clarice", "Redatora", "Escrevendo headline magnética e legenda persuasiva...", 0);
    }, 1800);

    // Etapa 3: Joaquim
    setTimeout(() => {
      animarAgente("designer", "Joaquim", "Designer", "Aplicando corte 4:5 e diagramação com logo da marca...", 0);
    }, 3600);

    // Etapa 4: Otávio
    setTimeout(() => {
      animarAgente("diretor_arte", "Otávio", "Diretor", "Examinando contraste visual e legibilidade para feed...", 0);
    }, 5400);

    // Conclusão
    setTimeout(() => {
      const isKav = slug === "kav";
      const postSimulado = isKav
        ? {
            cliente: "kav",
            prato: "Tráfego Local no Raio Certo",
            headline: "PARE DE ANUNCIAR PRA CIDADE INTEIRA",
            selo: "KAV · PERFORMANCE",
            legenda:
              "Seu cliente ideal está a menos de 10 minutos da sua porta. 🎯📍\n\nQuando você fecha o raio para 3 a 7 km em volta do seu endereço, cada centavo do seu orçamento trabalha para impactar quem realmente compra de você hoje.\n\n👉 Mande um direct para mapearmos o raio do seu negócio!\n\n#KavMkt #TrafegoPagoLocal #MarketingParaPMEs #NegociosLocais",
            imagem_b64: null,
            criadores: "Pauta IA: Benedito · Texto: Clarice · Arte: Joaquim · Direção: Otávio",
            aprovacao: { nota: 9.8, aprovado: true, parecer: "Layout de alto impacto B2B com paleta oficial da Kav." },
          }
        : {
            cliente: "nn-restaurante",
            prato: "Prato Executivo Especial",
            headline: "Feito no Capricho para o Almoço",
            selo: "Qualidade Garantida",
            legenda:
              "Aquele almoço saboroso com tempero de casa e ingredientes frescos preparados especialmente pra você. 🍽️\n\nVem saborear o verdadeiro almoço brasileiro no NN Restaurante!\n\nPeça já pelo WhatsApp ou venha nos visitar em Santana de Parnaíba.\n\n#NNRestaurante #ComidaCaseira #Almoço #Gastronomia #SantanaDeParnaiba",
            imagem_b64: null,
            criadores: "Curadoria: Benedito · Texto: Clarice · Arte: Joaquim · Direção: Otávio",
            aprovacao: { nota: 9.5, aprovado: true, parecer: "Excelente apetite appeal e hierarquia tipográfica." },
          };

      finalizarProducaoComSucesso(postSimulado);
      emExecucao = false;
      bloquearBotoes(false);
    }, 7200);
  }

  // ==========================================
  // ANIMAÇÕES DOS AVATARES ESTILO HABBO
  // ==========================================

  function iniciarSequenciaAvatares() {
    animarAgente("curador", "Benedito", "Curador", "Analisando material e pautas...", 0);
    setTimeout(() => animarAgente("copywriter", "Clarice", "Redatora", "Redigindo copy de alta conversão...", 0), 2000);
    setTimeout(() => animarAgente("designer", "Joaquim", "Designer", "Renderizando arte em 1080x1350...", 0), 4500);
    setTimeout(() => animarAgente("diretor_arte", "Otávio", "Diretor", "Auditando composição e branding...", 0), 7500);
  }

  function animarAgente(idDesk, nome, cargo, fala, delayMs) {
    setTimeout(() => {
      const desk = document.getElementById(`desk-${idDesk}`);
      if (!desk) return;

      const bubble = desk.querySelector(".avatar-bubble");
      const avatar = desk.querySelector(".habbo-avatar");

      // Animação de fala e pulo
      desk.classList.add("agent-active");
      if (avatar) avatar.classList.add("avatar-speaking");

      if (bubble) {
        bubble.textContent = fala;
        bubble.classList.add("bubble-visible");
      }

      adicionarLogChat(nome, fala, "agent");

      // Some o balão após 3.5 segundos
      setTimeout(() => {
        desk.classList.remove("agent-active");
        if (avatar) avatar.classList.remove("avatar-speaking");
        if (bubble) bubble.classList.remove("bubble-visible");
      }, 3500);
    }, delayMs);
  }

  // ==========================================
  // RENDERIZAÇÃO DA ENTREGA DO POST
  // ==========================================

  function finalizarProducaoComSucesso(post) {
    adicionarLogChat("Otávio", `POST APROVADO! Nota: ${post.aprovacao?.nota || "10"}/10. Excelente trabalho, equipe!`, "boss");

    previewTagStatus.textContent = "Aprovado ✓";
    previewTagStatus.className = "preview-badge badge-success";

    previewHeadline.textContent = post.headline || "Headline Oficial";
    previewCaption.textContent = post.legenda || "Legenda do post...";

    if (post.imagem_b64) {
      previewImage.innerHTML = `<img src="data:image/png;base64,${post.imagem_b64}" alt="Post Gerado" class="rendered-post-img" />`;
    } else {
      previewImage.innerHTML = `
        <div class="mockup-placeholder-art">
          <div class="art-badge">${post.selo || "KAV PERFORMANCE"}</div>
          <h2 class="art-headline">${post.headline || "HEADLINE IMPACTANTE"}</h2>
          <p class="art-subhead">${post.prato || "Marketing Descomplicado para PMEs"}</p>
          <div class="art-footer-tag">@kav.mkt · 1080x1350</div>
        </div>
      `;
    }

    // Abre o modal de comemoração
    abrirModalSucesso(post);
  }

  function finalizarProducaoComErro(erro) {
    adicionarLogChat("Sistema", `Erro na produção: ${erro}`, "error");
    previewTagStatus.textContent = "Erro ✕";
    previewTagStatus.className = "preview-badge badge-error";
  }

  function abrirModalSucesso(post) {
    modalConteudo.innerHTML = `
      <div class="modal-approved-card">
        <div class="stamp-approved">APROVADO</div>
        <h3>${post.headline || "Arte Concluída"}</h3>
        <p class="modal-sub">${post.prato || "Post de Tráfego Local"}</p>
        <div class="modal-meta-box">
          <div><strong>Cliente:</strong> ${post.cliente?.toUpperCase()}</div>
          <div><strong>Nota da Direção:</strong> ${post.aprovacao?.nota || 10}/10</div>
          <div><strong>Equipe:</strong> ${post.criadores || "Benedito, Clarice, Joaquim e Otávio"}</div>
        </div>
        <div class="modal-actions">
          <button id="btn-copiar-legenda" class="habbo-btn habbo-btn-gold">📋 Copiar Legenda</button>
        </div>
      </div>
    `;

    document.getElementById("btn-copiar-legenda").addEventListener("click", () => {
      navigator.clipboard.writeText(post.legenda || "");
      alert("Legenda copiada para a área de transferência!");
    });

    modalEntrega.classList.remove("hidden");
  }

  // ==========================================
  // UTILITÁRIOS DE TELA E LOGS
  // ==========================================

  function adicionarLogChat(autor, texto, tipo = "agent") {
    const hora = new Date().toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit", second: "2-digit" });
    const msg = document.createElement("div");
    msg.className = `chat-msg ${tipo}`;
    msg.innerHTML = `<span class="msg-time">[${hora}]</span> <strong>${autor}:</strong> ${texto}`;
    chatStream.appendChild(msg);
    chatStream.scrollTop = chatStream.scrollHeight;
  }

  function bloquearBotoes(bloquear) {
    btnProduzir.disabled = bloquear;
    btnDemo.disabled = bloquear;
    selectCliente.disabled = bloquear;
    btnProduzir.classList.toggle("btn-disabled", bloquear);
    btnDemo.classList.toggle("btn-disabled", bloquear);
  }

  function resetarVisualizadores() {
    previewTagStatus.textContent = "Produzindo...";
    previewTagStatus.className = "preview-badge badge-producing";
    previewImage.innerHTML = `
      <div class="loading-spinner-box">
        <span class="spinner-pixel">⏳</span>
        <span>Equipe criando a arte...</span>
      </div>
    `;
    previewHeadline.textContent = "Carregando...";
    previewCaption.textContent = "Aguardando entrega da copywriter Clarice...";
  }
});
