// HTML do card da lista e do popup do mapa. Todo texto que vem das fontes passa por esc().
import { ETAPA } from '../nucleo/etapas.js';
import { dataBR, esc, faixa, plural } from '../nucleo/formato.js';

// dados do OpenStreetMap: estacao a ate 3 km e servicos a ate 1 km, distancias em linha reta
function arredores(e) {
  if (e.estacao === undefined) return '';  // ainda nao consultado
  const est = e.estacao
    ? `Estação ${esc(e.estacao.nome)} (${e.estacao.tipo}) · ${e.estacao.km < 0.1 ? 'menos de 100 m' : e.estacao.km.toLocaleString('pt-BR') + ' km'} em linha reta`
    : 'Nenhuma estação de trem ou metrô a até 3 km';
  const p = e.perto || {};
  const servicos = [p.escolas && plural(p.escolas, 'escola', 'escolas'), p.saude && plural(p.saude, 'serviço de saúde', 'serviços de saúde'),
                    p.mercados && plural(p.mercados, 'mercado', 'mercados'), p.parques && plural(p.parques, 'parque', 'parques')].filter(Boolean);
  return `<p class="info perto">${est}</p>` + (servicos.length ? `<p class="info perto">A até 1 km: ${servicos.join(' · ')}</p>` : '');
}

// o que card e popup compartilham; ctx = { novoDesde, parados }
function partes(e, { novoDesde }) {
  const [cls] = ETAPA[e.etapa] || [''];
  const fatos = [faixa(e.dorms, ' dorm.'), e.tipo === 'Lote' && e.m2 ? `lotes a partir de ${e.m2[0]} m²` : faixa(e.m2, ' m²')].filter(Boolean).join(' · ');
  const novo = e.desde && e.desde >= novoDesde ? `<span class="selo-novo" title="No site desde ${dataBR(e.desde)}">Novo</span>` : '';
  const mcmv = e.mcmv ? '<span class="selo-mcmv" title="A página da construtora cita o Minha Casa Minha Vida. Confira as condições no simulador da Caixa.">MCMV</span>' : '';
  const selos = `<span class="etapa ${cls}">${esc(e.etapa)}</span>${novo}${mcmv}`;
  const acao = e.pagina ? `<a class="btn primario" href="e/${esc(e.pagina)}.html">Ver detalhes</a>`
                        : `<a class="btn" href="${esc(e.fonte)}" target="_blank" rel="noopener">Construtora ↗</a>`;
  return { selos, fatos, acao };
}

export function cartao(e, ctx) {
  const { selos, fatos, acao } = partes(e, ctx);
  const corpo = `${selos}<h2>${esc(e.nome)}</h2>
      <p class="info">${esc(e.tipo)} · ${esc(e.construtora)} · ${esc(e.cidade ?? '')}${e.uf ? ' - ' + esc(e.uf) : ''}</p>
      ${e.endereco ? `<p class="info">${esc(e.endereco)}</p>` : ''}
      ${fatos ? `<p class="fatos">${esc(fatos)}</p>` : ''}
      ${e.entrega ? `<p class="info">Entrega: ${esc(e.entrega)}</p>` : ''}
      ${e.aprox ? `<p class="info aprox">Localização aproximada: o pino está ${e.aprox === 'rua' ? 'na rua' : 'no bairro'}, não no endereço exato</p>` : ''}
      ${ctx.parados[e.construtora] ? `<p class="info aprox">Dados de ${dataBR(ctx.parados[e.construtora])}: o site da ${esc(e.construtora)} não respondeu às últimas coletas</p>` : ''}
      ${arredores(e)}
      <div class="acoes">${acao}</div>`;
  return (e.imagem ? `<img src="${esc(e.imagem)}" alt="" loading="lazy" decoding="async" width="600" height="300">` : '') + `<div class="corpo">${corpo}</div>`;
}

// popup curto: o card completo fica na lista e na pagina do empreendimento
export function popup(e, ctx) {
  const { selos, fatos, acao } = partes(e, ctx);
  return `${selos}<h2>${esc(e.nome)}</h2><p class="info">${esc(e.construtora)} · ${esc(e.cidade ?? '')}</p>
      ${fatos ? `<p class="fatos">${esc(fatos)}</p>` : ''}<div class="acoes">${acao}</div>`;
}
