import re, time
import httpx
from bs4 import BeautifulSoup

BASE = 'https://www.cacengenharia.com.br'
UA = {'User-Agent': 'NaPlantaBot/0.1 (projeto academico UMC)'}


def ficha(s, campo):
    for strong in s.find_all('strong'):
        if strong.get_text(strip=True).startswith(campo):
            txt = []
            for n in strong.next_siblings:
                if getattr(n, 'name', None) in ('strong', 'br') and txt:
                    break
                txt.append(n.get_text() if hasattr(n, 'get_text') else str(n))
            return ' '.join(''.join(txt).split()) or None


def parse(url, html):
    s = BeautifulSoup(html, 'html.parser')
    ban = s.find('section', id='banner_empreendimento')
    if not ban or not ban.find('h2'):
        return None
    cidade, uf = ban.find('span', class_=re.compile('^cidade_')), ban.find('span', class_=re.compile('^estado_'))
    etapa = ban.select_one('.status .box')
    lat = lng = None
    if mapa := s.find('iframe', src=re.compile(r'maps/embed.*!2d-?[\d.]+!3d-?[\d.]+')):
        m = re.search(r'!2d(-?[\d.]+)!3d(-?[\d.]+)', mapa['src'])
        lng, lat = float(m[1]), float(m[2])
    tipo = (ficha(s, 'Tipologia') or '').split('+')[0]
    m2 = [float(x.replace('.', '').replace(',', '.')) for x in re.findall(r'([\d.,]+)\s*m²', tipo)]
    grupos = re.findall(r'((?:\d+\s*(?:,|e|ou)\s*)*\d+)\s*(?:quarto|dorm)', tipo + ' ' + ban.get_text(' '), re.I)
    dorms = [int(x) for g in grupos for x in re.findall(r'\d+', g)]
    img = re.search(r'#banner_empreendimento\s*{\s*background-image:\s*url\(([^)]+)\)', html)
    return {
        'nome': ban.find('h2').get_text(strip=True),
        'construtora': 'C.A.C Engenharia',
        'etapa': etapa.get_text(strip=True) if etapa else None,
        'endereco': None,
        'cidade': cidade.get_text(strip=True) if cidade else None,
        'uf': uf.get_text(strip=True) if uf else None,
        'lat': lat, 'lng': lng,
        'dorms': [min(dorms), max(dorms)] if dorms else None,
        'm2': [min(m2), max(m2)] if m2 else None,
        'plantas': [tipo.strip()] if tipo.strip() else [],
        'entrega': ficha(s, 'Previsão de entrega'),
        'texto': f"{ficha(s, 'Produto') or ''} {ban.get_text(' ')}",
        'imagem': img[1] if img else None,
        'fonte': url,
    }


def coletar():
    out = []
    with httpx.Client(headers=UA, timeout=30, follow_redirects=True) as c:
        xml = c.get(f'{BASE}/empreendimento-sitemap.xml').text
        for url in re.findall(rf'<loc>({BASE}/empreendimento/[^<]+)</loc>', xml):
            time.sleep(1)
            r = c.get(url)
            if r.status_code == 200 and (e := parse(url, r.text)):
                out.append(e)
    return out
