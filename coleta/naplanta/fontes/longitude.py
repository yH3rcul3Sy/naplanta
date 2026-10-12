"""Longitude (capital e interior de SP): /imoveis lista os links /imoveis/<cidade>/<tipo>/<slug> (nome no title);
a pagina de cada imovel traz a etapa (selo), a cidade (icone de local), o endereco ("Rua X, 1 <br/> Bairro, Cidade/UF") e as fotos."""
import re
from bs4 import BeautifulSoup
from naplanta.dominio.texto import cita_mcmv
from naplanta.infra import rede

BASE = 'https://www.longitude.com.br'
ETAPAS = {'futuro': 'Breve lançamento', 'futuro lançamento': 'Breve lançamento', 'breve lançamento': 'Breve lançamento',
          'lançamento': 'Lançamento', 'em construção': 'Em obras', 'em obras': 'Em obras', 'imóvel pronto': 'Pronto para morar'}
IMOVEL = re.compile(rf'{re.escape(BASE)}/imoveis/[a-z0-9-]+/(apartamento|casa|townhouse|loteamento)/[a-z0-9-]+')
ENDERECO = re.compile(r'((?:Rua|R\.|Av\.|Avenida|Estrada|Alameda|Rodovia)\s[^<]{3,80}?)\s*<br\s*/?>\s*([^,<]{2,40}?)\s*,'
                      r'\s*([^/<]{2,40})/([A-Z]{2})')


def parse(url, html, nome):
    s = BeautifulSoup(html, 'html.parser')
    selo = s.select_one('li.nav-item.bg-primary')
    etapa = ETAPAS.get(' '.join(selo.get_text(' ').split()).lower()) if selo else None
    if not etapa:
        return None
    local = s.select_one('li.nav-item .icon-location')
    cidade = ' '.join(local.parent.get_text(' ').split()) if local else None
    end = ENDERECO.search(html)
    texto = ' '.join(s.get_text(' ').split())
    dorms = [int(x) for x in re.findall(r'(\d)\s*dormit', texto, re.I)]
    foto = re.search(r'https://cdn\.longitude\.com\.br/[^"\s)]+\.jpe?g', html)
    tipo = IMOVEL.match(url)[1]
    return {
        'nome': nome,
        'construtora': 'Longitude',
        'etapa': etapa,
        'endereco': f'{end[1].strip()}, {end[2].strip()}, {end[3].strip()} - {end[4]}' if end else None,
        'bairro': end[2].strip() if end else None,
        'cidade': end[3].strip() if end else cidade,
        'uf': end[4] if end else 'SP',
        'lat': None, 'lng': None,
        'dorms': [min(dorms), max(dorms)] if dorms else None,
        'm2': None,
        'texto': f"{nome} {'loteamento' if tipo == 'loteamento' else 'casas' if tipo in ('casa', 'townhouse') else 'apartamentos'}",
        'imagem': foto[0] if foto else None,
        'fonte': url,
        'mcmv': cita_mcmv(html),
    }


def coletar():
    out = []
    with rede.cliente() as c:
        lista = BeautifulSoup(c.get(f'{BASE}/imoveis').text, 'html.parser')
        nomes = {a['href']: a['title'] for a in lista.select('a.stretched-link[href][title]') if IMOVEL.fullmatch(a['href'])}
        for url, nome in sorted(nomes.items()):
            r = c.get(url)
            if r.status_code == 200 and (e := parse(url, r.text, nome.strip())):
                out.append(e)
    return out
