// Liga as pecas: carrega os dados, aplica os filtros e coordena mapa, lista e paineis. Nao desenha nada sozinho.
import { carregar } from './dados.js';
import { contarAtivos, filtrar, ordenar } from './nucleo/filtros.js';
import { diasAtras } from './nucleo/formato.js';
import { DIAS_NOVO, DIAS_PAINEL, eventosRecentes, resumirStatus } from './nucleo/situacao.js';
import { criarBoasVindas } from './ui/boas-vindas.js';
import { criarCabecalho } from './ui/cabecalho.js';
import { criarLista } from './ui/lista.js';
import { criarMapa } from './ui/mapa.js';
import { cartao, popup } from './ui/modelos.js';
import { criarNovidades } from './ui/novidades.js';
import { criarPainelFiltros } from './ui/painel-filtros.js';

const celular = matchMedia('(max-width: 800px)');
let dados = [], mudancas = { inicio: null, eventos: [] }, situacao = { atualizado: '', parados: {} };

const filtros = criarPainelFiltros({ celular, aoMudar: render });
const mapa = criarMapa('mapa', { agruparDeLonge: () => !filtros.cidade() });
const cabecalho = criarCabecalho({ redimensionarMapa: mapa.redimensionar });
const lista = criarLista(document.getElementById('lista'));
const novidades = criarNovidades({ aoEscolher: focar });
const boasVindas = criarBoasVindas();
document.getElementById('abrirNovidades').onclick = () => novidades.mostrar(eventosRecentes(mudancas, filtros.cidade(), DIAS_PAINEL), {
  dias: DIAS_PAINEL, cidade: filtros.cidade(), inicio: mudancas.inicio,
  podeAbrir: ev => dados.some(d => d.fonte === ev.fonte && d.lat != null) });

// abre no mapa e destaca na lista (no celular a lista fica escondida atras do mapa)
function abrir(e, rolar) {
  if (celular.matches) cabecalho.verLista(false);
  mapa.abrir(e);
  lista.marcar(e.fonte, rolar);
}

// vindo das novidades ou de um link: se os filtros o escondem, mostra a cidade dele com tudo
function focar(e) {
  if (!mapa.tem(e.fonte)) { filtros.mostrarTudoEm(e.cidade); render(); }
  if (mapa.tem(e.fonte)) abrir(e, !celular.matches);
}

function render() {
  const f = filtros.ler();
  const visiveis = ordenar(filtrar(dados, f), f.ordem);
  cabecalho.atualizar({ total: visiveis.length, atualizado: situacao.atualizado, filtrosAtivos: contarAtivos(f),
                        novidades: eventosRecentes(mudancas, f.cidade, DIAS_NOVO).length });
  const ctx = { novoDesde: diasAtras(DIAS_NOVO), parados: situacao.parados };
  mapa.montar(visiveis, { popup: e => popup(e, ctx), aoClicar: e => lista.marcar(e.fonte, !celular.matches),
                          aoFecharPopup: e => lista.desmarcar(e.fonte) });
  lista.montar(visiveis, { conteudo: e => cartao(e, ctx), aoAbrir: e => abrir(e, false),
                           vazio: '<p class="vazio">Nenhum empreendimento com esses filtros.<br>Tente limpar algum deles.</p>' });
  mapa.enquadrar();
}

carregar().then(r => {
  ({ dados, mudancas } = r);
  situacao = resumirStatus(r.status);
  filtros.preencher(dados);
  const params = new URLSearchParams(location.search);
  if (params.get('cidade')) filtros.escolherCidade(params.get('cidade'));  // "Ver no mapa" das paginas de cidade
  render();
  // link "Ver no mapa" das paginas de empreendimento: ?e=<pagina>
  const alvo = dados.find(e => e.pagina && e.pagina === params.get('e'));
  if (alvo) focar(alvo); else boasVindas.mostrarSePrimeiraVisita();
}).catch(() => {
  document.getElementById('lista').innerHTML = '<p class="vazio">Não foi possível carregar os empreendimentos.<br>Confira a conexão e recarregue a página.</p>';
});
