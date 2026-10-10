import re
from bs4 import BeautifulSoup
import rede

BASE = 'https://cury.net'


def parse(url, html):
    s = BeautifulSoup(html, 'html.parser')
    nome = s.select_one('.name-imovel')
    if not nome:
        return None
    etapa = s.select_one('.tag-house p')
    end = s.select_one('.box-location h4')
    lat = lng = None
    if m := re.search(r'waze\.com/ul\?ll=(-?[\d.]+),(-?[\d.]+)', html):
        lat, lng = float(m[1]), float(m[2])
    sobre = ' '.join(p.get_text(' ', strip=True) for p in s.select('.about-imovel'))
    dorms = [int(x) for g in re.findall(r'((?:\d+\s*(?:,|e|ou)\s*)*\d+)\s*dorm', sobre, re.I) for x in re.findall(r'\d+', g)]
    img = re.search(r'https://cury\.net/storage/images_webp/products/gallery/[^"\s]+', html)
    return {
        'nome': nome.get_text(strip=True),
        'construtora': 'Cury',
        'etapa': etapa.get_text(strip=True) if etapa else None,
        'endereco': end.get_text(' ', strip=True) if end else None,
        'lat': lat, 'lng': lng,
        'dorms': [min(dorms), max(dorms)] if dorms else None,
        'm2': None,
        'plantas': [],
        'texto': sobre,
        'imagem': img[0] if img else None,
        'fonte': url,
    }


IMOVEL = re.compile(r'(?:https://cury\.net)?(/imovel/[A-Za-z]{2}/[a-z0-9-]+/[a-z0-9-]+)(?=["#?\s<])')


def coletar():
    # o sitemap so traz empreendimentos antigos (quase todos prontos); os lancamentos e obras aparecem na pagina
    # inicial e nos "imoveis relacionados" de cada pagina, entao a coleta segue esses links ate nao achar nenhum novo
    out = []
    with rede.cliente() as c:
        fila = {BASE + p for p in IMOVEL.findall(c.get(f'{BASE}/sitemap.xml').text + c.get(BASE).text)}
        vistos = set()
        while fila - vistos:
            url = min(fila - vistos)
            vistos.add(url)
            r = c.get(url)
            if r.status_code == 200:
                fila |= {BASE + p for p in IMOVEL.findall(r.text)}
                if e := parse(url, r.text):
                    out.append(e)
    return out
