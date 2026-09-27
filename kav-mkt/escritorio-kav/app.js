// Kav — Escritório Virtual de Agentes de IA
// Controla o estado em tempo real e a interatividade dos avatares

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
    fala: "Padrão de legenda 'Sabor de Casa' carregado. Ganchos de fome de almoço prontos!",
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

let estadoAgentes = { ...AGENTES_INICIAIS };

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
        // Converte formato do Python para o frontend
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
    }
  } catch (e) {
    console.log("Usando dados integrados de demonstração.");
  }
  renderizarEscritorio();
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
    `Sofia (Supervisor): "${estadoAgentes.supervisor.fala}"`,
    `Marcos (Métricas): "${estadoAgentes.metricas.fala}"`,
    `Beatriz (Copywriter): "${estadoAgentes.copywriter.fala}"`,
    `Lucas (Designer): "${estadoAgentes.designer.fala}"`,
    `Enzo (Curador): "${estadoAgentes.pesquisador.fala}"`
  ];
  ticker.textContent = frases.join("  ✦  ");
}

// Configura cliques e modal
function configurarEventos() {
  // Cliques nas estações
  document.querySelectorAll(".workstation").forEach(station => {
    station.addEventListener("click", () => {
      const agentId = station.getAttribute("data-agent");
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
      fala: "Varrendo repositório de fotos... Prato selecionado: 'Virado à Paulista'!",
      atividade: "Sorteando foto real do NN Restaurante sem repetição nos últimos 45 dias"
    },
    {
      agente: "copywriter",
      status: "trabalhando",
      fala: "Criando headline e legenda de água na boca no padrão do cliente...",
      atividade: "Escrevendo copy: 'Tradição no almoço de terça' + chamada de entrega no raio de 3km"
    },
    {
      agente: "designer",
      status: "trabalhando",
      fala: "Aplicando headline, selo e logo sobre a foto real em 1080x1440...",
      atividade: "Renderizando arte visual final mantendo a foto do prato intacta"
    },
    {
      agente: "metricas",
      status: "trabalhando",
      fala: "Puxando dados do Meta Ads... 53 conversas no WhatsApp iniciadas nos últimos 30 dias!",
      atividade: "Monitorando custo por conversa e cliques nas campanhas do Meta"
    },
    {
      agente: "supervisor",
      status: "alerta",
      fala: "Diagnóstico gerado: Tráfego pago excelente, mas precisamos postar este Virado hoje no feed!",
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
      
      // Destaque visual na estação ativa
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
      btn.textContent = "⚡ Simular Ciclo de Trabalho";
    }
  }

  proximoPasso();
}


// ---------------------------------------------------------------------------
// Disparo Real de Agentes (Botão Dar o Play) e Modal de Entrega
// ---------------------------------------------------------------------------

function configurarBotaoPlay() {
  const btnPlay = document.getElementById("btn-play");
  const btnVerPosts = document.getElementById("btn-ver-posts");
  const modalPost = document.getElementById("post-delivery-modal");
  const btnClosePost = document.getElementById("post-modal-close");
  const btnCopy = document.getElementById("post-modal-copy-btn");

  if (btnClosePost) {
    btnClosePost.addEventListener("click", () => {
      modalPost.classList.remove("open");
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

  if (btnVerPosts) {
    btnVerPosts.addEventListener("click", () => {
      const producao = estadoAgentes.producao_recente || [];
      if (producao.length === 0) {
        alert("Nenhum post foi gerado ainda nesta sessão. Clique em '▶️ Dar o Play' para produzir!");
        return;
      }
      exibirPostModal(producao[0]);
    });
  }

  if (!btnPlay) return;

  btnPlay.addEventListener("click", async () => {
    const selectCliente = document.getElementById("select-cliente");
    const selectModo = document.getElementById("select-modo");
    const slug = selectCliente ? selectCliente.value : "nn-restaurante";
    const modo = selectModo ? selectModo.value : "organico";
    const nomeCliente = selectCliente ? selectCliente.options[selectCliente.selectedIndex].text : slug;

    btnPlay.disabled = true;
    btnPlay.textContent = modo === "campanha" ? "⏳ Montando Campanha..." : "⏳ Agentes em Ação...";

    // Anima as estações em sequência demonstrando o trabalho
    let step = 0;
    const animInterval = setInterval(() => {
      const agentes = ["pesquisador", "copywriter", "designer", "supervisor"];
      const agId = agentes[step % agentes.length];
      animarPulo(agId);
      step++;
    }, 1500);

    try {
      const res = await fetch("/api/executar", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ slug: slug, com_imagem: true, modo: modo })
      });

      clearInterval(animInterval);
      const data = await res.json();

      if (data.sucesso && data.post) {
        btnPlay.disabled = false;
        btnPlay.textContent = "▶️ Dar o Play";

        // Atualiza estado do escritório
        carregarEstado();

        // Formata post para o modal
        const p = data.post;
        const ehCampanha = p.tipo_post === "campanha" && !!p.estrategia;
        const postFormatado = ehCampanha ? {
          tipo_post: "campanha",
          prato: p.foto ? (p.foto.nome || "Prato do Dia") : "Peça de Campanha",
          headline: p.estrategia.headline_impacto || "NOVO ANÚNCIO",
          selo: p.estrategia.selo_produto || "Peça de Campanha",
          legenda: p.estrategia.copy_anuncio || "",
          angulo_conversao: p.estrategia.angulo_conversao || "",
          imagem_b64: p.imagem ? p.imagem.imagem_b64 : null,
          criadores: "Estratégia: Augusto · Copy: Clarice · Arte: Joaquim"
        } : {
          tipo_post: "organico",
          prato: p.foto ? (p.foto.nome || "Prato do Dia") : (p.produto ? p.produto.nome : (p.pauta ? p.pauta.tema : "Post Kav")),
          headline: p.copy ? p.copy.headline_imagem : (p.roteiro ? (p.roteiro.paginas ? p.roteiro.paginas[0].titulo : "Post Pronto") : "NOVO POST"),
          selo: p.copy ? (p.copy.selo_produto || "Destaque") : (p.slides ? `${p.slides.length} Páginas` : "Pronto"),
          legenda: p.copy ? p.copy.legenda : (p.roteiro ? p.roteiro.legenda : ""),
          imagem_b64: p.imagem ? p.imagem.imagem_b64 : (p.slides && p.slides[0] ? p.slides[0].imagem_b64 : null),
          criadores: "Curadoria: Benedito · Texto: Clarice · Arte: Joaquim"
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
  });
}

function exibirPostModal(item) {
  const modal = document.getElementById("post-delivery-modal");
  if (!modal) return;

  const ehCampanha = item.tipo_post === "campanha";

  document.getElementById("post-modal-headline").textContent = item.headline || item.prato || "NOVO POST";
  document.getElementById("post-modal-selo").textContent = item.selo || "Destaque";
  document.getElementById("post-modal-copy").textContent = item.legenda || "";
  document.getElementById("post-modal-creators").textContent = item.criadores || "Equipe Kav Multi-Agente";

  const badgeCampanha = document.getElementById("post-modal-badge-campanha");
  const anguloSection = document.getElementById("post-modal-angulo-section");
  const headlineLabel = document.getElementById("post-modal-headline-label");
  const copyLabel = document.getElementById("post-modal-copy-label");

  if (badgeCampanha) badgeCampanha.style.display = ehCampanha ? "inline-block" : "none";
  if (anguloSection) anguloSection.style.display = ehCampanha && item.angulo_conversao ? "block" : "none";
  if (anguloSection) document.getElementById("post-modal-angulo").textContent = item.angulo_conversao || "-";
  if (headlineLabel) headlineLabel.textContent = ehCampanha ? "HEADLINE DE ALTO IMPACTO" : "CHAMADA (HEADLINE)";
  if (copyLabel) copyLabel.textContent = ehCampanha ? "COPY DO ANÚNCIO" : "LEGENDA DO POST";

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

// Inicializa o botão de play junto com os outros eventos
const setupOriginal = configurarEventos;
configurarEventos = function() {
  if (typeof setupOriginal === "function") setupOriginal();
  configurarBotaoPlay();
};
