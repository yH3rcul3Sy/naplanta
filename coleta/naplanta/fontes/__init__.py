"""Adaptadores das incorporadoras. Cada modulo expoe BASE (URL do site) e coletar() -> lista de empreendimentos crus.
Nova fonte: criar o modulo, conferir o robots.txt e incluir aqui."""
from naplanta.fontes import (arbore, cac, cury, damebe, econ, eztec, gfr, helbor, integra, jbianchi, metrocasa, scopel,
                             sousaaraujo, tenda, vibra)

FONTES = [helbor, cac, cury, tenda, integra, sousaaraujo, damebe, eztec, econ, metrocasa, vibra, arbore, jbianchi, gfr, scopel]
