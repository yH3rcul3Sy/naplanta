import json, re
import rede

BASE = 'https://econconstrutora.com.br'
ETAPA = {'futuro-lancamento': 'Breve lançamento', 'breve-lancamento': 'Breve lançamento', 'lancamento': 'Lançamento',
         'em-construcao': 'Em obras', 'pronto-para-morar': 'Pronto para morar'}


def rsc(html):
    """Junta o payload que o Next.js manda em pedacos (self.__next_f.push)."""
    return ''.join(json.loads(f'"{x}"') for x in re.findall(r'self\.__next_f\.push\(\[1,"(.*?)"\]\)', html, re.S))


def parse(url, html):
    p = rsc(html)
    i = p.find('"initialEmpreendimento":')
    if i < 0:
        return None
    e = json.JSONDecoder().raw_decode(p, i + len('"initialEmpreendimento":'))[0]
    if e.get('categoria') == 'pronto-para-morar' and not e.get('quantidade_estoque'):
        return None  # pronto e sem estoque = esgotado (em obras o estoque vem zerado mesmo a venda, entao so vale aqui)
    loc, metros, quartos = e.get('localizacao') or {}, [m['metros'] for m in e.get('metragem') or []], [q['qtde'] for q in e.get('quartos') or []]
    zona = loc.get('zona') or ''
    # na capital a Econ informa a zona; em "Grande São Paulo" a cidade e o fim do endereco ("..., 160 - Guarulhos")
    fim = re.split(r'\s[-–]\s|,', loc.get('endereco_empreendimento') or '')[-1].strip()
    cidade = 'São Paulo' if re.match(r'(?i)zona|centro', zona) else (fim or None) if 'grande' in zona.lower() else zona or None
    return {
        'nome': e['titulo'],
        'construtora': 'Econ',
        'etapa': ETAPA.get(e.get('categoria')),
        'endereco': ', '.join(filter(None, [loc.get('endereco'), loc.get('bairro'), cidade])),
        'cidade': cidade, 'uf': 'SP',
        'lat': loc.get('latitude'), 'lng': loc.get('longitude'),
        'dorms': [min(quartos), max(quartos)] if quartos else None,
        'm2': [min(metros), max(metros)] if metros else None,
        'entrega': str(e['ano_obra']) if e.get('ano_obra') else None,
        'texto': f"{e['titulo']} apartamentos",
        'imagem': (e.get('new_thumb') or (e.get('fotos') or [{}])[0].get('path')),
        'fonte': url,
    }


def coletar():
    out = []
    with rede.cliente() as c:
        xml = c.get(f'{BASE}/sitemap.xml').text
        for url in sorted(set(re.findall(rf'{BASE}/imovel/[a-z0-9-]+/[a-z0-9-]+(?=<|\s)', xml))):
            r = c.get(url)
            if r.status_code == 200 and (e := parse(url, r.text)):
                out.append(e)
    return out
