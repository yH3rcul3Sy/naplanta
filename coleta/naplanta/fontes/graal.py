"""Graal Engenharia (Zonas Leste e Norte de SP): a API do WordPress (/wp-json/wp/v2/obra) traz cada empreendimento com
etapa, bairro, textos de dormitorios e metragem, foto e selo do MCMV; a pagina de cada um tem o mapa embutido com a
posicao do predio."""
import re
from html import unescape
from naplanta.infra import rede

BASE = 'https://graalengenharia.com.br'
# "entregue" fica de fora: e o portfolio, com obras de anos atras ja vendidas
ETAPAS = {'futuro-lancamento': 'Breve lançamento', 'breve-lancamento': 'Breve lançamento', 'lancamento': 'Lançamento',
          'obras-em-andamento': 'Em obras'}
MINUSCULAS = {'da', 'das', 'de', 'do', 'dos', 'e'}


def titulo(texto):  # "BRISAS DA PRAÇA &#8211; PATRIARCA" -> "Brisas da Praça - Patriarca"
    texto = unescape(texto).replace('–', '-')
    return ' '.join(p if p in MINUSCULAS else p[:1].upper() + p[1:] for p in texto.lower().split())


assert titulo('BRISAS DA PRAÇA &#8211; PATRIARCA') == 'Brisas da Praça - Patriarca'


MAPA = re.compile(r'!2d(-4\d\.\d+)!3d(-2\d\.\d+)')  # embed do Google Maps: !2d<lng>!3d<lat>


def posicao(html):
    m = MAPA.search(html)
    return (float(m[2]), float(m[1])) if m else (None, None)


assert posicao('embed?pb=!1m18!2d-46.4538972!3d-23.5414127!2m3') == (-23.5414127, -46.4538972)


def parse(obras):
    out = []
    for o in obras:
        etapa = ETAPAS.get(o.get('statusSlug'))
        if not etapa:
            continue
        nome = titulo(o['title']['rendered'])
        acf = o.get('acf') or {}
        bairros = (o.get('cidadeBairro') or {}).get('bairro') or []
        bairro = unescape(bairros[0]['name']) if bairros else None
        dorms = [int(x) for x in re.findall(r'\d', acf.get('texto_dormitorios') or '')]
        m2 = [int(x) for x in re.findall(r'(\d{2,3})\s*m²', acf.get('texto_metragem') or '')]
        out.append({
            'nome': nome,
            'construtora': 'Graal',
            'etapa': etapa,
            'endereco': f'{nome}, {bairro}' if bairro else None,  # sem rua na API; o geo procura pelo nome e pelo bairro
            'cidade': 'São Paulo',  # so atua na capital (out/2026)
            'uf': 'SP',
            'lat': None, 'lng': None,
            'dorms': [min(dorms), max(dorms)] if dorms else None,
            'm2': [min(m2), max(m2)] if m2 else None,
            'texto': f'{nome} apartamentos',
            'imagem': o.get('thumbnail') or None,
            'fonte': o['link'],
            'mcmv': bool(o.get('programa')),
        })
    return out


def coletar():
    with rede.cliente() as c:
        out = parse(c.get(f'{BASE}/wp-json/wp/v2/obra', params={'per_page': 100}).raise_for_status().json())
        for e in out:
            r = c.get(e['fonte'])
            if r.status_code == 200:
                e['lat'], e['lng'] = posicao(r.text)
    return out
