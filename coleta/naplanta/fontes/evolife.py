"""Evo Life Incorporadora (Zona Leste de SP): uma lista por etapa em /categoria-do-imovel/<etapa>/; a pagina de cada
imovel traz o endereco (lista com o icone de mapa) e as plantas ("Metros m²: 71", "Dormitório(s): 2")."""
import re
from bs4 import BeautifulSoup
from naplanta.dominio.texto import cita_mcmv
from naplanta.infra import rede

BASE = 'https://evolifeincorporadora.com.br'
ETAPAS = {'breve-lancamento': 'Breve lançamento', 'lancamento': 'Lançamento', 'obras-em-andamento': 'Em obras',
          'imoveis-prontos': 'Pronto para morar'}
ESCRITORIO = 'Serra de Botucatu'  # endereco da sede, que aparece no rodape de toda pagina


def parse(url, html, etapa):
    s = BeautifulSoup(html, 'html.parser')
    titulo = s.select_one('meta[property="og:title"]')
    nome = re.sub(r'\s*-\s*Evo Life Incorporadora\s*$', '', titulo['content'] if titulo else '').strip()
    endereco = None
    for lista in s.select('ul.elementor-icon-list-items'):
        if lista.select_one('.e-fas-map-marker-alt') and ESCRITORIO not in lista.get_text():
            endereco = re.sub(r'\s+,', ',', ' '.join(lista.get_text(' ').split()))
            break
    campos = ' | '.join(x.get_text(' ', strip=True) for x in s.select('.jet-listing-dynamic-field__content'))
    m2 = [int(x) for x in re.findall(r'Metros m²:\s*(\d+)', campos) if int(x) >= 15]
    dorms = [int(x) for x in re.findall(r'Dormitório\(s\):\s*(\d)', campos)]
    foto = s.select_one('meta[property="og:image"]')
    return {
        'nome': nome,
        'construtora': 'Evo Life',
        'etapa': etapa,
        'endereco': endereco,
        'cidade': 'São Paulo',  # so atua na Zona Leste da capital (out/2026)
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
        for chave, etapa in ETAPAS.items():
            lista = c.get(f'{BASE}/categoria-do-imovel/{chave}/').text
            for url in sorted(set(re.findall(rf'href="({BASE}/imovel/[a-z0-9-]+/)"', lista))):
                r = c.get(url)
                if r.status_code == 200:
                    out.append(parse(url, r.text, etapa))
    return out
