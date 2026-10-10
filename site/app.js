const $ = id => document.getElementById(id);
const CAMPOS = ['cidade', 'tipo', 'etapa', 'construtora', 'dorms', 'estacao', 'm2'];
const ETAPA = { 'Breve lançamento': ['e-breve', '#c58a1a'], 'Lançamento': ['e-lanc', '#d0582a'],
                'Em obras': ['e-obras', '#2f6fc4'], 'Pronto para morar': ['e-pronto', '#1f8a58'] };
const celular = matchMedia('(max-width: 800px)');
const mapa = L.map('mapa', { tap: false }).setView([-23.52, -46.19], 11);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  attribution: '&copy; OpenStreetMap contributors', maxZoom: 19 }).addTo(mapa);
// balao com numero so para empreendimentos no mesmo lugar de fato (a ate ~3 m, como Mirage e Solare), em qualquer zoom:
// o raio em pixels acompanha o zoom (metros por pixel ~ 156543 * cos(23°) / 2^z). O balao abre em leque no clique
const METROS_JUNTOS = 3;
const camada = L.markerClusterGroup({ maxClusterRadius: z => METROS_JUNTOS / (144000 / 2 ** z), showCoverageOnHover: false, animate: false,
  iconCreateFunction: g => L.divIcon({ className: 'grupo', html: g.getChildCount(), iconSize: [34, 34] }) }).addTo(mapa);
const legenda = L.control({ position: 'bottomleft' });
legenda.onAdd = () => Object.assign(L.DomUtil.create('div', 'legenda'), {
  innerHTML: Object.entries(ETAPA).map(([n, [, c]]) => `<i style="background:${c}"></i>${n}`).join('<br>') });
legenda.addTo(mapa);
const faixa = (v, u = '') => v ? (v[0] === v[1] ? v[0] : `${v[0]} a ${v[1]}`) + u : null;
const plural = (n, um, varios) => `${n} ${n === 1 ? um : varios}`;
// dados do OpenStreetMap: estacao a ate 3 km e servicos a ate 1 km, distancias em linha reta
function arredores(e) {
  if (e.estacao === undefined) return '';  // ainda nao consultado
  const est = e.estacao
    ? `Estação ${esc(e.estacao.nome)} (${e.estacao.tipo}) · ${e.estacao.km.toLocaleString('pt-BR')} km em linha reta`
    : 'Nenhuma estação de trem ou metrô a até 3 km';
  const p = e.perto || {};
  const servicos = [p.escolas && plural(p.escolas, 'escola', 'escolas'), p.saude && plural(p.saude, 'serviço de saúde', 'serviços de saúde'),
                    p.mercados && plural(p.mercados, 'mercado', 'mercados'), p.parques && plural(p.parques, 'parque', 'parques')].filter(Boolean);
  return `<p class="info perto">${est}</p>` + (servicos.length ? `<p class="info perto">A até 1 km: ${servicos.join(' · ')}</p>` : '');
}
const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const pino = e => L.divIcon({ className: '', iconSize: [18, 18], iconAnchor: [9, 18], popupAnchor: [0, -18],
  html: `<div class="pino" style="background:${(ETAPA[e.etapa] || [, '#666'])[1]}"></div>` });
let dados = [];

function verLista(sim) {
  document.body.classList.toggle('ver-lista', sim);
  $('alternar').textContent = sim ? 'Ver mapa' : 'Ver lista';
  if (!sim) mapa.invalidateSize();
}
$('alternar').onclick = () => verLista(!document.body.classList.contains('ver-lista'));
$('abrirFiltros').onclick = () => {
  const aberto = document.body.classList.toggle('filtros-abertos');
  $('abrirFiltros').setAttribute('aria-expanded', aberto);
  mapa.invalidateSize();
};
$('limpar').onclick = () => { CAMPOS.forEach(id => $(id).value = ''); $('prontos').checked = false; render(); };
CAMPOS.forEach(id => $(id).addEventListener('input', render));
$('prontos').addEventListener('input', render);

const DIAS_NOVO = 7, DIAS_PAINEL = 30;
const diasAtras = n => new Date(Date.now() - n * 864e5).toISOString().slice(0, 10);
const dataBR = iso => iso.split('-').reverse().join('/');
const TIPO_EVENTO = { novo: ['t-novo', 'Novo no site'], etapa: ['t-etapa', 'Mudou de etapa'], saiu: ['t-saiu', 'Saiu do site'] };
let mudancas = { inicio: null, eventos: [] };
const abrirPor = new Map();  // fonte -> funcao que foca o empreendimento no mapa

function eventosVisiveis(dias) {
  const cidade = $('cidade').value, limite = diasAtras(dias);
  return mudancas.eventos.filter(e => e.data >= limite && (!cidade || e.cidade === cidade));
}

function mostrarNovidades() {
  const cidade = $('cidade').value, evs = eventosVisiveis(DIAS_PAINEL);
  $('resumoNovidades').textContent = `Últimos ${DIAS_PAINEL} dias ${cidade ? 'em ' + cidade : 'em todas as cidades'}` +
    (mudancas.inicio ? ` · acompanhando diariamente desde ${dataBR(mudancas.inicio)}` : '');
  $('eventos').innerHTML = evs.length ? '' :
    '<p class="vazio">Nenhuma mudança nesse período.<br>A coleta roda todo dia: lançamentos, trocas de etapa e saídas aparecem aqui.</p>';
  let dia;
  for (const e of evs) {
    if (e.data !== dia) $('eventos').insertAdjacentHTML('beforeend', `<h3>${dataBR(dia = e.data)}</h3>`);
    const [cls, rotulo] = TIPO_EVENTO[e.tipo];
    const detalhe = e.tipo === 'etapa' ? `${esc(e.de)} → ${esc(e.etapa)}`
      : e.tipo === 'saiu' ? 'Provavelmente esgotado ou retirado pela incorporadora' : esc(e.etapa);
    const b = document.createElement('button');
    b.type = 'button'; b.className = 'evento';
    b.disabled = e.tipo === 'saiu' || !dados.some(d => d.fonte === e.fonte && d.lat != null);
    b.innerHTML = `<span class="tipo-evento ${cls}">${rotulo}</span><strong>${esc(e.nome)}</strong>
      <span class="info">${esc(e.construtora)} · ${esc(e.cidade ?? '')} · ${detalhe}</span>`;
    b.onclick = () => {
      $('novidades').close();
      if (!abrirPor.has(e.fonte)) { CAMPOS.forEach(id => $(id).value = ''); $('cidade').value = e.cidade ?? ''; $('prontos').checked = true; render(); }
      abrirPor.get(e.fonte)?.({ target: document.body }, !celular.matches);
    };
    $('eventos').append(b);
  }
  $('novidades').showModal();
}
$('abrirNovidades').onclick = mostrarNovidades;
$('fecharNovidades').onclick = () => $('novidades').close();
$('novidades').onclick = ev => { if (ev.target === $('novidades')) $('novidades').close(); };  // clique fora fecha

// construtora -> dia da ultima coleta que deu certo, so para fontes paradas ha mais de um dia (status.json)
let parados = {};
Promise.all([
  fetch('dados.json').then(r => r.ok ? r.json() : Promise.reject(r.status)),
  fetch('mudancas.json').then(r => r.ok ? r.json() : mudancas).catch(() => mudancas),
  fetch('status.json').then(r => r.ok ? r.json() : { fontes: [] }).catch(() => ({ fontes: [] })),
]).then(([d, m, s]) => {
  dados = d; mudancas = m;
  parados = Object.fromEntries(s.fontes.filter(f => !f.ok && f.atualizada && f.atualizada < diasAtras(1)).map(f => [f.construtora, f.atualizada]));
  for (const k of ['cidade', 'tipo', 'etapa', 'construtora'])
    [...new Set(d.map(e => e[k]).filter(Boolean))].sort().forEach(v => $(k).add(new Option(v, v)));
  if ([...$('cidade').options].some(o => o.value === 'Mogi das Cruzes')) $('cidade').value = 'Mogi das Cruzes';
  render();
}).catch(() => {
  $('lista').innerHTML = '<p class="vazio">Não foi possível carregar os empreendimentos.<br>Confira a conexão e recarregue a página.</p>';
});

function marcar(card, rolar) {
  document.querySelectorAll('.card.ativo').forEach(c => c.classList.remove('ativo'));
  card.classList.add('ativo');
  if (rolar) card.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

function render() {
  const f = Object.fromEntries(CAMPOS.map(id => [id, $(id).value]));
  const vis = dados.filter(e =>
    (!f.cidade || e.cidade === f.cidade) && (!f.tipo || e.tipo === f.tipo) &&
    // o foco e na planta: prontos so aparecem marcando a caixa ou escolhendo essa etapa
    (f.etapa ? e.etapa === f.etapa : $('prontos').checked || e.etapa !== 'Pronto para morar') &&
    (!f.construtora || e.construtora === f.construtora) &&
    (!f.dorms || (e.dorms && e.dorms[1] >= +f.dorms)) && (!f.m2 || (e.m2 && e.m2[1] >= +f.m2)) &&
    (!f.estacao || (e.estacao && e.estacao.km <= +f.estacao)));
  const n = CAMPOS.filter(id => f[id]).length + $('prontos').checked;
  $('nFiltros').hidden = !n; $('nFiltros').textContent = n;
  $('total').textContent = `${vis.length} empreendimento${vis.length === 1 ? '' : 's'}`;
  const nNovidades = eventosVisiveis(DIAS_NOVO).length;
  $('nNovidades').hidden = !nNovidades; $('nNovidades').textContent = nNovidades;
  $('abrirNovidades').setAttribute('aria-label', `Novidades: ${nNovidades} na última semana`);
  const novoDesde = diasAtras(DIAS_NOVO);
  camada.clearLayers(); $('lista').innerHTML = ''; abrirPor.clear(); fila = []; mostrados = 0;
  if (!vis.length) $('lista').innerHTML = '<p class="vazio">Nenhum empreendimento com esses filtros.<br>Tente limpar algum deles.</p>';
  const marcadores = [];
  vis.forEach((e, i) => {
    const [cls] = ETAPA[e.etapa] || [''];
    const fatos = [faixa(e.dorms, ' dorm.'), e.tipo === 'Lote' && e.m2 ? `lotes a partir de ${e.m2[0]} m²` : faixa(e.m2, ' m²')].filter(Boolean).join(' · ');
    const novo = e.desde && e.desde >= novoDesde ? `<span class="selo-novo" title="No site desde ${dataBR(e.desde)}">Novo</span>` : '';
    const html = `<span class="etapa ${cls}">${esc(e.etapa)}</span>${novo}<h2>${esc(e.nome)}</h2>
      <p class="info">${esc(e.tipo)} · ${esc(e.construtora)} · ${esc(e.cidade ?? '')}${e.uf ? ' - ' + esc(e.uf) : ''}</p>
      ${e.endereco ? `<p class="info">${esc(e.endereco)}</p>` : ''}
      ${fatos ? `<p class="fatos">${esc(fatos)}</p>` : ''}
      ${e.entrega ? `<p class="info">Entrega: ${esc(e.entrega)}</p>` : ''}
      ${e.aprox ? '<p class="info aprox">Localização aproximada: o pino está no bairro, não no endereço exato</p>' : ''}
      ${parados[e.construtora] ? `<p class="info aprox">Dados de ${dataBR(parados[e.construtora])}: o site da ${esc(e.construtora)} não respondeu às últimas coletas</p>` : ''}
      ${arredores(e)}
      <a class="fonte" href="${esc(e.fonte)}" target="_blank" rel="noopener">Ver na fonte original ↗</a>`;
    let card, m, abrir;
    const obterCard = () => {  // criado so quando entra na lista (ou quando o pino dele e clicado)
      if (card) return card;
      card = document.createElement('article');
      card.className = 'card'; card.tabIndex = 0;
      card.innerHTML = (e.imagem ? `<img src="${esc(e.imagem)}" alt="" loading="lazy" decoding="async" width="600" height="300">` : '') + `<div class="corpo">${html}</div>`;
      if (abrir) { card.onclick = abrir; card.onkeydown = ev => { if (ev.key === 'Enter') abrir(ev); }; }
      return card;
    };
    const cardVisivel = () => (mostrarAte(i + 1), obterCard());
    fila.push(obterCard);
    if (e.lat == null) return;
    m = L.marker([e.lat, e.lng], { icon: pino(e), title: e.nome }).bindPopup(html, { maxWidth: 260 });
    marcadores.push(m);
    m.on('click', () => marcar(cardVisivel(), !celular.matches));  // no celular a lista fica escondida atras do mapa
    m.on('popupclose', () => card?.classList.remove('ativo'));
    abrir = (ev, rolar = false) => {
      if (ev.target.closest('a')) return;
      if (celular.matches) verLista(false);
      mapa.setView([e.lat, e.lng], 15, { animate: false });
      const grupo = camada.getVisibleParent(m);  // se ainda estiver agrupado, abre o leque antes do popup
      if (grupo && grupo !== m) { camada.once('spiderfied', () => m.openPopup()); grupo.spiderfy(); } else m.openPopup();
      marcar(cardVisivel(), rolar);
    };
    abrirPor.set(e.fonte, abrir);
  });
  camada.addLayers(marcadores);  // em lote: bem mais rapido que um por um
  mostrarAte(LOTE);
  mapa.invalidateSize();
  if (marcadores.length) mapa.fitBounds(camada.getBounds(), { padding: [30, 30], maxZoom: 15 });
}

// a lista cresce de LOTE em LOTE conforme a rolagem chega perto do fim
const LOTE = 30, fimDaLista = document.createElement('div');
let fila = [], mostrados = 0;
function mostrarAte(n) {
  while (mostrados < Math.min(n, fila.length)) $('lista').append(fila[mostrados++]());
  if (mostrados < fila.length) $('lista').append(fimDaLista); else fimDaLista.remove();
}
new IntersectionObserver(es => { if (es[0].isIntersecting) mostrarAte(mostrados + LOTE); },
  { root: $('lista'), rootMargin: '800px' }).observe(fimDaLista);
