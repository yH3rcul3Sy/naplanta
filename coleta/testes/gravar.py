"""Grava uma pagina real de cada fonte e o resultado da leitura como "esperado" para o testar.py.
Rodar so quando um coletor for mudado de proposito (ou para incluir uma fonte nova):
python coleta/testes/gravar.py            todas
python coleta/testes/gravar.py helbor     so as citadas"""
import gzip, json, pathlib, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from naplanta.config import SITE
from naplanta.fontes import FONTES
from naplanta.infra import rede
from testar import CASOS, ler, nome

CAMPOS = ('lat', 'dorms', 'm2', 'imagem', 'endereco', 'entrega')


def amostra(fonte, dados):
    """O empreendimento ja publicado dessa fonte com mais campos preenchidos (exercita mais o parse)."""
    deles = [e for e in dados if e.get('fonte', '').startswith(fonte.BASE + '/')]
    return max(deles, key=lambda e: (e.get('etapa') != 'Pronto para morar', sum(bool(e.get(k)) for k in CAMPOS)), default=None)


def gravar(fonte, dados):
    if nome(fonte) == 'eztec':
        caso = {'url': f'{fonte.BASE}/imoveis'}
    elif nome(fonte) == 'gfr':
        caso = {'url': f'{fonte.BASE}/load_projetos.ashx?lancamento=1', 'etapa': 'Lançamento'}
    elif nome(fonte) == 'lumiar':
        caso = {'url': f'{fonte.BASE}/imoveis-grid.php?pagina=1'}
    elif nome(fonte) == 'jeronimodaveiga':
        caso = {'url': f'{fonte.BASE}/empreendimentos/'}
    elif nome(fonte) == 'ribeira':
        with rede.cliente() as c:
            card = next(k for k in fonte.cards(c.get(f'{fonte.BASE}/empreendimentos/').text) if k[1] and k[4].startswith(fonte.BASE))
        caso = {'url': card[4], 'card': list(card)}
    elif (e := amostra(fonte, dados) or amostra(fonte, fonte.coletar())) is None:  # fonte nova: ainda sem nada publicado
        return 'sem empreendimento publicado para usar de amostra'
    else:
        caso = {'url': e['fonte'], **({'etapa': e['etapa']} if nome(fonte) in ('integra', 'evolife', 'lumy') else {})}
    with rede.cliente() as c:
        r = c.get(caso['url'])
    if r.status_code != 200:
        return f'pagina respondeu {r.status_code}'
    caso['esperado'] = ler(fonte, caso, r.text)
    if not caso['esperado'] or not all(caso['esperado']):
        return 'a leitura da pagina veio vazia'
    CASOS.mkdir(exist_ok=True)
    (CASOS / f'{nome(fonte)}.html.gz').write_bytes(gzip.compress(r.text.encode('utf8'), 9, mtime=0))
    (CASOS / f'{nome(fonte)}.json').write_text(json.dumps(caso, ensure_ascii=False, indent=1), encoding='utf8')
    return 'gravada: ' + caso['url']


if __name__ == '__main__':
    dados = json.loads((SITE / 'dados.json').read_text(encoding='utf8'))
    for f in FONTES:
        if len(sys.argv) == 1 or nome(f) in sys.argv[1:]:
            try:
                print(f'{nome(f)}: {gravar(f, dados)}')
            except Exception as erro:
                print(f'{nome(f)}: nao gravou ({type(erro).__name__}: {erro})')
