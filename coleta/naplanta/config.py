"""Onde ficam os arquivos e como o robo se identifica: o unico lugar que conhece caminhos e constantes do ambiente."""
import pathlib
from datetime import timedelta, timezone

RAIZ = pathlib.Path(__file__).resolve().parents[2]  # coleta/naplanta/config.py -> raiz do repositorio
SITE = RAIZ / 'site'
FOTOS = SITE / 'fotos'
CACHE = RAIZ / 'coleta' / 'cache'
URL_SITE = 'https://naplanta.app.br/'

FUSO = timezone(timedelta(hours=-3))  # Brasil sem horario de verao desde 2019
UA_ROBO = 'NaPlantaBot/0.1 (projeto academico UMC)'  # sites das incorporadoras e fotos
UA_OSM = 'NaPlanta/0.1 (projeto academico UMC)'  # Nominatim e Overpass
