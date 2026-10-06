"""Junta os dados dos passos 1 a 5 e gera o site (index.html na raiz do repositório).

Saídas: dados/relatorio.json (tudo o que a página usa) e index.html
"""
from comum import CANDIDATO, DADOS, RAIZ, candidatos, ler_json, salvar_json

estado = ler_json('resultado_estado.json')
k = next(c for c, _, _ in candidatos(estado) if c['n'] == CANDIDATO)

relatorio = dict(
    meta=dict(dg=estado['dg'], hg=estado['hg'], aviso=estado.get('mntf') or '', pvap=float(k['pvap'].replace(',', '.')),
              seq=int(k['seq'])),
    mun=[[m['nome'], m['votos'], m['pct'], m['pos'], m['outro'], m['outro_sg'], m['outro_pct']]
         for m in ler_json('municipios.json') if m['votos'] > 0],
    mapa=ler_json('mapa.json'),
    oficial=ler_json('resultado_oficial.json'),
    secoes=ler_json('secoes.json'),
    base=ler_json('base.json'),
    b2=ler_json('base_2022x2026.json'),
)
salvar_json(relatorio, 'relatorio.json')

modelo = (RAIZ / 'scripts' / 'template.html').read_text(encoding='utf-8')
geo = (DADOS / 'pe_municipios.geojson').read_text(encoding='utf-8')
dados = (DADOS / 'relatorio.json').read_text(encoding='utf-8')
corpo = modelo.replace('/*DATA*/', dados).replace('/*GEO*/', geo)
# o modelo começa no <title> e termina no </script>; aqui vira um documento HTML completo
cabeca, resto = corpo.split('</style>', 1)
html = ('<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
        + cabeca + '</style></head><body>' + resto + '</body></html>\n')
(RAIZ / 'index.html').write_text(html, encoding='utf-8')
print(f'index.html gerado ({len(html) // 1024} KB), dados do TSE de {estado["dg"]} {estado["hg"]}')
