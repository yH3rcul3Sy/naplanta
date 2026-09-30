# NaPlanta

Mapa gratuito de lançamentos imobiliários na planta, com foco em **Mogi das Cruzes e no Alto Tietê**, que também cobre a Grande São Paulo e outras capitais.

**Acesse:** https://yh3rcul3sy.github.io/naplanta/

Os dados vêm direto dos sites das próprias incorporadoras e são atualizados automaticamente todo dia. Cada empreendimento leva à página oficial, sem corretor nem intermediário.

Projeto acadêmico da Universidade de Mogi das Cruzes (UMC), submetido ao UMC Summit.

## O que o site faz

- **Mapa e lista** de cerca de 850 empreendimentos de 11 incorporadoras, com filtros por cidade, tipo (apartamento, casa em condomínio, lote), etapa da obra, construtora, dormitórios, área e distância até a estação.
- **Estação de trem ou metrô mais próxima** (até 3 km) e escolas, serviços de saúde, mercados e parques a até 1 km, em linha reta.
- **O que mudou:** lançamentos novos, mudanças de etapa e empreendimentos que saíram do site, comparando cada coleta com a do dia anterior.
- **Sobre os dados:** página com a situação de cada fonte, a data da última coleta, as regras de coleta e os limites.
- Funciona no celular e pode ser **adicionado à tela inicial** como um app.

## Como funciona

```
GitHub Actions (todo dia)
  └─ coleta/coletar.py
       ├─ um coletor por incorporadora  →  nome, etapa, endereço, dormitórios, área, foto
       ├─ geo.py        →  confere a coordenada (Nominatim) e leva o pino ao prédio de mesmo nome no OpenStreetMap
       ├─ arredores.py  →  estação e serviços próximos (Overpass / OpenStreetMap)
       ├─ fotos.py      →  miniaturas WebP servidas pelo próprio site
       └─ grava site/dados.json, mudancas.json e status.json
  └─ publica a pasta site/ no GitHub Pages
```

O site é estático: um único `index.html` lê o `dados.json` e desenha o mapa com Leaflet. Não há servidor nem banco de dados.

## Regras da coleta

- Só lê o que o `robots.txt` de cada site permite. **Bloqueios nunca são contornados**: a MRV, a Plano&Plano, a Habras e a Cyrela ficaram de fora por isso.
- Identifica-se como `NaPlantaBot/0.1 (projeto academico UMC)` e espera 1 segundo entre páginas.
- Guarda só informações públicas do empreendimento. **Não coleta preços nem dados pessoais.**
- Empreendimentos 100% vendidos ficam de fora.
- Se um site falha, responde vazio ou perde mais de 30% dos empreendimentos de um dia para o outro, os dados da coleta anterior são mantidos.

## Fontes

| Incorporadora | Região principal |
|---|---|
| Helbor | Mogi das Cruzes, São Paulo e outras capitais |
| C.A.C Engenharia | Mogi das Cruzes |
| Integra Urbano | Mogi das Cruzes e Suzano |
| Sousa Araujo | Mogi das Cruzes e interior de SP |
| Damebe | Mogi das Cruzes |
| Cury | São Paulo e Rio de Janeiro |
| Tenda | Diversas capitais |
| EZTEC | São Paulo, Guarulhos, Osasco e ABC |
| Econ | São Paulo e Guarulhos |
| Metrocasa | São Paulo |
| Vibra Residencial | São Paulo |

Cury e Sousa Araujo não respondem às coletas feitas pelos servidores do GitHub; os dados delas são atualizados quando a coleta roda localmente.

## Rodar localmente

Requer Python 3.12 ou mais novo.

```bash
pip install -r coleta/requirements.txt
python coleta/coletar.py
python -m http.server 8000 --directory site
```

Depois é só abrir http://localhost:8000. A primeira coleta demora mais, porque preenche os caches de localização (`geo_cache.json`), de arredores (`arredores_cache.json`) e as miniaturas.

## Estrutura

```
coleta/
  coletar.py           orquestra a coleta e detecta mudanças
  <incorporadora>.py   um coletor por fonte (coletar() e parse())
  geo.py               geocodificação e conferência de coordenadas
  arredores.py         estação e serviços próximos
  fotos.py             miniaturas das fotos
site/
  index.html           mapa, lista, filtros e painel de novidades
  transparencia.html   página "Sobre os dados"
  dados.json           empreendimentos (gerado)
  mudancas.json        histórico de mudanças, 180 dias (gerado)
  status.json          situação de cada fonte (gerado)
  fotos/               miniaturas (geradas)
.github/workflows/coleta.yml   coleta diária e publicação
```

## Tecnologias

Todas gratuitas e abertas: Python (httpx, BeautifulSoup e Pillow), Leaflet com Leaflet.markercluster, OpenStreetMap (mapa, Nominatim e Overpass), GitHub Actions e GitHub Pages.

## Limites

- A etapa da obra é a que a incorporadora informa no site dela.
- Alguns pinos são aproximados: ficam no ponto da rua quando nem a fonte nem o OpenStreetMap têm a posição do prédio.
- As distâncias até estações e serviços são em linha reta, não o caminho a pé.

## Direitos

© 2026 autores do NaPlanta. Todos os direitos reservados. O código está visível para fins acadêmicos e de transparência; uso, cópia ou redistribuição dependem de autorização dos autores.

Os dados de mapa são © colaboradores do [OpenStreetMap](https://www.openstreetmap.org/copyright) (ODbL). Nomes, informações e fotos dos empreendimentos pertencem às respectivas incorporadoras.
