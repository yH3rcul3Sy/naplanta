"""Regras de coordenadas, sem rede nem disco."""


def geohash(h):
    lat, lng, par = [-90.0, 90.0], [-180.0, 180.0], True
    for ch in h:
        n = '0123456789bcdefghjkmnpqrstuvwxyz'.index(ch)
        for bit in (16, 8, 4, 2, 1):
            iv = lng if par else lat
            iv[0 if n & bit else 1] = sum(iv) / 2
            par = not par
    return round(sum(lat) / 2, 6), round(sum(lng) / 2, 6)


assert geohash("ezs42") == (42.604980, -5.603027)


def no_brasil(lat, lng):
    return -34 < lat < 5.5 and -74 < lng < -34.5


assert no_brasil(-23.5, -46.2) and not no_brasil(23.5, 46.7) and not no_brasil(-19.4, -19.4)
