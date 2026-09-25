# NaPlanta — stack (tudo grátis/aberto)

| Parte | Ferramenta | Custo |
|---|---|---|
| Coleta (scraping) | Python + httpx + BeautifulSoup (Playwright só em site com JS) | grátis |
| Agendamento | GitHub Actions (cron, ex.: 1x/dia) | grátis (repo público) |
| Banco + API | Supabase (PostgreSQL + PostGIS) | plano free |
| Web | Next.js (React) | grátis |
| Hospedagem | Vercel | plano hobby |
| Mapa | Leaflet + OpenStreetMap | grátis |
| Geocodificação | Nominatim (OSM), 1 req/s, com cache no banco | grátis |

Fluxo: `GitHub Actions → scraper Python → Supabase → Next.js na Vercel → mapa Leaflet`

Regras: respeitar robots.txt e termos de uso, sempre linkar a fonte original, não coletar dados pessoais (LGPD).
