"""API da Brevo (e-mail): listas de inscritos por cidade e envio de campanha. A chave vem do ambiente (segredo do GitHub)."""
import os
import httpx

API = 'https://api.brevo.com/v3'
PASTA = 'NaPlanta'


def _cliente():
    chave = os.environ.get('BREVO_API_KEY')
    if not chave:
        raise RuntimeError('BREVO_API_KEY nao configurada')
    return httpx.Client(base_url=API, headers={'api-key': chave, 'accept': 'application/json'}, timeout=30)


def listas():
    """{nome: id} de todas as listas da conta."""
    with _cliente() as c:
        out, offset = {}, 0
        while True:
            pagina = c.get('/contacts/lists', params={'limit': 50, 'offset': offset}).raise_for_status().json().get('lists') or []
            out |= {l['name']: l['id'] for l in pagina}
            if len(pagina) < 50:
                return out
            offset += 50


def criar_lista(nome):
    with _cliente() as c:
        pastas = c.get('/contacts/folders', params={'limit': 50}).raise_for_status().json().get('folders') or []
        pasta = next((p['id'] for p in pastas if p['name'] == PASTA), None)
        if pasta is None:
            pasta = c.post('/contacts/folders', json={'name': PASTA}).raise_for_status().json()['id']
        return c.post('/contacts/lists', json={'name': nome, 'folderId': pasta}).raise_for_status().json()['id']


def enviar_campanha(lista_id, nome, assunto, html, remetente):
    """Cria e dispara uma campanha para a lista; a Brevo cuida do descadastro ({{ unsubscribe }} no html)."""
    with _cliente() as c:
        campanha = c.post('/emailCampaigns', json={
            'name': nome, 'subject': assunto, 'htmlContent': html,
            'sender': remetente, 'recipients': {'listIds': [lista_id]}}).raise_for_status().json()['id']
        c.post(f'/emailCampaigns/{campanha}/sendNow').raise_for_status()
        return campanha
