"""Acesso aos sites das incorporadoras: identifica o robo, respeita o robots.txt e espera entre paginas.
Todo coletor abre as paginas por cliente(); assim as regras da coleta valem no codigo, nao so no README."""
import time
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser
import httpx

UA = 'NaPlantaBot/0.1 (projeto academico UMC)'
ROBO = 'NaPlantaBot'  # nome que o robots.txt usa para dar regras so para nos
PAUSA = 1  # segundos entre paginas
_regras = {}  # 'https://site' -> RobotFileParser


def _ler_regras(origem):
    # baixado pelo httpx com o nosso UA: o urllib padrao e barrado por alguns sites e ai trataria tudo como proibido
    r = httpx.get(f'{origem}/robots.txt', headers={'User-Agent': UA}, timeout=30, follow_redirects=True)
    regras = RobotFileParser()
    if r.status_code >= 500:
        r.raise_for_status()  # servidor com problema: a fonte falha hoje e fica a coleta anterior (RFC 9309)
    regras.parse(r.text.splitlines() if r.status_code == 200 else [])  # 4xx = sem robots.txt = tudo liberado (RFC 9309)
    return regras


def permitido(url):
    # shortcut: o robotparser do Python nao entende curingas (* e $) no caminho; nenhuma das 11 fontes usa (out/2026),
    # trocar por um parser completo se alguma passar a usar
    p = urlsplit(url)
    origem = f'{p.scheme}://{p.netloc}'
    if origem not in _regras:
        _regras[origem] = _ler_regras(origem)
    return _regras[origem].can_fetch(ROBO, url)


class _Transporte(httpx.HTTPTransport):
    def handle_request(self, request):
        if not permitido(str(request.url)):
            print('robots.txt nao permite:', request.url)
            return httpx.Response(403, request=request)  # os coletores ja ignoram resposta diferente de 200
        time.sleep(PAUSA)
        return super().handle_request(request)


def cliente():
    """httpx.Client que so abre o que o robots.txt permite (inclusive apos redirecionamento) e espera PAUSA entre paginas."""
    return httpx.Client(headers={'User-Agent': UA}, timeout=30, follow_redirects=True, transport=_Transporte())


_teste = RobotFileParser()
_teste.parse(['User-agent: *', 'Allow: /admin/api2/storage', 'Disallow: /admin/api2', 'Disallow: /api/'])
assert _teste.can_fetch(ROBO, 'https://tenda.com/apartamentos-a-venda/sp/x')
assert not _teste.can_fetch(ROBO, 'https://tenda.com/api/imoveis') and not _teste.can_fetch(ROBO, 'https://tenda.com/admin/api2/x')
_teste = RobotFileParser()
_teste.parse(['User-agent: NaPlantaBot', 'Disallow: /', '', 'User-agent: *', 'Disallow:'])
assert not _teste.can_fetch(ROBO, 'https://x.com/a') and _teste.can_fetch('OutroBot', 'https://x.com/a')
_teste = RobotFileParser()
_teste.parse([])  # robots.txt inexistente
assert _teste.can_fetch(ROBO, 'https://x.com/a')
