"""O que mudou de uma coleta para a outra e quando uma queda de volume e falha ou realidade. Sem rede nem disco."""
from datetime import datetime, timedelta

QUEDA_MAXIMA = 0.3  # fonte que perde mais que isso de um dia para o outro falhou no meio (Helbor em 26/09: 38 -> 8)
COLETAS_PARA_ACEITAR_QUEDA = 3  # a mesma queda em coletas seguidas e real (esgotamento em massa), nao falha
DIAS_DE_HISTORICO = 180


def quedas(n_novos, n_velhos, seguidas):
    """Quantas coletas seguidas a fonte veio com queda grande (0 = normal)."""
    return seguidas + 1 if n_novos < n_velhos * (1 - QUEDA_MAXIMA) else 0


assert quedas(8, 38, 0) == 1 and quedas(8, 38, 2) == 3 and quedas(30, 38, 2) == 0 and quedas(5, 0, 0) == 0


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


def historico_recente(eventos, dia):
    """Eventos dos ultimos DIAS_DE_HISTORICO dias, a contar de dia."""
    limite = (datetime.fromisoformat(dia) - timedelta(days=DIAS_DE_HISTORICO)).date().isoformat()
    return [e for e in eventos if e['data'] >= limite]


assert [e['data'] for e in historico_recente([{'data': '2026-10-10'}, {'data': '2026-01-01'}], '2026-10-10')] == ['2026-10-10']
