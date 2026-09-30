import json, pathlib, re, time, unicodedata
import httpx

URL = 'https://nominatim.openstreetmap.org'
UA = {'User-Agent': 'NaPlanta/0.1 (projeto academico UMC)'}
CACHE = pathlib.Path(__file__).parent / 'geo_cache.json'
cache = json.loads(CACHE.read_text(encoding='utf8')) if CACHE.exists() else {}


def _get(path, **params):
    key = path + json.dumps(params, sort_keys=True)
    if key not in cache:
        time.sleep(1)  # politica do Nominatim: 1 req/s
        cache[key] = httpx.get(f'{URL}/{path}', params={**params, 'format': 'jsonv2', 'addressdetails': 1},
                               headers=UA, timeout=30).json()
        CACHE.write_text(json.dumps(cache, ensure_ascii=False), encoding='utf8')
    return cache[key]


def geohash(h):
    lat, lng, par = [-90.0, 90.0], [-180.0, 180.0], True
    for ch in h:
        n = '0123456789bcdefghjkmnpqrstuvwxyz'.index(ch)
        for bit in (16, 8, 4, 2, 1):
            iv = lng if par else lat
            iv[0 if n & bit else 1] = sum(iv) / 2
            par = not par
    return round(sum(lat) / 2, 6), round(sum(lng) / 2, 6)


assert geohash("ezs42") == (42.604980, -5.603027)


def _cidade(a):
    return a.get('city') or a.get('town') or a.get('municipality') or a.get('village')


def _sem_acento(s):
    return unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode().lower().strip()


assert _sem_acento('São Paulo ') == 'sao paulo' and _sem_acento(None) == ''


def na_cidade(lat, lng, cidade):
    a = _get('reverse', lat=lat, lon=lng, zoom=10).get('address', {})  # ponto no mar volta sem endereco
    return _sem_acento(_cidade(a)) == _sem_acento(cidade)


ABREV = {'av.': 'Avenida', 'av': 'Avenida', 'r.': 'Rua', 'r': 'Rua', 'est.': 'Estrada', 'al.': 'Alameda'}


def _tentativas(e):
    # o Nominatim erra enderecos longos; tenta do mais preciso ao mais aproximado
    end = e['endereco'].replace('|', ',')
    yield {'q': end if not e['cidade'] or e['cidade'] in end else f"{end}, {e['cidade']}"}
    if cep := re.search(r'\d{5}-?\d{3}', end):
        yield {'postalcode': cep[0]}
    rua = re.split(r'[,–-]', end)[0].split()
    if rua and e['cidade']:
        rua[0] = ABREV.get(rua[0].lower(), rua[0])
        yield {'street': ' '.join(rua), 'city': e['cidade']}


def no_brasil(lat, lng):
    return -34 < lat < 5.5 and -74 < lng < -34.5


assert no_brasil(-23.5, -46.2) and not no_brasil(23.5, 46.7) and not no_brasil(-19.4, -19.4)


GENERICAS = {'residencial', 'condominio', 'edificio', 'resort', 'park', 'parque', 'jardim', 'jardins', 'life', 'home', 'clube',
             'club', 'vila', 'das', 'dos', 'del', 'the', 'metrocasa', 'vibra', 'viva', 'sou', 'mais'}


def _palavras(s):
    return {w for w in re.findall(r'[a-z0-9]{3,}', _sem_acento(s)) if w not in GENERICAS}


def mesmo_nome(nome, osm):  # todas as palavras do empreendimento precisam estar no nome do OSM
    return bool(_palavras(nome)) and _palavras(nome) <= _palavras(osm)


assert mesmo_nome('Residencial Way', 'Way Loft') and mesmo_nome('Stories - Belém', 'Condomínio Stories Home Belém')
assert not mesmo_nome('Urban Barra Funda', 'Edifício Urban Office') and not mesmo_nome('Jardim Dos Ipês', 'Rua Jardim')


def pelo_nome(e):
    """Predio com o mesmo nome no OpenStreetMap, perto do ponto atual; None se nao houver."""
    for r in _get('search', q=f"{e['nome']}, {e['cidade']}", countrycodes='br', limit=3):
        if r.get('category') in ('building', 'landuse') and mesmo_nome(e['nome'], r.get('name') or '') \
                and abs(float(r['lat']) - e['lat']) < 0.02 and abs(float(r['lon']) - e['lng']) < 0.02:  # ~2 km
            return float(r['lat']), float(r['lon'])


def separar(dados):
    """Varios empreendimentos no mesmo ponto (endereco aproximado ou coordenada repetida pela fonte, como Way e Duetto
    no CEP da avenida): tenta o ponto de cada predio pelo nome. Os que continuarem juntos o mapa abre em leque."""
    grupos = {}
    for e in dados:
        if e.get('lat') is not None and e.get('cidade'):
            grupos.setdefault((round(e['lat'], 5), round(e['lng'], 5)), []).append(e)
    for g in grupos.values():
        for e in g if len(g) > 1 else []:
            if p := pelo_nome(e):
                e['lat'], e['lng'] = p


def completar(e):
    e.setdefault('cidade', None); e.setdefault('uf', None)
    # fontes erram coordenadas: sinal trocado (Cury Jaguare caia na Arabia) ou lng = lat (Tenda Sete Lagoas no Atlantico)
    if e['lat'] is not None and not no_brasil(e['lat'], e['lng']):
        e['lat'], e['lng'] = (-abs(e['lat']), -abs(e['lng'])) if no_brasil(-abs(e['lat']), -abs(e['lng'])) else (None, None)
    # a Tenda publica pontos no mar (Recife, Fortaleza) ou em outra cidade (Salvador -> Camacari)
    if e['lat'] is not None and e['cidade'] and not na_cidade(e['lat'], e['lng'], e['cidade']):
        e['lat'] = e['lng'] = None
    if e['lat'] is None and e['endereco']:
        for t in _tentativas(e):
            r = _get('search', countrycodes='br', limit=1, **t)
            if r and (not e['cidade'] or na_cidade(float(r[0]['lat']), float(r[0]['lon']), e['cidade'])):
                e['lat'], e['lng'] = float(r[0]['lat']), float(r[0]['lon'])
                break
    if e['lat'] is not None and not e['cidade']:
        a = _get('reverse', lat=e['lat'], lon=e['lng'], zoom=10).get('address', {})
        e['cidade'], e['uf'] = _cidade(a), a.get('ISO3166-2-lvl4', '').removeprefix('BR-') or None
    return e
