import json, pathlib, re, time
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


ABREV = {'av.': 'Avenida', 'av': 'Avenida', 'r.': 'Rua', 'r': 'Rua', 'est.': 'Estrada', 'al.': 'Alameda'}


def _tentativas(e):
    # o Nominatim erra enderecos longos; tenta do mais preciso ao mais aproximado
    end = e['endereco'].replace('|', ',')
    yield {'q': end}
    if cep := re.search(r'\d{5}-?\d{3}', end):
        yield {'postalcode': cep[0]}
    rua = re.split(r'[,–-]', end)[0].split()
    if rua and e['cidade']:
        rua[0] = ABREV.get(rua[0].lower(), rua[0])
        yield {'street': ' '.join(rua), 'city': e['cidade']}


def no_brasil(lat, lng):
    return -34 < lat < 5.5 and -74 < lng < -34.5


assert no_brasil(-23.5, -46.2) and not no_brasil(23.5, 46.7) and not no_brasil(-19.4, -19.4)


def completar(e):
    e.setdefault('cidade', None); e.setdefault('uf', None)
    # fontes erram coordenadas: sinal trocado (Cury Jaguare caia na Arabia) ou lng = lat (Tenda Sete Lagoas no Atlantico)
    if e['lat'] is not None and not no_brasil(e['lat'], e['lng']):
        e['lat'], e['lng'] = (-abs(e['lat']), -abs(e['lng'])) if no_brasil(-abs(e['lat']), -abs(e['lng'])) else (None, None)
    if e['lat'] is None and e['endereco']:
        for t in _tentativas(e):
            if r := _get('search', countrycodes='br', limit=1, **t):
                e['lat'], e['lng'] = float(r[0]['lat']), float(r[0]['lon'])
                break
    if e['lat'] is not None and not e['cidade']:
        a = _get('reverse', lat=e['lat'], lon=e['lng'], zoom=10).get('address', {})
        e['cidade'], e['uf'] = _cidade(a), a.get('ISO3166-2-lvl4', '').removeprefix('BR-') or None
    return e
