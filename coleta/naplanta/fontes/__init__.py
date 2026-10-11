"""Adaptadores das incorporadoras. Cada modulo expoe BASE (URL do site) e coletar() -> lista de empreendimentos crus.
Nova fonte: criar o modulo, conferir o robots.txt e incluir aqui."""
from naplanta.fontes import cac, cury, damebe, econ, eztec, helbor, integra, metrocasa, sousaaraujo, tenda, vibra

FONTES = [helbor, cac, cury, tenda, integra, sousaaraujo, damebe, eztec, econ, metrocasa, vibra]
