const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const dataBR = iso => iso ? iso.slice(0, 10).split('-').reverse().join('/') : null;
function motivo(erro) {
  if (/nenhum/.test(erro)) return 'O site não responde à coleta automática feita pelos servidores do GitHub. Os dados são atualizados quando a coleta roda no computador do projeto.';
  if (/incompleta/.test(erro)) return 'A coleta de hoje veio incompleta, então a anterior foi mantida.';
  return 'O site estava fora do ar ou mudou de formato, então a coleta anterior foi mantida.';
}
fetch('status.json').then(r => r.ok ? r.json() : Promise.reject()).then(({ coleta, fontes }) => {
  const total = fontes.reduce((s, f) => s + f.total, 0);
  const quando = new Date(coleta).toLocaleString('pt-BR', { dateStyle: 'short', timeStyle: 'short', timeZone: 'America/Sao_Paulo' });
  document.getElementById('resumo').innerHTML =
    `<strong>${total.toLocaleString('pt-BR')} empreendimentos</strong> de ${fontes.length} incorporadoras<br>
     <span class="info">Última coleta: ${quando} · ${fontes.filter(f => f.ok).length} de ${fontes.length} fontes atualizadas</span>`;
  document.getElementById('fontes').innerHTML = [...fontes].sort((a, b) => b.total - a.total).map(f => `
    <div class="fonte">
      <span class="nome">${esc(f.construtora)} <span class="info">· ${f.total} empreendimentos</span></span>
      <span class="selo ${f.ok ? 'ok' : 'aviso'}">${f.ok ? 'Atualizada' : f.atualizada ? 'Dados de ' + dataBR(f.atualizada) : 'Sem atualização'}</span>
      <p class="info"><a href="${esc(f.site)}">${esc(f.site.replace(/^https?:\/\/(www\.)?/, ''))}</a>${f.ok ? '' : ' · ' + motivo(f.erro)}</p>
    </div>`).join('');
}).catch(() => {
  document.getElementById('resumo').textContent = 'A situação de cada fonte aparece aqui depois da próxima coleta.';
});
