"""GFR Empreendimentos (loteamentos em Mogi, Aruja, Campinas e interior): a pagina de projetos carrega os cards por
etapa em load_projetos.ashx?<etapa>=1; cada card traz nome, "Cidade, UF", descricao, foto e link."""
import re
from bs4 import BeautifulSoup
from naplanta.dominio.texto import slug
from naplanta.infra import rede

BASE = 'https://gfrempreendimentos.com.br'
# fica de fora "entregue": loteamentos antigos ja ocupados, sem endereco no card para por no mapa
ETAPAS = {'futuro': 'Breve lançamento', 'lancamento': 'Lançamento', 'obra': 'Em obras'}
MINUSCULAS = {'da', 'das', 'de', 'do', 'dos', 'e'}
# shortcut: o card as vezes traz o bairro planejado antes da cidade (out/2026); outro caso cai aqui
CIDADE = {'Swiss Park Campinas': 'Campinas'}


def titulo(texto):  # o site escreve "RESERVA ARUJÁ"
    return ' '.join(p if p in MINUSCULAS else p.upper() if re.fullmatch(r'[ivx]+|gfr', p) else p[:1].upper() + p[1:]
                    for p in texto.lower().split())


assert titulo('RESERVA ARUJÁ') == 'Reserva Arujá' and titulo('GFR MOGI DAS CRUZES') == 'GFR Mogi das Cruzes'
assert titulo('SWISS BOULEVARD CAMPINAS II') == 'Swiss Boulevard Campinas II'


def parse(html, etapa):
    out = []
    for card in BeautifulSoup(html, 'html.parser').select('.projeto-box'):
        nome, local = card.select_one('.projeto-nome'), card.select_one('.projeto-local')
        if not (nome and local) or 'office' in nome.get_text().lower():  # sala comercial nao e moradia
            continue
        cidade, _, uf = ' '.join(local.get_text(' ').split()).rpartition(',')
        cidade = CIDADE.get(cidade.strip(), cidade.strip())
        link, foto = card.select_one('a[href]'), card.select_one('img[src]')
        descricao = ' '.join(card.select_one('.projeto-extra').get_text(' ').split()) if card.select_one('.projeto-extra') else ''
        href = link['href'] if link else ''
        nome = titulo(nome.get_text(' ').strip())
        m2 = [int(x) for x in re.findall(r'(\d+)\s*m²', descricao)]
        out.append({
            'nome': nome,
            'construtora': 'GFR',
            'etapa': etapa,
            'endereco': None,
            'cidade': cidade,
            'uf': uf.strip() or None,
            'lat': None, 'lng': None,
            'dorms': None,
            'm2': [min(m2), max(m2)] if m2 else None,
            'texto': f'{nome} {descricao} loteamento',  # o site so tem loteamentos
            'imagem': foto['src'] if foto else None,
            # projetos com site proprio linkam para fora; a origem fica a pagina de projetos da GFR
            'fonte': BASE + href if href.startswith('/projeto/') else f'{BASE}/projetos#{slug(nome)}',
            'mcmv': False,
        })
    return out


def coletar():
    out = []
    with rede.cliente() as c:
        for chave, etapa in ETAPAS.items():
            out += parse(c.get(f'{BASE}/load_projetos.ashx', params={chave: 1}).raise_for_status().text, etapa)
    return out
