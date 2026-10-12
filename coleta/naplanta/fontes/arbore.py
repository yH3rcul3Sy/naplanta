"""Arbore Engenharia (Suzano, Grande SP e interior): sitemap do WordPress; cada pagina traz etapa, nome, cidade e
endereco nos titulos do Elementor, nessa ordem."""
import re
from bs4 import BeautifulSoup
from naplanta.dominio.texto import cita_mcmv
from naplanta.infra import rede

BASE = 'https://arboreengenharia.com.br'
ETAPA = {'breve lançamento': 'Breve lançamento', 'lançamento': 'Lançamento', 'em obras': 'Em obras', 'entregue': 'Pronto para morar'}
MINUSCULAS = {'da', 'das', 'de', 'do', 'dos', 'e'}
# shortcut: bairros que o site escreve no lugar da cidade (out/2026); se aparecer outro, o pino fica sem cidade certa e vale incluir aqui
BAIRRO_CIDADE = {'Granja Viana': ('Cotia', 'SP'), 'Jabaquara': ('São Paulo', 'SP'), 'Jaraguá': ('São Paulo', 'SP'), 'Muro Alto': ('Ipojuca', 'PE')}
LUGAR = re.compile(r'\s*([^,\-–/]+?)\s*[-/]\s*([A-Z]{2})\s*$')  # "..., Cotia - SP" -> (Cotia, SP)


def cidade(texto):  # o site escreve "São paulo"
    return ' '.join(p if p in MINUSCULAS else p[:1].upper() + p[1:] for p in texto.lower().split())


assert cidade('São paulo') == 'São Paulo' and cidade('MOGI DAS CRUZES') == 'Mogi das Cruzes'
assert [LUGAR.search(b).groups() for b in ['Bairro do Raffo - Suzano / SP', 'São do Ó, Ipojuca - PE']] == \
       [('Suzano', 'SP'), ('Ipojuca', 'PE')]


def parse(url, html):
    s = BeautifulSoup(html, 'html.parser')
    titulos = [' '.join(h.get_text(' ').split()) for h in s.select('.elementor-heading-title')]
    if len(titulos) < 3 or titulos[0].lower() not in ETAPA:
        return None
    i = titulos.index('Imóvel') if 'Imóvel' in titulos else None
    rua, bairro = (titulos[i + 1:i + 3] + ['', ''])[:2] if i is not None else ('', '')
    # o 3o titulo as vezes e bairro ou regiao ("Granja Viana", "Muro Alto"); a cidade certa e a do endereco ("..., Cotia - SP")
    lugar = LUGAR.search(bairro)
    municipio, uf = cidade(lugar[1] if lugar else titulos[2]), lugar[2] if lugar else None
    municipio, uf = BAIRRO_CIDADE.get(municipio, (municipio, uf))
    dorms = [int(x) for x in re.findall(r'(\d)\s*Dormit', html)]
    fotos = [u for u in dict.fromkeys(re.findall(rf'{BASE}/wp-content/uploads/[^"\s\']+?\.(?:jpe?g|webp|png)', html))
             if not re.search(r'favicon|logo|icon|selo|mobile|-mb\.|-\d+x\d+\.', u)]
    descricao = s.find('meta', attrs={'name': 'description'})
    return {
        'nome': titulos[1],
        'construtora': 'Árbore',
        'etapa': ETAPA[titulos[0].lower()],
        'endereco': ', '.join(filter(None, [rua, bairro])) or None,
        'cidade': municipio,
        'uf': uf,
        'lat': None, 'lng': None,  # o mapa da pagina aponta o decorado; o geo localiza pelo endereco
        'dorms': [min(dorms), max(dorms)] if dorms else None,
        'm2': None,
        'texto': ' '.join([titulos[1], descricao.get('content', '') if descricao else '', 'apartamentos']),
        'imagem': fotos[0] if fotos else None,
        'fonte': url,
        'mcmv': cita_mcmv(html),
    }


def coletar():
    out = []
    with rede.cliente() as c:
        xml = c.get(f'{BASE}/wp-sitemap-posts-empreendimentos-1.xml').text
        for url in sorted(set(re.findall(rf'<loc>({BASE}/empreendimentos/[^<]+)</loc>', xml))):
            r = c.get(url)
            if r.status_code == 200 and (e := parse(url, r.text)):
                out.append(e)
    return out
