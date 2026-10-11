"""Paginas por empreendimento e sitemap (job publicar do GitHub Actions): python coleta/paginas.py"""
from naplanta.config import SITE
from naplanta.publicacao.paginas import gerar

if __name__ == '__main__':
    print(gerar(), 'paginas em', SITE / 'e')
