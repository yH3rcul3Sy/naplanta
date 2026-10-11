// Texto e data: funcoes puras, sem DOM nem Leaflet.
export const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
export const faixa = (v, u = '') => v ? (v[0] === v[1] ? v[0] : `${v[0]} a ${v[1]}`) + u : null;
export const plural = (n, um, varios) => `${n} ${n === 1 ? um : varios}`;
export const diasAtras = n => new Date(Date.now() - n * 864e5).toISOString().slice(0, 10);
export const dataBR = iso => iso.split('-').reverse().join('/');
// data local: diasAtras usa UTC e erraria a noite
export const hojeLocal = () => new Date().toLocaleDateString('sv');
