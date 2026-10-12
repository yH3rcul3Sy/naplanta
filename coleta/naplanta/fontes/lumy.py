"""Lumy Incorporadora (capital, Guarulhos, Cajamar e Jundiai): uma pagina por status em /status/<status>/; a pagina de
cada empreendimento traz "Localização <bairro ou cidade> Metragem <...> Tipologia <...>" e, as vezes, o endereco."""
import re
from bs4 import BeautifulSoup
from naplanta.dominio.texto import cita_mcmv
from naplanta.infra import rede

BASE = 'https://lumy.com.br'
STATUS = {'breve-lancamento': 'Breve lançamento', 'lancamento': 'Lançamento', 'em-construcao': 'Em obras',
          'pronto': 'Pronto para morar'}
# shortcut: cidades fora da capital onde a Lumy atua (out/2026); o resto da "Localização" e bairro de Sao Paulo
MUNICIPIOS = ('Cajamar', 'Jundiaí', 'Guarulhos', 'Osasco', 'Barueri', 'Santo André', 'São Bernardo do Campo')
FICHA = re.compile(r'Localização (.{2,50}?) Metragem (.{0,30}?) Tipologia (.{0,60}?) Financiamento')
ENDERECO = re.compile(r'((?:Rua|R\.|Av\.|Avenida|Estrada|Alameda|Rodovia)\s[^<>|]{3,70}?,\s*[\d.]+[^<>|]{0,40}?)(?:\s*[-/]\s*SP|/SP)')
SEDE = 'Tocantins'  # endereco do escritorio, no rodape


def lugar(texto):
    """'Polvilho - Cajamar' -> (Polvilho, Cajamar); 'Jundiaí' -> (None, Jundiaí); 'Penha' -> (Penha, São Paulo)."""
    bairro, _, fim = texto.rpartition(' - ')
    if fim in MUNICIPIOS:
        return bairro or None, fim
    return texto, 'São Paulo'


assert lugar('Polvilho - Cajamar') == ('Polvilho', 'Cajamar') and lugar('Jundiaí') == (None, 'Jundiaí')
assert lugar('Vila Clementino') == ('Vila Clementino', 'São Paulo')


def parse(url, html, etapa):
    s = BeautifulSoup(html, 'html.parser')
    # o og:title traz o slogan; o <title> traz o nome ("Lumy Brick – Lumy Incorporadora")
    nome = re.sub(r'\s*[–-]\s*Lumy Incorporadora\s*$', '', s.title.get_text() if s.title else '').strip()
    for t in s(['script', 'style', 'svg']):
        t.decompose()
    texto = ' '.join(s.get_text(' ').split())
    ficha = FICHA.search(texto)
    bairro, cidade = lugar(ficha[1]) if ficha else (None, None)
    m2 = [int(x) for x in re.findall(r'(\d{2,3})\s*m²', ficha[2])] if ficha else []
    dorms = [int(x) for x in re.findall(r'(\d)(?=(?:\s*e\s*\d)*\s*dorm)', ficha[3])] if ficha else []
    end = next((m[1].strip() for m in ENDERECO.finditer(html) if SEDE not in m[1]), None)
    foto = s.select_one('meta[property="og:image"]')
    return {
        'nome': nome,
        'construtora': 'Lumy',
        'etapa': etapa,
        # sem endereco, o nome e o bairro ajudam o geo
        'endereco': end or (f'{nome}, {bairro}' if bairro else None),
        'cidade': cidade,
        'uf': 'SP',
        'lat': None, 'lng': None,
        'dorms': [min(dorms), max(dorms)] if dorms else None,
        'm2': [min(m2), max(m2)] if m2 else None,
        'texto': f'{nome} apartamentos',
        'imagem': foto['content'] if foto else None,
        'fonte': url,
        'mcmv': cita_mcmv(html),
    }


def coletar():
    out = []
    with rede.cliente() as c:
        for chave, etapa in STATUS.items():
            lista = c.get(f'{BASE}/status/{chave}/').text
            for url in sorted(set(re.findall(rf'({BASE}/empreendimentos/[a-z0-9-]+/)', lista))):
                r = c.get(url)
                if r.status_code == 200:
                    out.append(parse(url, r.text, etapa))
    return out
