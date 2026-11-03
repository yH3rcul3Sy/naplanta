// Campos de filtro e ordenacao: le e escreve o formulario; quem decide o que aparece e nucleo/filtros.js.
import { CAIXAS, CAMPOS } from '../nucleo/filtros.js';

const $ = id => document.getElementById(id);

// os rotulos ficam so para leitor de tela (no celular e no computador), entao a primeira opcao diz o que o campo e
const TEXTO_CELULAR = { cidade: ['Todas as cidades'], bairro: ['Todos os bairros'], tipo: ['Todos os tipos'], etapa: ['Todas as etapas'], construtora: ['Construtoras'],
  dorms: ['Dormitórios', '1+ dorm.', '2+ dorms', '3+ dorms', '4+ dorms'], estacao: ['Estação: qualquer', 'Estação até 1 km', 'Estação até 2 km', 'Estação até 3 km'],
  ordem: ['Ordenar'] };

export function criarPainelFiltros({ aoMudar }) {
  let todos = [];
  for (const [id, textos] of Object.entries(TEXTO_CELULAR))
    [...$(id).options].slice(0, textos.length).forEach((o, i) => { o.text = textos[i]; });
  // os bairros sao os da cidade escolhida; sem cidade (ou com um bairro so) o campo some
  function bairros() {
    const cidade = $('cidade').value, atual = $('bairro').value;
    $('bairro').replaceChildren($('bairro').options[0]);
    [...new Set(todos.filter(e => e.cidade === cidade).map(e => e.bairro).filter(Boolean))].sort((a, b) => a.localeCompare(b, 'pt-BR')).forEach(v => $('bairro').add(new Option(v, v)));
    $('bairro').value = atual; $('bairro').closest('label').hidden = !cidade || $('bairro').options.length < 3;
  }
  $('cidade').addEventListener('input', bairros);
  $('limpar').onclick = () => { CAMPOS.forEach(id => $(id).value = ''); CAIXAS.forEach(id => $(id).checked = false); bairros(); aoMudar(); };
  [...CAMPOS, ...CAIXAS, 'ordem'].forEach(id => $(id).addEventListener('input', aoMudar));

  return {
    ler: () => ({ ...Object.fromEntries(CAMPOS.map(id => [id, $(id).value])),
                  ...Object.fromEntries(CAIXAS.map(id => [id, $(id).checked])), ordem: $('ordem').value }),
    cidade: () => $('cidade').value,
    // opcoes vindas dos dados; abre em Mogi das Cruzes quando existe
    preencher(dados) {
      todos = dados;
      for (const k of ['cidade', 'tipo', 'etapa', 'construtora'])
        [...new Set(dados.map(e => e[k]).filter(Boolean))].sort().forEach(v => $(k).add(new Option(v, v)));
      if ([...$('cidade').options].some(o => o.value === 'Mogi das Cruzes')) $('cidade').value = 'Mogi das Cruzes';
      bairros();
    },
    // filtros no link (?cidade=Suzano&dorms=2&ordem=estacao): so valores que existem; a cidade entra mesmo vazia ("todas")
    daURL(params) {
      const livre = ['cidade', 'busca', 'm2'];
      for (const id of [...CAMPOS, 'ordem']) if (params.has(id) && (livre.includes(id) || [...$(id).options].some(o => o.value === params.get(id)))) $(id).value = params.get(id);
      for (const id of CAIXAS) if (params.has(id)) $(id).checked = params.get(id) === '1';
      bairros();
      if (params.has('bairro')) $('bairro').value = params.get('bairro');
    },
    paraURL() {
      const p = new URLSearchParams();
      for (const id of [...CAMPOS, 'ordem']) if ($(id).value || id === 'cidade') p.set(id, $(id).value);
      for (const id of CAIXAS) if ($(id).checked) p.set(id, '1');
      return p;
    },
    // link ?cidade=: so aceita uma cidade que existe nas opcoes
    escolherCidade(cidade) {
      if ([...$('cidade').options].some(o => o.value === cidade)) $('cidade').value = cidade;
      bairros();
    },
    // para focar um empreendimento escondido pelos filtros: a cidade dele com tudo
    mostrarTudoEm(cidade) {
      CAMPOS.forEach(id => $(id).value = '');
      $('cidade').value = cidade ?? '';
      $('prontos').checked = true; $('mcmv').checked = false;
      bairros();
    },
  };
}
