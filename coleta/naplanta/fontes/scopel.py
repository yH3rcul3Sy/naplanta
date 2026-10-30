"""Scopel (loteamentos em Aruja, Mogi, Itaquaquecetuba, Guarulhos e interior): sitemap do WordPress; cada pagina traz a
cidade e a disponibilidade nas classes do <main> e, nas paginas novas, a etapa no topo ("EM OBRAS")."""
import re
from urllib.parse import unquote
from bs4 import BeautifulSoup
from naplanta.infra import rede

BASE = 'https://scopel.com.br'
# shortcut: o slug da cidade perde os acentos; cidades do sitemap em out/2026 (outra nova cai no titulo sem acento)
CIDADES = {'aracatuba': 'Araçatuba', 'aruja': 'Arujá', 'embu-guacu': 'Embu-Guaçu', 'jacarei': 'Jacareí', 'paulinia': 'Paulínia',
           'poa': 'Poá', 'santana-de-parnaiba': 'Santana de Parnaíba', 'sao-jose-do-rio-preto': 'São José do Rio Preto',
           'sao-roque': 'São Roque', 'sumare': 'Sumaré', 'taubate': 'Taubaté'}
MINUSCULAS = {'da', 'das', 'de', 'do', 'dos', 'e'}
LOTE = re.compile(r'lotes?\b[^.\d]{0,25}?(\d{2,4})\s*m²', re.I)  # "Lotes de até 467m²", "TAMANHO DOS LOTES 360m²"
ETAPA = re.compile(r'^\s*(breve lan[çc]amento|lan[çc]amento|.{0,20}obras)', re.I)


def cidade(slug):
    return CIDADES.get(slug) or ' '.join(p if p in MINUSCULAS else p.capitalize() for p in slug.split('-'))


def etapa(topo, breve):
    """A etapa do topo da pagina; sem ela (paginas antigas, de loteamentos ja entregues com lotes a venda), pronto."""
    m = ETAPA.match(topo)
    if m:
        t = m[1].lower()
        return 'Em obras' if 'obras' in t else 'Breve lançamento' if 'breve' in t else 'Lançamento'
    return 'Breve lançamento' if breve else 'Pronto para morar'


assert LOTE.findall('ÁREA TOTAL 697.434,00m² UNIDADES / LOTES 600 TAMANHO DOS LOTES 360m²') == ['360']
assert cidade('aruja') == 'Arujá' and cidade('mogi-das-cruzes') == 'Mogi das Cruzes'
assert [etapa('EM OBRAS RESERVA ARUÃ', False), etapa('Etapa Final de Obras ARUJÁ', True), etapa('Mogi das Cruzes Sobre', False),
        etapa('', True), etapa('Lançamento X', False)] == ['Em obras', 'Em obras', 'Pronto para morar', 'Breve lançamento', 'Lançamento']


def parse(url, html):
    s = BeautifulSoup(html, 'html.parser')
    main = s.select_one('main')
    classes = ' '.join(main.get('class', [])) if main else ''
    lugar = re.search(r'cidade_empreendimento-([a-z0-9-]+)', classes)
    if not lugar or 'nome_empreendimento-' not in classes:
        return None
    meta = lambda p: (s.select_one(f'meta[property="{p}"]') or {}).get('content') or ''
    nome = re.sub(r'\s*-\s*Scopel\s*$', '', meta('og:title') or (s.title.get_text() if s.title else '')).strip()
    topo = ' '.join(meta('og:description').split())
    m2 = [int(x) for x in LOTE.findall(topo)]
    # o mapa embutido busca pelo endereco ("Aruã Brisas, Av. das Américas - Mogi das Cruzes, SP") ou so pelo nome
    busca = re.search(r'maps/embed/v1/place\?[^"]*?q=([^&"]+)', html)
    endereco = unquote(busca[1]) if busca and '%2C' in busca[1] else None
    return {
        'nome': nome,
        'construtora': 'Scopel',
        # pagina antiga sem etapa no topo, mas com nova fase a venda ("lança agora sua terceira etapa": Ibirapitanga 3)
        'etapa': 'Lançamento' if re.search(r'(?i)lan[çc]a agora', s.get_text(' ')) and not ETAPA.match(topo)
        else etapa(topo, 'disponibilidade_empreendimento-breve-lancamento' in classes),
        'endereco': endereco,
        'cidade': cidade(lugar[1]),
        'uf': 'SP',
        'lat': None, 'lng': None,  # sem endereco, o geo procura o loteamento pelo nome
        'dorms': None,
        'm2': [min(m2), max(m2)] if m2 else None,
        'texto': f'{nome} loteamento',  # o site so tem loteamentos
        'imagem': meta('og:image') or None,
        'fonte': url,
        'mcmv': False,
    }


def coletar():
    out = []
    with rede.cliente() as c:
        xml = c.get(f'{BASE}/empreendimentos-sitemap.xml').text
        for url in sorted(set(re.findall(rf'<loc>({BASE}/empreendimentos/[^<]+)</loc>', xml))):
            r = c.get(url)
            # loteamento antigo ja entregue, com lotes de revenda: nao e lancamento na planta
            if r.status_code == 200 and (e := parse(url, r.text)) and e['etapa'] != 'Pronto para morar':
                out.append(e)
    return out
