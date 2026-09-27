/**
 * Kav — Agendamento automático de campanhas do Meta Ads (NN Restaurante)
 *
 * O Meta Ads não tem "programação de anúncio por dia/horário" pronta pra esse
 * caso (ad scheduling do Meta só funciona com orçamento vitalício, não diário).
 * Este script substitui isso: liga e desliga as campanhas listadas em
 * CAMPANHAS_GERENCIADAS nos horários da tabela HORARIOS, chamando a API do
 * Meta direto.
 *
 * Horário (America/Sao_Paulo):
 *   Segunda a sexta: liga 09:00, desliga 14:30
 *   Sábado:          liga 09:00, desliga 14:00
 *   Domingo:         nunca liga (fica desligado desde o desligamento de sábado)
 *
 * Roda a cada minuto (gatilho instalado por configurarGatilho(), rodar uma vez)
 * e só chama a API do Meta exatamente nos minutos da tabela — o resto do tempo
 * só confere o relógio e sai.
 *
 * IMPORTANTE — antes de instalar o gatilho, veja o passo 0 nas instruções: o
 * token precisa ter o escopo "ads_management" (o token atual, usado só pelo
 * agente de métricas, é só leitura e vai falhar aqui).
 */

// ===================== CONFIGURAÇÃO =====================

// IDs das campanhas controladas por este agendamento. Adicione mais IDs aqui
// (separados por vírgula) se quiser que outra campanha também siga o horário
// — nunca inclua uma campanha só porque ela "pode" ser reativada; a automação
// vai ligá-la de verdade todo dia às 9h.
const CAMPANHAS_GERENCIADAS = [
  '120242082776660075', // [Whats][09/04][camp2]
];

const GRAPH_API_VERSION = 'v21.0'; // ver developers.facebook.com/docs/graph-api/changelog
// se a Meta desativar essa versão (normalmente ~2 anos depois do lançamento),
// só trocar esse número.

const FUSO_HORARIO = 'America/Sao_Paulo';
const CHAVE_TOKEN = 'META_ACCESS_TOKEN'; // nome da Propriedade do script (passo 3)

// Dia da semana: 0=domingo, 1=segunda ... 6=sábado (igual Date.getDay() em JS)
// Cada linha: [dia, hora, minuto, ação]
const HORARIOS = [
  [1, 9, 0, 'ligar'], [1, 14, 30, 'desligar'], // segunda
  [2, 9, 0, 'ligar'], [2, 14, 30, 'desligar'], // terça
  [3, 9, 0, 'ligar'], [3, 14, 30, 'desligar'], // quarta
  [4, 9, 0, 'ligar'], [4, 14, 30, 'desligar'], // quinta
  [5, 9, 0, 'ligar'], [5, 14, 30, 'desligar'], // sexta
  [6, 9, 0, 'ligar'], [6, 14, 0, 'desligar'],  // sábado (desliga mais cedo)
  // domingo (0): nenhum horário — fica desligado o dia todo
];

// ===================== GATILHO PRINCIPAL =====================

function verificarHorario() {
  const { diaSemana, hora, minuto } = horaAtualEmSaoPaulo_();
  for (const [dia, h, m, acao] of HORARIOS) {
    if (dia === diaSemana && h === hora && m === minuto) {
      Logger.log('Horário bateu: dia=' + dia + ' ' + h + ':' + m + ' -> ' + acao);
      if (acao === 'ligar') ligarCampanhas();
      else desligarCampanhas();
      return; // só uma ação por minuto
    }
  }
}

function horaAtualEmSaoPaulo_() {
  const agora = new Date();
  const dataStr = Utilities.formatDate(agora, FUSO_HORARIO, 'yyyy-MM-dd');
  const horaStr = Utilities.formatDate(agora, FUSO_HORARIO, 'HH:mm');
  const partesData = dataStr.split('-').map(Number);
  const partesHora = horaStr.split(':').map(Number);
  // new Date(ano, mes-1, dia) sem horário: getDay() dá o dia da semana certo
  // pro calendário de São Paulo, sem depender do fuso do servidor do Google.
  const diaSemana = new Date(partesData[0], partesData[1] - 1, partesData[2]).getDay();
  return { diaSemana, hora: partesHora[0], minuto: partesHora[1] };
}

// ===================== AÇÕES =====================

function ligarCampanhas() {
  alterarTodas_('ACTIVE', 'ligar');
}

function desligarCampanhas() {
  alterarTodas_('PAUSED', 'desligar');
}

function alterarTodas_(novoStatus, rotuloAcao) {
  const token = obterToken_();
  CAMPANHAS_GERENCIADAS.forEach((id) => {
    try {
      alterarStatusCampanha_(id, novoStatus, token);
      Logger.log('OK: campanha ' + id + ' -> ' + novoStatus);
    } catch (erro) {
      Logger.log('ERRO ao ' + rotuloAcao + ' campanha ' + id + ': ' + erro);
      notificarErro_(rotuloAcao + ' a campanha ' + id, erro);
    }
  });
}

// ===================== CHAMADAS À API DO META =====================

function alterarStatusCampanha_(campanhaId, novoStatus, token) {
  const url = 'https://graph.facebook.com/' + GRAPH_API_VERSION + '/' + campanhaId
    + '?status=' + novoStatus
    + '&access_token=' + encodeURIComponent(token);
  const resposta = UrlFetchApp.fetch(url, { method: 'post', muteHttpExceptions: true });
  const dados = JSON.parse(resposta.getContentText());
  if (dados.error) {
    throw new Error(dados.error.message + ' (code ' + dados.error.code + ')');
  }
}

function obterToken_() {
  const token = PropertiesService.getScriptProperties().getProperty(CHAVE_TOKEN);
  if (!token) {
    throw new Error('Propriedade "' + CHAVE_TOKEN + '" não configurada nas Propriedades do script.');
  }
  return token;
}

function notificarErro_(acao, erro) {
  try {
    MailApp.sendEmail({
      to: Session.getEffectiveUser().getEmail(),
      subject: '⚠️ Kav — falha no agendamento de campanhas (Meta Ads)',
      body: 'O script de agendamento não conseguiu ' + acao + '.\n\n'
        + 'Erro: ' + erro + '\n\n'
        + 'Causas comuns: token expirado, token sem permissão "ads_management", '
        + 'ou a campanha foi deletada/arquivada no Meta Ads Manager.\n\n'
        + 'Veja "Execuções" no editor do Apps Script para mais detalhes.'
    });
  } catch (e) {
    Logger.log('Não consegui enviar e-mail de erro: ' + e);
  }
}

// ===================== SETUP (rodar manualmente uma vez cada) =====================

/** Roda uma vez pra instalar o gatilho de minuto a minuto. */
function configurarGatilho() {
  ScriptApp.getProjectTriggers().forEach((t) => {
    if (t.getHandlerFunction() === 'verificarHorario') ScriptApp.deleteTrigger(t);
  });
  ScriptApp.newTrigger('verificarHorario').timeBased().everyMinutes(1).create();
  Logger.log('Gatilho instalado: verificarHorario vai rodar a cada minuto.');
}

/** Roda manualmente pra confirmar que o token e os IDs de campanha estão ok,
 * sem ligar/desligar nada. */
function testarConexao() {
  const token = obterToken_();
  CAMPANHAS_GERENCIADAS.forEach((id) => {
    const url = 'https://graph.facebook.com/' + GRAPH_API_VERSION + '/' + id
      + '?fields=id,name,status&access_token=' + encodeURIComponent(token);
    const resposta = UrlFetchApp.fetch(url, { muteHttpExceptions: true });
    Logger.log(resposta.getContentText());
  });
}
