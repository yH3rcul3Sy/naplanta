// Busca os JSON publicados pela coleta. So dados.json e obrigatorio; os outros tem valor padrao.
const SEM_MUDANCAS = { inicio: null, eventos: [] };

export async function carregar() {
  const [dados, mudancas, status] = await Promise.all([
    fetch('dados.json').then(r => r.ok ? r.json() : Promise.reject(r.status)),
    fetch('mudancas.json').then(r => r.ok ? r.json() : SEM_MUDANCAS).catch(() => SEM_MUDANCAS),
    fetch('status.json').then(r => r.ok ? r.json() : { fontes: [] }).catch(() => ({ fontes: [] })),
  ]);
  return { dados, mudancas, status };
}
