// Kav — Escritório Virtual de Agentes de IA
// Controla o estado em tempo real, interatividade dos avatares, gaveta de posts e layout das artes

const AGENTES_INICIAIS = {
  supervisor: {
    id: "supervisor",
    nome: "Augusto",
    cargo: "Head de Inteligência & Estratégia",
    departamento: "Diretoria",
    status: "alerta",
    fala: "53 conversas no WhatsApp nos últimos 30 dias. Feed precisa de novos posts urgentes!",
    atividade: "Supervisionando alinhamento de tráfego pago vs. presença orgânica",
    historico: [
      "Alerta emitido: Meta Ads ativo com R$ 260,79 gastos e zero posts no feed há 6 meses.",
      "Análise de concorrência e raio de 3km concluída.",
      "Recomendação enviada: postar 3x/semana pratos executivos do buffet."
    ]
  },
  metricas: {
    id: "metricas",
    nome: "Vicente",
    cargo: "Analista de Tráfego & Performance",
    departamento: "Performance",
    status: "trabalhando",
    fala: "Meta Ads coletado: 594 cliques, CTR 2,1%, 53 conversas no WhatsApp iniciadas.",
    atividade: "Conectado à Graph API do Meta (Conta: CA - N&N Alimentos)",
    historico: [
      "Coleta Meta Marketing API: R$ 260,79 gastos em 30 dias.",
      "Instagram @nnrestaurante_: 524 seguidores, 33 posts cadastrados.",
      "Aguardando credenciais do Google Ads para unificar dashboard."
    ]
  },
  copywriter: {
    id: "copywriter",
    nome: "Clarice",
    cargo: "Redatora de Conteúdo & Copywriter",
    departamento: "Criação",
    status: "online",
    fala: "Padrão de legenda 'Sabor de Casa' carregado. Ganchos de almoço prontos!",
    atividade: "Escrevendo headlines e selos de pratos para o feed",
    historico: [
      "Copy gerada: Headline 'Feijoada Completa', gancho de almoço de sexta.",
      "Legenda formatada com emojis e hashtags locais de Santana de Parnaíba.",
      "Diretrizes de marca do NN Restaurante aplicadas."
    ]
  },
  designer: {
    id: "designer",
    nome: "Joaquim",
    cargo: "Diretor de Arte & Designer",
    departamento: "Criação",
    status: "trabalhando",
    fala: "Compondo headline e selo sobre a foto real do buffet. Formato 1080x1440 pronto.",
    atividade: "Diagramando arte gráfica sobre a foto real (sem alterar a comida)",
    historico: [
      "Tratamento gráfico aplicado sobre foto real do buffet executivo.",
      "Cores da marca utilizadas: Cinza #2A2A2E + Dourado #EEB730 + Vermelho #A31D1D.",
      "Margem de segurança de corte vertical respeitada."
    ]
  },
  pesquisador: {
    id: "pesquisador",
    nome: "Benedito",
    cargo: "Curador de Acervo & Catálogo",
    departamento: "Planejamento",
    status: "online",
    fala: "33 fotos no acervo. Próximo prato sorteado sem repetição em 45 dias.",
    atividade: "Gerenciando fotos reais de pratos e buffet em clientes/nn-restaurante/fotos/",
    historico: [
      "Foto selecionada: 'buffet_saladas_02.jpg' (não usada há 50 dias).",
      "Sincronização de catálogo e acervo de imagens validada.",
      "Controle de repetição registrado no histórico do GitHub."
    ]
  }
};

const POSTS_PADRAO = [
  {
    id: "post-01",
    data: "Hoje · Almoço de Sexta",
    prato: "Feijoada Completa Tradicional",
    categoria: "Almoço Executivo",
    headline: "SABOR DE CASA",
    selo: "Feijoada Completa",
    imagem_url: "https://images.unsplash.com/photo-1555939594-58d7cb561ad1?w=900&auto=format&fit=crop&q=80",
    legenda: `Sexta-feira combina com feijoada no capricho! 🍲

Aqui no N&N Restaurante a nossa feijoada é preparada com carnes selecionadas, tempero caseiro de verdade e todos os acompanhamentos tradicionais: arroz soltinho, couve refogada, farofa crocante e torresmo sequinho.

Almoce com a gente ou peça no delivery (entregamos num raio de 3km com rapidez e tudo quentinho)!

📍 Alameda das Garças, 45 - Santana de Parnaíba
📲 Peça pelo WhatsApp no link da bio.

#comidacaseira #feijoada #almocoexecutivo #santanadeparnaiba #deliverycomida`,
    criadores: "Curadoria: Benedito · Texto: Clarice · Arte: Joaquim"
  },
  {
    id: "post-02",
    data: "Ontem · Buffet Executivo",
    prato: "Buffet Executivo de Saladas & Carnes",
    categoria: "Self-Service",
    headline: "VARIEDADE & FARTURA",
    selo: "Buffet Executivo",
    imagem_url: "https://images.unsplash.com/photo-1540420773420-3366772f4999?w=900&auto=format&fit=crop&q=80",
    legenda: `Quem disse que comer bem fora de casa precisa ser difícil? 🥗🥩

Nosso buffet completo tem saladas frescas do dia, pratos quentes e carnes grelhadas preparadas na hora. Comida feita como na sua casa, com higiene impecável e fartura garantida.

Venha fazer sua pausa de almoço com a gente!

📍 N&N Restaurante - Santana de Parnaíba
⏰ Aberto de segunda a sábado das 11h às 15h.

#buffetexecutivo #almocosaudavel #restaurantecaseiro #comidadeverdade`,
    criadores: "Curadoria: Benedito · Texto: Clarice · Arte: Joaquim"
  },
  {
    id: "post-03",
    data: "Quarta · Prato do Dia",
    prato: "Filé à Parmegiana da Casa",
    categoria: "Prato Especial",
    headline: "TRADIÇÃO & CROCÂNCIA",
    selo: "Parmegiana Artesanal",
    imagem_url: "https://images.unsplash.com/photo-1529692236671-f1f6cf9683ba?w=900&auto=format&fit=crop&q=80",
    legenda: `Quarta-feira é dia da clássica Parmegiana da Casa! 🥩🧀

Filé empanado crocante, coberto com muito queijo derretido e molho de tomate fresco artesanal. Acompanha arroz soltinho e batata frita sequinha e dourada.

Almoce com a gente ou peça pelo WhatsApp (entregamos quentinho num raio de 3km)!

📍 Alameda das Garças, 45 - Santana de Parnaíba
📲 Peça pelo WhatsApp no link da bio.

#parmegiana #comidacaseira #almocoexecutivo #santanadeparnaiba #delivery`,
    criadores: "Curadoria: Benedito · Texto: Clarice · Arte: Joaquim"
  }
];

let estadoAgentes = { ...AGENTES_INICIAIS };
let producaoPosts = [ ...POSTS_PADRAO ];

// Inicialização
document.addEventListener("DOMContentLoaded", () => {
  iniciarRelogio();
  carregarEstado();
  configurarEventos();
});

// Relógio ao vivo
function iniciarRelogio() {
  const clockEl = document.getElementById("live-clock");
  if (!clockEl) return;
  function tick() {
    const agora = new Date();
    clockEl.textContent = agora.toLocaleTimeString("pt-BR", { hour12: false });
  }
  tick();
  setInterval(tick, 1000);
}

// Carregar estado (do arquivo JSON ou fallback inicial)
async function carregarEstado() {
  try {
    const res = await fetch("estado_agentes.json?t=" + Date.now());
    if (res.ok) {
      const dados = await res.json();
      if (dados.funcionarios) {
        Object.keys(dados.funcionarios).forEach(id => {
          const f = dados.funcionarios[id];
          if (estadoAgentes[id]) {
            estadoAgentes[id].status = f.status || estadoAgentes[id].status;
            estadoAgentes[id].fala = f.fala_atual || estadoAgentes[id].fala;
            estadoAgentes[id].atividade = f.atividade_atual || estadoAgentes[id].atividade;
            if (f.historico_atividades && f.historico_atividades.length > 0) {
              estadoAgentes[id].historico = f.historico_atividades.map(h => `${h.atividade} — "${h.fala}"`);
            }
          }
        });
      }
      if (dados.producao_recente && dados.producao_recente.length > 0) {
        producaoPosts = dados.producao_recente;
      }
    }
  } catch (e) {
    console.log("Usando dados integrados de demonstração.");
  }
  renderizarEscritorio();
  renderizarPosts();
}

// Renderiza balões e status nas estações
function renderizarEscritorio() {
  Object.keys(estadoAgentes).forEach(id => {
    const agente = estadoAgentes[id];
    const bubbleText = document.querySelector(`#bubble-${id} .bubble-text`);
    if (bubbleText) {
      bubbleText.textContent = agente.fala;
    }
    
    const badgeDot = document.querySelector(`.station-${id} .badge-dot`);
    if (badgeDot) {
      badgeDot.className = "badge-dot status-" + agente.status;
    }
  });

  atualizarFeedTicker();
}

// Atualiza o letreiro de atividades
function atualizarFeedTicker() {
  const ticker = document.getElementById("feed-ticker");
  if (!ticker) return;
  const frases = [
    `Augusto (Supervisor): "${estadoAgentes.supervisor.fala}"`,
    `Vicente (Métricas): "${estadoAgentes.metricas.fala}"`,
    `Clarice (Copywriter): "${estadoAgentes.copywriter.fala}"`,
    `Joaquim (Designer): "${estadoAgentes.designer.fala}"`,
    `Benedito (Curador): "${estadoAgentes.pesquisador.fala}"`
  ];
  ticker.textContent = frases.join("  ✦  ");
}

// Renderiza a lista de posts na gaveta lateral com o LAYOUT VISUAL DO POST + LEGENDA
function renderizarPosts() {
  const container = document.getElementById("posts-list-container");
  if (!container) return;

  container.innerHTML = "";
  producaoPosts.forEach((p, idx) => {
    const card = document.createElement("div");
    card.className = "post-delivery-card";
    const imgUrl = p.imagem_url || (p.imagem_b64 ? `data:image/png;base64,${p.imagem_b64}` : "");

    card.innerHTML = `
      <div class="post-card-meta">
        <div class="post-badge-group">
          <span class="post-badge">📱 Formato Feed 4:5 · 1080x1440</span>
          <span class="post-cat-pill">${p.categoria || "Almoço Executivo"}</span>
        </div>
        <span class="post-date-text">${p.data}</span>
      </div>

      <div class="post-card-grid">
        <!-- COLUNA 1: LAYOUT VISUAL DO POST (ARTE DO INSTAGRAM CRIADA POR JOAQUIM) -->
        <div class="post-layout-col">
          <div class="col-section-header">
            <span class="col-section-title">🎨 Layout da Arte</span>
            <span class="col-section-tag">Diagramação Joaquim</span>
          </div>

          <!-- MOLDURA DA ARTE DO POST (4:5) -->
          <div class="post-art-canvas" onclick="abrirModalArte(${idx})" title="Clique para ver o layout em tela cheia">
            <!-- Imagem Gastronômica Real -->
            <div class="art-photo-bg" style="background-image: url('${imgUrl}');">
              ${!imgUrl ? `<div class="art-fallback-icon">🍲</div>` : ''}
            </div>

            <!-- Vinhetas Cinematográficas -->
            <div class="art-vignette-top"></div>
            <div class="art-vignette-bottom"></div>

            <!-- Cabeçalho da Arte com Branding N&N -->
            <div class="art-header-layer">
              <div class="art-brand-badge">
                <span class="art-brand-icon">🍽️</span>
                <div>
                  <div class="art-brand-name">N&N RESTAURANTE</div>
                  <div class="art-brand-sub">Comida Caseira & Buffet</div>
                </div>
              </div>
              <span class="art-city-pill">SANTANA DE PARNAÍBA</span>
            </div>

            <!-- Rodapé da Arte: Selo, Headline e Rodapé -->
            <div class="art-footer-layer">
              <div class="art-seal-ribbon">
                <span class="star">✦</span>
                <span class="seal-text">${p.selo}</span>
                <span class="star">✦</span>
              </div>
              <h3 class="art-headline">${p.headline}</h3>
              <div class="art-footer-info">
                <span>📍 Alameda das Garças, 45</span>
                <span>📲 Delivery no WhatsApp (Raio 3km)</span>
              </div>
            </div>

            <!-- Efeito de Hover -->
            <div class="art-hover-overlay">
              <span>🔍 Ver Arte em Tela Cheia</span>
            </div>
          </div>

          <!-- Ações da Arte -->
          <div class="art-actions-row">
            <button class="btn-art-action" onclick="abrirModalArte(${idx})">
              🔍 Expandir Arte
            </button>
            <button class="btn-art-action btn-art-download" onclick="baixarArteComoImagem(${idx})">
              ⬇️ Baixar Imagem
            </button>
          </div>
        </div>

        <!-- COLUNA 2: LEGENDA & COPIA -->
        <div class="post-caption-col">
          <div class="col-section-header">
            <span class="col-section-title">✍️ Legenda Oficial</span>
            <span class="col-section-tag ready">Texto de Clarice</span>
          </div>

          <div class="post-item-title-box">
            <div class="post-item-name">${p.prato}</div>
            <div class="post-creators-tag">${p.criadores || "Criado pela equipe Kav"}</div>
          </div>

          <div class="post-caption-box" id="caption-box-${idx}">${p.legenda}</div>

          <div class="post-caption-footer">
            <button class="btn-copy" onclick="copiarLegenda(${idx}, this)">
              📋 Copiar Legenda
            </button>
          </div>
        </div>
      </div>
    `;
    container.appendChild(card);
  });
}

// Modal de Zoom da Arte & Mockup Instagram Feed
window.abrirModalArte = function(idx) {
  const post = producaoPosts[idx];
  if (!post) return;

  const modal = document.getElementById("art-zoom-modal");
  const container = document.getElementById("instagram-post-preview-container");
  if (!modal || !container) return;

  const imgUrl = post.imagem_url || (post.imagem_b64 ? `data:image/png;base64,${post.imagem_b64}` : "");

  container.innerHTML = `
    <div class="insta-mockup-frame">
      <!-- Topo Instagram -->
      <div class="insta-top-bar">
        <div class="insta-user-box">
          <div class="insta-avatar-ring">
            <div class="insta-avatar-inner">🍽️</div>
          </div>
          <div class="insta-meta">
            <div class="insta-name-row">
              <strong>nnrestaurante_</strong>
              <span class="insta-badge-check">✓</span>
              <span class="insta-dot-sep">•</span>
              <span class="insta-follow-btn">Seguindo</span>
            </div>
            <div class="insta-loc-sub">Santana de Parnaíba · Alameda das Garças, 45</div>
          </div>
        </div>
        <div class="insta-options-btn">•••</div>
      </div>

      <!-- A Arte do Post Expandida -->
      <div class="insta-creative-canvas">
        <div class="art-photo-bg" style="background-image: url('${imgUrl}');">
          ${!imgUrl ? `<div class="art-fallback-icon">🍲</div>` : ''}
        </div>
        <div class="art-vignette-top"></div>
        <div class="art-vignette-bottom"></div>

        <div class="art-header-layer">
          <div class="art-brand-badge">
            <span class="art-brand-icon">🍽️</span>
            <div>
              <div class="art-brand-name">N&N RESTAURANTE</div>
              <div class="art-brand-sub">Comida Caseira & Buffet</div>
            </div>
          </div>
          <span class="art-city-pill">SANTANA DE PARNAÍBA</span>
        </div>

        <div class="art-footer-layer">
          <div class="art-seal-ribbon">
            <span class="star">✦</span>
            <span class="seal-text">${post.selo}</span>
            <span class="star">✦</span>
          </div>
          <h3 class="art-headline">${post.headline}</h3>
          <div class="art-footer-info">
            <span>📍 Santana de Parnaíba</span>
            <span>📲 WhatsApp na Bio (Raio 3km)</span>
          </div>
        </div>
      </div>

      <!-- Barra de Ações Instagram -->
      <div class="insta-engagement-bar">
        <div class="insta-icons-group">
          <span class="insta-action-btn red">❤️</span>
          <span class="insta-action-btn">💬</span>
          <span class="insta-action-btn">🚀</span>
        </div>
        <span class="insta-action-btn">🔖</span>
      </div>

      <!-- Curtidas e Legenda -->
      <div class="insta-text-section">
        <div class="insta-likes-count">Curtido por <strong>kav.mkt</strong> e <strong>outras 184 pessoas</strong></div>
        <div class="insta-full-caption">
          <strong>nnrestaurante_</strong> ${post.legenda.replace(/\n/g, '<br>')}
        </div>
      </div>

      <!-- Rodapé do Modal com Botões -->
      <div class="insta-modal-actions">
        <button class="btn btn-secondary" onclick="baixarArteComoImagem(${idx})">
          💾 Baixar Arte (.png)
        </button>
        <button class="btn btn-primary" onclick="copiarLegenda(${idx}, this)">
          📋 Copiar Legenda
        </button>
      </div>
    </div>
  `;

  modal.classList.add("open");
};

window.fecharModalArte = function() {
  const modal = document.getElementById("art-zoom-modal");
  if (modal) modal.classList.remove("open");
};

// Baixar arte gerada via Canvas 1080x1440
window.baixarArteComoImagem = function(idx) {
  const post = producaoPosts[idx];
  if (!post) return;

  const canvas = document.createElement("canvas");
  canvas.width = 1080;
  canvas.height = 1440;
  const ctx = canvas.getContext("2d");

  // Fundo gradiente
  const gradBg = ctx.createLinearGradient(0, 0, 0, 1440);
  gradBg.addColorStop(0, "#00182c");
  gradBg.addColorStop(0.5, "#0b2640");
  gradBg.addColorStop(1, "#000c17");
  ctx.fillStyle = gradBg;
  ctx.fillRect(0, 0, 1080, 1440);

  const img = new Image();
  img.crossOrigin = "anonymous";
  img.onload = function() {
    ctx.drawImage(img, 0, 100, 1080, 1000);
    concluirDesenho();
  };
  img.onerror = function() {
    concluirDesenho();
  };

  function concluirDesenho() {
    // Vinheta superior
    const vTop = ctx.createLinearGradient(0, 0, 0, 360);
    vTop.addColorStop(0, "rgba(0,18,32,0.96)");
    vTop.addColorStop(1, "rgba(0,18,32,0)");
    ctx.fillStyle = vTop;
    ctx.fillRect(0, 0, 1080, 360);

    // Vinheta inferior
    const vBottom = ctx.createLinearGradient(0, 650, 0, 1440);
    vBottom.addColorStop(0, "rgba(0,18,32,0)");
    vBottom.addColorStop(0.35, "rgba(0,18,32,0.85)");
    vBottom.addColorStop(1, "rgba(0,18,32,0.98)");
    ctx.fillStyle = vBottom;
    ctx.fillRect(0, 650, 1080, 790);

    // Header Marca
    ctx.fillStyle = "#EEB730";
    ctx.font = "bold 40px 'Plus Jakarta Sans', sans-serif";
    ctx.fillText("N&N RESTAURANTE", 60, 110);

    ctx.fillStyle = "#CBD5E1";
    ctx.font = "24px 'Plus Jakarta Sans', sans-serif";
    ctx.fillText("COMIDA CASEIRA · SANTANA DE PARNAÍBA", 60, 150);

    // Tag Cidade
    ctx.fillStyle = "rgba(0, 0, 0, 0.6)";
    ctx.fillRect(720, 65, 300, 60);
    ctx.fillStyle = "#EEB730";
    ctx.font = "bold 20px 'JetBrains Mono', monospace";
    ctx.textAlign = "center";
    ctx.fillText("ALMOÇO EXECUTIVO", 870, 102);
    ctx.textAlign = "left";

    // Selo Ribbon
    ctx.fillStyle = "#EEB730";
    ctx.fillRect(60, 1030, 520, 60);
    ctx.fillStyle = "#001D32";
    ctx.font = "800 28px 'Plus Jakarta Sans', sans-serif";
    ctx.fillText("✦ " + post.selo.toUpperCase() + " ✦", 80, 1072);

    // Headline
    ctx.fillStyle = "#FFFFFF";
    ctx.font = "800 68px 'Plus Jakarta Sans', sans-serif";
    ctx.fillText(post.headline.toUpperCase(), 60, 1180);

    // Linha divisória
    ctx.strokeStyle = "rgba(238, 183, 48, 0.5)";
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.moveTo(60, 1230);
    ctx.lineTo(1020, 1230);
    ctx.stroke();

    // Rodapé info
    ctx.fillStyle = "#E2E8F0";
    ctx.font = "26px 'Plus Jakarta Sans', sans-serif";
    ctx.fillText("📍 Alameda das Garças, 45 · Santana de Parnaíba", 60, 1290);
    ctx.fillText("📲 Pedidos no WhatsApp · Entregamos num raio de 3km", 60, 1340);

    // Trigger download
    const link = document.createElement("a");
    link.download = `post_${post.id}_nn_restaurante.png`;
    link.href = canvas.toDataURL("image/png");
    link.click();
  }

  if (post.imagem_url) {
    img.src = post.imagem_url;
  } else {
    concluirDesenho();
  }
};

// Copiar legenda com feedback visual
window.copiarLegenda = function(index, btnElement) {
  const post = producaoPosts[index];
  if (!post) return;

  navigator.clipboard.writeText(post.legenda).then(() => {
    const originalText = btnElement.innerHTML;
    btnElement.className = "btn-copy copied";
    btnElement.innerHTML = "✅ Copiado!";
    setTimeout(() => {
      btnElement.className = "btn-copy";
      btnElement.innerHTML = originalText;
    }, 2000);
  });
};

// Configura cliques, drawer e modal
function configurarEventos() {
  // Cliques nas estações
  document.querySelectorAll(".workstation").forEach(station => {
    station.addEventListener("click", () => {
      const agentId = station.getAttribute("data-agent");
      abrirModal(agentId);
    });
  });

  // Fechar modal de agentes
  const modalClose = document.getElementById("modal-close");
  if (modalClose) modalClose.addEventListener("click", fecharModal);
  
  const agentModal = document.getElementById("agent-modal");
  if (agentModal) {
    agentModal.addEventListener("click", (e) => {
      if (e.target.id === "agent-modal") fecharModal();
    });
  }

  // Gaveta de Posts & Legendas
  const btnPosts = document.getElementById("btn-posts");
  const drawerOverlay = document.getElementById("posts-drawer-overlay");
  const btnCloseDrawer = document.getElementById("btn-close-drawer");

  if (btnPosts && drawerOverlay) {
    btnPosts.addEventListener("click", () => {
      renderizarPosts();
      drawerOverlay.classList.add("open");
    });
  }

  if (btnCloseDrawer && drawerOverlay) {
    btnCloseDrawer.addEventListener("click", () => {
      drawerOverlay.classList.remove("open");
    });
  }

  if (drawerOverlay) {
    drawerOverlay.addEventListener("click", (e) => {
      if (e.target.id === "posts-drawer-overlay") {
        drawerOverlay.classList.remove("open");
      }
    });
  }

  // Fechar modal de arte
  const artModalClose = document.getElementById("art-modal-close");
  const artZoomModal = document.getElementById("art-zoom-modal");

  if (artModalClose) artModalClose.addEventListener("click", fecharModalArte);
  if (artZoomModal) {
    artZoomModal.addEventListener("click", (e) => {
      if (e.target.id === "art-zoom-modal") fecharModalArte();
    });
  }

  // Botão de Refresh
  const btnRefresh = document.getElementById("btn-refresh");
  if (btnRefresh) {
    btnRefresh.addEventListener("click", () => {
      carregarEstado();
      animarPulo();
    });
  }

  // Botão de Simulação / Demonstração ao vivo
  const btnDemo = document.getElementById("btn-demo");
  if (btnDemo) {
    btnDemo.addEventListener("click", rodarDemonstracao);
  }
}

function abrirModal(agentId) {
  const agente = estadoAgentes[agentId];
  if (!agente) return;

  document.getElementById("modal-name").textContent = agente.nome;
  document.getElementById("modal-role").textContent = agente.cargo;
  document.getElementById("modal-dept").textContent = agente.departamento;

  const dot = document.getElementById("modal-status-dot");
  if (dot) dot.className = "badge-dot status-" + agente.status;
  
  const statusText = document.getElementById("modal-status-text");
  if (statusText) statusText.textContent = formatarStatus(agente.status);

  const taskDesc = document.getElementById("modal-current-task");
  if (taskDesc) taskDesc.textContent = agente.atividade;
  
  const speech = document.getElementById("modal-speech");
  if (speech) speech.textContent = `"${agente.fala}"`;

  const historyList = document.getElementById("modal-history");
  if (historyList) {
    historyList.innerHTML = "";
    (agente.historico || []).forEach(item => {
      const li = document.createElement("li");
      li.textContent = item;
      historyList.appendChild(li);
    });
  }

  const iconPreview = document.getElementById("modal-avatar-icon");
  if (iconPreview) {
    iconPreview.className = "modal-avatar-preview avatar-" + agente.nome.toLowerCase();
  }

  const modal = document.getElementById("agent-modal");
  if (modal) modal.classList.add("open");
}

function fecharModal() {
  const modal = document.getElementById("agent-modal");
  if (modal) modal.classList.remove("open");
}

function formatarStatus(status) {
  const mapa = {
    online: "Online / Pronto",
    trabalhando: "Em Execução (Ativo)",
    alerta: "Atenção / Alerta Estratégico",
    ocioso: "Ocioso"
  };
  return mapa[status] || "Online";
}

function animarPulo() {
  document.querySelectorAll(".avatar-sprite").forEach(avatar => {
    avatar.style.transform = "scale(1.2)";
    setTimeout(() => { avatar.style.transform = ""; }, 300);
  });
}

// Simulação de ciclo de trabalho em cadeia
function rodarDemonstracao() {
  const btn = document.getElementById("btn-demo");
  if (!btn) return;
  btn.disabled = true;
  btn.textContent = "⏳ Ciclo em Andamento...";

  const passos = [
    {
      agente: "pesquisador",
      status: "trabalhando",
      fala: "Varrendo acervo... Prato selecionado por Benedito: 'Virado à Paulista'!",
      atividade: "Sorteando foto real do NN Restaurante sem repetição nos últimos 45 dias"
    },
    {
      agente: "copywriter",
      status: "trabalhando",
      fala: "Clarice criando headline e legenda clássica no padrão do cliente...",
      atividade: "Escrevendo copy: 'Tradição no almoço de terça' + chamada de entrega no raio de 3km"
    },
    {
      agente: "designer",
      status: "trabalhando",
      fala: "Joaquim aplicando headline, selo e logo sobre a foto real em 1080x1440...",
      atividade: "Renderizando arte visual final mantendo a foto do prato intacta"
    },
    {
      agente: "metricas",
      status: "trabalhando",
      fala: "Vicente puxando Meta Ads: 53 conversas no WhatsApp iniciadas nos últimos 30 dias!",
      atividade: "Monitorando custo por conversa e cliques nas campanhas do Meta"
    },
    {
      agente: "supervisor",
      status: "alerta",
      fala: "Augusto gerou diagnóstico: Tráfego pago excelente, mas precisamos postar este Virado hoje no feed!",
      atividade: "Supervisionando alinhamento: WhatsApp ativo vs. feed parado"
    }
  ];

  let i = 0;
  function proximoPasso() {
    if (i < passos.length) {
      const p = passos[i];
      estadoAgentes[p.agente].status = p.status;
      estadoAgentes[p.agente].fala = p.fala;
      estadoAgentes[p.agente].atividade = p.atividade;
      
      document.querySelectorAll(".workstation").forEach(w => w.style.filter = "grayscale(0.4) opacity(0.7)");
      const ativa = document.querySelector(`.station-${p.agente}`);
      if (ativa) {
        ativa.style.filter = "none";
        ativa.style.transform = "scale(1.08)";
        setTimeout(() => { ativa.style.transform = ""; }, 500);
      }

      renderizarEscritorio();
      i++;
      setTimeout(proximoPasso, 2200);
    } else {
      document.querySelectorAll(".workstation").forEach(w => w.style.filter = "none");
      btn.disabled = false;
      btn.textContent = "⚡ Simular Ciclo";
    }
  }

  proximoPasso();
}
