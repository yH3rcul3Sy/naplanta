"""Alertas do dia por e-mail (workflow 'alertas', a noite): python coleta/alertas.py
Sem BREVO_API_KEY no ambiente so mostra o que mandaria."""
import os
from datetime import date, timedelta
from naplanta.app import alertas
from naplanta.app.coleta_diaria import hoje
from naplanta.infra import brevo, repositorio

if __name__ == '__main__':
    hj = hoje()
    dados, historico, _ = repositorio.ler(hj)
    # o agendamento do GitHub atrasa e roda depois da meia-noite, quando "hoje" ainda nao tem coleta: olha ontem tambem.
    # Nao manda duas vezes: a campanha tem nome unico por cidade e dia (brevo.enviar_campanha)
    for dia in ((date.fromisoformat(hj) - timedelta(days=1)).isoformat(), hj):
        if not os.environ.get('BREVO_API_KEY'):
            print(dia, 'sem BREVO_API_KEY; mandaria:', [alertas.email(c, e, dados)[0] for c, e in alertas.eventos_do_dia(historico, dia).items()] or 'nada')
        else:
            print(dia, 'enviados:', alertas.executar(dia, historico, dados, brevo) or 'nenhuma novidade')
