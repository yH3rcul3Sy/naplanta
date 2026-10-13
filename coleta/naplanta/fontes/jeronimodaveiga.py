"""Jeronimo da Veiga (Poa, Taboao da Serra e Grande Rio): a pagina /empreendimentos/ traz um card por empreendimento com
nome, cidade, UF, etapa, quartos e MCMV em atributos data-*. So os lancamentos entram: os "prontos" sao o portfolio
da empresa, com obras de decadas atras e ja vendidas."""
import re
from bs4 import BeautifulSoup
from naplanta.dominio.texto import slug
from naplanta.infra import rede

BASE = 'https://jeronimodaveiga.com.br'
# shortcut: cards que trazem o bairro no lugar da cidade (out/2026)
CIDADE = {'Grajaú': 'Rio de Janeiro', 'Campo Grande': 'Rio de Janeiro'}


def parse(html):
    out = []
    for card in BeautifulSoup(html, 'html.parser').select('article.emp-card[data-nome]'):
        if card.get('data-status') != 'lancamento':
            continue
        nome = ' '.join(card['data-nome'].split())
        quartos = [int(x) for x in re.findall(r'\d', card.get('data-quartos', ''))]
        img = card.select_one('img[src]')
        out.append({
            'nome': nome,
            'construtora': 'Jeronimo da Veiga',
            'etapa': 'Lançamento',
            'endereco': None,
            'cidade': CIDADE.get(card.get('data-cidade'), card.get('data-cidade')),
            'uf': card.get('data-uf'),
            'lat': None, 'lng': None,
            'dorms': [min(quartos), max(quartos)] if quartos else None,
            'm2': None,
            'texto': f"{nome} {card.get('data-busca', '')} apartamentos" + (' casas' if 'casas' in nome.lower() else ''),
            'imagem': BASE + img['src'] if img and img['src'].startswith('/') else None,
            # cada lancamento tem site proprio, fora do dominio; a origem fica a pagina de empreendimentos
            'fonte': f'{BASE}/empreendimentos/#{slug(nome)}',
            'mcmv': 'mcmv' in card.get('data-programa', ''),
        })
    return out


MAPA = re.compile(r'!2d(-?\d+\.\d+)!3d(-?\d+\.\d+)')  # embed do Google Maps: !2d<lng>!3d<lat>


def sites(html):
    """{nome: site proprio do lancamento}; e la que fica o mapa com a posicao do predio."""
    return {' '.join(c['data-nome'].split()): c.select_one('a[href^="http"]')['href']
            for c in BeautifulSoup(html, 'html.parser').select('article.emp-card[data-nome]') if c.select_one('a[href^="http"]')}


def coletar():
    with rede.cliente() as c:
        html = c.get(f'{BASE}/empreendimentos/').raise_for_status().text
        out, links = parse(html), sites(html)
        for e in out:
            if (site := links.get(e['nome'])) and (r := c.get(site)).status_code == 200 and (m := MAPA.search(r.text)):
                e['lat'], e['lng'] = float(m[2]), float(m[1])
    return out
