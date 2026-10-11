"""Regras de texto, sem rede nem disco."""
import re, unicodedata


def slug(s):
    return re.sub(r'[^a-z0-9]+', '-', unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode().lower()).strip('-')


assert slug('Américas 19 - São Paulo') == 'americas-19-sao-paulo'

_MCMV = re.compile(r'minha\s*casa,?\s*minha\s*vida|\bmcmv\b', re.I)


def cita_mcmv(html):
    """A pagina da incorporadora cita o Minha Casa Minha Vida (o site mostra so isso, nunca afirma que o imovel se enquadra)."""
    return bool(_MCMV.search(html or ''))


assert cita_mcmv('Apartamentos no Minha Casa, Minha Vida') and cita_mcmv('faixa 2 do MCMV') and not cita_mcmv('minha casa nova')
