// Kav — Escritório Virtual de Agentes de IA
// Controla o estado em tempo real, interatividade dos avatares e gaveta de posts

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
      "Cores da marca utilizadas: Cinza #2A2A2E + Vermelho #A31D1D.",
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
    data: "Hoje · Almoço",
    prato: "Feijoada Completa Tradicional",
    categoria: "Almoço Executivo",
    headline: "Sabor de Casa",
    selo: "Feijoada Completa",
    legenda: "Sexta-feira combina com feijoada no capricho! 🍲\n\nAqui no N&N Restaurante a nossa feijoada é preparada com carnes selecionadas, tempero caseiro de verdade e todos os acompanhamentos tradicionais: arroz soltinho, couve refogada, farofa crocante e torresmo sequinho.\n\nAlmoce com a gente ou peça no delivery (entregamos num raio de 3km com rapidez e tudo quentinho)!\n\n📍 Alameda das Garças, 45 - Santana de Parnaíba\n📲 Peça pelo WhatsApp no link da bio.\n\n#comidacaseira #feijoada #almocoexecutivo #santanadeparnaiba #deliverycomida",
    criadores: "Curadoria: Benedito · Texto: Clarice · Arte: Joaquim"
  },
  {
    id: "post-02",
    data: "Ontem · Buffet",
    prato: "Buffet Executivo de Saladas & Carnes",
    categoria: "Self-Service",
    headline: "Variedade e Fartura",
    selo: "Buffet Executivo",
    legenda: "Quem disse que comer bem fora de casa precisa ser difícil? 🥗🥩\n\nNosso buffet completo tem saladas frescas do dia, pratos quentes e carnes grelhadas preparadas na hora. Comida feita como na sua casa, com higiene impecável e fartura garantida.\n\nVenha fazer sua pausa de almoço com a gente!\n\n📍 N&N Restaurante - Santana de Parnaíba\n⏰ Aberto de segunda a sábado das 11h às 15h.\n\n#buffetexecutivo #almocosaudavel #restaurantecaseiro #comidadeverdade",
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
  const frases = [
    `Augusto (Supervisor): "${estadoAgentes.supervisor.fala}"`,
    `Vicente (Métricas): "${estadoAgentes.metricas.fala}"`,
    `Clarice (Copywriter): "${estadoAgentes.copywriter.fala}"`,
    `Joaquim (Designer): "${estadoAgentes.designer.fala}"`,
    `Benedito (Curador): "${estadoAgentes.pesquisador.fala}"`
  ];
  ticker.textContent = frases.join("  ✦  ");
}

// Renderiza a lista de posts na gaveta lateral
function renderizarPosts() {
  const container = document.getElementById("posts-list-container");
  if (!container) return;

  container.innerHTML = "";
  producaoPosts.forEach((p, idx) => {
    const card = document.createElement("div");
    card.className = "post-delivery-card";
    card.innerHTML = `
      <div class="post-card-meta">
        <span class="post-badge">Post Instagram · 1080x1440</span>
        <span>${p.data}</span>
      </div>
      <div class="post-card-headline">
        <strong>${p.headline}</strong> · <span style="color: #EEB730;">${p.selo}</span>
      </div>
      <div class="post-caption-box" id="caption-box-${idx}">${p.legenda}</div>
      <div class="post-card-footer">
        <span class="post-creators">${p.criadores || "Criado pela equipe Kav"}</span>
        <button class="btn-copy" onclick="copiarLegenda(${idx}, this)">
          📋 Copiar Legenda
        </button>
      </div>
    `;
    container.appendChild(card);
  });
}

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
  document.querySelectorAll(".workstation").forEach(station => {
    station.addEventListener("click", () => {
      const agentId = station.getAttribute("data-agent");
      abrirModal(agentId);
    });
  });

  document.getElementById("modal-close").addEventListener("click", fecharModal);
  document.getElementById("agent-modal").addEventListener("click", (e) => {
    if (e.target.id === "agent-modal") fecharModal();
  });

  // Gaveta de Posts & Legendas
  const btnPosts = document.getElementById("btn-posts");
  const drawerOverlay = document.getElementById("posts-drawer-overlay");
  const btnCloseDrawer = document.getElementById("btn-close-drawer");

  btnPosts.addEventListener("click", () => {
    renderizarPosts();
    drawerOverlay.classList.add("open");
  });

  btnCloseDrawer.addEventListener("click", () => {
    drawerOverlay.classList.remove("open");
  });

  drawerOverlay.addEventListener("click", (e) => {
    if (e.target.id === "posts-drawer-overlay") {
      drawerOverlay.classList.remove("open");
    }
  });

  // Botão de Refresh
  document.getElementById("btn-refresh").addEventListener("click", () => {
    carregarEstado();
    animarPulo();
  });

  // Botão de Simulação / Demonstração ao vivo
  document.getElementById("btn-demo").addEventListener("click", rodarDemonstracao);
}

function abrirModal(agentId) {
  const agente = estadoAgentes[agentId];
  if (!agente) return;

  document.getElementById("modal-name").textContent = agente.nome;
  document.getElementById("modal-role").textContent = agente.cargo;
  document.getElementById("modal-dept").textContent = agente.departamento;

  const dot = document.getElementById("modal-status-dot");
  dot.className = "badge-dot status-" + agente.status;
  document.getElementById("modal-status-text").textContent = formatarStatus(agente.status);

  document.getElementById("modal-current-task").textContent = agente.atividade;
  document.getElementById("modal-speech").textContent = `"${agente.fala}"`;

  const historyList = document.getElementById("modal-history");
  historyList.innerHTML = "";
  (agente.historico || []).forEach(item => {
    const li = document.createElement("li");
    li.textContent = item;
    historyList.appendChild(li);
  });

  const iconPreview = document.getElementById("modal-avatar-icon");
  iconPreview.className = "modal-avatar-preview avatar-" + agente.nome.toLowerCase();

  document.getElementById("agent-modal").classList.add("open");
}

function fecharModal() {
  document.getElementById("agent-modal").classList.remove("open");
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

// Simulação de ciclo de trabalho em cadeia para apresentação de vendas
function rodarDemonstracao() {
  const btn = document.getElementById("btn-demo");
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
