// Lista de cards: cada card so e criado quando entra na lista, que cresce de LOTE em LOTE conforme a rolagem.
const LOTE = 30;

export function criarLista(el) {
  const fim = document.createElement('div');
  let fila = [], mostrados = 0, indice = new Map();  // fila: { e, card? }; indice: fonte -> posicao
  let criar = () => null;

  const obter = item => item.card ??= criar(item.e);
  function mostrarAte(n) {
    while (mostrados < Math.min(n, fila.length)) el.append(obter(fila[mostrados++]));
    if (mostrados < fila.length) el.append(fim); else fim.remove();
  }
  new IntersectionObserver(es => { if (es[0].isIntersecting) mostrarAte(mostrados + LOTE); }, { root: el, rootMargin: '800px' }).observe(fim);

  return {
    // conteudo(e) -> HTML do card; aoAbrir(e) quando o card de um empreendimento com pino e clicado
    montar(itens, { conteudo, aoAbrir, vazio }) {
      criar = e => {
        const card = document.createElement('article');
        card.className = 'card'; card.tabIndex = 0;
        card.innerHTML = conteudo(e);
        // a foto aparece quando termina de carregar (pode carregar antes do card entrar na pagina, dai o complete)
        for (const img of card.querySelectorAll('img')) {
          const ok = () => img.classList.add('ok');
          if (img.complete) ok(); else { img.onload = ok; img.onerror = ok; }
        }
        if (e.lat != null) {
          const abrir = ev => { if (!ev.target.closest('a')) aoAbrir(e); };
          card.onclick = abrir; card.onkeydown = ev => { if (ev.key === 'Enter') abrir(ev); };
        }
        return card;
      };
      el.innerHTML = ''; mostrados = 0; el.removeAttribute('aria-busy');
      fila = itens.map(e => ({ e }));
      indice = new Map(itens.map((e, i) => [e.fonte, i]));
      if (!itens.length) el.innerHTML = vazio;
      mostrarAte(LOTE);
    },
    // destaca o card (criando e mostrando a lista ate ele, se preciso)
    marcar(fonte, rolar) {
      const i = indice.get(fonte);
      mostrarAte(i + 1);
      const card = obter(fila[i]);
      el.querySelectorAll('.card.ativo').forEach(c => c.classList.remove('ativo'));
      card.classList.add('ativo');
      if (rolar) card.scrollIntoView({ behavior: 'smooth', block: 'center' });
    },
    desmarcar: fonte => fila[indice.get(fonte)]?.card?.classList.remove('ativo'),
  };
}
