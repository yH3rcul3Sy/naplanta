"""Caso de uso: alerta diario por e-mail para quem se inscreveu numa cidade.
A inscricao (site/alertas.html) cai na lista "Alertas · Inscritos" com o atributo CIDADES ("Mogi das Cruzes; Suzano").
No dia com novidade, a lista "Alertas · <Cidade>" e sincronizada com quem pediu a cidade e recebe a campanha.
Manda so lancamentos novos e trocas de etapa do dia; empreendimento que saiu do site nao vira alerta."""
from html import escape
from naplanta.config import URL_SITE
from naplanta.publicacao.paginas import pagina, pagina_cidade

PREFIXO = 'Alertas · '
INSCRITOS = PREFIXO + 'Inscritos'
REMETENTE = {'name': 'NaPlanta', 'email': 'contato@naplanta.app.br'}


def eventos_do_dia(historico, dia):
    """{cidade: [eventos novo/etapa do dia]}."""
    por_cidade = {}
    for ev in historico['eventos']:
        if ev['data'] == dia and ev['tipo'] in ('novo', 'etapa') and ev.get('cidade'):
            por_cidade.setdefault(ev['cidade'], []).append(ev)
    return por_cidade


_h = {'eventos': [{'data': '2026-10-12', 'tipo': 'novo', 'cidade': 'Suzano'}, {'data': '2026-10-12', 'tipo': 'saiu', 'cidade': 'Suzano'},
                  {'data': '2026-10-11', 'tipo': 'novo', 'cidade': 'Suzano'}, {'data': '2026-10-12', 'tipo': 'etapa'}]}
assert {c: len(e) for c, e in eventos_do_dia(_h, '2026-10-12').items()} == {'Suzano': 1}


def interessados(contatos):
    """{cidade: {e-mails}} a partir do atributo CIDADES de cada inscrito."""
    out = {}
    for c in contatos:
        for cidade in str((c.get('attributes') or {}).get('CIDADES') or '').split(';'):
            if cidade.strip():
                out.setdefault(cidade.strip(), set()).add(c['email'].lower())
    return out


assert interessados([{'email': 'A@x.com', 'attributes': {'CIDADES': 'Suzano; Poá'}}, {'email': 'b@x.com', 'attributes': {}},
                     {'email': 'c@x.com', 'attributes': {'CIDADES': 'Suzano'}}]) == {'Suzano': {'a@x.com', 'c@x.com'}, 'Poá': {'a@x.com'}}


def email(cidade, eventos, dados):
    """(assunto, html) do alerta de uma cidade. Texto das fontes sempre escapado."""
    novos = sum(ev['tipo'] == 'novo' for ev in eventos)
    partes = [f'{novos} novo{"s" if novos > 1 else ""}' if novos else '',
              f'{len(eventos) - novos} mudança{"s" if len(eventos) - novos > 1 else ""} de etapa' if len(eventos) > novos else '']
    assunto = f'Novidades em {cidade}: ' + ' e '.join(p for p in partes if p)
    por_fonte = {e['fonte']: e for e in dados}
    itens = ''
    for ev in eventos:
        e = por_fonte.get(ev['fonte'])
        link = f'{URL_SITE}e/{pagina(e)}.html' if e else ev['fonte']
        o_que = 'Lançamento novo no site' if ev['tipo'] == 'novo' else f"Mudou de {escape(ev['de'])} para {escape(ev['etapa'])}"
        itens += (f'<li style="margin:0 0 14px"><strong>{escape(ev["nome"])}</strong> · {escape(ev["construtora"])}<br>'
                  f'{o_que}{" · " + escape(ev["etapa"]) if ev["tipo"] == "novo" else ""}<br><a href="{escape(link)}">Ver detalhes</a></li>')
    html = f'''<div style="font-family:Arial,sans-serif;font-size:15px;color:#1d1d1b;max-width:560px">
<p style="font-size:22px;font-weight:bold;margin:0 0 4px">Na<span style="color:#1f6f4a">Planta</span></p>
<p>Novidades de hoje em <strong>{escape(cidade)}</strong>, direto dos sites das incorporadoras:</p>
<ul style="padding-left:18px">{itens}</ul>
<p><a href="{URL_SITE}lancamentos/{pagina_cidade(cidade)}.html">Ver todos os lançamentos em {escape(cidade)}</a></p>
<p style="font-size:12px;color:#6b6a66">Você recebe este e-mail porque se inscreveu nos alertas de {escape(cidade)} em naplanta.app.br.
Preço e disponibilidade: consulte a construtora. <a href="{{{{ unsubscribe }}}}">Cancelar alertas</a></p></div>'''
    return assunto, html


_ev = [{'tipo': 'novo', 'nome': '<b>X</b>', 'construtora': 'C', 'etapa': 'Lançamento', 'fonte': 'https://c.com/x', 'cidade': 'Suzano'},
       {'tipo': 'etapa', 'nome': 'Y', 'construtora': 'C', 'de': 'Lançamento', 'etapa': 'Em obras', 'fonte': 'https://c.com/y', 'cidade': 'Suzano'}]
_a, _html = email('Suzano', _ev, [{'nome': 'Y', 'cidade': 'Suzano', 'fonte': 'https://c.com/y'}])
assert _a == 'Novidades em Suzano: 1 novo e 1 mudança de etapa' and '<b>X</b>' not in _html and '{{ unsubscribe }}' in _html
assert 'naplanta.app.br/e/y-suzano-' in _html and 'href="https://c.com/x"' in _html


def executar(dia, historico, dados, brevo, enviar=True):
    """Manda o alerta do dia de cada cidade com novidade e com inscrito. Devolve o que mandou (ou mandaria)."""
    eventos = eventos_do_dia(historico, dia)
    if not eventos:
        return []
    existentes = brevo.listas()
    quer = interessados(brevo.contatos(existentes[INSCRITOS])) if INSCRITOS in existentes else {}
    feito = []
    for cidade, evs in eventos.items():
        if not (emails := quer.get(cidade)):
            continue
        assunto, html = email(cidade, evs, dados)
        if enviar:
            if (lista := existentes.get(PREFIXO + cidade)) is None:
                lista = existentes[PREFIXO + cidade] = brevo.criar_lista(PREFIXO + cidade)
            # a lista da cidade espelha o atributo: entra quem pediu, sai quem tirou a cidade
            atuais = {c['email'].lower() for c in brevo.contatos(lista)}
            brevo.ajustar_lista(lista, emails - atuais, atuais - emails)
            brevo.enviar_campanha(lista, f'Alerta {cidade} {dia}', assunto, html, REMETENTE)
        feito.append(assunto)
    return feito


class _BrevoFalsa:
    def __init__(self):
        self.lists, self.membros, self.enviadas = {INSCRITOS: 1, PREFIXO + 'Suzano': 2}, {1: [], 2: [{'email': 'velho@x.com'}]}, []
        self.membros[1] = [{'email': 'a@x.com', 'attributes': {'CIDADES': 'Suzano; Poá'}}]
    def listas(self): return dict(self.lists)
    def criar_lista(self, nome): self.lists[nome] = len(self.lists) + 1; self.membros[self.lists[nome]] = []; return self.lists[nome]
    def contatos(self, i): return self.membros[i]
    def ajustar_lista(self, i, entrar, sair): self.membros[i] = [m for m in self.membros[i] if m['email'] not in sair] + [{'email': e} for e in entrar]
    def enviar_campanha(self, i, *a): self.enviadas.append(i)


_b = _BrevoFalsa()
_hist = {'eventos': [{**_ev[0], 'data': 'd'}, {**_ev[0], 'cidade': 'Poá', 'data': 'd'}, {**_ev[0], 'cidade': 'Natal', 'data': 'd'}]}
assert len(executar('d', _hist, [], _b)) == 2 and _b.enviadas == [2, 3] and _b.membros[2] == [{'email': 'a@x.com'}]
