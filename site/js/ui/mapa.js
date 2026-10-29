// Mapa Leaflet: pinos, agrupamento, legenda e foco num empreendimento. O resto do app nao fala com o Leaflet.
import { ETAPA } from '../nucleo/etapas.js';

// balao com numero so para empreendimentos no mesmo lugar de fato (a ate ~3 m, como Mirage e Solare), em qualquer zoom:
// o raio em pixels acompanha o zoom (metros por pixel ~ 156543 * cos(23°) / 2^z). O balao abre em leque no clique
const METROS_JUNTOS = 3;

const pino = e => L.divIcon({ className: '', iconSize: [18, 18], iconAnchor: [9, 18], popupAnchor: [0, -18],
  html: `<div class="pino" style="background:${(ETAPA[e.etapa] || [, '#666'])[1]}"></div>` });

// agruparDeLonge(): sem cidade escolhida, de longe (zoom 11 ou menos) agrupa de verdade: ~900 pinos soltos travavam o celular
export function criarMapa(id, { agruparDeLonge }) {
  const mapa = L.map(id, { tap: false }).setView([-23.52, -46.19], 11);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors', maxZoom: 19 }).addTo(mapa);
  const camada = L.markerClusterGroup({ maxClusterRadius: z => agruparDeLonge() && z <= 11 ? 60 : METROS_JUNTOS / (144000 / 2 ** z),
    showCoverageOnHover: false, animate: false,
    iconCreateFunction: g => L.divIcon({ className: 'grupo', html: g.getChildCount(), iconSize: [34, 34] }) }).addTo(mapa);
  const legenda = L.control({ position: 'bottomleft' });
  legenda.onAdd = () => Object.assign(L.DomUtil.create('div', 'legenda'), {
    innerHTML: Object.entries(ETAPA).map(([n, [, c]]) => `<i style="background:${c}"></i>${n}`).join('<br>') });
  legenda.addTo(mapa);
  const marcadores = new Map();  // fonte -> marcador

  return {
    // so os que tem coordenada viram pino
    montar(itens, { popup, aoClicar, aoFecharPopup }) {
      camada.clearLayers();
      // shortcut: API interna do markercluster 1.5.3 (recalcula o raio, que depende da cidade); rever ao trocar de versao
      camada._generateInitialClusters();
      marcadores.clear();
      for (const e of itens) {
        if (e.lat == null) continue;
        const m = L.marker([e.lat, e.lng], { icon: pino(e), title: e.nome }).bindPopup(popup(e), { maxWidth: 240 });
        m.on('click', () => aoClicar(e));
        m.on('popupclose', () => aoFecharPopup(e));
        marcadores.set(e.fonte, m);
      }
      camada.addLayers([...marcadores.values()]);  // em lote: bem mais rapido que um por um
    },
    // animar so quando o usuario muda um filtro: na abertura, o fim da animacao desfazia o foco no pino (link ?e=)
    enquadrar(animar = false) {
      mapa.invalidateSize();
      if (marcadores.size) mapa.fitBounds(camada.getBounds(), { padding: [30, 30], maxZoom: 15, animate: animar, duration: 0.5 });
    },
    tem: fonte => marcadores.has(fonte),
    // e pode ser um evento das novidades (sem coordenada): a posicao vem do pino
    abrir(e) {
      const m = marcadores.get(e.fonte), alvo = m.getLatLng(), zoom = Math.max(mapa.getZoom(), 15);
      const mostrar = () => {
        const grupo = camada.getVisibleParent(m);  // se ainda estiver agrupado, abre o leque antes do popup
        if (grupo && grupo !== m) { camada.once('spiderfied', () => m.openPopup()); grupo.spiderfy(); } else m.openPopup();
      };
      // voo curto ate o pino (pula direto se ja esta la ou se o sistema pede menos movimento)
      if (matchMedia('(prefers-reduced-motion: reduce)').matches || (mapa.getZoom() === zoom && mapa.getCenter().distanceTo(alvo) < 5)) {
        mapa.setView(alvo, zoom, { animate: false }); mostrar();
      } else { mapa.once('moveend', mostrar); mapa.flyTo(alvo, zoom, { duration: 0.6 }); }
    },
    redimensionar: () => mapa.invalidateSize(),
  };
}
