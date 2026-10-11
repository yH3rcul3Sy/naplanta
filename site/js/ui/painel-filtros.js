// Campos de filtro e ordenacao: le e escreve o formulario; quem decide o que aparece e nucleo/filtros.js.
import { CAIXAS, CAMPOS } from '../nucleo/filtros.js';

const $ = id => document.getElementById(id);

// no celular os rotulos somem, entao a primeira opcao (e a do dorms/estacao) diz o que o campo e
const TEXTO_CELULAR = { cidade: ['Todas as cidades'], tipo: ['Todos os tipos'], etapa: ['Todas as etapas'], construtora: ['Construtoras'],
  dorms: ['Dormitórios', '1+ dorm.', '2+ dorms', '3+ dorms', '4+ dorms'], estacao: ['Estação: qualquer', 'Estação até 1 km', 'Estação até 2 km', 'Estação até 3 km'],
  ordem: ['Ordenar'] };

export function criarPainelFiltros({ celular, aoMudar }) {
  function rotular() {
    for (const [id, textos] of Object.entries(TEXTO_CELULAR))
      [...$(id).options].slice(0, textos.length).forEach((o, i) => { o.dataset.pc ??= o.text; o.text = celular.matches ? textos[i] : o.dataset.pc; });
    $('m2').placeholder = celular.matches ? 'Área mín. (m²)' : 'm²';
  }
  rotular();
  celular.addEventListener('change', rotular);
  $('limpar').onclick = () => { CAMPOS.forEach(id => $(id).value = ''); CAIXAS.forEach(id => $(id).checked = false); aoMudar(); };
  [...CAMPOS, ...CAIXAS, 'ordem'].forEach(id => $(id).addEventListener('input', aoMudar));

  return {
    ler: () => ({ ...Object.fromEntries(CAMPOS.map(id => [id, $(id).value])),
                  ...Object.fromEntries(CAIXAS.map(id => [id, $(id).checked])), ordem: $('ordem').value }),
    cidade: () => $('cidade').value,
    // opcoes vindas dos dados; abre em Mogi das Cruzes quando existe
    preencher(dados) {
      for (const k of ['cidade', 'tipo', 'etapa', 'construtora'])
        [...new Set(dados.map(e => e[k]).filter(Boolean))].sort().forEach(v => $(k).add(new Option(v, v)));
      if ([...$('cidade').options].some(o => o.value === 'Mogi das Cruzes')) $('cidade').value = 'Mogi das Cruzes';
    },
    // link ?cidade=: so aceita uma cidade que existe nas opcoes
    escolherCidade(cidade) {
      if ([...$('cidade').options].some(o => o.value === cidade)) $('cidade').value = cidade;
    },
    // para focar um empreendimento escondido pelos filtros: a cidade dele com tudo
    mostrarTudoEm(cidade) {
      CAMPOS.forEach(id => $(id).value = '');
      $('cidade').value = cidade ?? '';
      $('prontos').checked = true; $('mcmv').checked = false;
    },
  };
}
