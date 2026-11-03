// Regras de filtro e ordenacao do mapa (site/js/nucleo/filtros.js): node --test coleta/testes/filtros.test.mjs
import assert from 'node:assert/strict';
import { test } from 'node:test';
import { filtrar, ordenar, km } from '../../site/js/nucleo/filtros.js';

const A = { nome: 'Máximo Braz Cubas', bairro: 'Braz Cubas', construtora: 'Ribeira', cidade: 'Mogi das Cruzes', etapa: 'Lançamento', tipo: 'Apartamento',
            dorms: [1, 2], m2: [32, 49], estacao: { km: 0.7 }, mcmv: false, lat: -23.54, lng: -46.22, desde: '2026-10-20', endereco: 'Av. Júlio Simões, 600' };
const B = { nome: 'Pronto X', bairro: 'Centro', construtora: 'Lidera', cidade: 'Mogi das Cruzes', etapa: 'Pronto para morar', tipo: 'Apartamento',
            dorms: [2, 2], m2: [50, 50], estacao: null, mcmv: true, lat: -23.50, lng: -46.18, desde: null };
const C = { nome: 'Sou Mais Suzano', bairro: null, construtora: 'Sousa Araujo', cidade: 'Suzano', etapa: 'Em obras', tipo: 'Apartamento',
            dorms: [2, 2], m2: [46, 46], estacao: { km: 2.5 }, mcmv: true, lat: -23.58, lng: -46.32, desde: '2026-11-01' };
const F = { cidade: '', bairro: '', tipo: '', etapa: '', construtora: '', dorms: '', estacao: '', m2: '', busca: '', prontos: false, mcmv: false, ordem: '' };
const nomes = l => l.map(e => e.nome);

test('prontos ficam de fora por padrao e entram pela caixa ou pela etapa', () => {
  assert.deepEqual(nomes(filtrar([A, B, C], F)), ['Máximo Braz Cubas', 'Sou Mais Suzano']);
  assert.deepEqual(nomes(filtrar([A, B, C], { ...F, prontos: true })), ['Máximo Braz Cubas', 'Pronto X', 'Sou Mais Suzano']);
  assert.deepEqual(nomes(filtrar([A, B, C], { ...F, etapa: 'Pronto para morar' })), ['Pronto X']);
});

test('cidade, bairro, dorms, estacao, area e mcmv', () => {
  assert.deepEqual(nomes(filtrar([A, B, C], { ...F, cidade: 'Suzano' })), ['Sou Mais Suzano']);
  assert.deepEqual(nomes(filtrar([A, B, C], { ...F, cidade: 'Mogi das Cruzes', bairro: 'Braz Cubas' })), ['Máximo Braz Cubas']);
  assert.deepEqual(nomes(filtrar([A, B, C], { ...F, dorms: '2' })), ['Máximo Braz Cubas', 'Sou Mais Suzano']);
  assert.deepEqual(nomes(filtrar([A, B, C], { ...F, estacao: '1' })), ['Máximo Braz Cubas']);
  assert.deepEqual(nomes(filtrar([A, B, C], { ...F, m2: '40' })), ['Máximo Braz Cubas', 'Sou Mais Suzano']);
  assert.deepEqual(nomes(filtrar([A, B, C], { ...F, mcmv: true })), ['Sou Mais Suzano']);
});

test('busca ignora acento e maiuscula e olha nome, bairro, construtora e rua', () => {
  assert.deepEqual(nomes(filtrar([A, B, C], { ...F, busca: 'MAXIMO' })), ['Máximo Braz Cubas']);
  assert.deepEqual(nomes(filtrar([A, B, C], { ...F, busca: 'julio simoes' })), ['Máximo Braz Cubas']);
  assert.deepEqual(nomes(filtrar([A, B, C], { ...F, busca: 'sousa' })), ['Sou Mais Suzano']);
  assert.deepEqual(nomes(filtrar([A, B, C], { ...F, busca: 'nada disso' })), []);
});

test('ordenacao: quem nao tem o dado vai para o fim; perto de mim usa a posicao', () => {
  assert.deepEqual(nomes(ordenar([C, A], 'estacao')), ['Máximo Braz Cubas', 'Sou Mais Suzano']);
  assert.deepEqual(nomes(ordenar([A, C], 'novos')), ['Sou Mais Suzano', 'Máximo Braz Cubas']);
  assert.deepEqual(nomes(ordenar([C, A, B], 'etapa', null)), ['Máximo Braz Cubas', 'Sou Mais Suzano', 'Pronto X']);
  assert.deepEqual(nomes(ordenar([A, C], 'perto', { lat: -23.58, lng: -46.32 })), ['Sou Mais Suzano', 'Máximo Braz Cubas']);
  assert.deepEqual(nomes(ordenar([A, C], 'perto', null)), ['Máximo Braz Cubas', 'Sou Mais Suzano']);  // sem posicao: ordem padrao
  assert.equal(Math.round(km(-23.5, -46.2, -23.51, -46.2) * 100) / 100, 1.11);
});
