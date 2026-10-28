"""HM Engenharia (MCMV no interior de SP, capital, Mogi, Extrema-MG): o sitemap lista /imoveis/<slug> e cada pagina
traz um JSON-LD ApartmentComplex com nome, endereco, status da obra, dormitorios, area e disponibilidade."""
import json, re
from naplanta.dominio.texto import cita_mcmv
from naplanta.infra import rede

BASE = 'https://eme.maishm.com.br'


def ficha(html):
    """O bloco JSON-LD do empreendimento, ou None (paginas antigas trazem outro formato e ficam de fora)."""
    for bloco in re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S):
        d = json.loads(bloco)
        if d.get('@type') == 'ApartmentComplex':
            return d
    return None


def parse(url, html):
    d = ficha(html)
    # esgotado sai do mapa, como o "100% vendido" das outras fontes
    if not d or d.get('offers', {}).get('availability', '').endswith('SoldOut'):
        return None
    end, prop = d.get('address', {}), {p['name']: p['value'] for p in d.get('additionalProperty', [])}
    quartos, area = d.get('numberOfRooms'), d.get('floorSize', {}).get('value')
    return {
        'nome': ' '.join(d['name'].split()),
        'construtora': 'HM Engenharia',
        'etapa': prop.get('Status da obra'),
        'endereco': end.get('streetAddress'),
        'cidade': re.sub(r'^Sta\. ', 'Santa ', end.get('addressLocality') or '') or None,
        'uf': end.get('addressRegion'),
        'lat': None, 'lng': None,
        'dorms': [quartos, quartos] if isinstance(quartos, int) and quartos > 0 else None,
        'm2': [area, area] if isinstance(area, (int, float)) and area >= 15 else None,  # ha pagina com "2" no lugar da area
        'texto': f"{d['name']} apartamentos",
        'imagem': d.get('image'),
        'fonte': url,
        'mcmv': cita_mcmv(html),
    }


def coletar():
    out = []
    with rede.cliente() as c:
        for url in sorted(set(re.findall(rf'<loc>({BASE}/imoveis/[a-z0-9-]+)</loc>', c.get(f'{BASE}/sitemap.xml').text))):
            r = c.get(url)
            if r.status_code == 200 and (e := parse(url, r.text)):
                out.append(e)
    return out
