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


def coletar():
    with rede.cliente() as c:
        return parse(c.get(f'{BASE}/empreendimentos/').raise_for_status().text)
