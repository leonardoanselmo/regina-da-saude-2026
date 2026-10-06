"""Prepara o mapa: contornos dos municípios de PE e votos por código IBGE.

Contornos: geodata-br (malha do IBGE), via jsDelivr. As coordenadas são arredondadas
para 3 casas e anéis degenerados são descartados para deixar o arquivo leve.

Entrada: dados/municipios.json (passo 1).
Saídas: dados/pe_municipios.geojson, dados/mapa.json ({ibge: [nome, votos, %, posição]})
"""
import json

from comum import BRUTOS, DADOS, baixar, ler_json, salvar_json

geo_path = baixar('https://cdn.jsdelivr.net/gh/tbrugz/geodata-br@master/geojson/geojs-26-mun.json',
                  BRUTOS / 'geojs-26-mun.json')
geo = json.load(open(geo_path, encoding='utf-8'))


def area(r):
    return sum(r[i][0] * r[i + 1][1] - r[i + 1][0] * r[i][1] for i in range(len(r) - 1)) / 2


def anel(r):
    r = [[round(x, 3), round(y, 3)] for x, y in r]
    r = [r[0]] + [p for i, p in enumerate(r[1:], 1) if p != r[i - 1]]
    if r[0] != r[-1]:
        r.append(r[0])
    return r if len(r) >= 4 and abs(area(r)) > 1e-9 else None


def poligono(poly):
    aneis = [anel(r) for r in poly]
    return None if aneis[0] is None else [a for a in aneis if a]


for f in geo['features']:
    g = f['geometry']
    if g['type'] == 'Polygon':
        g['coordinates'] = poligono(g['coordinates'])
    else:
        g['coordinates'] = [p for p in map(poligono, g['coordinates']) if p]
    f['properties'] = {'id': f['properties']['id'], 'name': f['properties']['name']}
with open(DADOS / 'pe_municipios.geojson', 'w', encoding='utf-8') as out:
    json.dump(geo, out, ensure_ascii=False, separators=(',', ':'))

mapa = {m['ibge']: [m['nome'], m['votos'], m['pct'], m['pos']] for m in ler_json('municipios.json')}
faltando = set(mapa) - {f['properties']['id'] for f in geo['features']}
print(f'{len(geo["features"])} contornos, {len(mapa)} municípios com dados, sem contorno: {faltando or "nenhum"}')
salvar_json(mapa, 'mapa.json')
