import json, pathlib, re
from datetime import datetime, timedelta, timezone
import arredores, cac, cury, damebe, econ, eztec, fotos, geo, helbor, integra, metrocasa, sousaaraujo, tenda, vibra

FONTES = [helbor, cac, cury, tenda, integra, sousaaraujo, damebe, eztec, econ, metrocasa, vibra]
SITE = pathlib.Path(__file__).parent.parent / 'site'
DESTINO, MUDANCAS, STATUS = SITE / 'dados.json', SITE / 'mudancas.json', SITE / 'status.json'
ETAPAS = {'breve lançamento': 'Breve lançamento', 'lançamento': 'Lançamento', 'em obras': 'Em obras',
          'obras avançadas': 'Em obras', 'em construção': 'Em obras', 'pronto para morar': 'Pronto para morar'}
QUEDA_MAXIMA = 0.3  # fonte que perde mais que isso de um dia para o outro falhou no meio (Helbor em 26/09: 38 -> 8)
DIAS_DE_HISTORICO = 180


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


def comparar(velhos, novos, dia):
    """Leva a data de estreia ('desde') de uma coleta para a outra e lista o que mudou numa fonte."""
    if not velhos:  # fonte recem-integrada: tudo nela seria "novo", mas nao e lancamento
        for e in novos:
            e.setdefault('desde', None)
        return []
    antes = {e['fonte']: e for e in velhos}
    agora = {e['fonte'] for e in novos}
    ev = lambda e, t, **x: {'data': dia, 'tipo': t, 'nome': e['nome'], 'construtora': e['construtora'],
                            'cidade': e.get('cidade'), 'uf': e.get('uf'), 'etapa': e['etapa'], 'fonte': e['fonte'], **x}
    eventos = []
    for e in novos:
        v = antes.get(e['fonte'])
        e['desde'] = v.get('desde') if v else dia
        if not v:
            eventos.append(ev(e, 'novo'))
        elif v['etapa'] != e['etapa']:
            eventos.append(ev(e, 'etapa', de=v['etapa']))
    return eventos + [ev(v, 'saiu') for f, v in antes.items() if f not in agora]


_v = [{'fonte': 'a', 'nome': 'A', 'construtora': 'X', 'etapa': 'Lançamento', 'desde': '2026-09-01'},
      {'fonte': 'b', 'nome': 'B', 'construtora': 'X', 'etapa': 'Em obras'}]
_n = [{'fonte': 'a', 'nome': 'A', 'construtora': 'X', 'etapa': 'Em obras'},
      {'fonte': 'c', 'nome': 'C', 'construtora': 'X', 'etapa': 'Lançamento'}]
assert [(e['tipo'], e['nome']) for e in comparar(_v, _n, '2026-09-28')] == [('etapa', 'A'), ('novo', 'C'), ('saiu', 'B')]
assert [e['desde'] for e in _n] == ['2026-09-01', '2026-09-28']
assert comparar([], [{'fonte': 'z'}], '2026-09-28') == []


def hoje():
    return datetime.now(timezone(timedelta(hours=-3))).date().isoformat()  # Brasil sem horario de verao desde 2019


if __name__ == '__main__':
    dia = hoje()
    anteriores = json.loads(DESTINO.read_text(encoding='utf8')) if DESTINO.exists() else []
    historico = json.loads(MUDANCAS.read_text(encoding='utf8')) if MUDANCAS.exists() else {'inicio': dia, 'eventos': []}
    antes = {s['site']: s for s in json.loads(STATUS.read_text(encoding='utf8'))['fontes']} if STATUS.exists() else {}
    dados, eventos, fontes = [], [], []
    for f in FONTES:
        velhos = [e for e in anteriores if e.get('fonte', '').startswith(f.BASE)]
        try:
            novos = []
            for e in f.coletar():
                e['etapa'] = ETAPAS.get((e['etapa'] or '').lower())
                e['tipo'] = tipo(e.pop('texto'))
                if e['etapa']:  # descarta "100% vendido" e etapas desconhecidas
                    novos.append(e)
            if not novos:  # site que bloqueia o servidor responde "vazio" em vez de dar erro
                raise RuntimeError('nenhum empreendimento retornado (site fora do ar ou bloqueando o acesso)')
            if len(novos) < len(velhos) * (1 - QUEDA_MAXIMA):
                # ponytail: queda real e grande num dia so (esgotamento em massa) tambem e barrada; aceitar se repetir por dias
                raise RuntimeError(f'so {len(novos)} de {len(velhos)} (coleta incompleta)')
        except Exception as erro:  # mantem os dados da ultima coleta dessa fonte
            print(f'falha em {f.__name__}: {erro} -> mantendo {len(velhos)} da coleta anterior')
            dados += [geo.completar(e) for e in velhos]
            fontes.append({'site': f.BASE, 'construtora': velhos[0]['construtora'] if velhos else f.__name__, 'total': len(velhos),
                           'ok': False, 'erro': str(erro), 'atualizada': antes.get(f.BASE, {}).get('atualizada')})
            continue
        print(f'{f.__name__}: {len(novos)} coletados')
        eventos += comparar(velhos, novos, dia)
        dados += [geo.completar(e) for e in novos]
        fontes.append({'site': f.BASE, 'construtora': novos[0]['construtora'], 'total': len(novos), 'ok': True, 'atualizada': dia})
    for e in dados:
        e.pop('plantas', None)  # o site nao usa; so pesa no download
    geo.separar(dados)
    arredores.completar(dados)
    fotos.completar(dados)
    limite = (datetime.fromisoformat(dia) - timedelta(days=DIAS_DE_HISTORICO)).date().isoformat()
    historico['eventos'] = [e for e in eventos + historico['eventos'] if e['data'] >= limite]
    SITE.mkdir(exist_ok=True)
    DESTINO.write_text(json.dumps(dados, ensure_ascii=False, separators=(',', ':')), encoding='utf8')
    MUDANCAS.write_text(json.dumps(historico, ensure_ascii=False, separators=(',', ':')), encoding='utf8')
    agora = datetime.now(timezone(timedelta(hours=-3))).isoformat(timespec='minutes')
    STATUS.write_text(json.dumps({'coleta': agora, 'fontes': fontes}, ensure_ascii=False, indent=1), encoding='utf8')
    print(len(dados), 'empreendimentos,', len(eventos), 'mudancas hoje ->', SITE)
