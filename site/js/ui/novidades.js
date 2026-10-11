// Painel "O que mudou": desenha os eventos e avisa qual foi escolhido.
import { dataBR, esc } from '../nucleo/formato.js';

const $ = id => document.getElementById(id);
const TIPO_EVENTO = { novo: ['t-novo', 'Novo no site'], etapa: ['t-etapa', 'Mudou de etapa'], saiu: ['t-saiu', 'Saiu do site'] };

export function criarNovidades({ aoEscolher }) {
  const dialogo = $('novidades');
  $('fecharNovidades').onclick = () => dialogo.close();
  dialogo.onclick = ev => { if (ev.target === dialogo) dialogo.close(); };  // clique fora fecha

  return {
    // podeAbrir(e): o empreendimento do evento ainda esta nos dados e tem pino
    mostrar(eventos, { dias, cidade, inicio, podeAbrir }) {
      $('resumoNovidades').textContent = `Últimos ${dias} dias ${cidade ? 'em ' + cidade : 'em todas as cidades'}` +
        (inicio ? ` · acompanhando diariamente desde ${dataBR(inicio)}` : '');
      $('eventos').innerHTML = eventos.length ? '' :
        '<p class="vazio">Nenhuma mudança nesse período.<br>A coleta roda todo dia: lançamentos, trocas de etapa e saídas aparecem aqui.</p>';
      let dia;
      for (const e of eventos) {
        if (e.data !== dia) $('eventos').insertAdjacentHTML('beforeend', `<h3>${dataBR(dia = e.data)}</h3>`);
        const [cls, rotulo] = TIPO_EVENTO[e.tipo];
        const detalhe = e.tipo === 'etapa' ? `${esc(e.de)} → ${esc(e.etapa)}`
          : e.tipo === 'saiu' ? 'Provavelmente esgotado ou retirado pela incorporadora' : esc(e.etapa);
        const b = document.createElement('button');
        b.type = 'button'; b.className = 'evento';
        b.disabled = e.tipo === 'saiu' || !podeAbrir(e);
        b.innerHTML = `<span class="tipo-evento ${cls}">${rotulo}</span><strong>${esc(e.nome)}</strong>
      <span class="info">${esc(e.construtora)} · ${esc(e.cidade ?? '')} · ${detalhe}</span>`;
        b.onclick = () => { dialogo.close(); aoEscolher(e); };
        $('eventos').append(b);
      }
      dialogo.showModal();
    },
  };
}
