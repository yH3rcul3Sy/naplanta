"""NGN Engenharia (Suzano e Mogi das Cruzes): uma pagina por empreendimento (/ngn-<nome>/), linkada no menu da home.
A pagina traz o mapa (endereco em ?q= ou posicao em !2d/!3d), dormitorios e area. Nao ha etapa por extenso: so
entram as que se anunciam como lancamento (as outras sao condominios ja entregues)."""
import re
from urllib.parse import unquote
from bs4 import BeautifulSoup
from naplanta.dominio.texto import cita_mcmv
from naplanta.infra import rede

BASE = 'https://ngnengenharia.com.br'
POSICAO = re.compile(r'!2d(-4\d\.\d+)!3d(-2\d\.\d+)')  # embed do Google Maps: !2d<lng>!3d<lat>
ENDERECO = re.compile(r'maps\?q=([^&"\']+)')


def parse(url, html):
    s = BeautifulSoup(html, 'html.parser')
    titulo = s.title.get_text() if s.title else ''
    nome = re.split(r'\s+[|–-]\s+', titulo)[0].strip()
    for t in s(['script', 'style', 'svg', 'header', 'footer', 'nav']):
        t.decompose()
    texto = ' '.join(s.get_text(' ').split())
    if not nome or not re.search(r'\blançamento\b', texto, re.I):
        return None
    pos, end = POSICAO.search(html), ENDERECO.search(html)
    end = unquote(end[1]).replace('&#038;', '&') if end else None
    dorms = [int(x) for x in re.findall(r'(\d)\s*dormit', texto, re.I)]
    m2 = [float(x.replace(',', '.')) for x in re.findall(r'(\d{2,3}(?:,\d+)?)\s*m²', texto, re.I)]
    return {
        'nome': nome,
        'construtora': 'NGN Engenharia',
        'etapa': 'Lançamento',
        'endereco': end,
        'cidade': 'Mogi das Cruzes' if 'Mogi das Cruzes' in f'{titulo} {end}' else 'Suzano',
        'uf': 'SP',
        'lat': float(pos[2]) if pos else None, 'lng': float(pos[1]) if pos else None,
        'dorms': [min(dorms), max(dorms)] if dorms else None,
        'm2': [min(m2), max(m2)] if m2 else None,
        'texto': f'{nome} {texto}',  # so serve para o tipo (o Premier e de casas)
        'imagem': None,  # o og:image e o logo da NGN
        'fonte': url,
        'mcmv': cita_mcmv(texto),
    }


def coletar():
    out = []
    with rede.cliente() as c:
        # o menu da home e o sitemap trazem listas diferentes (o Novo Horizonte so no menu, o Premier so no sitemap)
        paginas = c.get(BASE + '/').text + c.get(BASE + '/page-sitemap.xml').text
        for url in sorted({BASE + p for p in re.findall(r'(?:href="|\[)(?:https://ngnengenharia\.com\.br)?(/ngn-[a-z0-9-]+/)', paginas)}):
            r = c.get(url)
            if r.status_code == 200 and (e := parse(url, r.text)):
                out.append(e)
    return out
