import json, re
from econ import rsc
import rede

BASE = 'https://www.eztec.com.br'
ETAPA = {'breve_lancamento': 'Breve lançamento', 'lancamento': 'Lançamento', 'obras_iniciadas': 'Em obras',
         'obras_aceleradas': 'Em obras', 'pronto_para_morar': 'Pronto para morar', 'pronto': 'Pronto para morar'}  # 'vendido' fica de fora
CIDADES = {'São Caetano': 'São Caetano do Sul'}


def dorms(rotulo):
    n = [int(x) for x in re.findall(r'\d+', rotulo)] + ([1] if 'studio' in rotulo.lower() else [])
    return [min(n), max(n)] if n else None


assert dorms('Studios a 3 dorms.') == [1, 3] and dorms('2 e 3 suítes') == [2, 3] and dorms('') is None


def parse(e):
    cidade = CIDADES.get(e['cidadeLabel'], e['cidadeLabel'])
    c = e.get('coords') or {}
    return {
        'nome': e['nome'].strip(),
        'construtora': 'EZTEC',
        'etapa': ETAPA.get(e.get('statusSlug')),
        'endereco': ', '.join(dict.fromkeys(filter(None, [e.get('bairroLabel'), cidade]))),
        'cidade': cidade, 'uf': 'SP',
        'lat': c.get('lat'), 'lng': c.get('lng'),
        'dorms': dorms(e.get('dormsLabel') or ''),
        'm2': [e['areaMin'], e['areaMax']] if e.get('areaMin') else None,
        'texto': f"{e['nome']} {e.get('dormsLabel') or ''}",
        'imagem': e.get('image'),
        'fonte': BASE + e['href'],
    }


def coletar():
    # a pagina de imoveis ja traz a lista completa com etapa e coordenadas; nao precisa abrir um por um
    with rede.cliente() as c:
        html = c.get(f'{BASE}/imoveis').text
    p = rsc(html)
    lista = json.JSONDecoder().raw_decode(p, p.index('"empreendimentos":[') + len('"empreendimentos":'))[0]
    return [parse(e) for e in lista]
