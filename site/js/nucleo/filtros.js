// Regras de filtro e ordenacao: recebem os dados e os valores escolhidos, devolvem a lista visivel. Sem DOM.
import { ETAPA } from './etapas.js';

export const CAMPOS = ['cidade', 'tipo', 'etapa', 'construtora', 'dorms', 'estacao', 'm2'];
export const CAIXAS = ['prontos', 'mcmv'];

// empates e quem nao tem o dado ficam na ordem padrao, no fim
const ORDEM = {
  novos: e => e.desde ? -Date.parse(e.desde) : Infinity,
  estacao: e => e.estacao ? e.estacao.km : Infinity,
  area: e => e.m2 ? -e.m2[1] : Infinity,
  etapa: e => Object.keys(ETAPA).indexOf(e.etapa),
};

export function filtrar(dados, f) {
  return dados.filter(e =>
    (!f.cidade || e.cidade === f.cidade) && (!f.tipo || e.tipo === f.tipo) &&
    // o foco e na planta: prontos so aparecem marcando a caixa ou escolhendo essa etapa
    (f.etapa ? e.etapa === f.etapa : f.prontos || e.etapa !== 'Pronto para morar') &&
    (!f.construtora || e.construtora === f.construtora) &&
    (!f.dorms || (e.dorms && e.dorms[1] >= +f.dorms)) && (!f.m2 || (e.m2 && e.m2[1] >= +f.m2)) &&
    (!f.estacao || (e.estacao && e.estacao.km <= +f.estacao)) && (!f.mcmv || e.mcmv));
}

export function ordenar(lista, ordem) {
  const chave = ORDEM[ordem];
  if (chave) lista.sort((a, b) => chave(a) - chave(b) || 0);
  return lista;
}

export const contarAtivos = f => CAMPOS.filter(id => f[id]).length + CAIXAS.filter(id => f[id]).length;
