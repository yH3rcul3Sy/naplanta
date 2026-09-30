import json, re, time
import httpx
from bs4 import BeautifulSoup

BASE = 'https://www.vibraresidencial.com.br'
UA = {'User-Agent': 'NaPlantaBot/0.1 (projeto academico UMC)'}
ETAPA = {'breve lançamento': 'Breve lançamento', 'lançamento': 'Lançamento', 'em obras': 'Em obras',
         'pronto': 'Pronto para morar', 'pronto para morar': 'Pronto para morar', 'entregue': 'Pronto para morar'}


def parse(url, html):
    s = BeautifulSoup(html, 'html.parser')
    g = next((n for j in s.find_all('script', type='application/ld+json') if 'ApartmentComplex' in (j.string or '')
              for n in json.loads(j.string).get('@graph', []) if n.get('@type') == 'ApartmentComplex'), None)
    if not g or not re.search(r'InStock|PreOrder', (g.get('offers') or {}).get('availability') or ''):  # SoldOut fica de fora
        return None
    prop = {p['name']: p['value'] for p in g.get('additionalProperty', [])}
    a, geo = g.get('address') or {}, g.get('geo') or {}
    # em algumas paginas o geo vem sem o ponto decimal (-23612313034762700); ai vale o link do mapa
    m = re.search(r'@(-\d+\.\d+),(-\d+\.\d+)', g.get('hasMap') or '')
    ll = (geo['latitude'], geo['longitude']) if abs(geo.get('latitude') or 99) < 90 else \
        (float(m[1]), float(m[2])) if m else (None, None)
    d = [int(x) for x in re.findall(r'\d+', prop.get('Dormitórios', ''))]
    cidade = (a.get('addressLocality') or 'São Paulo').split('/')[0]  # ora "São Paulo", ora "São Paulo/SP"
    for x in s(['script', 'style', 'svg', 'noscript']):
        x.decompose()
    texto = ' '.join(s.get_text(' ').split())
    areas = [float(x.replace(',', '.')) for x in re.findall(r'(\d{2,3}(?:,\d+)?)\s*m²', texto) if 15 <= float(x.replace(',', '.')) <= 300]
    return {
        'nome': g['name'].title(),
        'construtora': 'Vibra Residencial',
        'etapa': ETAPA.get(prop.get('Status do empreendimento', '').strip().lower()),
        'endereco': ', '.join(filter(None, [a.get('streetAddress'), prop.get('Bairro'), cidade])),
        'cidade': cidade, 'uf': 'SP',
        'lat': ll[0], 'lng': ll[1],
        'dorms': [min(d), max(d)] if d else None,
        'm2': [min(areas), max(areas)] if areas else None,
        'texto': f"{g['name']} apartamentos",
        'imagem': (g.get('image') or [{}])[0].get('url'),
        'fonte': url,
    }


def coletar():
    out = []
    with httpx.Client(headers=UA, timeout=30, follow_redirects=True) as c:
        html = c.get(f'{BASE}/produtos/').text
        for url in sorted(set(re.findall(rf'{BASE}/produtos/[a-z0-9-]+/', html))):
            time.sleep(1)
            r = c.get(url)
            if r.status_code == 200 and (e := parse(url, r.text)):
                out.append(e)
    return out
