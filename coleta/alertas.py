"""Alertas do dia por e-mail (workflow 'alertas', a noite): python coleta/alertas.py
Sem BREVO_API_KEY no ambiente so mostra o que mandaria."""
import os
from naplanta.app import alertas
from naplanta.app.coleta_diaria import hoje
from naplanta.infra import brevo, repositorio

if __name__ == '__main__':
    dia = hoje()
    dados, historico, _ = repositorio.ler(dia)
    if not os.environ.get('BREVO_API_KEY'):
        print('sem BREVO_API_KEY; mandaria:', [alertas.email(c, e, dados)[0] for c, e in alertas.eventos_do_dia(historico, dia).items()] or 'nada')
    else:
        print('enviados:', alertas.executar(dia, historico, dados, brevo) or 'nenhuma novidade hoje')
