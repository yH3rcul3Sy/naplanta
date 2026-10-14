"""Valida os JSONs publicados (site/dados.json, status.json, mudancas.json): estrutura, campos obrigatorios e
consistencia entre eles. Roda nos testes de cada push e na coleta, antes de gravar: dado fora do formato nao vai ao ar.
python coleta/testes/validar_dados.py [pasta do site] [--publicacao]   (sai com erro e lista os problemas)
--publicacao: depois do paginas.py, confere tambem uma pagina por empreendimento e o sitemap (o que vai mesmo ao ar)."""
import json, pathlib, re, sys
from collections import Counter

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from naplanta.config import SITE
from naplanta.dominio.coordenadas import no_brasil
from naplanta.dominio.empreendimento import ETAPAS, problemas
from naplanta.fontes import FONTES

DATA = re.compile(r'\d{4}-\d{2}-\d{2}$')
TIPOS = {'Apartamento', 'Lote', 'Casa em condomínio'}
EVENTOS = {'novo', 'etapa', 'saiu'}


def base_de(url):
    """BASE da fonte dona da URL (a mais longa que for prefixo), ou None."""
    return max((f.BASE for f in FONTES if url.startswith(f.BASE + '/')), key=len, default=None)


def erros_dados(dados, pasta):
    erros = []
    if not isinstance(dados, list) or not dados:
        return ['dados.json: deveria ser uma lista nao vazia']
    for i, e in enumerate(dados):
        quem = f"dados[{i}] {str(e.get('nome'))[:40]!r}"
        if not (base := base_de(e.get('fonte') or '')):
            erros.append(f'{quem}: fonte {e.get("fonte")!r} nao pertence a nenhuma fonte cadastrada')
            continue
        # no dado publicado a imagem ja e a miniatura local (fotos/...), conferida abaixo; na coleta ela e uma URL
        erros += [f'{quem}: campo invalido {c}' for c in problemas(e, base)
                  if not (c == 'imagem' and str(e.get('imagem')).startswith('fotos/'))]
        for campo in ('construtora', 'etapa', 'tipo'):
            if not isinstance(e.get(campo), str) or not e[campo].strip():
                erros.append(f'{quem}: sem {campo}')
        if e.get('etapa') not in set(ETAPAS.values()):
            erros.append(f'{quem}: etapa desconhecida {e.get("etapa")!r}')
        if e.get('tipo') not in TIPOS:
            erros.append(f'{quem}: tipo desconhecido {e.get("tipo")!r}')
        if e.get('lat') is not None and isinstance(e.get('lng'), (int, float)) and not no_brasil(e['lat'], e['lng']):
            erros.append(f'{quem}: posicao fora do Brasil ({e["lat"]}, {e["lng"]})')
        if e.get('uf') is not None and not re.fullmatch(r'[A-Z]{2}', str(e['uf'])):
            erros.append(f'{quem}: uf invalida {e["uf"]!r}')
        if e.get('aprox') not in (None, 'bairro', 'rua'):
            erros.append(f'{quem}: aprox invalido {e["aprox"]!r}')
        if e.get('desde') is not None and not DATA.match(str(e['desde'])):
            erros.append(f'{quem}: desde invalido {e["desde"]!r}')
        if (img := e.get('imagem')) and not (pasta / img).is_file():
            erros.append(f'{quem}: imagem {img!r} nao existe no site')
    repetidas = [f for f, n in Counter(e.get('fonte') for e in dados).items() if n > 1]
    erros += [f'dados.json: fonte repetida {f}' for f in repetidas]
    return erros


def erros_status(status, dados):
    erros = []
    if not isinstance(status.get('coleta'), str) or not re.match(r'\d{4}-\d{2}-\d{2}T', status['coleta']):
        erros.append(f'status.json: coleta invalida {status.get("coleta")!r}')
    fontes = status.get('fontes')
    if not isinstance(fontes, list):
        return erros + ['status.json: sem lista de fontes']
    por_base = Counter(base_de(e.get('fonte') or '') for e in dados)
    for f in fontes:
        if f.get('site') not in {x.BASE for x in FONTES}:
            erros.append(f'status.json: site {f.get("site")!r} nao e uma fonte cadastrada')
        elif f.get('total') != por_base[f['site']]:
            erros.append(f'status.json: {f["site"]} diz {f.get("total")} empreendimentos, dados.json tem {por_base[f["site"]]}')
        if not isinstance(f.get('ok'), bool):
            erros.append(f'status.json: {f.get("site")!r} sem ok')
    return erros


def erros_mudancas(mudancas):
    erros = []
    if not DATA.match(str(mudancas.get('inicio'))):
        erros.append(f'mudancas.json: inicio invalido {mudancas.get("inicio")!r}')
    for i, ev in enumerate(mudancas.get('eventos') or []):
        if ev.get('tipo') not in EVENTOS or not DATA.match(str(ev.get('data'))) or not ev.get('nome') or not ev.get('fonte'):
            erros.append(f'mudancas.json: evento {i} malformado {str(ev)[:80]}')
    return erros


def erros_publicacao(dados, pasta):
    """Depois do paginas.py: cada empreendimento com a sua pagina, nenhuma pagina sobrando e o sitemap completo."""
    erros = []
    nomes = [e.get('pagina') for e in dados]
    if not all(isinstance(n, str) and n for n in nomes):
        return [f'publicacao: {sum(not n for n in nomes)} empreendimento(s) sem o campo pagina (paginas.py nao rodou?)']
    erros += [f'publicacao: pagina repetida {n}' for n, k in Counter(nomes).items() if k > 1]
    feitas = {p.stem for p in (pasta / 'e').glob('*.html')} - {'index'}
    erros += [f'publicacao: falta a pagina e/{n}.html' for n in sorted(set(nomes) - feitas)]
    erros += [f'publicacao: pagina e/{n}.html sem empreendimento' for n in sorted(feitas - set(nomes))]
    if len(feitas) != len(dados):
        erros.append(f'publicacao: {len(feitas)} paginas em e/ para {len(dados)} empreendimentos')
    if not (pasta / 'e' / 'index.html').is_file():
        erros.append('publicacao: falta e/index.html')
    sitemap = (pasta / 'sitemap.xml').read_text(encoding='utf8') if (pasta / 'sitemap.xml').is_file() else ''
    no_sitemap = len(re.findall(r'<loc>[^<]*/e/[^<]+\.html</loc>', sitemap))
    if no_sitemap != len(dados):
        erros.append(f'publicacao: sitemap com {no_sitemap} paginas de empreendimento para {len(dados)} empreendimentos')
    return erros


def validar(pasta, publicacao=False):
    ler = lambda nome: json.loads((pasta / nome).read_text(encoding='utf8'))
    dados = ler('dados.json')
    erros = erros_dados(dados, pasta) + erros_status(ler('status.json'), dados) + erros_mudancas(ler('mudancas.json'))
    return erros + (erros_publicacao(dados, pasta) if publicacao else [])


# autoteste: o validador pega o que deve pegar
_bom = {'nome': 'A', 'construtora': 'X', 'etapa': 'Lançamento', 'tipo': 'Apartamento', 'fonte': FONTES[0].BASE + '/a',
        'lat': -23.5, 'lng': -46.2, 'dorms': [1, 2], 'm2': None, 'imagem': None, 'uf': 'SP'}
assert erros_dados([_bom], SITE) == []
assert any('etapa desconhecida' in x for x in erros_dados([{**_bom, 'etapa': 'Vendido'}], SITE))
assert any('fora do Brasil' in x for x in erros_dados([{**_bom, 'lat': 48.8, 'lng': 2.3}], SITE))
assert any('nao pertence' in x for x in erros_dados([{**_bom, 'fonte': 'https://golpe.io/a'}], SITE))
assert any('repetida' in x for x in erros_dados([_bom, _bom], SITE))
assert any('nao existe' in x for x in erros_dados([{**_bom, 'imagem': 'fotos/nao-existe.webp'}], SITE))
assert any('sem o campo pagina' in x for x in erros_publicacao([_bom], SITE))
assert any('falta a pagina' in x for x in erros_publicacao([{**_bom, 'pagina': 'a'}], pathlib.Path('pasta-que-nao-existe')))
assert any('diz 5' in x for x in erros_status({'coleta': '2026-10-14T05:23', 'fontes': [
    {'site': FONTES[0].BASE, 'total': 5, 'ok': True}]}, [_bom]))


if __name__ == '__main__':
    publicacao = '--publicacao' in sys.argv  # no job publicar, depois do paginas.py: confere tambem paginas e sitemap
    args = [a for a in sys.argv[1:] if a != '--publicacao']
    pasta = pathlib.Path(args[0]) if args else SITE
    erros = validar(pasta, publicacao)
    for erro in erros[:50]:
        print('ERRO', erro)
    if len(erros) > 50:
        print(f'... e mais {len(erros) - 50}')
    print(f'{len(erros)} problema(s) em {pasta}')
    sys.exit(1 if erros else 0)
