"""Cadastro de lancamentos (naplanta.app.br/cadastro.html): incorporadoras e corretores preenchem um Google Forms;
o mantenedor confere e marca "aprovado" na planilha, e a aba "publico" (so os aprovados, sem os contatos) e publicada
em CSV. Entrada de terceiros: cada campo e conferido aqui e de novo em dominio.empreendimento.problemas.
fonte e o id no NaPlanta (BASE/<slug>); o link oficial do empreendimento vai em "link"."""
import csv, io, ipaddress, re
from urllib.parse import urlsplit
import httpx
from naplanta.config import UA_ROBO
from naplanta.dominio.texto import slug

BASE = 'https://naplanta.app.br/cadastro'
CSV = ('https://docs.google.com/spreadsheets/d/e/2PACX-1vRxvN8YAP8ytxuz8nTf7eakdpE7sXKOEIZ_NoYZuGLTUbHlkEEknDk9FxYyz_dL2rJ4i9sQ9J'
       'pFdbiO/pub?gid=1067202210&single=true&output=csv')
VAZIO_OK = True  # planilha sem aprovados e normal, nao e fonte parada
ROTULO = 'Cadastro pelo site'  # nome na lista de fontes (os empreendimentos tem cada um a sua incorporadora)


def url_publica(v):
    """O link so se for https para um nome de site de verdade (nada de IP, localhost ou rede interna)."""
    v = (v or '').strip()
    host = urlsplit(v).hostname or ''
    if not v.startswith('https://') or '.' not in host or host.endswith(('.local', '.internal', '.lan')):
        return None
    try:
        ipaddress.ip_address(host)
        return None
    except ValueError:
        return v


assert url_publica('https://lidera.com.br/x') == 'https://lidera.com.br/x'
assert url_publica('http://lidera.com.br') is None and url_publica('https://192.168.0.1/a') is None
assert url_publica('https://localhost/a') is None and url_publica('javascript:alert(1)') is None


def numero(v, minimo, maximo):
    try:
        n = float(str(v).replace(',', '.'))
    except ValueError:
        return None
    return n if minimo <= n <= maximo else None


def faixa(a, b):
    v = sorted(x for x in (a, b) if x is not None)
    return [v[0], v[-1]] if v else None


def parse(linha):
    nome, cidade, link = (linha.get(k, '').strip() for k in ('Nome do empreendimento', 'Cidade', 'Link oficial do empreendimento'))
    if not nome or not cidade or not url_publica(link):
        return None
    dorms = faixa(*(numero(linha.get(f'Dormitórios ({k})'), 0, 6) for k in ('mínimo', 'máximo')))
    end = ', '.join(x for x in (linha.get('Endereço (rua e número)', '').strip(), linha.get('Bairro', '').strip()) if x)
    uf = linha.get('Estado (sigla)', '').strip().upper()
    return {
        'nome': nome[:120],
        'construtora': linha.get('Incorporadora', '').strip()[:80] or 'Não informada',
        'etapa': linha.get('Etapa', '').strip(),
        'endereco': end[:200] or None,
        'cidade': cidade[:80],
        'uf': uf if re.fullmatch(r'[A-Z]{2}', uf) else None,
        'lat': None, 'lng': None,
        'dorms': [int(x) for x in dorms] if dorms else None,
        'm2': faixa(*(numero(linha.get(f'Área {k} (m²)'), 15, 1000) for k in ('mínima', 'máxima'))),
        'entrega': linha.get('Previsão de entrega', '').strip()[:30] or None,
        'texto': linha.get('Tipo', ''),
        'imagem': url_publica(linha.get('Link de uma foto do empreendimento')),
        'fonte': f'{BASE}/{slug(nome)}-{slug(cidade)}',
        'link': link,
        'mcmv': linha.get('Minha Casa Minha Vida', '').strip() == 'Sim',
    }


_ok = parse({'Nome do empreendimento': 'Vila Teste', 'Cidade': 'Mogi das Cruzes', 'Estado (sigla)': 'sp', 'Etapa': 'Em obras',
             'Link oficial do empreendimento': 'https://exemplo.com.br/vila', 'Dormitórios (mínimo)': '2', 'Dormitórios (máximo)': '1',
             'Área mínima (m²)': '42,5', 'Área máxima (m²)': '9999', 'Tipo': 'Apartamento', 'Minha Casa Minha Vida': 'Sim'})
assert _ok['fonte'] == f'{BASE}/vila-teste-mogi-das-cruzes' and _ok['dorms'] == [1, 2] and _ok['m2'] == [42.5, 42.5]
assert _ok['uf'] == 'SP' and _ok['mcmv'] and _ok['construtora'] == 'Não informada'
assert parse({'Nome do empreendimento': 'X', 'Cidade': 'Y', 'Link oficial do empreendimento': 'http://x.com'}) is None


def coletar():
    # a planilha e nossa (nao e site de terceiro): baixada direto, sem as regras de robots.txt dos coletores
    r = httpx.get(CSV, headers={'User-Agent': UA_ROBO}, timeout=30, follow_redirects=True)
    r.raise_for_status()
    vistos = {}
    for linha in csv.DictReader(io.StringIO(r.content.decode('utf-8'))):
        if (e := parse(linha)) and e['fonte'] not in vistos:  # o mesmo empreendimento aprovado duas vezes entra uma
            vistos[e['fonte']] = e
    return list(vistos.values())
