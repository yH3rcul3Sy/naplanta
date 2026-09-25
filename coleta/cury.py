import re, time
import httpx
from bs4 import BeautifulSoup

BASE = 'https://cury.net'
UA = {'User-Agent': 'NaPlantaBot/0.1 (projeto academico UMC)'}


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


def coletar():
    out = []
    with httpx.Client(headers=UA, timeout=30, follow_redirects=True) as c:
        xml = c.get(f'{BASE}/sitemap.xml').text
        for url in sorted(set(re.findall(rf'<loc>({BASE}/imovel/[^<]+)</loc>', xml))):
            time.sleep(1)
            r = c.get(url)
            if r.status_code == 200 and (e := parse(url, r.text)):
                out.append(e)
    return out
