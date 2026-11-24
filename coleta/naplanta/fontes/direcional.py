"""Direcional Engenharia (todo o pais): o sitemap que o robots.txt deles indica (/enterprise-sitemap.xml) lista os links
(a API do WordPress, usada ate 17/11/2026, passou a exigir login); a pagina de cada um (layout novo
de nov/2026) tem o nome (h1), a etapa (selo ao lado do nome) e o mapa embutido com o
endereco (!2s) e a posicao (!2d lng, !3d lat)."""
import re
from urllib.parse import unquote
from bs4 import BeautifulSoup
from naplanta.dominio.texto import cita_mcmv
from naplanta.infra import rede

BASE = 'https://www.direcional.com.br'
MAPA = re.compile(r'!2d(-?\d+\.\d+)!3d(-?\d+\.\d+)[^"]*?!2s([^!"]+)')
LUGAR = re.compile(r',\s*([^,]+?)\s*-\s*([A-Z]{2})(?:,\s*[\d-]+)?$')  # "..., Ribeirão Preto - SP, 14021-520"
ETAPAS = {'breve lançamento': 'Breve lançamento', 'lançamento': 'Lançamento', 'em obras': 'Em obras',
          'obras avançadas': 'Em obras', 'pronto para morar': 'Pronto para morar'}


def mapa(html):
    """(endereco, cidade, uf, lat, lng) do mapa embutido; nada quando o pino e a central de vendas ou sem endereco."""
    m = MAPA.search(html)
    if not m:
        return None, None, None, None, None
    end = unquote(m[3]).replace('+', ' ').strip()
    if re.search(r'central de vendas|stand|plant[aã]o', end, re.I) or not re.search(r'\d|,', end):
        return None, None, None, None, None
    lugar = LUGAR.search(end)
    return end, lugar[1] if lugar else None, lugar[2] if lugar else None, float(m[2]), float(m[1])


assert mapa('pb=!2d-47.7883621!3d-21.211835!2m3!1s0x9%3A0x6!2sAv.%20Guilhermina%2C%20146%20-%20City%2C%20Ribeir%C3%A3o'
            '%20Preto%20-%20SP%2C%2014021-520!5e0') == ('Av. Guilhermina, 146 - City, Ribeirão Preto - SP, 14021-520',
                                                       'Ribeirão Preto', 'SP', -21.211835, -47.7883621)
assert mapa('!2d-38.3!3d-12.9!2m3!2sCentral%20de%20Vendas%20Direcional!5e0') == (None,) * 5


def parse(url, html, nome):
    s = BeautifulSoup(html, 'html.parser')
    atual = s.select_one('.enterprise-introduction__status')
    etapa = ETAPAS.get(atual.get_text(strip=True).lower()) if atual else None
    if not etapa:
        return None
    endereco, cidade, uf, lat, lng = mapa(html)
    if lat is None:  # sem mapa do predio nao da para saber nem a cidade (a pagina so cita a central de vendas)
        return None
    foto = s.select_one('meta[property="og:image"]')
    return {
        'nome': nome,
        'construtora': 'Direcional',
        'etapa': etapa,
        'endereco': endereco,
        'cidade': cidade,
        'uf': uf,
        'lat': lat, 'lng': lng,
        'dorms': None,
        'm2': None,
        'texto': f'{nome} apartamentos',
        'imagem': foto['content'] if foto else None,
        'fonte': url,
        'mcmv': cita_mcmv(html),
    }


def links(xml):
    """Paginas de empreendimento citadas no sitemap."""
    return re.findall(rf'<loc>\s*({re.escape(BASE)}/empreendimentos/[^<\s]+)', xml)


assert links(f'<loc>{BASE}/encontre-seu-apartamento/</loc><loc>{BASE}/empreendimentos/x/</loc>') == [f'{BASE}/empreendimentos/x/']


def coletar():
    out = []
    with rede.cliente() as c:
        obras = links(c.get(f'{BASE}/enterprise-sitemap.xml').raise_for_status().text)
        if not obras:
            raise ValueError('sitemap sem empreendimentos (o site pode ter mudado)')
        for link in obras:
            r = c.get(link)
            nome = BeautifulSoup(r.text, 'html.parser').select_one('h1') if r.status_code == 200 else None
            if nome and (e := parse(link, r.text, nome.get_text(' ', strip=True))):
                out.append(e)
    return out
