"""Coleta os votos da candidata 20123 em cada município de PE pela API de resultados do TSE.

Também guarda, por município, a posição dela entre os candidatos a deputado estadual e quem
foi o mais votado na cidade.

Saídas em dados/:
  resultado_estado.json                   resultado estadual de deputado estadual (todos os candidatos)
  regina_da_saude_20123_por_municipio.csv votos e % dos válidos nos 185 municípios
  municipios.json                         votos, %, posição e o mais votado de cada município
"""
import concurrent.futures as cf
import csv

from comum import (API, CANDIDATO, CARGO_ARQ, CSV_MUNICIPIOS, DADOS, ELEICAO, UF, candidatos, get_json,
                   municipios_pe, salvar_json)

BASE_URL = f'{API}/{ELEICAO}/dados/{UF}/'


def dela(d):
    return next((k, p) for k, p, _ in candidatos(d) if k['n'] == CANDIDATO)


estado = get_json(f'{BASE_URL}{UF}-c{CARGO_ARQ}-e00{ELEICAO}-u.json')
salvar_json(estado, 'resultado_estado.json')
k, p = dela(estado)
print(f"{k['nm']} ({p['sg']}): {k['vap']} votos, {k['pvap']}%, {k['seq']}º lugar, situação: {k['st'] or '(não proclamada)'}")
print(f"Dados do TSE de {estado['dg']} {estado['hg']}. Aviso: {estado.get('mntf') or '(nenhum)'}")


def um(m):
    d = get_json(f"{BASE_URL}{UF}{m['cd']}-c{CARGO_ARQ}-e00{ELEICAO}-u.json")
    todos = sorted(((int(c['vap']), c, pp) for c, pp, _ in candidatos(d)), key=lambda x: -x[0])
    pos = next(i for i, (_, c, _) in enumerate(todos, 1) if c['n'] == CANDIDATO)
    v, c, _ = todos[pos - 1]
    lv, lc, lp = todos[0] if pos != 1 else (todos[1] if len(todos) > 1 else (0, {'nmu': '', 'pvap': '0'}, {'sg': ''}))
    return dict(nome=m['nm'], ibge=m['cdi'], votos=v, pct=float(c['pvap'].replace(',', '.')), pos=pos if v else None,
                outro=lc['nmu'], outro_sg=lp['sg'], outro_v=lv, outro_pct=float(lc['pvap'].replace(',', '.')))


with cf.ThreadPoolExecutor(12) as ex:
    linhas = sorted(ex.map(um, municipios_pe()), key=lambda r: -r['votos'])

with open(DADOS / CSV_MUNICIPIOS, 'w', newline='', encoding='utf-8-sig') as f:
    w = csv.writer(f, delimiter=';')
    w.writerow(['Municipio', 'Votos', '% votos validos no municipio', 'Posicao entre os candidatos'])
    for r in linhas:
        w.writerow([r['nome'], r['votos'], str(r['pct']).replace('.', ','), r['pos'] or ''])
salvar_json(linhas, 'municipios.json')

total = sum(r['votos'] for r in linhas)
print(f"{len(linhas)} municípios, {total} votos (estado: {k['vap']}), {sum(1 for r in linhas if r['votos'])} com voto,",
      f"1ª colocada em {sum(1 for r in linhas if r['pos'] == 1)}")
assert total == int(k['vap']), 'soma por município não bate com o total do estado'
