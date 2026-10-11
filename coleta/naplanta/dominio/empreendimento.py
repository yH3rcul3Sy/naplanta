"""O que e um empreendimento valido: limpeza, validacao e padronizacao do que vem das fontes. Sem rede nem disco."""
import re, unicodedata

ETAPAS = {'breve lançamento': 'Breve lançamento', 'lançamento': 'Lançamento', 'em obras': 'Em obras',
          'obras avançadas': 'Em obras', 'em construção': 'Em obras', 'pronto para morar': 'Pronto para morar'}


def etapa(texto):
    """Etapa padronizada, ou None para "100% vendido" e etapas desconhecidas (que ficam de fora)."""
    return ETAPAS.get((texto or '').lower())


assert etapa('Obras Avançadas') == 'Em obras' and etapa('100% vendido') is None and etapa(None) is None


def tipo(texto):
    t = texto.lower()
    if re.search(r'\blote(s|amento)?\b', t):
        return 'Lote'
    if re.search(r'\bcasas\b|\bcasa (em|de) condom', t):
        return 'Casa em condomínio'
    return 'Apartamento'


assert tipo('Loteamento fechado de alto padrão') == 'Lote'
assert tipo('Casas em Condomínio Fechado de 2 e 3 dorms.') == 'Casa em condomínio'
assert tipo('Casa Piauí, studios de 30 m²') == 'Apartamento'

INVISIVEIS = re.compile(r'[​-‏⁠﻿]')


def limpo(e):
    """Texto das fontes vem com caractere invisivel e espaco sobrando ('Sao Paulo' + zero-width da Cury duplicava a cidade no filtro)."""
    for k, v in e.items():
        if isinstance(v, str):
            e[k] = ' '.join(unicodedata.normalize('NFC', INVISIVEIS.sub('', v)).split())
    return e


assert limpo({'cidade': 'São Paulo​', 'nome': ' Walk -  Guarulhos ', 'n': 2}) == {'cidade': 'São Paulo', 'nome': 'Walk - Guarulhos', 'n': 2}


def problemas(e, base):
    """Campos fora do formato que o site espera: o HTML das incorporadoras e entrada de terceiros."""
    num = lambda v: isinstance(v, (int, float)) and not isinstance(v, bool)
    faixa = lambda v: v is None or (isinstance(v, list) and len(v) == 2 and all(map(num, v)) and v[0] <= v[1])
    texto = lambda v: v is None or isinstance(v, str)
    regras = {'nome': lambda v: isinstance(v, str) and v.strip() != '',
              'fonte': lambda v: isinstance(v, str) and v.startswith(base + '/'),
              'lat': lambda v: v is None or (num(v) and -90 <= v <= 90),
              'lng': lambda v: v is None or (num(v) and -180 <= v <= 180),
              'dorms': faixa, 'm2': faixa,
              'imagem': lambda v: v is None or (isinstance(v, str) and v.startswith(('https://', 'http://'))),
              'etapa': texto, 'endereco': texto, 'cidade': texto, 'uf': texto, 'entrega': texto}
    ruins = [k for k, ok in regras.items() if not ok(e.get(k))]
    if (e.get('lat') is None) != (e.get('lng') is None):
        ruins += ['lat', 'lng']
    return sorted(set(ruins))


_ok = {'nome': 'A', 'fonte': 'https://x.com/a', 'lat': -23.5, 'lng': -46.2, 'dorms': [1, 3], 'm2': None, 'imagem': 'https://x.com/a.jpg'}
assert problemas(_ok, 'https://x.com') == []
assert problemas({**_ok, 'fonte': 'https://x.com.golpe.io/a'}, 'https://x.com') == ['fonte']
assert problemas({**_ok, 'm2': ['50', 70], 'imagem': 'javascript:alert(1)', 'lng': None}, 'https://x.com') == ['imagem', 'lat', 'lng', 'm2']
assert problemas({**_ok, 'dorms': [3, 1], 'nome': ' '}, 'https://x.com') == ['dorms', 'nome']
