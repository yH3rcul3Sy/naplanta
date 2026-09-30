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


ABREV = {'av.': 'Avenida', 'av': 'Avenida', 'r.': 'Rua', 'r': 'Rua', 'est.': 'Estrada', 'est': 'Estrada',
         'estr.': 'Estrada', 'al.': 'Alameda', 'rod.': 'Rodovia', 'tv.': 'Travessa'}


def _bairro(e):
    """Ultimo trecho do endereco que nao e numero, CEP, cidade ou UF: 'Rua X, 178, Areia Branca' -> 'Areia Branca'."""
    fora = {_sem_acento(e.get('cidade')), _sem_acento(e.get('uf'))}
    partes = [p.strip(' .') for p in re.split(r'[,–]| - ', e.get('endereco') or '')[1:]]
    resto = [p for p in partes if len(p) > 2 and _sem_acento(p) not in fora
             and not re.fullmatch(r'(?i)s/?n|n?º?\s*\d+\w?|cep.*|\d{5}-?\d{3}|lote.*', p)]
    return resto[-1] if resto else None


assert _bairro({'endereco': 'Rua Viver Cassage, 178, Areia Branca', 'cidade': 'Salvador'}) == 'Areia Branca'
assert _bairro({'endereco': 'Av. Sen. Roberto Símonsen, 1545 - Jardim Imperador, Suzano - SP', 'cidade': 'Suzano', 'uf': 'SP'}) == 'Jardim Imperador'
assert _bairro({'endereco': 'Rua Projetada A, S/N', 'cidade': 'Fortaleza'}) is None


def _tentativas(e):
    """Do mais preciso ao mais aproximado: (parametros da busca, filtro do resultado, None ou 'bairro'/'cidade')."""
    cidade, end, todo = e['cidade'], (e.get('endereco') or '').replace('|', ','), lambda r: True
    if end:  # o Nominatim erra enderecos longos e abreviados
        yield {'q': end if not cidade or cidade in end else f'{end}, {cidade}'}, todo, None
        if cep := re.search(r'\d{5}-?\d{3}', end):
            yield {'postalcode': cep[0]}, todo, None
        rua = re.split(r'[,–-]', end)[0].split()
        if rua and cidade:
            rua[0] = ABREV.get(rua[0].lower(), rua[0])
            yield {'street': ' '.join(rua), 'city': cidade}, todo, None
            # sem tipo e titulo: a fonte escreve "Rua Professor X" e o OSM tem "Rua Professora X"
            nucleo = re.sub(r'(?i)^(?:rua|avenida|estrada|alameda|travessa|rodovia)\s+(?:(?:professora?|prof\.?|doutora?|dra?\.?|'
                            r'engenheir[oa]|eng\.?|coronel|cel\.?|senador|sen\.?|padre|pe\.?)\s+)?', '', ' '.join(rua))
            if nucleo != ' '.join(rua):
                yield {'q': f'{nucleo}, {cidade}'}, lambda r: r.get('category') == 'highway', None
    if cidade:  # o predio pelo nome; na falta dele, o bairro, marcado como aproximado (centro da cidade nao serve)
        yield {'q': f"{e['nome']}, {cidade}", 'limit': 3}, \
            lambda r: r.get('category') in PREDIO and mesmo_nome(e['nome'], r.get('name') or ''), None
        if bairro := _bairro(e):
            yield {'q': f'{bairro}, {cidade}'}, todo, 'bairro'
        # nomes como "Estação Ermelino" ou "Parque São Domingos" sao o bairro ou a estacao ao lado
        nome = re.sub(rf"(?i)^{re.escape(e.get('construtora') or '')}\s+|\s+(?:[IV]+|\d+)$", '', e['nome'])
        yield {'q': f'{nome}, {cidade}'}, lambda r: r.get('category') in ('place', 'boundary', 'railway', 'highway'), 'bairro'


def _procurar(e):
    for params, serve, aprox in _tentativas(e):
        for r in _get('search', countrycodes='br', **{'limit': 1, **params}):
            lat, lng = float(r['lat']), float(r['lon'])
            if serve(r) and (not e['cidade'] or na_cidade(lat, lng, e['cidade'])):
                return lat, lng, aprox


def no_brasil(lat, lng):
    return -34 < lat < 5.5 and -74 < lng < -34.5


assert no_brasil(-23.5, -46.2) and not no_brasil(23.5, 46.7) and not no_brasil(-19.4, -19.4)


GENERICAS = {'residencial', 'condominio', 'edificio', 'resort', 'park', 'parque', 'jardim', 'jardins', 'life', 'home', 'clube',
             'club', 'vila', 'das', 'dos', 'del', 'the', 'metrocasa', 'vibra', 'viva', 'sou', 'mais'}


def _palavras(s):
    return {w for w in re.findall(r'[a-z0-9]{3,}', _sem_acento(s)) if w not in GENERICAS}


ROMANOS = {'i': '1', 'ii': '2', 'iii': '3', 'iv': '4'}


def _numeros(s):  # fase/torre: "Meu Lar Mogi 2" e "Meu Lar Mogi II" sao o mesmo; sem numero vale como 1
    return {ROMANOS.get(w, w) for w in re.findall(r'\b(?:\d+|i{1,3}|iv)\b', _sem_acento(s))}


def mesmo_nome(nome, osm):  # todas as palavras do empreendimento no nome do OSM, e o mesmo numero de fase
    n_osm = _numeros(osm)
    return bool(_palavras(nome)) and _palavras(nome) <= _palavras(osm) and (not n_osm or n_osm == (_numeros(nome) or {'1'}))


assert mesmo_nome('Residencial Way', 'Way Loft') and mesmo_nome('Stories - Belém', 'Condomínio Stories Home Belém')
assert not mesmo_nome('Urban Barra Funda', 'Edifício Urban Office') and not mesmo_nome('Jardim Dos Ipês', 'Rua Jardim')
assert mesmo_nome('Meu Lar Mogi', 'Meu Lar Mogi I') and not mesmo_nome('Meu Lar Mogi', 'Meu Lar Mogi II')
assert mesmo_nome('Meu Lar Mogi 2', 'Meu Lar Mogi II') and mesmo_nome('Duetto', 'Duetto Damebe Residence')


PREDIO = ('building', 'landuse', 'leisure')


def pelo_nome(e):
    """Predio com o mesmo nome no OpenStreetMap, perto do ponto atual; None se nao houver."""
    for r in _get('search', q=f"{e['nome']}, {e['cidade']}", countrycodes='br', limit=3):
        if r.get('category') in PREDIO and mesmo_nome(e['nome'], r.get('name') or '') \
                and abs(float(r['lat']) - e['lat']) < 0.02 and abs(float(r['lon']) - e['lng']) < 0.02:  # ~2 km
            return float(r['lat']), float(r['lon'])


def no_predio(dados):
    """Leva o pino ao predio de mesmo nome no OpenStreetMap, quando ele existe: a fonte costuma dar o estande de vendas
    (Cury, ~100 m ao lado) ou so a rua (Way e Duetto caiam no CEP da avenida), e o mapa mostra o predio com o nome."""
    for e in dados:
        if e.get('lat') is not None and e.get('cidade') and (p := pelo_nome(e)):
            e['lat'], e['lng'] = p
            e.pop('aprox', None)


def completar(e):
    e.setdefault('cidade', None); e.setdefault('uf', None)
    if not e['cidade'] and (m := re.search(r'([^\W\d_][^,.\d/-]+?)\s*[-/]\s*([A-Z]{2})\s*$', e.get('endereco') or '')):
        e['cidade'], e['uf'] = m[1].strip(), m[2]  # "..., Santa Rosa. Niterói - RJ"
    # fontes erram coordenadas: sinal trocado (Cury Jaguare caia na Arabia) ou lng = lat (Tenda Sete Lagoas no Atlantico)
    if e['lat'] is not None and not no_brasil(e['lat'], e['lng']):
        e['lat'], e['lng'] = (-abs(e['lat']), -abs(e['lng'])) if no_brasil(-abs(e['lat']), -abs(e['lng'])) else (None, None)
    # a Tenda publica pontos no mar (Recife, Fortaleza) ou em outra cidade (Salvador -> Camacari)
    if e['lat'] is not None and e['cidade'] and not na_cidade(e['lat'], e['lng'], e['cidade']):
        e['lat'] = e['lng'] = None
    if e['lat'] is None and (achado := _procurar(e)):
        e['lat'], e['lng'], aprox = achado
        if aprox:
            e['aprox'] = aprox
    if e['lat'] is not None and not e['cidade']:
        a = _get('reverse', lat=e['lat'], lon=e['lng'], zoom=10).get('address', {})
        e['cidade'], e['uf'] = _cidade(a), a.get('ISO3166-2-lvl4', '').removeprefix('BR-') or None
    return e
