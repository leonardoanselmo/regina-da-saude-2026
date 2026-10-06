"""Itaíba, 2022 × 2026: de quem eram, em 2022, os votos que Regina da Saúde conquistou em 2026.

2026 é a primeira eleição de Regina para deputada estadual. Em 2022, os votos de Itaíba para deputado
estadual se concentraram em Rodrigo Novaes (40555), que não concorreu em 2026, e em Claudiano Filho
(11555), que disputou as duas. A comparação mostra, por bairro e por local de votação, a fatia de cada
um nos votos válidos para deputado estadual.

Cada ano usa o próprio cadastro de locais (1º turno), ligado pela seção. A comparação por local junta
só locais com o mesmo código nos dois anos; os demais são somados à parte.

Baixa para brutos/ (~150 MB): votacao_secao_2022_PE.zip e eleitorado_local_votacao_2022.zip.
Usa também os downloads de 2026 do passo 3. Saída: dados/base_2022x2026.json
"""
import collections as C
import csv
import io
import zipfile

from comum import BASE as MUNICIPIO, BRUTOS, CANDIDATO, CARGO, CDN, baixar, salvar_json

# (rótulo, ano, número) — todos no cargo de deputado estadual
SERIES = [('regina', '2026', CANDIDATO), ('novaes', '2022', '40555'), ('claudiano22', '2022', '11555'), ('claudiano26', '2026', '11555')]
NOMES = {'regina': 'Regina da Saúde', 'novaes': 'Rodrigo Novaes', 'claudiano': 'Claudiano Filho'}
ARQ = {
    '2022': (('votacao_secao/votacao_secao_2022_PE.zip', 'votacao_secao_2022_PE.csv'),
             ('eleitorado_locais_votacao/eleitorado_local_votacao_2022.zip', 'eleitorado_local_votacao_2022.csv')),
    '2026': (('votacao_secao/votacao_secao_2026_PE.zip', 'votacao_secao_2026_PE.csv'),
             ('eleitorado_locais_votacao/eleitorado_local_votacao_2026.zip', 'eleitorado_local_votacao_2026_PE.csv')),
}


def ler(caminho, membro):
    zp = baixar(f'{CDN}/{caminho}', BRUTOS / caminho.split('/')[-1])
    with zipfile.ZipFile(zp) as z, z.open(membro) as f:
        for r in csv.DictReader(io.TextIOWrapper(f, encoding='latin-1'), delimiter=';'):
            if r['NM_MUNICIPIO'] == MUNICIPIO and r['NR_TURNO'] == '1':
                yield r


def ano(a):
    (vz, vm), (lz, lm) = ARQ[a]
    cadastro = {(r['NR_ZONA'], r['NR_SECAO']): r for r in ler(lz, lm)}
    loc = C.defaultdict(lambda: dict(validos=0, secoes=set(), nome='', bairro='', **{s: 0 for s, aa, _ in SERIES if aa == a}))
    for r in ler(vz, vm):
        if r['CD_CARGO'] != CARGO:
            continue
        cad = cadastro[(r['NR_ZONA'], r['NR_SECAO'])]
        x = loc[cad['NR_LOCAL_VOTACAO']]
        x.update(nome=cad['NM_LOCAL_VOTACAO'], bairro=cad['NM_BAIRRO'])
        x['secoes'].add(r['NR_SECAO'])
        if r['NR_VOTAVEL'] not in ('95', '96'):
            x['validos'] += int(r['QT_VOTOS'])
        for s, aa, num in SERIES:
            if aa == a and r['NR_VOTAVEL'] == num:
                x[s] += int(r['QT_VOTOS'])
    return loc


L = {a: ano(a) for a in ('2022', '2026')}


def pct(v, t):
    return round(100 * v / t, 2) if t else 0.0


def soma(locais, chaves):
    out = C.Counter()
    for x in locais:
        for k in chaves:
            out[k] += x[k]
    return out


tot = {a: soma(L[a].values(), ['validos'] + [s for s, aa, _ in SERIES if aa == a]) for a in L}
for a in L:
    print(a, f"{len(L[a])} locais, {sum(len(x['secoes']) for x in L[a].values())} seções,", dict(tot[a]))

# por bairro: [bairro, regina26 v, %, novaes22 v, %, claud22 v, %, claud26 v, %]
bairros = C.defaultdict(lambda: {a: C.Counter() for a in L})
for a in L:
    for x in L[a].values():
        for k in ['validos'] + [s for s, aa, _ in SERIES if aa == a]:
            bairros[x['bairro']][a][k] += x[k]


def linha(v22, v26):
    return [v26['regina'], pct(v26['regina'], v26['validos']), v22['novaes'], pct(v22['novaes'], v22['validos']),
            v22['claudiano22'], pct(v22['claudiano22'], v22['validos']), v26['claudiano26'], pct(v26['claudiano26'], v26['validos'])]


saida_bairros = sorted(([b] + linha(v['2022'], v['2026']) for b, v in bairros.items()), key=lambda r: -r[1])

comuns = set(L['2022']) & set(L['2026'])
saida_locais = []
for k in comuns:
    x22, x26 = L['2022'][k], L['2026'][k]
    saida_locais.append([x26['nome'], x26['bairro']] + linha(x22, x26) + [x22['nome'] if x22['nome'] != x26['nome'] else ''])
saida_locais.sort(key=lambda r: -r[2])
mudaram = {a: [L[a][k]['nome'] for k in set(L[a]) - comuns] for a in L}
print(f'{len(comuns)} locais comuns; só 2022: {mudaram["2022"]}; só 2026: {mudaram["2026"]}')
salvar_json(dict(tot={a: dict(tot[a]) for a in tot}, nomes=NOMES, bairros=saida_bairros, locais=saida_locais, mudaram=mudaram),
            'base_2022x2026.json')
