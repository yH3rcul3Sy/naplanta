import re
from urllib.parse import unquote
from bs4 import BeautifulSoup
import rede

BASE = 'https://www.damebe.com.br'
FORA = {'', 'quem-somos', 'contato', 'blog', 'politica-de-privacidade'}


def etapa(texto):
    # paginas sem campo de etapa: vale o termo mais avancado que aparecer
    t = texto.lower()
    if 'obras iniciadas' in t or 'em obras' in t:
        return 'Em obras'
    if 'entregue' in t:
        return 'Pronto para morar'
    if 'lançamento' in t:
        return 'Lançamento'


def parse(url, html):
    s = BeautifulSoup(html, 'html.parser')
    titulo = s.title.get_text(strip=True).split(' - ')[0] if s.title else None
    mapa = next((f['src'] for f in s.find_all('iframe') if 'maps' in (f.get('src') or '')), None)
    if not titulo or not mapa:
        return None
    for x in s(['script', 'style', 'svg', 'noscript']):
        x.decompose()
    texto = ' '.join(s.get_text(' ').split())
    m2 = re.search(r'(?i)área privativa\s*([\d.,]+)\s*m²', texto)
    dorms = re.search(r'(\d+)\s*e\s*(\d+)\s*dormit|(\d+)\s*dormit', texto)
    img = next((i['src'] for i in s.find_all('img', src=re.compile(r'/wp-content/uploads/.+\.(jpe?g|webp)$', re.I))
                if 'logo' not in i['src'].lower()), None)
    return {
        'nome': titulo,
        'construtora': 'Damebe',
        'etapa': etapa(texto),
        'endereco': unquote(re.search(r'[?&]q=([^&]+)', mapa)[1]),
        'cidade': 'Mogi das Cruzes', 'uf': 'SP',  # a Damebe so constroi em Mogi (e o endereco do Santorini nem cita a cidade)
        'lat': None, 'lng': None,  # geo.completar geocodifica pelo endereco
        'dorms': [int(dorms[1]), int(dorms[2])] if dorms and dorms[1] else [int(dorms[3])] * 2 if dorms else None,
        'm2': [float(m2[1].replace('.', '').replace(',', '.'))] * 2 if m2 else None,
        'texto': texto[:600],
        'imagem': img,
        'fonte': url,
    }


def coletar():
    out = []
    with rede.cliente() as c:
        xml = c.get(f'{BASE}/page-sitemap.xml').text
        for url in re.findall(r'<loc>([^<]+)</loc>', xml):
            if url.rstrip('/').rsplit('/', 1)[-1].replace('www.damebe.com.br', '') in FORA:
                continue
            r = c.get(url)
            if r.status_code == 200 and (e := parse(url, r.text)):
                out.append(e)
    return out
