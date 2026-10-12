"""Imprime o aviso de fontes paradas a partir do status.json (vazio = tudo bem). Usado pelo workflow: python coleta/alerta.py"""
import json
from naplanta.app.alerta import mensagem
from naplanta.app.coleta_diaria import hoje
from naplanta.infra.repositorio import STATUS

if __name__ == '__main__':
    print(mensagem(json.loads(STATUS.read_text(encoding='utf8')), hoje()) if STATUS.exists() else '')
