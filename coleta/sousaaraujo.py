import re
from bs4 import BeautifulSoup
from geo import geohash
import rede

BASE = 'https://sousaaraujo.com.br'


def parse(url, html):
    s = BeautifulSoup(html, 'html.parser')
    h1, etapa = s.find('h1'), s.select_one('span.badge')
    if not h1:
        return None
    lat = lng = None
    if m := re.search(r'waze\.com/ul/h(\w+)', html):
        lat, lng = geohash(m[1])
    elif m := re.search(r'waze\.com/ul\?ll=(-?[\d.]+)%2C(-?[\d.]+)', html):
        lat, lng = float(m[1]), float(m[2])
    local = re.search(r' em (.+?) - ([A-Z]{2})$', h1.find_next('h2').get_text(strip=True)) if h1.find_next('h2') else None
    topo = ' '.join(p.get_text(' ', strip=True) for p in h1.find_next_siblings())
    m2 = [float(x.replace(',', '.')) for x in re.findall(r'([\d,]+)\s*m²', topo)]
    dorms = [int(x) for g in re.findall(r'((?:\d+\s*(?:,|e|ou)\s*)*\d+)\s*dorm', topo, re.I) for x in re.findall(r'\d+', g)]
    img = re.search(r'https://cdnm\.com\.br/sousaaraujo/media/[^"\s]+?\.jpe?g', html)
    texto = ' '.join(s.get_text(' ').split())
    end = re.search(r'((?:Av\.|Avenida|Rua|R\.|Estrada|Alameda|Rodovia)\s[^|]{5,120}?)\s+Google Maps', texto)  # "Av. X, 1545 - Bairro, Cidade - SP Google Maps"
    return {
        'nome': h1.get_text(strip=True).title(),
        'construtora': 'Sousa Araujo',
        'etapa': etapa.get_text(strip=True) if etapa else None,
        'endereco': end[1].strip(' -') if end else None,
        'cidade': local[1] if local else None, 'uf': local[2] if local else None,
        'lat': lat, 'lng': lng,
        'dorms': [min(dorms), max(dorms)] if dorms else None,
        'm2': [min(m2), max(m2)] if m2 else None,
        'texto': topo,
        'imagem': img[0] if img else None,
        'fonte': url,
    }


def coletar():
    out, urls = [], set()
    with rede.cliente() as c:
        for pagina in range(1, 20):  # listagem paginada; para quando uma pagina nao traz nada novo
            html = c.get(f'{BASE}/empreendimentos', params={'page': pagina}).text
            novas = set(re.findall(rf'{BASE}/empreendimentos/[a-z0-9-]+(?=")', html)) - urls
            if not novas:
                break
            urls |= novas
        for url in sorted(urls):
            r = c.get(url)
            if r.status_code == 200 and (e := parse(url, r.text)):
                out.append(e)
    return out
