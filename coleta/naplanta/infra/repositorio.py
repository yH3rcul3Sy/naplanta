"""Leitura e gravacao dos JSON que o site publica: a coleta so conversa com o disco por aqui."""
import json
from naplanta.config import SITE

DADOS, MUDANCAS, STATUS = SITE / 'dados.json', SITE / 'mudancas.json', SITE / 'status.json'


def _ler(caminho, padrao):
    return json.loads(caminho.read_text(encoding='utf8')) if caminho.exists() else padrao


def ler(dia):
    """(empreendimentos da coleta anterior, historico de mudancas, status anterior por site)"""
    status = _ler(STATUS, {'fontes': []})
    return _ler(DADOS, []), _ler(MUDANCAS, {'inicio': dia, 'eventos': []}), {s['site']: s for s in status['fontes']}


def gravar(dados, historico, status):
    SITE.mkdir(exist_ok=True)
    DADOS.write_text(json.dumps(dados, ensure_ascii=False, separators=(',', ':')), encoding='utf8')
    MUDANCAS.write_text(json.dumps(historico, ensure_ascii=False, separators=(',', ':')), encoding='utf8')
    STATUS.write_text(json.dumps(status, ensure_ascii=False, indent=1), encoding='utf8')
