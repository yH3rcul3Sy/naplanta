"""Estacao de trem/metro mais proxima e servicos a pe, pelo OpenStreetMap (API Overpass)."""
import json, math, pathlib, re, time
from collections import defaultdict
import httpx

# o servidor principal vive sobrecarregado (504) e o z. cai com frequencia; o lz4 e o mais estavel (set/2026)
ESPELHOS = ['https://lz4.overpass-api.de/api/interpreter', 'https://overpass-api.de/api/interpreter',
            'https://z.overpass-api.de/api/interpreter']
UA = {'User-Agent': 'NaPlanta/0.1 (projeto academico UMC)'}
CACHE = pathlib.Path(__file__).parent / 'arredores_cache.json'
RAIO_ESTACAO, RAIO_SERVICOS = 3.0, 1.0  # km
SERVICOS = {'escolas': ['amenity=school', 'amenity=kindergarten'], 'saude': ['amenity=hospital', 'amenity=clinic'],
            'mercados': ['shop=supermarket'], 'parques': ['leisure=park']}
# consultar um raio em volta de cada imovel derruba o Overpass; um quadrado com varios imoveis sai numa consulta leve
QUADRADO, MARGEM = 0.05, 0.035  # graus: quadrado de ~5,5 km + margem que cobre o raio da estacao
ORCAMENTO = 600  # segundos de Overpass por coleta; o resto do cache se completa nos dias seguintes
# ponytail: cache sem validade (estacao e escola mudam pouco); apagar o arquivo refaz tudo
cache = json.loads(CACHE.read_text(encoding='utf8')) if CACHE.exists() else {}


def km(lat1, lng1, lat2, lng2):  # linha reta; basta para distancias de poucos km
    return math.hypot((lat2 - lat1) * 111.2, (lng2 - lng1) * 111.2 * math.cos(math.radians(lat1)))


assert round(km(-23.5, -46.2, -23.51, -46.2), 2) == 1.11


def _consultar(sul, oeste, norte, leste):
    caixa = f'({sul},{oeste},{norte},{leste})'
    filtros = [f'nwr[railway=station]{caixa};'] + [f'nwr[{tag}]{caixa};' for tags in SERVICOS.values() for tag in tags]
    q = f'[out:json][timeout:60];({"".join(filtros)});out center tags qt;'
    for tentativa in range(6):
        try:
            r = httpx.post(ESPELHOS[tentativa % len(ESPELHOS)], data={'data': q}, headers=UA, timeout=90)
            if r.status_code == 200 and r.text.lstrip().startswith('{'):
                return r.json()['elements']
        except httpx.HTTPError:
            pass
        time.sleep(5)
    return None  # tudo fora do ar: tenta de novo na proxima coleta


def resumir(lat, lng, elementos):
    estacoes, perto = [], dict.fromkeys(SERVICOS, 0)
    for el in elementos:
        t, p = el.get('tags', {}), el.get('center', el)
        d = km(lat, lng, p['lat'], p['lon'])
        if t.get('railway') == 'station':
            if d <= RAIO_ESTACAO and t.get('name') and 'disused' not in t and t.get('usage') != 'tourism':
                tipo = 'metrô' if t.get('station') == 'subway' or t.get('subway') == 'yes' else \
                       'monotrilho' if t.get('station') == 'monorail' else 'trem'
                nome = re.sub(r'^esta[çc][ãa]o\s+', '', t['name'], flags=re.I)  # o OSM ora traz "Estação X", ora "X"
                estacoes.append({'nome': nome, 'tipo': tipo, 'km': round(d, 1)})
        elif d <= RAIO_SERVICOS:
            for servico, tags in SERVICOS.items():
                if any(t.get(k) == v for k, v in (tag.split('=') for tag in tags)):
                    perto[servico] += 1
                    break
    return {'estacao': min(estacoes, key=lambda s: s['km'], default=None), 'perto': perto}


_r = resumir(-23.5, -46.2, [
    {'tags': {'railway': 'station', 'name': 'Longe'}, 'lat': -23.52, 'lon': -46.2},
    {'tags': {'railway': 'station', 'name': 'Estação Perto', 'station': 'subway'}, 'lat': -23.505, 'lon': -46.2},
    {'tags': {'railway': 'station', 'name': 'Antiga', 'disused': 'yes'}, 'lat': -23.5, 'lon': -46.2},
    {'tags': {'railway': 'station', 'name': 'Fora do raio'}, 'lat': -23.6, 'lon': -46.2},
    {'tags': {'amenity': 'school'}, 'center': {'lat': -23.5, 'lon': -46.2}},
    {'tags': {'amenity': 'school'}, 'lat': -23.52, 'lon': -46.2},  # 2,2 km: fora do raio de servicos
    {'tags': {'shop': 'supermarket'}, 'lat': -23.5, 'lon': -46.2}])
assert _r == {'estacao': {'nome': 'Perto', 'tipo': 'metrô', 'km': 0.6},
              'perto': {'escolas': 1, 'saude': 0, 'mercados': 1, 'parques': 0}}, _r


def chave(e):
    return f"{e['lat']:.4f},{e['lng']:.4f}"


def completar(dados, orcamento=ORCAMENTO):
    """Preenche 'estacao' e 'perto' de todos; consulta o Overpass so para os quadrados ainda fora do cache."""
    inicio, faltam = time.monotonic(), defaultdict(list)
    for e in dados:
        if e.get('lat') is not None and chave(e) not in cache:
            faltam[(math.floor(e['lat'] / QUADRADO), math.floor(e['lng'] / QUADRADO))].append(e)
    for (i, j), grupo in faltam.items():
        if time.monotonic() - inicio > orcamento:
            break
        elementos = _consultar(i * QUADRADO - MARGEM, j * QUADRADO - MARGEM, (i + 1) * QUADRADO + MARGEM, (j + 1) * QUADRADO + MARGEM)
        time.sleep(1)  # uso justo do servidor publico
        if elementos is None:
            continue
        for e in grupo:
            cache[chave(e)] = resumir(e['lat'], e['lng'], elementos)
        CACHE.write_text(json.dumps(cache, ensure_ascii=False, separators=(',', ':')), encoding='utf8')
    for e in dados:
        if e.get('lat') is not None and chave(e) in cache:
            e.update(cache[chave(e)])
    return len(faltam)
