// Kav Hotel — Motor Isométrico 2.5D Estilo Habbo Hotel
// Renderização em Pixel Art no Canvas + Personagens Humanóides + Diálogos 100% Emojis

// Configurações da Projeção Isométrica (Habbo 2:1)
const TILE_W = 64;
const TILE_H = 32;
const ORIGIN_X = 590;
const ORIGIN_Y = 150;
const GRID_COLS = 14;
const GRID_ROWS = 12;

function toScreen(gx, gy, gz = 0) {
  return {
    x: ORIGIN_X + (gx - gy) * (TILE_W / 2),
    y: ORIGIN_Y + (gx + gy) * (TILE_H / 2) - gz * 16
  };
}

// Definição dos 6 Agentes Habbos da Kav
const DADOS_AGENTES = {
  augusto: {
    id: "augusto",
    nome: "Augusto",
    cargo: "Supervisor de Operações",
    dept: "Diretoria",
    deskPos: { gx: 7, gy: 2 },
    chairPos: { gx: 6, gy: 2 },
    cafePos: { gx: 1, gy: 4 }, // Ao lado do bebedouro
    skin: "#FCD2A2",
    hair: "#4A2E18",
    hairStyle: "exec",
    shirt: "#0F2942", // Terno Azul Marinho
    tie: "#EEB730",   // Gravata Ouro Kav
    pants: "#0A1C2E",
    shoes: "#111827",
    acc: "tie"
  },
  otavio: {
    id: "otavio",
    nome: "Otávio",
    cargo: "Diretor de Arte Sênior",
    dept: "Criação",
    deskPos: { gx: 11, gy: 2 },
    chairPos: { gx: 10, gy: 2 },
    cafePos: { gx: 10, gy: 2 }, // Fica na mesa focado
    skin: "#FCD2A2",
    hair: "#1E1E24",
    hairStyle: "messy",
    shirt: "#5B21B6", // Blusão Roxo/Indigo
    pants: "#1F2937",
    shoes: "#E5E7EB",
    acc: "glasses"   // Óculos de armação escura
  },
  vicente: {
    id: "vicente",
    nome: "Vicente",
    cargo: "Analista de Tráfego & Performance",
    dept: "Performance",
    deskPos: { gx: 7, gy: 6 },
    chairPos: { gx: 6, gy: 6 },
    cafePos: { gx: 6, gy: 6 }, // Na mesa
    skin: "#F5C294",
    hair: "#111827",
    hairStyle: "short",
    shirt: "#1D4ED8", // Camiseta Azul Royal
    pants: "#1E3A8A",
    shoes: "#38BDF8",
    acc: "headset"   // Fone Gamer com microfone
  },
  clarice: {
    id: "clarice",
    nome: "Clarice",
    cargo: "Redatora & Copywriter",
    dept: "Criação",
    deskPos: { gx: 11, gy: 6 },
    chairPos: { gx: 10, gy: 6 },
    cafePos: { gx: 2, gy: 7 }, // Sentada no Sofá Habbo Club
    skin: "#FEE2D5",
    hair: "#B45309", // Bob Ruivo/Castanho Claro
    hairStyle: "bob",
    shirt: "#BE185D", // Blazer Rosa Magenta
    pants: "#111827",
    shoes: "#18181B",
    acc: "necklace"
  },
  benedito: {
    id: "benedito",
    nome: "Benedito",
    cargo: "Curador de Fotos & Cardápio",
    dept: "Planejamento",
    deskPos: { gx: 7, gy: 10 },
    chairPos: { gx: 6, gy: 10 },
    cafePos: { gx: 1, gy: 2 }, // No balcão de café
    skin: "#E5A97B",
    hair: "#1C1917",
    hairStyle: "crop",
    shirt: "#047857", // Camisa Verde Esmeralda
    pants: "#92400E", // Calça Cáqui
    shoes: "#451A03",
    acc: "badge"
  },
  joaquim: {
    id: "joaquim",
    nome: "Joaquim",
    cargo: "Designer & Arte Finalista",
    dept: "Criação",
    deskPos: { gx: 11, gy: 10 },
    chairPos: { gx: 10, gy: 10 },
    cafePos: { gx: 2, gy: 2 }, // Na banqueta da mesa bistrô
    skin: "#FCD2A2",
    hair: "#18181B",
    hairStyle: "beanie", // Gorro Preto com faixa amarela
    shirt: "#CA8A04",   // Camiseta Amarela
    pants: "#374151",
    shoes: "#DC2626",
    acc: "beanie"
  }
};

// Bancos de Emojis Visuais (SEM TEXTO)
const EMOJIS_CAFE = ["☕", "🍩", "🥐", "🥪", "💬", "😋", "🥤", "✨", "💡", "💭", "🍕", "😄", "🤝"];
const EMOJIS_TRABALHO = {
  augusto:  ["👔", "⚡", "🧠", "⏱️", "🤝", "🎯"],
  otavio:   ["🧐", "🔍", "🎯", "💎", "✅", "✨"],
  vicente:  ["📊", "📈", "💻", "🚀", "📱", "⚡"],
  clarice:  ["✍️", "📝", "💡", "🔥", "🏷️", "✨"],
  benedito: ["📸", "🍽️", "🍗", "🗂️", "🔍", "👌"],
  joaquim:  ["🎨", "📐", "🖼️", "🖌️", "✨", "💫"]
};
const EMOJIS_FESTA = ["🎉", "🥳", "🏆", "👏", "✅", "⭐", "🍕", "🙌"];

// Instância dos Personagens no Mundo Isométrico
class HabboActor {
  constructor(dados) {
    this.dados = dados;
    this.id = dados.id;
    this.nome = dados.nome;
    
    // Começa na posição de café
    this.gx = dados.cafePos.gx;
    this.gy = dados.cafePos.gy;
    this.targetGx = this.gx;
    this.targetGy = this.gy;
    
    // Poses: "sit" | "stand" | "run" | "celebrate"
    this.pose = (this.id === "clarice" || this.id === "joaquim" || this.id === "vicente" || this.id === "otavio") ? "sit" : "stand";
    this.state = "idle"; // "idle" | "running" | "working" | "celebrating"
    
    this.screenX = 0;
    this.screenY = 0;
    this.animTime = Math.random() * 10;
    this.currentEmoji = "☕";
    this.facing = 2; // South-East (135°)
  }

  update(dt) {
    this.animTime += dt;
    
    // Movimento suave na grade isométrica (interpolação)
    const dx = this.targetGx - this.gx;
    const dy = this.targetGy - this.gy;
    const dist = Math.sqrt(dx * dx + dy * dy);

    if (dist > 0.05) {
      // Velocidade de corrida rápida ao dar o Play
      const speed = this.state === "running" ? 6.5 : 2.5;
      this.gx += (dx / dist) * Math.min(dist, speed * dt);
      this.gy += (dy / dist) * Math.min(dist, speed * dt);
      this.pose = "run";
    } else {
      this.gx = this.targetGx;
      this.gy = this.targetGy;

      if (this.state === "running") {
        // Chegou na cadeira da estação de trabalho!
        this.state = "working";
        this.pose = "sit";
        const pool = EMOJIS_TRABALHO[this.id] || ["💻"];
        this.currentEmoji = pool[0];
      } else if (this.state === "working") {
        this.pose = "sit";
      } else if (this.state === "celebrating") {
        this.pose = "celebrate";
      } else if (this.state === "idle") {
        // Se estiver em cima de um móvel que senta (cadeira, sofá, banqueta)
        if (this.isAtChairOrSeat()) {
          this.pose = "sit";
        } else {
          this.pose = "stand";
        }
      }
    }

    const scr = toScreen(this.gx, this.gy);
    this.screenX = scr.x;
    this.screenY = scr.y;
  }

  isAtChairOrSeat() {
    return (
      (this.gx === this.dados.chairPos.gx && this.gy === this.dados.chairPos.gy) ||
      (this.gx === 2 && this.gy === 7) || // Sofá HC
      (this.gx === 2 && this.gy === 2)    // Banqueta
    );
  }
}

// Estado Global do Escritório Habbo
let atores = [];
let estadoGeral = "idle"; // "idle" | "running" | "working" | "celebrating"
let ctx = null;
let canvas = null;
let vaporParticulas = [];
let ultimoTempo = 0;
let intervaloCicloEmojis = null;

// Inicialização Principal
document.addEventListener("DOMContentLoaded", () => {
  canvas = document.getElementById("habbo-canvas");
  if (!canvas) return;
  ctx = canvas.getContext("2d");
  ctx.imageSmoothingEnabled = false;

  iniciarRelogio();
  inicializarAtores();
  inicializarVapor();
  configurarEventosUI();
  iniciarCicloEmojis();

  ultimoTempo = performance.now();
  requestAnimationFrame(loopPrincipal);
});

function iniciarRelogio() {
  const clockEl = document.getElementById("live-clock");
  function tick() {
    const agora = new Date();
    clockEl.textContent = agora.toLocaleTimeString("pt-BR", { hour12: false });
  }
  tick();
  setInterval(tick, 1000);
}

function inicializarAtores() {
  atores = Object.values(DADOS_AGENTES).map(d => new HabboActor(d));
  criarBalõesDOM();
}

function inicializarVapor() {
  vaporParticulas = [];
  for (let i = 0; i < 6; i++) {
    vaporParticulas.push({
      x: 0,
      y: 0,
      offsetY: Math.random() * 16,
      alpha: Math.random(),
      speed: 10 + Math.random() * 8
    });
  }
}

// Cria os balões de fala do Habbo na camada DOM acima dos personagens
function criarBalõesDOM() {
  const layer = document.getElementById("habbo-chat-layer");
  if (!layer) return;
  layer.innerHTML = "";

  atores.forEach(ator => {
    const bubble = document.createElement("div");
    bubble.className = "habbo-bubble";
    bubble.id = `habbo-bubble-${ator.id}`;
    bubble.textContent = ator.currentEmoji;
    bubble.title = `${ator.nome} (${ator.dados.cargo})`;

    bubble.addEventListener("click", () => {
      abrirModalHabbo(ator.id);
    });

    layer.appendChild(bubble);
  });
}

// Loop Principal de Animação e Renderização 60FPS
function loopPrincipal(timestamp) {
  const dt = Math.min((timestamp - ultimoTempo) / 1000, 0.1);
  ultimoTempo = timestamp;

  // Atualiza lógica dos atores
  atores.forEach(a => a.update(dt));

  // Atualiza partículas de vapor da cafeteira
  vaporParticulas.forEach(p => {
    p.offsetY += p.speed * dt;
    if (p.offsetY > 22) {
      p.offsetY = 0;
      p.alpha = 0.9;
    } else {
      p.alpha = 1 - (p.offsetY / 22);
    }
  });

  // Limpa o canvas
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  // 1. Desenha o fundo e paredes do quarto Habbo
  desenharParedesHabbo();

  // 2. Desenha o piso isométrico (Tiles 2:1)
  desenharPisoHabbo();

  // 3. Monta e ordena todas as entidades (Móveis + Personagens) por Profundidade Z
  desenharObjetosEPersonagens();

  // 4. Atualiza posição dos balões de emoji na camada DOM
  atualizarBalõesDOM();

  requestAnimationFrame(loopPrincipal);
}

// ---------------------------------------------------------------------------
// RENDERIZAÇÃO DO QUARTO HABBO (PAREDES & PISO)
// ---------------------------------------------------------------------------

function desenharParedesHabbo() {
  const topPoint = toScreen(0, 0);
  const leftPoint = toScreen(0, GRID_ROWS);
  const rightPoint = toScreen(GRID_COLS, 0);
  const wallH = 145;

  // PAREDE ESQUERDA (Along X = 0)
  ctx.save();
  ctx.beginPath();
  ctx.moveTo(leftPoint.x, leftPoint.y);
  ctx.lineTo(leftPoint.x, leftPoint.y - wallH);
  ctx.lineTo(topPoint.x, topPoint.y - wallH);
  ctx.lineTo(topPoint.x, topPoint.y);
  ctx.closePath();

  // Gradiente suave da parede esquerda
  const gradLeft = ctx.createLinearGradient(leftPoint.x, 0, topPoint.x, 0);
  gradLeft.addColorStop(0, "#061B2E");
  gradLeft.addColorStop(1, "#0A2844");
  ctx.fillStyle = gradLeft;
  ctx.fill();
  ctx.strokeStyle = "#020D17";
  ctx.lineWidth = 2;
  ctx.stroke();

  // Rodapé da parede esquerda
  ctx.beginPath();
  ctx.moveTo(leftPoint.x, leftPoint.y);
  ctx.lineTo(leftPoint.x, leftPoint.y - 12);
  ctx.lineTo(topPoint.x, topPoint.y - 12);
  ctx.lineTo(topPoint.x, topPoint.y);
  ctx.closePath();
  ctx.fillStyle = "#1E130B";
  ctx.fill();
  ctx.strokeStyle = "#0A0603";
  ctx.stroke();

  // 2 JANELAS HABBO NA PAREDE ESQUERDA (Vista Noturna da Cidade)
  desenharJanelaHabbo(leftPoint.x + 80, leftPoint.y - wallH + 35, 65, 75);
  desenharJanelaHabbo(leftPoint.x + 220, leftPoint.y - wallH + 90, 65, 75);

  // Placa Neon na parede esquerda: "☕ KAV CAFÉ & LOUNGE"
  desenharPlacaNeon(leftPoint.x + 130, leftPoint.y - wallH + 18);

  ctx.restore();

  // PAREDE DIREITA (Along Y = 0)
  ctx.save();
  ctx.beginPath();
  ctx.moveTo(topPoint.x, topPoint.y);
  ctx.lineTo(topPoint.x, topPoint.y - wallH);
  ctx.lineTo(rightPoint.x, rightPoint.y - wallH);
  ctx.lineTo(rightPoint.x, rightPoint.y);
  ctx.closePath();

  const gradRight = ctx.createLinearGradient(topPoint.x, 0, rightPoint.x, 0);
  gradRight.addColorStop(0, "#082138");
  gradRight.addColorStop(1, "#0D3356");
  ctx.fillStyle = gradRight;
  ctx.fill();
  ctx.strokeStyle = "#020D17";
  ctx.lineWidth = 2;
  ctx.stroke();

  // Rodapé da parede direita
  ctx.beginPath();
  ctx.moveTo(topPoint.x, topPoint.y);
  ctx.lineTo(topPoint.x, topPoint.y - 12);
  ctx.lineTo(rightPoint.x, rightPoint.y - 12);
  ctx.lineTo(rightPoint.x, rightPoint.y);
  ctx.closePath();
  ctx.fillStyle = "#2D1D10";
  ctx.fill();
  ctx.strokeStyle = "#0A0603";
  ctx.stroke();

  // Lousa Executiva Habbo (Whiteboard) na parede direita
  desenharLousaHabbo(topPoint.x + 60, topPoint.y - wallH + 25);

  // Quadro de Honra Kav
  desenharPosterKav(topPoint.x + 260, topPoint.y - wallH + 105);

  ctx.restore();
}

function desenharJanelaHabbo(x, y, w, h) {
  ctx.save();
  // Moldura chanfrada 3D
  ctx.fillStyle = "#1E293B";
  ctx.fillRect(x - 3, y - 3, w + 6, h + 6);
  ctx.fillStyle = "#0F172A";
  ctx.fillRect(x - 1, y - 1, w + 2, h + 2);

  // Vidro da janela: céu noturno pixel art com lua e arranha-céus iluminados
  ctx.fillStyle = "#020B14";
  ctx.fillRect(x, y, w, h);

  // Lua pixel art
  ctx.fillStyle = "#FEF08A";
  ctx.fillRect(x + w - 16, y + 8, 8, 8);
  ctx.fillStyle = "#FDE047";
  ctx.fillRect(x + w - 14, y + 10, 4, 4);

  // Estrelinhas piscando
  ctx.fillStyle = "#FFFFFF";
  ctx.fillRect(x + 10, y + 12, 1, 1);
  ctx.fillRect(x + 25, y + 20, 2, 2);
  ctx.fillRect(x + 35, y + 8, 1, 1);

  // Silhuetas de prédios com janelas acesas
  ctx.fillStyle = "#061320";
  ctx.fillRect(x + 4, y + h - 35, 18, 35);
  ctx.fillRect(x + 24, y + h - 45, 20, 45);
  ctx.fillRect(x + 46, y + h - 28, 16, 28);

  // Janelinhas amarelas nos prédios
  ctx.fillStyle = "#FACC15";
  for (let r = 0; r < 4; r++) {
    ctx.fillRect(x + 7, y + h - 30 + r * 7, 3, 3);
    ctx.fillRect(x + 14, y + h - 30 + r * 7, 3, 3);
    ctx.fillRect(x + 28, y + h - 40 + r * 8, 3, 3);
    ctx.fillRect(x + 36, y + h - 40 + r * 8, 3, 3);
  }

  // Divisórias da janela
  ctx.strokeStyle = "#334155";
  ctx.lineWidth = 2;
  ctx.strokeRect(x, y, w, h);
  ctx.beginPath();
  ctx.moveTo(x + w / 2, y);
  ctx.lineTo(x + w / 2, y + h);
  ctx.moveTo(x, y + h / 2);
  ctx.lineTo(x + w, y + h / 2);
  ctx.stroke();

  ctx.restore();
}

function desenharPlacaNeon(x, y) {
  ctx.save();
  ctx.fillStyle = "rgba(0, 18, 34, 0.9)";
  ctx.strokeStyle = "#EEB730";
  ctx.lineWidth = 2;
  ctx.fillRect(x, y, 160, 24);
  ctx.strokeRect(x, y, 160, 24);

  ctx.font = "8px 'Press Start 2P', monospace";
  ctx.fillStyle = "#FDE68A";
  ctx.fillText("☕ KAV CAFÉ & LOUNGE", x + 10, y + 16);
  ctx.restore();
}

function desenharLousaHabbo(x, y) {
  ctx.save();
  const w = 150;
  const h = 75;

  // Moldura de alumínio
  ctx.fillStyle = "#94A3B8";
  ctx.fillRect(x - 3, y - 3, w + 6, h + 6);
  ctx.fillStyle = "#F8FAFC";
  ctx.fillRect(x, y, w, h);

  // Cabeçalho da lousa
  ctx.font = "7px 'Press Start 2P', monospace";
  ctx.fillStyle = "#0F172A";
  ctx.fillText("📊 METAS KAV", x + 10, y + 14);

  // Gráfico de barras no whiteboard
  ctx.fillStyle = "#0284C7";
  ctx.fillRect(x + 12, y + 42, 10, 18);
  ctx.fillStyle = "#10B981";
  ctx.fillRect(x + 26, y + 30, 10, 30);
  ctx.fillStyle = "#F59E0B";
  ctx.fillRect(x + 40, y + 22, 10, 38);

  // Post-its coloridos
  ctx.fillStyle = "#FDE047"; // Post-it amarelo
  ctx.fillRect(x + 65, y + 20, 18, 18);
  ctx.fillStyle = "#F472B6"; // Post-it rosa
  ctx.fillRect(x + 88, y + 20, 18, 18);
  ctx.fillStyle = "#38BDF8"; // Post-it ciano
  ctx.fillRect(x + 65, y + 42, 18, 18);

  // Texto simulado
  ctx.fillStyle = "#475569";
  ctx.font = "6px monospace";
  ctx.fillText("53 WhatsApp", x + 112, y + 30);
  ctx.fillText("Meta Ads ON", x + 112, y + 42);

  ctx.restore();
}

function desenharPosterKav(x, y) {
  ctx.save();
  ctx.fillStyle = "#78350F";
  ctx.fillRect(x - 2, y - 2, 74, 54);
  ctx.fillStyle = "#001D32";
  ctx.fillRect(x, y, 70, 50);

  ctx.font = "8px 'Press Start 2P', monospace";
  ctx.fillStyle = "#EEB730";
  ctx.fillText("KAV", x + 20, y + 24);
  ctx.font = "5px monospace";
  ctx.fillStyle = "#E2E8F0";
  ctx.fillText("MARKETING", x + 12, y + 36);
  ctx.restore();
}

function desenharPisoHabbo() {
  for (let gy = 0; gy < GRID_ROWS; gy++) {
    for (let gx = 0; gx < GRID_COLS; gx++) {
      const scr = toScreen(gx, gy);

      ctx.beginPath();
      ctx.moveTo(scr.x, scr.y);
      ctx.lineTo(scr.x + TILE_W / 2, scr.y + TILE_H / 2);
      ctx.lineTo(scr.x, scr.y + TILE_H);
      ctx.lineTo(scr.x - TILE_W / 2, scr.y + TILE_H / 2);
      ctx.closePath();

      // Divisão das áreas no chão:
      if (gx < 5) {
        // ÁREA DO CAFÉ: Parquet de Madeira Quente (Estilo Habbo Wood Floor)
        const isAlt = (gx + gy) % 2 === 0;
        ctx.fillStyle = isAlt ? "#3D2411" : "#4A2D16";
        ctx.fill();
        ctx.strokeStyle = "#271609";
        ctx.lineWidth = 1;
        ctx.stroke();

        // Friso sutil de madeira
        ctx.strokeStyle = isAlt ? "rgba(255,255,255,0.06)" : "rgba(0,0,0,0.15)";
        ctx.beginPath();
        ctx.moveTo(scr.x - 14, scr.y + TILE_H / 2);
        ctx.lineTo(scr.x + 14, scr.y + TILE_H / 2);
        ctx.stroke();
      } else {
        // ÁREA DE TRABALHO EXECUTIVA: Carpete Azul Marinho Kav com borda dourada
        const isAlt = (gx + gy) % 2 === 0;
        ctx.fillStyle = isAlt ? "#082138" : "#0B2A47";
        ctx.fill();
        ctx.strokeStyle = "#041220";
        ctx.lineWidth = 1;
        ctx.stroke();

        // Borda dourada sutil nos cantos de cada tile executivo
        ctx.strokeStyle = "rgba(238, 183, 48, 0.12)";
        ctx.strokeRect(scr.x - 6, scr.y + TILE_H / 2 - 3, 12, 6);
      }
    }
  }
}

// ---------------------------------------------------------------------------
// RENDERIZAÇÃO DOS MÓVEIS (FURNIS) E PERSONAGENS ORDENADOS POR PROFUNDIDADE
// ---------------------------------------------------------------------------

function desenharObjetosEPersonagens() {
  const listaRender = [];

  // 1. Balcão de Café Habbo (Mode Bar)
  listaRender.push({
    tipo: "bar-counter",
    gx: 1, gy: 1, depth: (1 + 1) * 100,
    draw: () => desenharBalcaoBar(1, 1, "espresso")
  });
  listaRender.push({
    tipo: "bar-counter",
    gx: 1, gy: 2, depth: (1 + 2) * 100,
    draw: () => desenharBalcaoBar(1, 2, "cups")
  });

  // 2. Bebedouro Habbo (Water Cooler)
  listaRender.push({
    tipo: "water-cooler",
    gx: 1, gy: 4, depth: (1 + 4) * 100,
    draw: () => desenharBebedouroHabbo(1, 4)
  });

  // 3. Mesa Bistrô e Banquetas
  listaRender.push({
    tipo: "bistro-stool",
    gx: 2, gy: 2, depth: (2 + 2) * 100 - 10,
    draw: () => desenharBanqueta(2, 2)
  });
  listaRender.push({
    tipo: "bistro-table",
    gx: 3, gy: 2, depth: (3 + 2) * 100,
    draw: () => desenharMesaBistro(3, 2)
  });
  listaRender.push({
    tipo: "bistro-stool",
    gx: 4, gy: 2, depth: (4 + 2) * 100,
    draw: () => desenharBanqueta(4, 2)
  });

  // 4. Sofá Habbo Club (HC Sofa) de 2 Lugares em Azul Marinho Kav
  listaRender.push({
    tipo: "hc-sofa",
    gx: 2, gy: 7, depth: (2 + 7) * 100,
    draw: () => desenharSofaSofisticado(2, 7)
  });

  // 5. Plantas Clássicas Habbo (Yucca & Bonsai)
  listaRender.push({
    tipo: "plant-yucca",
    gx: 0, gy: 5, depth: (0 + 5) * 100,
    draw: () => desenharPlantaYucca(0, 5)
  });
  listaRender.push({
    tipo: "plant-bonsai",
    gx: 0, gy: 9, depth: (0 + 9) * 100,
    draw: () => desenharPlantaBonsai(0, 9)
  });

  // 6. As 6 Estações Executivas de Trabalho
  Object.values(DADOS_AGENTES).forEach(ag => {
    // Cadeira Executiva
    listaRender.push({
      tipo: "chair",
      gx: ag.chairPos.gx, gy: ag.chairPos.gy,
      depth: (ag.chairPos.gx + ag.chairPos.gy) * 100 - 20,
      draw: () => desenharCadeiraHabbo(ag.chairPos.gx, ag.chairPos.gy)
    });

    // Mesa com Computador
    listaRender.push({
      tipo: "desk",
      gx: ag.deskPos.gx, gy: ag.deskPos.gy,
      depth: (ag.deskPos.gx + ag.deskPos.gy) * 100 + 40,
      draw: () => desenharMesaComputador(ag)
    });
  });

  // 7. Personagens Humanóides Habbo
  atores.forEach(ator => {
    listaRender.push({
      tipo: "actor",
      gx: ator.gx, gy: ator.gy,
      depth: (ator.gx + ator.gy) * 100 + (ator.pose === "sit" ? -10 : 25),
      draw: () => desenharPersonagemHabbo(ator)
    });
  });

  // Ordena por profundidade (Isometric Depth Sort: do mais longe ao mais perto)
  listaRender.sort((a, b) => a.depth - b.depth);

  // Renderiza em ordem
  listaRender.forEach(item => item.draw());
}

// ---------------------------------------------------------------------------
// DESENHO DOS MÓVEIS (FURNIS)
// ---------------------------------------------------------------------------

function desenharBalcaoBar(gx, gy, extra) {
  const scr = toScreen(gx, gy);
  const h = 26;

  ctx.save();
  // Bloco isométrico do balcão (madeira escura com tampo de mármore)
  // Lado esquerdo
  ctx.beginPath();
  ctx.moveTo(scr.x - TILE_W / 2, scr.y + TILE_H / 2);
  ctx.lineTo(scr.x, scr.y + TILE_H);
  ctx.lineTo(scr.x, scr.y + TILE_H - h);
  ctx.lineTo(scr.x - TILE_W / 2, scr.y + TILE_H / 2 - h);
  ctx.closePath();
  ctx.fillStyle = "#381C0C";
  ctx.fill();
  ctx.stroke();

  // Lado direito
  ctx.beginPath();
  ctx.moveTo(scr.x, scr.y + TILE_H);
  ctx.lineTo(scr.x + TILE_W / 2, scr.y + TILE_H / 2);
  ctx.lineTo(scr.x + TILE_W / 2, scr.y + TILE_H / 2 - h);
  ctx.lineTo(scr.x, scr.y + TILE_H - h);
  ctx.closePath();
  ctx.fillStyle = "#4A2612";
  ctx.fill();
  ctx.stroke();

  // Tampo superior
  ctx.beginPath();
  ctx.moveTo(scr.x, scr.y - h);
  ctx.lineTo(scr.x + TILE_W / 2, scr.y + TILE_H / 2 - h);
  ctx.lineTo(scr.x, scr.y + TILE_H - h);
  ctx.lineTo(scr.x - TILE_W / 2, scr.y + TILE_H / 2 - h);
  ctx.closePath();
  ctx.fillStyle = "#E2E8F0"; // Mármore claro
  ctx.fill();
  ctx.strokeStyle = "#CBD5E1";
  ctx.stroke();

  // Detalhes extras no balcão
  if (extra === "espresso") {
    // Máquina de Café Expresso Italiana
    const mx = scr.x - 2;
    const my = scr.y - h - 14;

    ctx.fillStyle = "#94A3B8";
    ctx.fillRect(mx - 10, my, 20, 16);
    ctx.fillStyle = "#475569";
    ctx.fillRect(mx - 8, my + 4, 16, 6);
    ctx.fillStyle = "#E2E8F0";
    ctx.fillRect(mx - 10, my - 2, 20, 3); // Topo cromado

    // Bico e xícara
    ctx.fillStyle = "#000000";
    ctx.fillRect(mx - 2, my + 10, 4, 4);
    ctx.fillStyle = "#FFFFFF"; // Xícara
    ctx.fillRect(mx - 4, my + 13, 8, 5);

    // Partículas de vapor animadas
    vaporParticulas.forEach(p => {
      ctx.fillStyle = `rgba(255, 255, 255, ${p.alpha})`;
      ctx.beginPath();
      ctx.arc(mx, my - p.offsetY, 2, 0, Math.PI * 2);
      ctx.fill();
    });
  } else if (extra === "cups") {
    // Xícaras de café empilhadas
    const cx = scr.x;
    const cy = scr.y - h - 4;
    ctx.fillStyle = "#FFFFFF";
    ctx.fillRect(cx - 8, cy, 6, 4);
    ctx.fillRect(cx - 7, cy - 4, 6, 4);
    ctx.fillStyle = "#F59E0B"; // Caneca dourada
    ctx.fillRect(cx + 2, cy - 2, 7, 6);
  }

  ctx.restore();
}

function desenharBebedouroHabbo(gx, gy) {
  const scr = toScreen(gx, gy);
  ctx.save();

  // Pedestal branco
  const bx = scr.x;
  const by = scr.y;
  ctx.fillStyle = "#E2E8F0";
  ctx.fillRect(bx - 8, by - 26, 16, 26);
  ctx.fillStyle = "#CBD5E1";
  ctx.fillRect(bx + 4, by - 26, 4, 26);

  // Torneirinhas (vermelha e azul)
  ctx.fillStyle = "#38BDF8";
  ctx.fillRect(bx - 5, by - 16, 3, 3);
  ctx.fillStyle = "#EF4444";
  ctx.fillRect(bx + 2, by - 16, 3, 3);

  // Galão de água azul translúcido invertido
  ctx.fillStyle = "#0284C7";
  ctx.fillRect(bx - 7, by - 44, 14, 18);
  ctx.fillStyle = "#38BDF8";
  ctx.fillRect(bx - 5, by - 42, 6, 14);

  // Bolhas subindo
  const bubbleY = by - 30 - ((performance.now() / 80) % 12);
  ctx.fillStyle = "rgba(255, 255, 255, 0.8)";
  ctx.beginPath();
  ctx.arc(bx, bubbleY, 1.5, 0, Math.PI * 2);
  ctx.fill();

  ctx.restore();
}

function desenharSofaSofisticado(gx, gy) {
  const scr = toScreen(gx, gy);
  ctx.save();

  // Sofá Habbo Club (HC Sofa) em Veludo Azul Marinho Kav com detalhes em Ouro
  const sx = scr.x;
  const sy = scr.y - 12;

  // Base do assento
  ctx.fillStyle = "#0A2540";
  ctx.beginPath();
  ctx.moveTo(sx - 24, sy);
  ctx.lineTo(sx, sy + 12);
  ctx.lineTo(sx + 24, sy);
  ctx.lineTo(sx, sy - 12);
  ctx.closePath();
  ctx.fill();
  ctx.strokeStyle = "#EEB730";
  ctx.lineWidth = 1;
  ctx.stroke();

  // Encosto acolchoado
  ctx.fillStyle = "#0D3356";
  ctx.fillRect(sx - 22, sy - 24, 44, 20);
  ctx.strokeStyle = "#EEB730";
  ctx.strokeRect(sx - 22, sy - 24, 44, 20);

  // Botões dourados capitonê
  ctx.fillStyle = "#EEB730";
  for (let i = -16; i <= 16; i += 8) {
    ctx.fillRect(sx + i, sy - 15, 2, 2);
  }

  // Braços arredondados
  ctx.fillStyle = "#0A2540";
  ctx.fillRect(sx - 26, sy - 16, 6, 16);
  ctx.fillRect(sx + 20, sy - 16, 6, 16);

  ctx.restore();
}

function desenharMesaBistro(gx, gy) {
  const scr = toScreen(gx, gy);
  ctx.save();
  // Pé metálico
  ctx.fillStyle = "#64748B";
  ctx.fillRect(scr.x - 2, scr.y - 20, 4, 22);

  // Tampo redondo
  ctx.fillStyle = "#E2E8F0";
  ctx.beginPath();
  ctx.ellipse(scr.x, scr.y - 22, 16, 9, 0, 0, Math.PI * 2);
  ctx.fill();
  ctx.strokeStyle = "#94A3B8";
  ctx.stroke();

  // Croissant no prato
  ctx.font = "12px sans-serif";
  ctx.fillText("🥐", scr.x - 6, scr.y - 22);

  ctx.restore();
}

function desenharBanqueta(gx, gy) {
  const scr = toScreen(gx, gy);
  ctx.save();
  ctx.fillStyle = "#475569";
  ctx.fillRect(scr.x - 1, scr.y - 14, 2, 16);
  ctx.fillStyle = "#92400E";
  ctx.beginPath();
  ctx.ellipse(scr.x, scr.y - 14, 8, 4, 0, 0, Math.PI * 2);
  ctx.fill();
  ctx.strokeStyle = "#D97706";
  ctx.stroke();
  ctx.restore();
}

function desenharPlantaYucca(gx, gy) {
  const scr = toScreen(gx, gy);
  ctx.save();
  // Vaso terracota
  ctx.fillStyle = "#B45309";
  ctx.beginPath();
  ctx.moveTo(scr.x - 8, scr.y - 12);
  ctx.lineTo(scr.x + 8, scr.y - 12);
  ctx.lineTo(scr.x + 5, scr.y);
  ctx.lineTo(scr.x - 5, scr.y);
  ctx.closePath();
  ctx.fill();
  ctx.strokeStyle = "#78350F";
  ctx.stroke();

  // Folhas pontiagudas Yucca Habbo
  ctx.fillStyle = "#047857";
  ctx.fillRect(scr.x - 2, scr.y - 30, 4, 18);
  ctx.fillStyle = "#10B981";
  ctx.beginPath();
  ctx.moveTo(scr.x, scr.y - 38);
  ctx.lineTo(scr.x + 12, scr.y - 24);
  ctx.lineTo(scr.x, scr.y - 22);
  ctx.fill();
  ctx.beginPath();
  ctx.moveTo(scr.x, scr.y - 38);
  ctx.lineTo(scr.x - 12, scr.y - 24);
  ctx.lineTo(scr.x, scr.y - 22);
  ctx.fill();

  ctx.restore();
}

function desenharPlantaBonsai(gx, gy) {
  const scr = toScreen(gx, gy);
  ctx.save();
  ctx.fillStyle = "#111827";
  ctx.fillRect(scr.x - 10, scr.y - 6, 20, 6);
  ctx.fillStyle = "#451A03"; // Tronco
  ctx.fillRect(scr.x - 2, scr.y - 18, 4, 12);
  ctx.fillStyle = "#059669"; // Copa verde
  ctx.beginPath();
  ctx.arc(scr.x - 3, scr.y - 20, 8, 0, Math.PI * 2);
  ctx.arc(scr.x + 4, scr.y - 22, 9, 0, Math.PI * 2);
  ctx.fill();
  ctx.restore();
}

function desenharCadeiraHabbo(gx, gy) {
  const scr = toScreen(gx, gy);
  ctx.save();

  // Rodinhas e base estrela
  ctx.fillStyle = "#1E293B";
  ctx.fillRect(scr.x - 8, scr.y + 6, 16, 3);
  ctx.fillStyle = "#475569";
  ctx.fillRect(scr.x - 2, scr.y - 4, 4, 10);

  // Assento
  ctx.fillStyle = "#0F172A";
  ctx.beginPath();
  ctx.ellipse(scr.x, scr.y - 4, 11, 6, 0, 0, Math.PI * 2);
  ctx.fill();
  ctx.strokeStyle = "#38BDF8";
  ctx.lineWidth = 1;
  ctx.stroke();

  // Encosto alto ergonômico
  ctx.fillStyle = "#1E293B";
  ctx.fillRect(scr.x - 9, scr.y - 26, 18, 20);
  ctx.strokeStyle = "#475569";
  ctx.strokeRect(scr.x - 9, scr.y - 26, 18, 20);

  ctx.restore();
}

function desenharMesaComputador(ag) {
  const scr = toScreen(ag.deskPos.gx, ag.deskPos.gy);
  const h = 24;

  ctx.save();
  // Bloco da mesa executiva
  // Lado frontal esquerdo
  ctx.beginPath();
  ctx.moveTo(scr.x - TILE_W / 2, scr.y + TILE_H / 2);
  ctx.lineTo(scr.x, scr.y + TILE_H);
  ctx.lineTo(scr.x, scr.y + TILE_H - h);
  ctx.lineTo(scr.x - TILE_W / 2, scr.y + TILE_H / 2 - h);
  ctx.closePath();
  ctx.fillStyle = "#0F243A";
  ctx.fill();
  ctx.strokeStyle = "#071320";
  ctx.stroke();

  // Lado frontal direito
  ctx.beginPath();
  ctx.moveTo(scr.x, scr.y + TILE_H);
  ctx.lineTo(scr.x + TILE_W / 2, scr.y + TILE_H / 2);
  ctx.lineTo(scr.x + TILE_W / 2, scr.y + TILE_H / 2 - h);
  ctx.lineTo(scr.x, scr.y + TILE_H - h);
  ctx.closePath();
  ctx.fillStyle = "#153352";
  ctx.fill();
  ctx.strokeStyle = "#071320";
  ctx.stroke();

  // Tampo superior da mesa
  ctx.beginPath();
  ctx.moveTo(scr.x, scr.y - h);
  ctx.lineTo(scr.x + TILE_W / 2, scr.y + TILE_H / 2 - h);
  ctx.lineTo(scr.x, scr.y + TILE_H - h);
  ctx.lineTo(scr.x - TILE_W / 2, scr.y + TILE_H / 2 - h);
  ctx.closePath();
  ctx.fillStyle = "#1A3E63";
  ctx.fill();
  ctx.strokeStyle = "#EEB730";
  ctx.lineWidth = 1;
  ctx.stroke();

  // Computador Habbo sobre a mesa
  const cx = scr.x;
  const cy = scr.y - h;

  // Monitor
  const isWorking = (estadoGeral === "working");
  ctx.fillStyle = "#0F172A";
  ctx.fillRect(cx - 12, cy - 20, 24, 16);

  // Tela acesa
  ctx.fillStyle = isWorking ? "#38BDF8" : "#0284C7";
  ctx.fillRect(cx - 10, cy - 18, 20, 12);

  if (isWorking) {
    // Efeito de tela brilhando com linhas de código / gráficos
    ctx.fillStyle = "#FFFFFF";
    ctx.fillRect(cx - 8, cy - 15, 8, 2);
    ctx.fillRect(cx - 8, cy - 11, 14, 2);
    ctx.fillRect(cx - 8, cy - 7, 10, 2);

    // Glow na tela
    ctx.strokeStyle = "rgba(56, 189, 248, 0.6)";
    ctx.lineWidth = 2;
    ctx.strokeRect(cx - 12, cy - 20, 24, 16);
  }

  // Teclado e mousepad
  ctx.fillStyle = "#334155";
  ctx.fillRect(cx - 8, cy + 1, 16, 5);
  ctx.fillStyle = "#64748B";
  ctx.fillRect(cx + 9, cy + 2, 4, 4);

  // Plaquinha com nome do Agente na frente da mesa
  ctx.fillStyle = "rgba(0, 18, 34, 0.9)";
  ctx.fillRect(cx - 24, cy + 12, 48, 10);
  ctx.strokeStyle = "#EEB730";
  ctx.strokeRect(cx - 24, cy + 12, 48, 10);

  ctx.font = "6px 'JetBrains Mono', monospace";
  ctx.fillStyle = "#FDE68A";
  ctx.textAlign = "center";
  ctx.fillText(ag.nome, cx, cy + 19);
  ctx.textAlign = "left";

  ctx.restore();
}

// ---------------------------------------------------------------------------
// DESENHO DOS PERSONAGENS HABBO (HUMANÓIDES PIXEL ART)
// ---------------------------------------------------------------------------

function desenharPersonagemHabbo(ator, targetCtx) {
  const c = targetCtx || ctx;
  const sx = ator.screenX;
  const sy = ator.screenY;
  const d = ator.dados;

  c.save();

  // Sombra elíptica no chão
  c.fillStyle = "rgba(0, 0, 0, 0.35)";
  c.beginPath();
  c.ellipse(sx, sy + 4, 12, 6, 0, 0, Math.PI * 2);
  c.fill();

  let yOffset = 0;
  let runCycle = 0;

  if (ator.pose === "run") {
    // Balanço de corrida vigorosa
    runCycle = Math.sin(ator.animTime * 18);
    yOffset = Math.abs(runCycle) * 3;

    // Poeira de corrida no chão 💨
    c.fillStyle = "rgba(255, 255, 255, 0.6)";
    c.beginPath();
    c.arc(sx - 12, sy + 2, 3, 0, Math.PI * 2);
    c.arc(sx - 18, sy + 4, 2, 0, Math.PI * 2);
    c.fill();
  } else if (ator.pose === "celebrate") {
    // Pulo de alegria
    yOffset = Math.abs(Math.sin(ator.animTime * 12)) * 12;
  }

  const baseHeadY = sy - 38 - yOffset;

  if (ator.pose === "sit") {
    // ============================================
    // POSE SENTADO (SITTING) NO HABBO
    // ============================================
    // Pernas dobradas para frente sobre o assento
    c.fillStyle = d.pants;
    c.fillRect(sx - 6, sy - 14, 14, 8); // Coxas dobradas
    c.fillRect(sx + 2, sy - 8, 7, 10);  // Canelas para baixo

    // Sapatos
    c.fillStyle = d.shoes;
    c.fillRect(sx + 2, sy + 2, 8, 4);

    // Tronco / Camisa
    c.fillStyle = d.shirt;
    c.fillRect(sx - 7, sy - 28, 14, 16);

    // Gravata ou detalhe do terno
    if (d.tie) {
      c.fillStyle = d.tie;
      c.fillRect(sx - 1, sy - 26, 3, 10);
    }

    // Braços apoiados digitando no computador
    const typingJitter = (ator.state === "working") ? Math.sin(ator.animTime * 20) * 2 : 0;
    c.fillStyle = d.shirt;
    c.fillRect(sx + 4, sy - 22, 8, 6);
    c.fillStyle = d.skin;
    c.fillRect(sx + 10, sy - 18 + typingJitter, 4, 4); // Mão sobre o teclado

    // Cabeça
    desenharCabecaHabbo(sx, baseHeadY + 8, d, ator, c);

  } else {
    // ============================================
    // POSE EM PÉ / CORRENDO / COMEMORANDO
    // ============================================
    // Pernas
    c.fillStyle = d.pants;
    if (ator.pose === "run") {
      // Pernas alternando na corrida
      const legOffset = runCycle * 6;
      c.fillRect(sx - 6, sy - 18 - yOffset, 5, 14 + legOffset);
      c.fillRect(sx + 1, sy - 18 - yOffset, 5, 14 - legOffset);

      // Sapatos
      c.fillStyle = d.shoes;
      c.fillRect(sx - 7, sy - 4 - yOffset + legOffset, 6, 4);
      c.fillRect(sx, sy - 4 - yOffset - legOffset, 6, 4);
    } else {
      // Em pé reto
      c.fillRect(sx - 6, sy - 18 - yOffset, 5, 14);
      c.fillRect(sx + 1, sy - 18 - yOffset, 5, 14);

      // Sapatos
      c.fillStyle = d.shoes;
      c.fillRect(sx - 7, sy - 4 - yOffset, 6, 4);
      c.fillRect(sx, sy - 4 - yOffset, 6, 4);
    }

    // Tronco / Camisa
    c.fillStyle = d.shirt;
    c.fillRect(sx - 7, sy - 34 - yOffset, 14, 16);

    // Gravata ou detalhe
    if (d.tie) {
      c.fillStyle = d.tie;
      c.fillRect(sx - 1, sy - 32 - yOffset, 3, 11);
    }

    // Braços
    c.fillStyle = d.shirt;
    if (ator.pose === "celebrate") {
      // Braços erguidos em V para o alto \o/
      c.fillRect(sx - 12, sy - 44 - yOffset, 5, 14);
      c.fillRect(sx + 7, sy - 44 - yOffset, 5, 14);
      c.fillStyle = d.skin;
      c.fillRect(sx - 13, sy - 47 - yOffset, 5, 4);
      c.fillRect(sx + 8, sy - 47 - yOffset, 5, 4);
    } else if (ator.pose === "run") {
      // Braços balançando
      c.fillRect(sx - 9, sy - 30 - yOffset - runCycle * 4, 4, 10);
      c.fillRect(sx + 5, sy - 30 - yOffset + runCycle * 4, 4, 10);
      c.fillStyle = d.skin;
      c.fillRect(sx - 9, sy - 20 - yOffset - runCycle * 4, 4, 3);
      c.fillRect(sx + 5, sy - 20 - yOffset + runCycle * 4, 4, 3);
    } else {
      // Em pé relax
      c.fillRect(sx - 10, sy - 32 - yOffset, 4, 12);
      c.fillRect(sx + 6, sy - 32 - yOffset, 4, 12);
      c.fillStyle = d.skin;
      c.fillRect(sx - 10, sy - 20 - yOffset, 4, 3);
      c.fillRect(sx + 6, sy - 20 - yOffset, 4, 3);
    }

    // Cabeça
    desenharCabecaHabbo(sx, baseHeadY, d, ator, c);
  }

  c.restore();
}

function desenharCabecaHabbo(sx, hy, d, ator, targetCtx) {
  const c = targetCtx || ctx;
  // Rosto / Pele (formato clássico Habbo)
  c.fillStyle = d.skin;
  c.fillRect(sx - 8, hy - 14, 16, 14);

  // Olhos pretos característicos do Habbo (2 pixels verticais)
  c.fillStyle = "#111827";
  c.fillRect(sx - 4, hy - 7, 2, 3);
  c.fillRect(sx + 2, hy - 7, 2, 3);

  // Brilho do olho
  c.fillStyle = "#FFFFFF";
  c.fillRect(sx - 4, hy - 8, 1, 1);
  c.fillRect(sx + 2, hy - 8, 1, 1);

  // Sorriso amigável
  c.fillStyle = "#9A3412";
  c.fillRect(sx - 2, hy - 3, 4, 1);

  // Cabelos e Acessórios por personagem
  c.fillStyle = d.hair;

  if (d.hairStyle === "exec") {
    // Augusto: Cabelo executivo alinhado com topete lateral
    c.fillRect(sx - 9, hy - 19, 18, 6);
    c.fillRect(sx - 9, hy - 14, 4, 8);
    c.fillStyle = "#78350F"; // Mecha mais clara
    c.fillRect(sx - 4, hy - 18, 8, 2);
  } else if (d.hairStyle === "messy") {
    // Otávio: Cabelo preto moderno com óculos escuros
    c.fillRect(sx - 9, hy - 19, 18, 6);
    c.fillRect(sx + 3, hy - 15, 6, 6);
    // Óculos retangulares hipsters
    c.fillStyle = "#000000";
    c.fillRect(sx - 6, hy - 9, 5, 4);
    c.fillRect(sx + 1, hy - 9, 5, 4);
    c.fillRect(sx - 1, hy - 8, 2, 1); // Ponte do óculos
    c.fillStyle = "#38BDF8"; // Reflexo azul na lente
    c.fillRect(sx - 5, hy - 8, 2, 2);
    c.fillRect(sx + 2, hy - 8, 2, 2);
  } else if (d.hairStyle === "short") {
    // Vicente: Cabelo escuro com Headset Gamer
    c.fillRect(sx - 9, hy - 18, 18, 5);
    // Headset
    c.fillStyle = "#E2E8F0";
    c.fillRect(sx - 10, hy - 19, 20, 2); // Arco
    c.fillStyle = "#1E293B"; // Conchas
    c.fillRect(sx - 11, hy - 10, 3, 6);
    c.fillRect(sx + 8, hy - 10, 3, 6);
    c.fillStyle = "#38BDF8"; // Luz gamer
    c.fillRect(sx + 9, hy - 9, 2, 3);
  } else if (d.hairStyle === "bob") {
    // Clarice: Bob ruivo / castanho sofisticado
    c.fillRect(sx - 10, hy - 19, 20, 6);
    c.fillRect(sx - 10, hy - 13, 4, 10);
    c.fillRect(sx + 6, hy - 13, 4, 10);
    c.fillStyle = "#F59E0B"; // Luz do cabelo
    c.fillRect(sx - 5, hy - 18, 8, 2);
  } else if (d.hairStyle === "crop") {
    // Benedito: Corte alinhado curto
    c.fillRect(sx - 9, hy - 18, 18, 5);
    c.fillRect(sx - 9, hy - 13, 3, 5);
  } else if (d.hairStyle === "beanie") {
    // Joaquim: Touca/Gorro preto com dobra amarela mostarda
    c.fillStyle = "#18181B";
    c.fillRect(sx - 9, hy - 21, 18, 8);
    c.fillStyle = "#CA8A04"; // Borda amarela da touca
    c.fillRect(sx - 9, hy - 15, 18, 3);
  }
}

// ---------------------------------------------------------------------------
// ATUALIZAÇÃO DOS BALÕES DE CHAT ESTILO HABBO (DOM)
// ---------------------------------------------------------------------------

function atualizarBalõesDOM() {
  atores.forEach(ator => {
    const bubble = document.getElementById(`habbo-bubble-${ator.id}`);
    if (!bubble) return;

    // Posiciona exatamente acima da cabeça do avatar
    const headTopY = (ator.pose === "sit") ? ator.screenY - 50 : ator.screenY - 60;
    bubble.style.left = `${ator.screenX}px`;
    bubble.style.top = `${headTopY}px`;
  });
}

function iniciarCicloEmojis() {
  if (intervaloCicloEmojis) clearInterval(intervaloCicloEmojis);

  intervaloCicloEmojis = setInterval(() => {
    // Escolhe aleatoriamente 1 ou 2 Habbos para mudar de emoji
    const sorteados = [
      atores[Math.floor(Math.random() * atores.length)],
      atores[Math.floor(Math.random() * atores.length)]
    ];

    sorteados.forEach(ator => {
      let novoEmoji = "☕";

      if (estadoGeral === "working") {
        const pool = EMOJIS_TRABALHO[ator.id] || ["💻", "⚡"];
        novoEmoji = pool[Math.floor(Math.random() * pool.length)];
      } else if (estadoGeral === "celebrating") {
        novoEmoji = EMOJIS_FESTA[Math.floor(Math.random() * EMOJIS_FESTA.length)];
      } else if (estadoGeral === "running") {
        novoEmoji = "⚡";
      } else {
        novoEmoji = EMOJIS_CAFE[Math.floor(Math.random() * EMOJIS_CAFE.length)];
      }

      ator.currentEmoji = novoEmoji;
      const bEl = document.getElementById(`habbo-bubble-${ator.id}`);
      if (bEl) {
        bEl.textContent = novoEmoji;
      }
    });
  }, 2200);
}

// ---------------------------------------------------------------------------
// DISPARADA DE CORRIDA PARA AS ESTAÇÕES DE TRABALHO (HABBO PLAY)
// ---------------------------------------------------------------------------

function dispararCorridaParaMesas() {
  estadoGeral = "running";

  const statusLabel = document.getElementById("team-work-status");
  if (statusLabel) statusLabel.textContent = "🏃💨 Habbos correndo pras mesas!";

  const ticker = document.getElementById("feed-ticker");
  if (ticker) ticker.textContent = "⚡ Play disparado! Todos os agentes correndo pelo piso 2.5D para suas estações de trabalho...";

  atores.forEach((ator, i) => {
    ator.state = "running";
    ator.pose = "run";
    ator.currentEmoji = "⚡";

    const bEl = document.getElementById(`habbo-bubble-${ator.id}`);
    if (bEl) bEl.textContent = "⚡";

    // Define o destino como a cadeira da estação executiva
    ator.targetGx = ator.dados.chairPos.gx;
    ator.targetGy = ator.dados.chairPos.gy;
  });
}

function celebrarEntregaHabbo(postFormatado) {
  estadoGeral = "celebrating";

  const statusLabel = document.getElementById("team-work-status");
  if (statusLabel) statusLabel.textContent = "🎉 Post Concluído!";

  const ticker = document.getElementById("feed-ticker");
  if (ticker) ticker.textContent = "🏆 Entrega finalizada com sucesso! Todos os Habbos comemorando o novo post!";

  atores.forEach(ator => {
    ator.state = "celebrating";
    ator.pose = "celebrate";
    ator.currentEmoji = EMOJIS_FESTA[Math.floor(Math.random() * EMOJIS_FESTA.length)];

    const bEl = document.getElementById(`habbo-bubble-${ator.id}`);
    if (bEl) bEl.textContent = ator.currentEmoji;
  });

  if (postFormatado) {
    exibirPostModal(postFormatado);
  }

  // Após 5 segundos, relaxam e alguns voltam para o café
  setTimeout(() => {
    retornarAoModoRelax();
  }, 5000);
}

function retornarAoModoRelax() {
  estadoGeral = "idle";
  const statusLabel = document.getElementById("team-work-status");
  if (statusLabel) statusLabel.textContent = "☕ Relax no Kav Café";

  // Sorteia quem vai para o café
  const quemVaiProCafe = ["clarice", "benedito", "joaquim", "augusto"];

  atores.forEach(ator => {
    ator.state = "idle";
    if (quemVaiProCafe.includes(ator.id)) {
      ator.targetGx = ator.dados.cafePos.gx;
      ator.targetGy = ator.dados.cafePos.gy;
      ator.currentEmoji = "☕";
    } else {
      ator.targetGx = ator.dados.chairPos.gx;
      ator.targetGy = ator.dados.chairPos.gy;
      ator.currentEmoji = "💻";
    }

    const bEl = document.getElementById(`habbo-bubble-${ator.id}`);
    if (bEl) bEl.textContent = ator.currentEmoji;
  });
}

// ---------------------------------------------------------------------------
// EVENTOS DE INTERFACE E DISPARO REAL DE PRODUÇÃO
// ---------------------------------------------------------------------------

function configurarEventosUI() {
  const selectCliente = document.getElementById("select-cliente");
  if (selectCliente) {
    selectCliente.addEventListener("change", () => {
      const lbl = document.getElementById("lbl-cliente-ativo");
      if (lbl) {
        lbl.textContent = selectCliente.options[selectCliente.selectedIndex].text.replace(/^[^\s]+\s+/, "");
      }
    });
  }

  // Clique no canvas para identificar se clicou em um personagem
  canvas.addEventListener("click", (e) => {
    const rect = canvas.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;

    // Procura ator mais próximo do clique
    let clicado = null;
    let minDist = 32;

    atores.forEach(ator => {
      const dx = mouseX - ator.screenX;
      const dy = mouseY - (ator.screenY - 24);
      const d = Math.sqrt(dx * dx + dy * dy);
      if (d < minDist) {
        minDist = d;
        clicado = ator;
      }
    });

    if (clicado) {
      abrirModalHabbo(clicado.id);
    }
  });

  // Fechar modal crachá
  document.getElementById("modal-close").addEventListener("click", () => {
    document.getElementById("agent-modal").classList.remove("open");
  });

  // Fechar modal de post
  document.getElementById("post-modal-close").addEventListener("click", () => {
    document.getElementById("post-delivery-modal").classList.remove("open");
  });

  // Botão copiar legenda
  const btnCopy = document.getElementById("post-modal-copy-btn");
  if (btnCopy) {
    btnCopy.addEventListener("click", () => {
      const copyText = document.getElementById("post-modal-copy").textContent;
      navigator.clipboard.writeText(copyText).then(() => {
        btnCopy.textContent = "✅ Copiado!";
        setTimeout(() => { btnCopy.textContent = "📋 Copiar Legenda"; }, 2000);
      });
    });
  }

  // Botão Refresh
  document.getElementById("btn-refresh").addEventListener("click", () => {
    retornarAoModoRelax();
  });

  // Botão Simulação
  document.getElementById("btn-demo").addEventListener("click", () => {
    const btn = document.getElementById("btn-demo");
    btn.disabled = true;
    btn.textContent = "⏳ Habbos em Ação...";

    dispararCorridaParaMesas();

    setTimeout(() => {
      const simulado = {
        prato: "Prato Executivo do Chefe",
        headline: "Feito no Capricho para o Almoço",
        selo: "Qualidade Garantida",
        legenda: "Aquele almoço saboroso com tempero de casa e ingredientes frescos preparados especialmente pra você. 🍽️\n\nVem saborear o verdadeiro almoço brasileiro no NN Restaurante!\n\nPeça já pelo WhatsApp ou venha nos visitar em Santana de Parnaíba.\n\n#NNRestaurante #ComidaCaseira #Almoço #Gastronomia #SantanaDeParnaiba",
        imagem_b64: null,
        criadores: "Curadoria: Benedito · Texto: Clarice · Arte: Joaquim · Direção: Otávio"
      };
      celebrarEntregaHabbo(simulado);
      btn.disabled = false;
      btn.textContent = "⚡ Simular Corrida";
    }, 4500);
  });

  // Botão Ver Posts
  document.getElementById("btn-ver-posts").addEventListener("click", () => {
    const simulado = {
      prato: "Buffet Executivo Completo",
      headline: "Variedade e Sabor no Seu Dia",
      selo: "Prato do Dia",
      legenda: "Variedade todos os dias com carnes grelhadas na hora, saladas selecionadas e sobremesas deliciosas. 🥩🥗\n\nEsperamos você para o melhor almoço da região!\n\n#NNRestaurante #SantanaDeParnaiba #BuffetExecutivo #Almoço",
      imagem_b64: null,
      criadores: "Equipe Habbo Multi-Agente Kav"
    };
    exibirPostModal(simulado);
  });

  // Disparo Real pelo botão "▶️ Dar o Play"
  const btnPlay = document.getElementById("btn-play");
  if (btnPlay) {
    btnPlay.addEventListener("click", async () => {
      const selectCliente = document.getElementById("select-cliente");
      const slug = selectCliente ? selectCliente.value : "nn-restaurante";

      btnPlay.disabled = true;
      btnPlay.textContent = "⏳ Habbos Produzindo...";

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
          celebrarEntregaHabbo(postFormatado);
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
}

// Modal Crachá / Passaporte Habbo
function abrirModalHabbo(agenteId) {
  const ator = atores.find(a => a.id === agenteId);
  if (!ator) return;

  const info = ator.dados;
  document.getElementById("modal-name").textContent = info.nome;
  document.getElementById("modal-role").textContent = info.cargo;
  document.getElementById("modal-dept").textContent = info.dept;

  document.getElementById("modal-status-text").textContent =
    estadoGeral === "working" ? "Trabalhando no Computador" : "Relaxando no Habbo Café";

  document.getElementById("modal-current-task").textContent =
    estadoGeral === "working" ? "Executando tarefas da esteira autônoma no computador" : "Momento de pausa e alinhamento no café";

  document.getElementById("modal-speech").textContent =
    estadoGeral === "working" ? "⚡ Foco total na entrega do post!" : "☕ Tomando um café e trocando ideias.";

  const historyList = document.getElementById("modal-history");
  historyList.innerHTML = `
    <li>Habbo ID: ${info.id.toUpperCase()}</li>
    <li>Status Atual: ${ator.state.toUpperCase()} (${ator.pose})</li>
    <li>Posição Atual: (${ator.gx.toFixed(1)}, ${ator.gy.toFixed(1)})</li>
    <li>Comunicação: 100% Emojis Visuais</li>
  `;

  // Desenha mini avatar no canvas do passaporte
  const pCanvas = document.getElementById("passport-avatar-canvas");
  if (pCanvas) {
    const pCtx = pCanvas.getContext("2d");
    pCtx.clearRect(0, 0, 64, 64);
    pCtx.save();
    pCtx.translate(32, 54);
    desenharPersonagemHabbo({
      screenX: 0,
      screenY: 0,
      dados: info,
      pose: "stand",
      state: "idle",
      animTime: 0
    }, pCtx);
    pCtx.restore();
  }

  document.getElementById("agent-modal").classList.add("open");
}

// Modal de Entrega do Post Concluído
function exibirPostModal(item) {
  const modal = document.getElementById("post-delivery-modal");
  if (!modal) return;

  document.getElementById("post-modal-headline").textContent = item.headline || item.prato || "NOVO POST";
  document.getElementById("post-modal-selo").textContent = item.selo || "Qualidade Garantida";
  document.getElementById("post-modal-copy").textContent = item.legenda || "";
  document.getElementById("post-modal-creators").textContent = item.criadores || "Equipe Habbo Multi-Agente Kav";

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
