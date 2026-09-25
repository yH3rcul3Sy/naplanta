import json, pathlib, re
import cac, cury, damebe, geo, helbor, integra, sousaaraujo, tenda

FONTES = [helbor, cac, cury, tenda, integra, sousaaraujo, damebe]
DESTINO = pathlib.Path(__file__).parent.parent / 'site' / 'dados.json'
ETAPAS = {'breve lançamento': 'Breve lançamento', 'lançamento': 'Lançamento', 'em obras': 'Em obras',
          'obras avançadas': 'Em obras', 'em construção': 'Em obras', 'pronto para morar': 'Pronto para morar'}


def tipo(texto):
    t = texto.lower()
    if re.search(r'\blote(s|amento)?\b', t):
        return 'Lote'
    if re.search(r'\bcasas\b|\bcasa (em|de) condom', t):
        return 'Casa em condomínio'
    return 'Apartamento'


assert tipo('Loteamento fechado de alto padrão') == 'Lote'
assert tipo('Casas em Condomínio Fechado de 2 e 3 dorms.') == 'Casa em condomínio'
assert tipo('Casa Piauí, studios de 30 m²') == 'Apartamento'

if __name__ == '__main__':
    anteriores = json.loads(DESTINO.read_text(encoding='utf8')) if DESTINO.exists() else []
    dados = []
    for f in FONTES:
        try:
            novos = f.coletar()
        except Exception as erro:  # fonte fora do ar: mantem os dados da ultima coleta dela
            print('falha em', f.__name__, '->', erro)
            dados += [e for e in anteriores if e.get('fonte', '').startswith(f.BASE)]
            continue
        for e in novos:
            e['etapa'] = ETAPAS.get((e['etapa'] or '').lower())
            e['tipo'] = tipo(e.pop('texto'))
            if e['etapa']:  # descarta "100% vendido" e etapas desconhecidas
                dados.append(geo.completar(e))
    DESTINO.parent.mkdir(exist_ok=True)
    for e in dados:
        e.pop('plantas', None)  # o site nao usa; so pesa no download
    DESTINO.write_text(json.dumps(dados, ensure_ascii=False, separators=(',', ':')), encoding='utf8')
    print(len(dados), 'empreendimentos ->', DESTINO)
