import json, re, time, unicodedata
import httpx

BASE = 'https://tenda.com'
UA = {'User-Agent': 'NaPlantaBot/0.1 (projeto academico UMC)'}
# estagio_obra da Tenda: 1 obras nao iniciadas, 2 terraplenagem, 3 fundacao, 4 construcao, 5 acabamento, 6 entrega
ESTAGIO = {'1': 'Lançamento', '2': 'Em obras', '3': 'Em obras', '4': 'Em obras', '5': 'Em obras', '6': 'Pronto para morar'}


def slug(s):
    return re.sub(r'[^a-z0-9]+', '-', unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode().lower()).strip('-')


def parse(url, html):
    txt = ''.join(json.loads(f'"{c}"') for c in re.findall(r'self\.__next_f\.push\(\[1,"(.*?)"\]\)', html, re.S))
    def ref(v):  # "$22" aponta para um bloco "22:T<tamanho hex>,<texto>" do payload
        if not (v or '').startswith('$'):
            return v or None
        m = re.search(rf'(?<![0-9a-f]){v[1:]}:T([0-9a-f]+),', txt)
        return txt[m.end():m.end() + int(m[1], 16)] if m else None

    i = txt.find('"slug":"' + url.rstrip('/').rsplit('/', 1)[1] + '"')
    if i < 0:
        return None
    d, _ = json.JSONDecoder().raw_decode(txt[txt.rfind('{"id"', 0, i):])
    end = d.get('endereco') or {}
    cidade_url = url.split('/')[-2]
    if slug(end.get('cidade')) != cidade_url:  # fonte inconsistente (ex.: pagina de Poa com endereco em Salvador)
        return None
    etapa = ('Breve lançamento' if d.get('breve_lancamento') else 'Lançamento' if d.get('lancamento')
             else 'Pronto para morar' if d.get('pronto_morar') else ESTAGIO.get(str(d.get('estagio_obra'))))
    if 'vendido' in str(d.get('status')).lower():
        return None
    texto = ' '.join(p.get('nome') or '' for p in d.get('plantas') or []) or d.get('descricao') or ''
    grupos = re.findall(r'((?:\d+\s*(?:,|e|ou)\s*)*\d+)\s*(?:quarto|dorm)', texto, re.I)
    dorms = [int(x) for g in grupos for x in re.findall(r'\d+', g)]
    return {
        'nome': d['nome'].title() if d['nome'].isupper() else d['nome'],
        'construtora': 'Tenda',
        'etapa': etapa,
        'endereco': ', '.join(filter(None, [end.get('rua'), end.get('numero'), end.get('bairro')])) or None,
        'cidade': end.get('cidade'), 'uf': end.get('estado'),
        'lat': float(end['latitude']) if end.get('latitude') else None,
        'lng': float(end['longitude']) if end.get('longitude') else None,
        'dorms': [min(dorms), max(dorms)] if dorms else None,
        'm2': None,
        'plantas': [p['nome'] for p in d.get('plantas') or [] if p.get('nome')],
        'texto': f"{d.get('tipo') or ''} {d.get('descricao') or ''}",
        'imagem': ref(d.get('foto_card')),
        'fonte': url,
    }


def coletar():
    out = []
    with httpx.Client(headers=UA, timeout=30, follow_redirects=True) as c:
        xml = c.get(f'{BASE}/sitemap.xml').text
        for url in sorted(set(re.findall(rf'<loc>({BASE}/apartamentos-a-venda/[a-z]+/[a-z0-9-]+/[a-z0-9-]+)</loc>', xml))):
            time.sleep(1)
            r = c.get(url)
            if r.status_code == 200 and (e := parse(url, r.text)):
                out.append(e)
    return out
