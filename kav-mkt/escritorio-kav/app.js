// Kav — Escritório Virtual de Agentes de IA
// Sistema de movimentação autônoma, corrida ao dar o Play e diálogos por Emojis

// Coordenadas das Estações de Trabalho (Desks)
const COORD_DESKS = {
  supervisor:  { left: 490, top: 120 }, // Augusto
  diretor:     { left: 870, top: 120 }, // Otávio
  metricas:    { left: 490, top: 310 }, // Vicente
  copywriter:  { left: 870, top: 310 }, // Clarice
  pesquisador: { left: 490, top: 500 }, // Benedito
  designer:    { left: 870, top: 500 }  // Joaquim
};

// Coordenadas dos Pontos de Convivência na Área do Café (Kav Café & Lounge)
const COORD_CAFE = {
  supervisor:  { left: 90,  top: 530 }, // Sofá lounge
  diretor:     { left: 230, top: 530 }, // Sofá lounge
  metricas:    { left: 240, top: 190 }, // Bebedouro de água
  copywriter:  { left: 100, top: 310 }, // Mesa bistrô (banqueta esquerda)
  pesquisador: { left: 80,  top: 190 }, // Balcão da máquina de café
  designer:    { left: 220, top: 310 }  // Mesa bistrô (banqueta direita)
};

// Banco de Emojis para interações fictícias 100% visuais (SEM TEXTO)
const EMOJIS_CAFE = ["☕", "🍩", "🥐", "🥪", "💬", "😋", "🥤", "✨", "💡", "💭", "🍕", "😄", "🤝"];
const EMOJIS_TRABALHO = {
  supervisor:  ["👔", "⚡", "🧠", "⏱️", "🤝", "🎯"],
  diretor:     ["🧐", "🔍", "🎯", "💎", "✅", "✨"],
  metricas:    ["📊", "📈", "💻", "🚀", "📱", "⚡"],
  copywriter:  ["✍️", "📝", "💡", "🔥", "🏷️", "✨"],
  pesquisador: ["📸", "🍽️", "🍗", "🗂️", "🔍", "👌"],
  designer:    ["🎨", "📐", "🖼️", "🖌️", "✨", "💫"]
};
const EMOJIS_FESTA = ["🎉", "🥳", "🏆", "👏", "✅", "⭐", "🍕", "🙌"];

const DADOS_AGENTES = {
  supervisor:  { id: "supervisor",  nome: "Augusto",  cargo: "Supervisor de Operações",       dept: "Diretoria" },
  diretor:     { id: "diretor",     nome: "Otávio",   cargo: "Diretor de Arte Sênior",        dept: "Criação" },
  metricas:    { id: "metricas",    nome: "Vicente",  cargo: "Analista de Tráfego & Métricas", dept: "Performance" },
  copywriter:  { id: "copywriter",  nome: "Clarice",  cargo: "Redatora & Copywriter",         dept: "Criação" },
  pesquisador: { id: "pesquisador", nome: "Benedito", cargo: "Curador de Fotos & Cardápio",   dept: "Planejamento" },
  designer:    { id: "designer",    nome: "Joaquim",  cargo: "Designer & Arte Finalista",     dept: "Criação" }
};

let estadoGeral = "idle"; // "idle" | "running" | "working" | "celebrating"
let intervaloEmojis = null;
let agentesNoCafe = ["copywriter", "designer", "pesquisador", "supervisor"]; // Quem começa no café

// Inicialização
document.addEventListener("DOMContentLoaded", () => {
  iniciarRelogio();
  posicionarPersonagensInicial();
  iniciarCicloEmojis();
  configurarEventosGerais();
});

// Relógio ao vivo
function iniciarRelogio() {
  const clockEl = document.getElementById("live-clock");
  function tick() {
    const agora = new Date();
    clockEl.textContent = agora.toLocaleTimeString("pt-BR", { hour12: false });
  }
  tick();
  setInterval(tick, 1000);
}

// Posicionamento inicial dos avatares no escritório
function posicionarPersonagensInicial() {
  Object.keys(DADOS_AGENTES).forEach(agenteId => {
    const atorEl = document.getElementById(`actor-${agenteId}`);
    if (!atorEl) return;

    // Se estiver na lista do café, vai pro café; senão vai pra mesa
    const coord = agentesNoCafe.includes(agenteId) ? COORD_CAFE[agenteId] : COORD_DESKS[agenteId];
    atorEl.style.left = `${coord.left}px`;
    atorEl.style.top = `${coord.top}px`;
    atorEl.className = "avatar-actor idle";

    // Mostra um emoji relax inicial
    const bubble = document.getElementById(`bubble-${agenteId}`);
    if (bubble) {
      bubble.textContent = agentesNoCafe.includes(agenteId) ? "☕" : "💻";
      bubble.style.opacity = "1";
    }
  });

  const statusLabel = document.getElementById("team-work-status");
  if (statusLabel) statusLabel.textContent = "☕ Relax no Kav Café";
}

// Ciclo de Emojis aleatórios flutuando dos avatares (SEM TEXTO)
function iniciarCicloEmojis() {
  if (intervaloEmojis) clearInterval(intervaloEmojis);

  intervaloEmojis = setInterval(() => {
    const listaAgentes = Object.keys(DADOS_AGENTES);
    // Sorteia 1 ou 2 agentes para expressar emoji
    const sorteados = [
      listaAgentes[Math.floor(Math.random() * listaAgentes.length)],
      listaAgentes[Math.floor(Math.random() * listaAgentes.length)]
    ];

    sorteados.forEach(agenteId => {
      const bubble = document.getElementById(`bubble-${agenteId}`);
      if (!bubble) return;

      let emojiEscolhido = "☕";
      if (estadoGeral === "working") {
        const pool = EMOJIS_TRABALHO[agenteId] || ["💻", "⚡"];
        emojiEscolhido = pool[Math.floor(Math.random() * pool.length)];
      } else if (estadoGeral === "celebrating") {
        emojiEscolhido = EMOJIS_FESTA[Math.floor(Math.random() * EMOJIS_FESTA.length)];
      } else {
        emojiEscolhido = EMOJIS_CAFE[Math.floor(Math.random() * EMOJIS_CAFE.length)];
      }

      // Efeito de pop-in no balão
      bubble.style.opacity = "0";
      bubble.style.transform = "translateX(-50%) scale(0.6)";
      setTimeout(() => {
        bubble.textContent = emojiEscolhido;
        bubble.style.opacity = "1";
        bubble.style.transform = "translateX(-50%) scale(1)";
      }, 150);
    });
  }, 2200);
}

// ---------------------------------------------------------------------------
// ANIMAÇÃO DE DISPARADA: CORRIDA PARA AS MESAS AO DAR O PLAY
// ---------------------------------------------------------------------------
function dispararCorridaParaMesas() {
  estadoGeral = "running";
  const statusLabel = document.getElementById("team-work-status");
  if (statusLabel) statusLabel.textContent = "🏃💨 Correndo pras mesas!";

  const ticker = document.getElementById("feed-ticker");
  if (ticker) ticker.textContent = "⚡ Play disparado! Agentes correndo imediatamente para suas estações de trabalho...";

  // 1. Cada agente que está fora da mesa corre para sua estação
  Object.keys(DADOS_AGENTES).forEach((agenteId, index) => {
    const atorEl = document.getElementById(`actor-${agenteId}`);
    const deskCoord = COORD_DESKS[agenteId];
    if (!atorEl || !deskCoord) return;

    // Adiciona classe de corrida (inclinação + poeira 💨)
    atorEl.classList.remove("idle", "working", "celebrating");
    atorEl.classList.add("running");

    // Emoji de pressa no balão
    const bubble = document.getElementById(`bubble-${agenteId}`);
    if (bubble) bubble.textContent = "⚡";

    // Pequeno delay orgânico entre cada um correndo (0 a 180ms)
    setTimeout(() => {
      atorEl.style.left = `${deskCoord.left}px`;
      atorEl.style.top = `${deskCoord.top}px`;
    }, index * 40);
  });

  // 2. Após chegarem às mesas (~850ms), começam a trabalhar intensamente
  setTimeout(() => {
    iniciarTrabalhoNasMesas();
  }, 950);
}

// Inicia trabalho nas mesas: digitação e monitores brilhando
function iniciarTrabalhoNasMesas() {
  estadoGeral = "working";

  const statusLabel = document.getElementById("team-work-status");
  if (statusLabel) statusLabel.textContent = "🔥 Em Produção Total!";

  const ticker = document.getElementById("feed-ticker");
  if (ticker) ticker.textContent = "💻 Esteira ativa: Curadoria de fotos, redação de copy, design visual e inspeção de arte em andamento...";

  // Acende telas e coloca avatares em digitação
  document.querySelectorAll(".computer-screen").forEach(screen => {
    screen.classList.add("screen-working");
  });

  Object.keys(DADOS_AGENTES).forEach(agenteId => {
    const atorEl = document.getElementById(`actor-${agenteId}`);
    if (!atorEl) return;
    atorEl.classList.remove("running", "idle", "celebrating");
    atorEl.classList.add("working");

    // Emojis de trabalho intenso
    const bubble = document.getElementById(`bubble-${agenteId}`);
    if (bubble) {
      const pool = EMOJIS_TRABALHO[agenteId];
      bubble.textContent = pool ? pool[0] : "💻";
    }
  });
}

// ---------------------------------------------------------------------------
// ANIMAÇÃO DE CONCLUSÃO: POST ENTREGUE E COMEMORAÇÃO
// ---------------------------------------------------------------------------
function celebrarEntrega(postFormatado) {
  estadoGeral = "celebrating";

  const statusLabel = document.getElementById("team-work-status");
  if (statusLabel) statusLabel.textContent = "🎉 Post Concluído!";

  const ticker = document.getElementById("feed-ticker");
  if (ticker) ticker.textContent = "🏆 Entrega finalizada com sucesso! Post pronto com foto real e aprovação estética.";

  // Desliga o brilho de esforço extremo das telas
  document.querySelectorAll(".computer-screen").forEach(screen => {
    screen.classList.remove("screen-working");
  });

  // Todos pulam de comemoração com emojis de festa
  Object.keys(DADOS_AGENTES).forEach(agenteId => {
    const atorEl = document.getElementById(`actor-${agenteId}`);
    if (!atorEl) return;
    atorEl.classList.remove("working", "running");
    atorEl.classList.add("celebrating");

    const bubble = document.getElementById(`bubble-${agenteId}`);
    if (bubble) {
      bubble.textContent = EMOJIS_FESTA[Math.floor(Math.random() * EMOJIS_FESTA.length)];
    }
  });

  // Abre o modal de entrega do post
  if (postFormatado) {
    exibirPostModal(postFormatado);
  }

  // Após 5 segundos de comemoração, relaxam e alguns voltam para o café
  setTimeout(() => {
    retornarAoModoRelax();
  }, 5000);
}

// Retorna ao modo relax após comemoração
function retornarAoModoRelax() {
  estadoGeral = "idle";
  const statusLabel = document.getElementById("team-work-status");
  if (statusLabel) statusLabel.textContent = "☕ Modo Relax no Café";

  // Sorteia quem vai para o café desta vez
  const todos = Object.keys(DADOS_AGENTES);
  agentesNoCafe = todos.sort(() => 0.5 - Math.random()).slice(0, 3);

  Object.keys(DADOS_AGENTES).forEach(agenteId => {
    const atorEl = document.getElementById(`actor-${agenteId}`);
    if (!atorEl) return;
    atorEl.classList.remove("celebrating", "working", "running");
    atorEl.classList.add("idle");

    const coord = agentesNoCafe.includes(agenteId) ? COORD_CAFE[agenteId] : COORD_DESKS[agenteId];
    atorEl.style.left = `${coord.left}px`;
    atorEl.style.top = `${coord.top}px`;

    const bubble = document.getElementById(`bubble-${agenteId}`);
    if (bubble) {
      bubble.textContent = agentesNoCafe.includes(agenteId) ? "☕" : "💻";
    }
  });
}

// ---------------------------------------------------------------------------
// CONFIGURAÇÃO DOS EVENTOS, BOTÕES E MODAIS
// ---------------------------------------------------------------------------
function configurarEventosGerais() {
  // Cliques nos atores para ver crachá
  document.querySelectorAll(".avatar-actor").forEach(actor => {
    actor.addEventListener("click", () => {
      const agentId = actor.getAttribute("data-agent");
      abrirModal(agentId);
    });
  });

  // Fechar modal
  document.getElementById("modal-close").addEventListener("click", fecharModal);
  document.getElementById("agent-modal").addEventListener("click", (e) => {
    if (e.target.id === "agent-modal") fecharModal();
  });

  // Botão de Refresh
  document.getElementById("btn-refresh").addEventListener("click", () => {
    posicionarPersonagensInicial();
  });

  // Botão de Simulação de Corrida (para ver na hora sem gastar API)
  document.getElementById("btn-demo").addEventListener("click", () => {
    const btn = document.getElementById("btn-demo");
    btn.disabled = true;
    btn.textContent = "⏳ Simulando...";

    dispararCorridaParaMesas();

    setTimeout(() => {
      const simulado = {
        prato: "Frango Grelhado com Legumes",
        headline: "Feito no Capricho pra Você",
        selo: "Qualidade Garantida",
        legenda: "Aquele prato farto e suculento com tempero de casa para comemorar o dia. 🍗\n\nNosso prato do dia vem preparado no capricho com ingredientes frescos e amor pela gastronomia brasileira.\n\nVem provar! Clique no link da Bio.\n\n#NNRestaurante #ComidaCaseira #FrangoGrelhado #ComidaBrasileira #AlmoçoPerfeito",
        imagem_b64: null,
        criadores: "Curadoria: Benedito · Texto: Clarice · Arte: Joaquim · Direção: Otávio"
      };
      celebrarEntrega(simulado);
      btn.disabled = false;
      btn.textContent = "⚡ Simular Corrida";
    }, 4500);
  });

  configurarBotaoPlayReal();
}

// Botão "▶️ Dar o Play" com chamada real ao backend
function configurarBotaoPlayReal() {
  const btnPlay = document.getElementById("btn-play");
  const btnVerPosts = document.getElementById("btn-ver-posts");
  const btnClosePost = document.getElementById("post-modal-close");
  const btnCopy = document.getElementById("post-modal-copy-btn");

  if (btnClosePost) {
    btnClosePost.addEventListener("click", () => {
      document.getElementById("post-delivery-modal").classList.remove("open");
    });
  }

  if (btnCopy) {
    btnCopy.addEventListener("click", () => {
      const copyText = document.getElementById("post-modal-copy").textContent;
      navigator.clipboard.writeText(copyText).then(() => {
        btnCopy.textContent = "✅ Copiado!";
        setTimeout(() => { btnCopy.textContent = "📋 Copiar Legenda"; }, 2000);
      });
    });
  }

  if (!btnPlay) return;

  btnPlay.addEventListener("click", async () => {
    const selectCliente = document.getElementById("select-cliente");
    const slug = selectCliente ? selectCliente.value : "nn-restaurante";

    btnPlay.disabled = true;
    btnPlay.textContent = "⏳ Agentes em Ação...";

    // 1. CORREM PARA AS MESAS IMEDIATAMENTE!
    dispararCorridaParaMesas();

    try {
      const res = await fetch("/api/executar", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          slug: slug,
          com_imagem: true,
          modo: document.getElementById("select-modo") ? document.getElementById("select-modo").value : "campanha"
        })
      });

      const data = await res.json();

      if (data.sucesso && data.post) {
        btnPlay.disabled = false;
        btnPlay.textContent = "▶️ Dar o Play";

        const p = data.post;
        const postFormatado = {
          prato: p.foto ? (p.foto.nome || "Prato do Dia") : (p.produto ? p.produto.nome : "Post Kav"),
          headline: p.copy ? p.copy.headline_imagem : "NOVO POST",
          selo: p.copy ? (p.copy.selo_produto || "Qualidade Garantida") : "Qualidade Garantida",
          legenda: p.copy ? p.copy.legenda : "",
          imagem_b64: p.imagem ? p.imagem.imagem_b64 : (p.slides && p.slides[0] ? p.slides[0].imagem_b64 : null),
          criadores: "Curadoria: Benedito · Texto: Clarice · Arte: Joaquim · Direção: Otávio"
        };

        // 2. PARADA DE TRABALHO E COMEMORAÇÃO!
        celebrarEntrega(postFormatado);
      } else {
        throw new Error(data.erro || "Falha na esteira de produção");
      }
    } catch (err) {
      btnPlay.disabled = false;
      btnPlay.textContent = "▶️ Dar o Play";
      alert("Aviso: " + err.message);
      retornarAoModoRelax();
    }
  });
}

function abrirModal(agentId) {
  const info = DADOS_AGENTES[agentId];
  if (!info) return;

  document.getElementById("modal-name").textContent = info.nome;
  document.getElementById("modal-role").textContent = info.cargo;
  document.getElementById("modal-dept").textContent = info.dept;

  const dot = document.getElementById("modal-status-dot");
  dot.className = "badge-dot status-online";
  document.getElementById("modal-status-text").textContent = "Online no Escritório";

  document.getElementById("modal-current-task").textContent =
    estadoGeral === "working" ? "Executando tarefas da esteira de post no computador" : "Em momento de pausa e alinhamento no café";
  document.getElementById("modal-speech").textContent =
    estadoGeral === "working" ? "⚡ Foco total na entrega do post!" : "☕ Tomando um café e trocando ideias.";

  const historyList = document.getElementById("modal-history");
  historyList.innerHTML = `
    <li>Status atual: ${estadoGeral.toUpperCase()}</li>
    <li>Conexão: Agente autônomo conectado ao orquestrador</li>
    <li>Comunicação: Emojis visuais em tempo real</li>
  `;

  const iconPreview = document.getElementById("modal-avatar-icon");
  iconPreview.className = `modal-avatar-preview avatar-${info.nome.toLowerCase()}`;

  document.getElementById("agent-modal").classList.add("open");
}

function fecharModal() {
  document.getElementById("agent-modal").classList.remove("open");
}

function exibirPostModal(item) {
  const modal = document.getElementById("post-delivery-modal");
  if (!modal) return;

  document.getElementById("post-modal-headline").textContent = item.headline || item.prato || "NOVO POST";
  document.getElementById("post-modal-selo").textContent = item.selo || "Qualidade Garantida";
  document.getElementById("post-modal-copy").textContent = item.legenda || "";
  document.getElementById("post-modal-creators").textContent = item.criadores || "Equipe Kav Multi-Agente";

  const imgEl = document.getElementById("post-modal-img");
  const imgBox = document.getElementById("post-modal-img-placeholder");
  const dlLink = document.getElementById("post-modal-download-link");

  if (item.imagem_b64) {
    const dataUrl = "data:image/png;base64," + item.imagem_b64;
    imgEl.src = dataUrl;
    imgEl.style.display = "block";
    if (imgBox) imgBox.style.display = "none";
    dlLink.href = dataUrl;
    dlLink.download = `post-${(item.prato || "arte").toLowerCase().replace(/\s+/g, "-")}.png`;
    dlLink.style.display = "flex";
  } else {
    imgEl.style.display = "none";
    if (imgBox) {
      imgBox.style.display = "block";
      imgBox.textContent = "Arte gerada em modo simulação/texto.";
    }
    dlLink.style.display = "none";
  }

  modal.classList.add("open");
}
