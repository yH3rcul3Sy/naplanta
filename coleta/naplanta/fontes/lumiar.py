"""Construtora Lumiar (Zona Leste de SP, Mogi, Itaquaquecetuba e Suzano): a grade imoveis-grid.php?pagina=N tem um card
por imovel com nome, "Bairro, Cidade" (so o bairro quando e na capital), quartos, metragem e etapa."""
import re
from bs4 import BeautifulSoup
from naplanta.infra import rede

BASE = 'https://construtoralumiar.com.br'
ETAPAS = ('breve lançamento', 'lançamento', 'em obras', 'pronto para morar')


# shortcut: cidades da Grande SP onde a Lumiar atua (out/2026); o que nao for uma delas e bairro ou distrito da capital
MUNICIPIOS = ('Mogi das Cruzes', 'Itaquaquecetuba', 'Suzano', 'Poá', 'Ferraz de Vasconcelos', 'Guarulhos', 'Arujá')


MAPA = re.compile(r'!2d(-?\d+\.\d+)!3d(-?\d+\.\d+)')  # embed do Google Maps: !2d<lng>!3d<lat>


def lugar(texto, nome=''):
    """'Vila Nova Aparecida, Mogi das Cruzes' -> (bairro, cidade). Sem cidade conhecida no fim, vale a do nome
    ("Renaissance Suzano") ou a capital ("Vila Taquari, Itaquera")."""
    bairro, _, fim = texto.rpartition(',')
    if bairro and fim.strip() in MUNICIPIOS:
        return bairro.strip(), fim.strip()
    return texto.strip(), next((m for m in MUNICIPIOS if m in nome), 'São Paulo')


assert lugar('Vila Miranda, Itaquaquecetuba') == ('Vila Miranda', 'Itaquaquecetuba')
assert lugar('Vila Taquari, Itaquera') == ('Vila Taquari, Itaquera', 'São Paulo')
assert lugar('Chácara Faggion', 'Renaissance Suzano Condomínio Clube') == ('Chácara Faggion', 'Suzano')


def parse(html):
    out = []
    for card in BeautifulSoup(html, 'html.parser').select('article.lumiar-property-card'):
        titulo, local = card.select_one('.lumiar-property-card__title a'), card.select_one('.lumiar-property-card__location span')
        if not (titulo and local):
            continue
        meta = [' '.join(m.get_text(' ').split()) for m in card.select('.lumiar-property-card__meta-item')]
        etapa = next((m for m in meta if m.lower() in ETAPAS), None)  # locacao e "vendido" ficam sem etapa e saem
        ficha = ' '.join(meta)
        nome = ' '.join(titulo.get_text(' ').split())
        if not etapa or re.search(r'\boffice\b|sala comercial', nome + ficha, re.I):  # sala comercial nao e moradia
            continue
        bairro, cidade = lugar(' '.join(local.get_text(' ').split()), nome)
        dorms = [int(x) for x in re.findall(r'(\d)(?=(?:\s*(?:e|a)\s*\d)*\s*quartos?)', ficha)]
        m2 = [int(x) for x in re.findall(r'(\d{2,3})\s*(?=(?:a\s*\d{2,3}\s*)?m²)', ficha)]
        img = card.select_one('img[src]')
        out.append({
            'nome': nome,
            'construtora': 'Lumiar',
            'etapa': etapa,
            'endereco': f'{nome}, {bairro}',  # o geo usa o bairro quando nao acha o predio pelo nome
            'cidade': cidade,
            'uf': 'SP',
            'lat': None, 'lng': None,
            'dorms': [min(dorms), max(dorms)] if dorms else None,
            'm2': [min(m2), max(m2)] if m2 else None,
            'texto': f'{nome} {ficha}' + (' casas' if re.search(r'sobrado|casa', ficha, re.I) else ''),
            'imagem': BASE + img['src'] if img and img['src'].startswith('/') else (img['src'] if img else None),
            'fonte': f"{BASE}/{titulo['href'].lstrip('/')}",
            'mcmv': False,
        })
    return out


def coletar():
    out, vistos = [], set()
    with rede.cliente() as c:
        for pagina in range(1, 20):
            novos = [e for e in parse(c.get(f'{BASE}/imoveis-grid.php', params={'pagina': pagina}).text) if e['fonte'] not in vistos]
            if not novos:
                break
            vistos |= {e['fonte'] for e in novos}
            out += novos
        for e in out:
            # o bairro do card engana ("Vila da Prata" existe em Sao Paulo e em Mogi); o mapa da pagina nao.
            # Sem cidade, o geo tira a cidade da propria posicao.
            if (r := c.get(e['fonte'])).status_code == 200 and (m := MAPA.search(r.text)):
                e['lat'], e['lng'], e['cidade'], e['uf'] = float(m[2]), float(m[1]), None, None
    return out
