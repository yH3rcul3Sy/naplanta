"""Ribeira Empreendimentos (Mogi das Cruzes): a pagina /empreendimentos/ tem um card por empreendimento (etapa, nome,
"CIDADE - UF", ficha curta e link); a pagina de cada um traz o endereco e as metragens."""
import re
from html import unescape
from bs4 import BeautifulSoup
from naplanta.dominio.texto import cita_mcmv
from naplanta.infra import rede

BASE = 'https://ribeira.com.br'
MINUSCULAS = {'da', 'das', 'de', 'do', 'dos', 'e'}
ENDERECO = re.compile(r'((?:Rua|R\.|Av\.|Avenida|Estrada|Alameda|Travessa)\s[^<>"]{3,80}?\d[^<>"]{0,60}?)\s*(?:–|-)\s*'
                      r'([A-ZÀ-Ú][^<>"–-]{2,40}?)\s*(?:–|-)\s*Mogi das Cruzes')


MAPA = re.compile(r'!2d(-?\d+\.\d+)!3d(-?\d+\.\d+)')  # embed do Google Maps: !2d<lng>!3d<lat>


def cidade(texto):  # "MOGI DAS CRUZES - SP" -> ("Mogi das Cruzes", "SP")
    nome, _, uf = texto.rpartition('-')
    return ' '.join(p if p in MINUSCULAS else p.capitalize() for p in nome.lower().split()), uf.strip() or None


assert cidade('SÃO JOSÉ DOS CAMPOS - SP') == ('São José dos Campos', 'SP')


def cards(html):
    """[(etapa, nome, local, ficha, link, foto)] da pagina de empreendimentos."""
    s = BeautifulSoup(html, 'html.parser')
    out = []
    for a in s.select('a[href]'):
        if 'saiba mais' not in a.get_text(' ').lower():
            continue
        card = a
        while card is not None and not (card.select_one('h3') and card.select_one('h6')):
            card = card.parent
        if card is None:
            continue
        texto = lambda sel: ' '.join(card.select_one(sel).get_text(' ').split()) if card.select_one(sel) else ''
        img = card.select_one('img[data-lazy-src], img[src^="http"]')
        foto = img.get('data-lazy-src') or img.get('src') if img else None
        out.append((texto('h6'), texto('h3'), texto('h5'), texto('.elementor-widget-text-editor'), a['href'], foto))
    return out


def parse(url, html, card):
    etapa, nome, local, ficha, _, foto = card
    municipio, uf = cidade(local)
    texto = unescape(html)
    end = ENDERECO.search(texto)
    mapa = MAPA.search(html)
    m2 = [float(x.replace('.', '').replace(',', '.')) for x in re.findall(r'(?<![\d.])(\d{2,3}(?:,\d+)?)\s*m²', texto)]
    m2 = [x for x in m2 if 20 <= x <= 400]  # tira terreno e areas de lazer
    dorms = [int(x) for x in re.findall(r'(\d)\s*(?=(?:\s*(?:e|a)\s*\d)*\s*(?:dormit|su[íi]te))', ficha, re.I)]
    return {
        'nome': nome,
        'construtora': 'Ribeira',
        'etapa': etapa,
        'endereco': f'{end[1].strip()}, {end[2].strip()}, {municipio} - {uf}' if end else None,
        'cidade': municipio,
        'uf': uf,
        'lat': float(mapa[2]) if mapa else None, 'lng': float(mapa[1]) if mapa else None,
        'dorms': [min(dorms), max(dorms)] if dorms else None,
        'm2': [min(m2), max(m2)] if m2 else None,
        'texto': f'{nome} {ficha} apartamentos',
        'imagem': foto,
        'fonte': url,
        'mcmv': cita_mcmv(html),
    }


def coletar():
    out = []
    with rede.cliente() as c:
        for card in cards(c.get(f'{BASE}/empreendimentos/').text):
            url = card[4]
            if not url.startswith(BASE + '/'):
                continue
            r = c.get(url)
            if r.status_code == 200:
                out.append(parse(url, r.text, card))
    return out
