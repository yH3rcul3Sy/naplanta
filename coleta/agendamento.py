"""Registro das execucoes da coleta no GitHub Actions: horario previsto, inicio, fim, atraso e se coletou de fato.
Usa a API publica (sem token): python coleta/agendamento.py [dias]   -> tabela em Markdown para docs/agendamento.md"""
import re, sys
from datetime import datetime, timedelta, timezone
import httpx

REPO = 'yH3rcul3Sy/naplanta'
BRT = timezone(timedelta(hours=-3))  # Brasilia sem horario de verao desde 2019


def previsto(titulo, criado):
    """Horario agendado (em Brasilia) a partir do cron no titulo 'Coleta diária (23 8 * * *)'; None se manual."""
    m = re.search(r'\((\d+) (\d+) \* \* \*\)', titulo or '')
    if not m:
        return None
    dia = criado.astimezone(timezone.utc)
    alvo = dia.replace(hour=int(m[2]), minute=int(m[1]), second=0, microsecond=0)
    if alvo > dia:  # o GitHub cria a execucao depois do horario; se o relogio virou o dia, o agendamento era de ontem
        alvo -= timedelta(days=1)
    return alvo.astimezone(BRT)


assert previsto('Coleta diária (23 8 * * *)', datetime(2026, 10, 15, 8, 40, tzinfo=timezone.utc)) == \
    datetime(2026, 10, 15, 5, 23, tzinfo=BRT)
assert previsto('Coleta diária (23 17 * * *)', datetime(2026, 10, 16, 1, 5, tzinfo=timezone.utc)).day == 15
assert previsto('Coleta manual', datetime(2026, 10, 15, tzinfo=timezone.utc)) is None


def hora(iso):
    return datetime.fromisoformat(iso.replace('Z', '+00:00')) if iso else None


def execucoes(dias):
    desde = (datetime.now(timezone.utc) - timedelta(days=dias)).date().isoformat()
    with httpx.Client(headers={'Accept': 'application/vnd.github+json'}, timeout=30) as c:
        runs = c.get(f'https://api.github.com/repos/{REPO}/actions/workflows/coleta.yml/runs',
                     params={'per_page': 100, 'created': f'>={desde}'}).raise_for_status().json()['workflow_runs']
        for r in runs:
            if r['event'] not in ('schedule', 'workflow_dispatch'):
                continue
            jobs = c.get(r['jobs_url']).raise_for_status().json()['jobs']
            coleta = next((j for j in jobs if j['name'] == 'coleta'), {})
            yield r, coleta.get('conclusion') or coleta.get('status') or 'nao criado'


def tabela(dias):
    fmt = lambda d: d.astimezone(BRT).strftime('%d/%m %H:%M') if d else '—'
    linhas = ['| Previsto (BRT) | Criada | Início | Fim | Atraso | Resultado | Job coleta |', '|---|---|---|---|---|---|---|']
    for r, coleta in sorted(execucoes(dias), key=lambda x: x[0]['created_at']):
        criado, inicio, fim = hora(r['created_at']), hora(r.get('run_started_at')), hora(r['updated_at'])
        alvo = previsto(r['display_title'], criado)
        sem_alvo = 'manual' if r['event'] == 'workflow_dispatch' else 'agendada (antes do registro)'
        atraso = f'{(inicio - alvo).total_seconds() / 60:.0f} min' if alvo and inicio else '—'
        linhas.append(f"| {fmt(alvo) if alvo else sem_alvo} | {fmt(criado)} | {fmt(inicio)} | {fmt(fim)} | {atraso} "
                      f"| {r['conclusion'] or r['status']} | {coleta} |")
    return '\n'.join(linhas)


if __name__ == '__main__':
    print(tabela(int(sys.argv[1]) if len(sys.argv) > 1 else 7))
