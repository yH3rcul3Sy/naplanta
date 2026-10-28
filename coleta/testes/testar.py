"""Testa a leitura (parse) de cada fonte contra uma pagina real gravada: python coleta/testes/testar.py
Pega mudanca no codigo dos coletores antes de virar dado errado. Mudanca no site da construtora quem pega e a
checagem de campos sumidos na coleta (dominio.empreendimento.campos_sumidos)."""
import gzip, json, pathlib, sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from naplanta.fontes import FONTES

CASOS = pathlib.Path(__file__).parent / 'casos'


def nome(fonte):
    return fonte.__name__.rsplit('.', 1)[-1]


def ler(fonte, caso, html):
    """Resultado da leitura da pagina gravada, do mesmo jeito que coletar() faz."""
    if nome(fonte) == 'eztec':  # a EZTEC traz todos numa pagina so; os 5 primeiros bastam
        return fonte.lista(html)[:5]
    if nome(fonte) in ('integra', 'evolife', 'lumy'):  # a etapa vem da listagem, nao da pagina
        return [fonte.parse(caso['url'], html, caso['etapa'])]
    if nome(fonte) == 'gfr':  # a GFR traz os cards de uma etapa numa pagina so
        return fonte.parse(html, caso['etapa'])
    if nome(fonte) in ('lumiar', 'jeronimodaveiga'):  # todos numa pagina de lista
        return fonte.parse(html)[:5]
    if nome(fonte) in ('longitude', 'direcional'):  # o nome vem da lista
        return [fonte.parse(caso['url'], html, caso['nome'])]
    if nome(fonte) == 'graal':  # a lista vem da API em JSON
        return fonte.parse(json.loads(html))[:5]
    if nome(fonte) in ('ribeira', 'lidera'):  # etapa, nome e cidade vem do card da lista
        return [fonte.parse(caso['url'], html, tuple(caso['card']))]
    return [fonte.parse(caso['url'], html)]


def html(fonte):
    return gzip.decompress((CASOS / f'{nome(fonte)}.html.gz').read_bytes()).decode('utf8')


def testar():
    falhas, sem_caso = [], []
    for f in FONTES:
        if getattr(f, 'VAZIO_OK', False):  # o cadastro pelo site nao tem pagina: se testa pelos asserts do modulo
            continue
        arquivo = CASOS / f'{nome(f)}.json'
        if not arquivo.exists():
            sem_caso.append(nome(f))
            continue
        caso = json.loads(arquivo.read_text(encoding='utf8'))
        try:
            obtido = json.loads(json.dumps(ler(f, caso, html(f)), ensure_ascii=False))  # mesmo formato do arquivo
        except Exception as erro:
            falhas.append(f'{nome(f)}: erro na leitura ({type(erro).__name__}: {erro})')
            continue
        if obtido != caso['esperado']:
            for i, (a, b) in enumerate(zip(caso['esperado'], obtido)):
                diferentes = sorted(k for k in set(a) | set(b) if a.get(k) != b.get(k))
                if diferentes:
                    falhas.append(f"{nome(f)}: item {i} mudou em {diferentes} (esperado {[a.get(k) for k in diferentes]}, veio {[b.get(k) for k in diferentes]})")
            if len(obtido) != len(caso['esperado']):
                falhas.append(f"{nome(f)}: {len(caso['esperado'])} itens esperados, vieram {len(obtido)}")
        else:
            print(f'ok   {nome(f)}')
    for s in sem_caso:
        print(f'--   {s}: sem pagina gravada (rode coleta/testes/gravar.py {s})')
    for falha in falhas:
        print(f'FALHA {falha}')
    return not falhas


if __name__ == '__main__':
    sys.exit(0 if testar() else 1)
