"""Votos da candidata 20123 em cada seção eleitoral de Pernambuco.

Seções agregadas: quando uma seção é agregada a outra, os eleitores dela votam na urna da
seção principal e o TSE publica o resultado apenas na principal. Por isso:
  - as seções agregadas não aparecem no arquivo de votos e não ganham linha própria aqui;
  - a seção principal que recebe agregadas é marcada como "consolidada", com a lista das
    agregadas e o eleitorado somado (principal + agregadas), para o percentual não misturar bases;
  - o eleitorado vem só do 1º turno (o arquivo de locais repete cada seção para o 2º turno).

Usa os mesmos downloads do passo 3 (brutos/). Saídas em dados/:
  regina_da_saude_20123_por_secao.csv   todas as seções de PE com resultado (inclusive com 0 votos)
  secoes.json                        só as seções com voto, para o site
"""
import collections as C
import csv
import io
import zipfile

from comum import BRUTOS, CANDIDATO, CARGO, CDN, CSV_SECOES, DADOS, baixar, salvar_json

secao_zip = baixar(f'{CDN}/votacao_secao/votacao_secao_2026_PE.zip', BRUTOS / 'votacao_secao_2026_PE.zip')
locais_zip = baixar(f'{CDN}/eleitorado_locais_votacao/eleitorado_local_votacao_2026.zip', BRUTOS / 'eleitorado_local_votacao_2026.zip')


def ler(zip_path, membro):
    with zipfile.ZipFile(zip_path) as z, z.open(membro) as f:
        yield from csv.DictReader(io.TextIOWrapper(f, encoding='latin-1'), delimiter=';')


# eleitorado e endereço de cada seção, 1º turno
cadastro, agregadas = {}, C.defaultdict(list)
for r in ler(locais_zip, 'eleitorado_local_votacao_2026_PE.csv'):
    if r['NR_TURNO'] != '1':
        continue
    chave = (r['CD_MUNICIPIO'], r['NR_ZONA'], r['NR_SECAO'])
    if r['CD_TIPO_SECAO_AGREGADA'] == '2':
        principal = (r['CD_MUNICIPIO'], r['NR_ZONA'], r['NR_SECAO_PRINCIPAL'])
        agregadas[principal].append((r['NR_SECAO'], int(r['QT_ELEITOR_SECAO'])))
    else:
        cadastro[chave] = r

# votos de deputado estadual por seção (95 = branco, 96 = nulo)
secoes = {}
for r in ler(secao_zip, 'votacao_secao_2026_PE.csv'):
    if r['CD_CARGO'] != CARGO:
        continue
    chave = (r['CD_MUNICIPIO'], r['NR_ZONA'], r['NR_SECAO'])
    s = secoes.setdefault(chave, dict(municipio=r['NM_MUNICIPIO'], local=r['NM_LOCAL_VOTACAO'], votos=0, validos=0))
    if r['NR_VOTAVEL'] not in ('95', '96'):
        s['validos'] += int(r['QT_VOTOS'])
    if r['NR_VOTAVEL'] == CANDIDATO:
        s['votos'] += int(r['QT_VOTOS'])

agregadas_com_voto = [k for k in agregadas for a, _ in agregadas[k] if (k[0], k[1], a) in secoes]
assert not agregadas_com_voto, f'seção agregada com votos próprios: {agregadas_com_voto[:3]}'

linhas = []
for (cd, zona, nr), s in secoes.items():
    cad = cadastro.get((cd, zona, nr), {})
    ag = sorted(agregadas.get((cd, zona, nr), []))
    aptos = int(cad.get('QT_ELEITOR_SECAO') or 0) + sum(q for _, q in ag)
    linhas.append(dict(municipio=s['municipio'], zona=int(zona), secao=int(nr), local=s['local'],
                       bairro=cad.get('NM_BAIRRO', ''), aptos=aptos, votos=s['votos'], validos=s['validos'],
                       pct=round(100 * s['votos'] / s['validos'], 2) if s['validos'] else 0.0,
                       agregadas=' '.join(str(int(a)) for a, _ in ag)))
linhas.sort(key=lambda x: (-x['votos'], x['municipio'], x['zona'], x['secao']))

with open(DADOS / CSV_SECOES, 'w', newline='', encoding='utf-8-sig') as f:
    w = csv.writer(f, delimiter=';')
    w.writerow(['Municipio', 'Zona', 'Secao', 'Local de votacao', 'Bairro', 'Eleitores aptos', 'Votos Regina',
                'Validos dep. estadual', '% validos', 'Secoes agregadas (consolidadas nesta)'])
    for x in linhas:
        w.writerow([x['municipio'], x['zona'], x['secao'], x['local'], x['bairro'], x['aptos'], x['votos'],
                    x['validos'], str(x['pct']).replace('.', ','), x['agregadas']])

com_voto = [x for x in linhas if x['votos']]
total = sum(x['votos'] for x in linhas)
print(f'{len(linhas)} seções com resultado, {len(com_voto)} com voto, {total} votos')
print(f'{len(agregadas)} seções principais consolidam agregadas; {sum(1 for x in com_voto if x["agregadas"])} delas com voto da candidata')
salvar_json([[x['municipio'], x['zona'], x['secao'], x['local'], x['bairro'], x['aptos'], x['votos'], x['validos'],
              x['pct'], x['agregadas']] for x in com_voto], 'secoes.json')
