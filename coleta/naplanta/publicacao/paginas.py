"""Paginas estaticas para o Google, para IAs e para compartilhar: uma por empreendimento (e/), uma por cidade (lancamentos/),
a lista de todos, o sitemap.xml e o llms.txt. Roda na publicacao (job publicar), sobre o dados.json; so biblioteca padrao.
Nada disso vai para o git."""
import hashlib, json
from html import escape
from collections import Counter, defaultdict
from itertools import groupby
from urllib.parse import quote
from naplanta.config import CONTADOR, SITE, URL_SITE as URL
from naplanta.dominio.texto import slug


def pagina(e):
    """Nome do arquivo, estavel entre coletas: nome e cidade legiveis + 4 hex do link de origem (que e unico)."""
    return f"{slug(e['nome'])}-{slug(e.get('cidade'))}-{hashlib.sha1(e['fonte'].encode()).hexdigest()[:4]}".replace('--', '-')


assert pagina({'nome': 'Vila Itapety', 'cidade': 'Mogi das Cruzes', 'fonte': 'https://x.com/a'}).startswith('vila-itapety-mogi-das-cruzes-')
assert pagina({'nome': 'A', 'cidade': 'B', 'fonte': 'https://x.com/a'}) != pagina({'nome': 'A', 'cidade': 'B', 'fonte': 'https://x.com/b'})
assert pagina({'nome': 'A', 'cidade': None, 'fonte': 'https://x.com/a'}).count('--') == 0


def pagina_cidade(cidade):
    return slug(cidade)


assert pagina_cidade('Mogi das Cruzes') == 'mogi-das-cruzes'
NA_PLANTA = ('Breve lançamento', 'Lançamento', 'Em obras')  # a ordem da obra; prontos ficam por ultimo
IMAGEM_PADRAO = 'compartilhar.png'


def _ld(obj):
    # < escapado: texto da fonte com </script> ou <!-- quebraria o bloco
    return '<script type="application/ld+json">' + json.dumps(obj, ensure_ascii=False).replace('<', '\\u003c') + '</script>\n'


def _trilha(itens):
    """Breadcrumbs visiveis + BreadcrumbList para o Google. itens: [(nome, url ou None para a pagina atual)]"""
    # links visiveis relativos (funcionam em qualquer endereco); o JSON-LD exige URL completa
    partes = [f'<a href="{escape(u.replace(URL, "../"))}">{escape(n)}</a>' if u else f'<span aria-current="page">{escape(n)}</span>' for n, u in itens]
    ld = {'@context': 'https://schema.org', '@type': 'BreadcrumbList', 'itemListElement': [
        {'@type': 'ListItem', 'position': i, 'name': n, **({'item': u} if u else {})} for i, (n, u) in enumerate(itens, 1)]}
    return f'<nav class="trilha" aria-label="Você está em">{" › ".join(partes)}</nav>\n', _ld(ld)

ETAPA_CLASSE = {'Breve lançamento': 'e-breve', 'Lançamento': 'e-lanc', 'Em obras': 'e-obras', 'Pronto para morar': 'e-pronto'}

ESTILO = '''<style>
  :root { --bg:#f6f5f2; --card:#fff; --ink:#1d1d1b; --muted:#6b6a66; --line:#e3e1dc; --accent:#1f6f4a; --accent-bg:#e7f2ec; }
  * { box-sizing:border-box; }
  body { margin:0; font:16px/1.5 system-ui, -apple-system, "Segoe UI", sans-serif; color:var(--ink); background:var(--bg); }
  header { background:var(--card); border-bottom:1px solid var(--line); padding:8px 16px; display:flex; align-items:center; gap:12px; position:sticky; top:0; z-index:1; }
  .marca { font-size:24px; font-weight:700; color:inherit; text-decoration:none; } .marca span { color:var(--accent); }
  main { max-width:760px; margin:0 auto; padding:16px 16px 48px; }
  h1 { font-size:clamp(24px, 6vw, 32px); line-height:1.15; margin:10px 0 4px; } h2 { font-size:18px; margin:0 0 10px; }
  .foto { width:100%; height:auto; aspect-ratio:2/1; object-fit:cover; border-radius:16px; display:block; background:var(--line); }
  .selos { display:flex; flex-wrap:wrap; gap:6px; margin-top:14px; }
  .selo { font-size:13px; font-weight:600; padding:3px 10px; border-radius:99px; background:var(--accent-bg); color:var(--accent); }
  .e-breve { color:#8a5a00; background:#fbefd6; } .e-lanc { color:#9a3b12; background:#fbe3d8; }
  .e-obras { color:#1d4f91; background:#dde8f7; } .e-pronto { color:#1f6f4a; background:#e0f0e7; }
  .sub { color:var(--muted); margin:0; }
  .fatos { display:grid; grid-template-columns:repeat(auto-fit, minmax(140px, 1fr)); gap:8px; margin:18px 0; }
  .fato { background:var(--card); border:1px solid var(--line); border-radius:12px; padding:10px 12px; }
  .fato small { display:block; color:var(--muted); font-size:12px; text-transform:uppercase; letter-spacing:.05em; }
  .fato strong { font-size:17px; }
  .bloco { background:var(--card); border:1px solid var(--line); border-radius:14px; padding:16px; margin:12px 0; }
  .bloco ul { margin:0; padding-left:20px; } .bloco li { margin:4px 0; }
  .botoes { display:flex; flex-wrap:wrap; gap:8px; margin:18px 0; }
  .btn { display:inline-flex; align-items:center; justify-content:center; gap:6px; min-height:46px; padding:10px 16px; border-radius:12px;
         font-weight:600; text-decoration:none; border:1px solid var(--line); background:var(--card); color:var(--ink); flex:1 1 180px; }
  .btn:hover { border-color:var(--accent); color:var(--accent); }
  .btn.primario { background:var(--accent); border-color:var(--accent); color:#fff; } .btn.primario:hover { background:#185a3c; color:#fff; }
  .btn.zap { border-color:#25d366; color:#128c4a; }
  .voltar { margin-left:auto; flex:0 0 auto; min-height:40px; padding:6px 12px; }
  .info { color:var(--muted); font-size:14px; } .aviso { color:#8a5a00; }
  a { color:var(--accent); text-underline-offset:3px; } a:focus-visible { outline:2px solid var(--accent); outline-offset:2px; }
  ul.lista { padding-left:20px; } ul.lista li { margin:6px 0; }
  .trilha { font-size:14px; color:var(--muted); margin:2px 0 10px; } .trilha a { color:var(--muted); }
  .itens { list-style:none; padding:0; display:grid; gap:8px; }
  .itens a { display:block; background:var(--card); border:1px solid var(--line); border-radius:12px; padding:10px 14px; text-decoration:none; color:var(--ink); }
  .itens a:hover { border-color:var(--accent); } .itens strong { display:block; } .itens small { color:var(--muted); font-size:13px; }
  footer.rodape { max-width:760px; margin:0 auto; padding:0 16px 32px; color:var(--muted); font-size:14px; }
</style>'''


# as paginas geradas moram em site/e/ e site/lancamentos/, dai os ../
def _documento(titulo, descricao, canonica, corpo, imagem=None, extra='', palavras='lançamentos imobiliários, imóveis na planta'):
    imagem = imagem or IMAGEM_PADRAO
    og = f'<meta property="og:image" content="{escape(URL + imagem)}">' + (
        '\n<meta property="og:image:width" content="1200">\n<meta property="og:image:height" content="630">' if imagem == IMAGEM_PADRAO else '')
    return f'''<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta http-equiv="Content-Security-Policy" content="default-src 'self'; script-src 'self'; connect-src {CONTADOR}; style-src 'unsafe-inline'; img-src 'self'; object-src 'none'; base-uri 'self'; form-action 'none'">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(titulo)}</title>
<meta name="description" content="{escape(descricao)}">
<meta name="keywords" content="{escape(palavras)}">
<link rel="canonical" href="{escape(canonica)}">
<meta property="og:title" content="{escape(titulo)}">
<meta property="og:description" content="{escape(descricao)}">
<meta property="og:url" content="{escape(canonica)}">
<meta property="og:locale" content="pt_BR">
<meta name="twitter:card" content="summary_large_image">
{og}
<link rel="icon" type="image/png" href="../favicon.png">
{extra}{ESTILO}
</head>
<body>
<header><a class="marca" href="../">Na<span>Planta</span></a><a class="btn voltar" href="../">← Mapa</a></header>
<main>
{corpo}
</main>
<footer class="rodape"><a href="../e/">Todos os empreendimentos</a> · <a href="../transparencia.html">Sobre os dados</a> · <a href="../transparencia.html#perguntas">Perguntas frequentes</a> · <a href="../privacidade.html">Privacidade</a></footer>
<script data-goatcounter="{CONTADOR}/count" async src="../js/vendor/goatcounter.js"></script>
</body>
</html>
'''


def _faixa(v, u):
    return None if not v else f'{v[0]:g}{u}' if v[0] == v[1] else f'{v[0]:g} a {v[1]:g}{u}'


def html_empreendimento(e, nome_arquivo, outros=()):
    """outros: empreendimentos da mesma cidade para o bloco 'Outros lançamentos' (links internos)."""
    lugar = ' - '.join(filter(None, [e.get('cidade'), e.get('uf')]))
    fatos = ' · '.join(filter(None, [_faixa(e.get('dorms'), ' dormitórios'), _faixa(e.get('m2'), ' m²')]))
    descricao = f"{e['nome']}: {(e.get('tipo') or 'empreendimento').lower()} da {e['construtora']} em {lugar or 'local não informado'}, " \
                f"{(e.get('etapa') or '').lower()}{'. ' + fatos if fatos else ''}."
    est, perto = e.get('estacao'), e.get('perto') or {}
    arredores = []
    if 'estacao' in e:
        arredores.append(f"Estação {est['nome']} ({est['tipo']}) a {'menos de 100 m' if est['km'] < 0.1 else str(est['km']).replace('.', ',') + ' km'} em linha reta" if est
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
    cidade = e.get('cidade')
    trilha, ld_trilha = _trilha([('NaPlanta', URL)] + ([(cidade, f'{URL}lancamentos/{pagina_cidade(cidade)}.html')] if cidade else []) + [(e['nome'], None)])
    ld = _ld(dados) + ld_trilha
    rota = f"https://www.google.com/maps/dir/?api=1&destination={e['lat']},{e['lng']}" if e.get('lat') is not None else None
    fato =lambda rotulo, valor: f'<div class="fato"><small>{rotulo}</small><strong>{escape(valor)}</strong></div>' if valor else ''
    zap = 'https://wa.me/?text=' + quote(f"{e['nome']} ({e['construtora']}, {lugar or 'NaPlanta'}): {canonica}")
    corpo = f'''{trilha}{f'<img class="foto" src="../{escape(e["imagem"])}" alt="Foto de {escape(e["nome"])}" width="600" height="300">' if e.get('imagem') else ''}
<div class="selos"><span class="selo {ETAPA_CLASSE.get(e.get('etapa'), '')}">{escape(e.get('etapa') or '')}</span>{'<span class="selo">MCMV</span>' if e.get('mcmv') else ''}</div>
<h1>{escape(e['nome'])}</h1>
<p class="sub">{escape(e['construtora'])}{' · ' + escape(lugar) if lugar else ''}</p>
<div class="fatos">{fato('Dormitórios', _faixa(e.get('dorms'), ''))}{fato('Área', _faixa(e.get('m2'), ' m²'))}{fato('Tipo', e.get('tipo'))}{fato('Entrega', e.get('entrega'))}</div>
<div class="botoes">
  <a class="btn primario" href="../?e={escape(nome_arquivo)}">Ver no mapa</a>
  <a class="btn" href="{escape(e['fonte'])}" rel="noopener">Site da {escape(e['construtora'])} ↗</a>
  {f'<a class="btn" href="{escape(rota)}" rel="noopener">Como chegar ↗</a>' if rota else ''}
  <a class="btn zap" href="{escape(zap)}" rel="noopener">Compartilhar no WhatsApp</a>
</div>
{f'<p class="info">📍 {escape(e["endereco"])}</p>' if e.get('endereco') else ''}
{'<p class="aviso">Localização aproximada: o pino está no bairro, não no endereço exato.</p>' if e.get('aprox') else ''}
{'<div class="bloco"><h2>Minha Casa Minha Vida</h2><p style="margin:0">A página da construtora cita o programa. Veja se você se enquadra no <a href="https://www.portaldeempreendimentos.caixa.gov.br/simulador/" rel="noopener">simulador da Caixa ↗</a>.</p></div>' if e.get('mcmv') else ''}
{'<div class="bloco"><h2>Arredores</h2><ul>' + ''.join(f'<li>{escape(a)}</li>' for a in arredores) + '</ul><p class="info" style="margin:8px 0 0">Dados do OpenStreetMap, distâncias em linha reta.</p></div>' if arredores else ''}
<p class="info">{f"No site da construtora desde {'/'.join(reversed(e['desde'].split('-')))}. " if e.get('desde') else ''}Informações do site da {escape(e['construtora'])}; preço e disponibilidade, consulte a construtora.</p>
{_outros(cidade, outros)}'''
    return _documento(f"{e['nome']} · {e['construtora']}{' · ' + e['cidade'] if e.get('cidade') else ''} | NaPlanta",
                      descricao, canonica, corpo, e.get('imagem'), ld,
                      ', '.join(filter(None, [e['nome'], e['construtora'], e.get('cidade'), e.get('etapa'), e.get('tipo'), 'imóvel na planta'])))


def _item(e, prefixo):
    fatos = ' · '.join(filter(None, [e['construtora'], e.get('etapa'), _faixa(e.get('dorms'), ' dorm.'), _faixa(e.get('m2'), ' m²'),
                                     'MCMV' if e.get('mcmv') else None]))
    return f'<li><a href="{prefixo}{e["pagina"]}.html"><strong>{escape(e["nome"])}</strong><small>{escape(fatos)}</small></a></li>'


def _outros(cidade, outros):
    if not outros:
        return ''
    return (f'<div class="bloco"><h2>Outros lançamentos em {escape(cidade)}</h2><ul class="itens">' + ''.join(_item(o, '') for o in outros)
            + f'</ul><p style="margin:10px 0 0"><a href="../lancamentos/{pagina_cidade(cidade)}.html">Ver todos em {escape(cidade)} →</a></p></div>')


def vizinhos(e, da_cidade, n=6):
    """Ate n outros da mesma cidade: na planta antes de pronto, a mesma etapa antes das outras."""
    ordem = lambda o: (o.get('etapa') not in NA_PLANTA, o.get('etapa') != e.get('etapa'), o['nome'])
    return sorted((o for o in da_cidade if o is not e), key=ordem)[:n]


_a, _b, _c = ({'nome': n, 'etapa': et} for n, et in [('A', 'Lançamento'), ('B', 'Pronto para morar'), ('C', 'Em obras')])
assert [o['nome'] for o in vizinhos(_a, [_a, _b, _c])] == ['C', 'B']


def _plural(n, um, varios):
    return f'{n} {um if n == 1 else varios}'


def html_cidade(cidade, lista):
    na_planta = [e for e in lista if e.get('etapa') in NA_PLANTA]
    construtoras = sorted({e['construtora'] for e in lista})
    contagem = Counter(e.get('etapa') for e in lista)
    canonica = f'{URL}lancamentos/{pagina_cidade(cidade)}.html'
    trilha, ld_trilha = _trilha([('NaPlanta', URL), (cidade, None)])
    por_etapa = ', '.join(f'{contagem[et]} {"em obras" if et == "Em obras" else "em " + et.lower()}' for et in NA_PLANTA if contagem[et])
    prontos = contagem['Pronto para morar']
    descricao = (f'Lançamentos imobiliários na planta em {cidade}: {_plural(len(na_planta), "empreendimento", "empreendimentos")} de '
                 f'{_plural(len(construtoras), "construtora", "construtoras")}, com etapa da obra, dormitórios, área e estação próxima. Atualizado todo dia.')
    secoes = ''.join(f'<h2 style="margin-top:24px">{et}</h2><ul class="itens">' + ''.join(_item(e, '../e/') for e in sorted(grupo, key=lambda e: e['nome'])) + '</ul>'
                     for et in (*NA_PLANTA, 'Pronto para morar') if (grupo := [e for e in lista if e.get('etapa') == et]))
    ld = _ld({'@context': 'https://schema.org', '@type': 'ItemList', 'name': f'Lançamentos na planta em {cidade}',
              'itemListElement': [{'@type': 'ListItem', 'position': i, 'url': f'{URL}e/{e["pagina"]}.html', 'name': e['nome']}
                                  for i, e in enumerate(sorted(na_planta, key=lambda e: e['nome']), 1)]}) + ld_trilha
    corpo = f'''{trilha}<h1>Lançamentos na planta em {escape(cidade)}</h1>
<p class="sub">{_plural(len(na_planta), 'empreendimento', 'empreendimentos')} na planta{f' ({por_etapa})' if por_etapa else ''}{f' e {_plural(prontos, "pronto", "prontos")} para morar' if prontos else ''}, de {_plural(len(construtoras), 'construtora', 'construtoras')}.</p>
<div class="botoes"><a class="btn primario" href="../?cidade={quote(cidade)}">Ver {escape(cidade)} no mapa</a></div>
<p class="info">Construtoras: {escape(', '.join(construtoras))}. Dados coletados todo dia dos sites oficiais; preço e disponibilidade, consulte a construtora.</p>
{secoes}'''
    return _documento(f'Lançamentos na planta em {cidade} | NaPlanta', descricao, canonica, corpo, None, ld,
                      f'lançamentos {cidade}, imóveis na planta {cidade}, apartamento na planta {cidade}, breve lançamento {cidade}')


def html_lista(dados):
    por_cidade = groupby(sorted(dados, key=lambda e: (e.get('cidade') or '~', e['nome'])), key=lambda e: e.get('cidade') or 'Cidade não informada')
    titulo = lambda c: c if c == 'Cidade não informada' else f'<a href="../lancamentos/{pagina_cidade(c)}.html">{escape(c)}</a>'
    corpo = '<h1>Todos os empreendimentos</h1>\n<p class="info">Lançamentos, obras e prontos de ' \
            f'{len({e["construtora"] for e in dados})} incorporadoras. <a href="../">Ver no mapa</a></p>\n' + ''.join(
        f'<h2 style="margin-top:24px">{titulo(cidade)}</h2><ul class="lista">' + ''.join(
            f'<li><a href="{e["pagina"]}.html">{escape(e["nome"])}</a> <span class="info">· {escape(e["construtora"])} · {escape(e.get("etapa") or "")}</span></li>'
            for e in grupo) + '</ul>\n' for cidade, grupo in por_cidade)
    return _documento('Todos os empreendimentos | NaPlanta', 'Lista de lançamentos imobiliários na planta por cidade, com dados das incorporadoras.',
                      f'{URL}e/', corpo)


def llms_txt(dados, por_cidade):
    """Resumo do site para IAs (padrao llms.txt): o que e, de onde vem e onde esta cada coisa."""
    cidades = sorted(por_cidade.items(), key=lambda c: -sum(e.get('etapa') in NA_PLANTA for e in c[1]))
    return f"""# NaPlanta

> Mapa gratuito de lançamentos imobiliários na planta (breve lançamento, lançamento e em obras) no Brasil, com foco em Mogi das Cruzes e no Alto Tietê. Os dados vêm direto dos sites oficiais de {len({e['construtora'] for e in dados})} incorporadoras e são atualizados todo dia. Projeto acadêmico da Universidade de Mogi das Cruzes (UMC).

- Não coleta preços nem dados pessoais; cada empreendimento leva à página oficial da construtora.
- Para cada empreendimento: etapa da obra, construtora, endereço, dormitórios, área, previsão de entrega, estação de trem/metrô mais próxima e serviços a até 1 km (OpenStreetMap).
- Selo MCMV: a página da construtora cita o Minha Casa Minha Vida (não é garantia de enquadramento).
- Contato: contato@naplanta.app.br

## Páginas principais

- [Mapa interativo]({URL}): filtros por cidade, etapa, construtora, dormitórios, área, estação e MCMV
- [Todos os empreendimentos]({URL}e/): lista completa por cidade
- [Sobre os dados e perguntas frequentes]({URL}transparencia.html): fontes, frequência de coleta e limites
- [Privacidade]({URL}privacidade.html)

## Lançamentos por cidade

""" + ''.join(f"- [{c}]({URL}lancamentos/{pagina_cidade(c)}.html): {sum(e.get('etapa') in NA_PLANTA for e in l)} na planta\n" for c, l in cidades)


def _limpar(pasta):
    pasta.mkdir(exist_ok=True)
    for f in pasta.glob('*.html'):  # o que saiu do site nao deixa pagina para tras
        f.unlink()
    return pasta


def gerar():
    dados = json.loads((SITE / 'dados.json').read_text(encoding='utf8'))
    for e in dados:
        e['pagina'] = pagina(e)
    por_cidade = defaultdict(list)
    for e in dados:
        if e.get('cidade'):
            por_cidade[e['cidade']].append(e)
    pasta = _limpar(SITE / 'e')
    for e in dados:
        outros = vizinhos(e, por_cidade.get(e.get('cidade'), []))
        (pasta / f"{e['pagina']}.html").write_text(html_empreendimento(e, e['pagina'], outros), encoding='utf8')
    (pasta / 'index.html').write_text(html_lista(dados), encoding='utf8')
    pasta = _limpar(SITE / 'lancamentos')
    for cidade, lista in por_cidade.items():
        (pasta / f'{pagina_cidade(cidade)}.html').write_text(html_cidade(cidade, lista), encoding='utf8')
    (SITE / 'llms.txt').write_text(llms_txt(dados, por_cidade), encoding='utf8')
    # o mapa liga cada card a sua pagina por esse campo; so no dados.json publicado, nao no do git
    (SITE / 'dados.json').write_text(json.dumps(dados, ensure_ascii=False, separators=(',', ':')), encoding='utf8')
    urls = ([URL, URL + 'transparencia.html', URL + 'privacidade.html', URL + 'e/']
            + [f'{URL}lancamentos/{pagina_cidade(c)}.html' for c in sorted(por_cidade)] + [f"{URL}e/{e['pagina']}.html" for e in dados])
    (SITE / 'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                                      + ''.join(f'<url><loc>{escape(u)}</loc></url>\n' for u in urls) + '</urlset>\n', encoding='utf8')
    return len(dados)


_x = html_empreendimento({'nome': '<script>x</script>', 'construtora': 'C', 'fonte': 'https://c.com/"a', 'cidade': 'Mogi',
                          'etapa': 'Lançamento', 'endereco': '</script><b>', 'lat': None}, 'p')
assert '<script>x' not in _x and '</script><b>' not in _x and '"a"' not in _x
