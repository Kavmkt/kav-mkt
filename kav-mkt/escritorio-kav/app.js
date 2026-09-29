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
    cafePos: { gx: 1, gy: 4 },
    skin: "#FCD2A2",
    hair: "#4A2E18",
    hairStyle: "exec",
    shirt: "#0F2942",
    tie: "#EEB730",
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
    cafePos: { gx: 10, gy: 2 },
    skin: "#FCD2A2",
    hair: "#1E1E24",
    hairStyle: "messy",
    shirt: "#5B21B6",
    pants: "#1F2937",
    shoes: "#E5E7EB",
    acc: "glasses"
  },
  vicente: {
    id: "vicente",
    nome: "Vicente",
    cargo: "Analista de Tráfego & Performance",
    dept: "Performance",
    deskPos: { gx: 7, gy: 6 },
    chairPos: { gx: 6, gy: 6 },
    cafePos: { gx: 6, gy: 6 },
    skin: "#F5C294",
    hair: "#111827",
    hairStyle: "short",
    shirt: "#1D4ED8",
    pants: "#1E3A8A",
    shoes: "#38BDF8",
    acc: "headset"
  },
  clarice: {
    id: "clarice",
    nome: "Clarice",
    cargo: "Redatora & Copywriter",
    dept: "Criação",
    deskPos: { gx: 11, gy: 6 },
    chairPos: { gx: 10, gy: 6 },
    cafePos: { gx: 2, gy: 7 },
    skin: "#FEE2D5",
    hair: "#B45309",
    hairStyle: "bob",
    shirt: "#BE185D",
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
    cafePos: { gx: 1, gy: 2 },
    skin: "#E5A97B",
    hair: "#1C1917",
    hairStyle: "crop",
    shirt: "#047857",
    pants: "#92400E",
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
    cafePos: { gx: 2, gy: 2 },
    skin: "#FCD2A2",
    hair: "#18181B",
    hairStyle: "beanie",
    shirt: "#CA8A04",
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

class HabboActor {
  constructor(dados) {
    this.dados = dados;
    this.id = dados.id;
    this.nome = dados.nome;
    this.gx = dados.cafePos.gx;
    this.gy = dados.cafePos.gy;
    this.targetGx = this.gx;
    this.targetGy = this.gy;
    this.pose = (this.id === "clarice" || this.id === "joaquim" || this.id === "vicente" || this.id === "otavio") ? "sit" : "stand";
    this.state = "idle";
    this.screenX = 0;
    this.screenY = 0;
    this.animTime = Math.random() * 10;
    this.currentEmoji = "☕";
    this.facing = 2;
  }

  update(dt) {
    this.animTime += dt;
    const dx = this.targetGx - this.gx;
    const dy = this.targetGy - this.gy;
    const dist = Math.sqrt(dx * dx + dy * dy);

    if (dist > 0.05) {
      const speed = this.state === "running" ? 6.5 : 2.5;
      this.gx += (dx / dist) * Math.min(dist, speed * dt);
      this.gy += (dy / dist) * Math.min(dist, speed * dt);
      this.pose = "run";
    } else {
      this.gx = this.targetGx;
      this.gy = this.targetGy;

      if (this.state === "running") {
        this.state = "working";
        this.pose = "sit";
        const pool = EMOJIS_TRABALHO[this.id] || ["💻"];
        this.currentEmoji = pool[0];
      } else if (this.state === "working") {
        this.pose = "sit";
      } else if (this.state === "celebrating") {
        this.pose = "celebrate";
      } else if (this.state === "idle") {
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
      (this.gx === 2 && this.gy === 7) ||
      (this.gx === 2 && this.gy === 2)
    );
  }
}

let atores = [];
let estadoGeral = "idle";
let ctx = null;
let canvas = null;
let vaporParticulas = [];
let ultimoTempo = 0;
let intervaloCicloEmojis = null;

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
    if (clockEl) clockEl.textContent = agora.toLocaleTimeString("pt-BR", { hour12: false });
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

function loopPrincipal(timestamp) {
  const dt = Math.min((timestamp - ultimoTempo) / 1000, 0.1);
  ultimoTempo = timestamp;

  atores.forEach(a => a.update(dt));

  vaporParticulas.forEach(p => {
    p.offsetY += p.speed * dt;
    if (p.offsetY > 22) {
      p.offsetY = 0;
      p.alpha = 0.9;
    } else {
      p.alpha = 1 - (p.offsetY / 22);
    }
  });

  ctx.clearRect(0, 0, canvas.width, canvas.height);
  desenharParedesHabbo();
  desenharPisoHabbo();
  desenharObjetosEPersonagens();
  atualizarBalõesDOM();

  requestAnimationFrame(loopPrincipal);
}

function desenharParedesHabbo() {
  const topPoint = toScreen(0, 0);
  const leftPoint = toScreen(0, GRID_ROWS);
  const rightPoint = toScreen(GRID_COLS, 0);
  const wallH = 145;

  ctx.save();
  ctx.beginPath();
  ctx.moveTo(leftPoint.x, leftPoint.y);
  ctx.lineTo(leftPoint.x, leftPoint.y - wallH);
  ctx.lineTo(topPoint.x, topPoint.y - wallH);
  ctx.lineTo(topPoint.x, topPoint.y);
  ctx.closePath();

  const gradLeft = ctx.createLinearGradient(leftPoint.x, 0, topPoint.x, 0);
  gradLeft.addColorStop(0, "#061B2E");
  gradLeft.addColorStop(1, "#0A2844");
  ctx.fillStyle = gradLeft;
  ctx.fill();
  ctx.strokeStyle = "#020D17";
  ctx.lineWidth = 2;
  ctx.stroke();

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

  desenharJanelaHabbo(leftPoint.x + 80, leftPoint.y - wallH + 35, 65, 75);
  desenharJanelaHabbo(leftPoint.x + 220, leftPoint.y - wallH + 90, 65, 75);
  desenharPlacaNeon(leftPoint.x + 130, leftPoint.y - wallH + 18);
  ctx.restore();

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

  desenharLousaHabbo(topPoint.x + 60, topPoint.y - wallH + 25);
  desenharPosterKav(topPoint.x + 260, topPoint.y - wallH + 105);
  ctx.restore();
}

function desenharJanelaHabbo(x, y, w, h) {
  ctx.save();
  ctx.fillStyle = "#1E293B";
  ctx.fillRect(x - 3, y - 3, w + 6, h + 6);
  ctx.fillStyle = "#0F172A";
  ctx.fillRect(x - 1, y - 1, w + 2, h + 2);
  ctx.fillStyle = "#020B14";
  ctx.fillRect(x, y, w, h);

  ctx.fillStyle = "#FEF08A";
  ctx.fillRect(x + w - 16, y + 8, 8, 8);
  ctx.fillStyle = "#FDE047";
  ctx.fillRect(x + w - 14, y + 10, 4, 4);

  ctx.fillStyle = "#FFFFFF";
  ctx.fillRect(x + 10, y + 12, 1, 1);
  ctx.fillRect(x + 25, y + 20, 2, 2);
  ctx.fillRect(x + 35, y + 8, 1, 1);

  ctx.fillStyle = "#061320";
  ctx.fillRect(x + 4, y + h - 35, 18, 35);
  ctx.fillRect(x + 24, y + h - 45, 20, 45);
  ctx.fillRect(x + 46, y + h - 28, 16, 28);

  ctx.fillStyle = "#FACC15";
  for (let r = 0; r < 4; r++) {
    ctx.fillRect(x + 7, y + h - 30 + r * 7, 3, 3);
    ctx.fillRect(x + 14, y + h - 30 + r * 7, 3, 3);
    ctx.fillRect(x + 28, y + h - 40 + r * 8, 3, 3);
    ctx.fillRect(x + 36, y + h - 40 + r * 8, 3, 3);
  }

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
  ctx.fillStyle = "#94A3B8";
  ctx.fillRect(x - 3, y - 3, w + 6, h + 6);
  ctx.fillStyle = "#F8FAFC";
  ctx.fillRect(x, y, w, h);

  ctx.font = "7px 'Press Start 2P', monospace";
  ctx.fillStyle = "#0F172A";
  ctx.fillText("📊 METAS KAV", x + 10, y + 14);

  ctx.fillStyle = "#0284C7";
  ctx.fillRect(x + 12, y + 42, 10, 18);
  ctx.fillStyle = "#10B981";
  ctx.fillRect(x + 26, y + 30, 10, 30);
  ctx.fillStyle = "#F59E0B";
  ctx.fillRect(x + 40, y + 22, 10, 38);

  ctx.fillStyle = "#FDE047";
  ctx.fillRect(x + 65, y + 20, 18, 18);
  ctx.fillStyle = "#F472B6";
  ctx.fillRect(x + 88, y + 20, 18, 18);
  ctx.fillStyle = "#38BDF8";
  ctx.fillRect(x + 65, y + 42, 18, 18);

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

      if (gx < 5) {
        const isAlt = (gx + gy) % 2 === 0;
        ctx.fillStyle = isAlt ? "#3D2411" : "#4A2D16";
        ctx.fill();
        ctx.strokeStyle = "#271609";
        ctx.lineWidth = 1;
        ctx.stroke();
      } else {
        const isAlt = (gx + gy) % 2 === 0;
        ctx.fillStyle = isAlt ? "#082138" : "#0B2A47";
        ctx.fill();
        ctx.strokeStyle = "#041220";
        ctx.lineWidth = 1;
        ctx.stroke();
      }
    }
  }
}

function desenharObjetosEPersonagens() {
  const listaRender = [];

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
  listaRender.push({
    tipo: "water-cooler",
    gx: 1, gy: 4, depth: (1 + 4) * 100,
    draw: () => desenharBebedouroHabbo(1, 4)
  });
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
  listaRender.push({
    tipo: "hc-sofa",
    gx: 2, gy: 7, depth: (2 + 7) * 100,
    draw: () => desenharSofaSofisticado(2, 7)
  });

  Object.values(DADOS_AGENTES).forEach(ag => {
    listaRender.push({
      tipo: "chair",
      gx: ag.chairPos.gx, gy: ag.chairPos.gy,
      depth: (ag.chairPos.gx + ag.chairPos.gy) * 100 - 20,
      draw: () => desenharCadeiraHabbo(ag.chairPos.gx, ag.chairPos.gy)
    });
    listaRender.push({
      tipo: "desk",
      gx: ag.deskPos.gx, gy: ag.deskPos.gy,
      depth: (ag.deskPos.gx + ag.deskPos.gy) * 100 + 40,
      draw: () => desenharMesaComputador(ag)
    });
  });

  atores.forEach(ator => {
    listaRender.push({
      tipo: "actor",
      gx: ator.gx, gy: ator.gy,
      depth: (ator.gx + ator.gy) * 100 + (ator.pose === "sit" ? -10 : 25),
      draw: () => desenharPersonagemHabbo(ator)
    });
  });

  listaRender.sort((a, b) => a.depth - b.depth);
  listaRender.forEach(item => item.draw());
}

function desenharBalcaoBar(gx, gy, extra) {
  const scr = toScreen(gx, gy);
  const h = 26;
  ctx.save();
  ctx.beginPath();
  ctx.moveTo(scr.x - TILE_W / 2, scr.y + TILE_H / 2);
  ctx.lineTo(scr.x, scr.y + TILE_H);
  ctx.lineTo(scr.x, scr.y + TILE_H - h);
  ctx.lineTo(scr.x - TILE_W / 2, scr.y + TILE_H / 2 - h);
  ctx.closePath();
  ctx.fillStyle = "#381C0C";
  ctx.fill();
  ctx.stroke();

  ctx.beginPath();
  ctx.moveTo(scr.x, scr.y + TILE_H);
  ctx.lineTo(scr.x + TILE_W / 2, scr.y + TILE_H / 2);
  ctx.lineTo(scr.x + TILE_W / 2, scr.y + TILE_H / 2 - h);
  ctx.lineTo(scr.x, scr.y + TILE_H - h);
  ctx.closePath();
  ctx.fillStyle = "#4A2612";
  ctx.fill();
  ctx.stroke();

  ctx.beginPath();
  ctx.moveTo(scr.x, scr.y - h);
  ctx.lineTo(scr.x + TILE_W / 2, scr.y + TILE_H / 2 - h);
  ctx.lineTo(scr.x, scr.y + TILE_H - h);
  ctx.lineTo(scr.x - TILE_W / 2, scr.y + TILE_H / 2 - h);
  ctx.closePath();
  ctx.fillStyle = "#E2E8F0";
  ctx.fill();
  ctx.strokeStyle = "#CBD5E1";
  ctx.stroke();

  if (extra === "espresso") {
    const mx = scr.x - 2;
    const my = scr.y - h - 14;
    ctx.fillStyle = "#94A3B8";
    ctx.fillRect(mx - 10, my, 20, 16);
    ctx.fillStyle = "#475569";
    ctx.fillRect(mx - 8, my + 4, 16, 6);
    ctx.fillStyle = "#FFFFFF";
    ctx.fillRect(mx - 4, my + 13, 8, 5);

    vaporParticulas.forEach(p => {
      ctx.fillStyle = `rgba(255, 255, 255, ${p.alpha})`;
      ctx.beginPath();
      ctx.arc(mx, my - p.offsetY, 2, 0, Math.PI * 2);
      ctx.fill();
    });
  }
  ctx.restore();
}

function desenharBebedouroHabbo(gx, gy) {
  const scr = toScreen(gx, gy);
  ctx.save();
  const bx = scr.x;
  const by = scr.y;
  ctx.fillStyle = "#E2E8F0";
  ctx.fillRect(bx - 8, by - 26, 16, 26);
  ctx.fillStyle = "#0284C7";
  ctx.fillRect(bx - 7, by - 44, 14, 18);
  ctx.restore();
}

function desenharBanqueta(gx, gy) {
  const scr = toScreen(gx, gy);
  ctx.save();
  ctx.fillStyle = "#B45309";
  ctx.beginPath();
  ctx.arc(scr.x, scr.y - 12, 10, 0, Math.PI * 2);
  ctx.fill();
  ctx.restore();
}

function desenharMesaBistro(gx, gy) {
  const scr = toScreen(gx, gy);
  ctx.save();
  ctx.fillStyle = "#0284C7";
  ctx.beginPath();
  ctx.arc(scr.x, scr.y - 20, 16, 0, Math.PI * 2);
  ctx.fill();
  ctx.restore();
}

function desenharSofaSofisticado(gx, gy) {
  const scr = toScreen(gx, gy);
  ctx.save();
  ctx.fillStyle = "#1E3A8A";
  ctx.fillRect(scr.x - 24, scr.y - 20, 48, 20);
  ctx.restore();
}

function desenharCadeiraHabbo(gx, gy) {
  const scr = toScreen(gx, gy);
  ctx.save();
  ctx.fillStyle = "#0F172A";
  ctx.fillRect(scr.x - 8, scr.y - 18, 16, 18);
  ctx.restore();
}

function desenharMesaComputador(ag) {
  const scr = toScreen(ag.deskPos.gx, ag.deskPos.gy);
  ctx.save();
  ctx.fillStyle = "#334155";
  ctx.fillRect(scr.x - 20, scr.y - 22, 40, 22);

  // Monitor
  ctx.fillStyle = "#0F172A";
  ctx.fillRect(scr.x - 12, scr.y - 42, 24, 16);
  ctx.fillStyle = ag.state === "working" ? "#38BDF8" : "#0284C7";
  ctx.fillRect(scr.x - 10, scr.y - 40, 20, 12);
  ctx.restore();
}

function desenharPersonagemHabbo(ator) {
  const scr = toScreen(ator.gx, ator.gy);
  ctx.save();
  const px = scr.x;
  const py = scr.y - (ator.pose === "sit" ? 14 : 26);

  // Cabeça
  ctx.fillStyle = ator.dados.skin;
  ctx.beginPath();
  ctx.arc(px, py - 12, 8, 0, Math.PI * 2);
  ctx.fill();

  // Cabelo
  ctx.fillStyle = ator.dados.hair;
  ctx.beginPath();
  ctx.arc(px, py - 16, 8, Math.PI, Math.PI * 2);
  ctx.fill();

  // Corpo / Camiseta
  ctx.fillStyle = ator.dados.shirt;
  ctx.fillRect(px - 6, py - 4, 12, 14);

  // Calça
  ctx.fillStyle = ator.dados.pants;
  ctx.fillRect(px - 5, py + 10, 10, 10);
  ctx.restore();
}

function atualizarBalõesDOM() {
  atores.forEach(ator => {
    const bubble = document.getElementById(`habbo-bubble-${ator.id}`);
    if (!bubble) return;
    const scr = toScreen(ator.gx, ator.gy);
    bubble.style.left = `${scr.x}px`;
    bubble.style.top = `${scr.y - 50}px`;
    bubble.textContent = ator.currentEmoji;
  });
}

function iniciarCicloEmojis() {
  if (intervaloCicloEmojis) clearInterval(intervaloCicloEmojis);
  intervaloCicloEmojis = setInterval(() => {
    atores.forEach(ator => {
      if (Math.random() < 0.4) {
        if (ator.state === "working") {
          const pool = EMOJIS_TRABALHO[ator.id] || ["💻"];
          ator.currentEmoji = pool[Math.floor(Math.random() * pool.length)];
        } else if (ator.state === "celebrating") {
          ator.currentEmoji = EMOJIS_FESTA[Math.floor(Math.random() * EMOJIS_FESTA.length)];
        } else {
          ator.currentEmoji = EMOJIS_CAFE[Math.floor(Math.random() * EMOJIS_CAFE.length)];
        }
      }
    });
  }, 2500);
}

function dispararCorridaParaMesas() {
  estadoGeral = "running";
  const statusLabel = document.getElementById("team-work-status");
  if (statusLabel) statusLabel.textContent = "🏃💨 Correndo pras mesas!";

  atores.forEach(a => {
    a.state = "running";
    a.targetGx = a.dados.chairPos.gx;
    a.targetGy = a.dados.chairPos.gy;
    a.currentEmoji = "⚡";
  });
}

function celebrarEntrega(postFormatado) {
  estadoGeral = "celebrating";
  const statusLabel = document.getElementById("team-work-status");
  if (statusLabel) statusLabel.textContent = "🎉 Post Concluído!";

  const ticker = document.getElementById("feed-ticker");
  if (ticker) ticker.textContent = `🏆 Entrega finalizada! Post aprovado com sucesso.`;

  atores.forEach(a => {
    a.state = "celebrating";
    a.currentEmoji = EMOJIS_FESTA[Math.floor(Math.random() * EMOJIS_FESTA.length)];
  });

  if (postFormatado) {
    exibirPostModal(postFormatado);
  }

  setTimeout(() => {
    retornarAoModoRelax();
  }, 8000);
}

function retornarAoModoRelax() {
  estadoGeral = "idle";
  const statusLabel = document.getElementById("team-work-status");
  if (statusLabel) statusLabel.textContent = "☕ Modo Relax no Café";

  atores.forEach(a => {
    a.state = "idle";
    a.targetGx = a.dados.cafePos.gx;
    a.targetGy = a.dados.cafePos.gy;
    a.currentEmoji = "☕";
  });
}

function configurarEventosGerais() {
  const btnClose = document.getElementById("modal-close");
  if (btnClose) btnClose.addEventListener("click", fecharModal);

  const btnRefresh = document.getElementById("btn-refresh");
  if (btnRefresh) btnRefresh.addEventListener("click", retornarAoModoRelax);

  const btnDemo = document.getElementById("btn-demo");
  if (btnDemo) {
    btnDemo.addEventListener("click", () => {
      btnDemo.disabled = true;
      dispararCorridaParaMesas();
      setTimeout(() => {
        const simulado = {
          prato: "Tráfego Pago Local para PMEs",
          headline: "PARE DE ANUNCIAR PRA CIDADE INTEIRA",
          selo: "KAV · PERFORMANCE",
          legenda: "Seu cliente ideal está a menos de 10 minutos da sua porta. 🎯📍\n\nQuando você fecha o raio para 3 a 7 km em volta do seu endereço, cada centavo do seu orçamento trabalha para impactar quem realmente compra de você hoje.\n\n👉 Mande um direct para mapearmos o raio do seu negócio!\n\n#KavMkt #TrafegoPagoLocal #MarketingParaPMEs #NegociosLocais",
          imagem_b64: null,
          criadores: "Pauta IA: Benedito · Texto: Clarice · Arte: Joaquim · Direção: Otávio"
        };
        celebrarEntrega(simulado);
        btnDemo.disabled = false;
      }, 5000);
    });
  }
}

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
    if (dlLink) {
      dlLink.href = dataUrl;
      dlLink.download = `post-${(item.prato || item.headline || "arte").toLowerCase().replace(/\s+/g, "-")}.png`;
      dlLink.style.display = "flex";
    }
  } else {
    imgEl.style.display = "none";
    if (imgBox) {
      imgBox.style.display = "block";
      imgBox.textContent = "Arte sem imagem gerada (modo texto).";
    }
    if (dlLink) dlLink.style.display = "none";
  }

  modal.classList.add("open");
}

function fecharPostModal() {
  const modal = document.getElementById("post-delivery-modal");
  if (modal) modal.classList.remove("open");
}

function fecharModal() {
  const modal = document.getElementById("agent-modal");
  if (modal) modal.classList.remove("open");
}

function abrirModal(agentId) {
  const ator = atores.find(a => a.id === agentId);
  if (!ator) return;
  const modal = document.getElementById("agent-modal");
  if (!modal) return;

  document.getElementById("modal-name").textContent = ator.nome;
  document.getElementById("modal-role").textContent = ator.dados.cargo;
  document.getElementById("modal-dept").textContent = ator.dados.dept;
  document.getElementById("modal-status-text").textContent = ator.state === "working" ? "Em Produção" : "Online no Hotel";
  document.getElementById("modal-speech").textContent = ator.currentEmoji + " Humor: " + (ator.state === "working" ? "Focado" : "Relaxando");
  modal.classList.add("open");
}

function abrirModalHabbo(agenteId) {
  abrirModal(agenteId);
}

function configurarEventosUI() {
  configurarEventosGerais();
  const btnClosePost = document.getElementById("post-modal-close");
  if (btnClosePost) btnClosePost.addEventListener("click", fecharPostModal);

  const btnCopy = document.getElementById("post-modal-copy-btn");
  if (btnCopy) {
    btnCopy.addEventListener("click", () => {
      const copyText = document.getElementById("post-modal-copy").textContent;
      navigator.clipboard.writeText(copyText).then(() => {
        btnCopy.textContent = "✅ Copiado!";
        setTimeout(() => btnCopy.textContent = "📋 Copiar Legenda", 2000);
      });
    });
  }

  const btnPlay = document.getElementById("btn-play");
  if (btnPlay) {
    btnPlay.addEventListener("click", () => {
      dispararProducaoReal();
    });
  }

  const selectCli = document.getElementById("select-cliente");
  if (selectCli) {
    selectCli.addEventListener("change", () => {
      const lbl = document.getElementById("lbl-cliente-ativo");
      if (lbl) lbl.textContent = selectCli.options[selectCli.selectedIndex].text;
    });
  }
}

async function dispararProducaoReal() {
  const selectCli = document.getElementById("select-cliente");
  const selectModo = document.getElementById("select-modo");
  const slug = selectCli ? selectCli.value : "nn-restaurante";
  const modo = selectModo ? selectModo.value : "campanha";

  dispararCorridaParaMesas();

  const ticker = document.getElementById("feed-ticker");
  if (ticker) ticker.textContent = `🚀 Disparando esteira de agentes para ${slug.toUpperCase()}...`;

  try {
    const res = await fetch("/api/executar", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ slug, modo, com_imagem: true })
    });
    const dados = await res.json();
    if (dados.sucesso && dados.post) {
      celebrarEntrega(dados.post);
    } else {
      alert("Erro: " + (dados.erro || "Falha na execução dos agentes"));
      retornarAoModoRelax();
    }
  } catch (err) {
    console.error(err);
    alert("Aviso: " + err.message);
    retornarAoModoRelax();
  }
}
