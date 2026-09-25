import re, time
import httpx
from bs4 import BeautifulSoup
from geo import geohash

BASE = 'https://helbor.com.br'
UA = {'User-Agent': 'NaPlantaBot/0.1 (projeto academico UMC)'}


def links(c):
    xml = c.get(f'{BASE}/sitemap.xml').text
    return sorted(set(re.findall(rf'<loc>({BASE}/empreendimentos/[^<]+)</loc>', xml)))


def parse(url, html):
    s = BeautifulSoup(html, 'html.parser')
    h1 = s.find('h1')
    if not h1 or 'endereço' in h1.get_text():
        return None
    etapa = h1.find_previous('div', class_='p')
    lat = lng = None
    if waze := s.find('a', href=re.compile(r'ul\.waze\.com/ul\?.*ll=')):
        m = re.search(r'll=(-?[\d.]+)%2C(-?[\d.]+)', waze['href'])
        lat, lng = float(m[1]), float(m[2])
    elif waze := s.find('a', href=re.compile(r'waze\.com/ul/h\w+')):
        lat, lng = geohash(re.search(r'/ul/h(\w+)', waze['href'])[1])
    end = h1.find_next('div', class_='fw-light')
    topo = ' '.join([x.strip() for x in h1.find_all_next(string=True, limit=60) if x.strip()][1:8])
    plantas = sorted({a['title'] for a in s.find_all('a', title=re.compile(r'\d+\s*m²'))})
    m2 = [float(x.replace(',', '.')) for p in plantas or [topo] for x in re.findall(r'([\d,]+)\s*m²', p)]
    dorms = [int(x) for p in plantas for x in re.findall(r'(\d+)\s*dorm', p, re.I)]
    img = next((m[0] for pasta in ('image', 'description-image', 'galeria', 'differentials')
                if (m := re.search(rf'https://helbor\.com\.br/storage/media/development/{pasta}/[^"\s]+\.(?:jpe?g|png|webp)', html))), None)
    return {
        'nome': h1.get_text(strip=True),
        'construtora': 'Helbor',
        'etapa': etapa.get_text(strip=True) if etapa else None,
        'endereco': ' '.join(end.get_text().split()) if end else None,
        'lat': lat, 'lng': lng,
        'dorms': [min(dorms), max(dorms)] if dorms else None,
        'm2': [min(m2), max(m2)] if m2 else None,
        'plantas': plantas,
        'texto': topo,
        'imagem': img,
        'fonte': url,
    }


def coletar():
    out = []
    with httpx.Client(headers=UA, timeout=30, follow_redirects=True) as c:
        for url in links(c):
            time.sleep(1)  # educado com o servidor
            r = c.get(url)
            if r.status_code == 200 and (e := parse(url, r.text)):
                out.append(e)
    return out
