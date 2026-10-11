// O que o status.json e o mudancas.json dizem ao visitante. Sem DOM.
import { dataBR, diasAtras, hojeLocal } from './formato.js';

export const DIAS_NOVO = 7, DIAS_PAINEL = 30;

// " · atualizado hoje" ou " · dados de dd/mm", e construtora -> dia da ultima coleta boa das fontes paradas ha mais de um dia
export function resumirStatus(s) {
  const atualizado = !s.coleta ? '' : s.coleta.slice(0, 10) === hojeLocal() ? ' · atualizado hoje' : ` · dados de ${dataBR(s.coleta.slice(0, 10)).slice(0, 5)}`;
  const parados = Object.fromEntries(s.fontes.filter(f => !f.ok && f.atualizada && f.atualizada < diasAtras(1)).map(f => [f.construtora, f.atualizada]));
  return { atualizado, parados };
}

export function eventosRecentes(mudancas, cidade, dias) {
  const limite = diasAtras(dias);
  return mudancas.eventos.filter(e => e.data >= limite && (!cidade || e.cidade === cidade));
}
