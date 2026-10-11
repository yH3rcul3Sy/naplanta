// Topo e botoes de layout: contadores, painel de filtros e a troca mapa/lista do celular.
const $ = id => document.getElementById(id);

export function criarCabecalho({ redimensionarMapa }) {
  let visiveis = 0;
  const listaAberta = () => document.body.classList.contains('ver-lista');

  function verLista(sim) {
    document.body.classList.toggle('ver-lista', sim);
    $('alternar').textContent = sim ? 'Ver mapa' : `Ver lista · ${visiveis}`;
    if (!sim) redimensionarMapa();
  }
  $('alternar').onclick = () => verLista(!listaAberta());
  $('abrirFiltros').onclick = () => {
    const aberto = document.body.classList.toggle('filtros-abertos');
    $('abrirFiltros').setAttribute('aria-expanded', aberto);
    redimensionarMapa();
  };

  return {
    verLista,
    atualizar({ total, atualizado, filtrosAtivos, novidades }) {
      $('nFiltros').hidden = !filtrosAtivos; $('nFiltros').textContent = filtrosAtivos;
      $('total').textContent = `${total} empreendimento${total === 1 ? '' : 's'}${atualizado}`;
      visiveis = total;
      if (!listaAberta()) $('alternar').textContent = `Ver lista · ${visiveis}`;
      $('nNovidades').hidden = !novidades; $('nNovidades').textContent = novidades;
      $('abrirNovidades').setAttribute('aria-label', `Novidades: ${novidades} na última semana`);
    },
  };
}
