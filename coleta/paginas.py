"""Uma pagina HTML por empreendimento, a lista de todos e o sitemap.xml, para o Google indexar e para compartilhar um imovel.
Roda na publicacao (job publicar), sobre o dados.json; so biblioteca padrao. As paginas nao vao para o git."""
import hashlib, json, pathlib, re, unicodedata
from html import escape
from itertools import groupby

SITE = pathlib.Path(__file__).parent.parent / 'site'
URL = 'https://yh3rcul3sy.github.io/naplanta/'


def slug(s):
    return re.sub(r'[^a-z0-9]+', '-', unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode().lower()).strip('-')


def pagina(e):
    """Nome do arquivo, estavel entre coletas: nome e cidade legiveis + 4 hex do link de origem (que e unico)."""
    return f"{slug(e['nome'])}-{slug(e.get('cidade'))}-{hashlib.sha1(e['fonte'].encode()).hexdigest()[:4]}".replace('--', '-')


assert slug('Américas 19 - São Paulo') == 'americas-19-sao-paulo'
assert pagina({'nome': 'Vila Itapety', 'cidade': 'Mogi das Cruzes', 'fonte': 'https://x.com/a'}).startswith('vila-itapety-mogi-das-cruzes-')
assert pagina({'nome': 'A', 'cidade': 'B', 'fonte': 'https://x.com/a'}) != pagina({'nome': 'A', 'cidade': 'B', 'fonte': 'https://x.com/b'})
assert pagina({'nome': 'A', 'cidade': None, 'fonte': 'https://x.com/a'}).count('--') == 0

ESTILO = '''<style>
  body { margin:0; font:16px/1.5 system-ui, -apple-system, "Segoe UI", sans-serif; color:#1d1d1b; background:#f6f5f2; }
  header { background:#fff; border-bottom:1px solid #e3e1dc; padding:10px 16px; display:flex; align-items:center; gap:12px; }
  .marca { font-size:25px; font-weight:700; color:inherit; text-decoration:none; } .marca span { color:#1f6f4a; }
  main { max-width:760px; margin:0 auto; padding:20px 16px 48px; }
  h1 { font-size:28px; line-height:1.2; margin:8px 0; } h2 { font-size:20px; margin:28px 0 8px; }
  img { width:100%; height:auto; border-radius:12px; display:block; background:#e3e1dc; }
  .etapa { display:inline-block; font-size:13px; font-weight:600; padding:2px 10px; border-radius:99px; background:#e7f2ec; color:#1f6f4a; }
  .info { color:#6b6a66; } .aviso { color:#8a5a00; } a { color:#1f6f4a; }
  .botoes { display:flex; flex-wrap:wrap; gap:10px; margin:16px 0; }
  .botao { font-weight:600; color:#1d1d1b; text-decoration:none; border:1px solid #e3e1dc; background:#fff; border-radius:10px; padding:10px 14px; }
  .botao:hover { border-color:#1f6f4a; color:#1f6f4a; } a:focus-visible { outline:2px solid #1f6f4a; outline-offset:2px; }
  ul { padding-left:20px; } li { margin:4px 0; }
</style>'''


# todas as paginas geradas moram em site/e/, dai os ../
def _documento(titulo, descricao, canonica, corpo, imagem=None, extra='', palavras='lançamentos imobiliários, imóveis na planta'):
    og = f'<meta property="og:image" content="{escape(URL + imagem)}">' if imagem else ''
    return f'''<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta http-equiv="Content-Security-Policy" content="default-src 'self'; script-src 'none'; style-src 'unsafe-inline'; img-src 'self'; object-src 'none'; base-uri 'self'; form-action 'none'">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(titulo)}</title>
<meta name="description" content="{escape(descricao)}">
<meta name="keywords" content="{escape(palavras)}">
<link rel="canonical" href="{escape(canonica)}">
<meta property="og:title" content="{escape(titulo)}">
<meta property="og:description" content="{escape(descricao)}">
<meta property="og:url" content="{escape(canonica)}">
<meta property="og:locale" content="pt_BR">
<meta name="twitter:card" content="{'summary_large_image' if imagem else 'summary'}">
{og}
<link rel="icon" type="image/png" href="../favicon.png">
{extra}{ESTILO}
</head>
<body>
<header><a class="marca" href="../">Na<span>Planta</span></a></header>
<main>
{corpo}
</main>
</body>
</html>
'''


def _faixa(v, u):
    return None if not v else f'{v[0]:g}{u}' if v[0] == v[1] else f'{v[0]:g} a {v[1]:g}{u}'


def html_empreendimento(e, nome_arquivo):
    lugar = ' - '.join(filter(None, [e.get('cidade'), e.get('uf')]))
    fatos = ' · '.join(filter(None, [_faixa(e.get('dorms'), ' dormitórios'), _faixa(e.get('m2'), ' m²')]))
    descricao = f"{e['nome']}: {(e.get('tipo') or 'empreendimento').lower()} da {e['construtora']} em {lugar or 'local não informado'}, " \
                f"{(e.get('etapa') or '').lower()}{'. ' + fatos if fatos else ''}."
    itens = [f'<li>{escape(x)}</li>' for x in [
        f"Tipo: {e.get('tipo')}" if e.get('tipo') else None,
        f'Endereço: {e["endereco"]}' if e.get('endereco') else None,
        fatos or None,
        f"Entrega: {e['entrega']}" if e.get('entrega') else None,
        f"No site da construtora desde {'/'.join(reversed(e['desde'].split('-')))}" if e.get('desde') else None] if x]
    est, perto = e.get('estacao'), e.get('perto') or {}
    arredores = []
    if 'estacao' in e:
        arredores.append(f"Estação {est['nome']} ({est['tipo']}) a {str(est['km']).replace('.', ',')} km em linha reta" if est
                         else 'Nenhuma estação de trem ou metrô a até 3 km')
    nomes = {'escolas': 'escolas', 'saude': 'serviços de saúde', 'mercados': 'mercados', 'parques': 'parques'}
    if servicos := [f'{n} {nomes[k]}' for k, n in perto.items() if n and k in nomes]:
        arredores.append('A até 1 km: ' + ', '.join(servicos))
    canonica = f'{URL}e/{nome_arquivo}.html'
    dados = {'@context': 'https://schema.org', '@type': 'Residence', 'name': e['nome'], 'url': canonica,
             'address': {'@type': 'PostalAddress', 'streetAddress': e.get('endereco'), 'addressLocality': e.get('cidade'),
                         'addressRegion': e.get('uf'), 'addressCountry': 'BR'}}
    if e.get('lat') is not None:
        dados['geo'] = {'@type': 'GeoCoordinates', 'latitude': e['lat'], 'longitude': e['lng']}
    # < escapado: texto da fonte com </script> ou <!-- quebraria o bloco
    ld = '<script type="application/ld+json">' + json.dumps(dados, ensure_ascii=False).replace('<', '\\u003c') + '</script>\n'
    corpo = f'''<span class="etapa">{escape(e.get('etapa') or '')}</span>
<h1>{escape(e['nome'])}</h1>
<p class="info">{escape(e['construtora'])}{' · ' + escape(lugar) if lugar else ''}</p>
{f'<img src="../{escape(e["imagem"])}" alt="Foto de {escape(e["nome"])}" width="600" height="300">' if e.get('imagem') else ''}
<div class="botoes">
  <a class="botao" href="{escape(e['fonte'])}" rel="noopener">Ver no site da {escape(e['construtora'])} ↗</a>
  <a class="botao" href="../?e={escape(nome_arquivo)}">Ver no mapa</a>
</div>
<ul>{''.join(itens)}</ul>
{'<p class="aviso">Localização aproximada: o pino está no bairro, não no endereço exato.</p>' if e.get('aprox') else ''}
{'<h2>Arredores</h2><ul>' + ''.join(f'<li>{escape(a)}</li>' for a in arredores) + '</ul><p class="info">Dados do OpenStreetMap.</p>' if arredores else ''}
<p class="info">Informações coletadas do site da {escape(e['construtora'])}. Preço e disponibilidade: consulte a construtora.
<a href="../transparencia.html">Sobre os dados</a> · <a href="./">Todos os empreendimentos</a></p>'''
    return _documento(f"{e['nome']} · {e['construtora']}{' · ' + e['cidade'] if e.get('cidade') else ''} | NaPlanta",
                      descricao, canonica, corpo, e.get('imagem'), ld,
                      ', '.join(filter(None, [e['nome'], e['construtora'], e.get('cidade'), e.get('etapa'), e.get('tipo'), 'imóvel na planta'])))


def html_lista(dados):
    por_cidade = groupby(sorted(dados, key=lambda e: (e.get('cidade') or '~', e['nome'])), key=lambda e: e.get('cidade') or 'Cidade não informada')
    corpo = '<h1>Todos os empreendimentos</h1>\n<p class="info">Lançamentos, obras e prontos de ' \
            f'{len({e["construtora"] for e in dados})} incorporadoras. <a href="../">Ver no mapa</a></p>\n' + ''.join(
        f'<h2>{escape(cidade)}</h2><ul>' + ''.join(
            f'<li><a href="{e["pagina"]}.html">{escape(e["nome"])}</a> <span class="info">· {escape(e["construtora"])} · {escape(e.get("etapa") or "")}</span></li>'
            for e in grupo) + '</ul>\n' for cidade, grupo in por_cidade)
    return _documento('Todos os empreendimentos | NaPlanta', 'Lista de lançamentos imobiliários na planta por cidade, com dados das incorporadoras.',
                      f'{URL}e/', corpo)


def gerar():
    dados = json.loads((SITE / 'dados.json').read_text(encoding='utf8'))
    pasta = SITE / 'e'
    pasta.mkdir(exist_ok=True)
    for f in pasta.glob('*.html'):  # empreendimento que saiu do site nao deixa pagina para tras
        f.unlink()
    for e in dados:
        e['pagina'] = pagina(e)
        (pasta / f"{e['pagina']}.html").write_text(html_empreendimento(e, e['pagina']), encoding='utf8')
    (pasta / 'index.html').write_text(html_lista(dados), encoding='utf8')
    # o mapa (app.js) liga cada card a sua pagina por esse campo; so no dados.json publicado, nao no do git
    (SITE / 'dados.json').write_text(json.dumps(dados, ensure_ascii=False, separators=(',', ':')), encoding='utf8')
    urls = [URL, URL + 'transparencia.html', URL + 'e/'] + [f"{URL}e/{e['pagina']}.html" for e in dados]
    (SITE / 'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                                      + ''.join(f'<url><loc>{escape(u)}</loc></url>\n' for u in urls) + '</urlset>\n', encoding='utf8')
    return len(dados)


_x = html_empreendimento({'nome': '<script>x</script>', 'construtora': 'C', 'fonte': 'https://c.com/"a', 'cidade': 'Mogi',
                          'etapa': 'Lançamento', 'endereco': '</script><b>', 'lat': None}, 'p')
assert '<script>x' not in _x and '</script><b>' not in _x and '"a"' not in _x

if __name__ == '__main__':
    print(gerar(), 'paginas em', SITE / 'e')
