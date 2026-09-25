import re, time
from urllib.parse import unquote
import httpx
from bs4 import BeautifulSoup

BASE = 'https://integraurbano.com.br'
UA = {'User-Agent': 'NaPlantaBot/0.1 (projeto academico UMC)'}
LISTAS = {'breve-lancamento': 'Breve lançamento', 'lancamento': 'Lançamento', 'em-obras': 'Em obras'}


def parse(url, html, etapa):
    s = BeautifulSoup(html, 'html.parser')
    og = {m['property']: m.get('content') for m in s.find_all('meta', property=re.compile('^og:'))}
    if not og.get('og:title'):
        return None
    lat = lng = None
    if m := re.search(r'(-2\d\.\d{4,}),\s*(-[45]\d\.\d{4,})', html):
        lat, lng = float(m[1]), float(m[2])
    mapa = s.find('a', href=re.compile(r'google\.com/maps/place/'))
    end = unquote(mapa['href'].split('/place/')[1].split('/')[0]).replace('+', ' ') if mapa else None
    texto = ' '.join(s.get_text(' ').split())
    m2 = re.search(r'([\d,]+)\s*(?:a\s*([\d,]+)\s*)?m²\s*[\d,e ]+dorms', texto)
    dorms = re.search(r'((?:\d+\s*(?:,|e)\s*)*\d+)\s*dorms', texto)
    entrega = re.search(r'Previsão de Entrega\s*(\d{4})', texto)
    return {
        'nome': og['og:title'],
        'construtora': 'Integra Urbano',
        'etapa': etapa,
        'endereco': end,
        'lat': lat, 'lng': lng,
        'dorms': (lambda d: [min(d), max(d)])([int(x) for x in re.findall(r'\d+', dorms[1])]) if dorms else None,
        'm2': [float(m2[1].replace(',', '.')), float((m2[2] or m2[1]).replace(',', '.'))] if m2 else None,
        'entrega': entrega[1] if entrega else None,
        'texto': texto[:600],
        'imagem': og.get('og:image') or (img[0] if (img := re.search(rf'{BASE}/public/uploads/\w+\.(?:jpe?g|webp)', html)) else None),
        'fonte': url,
    }


def coletar():
    out = []
    with httpx.Client(headers=UA, timeout=30, follow_redirects=True) as c:
        for lista, etapa in LISTAS.items():
            html = c.get(f'{BASE}/empreendimentos/tipo/{lista}').text
            for url in sorted(set(re.findall(rf'{BASE}/empreendimento/[a-z0-9-]+', html))):
                time.sleep(1)
                r = c.get(url)
                if r.status_code == 200 and (e := parse(url, r.text, etapa)):
                    out.append(e)
    return out
