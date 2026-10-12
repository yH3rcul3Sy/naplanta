"""J.Bianchi e BRI Empreendimentos (Mogi das Cruzes): a pagina /imoveis-a-venda/ lista os empreendimentos; cada pagina
abre com um banner (#hero) que traz etapa, "Bairro - Cidade", nome e a ficha curta."""
import re
from urllib.parse import unquote_plus
from bs4 import BeautifulSoup
from naplanta.dominio.texto import cita_mcmv
from naplanta.infra import rede

BASE = 'https://jbianchi.com.br'
ETAPAS = (('breve', 'Breve lançamento'), ('lançamento', 'Lançamento'), ('constru', 'Em obras'), ('obra', 'Em obras'),
          ('pronto', 'Pronto para morar'), ('entregue', 'Pronto para morar'))
# "Centro – Mogi das Cruzes" ou "a 6 min. do Centro de Mogi das Cruzes"
LUGAR = re.compile(r'^(?:(.+?)\s+[–-]\s+)?(?:.*\bde\s+)?([A-ZÀ-Ú][\wÀ-ú]*(?:\s+(?:das?|de|dos?|[A-ZÀ-Ú][\wÀ-ú]*))*)$')


def etapa(tag):
    t = tag.lower()
    return next((e for chave, e in ETAPAS if chave in t), None)


def lugar(texto):
    m = LUGAR.match(' '.join(texto.split()))
    return (m[1], m[2]) if m else (None, None)


assert [etapa(t) for t in ('Pronto!', 'Em construção', 'Obras em Andamento', 'Lançamento')] == \
       ['Pronto para morar', 'Em obras', 'Em obras', 'Lançamento']
assert lugar('Centro – Mogi das Cruzes') == ('Centro', 'Mogi das Cruzes')
assert lugar('Vila Oliveira - Mogi das Cruzes') == ('Vila Oliveira', 'Mogi das Cruzes')
assert lugar('a 6 min. do Centro de Mogi das Cruzes') == (None, 'Mogi das Cruzes')


def parse(url, html):
    s = BeautifulSoup(html, 'html.parser')
    hero = s.select_one('#hero')
    tag, local = hero and hero.select_one('.tag'), hero and hero.select_one('strong')
    if not (tag and local and (fase := etapa(tag.get_text()))):
        return None
    bairro, cidade = lugar(local.get_text(' '))
    nome = (s.title.get_text() if s.title else '').rsplit(' - ', 1)[0].strip()
    ficha = ' '.join(hero.get_text(' ').split())
    # a ficha do banner ("2 e 3 dormitórios", "de 53 a 70m²") e os titulos das plantas ("3 Dormitórios - 100,87 m²")
    plantas = ' | '.join([ficha] + [h.get_text(' ') for h in s.select('h3')])
    dorms = [int(x) for x in re.findall(r'(\d)(?=(?:\s*e\s*\d)*\s*dormit)', plantas, re.I)]
    m2 = [float(x.replace(',', '.')) for x in re.findall(r'(\d+(?:,\d+)?)(?=(?:\s*(?:a|e)\s*\d+(?:,\d+)?)*\s*m²)', plantas)]
    # o endereco do proprio predio (o das rotas as vezes e o do stand); street view do embed, quando houver, e o predio
    endereco = re.search(r'maps\.google\.com/\?q=([^"&]+)', html)
    rua = re.search(r'!1d(-\d+\.\d+)!2d(-\d+\.\d+)!3f', html)
    foto = re.search(r'min-width:\s*728px\)\s*\{\s*#hero\{\s*background-image:url\(([^)]+)\)', html)
    return {
        'nome': nome,
        'construtora': 'J.Bianchi',
        'etapa': fase,
        'endereco': unquote_plus(endereco[1]).strip() if endereco else None,
        'bairro': bairro,
        'cidade': cidade,
        'uf': 'SP',
        'lat': float(rua[1]) if rua else None, 'lng': float(rua[2]) if rua else None,
        'dorms': [min(dorms), max(dorms)] if dorms else None,
        'm2': [min(m2), max(m2)] if m2 else None,
        'texto': f'{nome} {ficha}',
        'imagem': foto[1] if foto else None,
        'fonte': url,
        'mcmv': cita_mcmv(html),
    }


def coletar():
    out = []
    with rede.cliente() as c:
        lista = c.get(f'{BASE}/imoveis-a-venda/').text
        for url in sorted({u.lower() for u in re.findall(r'href="(https://jbianchi\.com\.br/empreendimento/[^"#?]+/)"', lista, re.I)}):
            r = c.get(url)
            if r.status_code == 200 and (e := parse(url, r.text)):
                out.append(e)
    return out
