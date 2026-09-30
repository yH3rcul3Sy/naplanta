import json, re, time
import httpx
from econ import rsc
from eztec import dorms

BASE = 'https://www.metrocasa.com.br'
UA = {'User-Agent': 'NaPlantaBot/0.1 (projeto academico UMC)'}
ETAPA = {'coming_soon': 'Breve lançamento', 'pre_launch': 'Breve lançamento', 'launch': 'Lançamento',
         'under_construction': 'Em obras', 'ready_to_move_in': 'Pronto para morar'}


def parse(url, html):
    p = rsc(html)
    i = p.find('"initialProperty":')
    if i < 0:
        return None
    e = json.JSONDecoder().raw_decode(p, i + len('"initialProperty":'))[0]
    a, plantas = e.get('address') or {}, e.get('plans') or []
    areas = [float(x.replace(',', '.')) for pl in plantas for x in re.findall(r'[\d,]+(?=\s*m²)', pl.get('area') or '')]
    return {
        'nome': 'Metrocasa ' + e['title'],
        'construtora': 'Metrocasa',
        'etapa': ETAPA.get(e.get('projectStatus')),
        'endereco': ', '.join(filter(None, [a.get('street'), a.get('number'), a.get('neighborhood'), a.get('city')])),
        'cidade': a.get('city') or 'São Paulo', 'uf': a.get('state') or 'SP',  # a Metrocasa so constroi na capital
        'lat': a.get('latitude'), 'lng': a.get('longitude'),
        'dorms': dorms(' '.join(pl.get('name') or '' for pl in plantas)),
        'm2': [min(areas), max(areas)] if areas else None,
        'texto': f"{e['title']} {(e.get('technicalSheet') or {}).get('typology') or ''}",
        'imagem': f"{BASE}/facades/{e['slug']}.webp",  # as chaves de 'facades'/'gallery' dao 404 no CDN; o card do site usa esta
        'fonte': url,
    }


def coletar():
    out = []
    with httpx.Client(headers=UA, timeout=30, follow_redirects=True) as c:
        xml = c.get(f'{BASE}/sitemap.xml').text
        for url in sorted(set(re.findall(rf'{BASE}/imoveis/[a-z0-9-]+(?=<|\s)', xml))):
            time.sleep(1)
            r = c.get(url)
            if r.status_code == 200 and (e := parse(url, r.text)):
                out.append(e)
    return out
