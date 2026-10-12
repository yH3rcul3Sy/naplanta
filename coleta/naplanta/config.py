"""Onde ficam os arquivos e como o robo se identifica: o unico lugar que conhece caminhos e constantes do ambiente."""
import pathlib
from datetime import timedelta, timezone

RAIZ = pathlib.Path(__file__).resolve().parents[2]  # coleta/naplanta/config.py -> raiz do repositorio
SITE = RAIZ / 'site'
FOTOS = SITE / 'fotos'
CACHE = RAIZ / 'coleta' / 'cache'
URL_SITE = 'https://naplanta.app.br/'
FORM_ALERTAS = 'https://26eab4e6.sibforms.com/v2/serve/MUIFAAVKS7lAG6EIHy0lNCUnBhjxcPaTA73UfM8FABKdd9RC_Qe6Zw8n8pGBroQPCAPxsGlOQEqGd6nqcMdefGKGFcghCakjXM7ZYJl9NOFFfsB_HsHpqj3xJgZBME1_UKHwZfZVziaLxXXVc24yFSa7wESWbalLPrGOKBnnpbs_zOd_tzqansrvmvFFOiwmV0FhREVGPMEg-_gCCQ=='  # inscricao nos alertas por e-mail (formulario da Brevo)
CONTADOR = 'https://naplanta.goatcounter.com'  # GoatCounter: visitas sem cookies (script em site/js/vendor)

FUSO = timezone(timedelta(hours=-3))  # Brasil sem horario de verao desde 2019
UA_ROBO = 'NaPlantaBot/0.1 (projeto academico UMC)'  # sites das incorporadoras e fotos
UA_OSM = 'NaPlanta/0.1 (projeto academico UMC)'  # Nominatim e Overpass
