// Janela de boas-vindas: aparece na primeira visita e pelo botao "Como funciona".
const $ = id => document.getElementById(id);

// sem localStorage (modo privado bloqueado) ela nao aparece, para nao repetir a cada visita
const lerVisto = () => { try { return localStorage.getItem('naplanta-visto'); } catch { return '1'; } };

export function criarBoasVindas() {
  const dialogo = $('boasVindas');
  dialogo.addEventListener('close', () => { try { localStorage.setItem('naplanta-visto', '1'); } catch {} });
  $('comecar').onclick = () => dialogo.close();
  $('comoFunciona').onclick = () => dialogo.showModal();
  return { mostrarSePrimeiraVisita: () => { if (!lerVisto()) dialogo.showModal(); } };
}
