import re
from bs4 import BeautifulSoup
from naplanta.dominio.texto import cita_mcmv
from naplanta.infra import rede

BASE = 'https://cury.net'
# o endereco termina em "Bairro. Cidade - UF", mas fora da capital vem "Cidade. Estado - UF" ("Mogi das Cruzes. São Paulo - SP")
ESTADOS = {'SP': 'São Paulo', 'RJ': 'Rio de Janeiro'}
# shortcut: municipios das regioes metropolitanas onde a Cury atua (out/2026); outro novo cai como capital e o geo nao acha
MUNICIPIOS = {'Mogi das Cruzes', 'Suzano', 'Itaquá', 'Itaquaquecetuba', 'Poá', 'Ferraz de Vasconcelos', 'Arujá', 'Guarulhos',
              'Osasco', 'Barueri', 'Carapicuíba', 'Cotia', 'Taboão da Serra', 'Santo André', 'São Bernardo do Campo', 'Diadema',
              'Mauá', 'São Caetano do Sul', 'Nova Iguaçu', 'São Gonçalo', 'Belford Roxo', 'Duque de Caxias',
              'São João de Meriti', 'Nilópolis', 'Mesquita', 'Queimados', 'Niterói', 'Maricá', 'Itaboraí'}
APELIDOS = {'Itaquá': 'Itaquaquecetuba'}
LUGAR = re.compile(r'([^,.]+)\.\s*([^,.]+?)\s*-\s*([A-Z]{2})\s*$')


def lugar(endereco):
    """(cidade, uf) do fim do endereco; None se o formato for outro (o geo tenta pelo endereco)."""
    m = LUGAR.search(endereco or '')
    if not m:
        return None, None
    antes, depois, uf = m[1].strip(), m[2].strip(), m[3]
    cidade = antes if depois == ESTADOS.get(uf) and antes in MUNICIPIOS else depois
    return APELIDOS.get(cidade, cidade), uf


assert lugar('Av. Francisco Rodrigues Filho, 2002, Mogi das Cruzes. São Paulo - SP') == ('Mogi das Cruzes', 'SP')
assert lugar('Rua Guariri, 355, Itaquá. São Paulo - SP') == ('Itaquaquecetuba', 'SP')
assert lugar('Rua X, 10, Barra Funda. São Paulo - SP') == ('São Paulo', 'SP')
assert lugar('Rua Y, S/N, Centro. Niterói - RJ') == ('Niterói', 'RJ')
assert lugar('Rua Z, 1, Santa Cruz, Rio de Janeiro') == (None, None)


def parse(url, html):
    s = BeautifulSoup(html, 'html.parser')
    nome = s.select_one('.name-imovel')
    if not nome:
        return None
    etapa = s.select_one('.tag-house p')
    end = s.select_one('.box-location h4')
    cidade, uf = lugar(end.get_text(' ', strip=True) if end else None)
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
        'cidade': cidade, 'uf': uf,
        'lat': lat, 'lng': lng,
        'dorms': [min(dorms), max(dorms)] if dorms else None,
        'm2': None,
        'plantas': [],
        'texto': sobre,
        'imagem': img[0] if img else None,
        'fonte': url,
        'mcmv': cita_mcmv(html),
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
