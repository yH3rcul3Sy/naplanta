"""Grupo Lidera (Mogi das Cruzes, Sorocaba, Itu, Barueri, litoral): a lista /imoveis/ traz um card por empreendimento
com etapa, "Cidade | UF" e nome; a pagina de cada um traz o endereco, os dormitorios e as plantas com area.
O site e em ISO-8859-1."""
import re
from bs4 import BeautifulSoup
from naplanta.dominio.texto import cita_mcmv
from naplanta.infra import rede

BASE = 'https://www.grupolidera.com.br'
ETAPAS = {'breve lançamento': 'Breve lançamento', 'lançamento': 'Lançamento', 'obras': 'Em obras',
          'em obras': 'Em obras', 'entregue': 'Pronto para morar'}
CARD = re.compile(r'HREF="(/imoveis/[a-z0-9-]+/)".*?ALT="([^"]+)".*?<FONT[^>]*>([^<|]+)\|\s*([A-Z]{2})\s*</FONT><BR>([^<]+)</DIV>', re.S)
ENDERECO = re.compile(r'((?:Rua|R\.|Av\.|Avenida|Estrada|Alameda|Rodovia|Travessa)\s[^|]{3,90}?/[A-Z]{2})')


def cards(html):
    """(url, etapa, cidade, uf, nome) de cada card da lista, sem repetir."""
    vistos = {}
    for bloco in html.split('<DIV CLASS="home_imoveismain ')[1:]:
        if m := CARD.search(bloco):
            url, etapa, cidade, uf, nome = m.groups()
            vistos.setdefault(BASE + url, (BASE + url, ETAPAS.get(etapa.strip().lower()), cidade.strip(), uf, ' '.join(nome.split())))
    return list(vistos.values())


def parse(url, html, card):
    _, etapa, cidade, uf, nome = card
    s = BeautifulSoup(html, 'html.parser')
    for t in s(['script', 'style', 'svg']):
        t.decompose()
    texto = ' '.join(s.get_text(' ').split())
    corpo = texto.split('Escritório:')[0]  # o rodape traz o endereco da sede e dos plantoes
    end = ENDERECO.search(corpo)
    dorms = [int(x) for x in re.findall(r'(\d)(?=(?:\s*(?:e|ou|,)\s*\d)*\s*dorm)', corpo, re.I)]
    m2 = [v for x in re.findall(r'(\d{1,3}(?:,\d+)?)\s*m²', corpo) if (v := float(x.replace(',', '.'))) >= 18]  # tira varanda e terraco soltos
    slug = url.rstrip('/').rsplit('/', 1)[-1]
    return {
        'nome': nome,
        'construtora': 'Lidera',
        'etapa': etapa,
        'endereco': end[1] if end else None,
        'cidade': cidade,
        'uf': uf,
        'lat': None, 'lng': None,
        'dorms': [min(dorms), max(dorms)] if dorms else None,
        'm2': [min(m2), max(m2)] if m2 else None,
        'texto': f'{nome} {corpo[:300]}',
        'imagem': f'{BASE}/imoveis/imagens/imoveis_{slug}.jpg',
        'fonte': url,
        'mcmv': cita_mcmv(corpo),  # o rodape cita o MCMV em todas as paginas
    }


def coletar():
    out = []
    with rede.cliente() as c:
        lista = c.get(f'{BASE}/imoveis/')
        lista.encoding = 'iso-8859-1'
        for card in cards(lista.text):
            r = c.get(card[0])
            if r.status_code == 200:
                r.encoding = 'iso-8859-1'
                out.append(parse(card[0], r.text, card))
    return out
