// Regras de filtro e ordenacao: recebem os dados e os valores escolhidos, devolvem a lista visivel. Sem DOM.
import { ETAPA } from './etapas.js';

export const CAMPOS = ['cidade', 'bairro', 'tipo', 'etapa', 'construtora', 'dorms', 'estacao', 'm2', 'busca'];
export const CAIXAS = ['prontos', 'mcmv'];

// texto sem acento nem maiuscula, para busca e comparacao
export const simples = s => String(s ?? '').normalize('NFD').replace(/\p{M}/gu, '').toLowerCase();
// distancia em linha reta, em km (a mesma conta de coleta/naplanta/infra/arredores.py)
export const km = (lat1, lng1, lat2, lng2) => Math.hypot((lat2 - lat1) * 111.2, (lng2 - lng1) * 111.2 * Math.cos(lat1 * Math.PI / 180));

// empates e quem nao tem o dado ficam na ordem padrao, no fim; pos = { lat, lng } de quem olha (ordem "perto")
const ORDEM = {
  novos: e => e.desde ? -Date.parse(e.desde) : Infinity,
  estacao: e => e.estacao ? e.estacao.km : Infinity,
  area: e => e.m2 ? -e.m2[1] : Infinity,
  etapa: e => Object.keys(ETAPA).indexOf(e.etapa),
  perto: (e, pos) => pos && e.lat != null ? km(pos.lat, pos.lng, e.lat, e.lng) : Infinity,
};

export function filtrar(dados, f) {
  const q = simples(f.busca).trim();
  return dados.filter(e =>
    (!f.cidade || e.cidade === f.cidade) && (!f.bairro || e.bairro === f.bairro) && (!f.tipo || e.tipo === f.tipo) &&
    (!q || simples(`${e.nome} ${e.bairro ?? ''} ${e.construtora} ${e.endereco ?? ''}`).includes(q)) &&
    // o foco e na planta: prontos so aparecem marcando a caixa ou escolhendo essa etapa
    (f.etapa ? e.etapa === f.etapa : f.prontos || e.etapa !== 'Pronto para morar') &&
    (!f.construtora || e.construtora === f.construtora) &&
    (!f.dorms || (e.dorms && e.dorms[1] >= +f.dorms)) && (!f.m2 || (e.m2 && e.m2[1] >= +f.m2)) &&
    (!f.estacao || (e.estacao && e.estacao.km <= +f.estacao)) && (!f.mcmv || e.mcmv));
}

export function ordenar(lista, ordem, pos) {
  const chave = ORDEM[ordem];
  if (chave) lista.sort((a, b) => chave(a, pos) - chave(b, pos) || 0);
  return lista;
}

export const contarAtivos = f => CAMPOS.filter(id => f[id]).length + CAIXAS.filter(id => f[id]).length;
