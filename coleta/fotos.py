"""Miniaturas das fotos servidas pelo proprio site: a Tenda assina os links com credencial que expira em horas,
a Cury bloqueia servicos de redimensionamento e o wsrv.nl demora segundos na primeira vez."""
import hashlib, io, pathlib, time
import httpx
from PIL import Image, ImageOps

PASTA = pathlib.Path(__file__).parent.parent / 'site' / 'fotos'
TAMANHO, QUALIDADE = (600, 300), 62  # o card mostra 16:8 com ate ~390 px de largura (x2 em tela retina)
UA = {'User-Agent': 'NaPlantaBot/0.1 (projeto academico UMC)'}


def nome(url):
    # sem a query: o link assinado da Tenda muda a cada coleta, mas o caminho da foto nao
    return hashlib.sha1(url.split('?')[0].encode()).hexdigest()[:16] + '.webp'


assert nome('https://x.com/a.jpg?X-Amz-Signature=1') == nome('https://x.com/a.jpg?X-Amz-Signature=2') != nome('https://x.com/b.jpg')


def miniatura(url, cliente):
    """Devolve o caminho relativo da miniatura, ou None se a foto nao baixar (tenta de novo na proxima coleta)."""
    if not url or url.startswith('fotos/'):
        return url
    destino = PASTA / nome(url)
    if not destino.exists():
        try:
            r = cliente.get(url)
            r.raise_for_status()
            img = ImageOps.fit(Image.open(io.BytesIO(r.content)).convert('RGB'), TAMANHO, Image.LANCZOS)
            PASTA.mkdir(exist_ok=True)
            img.save(destino, 'WEBP', quality=QUALIDADE, method=6)
            time.sleep(0.2)
        except Exception as erro:
            print('foto nao baixou:', url.split('?')[0][:100], getattr(getattr(erro, 'response', None), 'status_code', type(erro).__name__))
            return None
    return f'fotos/{destino.name}'


def completar(dados):
    with httpx.Client(headers=UA, timeout=30, follow_redirects=True) as c:
        for e in dados:
            e['imagem'] = miniatura(e.get('imagem'), c)
    usadas = {e['imagem'] for e in dados if e.get('imagem')}
    for f in PASTA.glob('*.webp'):  # foto de empreendimento que saiu do site
        if f'fotos/{f.name}' not in usadas:
            f.unlink()
