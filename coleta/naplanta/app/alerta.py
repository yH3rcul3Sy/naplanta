"""Caso de uso: avisar quando uma fonte para de atualizar ou perde campos. Devolve o texto do aviso, ou '' se esta tudo bem;
quem publica o aviso (issue no GitHub) e o workflow."""
from datetime import date

DIAS_PARADA = 2  # um dia sem atualizar e normal (site fora do ar por horas, coleta do PC atrasada)


def mensagem(status, hoje):
    linhas = []
    for f in status['fontes']:
        parada = (date.fromisoformat(hoje) - date.fromisoformat(f['atualizada'])).days if f.get('atualizada') else None
        if not f['ok'] and (parada is None or parada >= DIAS_PARADA):
            desde = f"desde {f['atualizada']} ({parada} dias)" if parada is not None else 'nunca coletada'
            linhas.append(f"- **{f['construtora']}** sem atualizar {desde}: {f.get('erro', '')}")
        if f.get('sumidos'):
            linhas.append(f"- **{f['construtora']}**: os campos {', '.join(f['sumidos'])} sumiram (o site pode ter mudado de layout)")
    if not linhas:
        return ''
    return ('A coleta de ' + hoje + ' encontrou problemas:\n\n' + '\n'.join(linhas) +
            '\n\nOs dados anteriores dessas fontes continuam no site. Esta issue fecha sozinha quando tudo voltar ao normal.')


_s = {'fontes': [{'construtora': 'A', 'ok': True, 'atualizada': '2026-10-12'},
                 {'construtora': 'B', 'ok': False, 'atualizada': '2026-10-11', 'erro': 'x'},  # 1 dia: ainda nao avisa
                 {'construtora': 'C', 'ok': False, 'atualizada': '2026-10-09', 'erro': 'caiu'},
                 {'construtora': 'D', 'ok': True, 'atualizada': '2026-10-12', 'sumidos': ['m2']}]}
assert '**C** sem atualizar desde 2026-10-09 (3 dias): caiu' in mensagem(_s, '2026-10-12')
assert '**B**' not in mensagem(_s, '2026-10-12') and '**D**: os campos m2' in mensagem(_s, '2026-10-12')
assert mensagem({'fontes': _s['fontes'][:2]}, '2026-10-12') == ''
