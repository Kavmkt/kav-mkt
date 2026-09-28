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
    cargo: "Designer Júnior",
    departamento: "Criação",
    status: "trabalhando",
    fala: "Compondo headline sobre a foto real do buffet. Formato 1080x1440 pronto.",
    atividade: "Diagramando arte gráfica sobre a foto real (sem alterar a comida)",
    historico: [
      "Tratamento gráfico aplicado sobre foto real do buffet executivo.",
      "Cores da marca utilizadas: Cinza #2A2A2E + Vermelho #A31D1D.",
      "Submetendo layout para revisão do Diretor de Arte."
    ]
  },
  diretor: {
    id: "diretor",
    nome: "Otávio",
    cargo: "Diretor de Arte Sênior & Head Visual",
    departamento: "Criação",
    status: "online",
    fala: "Supervisionando estética, tipografia refinada e integridade do logo oficial.",
    atividade: "Inspecionando e refinando peças do Joaquim com visão computacional",
    historico: [
      "Critérios ativos: logo oficial N&N obrigatório, sem contorno branco (glow) e sem elipses toscas.",
      "Inspeção multimodal automática em cada post gerado.",
      "Aprovação e refino com alta fidelidade gpt-image-2.5-sunburst."
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

let estadoAgentes = { ...AGENTES_INICIAIS };
let producaoPosts = [];

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

// Carregar estado (do endpoint da API /api/estado ou fallback no JSON estático)
async function carregarEstado() {
  try {
    const res = await fetch("/api/estado?t=" + Date.now());
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
    console.log("Não foi possível sincronizar estado com a API /api/estado");
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
    `Otávio (Diretor de Arte): "${estadoAgentes.diretor ? estadoAgentes.diretor.fala : 'Avaliando layouts'}"`,
    `Benedito (Curador): "${estadoAgentes.pesquisador.fala}"`
  ];
  ticker.textContent = frases.join("  ✦  ");
}

// Renderiza a lista de posts na gaveta lateral
function renderizarPosts() {
  const container = document.getElementById("posts-list-container");
  if (!container) return;

  container.innerHTML = "";
  if (producaoPosts.length === 0) {
    container.innerHTML = `<div style="padding: 24px; text-align: center; color: #94a3b8;">Nenhum post registrado ainda no histórico. Clique em "▶️ Dar o Play" para gerar sua primeira peça.</div>`;
    return;
  }

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
        <span class="post-date-text">${p.data || "Recente"}</span>
      </div>

      <div class="post-card-grid">
        <div class="post-layout-col">
          <div class="col-section-header">
            <span class="col-section-title">🎨 Layout da Arte</span>
            <span class="col-section-tag">Diagramação Joaquim</span>
          </div>

          <div class="post-art-canvas" onclick="abrirModalArte(${idx})" title="Clique para ver o layout em tela cheia">
            <div class="art-photo-bg" style="background-image: url('${imgUrl}');">
              ${!imgUrl ? `<div class="art-fallback-icon">🍲</div>` : ''}
            </div>
            <div class="art-hover-overlay">
              <span>🔍 Ver Arte em Tela Cheia</span>
            </div>
          </div>

          <div class="art-actions-row">
            <button class="btn-art-action" onclick="abrirModalArte(${idx})">
              🔍 Expandir Arte
            </button>
            <button class="btn-art-action btn-art-download" onclick="baixarArteComoImagem(${idx})">
              ⬇️ Baixar Imagem
            </button>
          </div>
        </div>

        <div class="post-caption-col">
          <div class="col-section-header">
            <span class="col-section-title">✍️ Legenda Oficial</span>
            <span class="col-section-tag ready">Texto de Clarice</span>
          </div>

          <div class="post-item-title-box">
            <div class="post-item-name">${p.prato || p.headline}</div>
            <div class="post-creators-tag">${p.criadores || "Criado pela equipe Kav"}</div>
          </div>

          <div class="post-caption-box" id="caption-box-${idx}">${(p.legenda || "").replace(/\n/g, '<br>')}</div>

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
            <div class="insta-loc-sub">Santana de Parnaíba · Vila Poupança</div>
          </div>
        </div>
        <div class="insta-options-btn">•••</div>
      </div>

      <div class="insta-creative-canvas" style="display:flex; justify-content:center; align-items:center; background:#000;">
        ${imgUrl ? `<img src="${imgUrl}" style="max-width:100%; max-height:550px; object-fit:contain; border-radius:4px;" />` : `<div style="padding:40px; color:#fff;">🍲 Imagem não renderizada</div>`}
      </div>

      <div class="insta-engagement-bar">
        <div class="insta-icons-group">
          <span class="insta-action-btn red">❤️</span>
          <span class="insta-action-btn">💬</span>
          <span class="insta-action-btn">🚀</span>
        </div>
        <span class="insta-action-btn">🔖</span>
      </div>

      <div class="insta-text-section">
        <div class="insta-full-caption">
          <strong>nnrestaurante_</strong> ${(post.legenda || "").replace(/\n/g, '<br>')}
        </div>
      </div>

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

// Baixar arte gerada
window.baixarArteComoImagem = function(idx) {
  const post = producaoPosts[idx];
  if (!post) return;

  if (post.imagem_b64) {
    const link = document.createElement("a");
    link.download = `post_${post.id || "nn_restaurante"}.png`;
    link.href = `data:image/png;base64,${post.imagem_b64}`;
    link.click();
  } else if (post.imagem_url) {
    window.open(post.imagem_url, "_blank");
  } else {
    alert("Nenhuma imagem gerada disponível para download.");
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

function animarPulo(agentId) {
  const target = agentId ? document.querySelector(`.station-${agentId} .pixel-character`) : document.querySelectorAll(".pixel-character");
  if (!target) return;
  if (target.forEach) {
    target.forEach(el => {
      el.classList.add("jump");
      setTimeout(() => el.classList.remove("jump"), 600);
    });
  } else {
    target.classList.add("jump");
    setTimeout(() => target.classList.remove("jump"), 600);
  }
}

// Configura eventos da tela
function configurarEventos() {
  // Cliques nas estações para ver crachá
  document.querySelectorAll(".workstation").forEach(station => {
    station.addEventListener("click", () => {
      const agentId = station.getAttribute("data-agent");
      abrirModal(agentId);
    });
  });

  const modalClose = document.getElementById("modal-close");
  if (modalClose) modalClose.addEventListener("click", fecharModal);

  const agentModal = document.getElementById("agent-modal");
  if (agentModal) {
    agentModal.addEventListener("click", (e) => {
      if (e.target.id === "agent-modal") fecharModal();
    });
  }

  // Gaveta de posts
  const btnVerPosts = document.getElementById("btn-ver-posts");
  const drawerOverlay = document.getElementById("posts-drawer-overlay");
  const btnCloseDrawer = document.getElementById("btn-close-drawer");

  if (btnVerPosts && drawerOverlay) {
    btnVerPosts.addEventListener("click", () => {
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

  // Refresh
  const btnRefresh = document.getElementById("btn-refresh");
  if (btnRefresh) {
    btnRefresh.addEventListener("click", () => {
      carregarEstado();
      animarPulo();
    });
  }

  // Botão de Play
  const btnPlay = document.getElementById("btn-play");
  if (btnPlay) {
    btnPlay.addEventListener("click", dispararProducaoReal);
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
  if (statusText) statusText.textContent = agente.status.toUpperCase();

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

  const modal = document.getElementById("agent-modal");
  if (modal) modal.classList.add("open");
}

function fecharModal() {
  const modal = document.getElementById("agent-modal");
  if (modal) modal.classList.remove("open");
}

// Execução real via backend server.py
async function dispararProducaoReal() {
  const btnPlay = document.getElementById("btn-play");
  const selectCli = document.getElementById("select-cliente");
  const slug = selectCli ? selectCli.value : "nn-restaurante";

  if (btnPlay) {
    btnPlay.disabled = true;
    btnPlay.textContent = "⏳ Agentes em Ação...";

    let step = 0;
    const animInterval = setInterval(() => {
      const agentes = ["pesquisador", "copywriter", "designer", "diretor", "supervisor"];
      const agId = agentes[step % agentes.length];
      animarPulo(agId);
      step++;
    }, 1500);

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
      
      clearInterval(animInterval);
      const data = await res.json();

      if (data.sucesso && data.post) {
        btnPlay.disabled = false;
        btnPlay.textContent = "▶️ Dar o Play";
        
        carregarEstado();

        const p = data.post;
        const postFormatado = {
          prato: p.foto ? (p.foto.nome || "Prato do Dia") : (p.produto ? p.produto.nome : (p.pauta ? p.pauta.tema : "Post Kav")),
          headline: p.copy ? p.copy.headline_imagem : (p.roteiro ? (p.roteiro.paginas ? p.roteiro.paginas[0].titulo : "Post Pronto") : "NOVO POST"),
          selo: p.copy ? (p.copy.selo_produto || "Destaque") : (p.slides ? `${p.slides.length} Páginas` : "Pronto"),
          legenda: p.copy ? p.copy.legenda : (p.roteiro ? p.roteiro.legenda : ""),
          imagem_b64: p.imagem ? p.imagem.imagem_b64 : (p.slides && p.slides[0] ? p.slides[0].imagem_b64 : null),
          criadores: "Curadoria: Benedito · Texto: Clarice · Arte: Joaquim · Direção de Arte: Otávio"
        };

        exibirPostModal(postFormatado);
      } else {
        throw new Error(data.erro || "Falha na esteira de produção");
      }
    } catch (err) {
      clearInterval(animInterval);
      btnPlay.disabled = false;
      btnPlay.textContent = "▶️ Dar o Play";
      alert("Aviso: " + err.message);
    }
  }
}

function exibirPostModal(item) {
  const modal = document.getElementById("post-delivery-modal");
  if (!modal) return;

  document.getElementById("post-modal-headline").textContent = item.headline || item.prato || "NOVO POST";
  document.getElementById("post-modal-selo").textContent = item.selo || "Destaque";
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
      imgBox.textContent = "Arte sem imagem gerada (modo texto).";
    }
    dlLink.style.display = "none";
  }

  modal.classList.add("open");
}
