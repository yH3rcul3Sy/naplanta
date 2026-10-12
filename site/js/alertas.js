// Inscricao nos alertas: envia e-mail + cidades (atributo CIDADES) para o formulario da Brevo, lista "Alertas · Inscritos" (id 11).
// A Brevo manda o e-mail de confirmacao (dupla confirmacao); o workflow 'alertas' le o atributo e separa por cidade.
const FORM = 'https://26eab4e6.sibforms.com/v2/serve/MUIFAAVKS7lAG6EIHy0lNCUnBhjxcPaTA73UfM8FABKdd9RC_Qe6Zw8n8pGBroQPCAPxsGlOQEqGd6nqcMdefGKGFcghCakjXM7ZYJl9NOFFfsB_HsHpqj3xJgZBME1_UKHwZfZVziaLxXXVc24yFSa7wESWbalLPrGOKBnnpbs_zOd_tzqansrvmvFFOiwmV0FhREVGPMEg-_gCCQ==';
const LISTA = '11';
const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const $ = id => document.getElementById(id);
const pedida = new URLSearchParams(location.search).get('cidade');

function marcadas() { return [...$('cidades').querySelectorAll('input:checked')].map(i => i.value); }
function resumo() {
  const m = marcadas();
  $('escolhidas').textContent = m.length ? 'Escolhidas: ' + m.join(', ') : 'Escolha uma ou mais.';
}

fetch('dados.json').then(r => r.json()).then(dados => {
  const nomes = new Set(dados.map(e => e.cidade).filter(Boolean));
  if (pedida) nomes.add(pedida);
  // a cidade que veio no link fica marcada e no topo; o resto em ordem alfabetica
  const cidades = [...nomes].sort((a, b) => (b === pedida) - (a === pedida) || a.localeCompare(b, 'pt-BR'));
  $('cidades').innerHTML = cidades.map(c => `<label><input type="checkbox" value="${esc(c)}"${c === pedida ? ' checked' : ''}> ${esc(c)}</label>`).join('');
  resumo();
});

$('cidades').addEventListener('change', resumo);
$('busca').addEventListener('input', () => {
  const q = $('busca').value.normalize('NFD').replace(/\p{M}/gu, '').toLowerCase();
  for (const l of $('cidades').children)
    l.hidden = !l.textContent.normalize('NFD').replace(/\p{M}/gu, '').toLowerCase().includes(q);
});

$('form').addEventListener('submit', async ev => {
  ev.preventDefault();
  const resposta = $('resposta'), email = $('email').value.trim(), cidades = marcadas();
  const erro = msg => { resposta.className = 'erro'; resposta.textContent = msg; };
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) return erro('Confira o e-mail digitado.');
  if (!cidades.length) return erro('Escolha pelo menos uma cidade.');
  const corpo = new FormData();
  corpo.append('EMAIL', email);
  corpo.append('CIDADES', cidades.join('; '));
  corpo.append('lists_25[]', LISTA);
  corpo.append('email_address_check', '');
  corpo.append('locale', 'pt');
  $('enviar').disabled = true;
  try {
    const r = await fetch(FORM, { method: 'POST', body: corpo });
    if (!r.ok || !(await r.json()).success) throw new Error();
    resposta.className = 'ok';
    resposta.textContent = 'Quase pronto! Enviamos um e-mail para confirmar a inscrição: abra e clique no link.';
    $('form').reset(); resumo();
  } catch {
    erro('Não foi possível salvar sua inscrição. Tente de novo em alguns minutos.');
  } finally {
    $('enviar').disabled = false;
  }
});
