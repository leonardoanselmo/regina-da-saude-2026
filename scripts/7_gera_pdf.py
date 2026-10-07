"""Gera o relatório em PDF (relatorio/Regina_da_Saude_20123_2026.pdf) com dicas ao passar o mouse.

As dicas são campos de formulário invisíveis com texto de ajuda (/TU). Aparecem no Adobe Acrobat
Reader e no Firefox; o leitor de PDF do Chrome e do Edge não as mostra.
Requer: pip install -r requirements.txt. Entradas: dados/relatorio.json e dados/pe_municipios.geojson (passos 5 e 6).
"""
import json, math
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor, Color
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import simpleSplit
from PIL import Image, ImageDraw

from comum import DADOS, RAIZ

pdfmetrics.registerFont(TTFont('R', 'C:/Windows/Fonts/segoeui.ttf'))
pdfmetrics.registerFont(TTFont('B', 'C:/Windows/Fonts/segoeuib.ttf'))
pdfmetrics.registerFont(TTFont('SB', 'C:/Windows/Fonts/seguisb.ttf'))

D = json.load(open(DADOS / 'relatorio.json', encoding='utf-8'))
GEO = json.load(open(DADOS / 'pe_municipios.geojson', encoding='utf-8'))

INK = HexColor('#16202a'); INK2 = HexColor('#4a5561'); MUTED = HexColor('#7a848e'); LINE = HexColor('#dfe3e0')
ACC = HexColor('#1f56c4'); ACCS = HexColor('#e3ebfa'); GRAY = HexColor('#b7bec4'); TRACK = HexColor('#eceeea')
UP = HexColor('#2a78d6'); DOWN = HexColor('#d6553f'); WARNBG = HexColor('#fdf3dc'); WARNINK = HexColor('#7a5208')
BINS = [HexColor(h) for h in ['#eceeea', '#d4e2f6', '#9fc0ec', '#5f95db', '#2c66c4', '#143f8a']]
W, H = A4; M = 40; CW = W - 2 * M

def fmt(n): return f'{int(round(n)):,}'.replace(',', '.')
def pct(p): return f'{p:.2f}'.replace('.', ',') + '%'
def sgn(d): return ('+' if d > 0 else '-' if d < 0 else '') + fmt(abs(d))
SMALL = {'da', 'de', 'do', 'dos', 'das', 'e'}
def title(s):
    return ' '.join(w if (i and w in SMALL) else w[:1].upper() + w[1:] for i, w in enumerate(s.lower().split()))
def binof(v): return 0 if not v else 1 if v < 10 else 2 if v < 100 else 3 if v < 500 else 4 if v < 1000 else 5

(RAIZ / 'relatorio').mkdir(exist_ok=True)
c = canvas.Canvas(str(RAIZ / 'relatorio' / 'Regina_da_Saude_20123_2026.pdf'), pagesize=A4)
c.setTitle('Regina da Saúde 20123 em 2026'); c.setAuthor('Dados: TSE'); c.setSubject('Votação para deputada estadual em Pernambuco, 1º turno de 2026')
NT = [0]
def tip(x, y, w, h, text):
    NT[0] += 1
    c.acroForm.textfield(name=f't{NT[0]}', tooltip=text, x=x, y=y, width=max(w, 1), height=max(h, 1),
                         borderWidth=0, borderColor=None, fillColor=None, textColor=None, value='',
                         fieldFlags='readOnly', forceBorder=False, relative=False)

PAGE = [0]
def footer():
    PAGE[0] += 1
    c.setFont('R', 7.5); c.setFillColor(MUTED)
    c.drawString(M, 24, f"Fonte: TSE (resultados.tse.jus.br e dadosabertos.tse.jus.br), dados de {D['meta']['dg']} às {D['meta']['hg']}." + (' Sujeitos a reprocessamento.' if D['meta']['aviso'] else ''))
    c.drawRightString(W - M, 24, f'{PAGE[0]}')

def text(x, y, s, font='R', size=10, color=INK, width=None, lead=None):
    c.setFont(font, size); c.setFillColor(color)
    lines = simpleSplit(s, font, size, width) if width else [s]
    lead = lead or size * 1.4
    for i, l in enumerate(lines): c.drawString(x, y - i * lead, l)
    return y - len(lines) * lead

def head(y, eyebrow, h, body=None):
    c.setStrokeColor(INK); c.setLineWidth(1.5); c.line(M, y, W - M, y)
    y -= 14; text(M, y, eyebrow.upper(), 'SB', 7.5, ACC)
    y -= 20; y = text(M, y, h, 'B', 16, INK, CW, 19)
    if body: y = text(M, y - 2, body, 'R', 9.5, INK2, CW, 13.5)
    return y - 8

def hint(y, s='Passe o mouse sobre os elementos para ver os detalhes.'):
    return text(M, y, s, 'R', 8, MUTED) - 4

# ---------- mapa ----------
def draw_map(x0, y0, w, h, bbox, feats, label_ids=(), cell=2.0):
    lon0, lat0, lon1, lat1 = bbox
    k = min(w / (lon1 - lon0), h / (lat1 - lat0))
    mw, mh = (lon1 - lon0) * k, (lat1 - lat0) * k
    ox, oy = x0 + (w - mw) / 2, y0 + (h - mh) / 2
    P = lambda lo, la: (ox + (lo - lon0) * k, oy + (la - lat0) * k)
    def polys(f):
        g = f['geometry']; return [g['coordinates']] if g['type'] == 'Polygon' else g['coordinates']
    c.saveState(); p = c.beginPath(); p.rect(x0, y0, w, h); c.clipPath(p, stroke=0, fill=0)
    c.setStrokeColor(HexColor('#ffffff')); c.setLineWidth(0.4)
    for f in feats:
        m = D['mapa'].get(f['properties']['id']); v = m[1] if m else 0
        c.setFillColor(BINS[binof(v)])
        pth = c.beginPath()
        for poly in polys(f):
            for ring in poly:
                pts = [P(*pt) for pt in ring]
                pth.moveTo(*pts[0])
                for q in pts[1:]: pth.lineTo(*q)
                pth.close()
        c.drawPath(pth, fill=1, stroke=1, fillMode=0)
    c.restoreState()
    # rótulos
    for f in feats:
        if f['properties']['id'] in label_ids:
            pts = [P(*pt) for poly in polys(f) for pt in poly[0]]
            cx = sum(p[0] for p in pts) / len(pts); cy = sum(p[1] for p in pts) / len(pts)
            m = D['mapa'][f['properties']['id']]
            s = f"{f['properties']['name']} {fmt(m[1])}"
            c.setFont('SB', 6.5); tw = c.stringWidth(s, 'SB', 6.5)
            c.setFillColor(Color(1, 1, 1, alpha=0.85)); c.roundRect(cx - tw / 2 - 2, cy - 3, tw + 4, 9, 2, fill=1, stroke=0)
            c.setFillColor(INK); c.drawCentredString(cx, cy - 0.5, s)
    # áreas de dica: rasteriza e junta células por linha
    gw, gh = int(w / cell) + 1, int(h / cell) + 1
    img = Image.new('I', (gw, gh), 0); dr = ImageDraw.Draw(img)
    for i, f in enumerate(feats):
        for poly in polys(f):
            pts = [((P(*pt)[0] - x0) / cell, (y0 + h - P(*pt)[1]) / cell) for pt in poly[0]]
            if len(pts) > 2: dr.polygon(pts, fill=i + 1)
    px = img.load()
    for r in range(gh):
        cstart, cur = 0, 0
        for col in range(gw + 1):
            v = px[col, r] if col < gw else 0
            if v != cur:
                if cur:
                    f = feats[cur - 1]; m = D['mapa'].get(f['properties']['id'])
                    nm = f['properties']['name']; v26 = m[1] if m else 0
                    t = f"{nm}: {fmt(v26)} voto{'s' if v26 != 1 else ''}" + (f" ({pct(m[2])} dos válidos, {m[3]}º lugar na cidade)" if v26 else '')
                    tip(x0 + cstart * cell, y0 + h - (r + 1) * cell, (col - cstart) * cell, cell, t)
                cur, cstart = v, col

def legend(y):
    x = M
    for i, t in enumerate(['0', '1 a 9', '10 a 99', '100 a 499', '500 a 999', '1.000 ou mais']):
        c.setFillColor(BINS[i]); c.rect(x, y, 12, 8, fill=1, stroke=0)
        c.setFillColor(INK2); c.setFont('R', 8); c.drawString(x + 16, y + 1, t); x += 22 + c.stringWidth(t, 'R', 8) + 10
    c.drawString(x + 4, y + 1, 'votos por município')

# ---------- barras ----------
def bars(x, y, w, items, row=12, lw=110, vmax=None, log=False, vw=70, fs=8):
    vmax = vmax or max(i['v'] for i in items)
    bw = w - lw - vw - 6
    def L(v):
        if log: return max(2, math.log10(v / 0.7) / math.log10(vmax * 1.05 / 0.7) * bw)
        return max(2, v / vmax * bw)
    for it in items:
        if it.get('cut'):
            c.setStrokeColor(DOWN); c.setDash(3, 2); c.setLineWidth(0.8); c.line(x, y + 2, x + w, y + 2); c.setDash()
            c.setFont('R', 7); c.setFillColor(DOWN); c.drawRightString(x + w, y + 4, it['cut']); y -= 10
        hl = it.get('hl')
        c.setFont('B' if hl else 'R', fs); c.setFillColor(INK if hl else INK2)
        lb = it['lb']
        while c.stringWidth(lb, 'B' if hl else 'R', fs) > lw - 4: lb = lb[:-2] + '…' if not lb.endswith('…') else lb[:-2] + '…'
        c.drawString(x, y, lb)
        c.setFillColor(GRAY if it.get('dim') else ACC)
        bl = L(it['v']); c.rect(x + lw, y - 1.5, bl, row * 0.62, fill=1, stroke=0)
        c.setFont('SB', fs - 0.5); c.setFillColor(INK); c.drawString(x + lw + bl + 4, y, fmt(it['v']) + ('  ' if it.get('x') else ''))
        if it.get('x'):
            off = c.stringWidth(fmt(it['v']) + '  ', 'SB', fs - 0.5)
            c.setFont('R', fs - 1); c.setFillColor(MUTED); c.drawString(x + lw + bl + 4 + off, y, it['x'])
        tip(x, y - row * 0.3, w, row, it['tip'])
        y -= row
    return y

# ---------- rodapé do autor ----------
FOTO = RAIZ / 'img' / 'leo.jpg'
def autor(y):
    """Cartão "Quem desenvolveu?" com foto redonda; abre página nova se não couber."""
    larg = CW - 132
    cargo = simpleSplit('Bacharelado em Administração e Desenvolvimento de Sistemas, com mais de 20 anos de experiência na área.', 'SB', 8.8, larg)
    p1 = simpleSplit('Procurei desenvolver um relatório baseado nos dados do TSE, mostrando o panorama político do candidato para o mesmo entender os dados consolidados e gerar conhecimento agregado da campanha atual.', 'R', 8.8, larg)
    p2 = simpleSplit('Com ajuda da inteligência artificial (AI) nos mapas e gráficos, obtendo uma compreensão visual mais detalhada.', 'R', 8.8, larg)
    alt = 34 + 22 + len(cargo) * 12 + 6 + (len(p1) + len(p2)) * 12.5 + 6 + 8 + 26
    if y - alt < 50:
        footer(); c.showPage(); y = H - 50
        y = head(y, 'Sobre o relatório', 'Quem desenvolveu este relatório') - 6
    topo = y; base = y - alt
    c.setStrokeColor(LINE); c.setFillColor(HexColor('#ffffff')); c.setLineWidth(0.8); c.roundRect(M, base, CW, alt, 10, fill=1, stroke=1)
    cx, cy, r = M + 62, topo - 64, 44
    c.setFillColor(ACCS); c.circle(cx, cy, r + 4, fill=1, stroke=0)
    c.saveState(); p = c.beginPath(); p.circle(cx, cy, r); c.clipPath(p, stroke=0, fill=0)
    c.drawImage(str(FOTO), cx - r, cy - r, 2 * r, 2 * r); c.restoreState()
    x = M + 124; yy = topo - 24
    text(x, yy, 'QUEM DESENVOLVEU?', 'SB', 7.5, ACC); yy -= 22
    text(x, yy, 'Léo Ansélmo', 'B', 16, INK); yy -= 16
    for l in cargo: text(x, yy, l, 'SB', 8.8, ACC); yy -= 12
    yy -= 6
    for l in p1: text(x, yy, l, 'R', 8.8, INK2); yy -= 12.5
    yy -= 6
    for l in p2: text(x, yy, l, 'R', 8.8, INK2); yy -= 12.5
    yy -= 8
    s = 'Instagram: @leonardoanselmo79'; c.setFont('SB', 8.8); tw = c.stringWidth(s, 'SB', 8.8)
    c.setStrokeColor(LINE); c.setFillColor(HexColor('#f5f6f3')); c.roundRect(x, yy - 6, tw + 20, 18, 9, fill=1, stroke=1)
    c.setFillColor(ACC); c.drawString(x + 10, yy, s)
    c.linkURL('https://www.instagram.com/leonardoanselmo79/', (x, yy - 6, x + tw + 20, yy + 12), relative=0)
    tip(x, yy - 6, tw + 20, 18, 'Abrir o Instagram de Léo Ansélmo: https://www.instagram.com/leonardoanselmo79/')
    return base - 10

# ================= PÁGINA 1 =================
EU = '20123'
O = D['oficial']; TOT = O['ela']['v']; B = D['base']; X = D['b2']; T = X['tot']
ITA = next(m for m in D['mun'] if m[0] == 'ITAÍBA')
NE = sum(1 for x in O['lista'] if x['e']); POS = next(i for i, x in enumerate(O['lista'], 1) if x['n'] == EU)
y = H - 50
text(M, y, 'ELEIÇÕES 2026 · PERNAMBUCO · DEPUTADA ESTADUAL · 1º TURNO, 04/10/2026', 'SB', 7.5, MUTED)
y -= 34; c.setFont('B', 30); c.setFillColor(INK); c.drawString(M, y, 'Regina da Saúde'); c.setFillColor(ACC); c.drawString(M + c.stringWidth('Regina da Saúde ', 'B', 30), y, '20123')
y -= 20; y = text(M, y, f"Para onde foram os {fmt(TOT)} votos da candidata do Podemos em sua primeira eleição para deputada estadual: cidade por cidade, a base em Itaíba, de quem eram esses votos em 2022 e por quanto a vaga escapou.", 'R', 11, INK2, CW, 15)
y -= 14
K = [('Votos em Pernambuco', fmt(TOT), f"{pct(D['meta']['pvap'])} dos válidos · {D['meta']['seq']}º lugar", f"Total de votos nominais de Regina da Saúde no estado: {fmt(TOT)} ({pct(D['meta']['pvap'])} dos válidos), {D['meta']['seq']}ª colocada entre todos os candidatos a deputado estadual."),
     ('Vieram de Itaíba', pct(100 * ITA[1] / TOT), f"{fmt(ITA[1])} votos, {pct(ITA[2])} da cidade", f"Itaíba deu {fmt(ITA[1])} dos {fmt(TOT)} votos. Na cidade, ela teve {pct(ITA[2])} dos votos válidos para deputado estadual."),
     ('Resultado', O['ela']['st'], f"{POS - NE}ª da fila de suplentes do Podemos", f"O Podemos elegeu {NE} deputados estaduais. Regina foi a {POS}ª mais votada do partido e ficou como {POS - NE}ª suplente."),
     ('Votos que faltaram', fmt(O['faltaram']), 'para a última vaga do Podemos', f"O último eleito do Podemos, {title(O['ultimo']['nm'])}, teve {fmt(O['ultimo']['v'])} votos. Com {fmt(O['faltaram'])} votos a mais, Regina teria passado à frente dele.")]
kw = (CW - 3 * 8) / 4
for i, (a, b, s, t) in enumerate(K):
    x = M + i * (kw + 8)
    c.setStrokeColor(LINE); c.setFillColor(HexColor('#ffffff')); c.setLineWidth(0.8); c.roundRect(x, y - 58, kw, 58, 5, fill=1, stroke=1)
    text(x + 9, y - 14, a, 'R', 8, INK2); text(x + 9, y - 36, b, 'B', 19, INK); text(x + 9, y - 50, s, 'R', 6.8, MUTED)
    tip(x, y - 58, kw, 58, t)
y -= 80
y = head(y, '1 · Mapa', 'Os votos se concentram no Sertão do Moxotó e no Agreste', 'Cor pela quantidade de votos em cada município. Fernando de Noronha não aparece no mapa.')
y = hint(y)
legend(y - 8); y -= 18
feats = [f for f in GEO['features'] if f['properties']['id'] != '2605459']
mh = 215
draw_map(M, y - mh, CW, mh, (-41.40, -9.50, -34.80, -7.25), feats, cell=2.0)
y -= mh + 14
text(M, y, 'A região de Itaíba, ampliada, está na página seguinte.', 'R', 8.5, INK2)
footer(); c.showPage()

# ================= PÁGINA 2: zoom =================
y = H - 50
y = head(y, '1 · Mapa ampliado', 'Itaíba e a região em detalhe', 'Recorte do Sertão do Moxotó e do Agreste. Os rótulos mostram as cidades com 400 votos ou mais; as demais aparecem ao passar o mouse.')
y = hint(y); legend(y - 8); y -= 20
BB = (-38.75, -9.55, -36.55, -8.15)
lab = {k for k, v in D['mapa'].items() if v[1] >= 400}
mh = 470
draw_map(M, y - mh, CW, mh, BB, feats, label_ids=lab, cell=2.5)
y -= mh + 14
def centro(f):
    g = f['geometry']; pol = g['coordinates'] if g['type'] == 'Polygon' else g['coordinates'][0]
    return sum(p[0] for p in pol[0]) / len(pol[0]), sum(p[1] for p in pol[0]) / len(pol[0])
dentro = {f['properties']['id'] for f in feats if BB[0] < centro(f)[0] < BB[2] and BB[1] < centro(f)[1] < BB[3]}
fora = [v for k, v in sorted(D['mapa'].items(), key=lambda kv: -kv[1][1]) if v[1] >= 400 and k not in dentro]
if fora:
    text(M, y, 'Fora do recorte, com 400 votos ou mais: ' + ', '.join(f"{title(m[0])} ({fmt(m[1])})" for m in fora) + '.', 'R', 8.5, INK2, CW, 12)
footer(); c.showPage()

# ================= PÁGINAS 3 e 4: municípios =================
items = [dict(lb=title(nm), v=v, x=f"{pct(p)} · {pos}º", hl=nm == 'ITAÍBA',
              tip=f"{title(nm)}: {fmt(v)} voto{'s' if v != 1 else ''}, {pct(p)} dos válidos, {pos}º lugar na cidade · {'2º colocado' if pos == 1 else 'mais votado'}: {title(o)} ({osg}, {pct(op)})")
         for nm, v, p, pos, o, osg, op in D['mun']]
vmax = D['mun'][0][1]
partes = [items[:106], items[106:]]
for n, parte in enumerate(partes):
    y = H - 50
    if n == 0:
        y = head(y, '2 · Por município', f"{len(items)} municípios deram ao menos um voto", 'Escala logarítmica: cada marca vale 10 vezes a anterior, o que deixa visíveis as cidades com 1 voto. Ao lado de cada barra: votos, % dos válidos e a posição dela entre os candidatos da cidade.')
    else:
        y = head(y, '2 · Por município (continuação)', f"Do {107}º ao {len(items)}º município")
    y = hint(y) - 6
    half = (len(parte) + 1) // 2; colw = (CW - 16) / 2
    bars(M, y, colw, parte[:half], row=11.6, lw=92, vmax=vmax, log=True, vw=78, fs=7.1)
    bars(M + colw + 16, y, colw, parte[half:], row=11.6, lw=92, vmax=vmax, log=True, vw=78, fs=7.1)
    footer(); c.showPage()

# ================= PÁGINA 5: força nas cidades =================
Mn = D['mun']
c1 = sum(1 for m in Mn if m[3] == 1); c3 = sum(1 for m in Mn if m[3] <= 3); c5 = sum(1 for m in Mn if m[3] <= 5); c10 = sum(1 for m in Mn if m[3] <= 10)
y = H - 50
y = head(y, '3 · Força nas cidades', f"Foi a mais votada em {'1 município' if c1 == 1 else f'{c1} municípios'} e ficou entre os 3 primeiros em {c3}",
         'Posição de Regina entre todos os candidatos a deputado estadual em cada município, e quem disputou a ponta com ela. É a primeira eleição dela para deputada estadual, então não há votação anterior para comparar; a seção 5 mostra de quem eram, em 2022, os votos de Itaíba.')
x = M
for t_, n_ in [('1º lugar', c1), ('Entre os 3 primeiros', c3), ('Entre os 5 primeiros', c5), ('Entre os 10 primeiros', c10), ('Com ao menos 1 voto', len(Mn))]:
    s = f'{t_}: {n_}'; c.setFont('SB', 8); tw = c.stringWidth(s, 'SB', 8)
    c.setStrokeColor(LINE); c.setFillColor(HexColor('#ffffff')); c.roundRect(x, y - 5, tw + 14, 15, 7, fill=1, stroke=1)
    c.setFillColor(INK); c.drawString(x + 7, y, s); x += tw + 22
y -= 24
y = text(M, y, 'Os 25 municípios com mais votos. Na última coluna aparece o mais votado da cidade; onde ela ficou em 1º, aparece o 2º colocado.', 'R', 8, INK2, CW, 11) - 6
cols = [('Município', 0, 120), ('Votos', 120, 50), ('% dos válidos', 170, 62), ('Posição', 232, 45), ('Quem liderou (ou 2º, se ela foi 1ª)', 287, CW - 287)]
c.setFont('SB', 7.8); c.setFillColor(INK2)
for nm, x, w in cols:
    (c.drawString if x in (0, 287) else c.drawRightString)(M + x + (0 if x in (0, 287) else w), y, nm)
y -= 5; c.setStrokeColor(INK); c.setLineWidth(0.8); c.line(M, y, W - M, y); y -= 11
for i, (nm, v, p, pos, o, osg, op) in enumerate(Mn[:25]):
    if i % 2 == 0: c.setFillColor(HexColor('#f5f6f3')); c.rect(M, y - 3.5, CW, 13.6, fill=1, stroke=0)
    vals = [title(nm), fmt(v), pct(p), f'{pos}º', f"{title(o)} ({osg}, {pct(op)})"]
    for (cn, x, w), val in zip(cols, vals):
        c.setFont('SB' if cn == 'Posição' else 'R', 7.6); c.setFillColor(INK)
        (c.drawString if x in (0, 287) else c.drawRightString)(M + x + (0 if x in (0, 287) else w), y, val)
    tip(M, y - 3.5, CW, 13.6, f"{title(nm)}: {fmt(v)} votos ({pct(p)}), {pos}º lugar · {'2º colocado' if pos == 1 else 'mais votado'}: {title(o)} ({osg}), {pct(op)}")
    y -= 13.6
footer(); c.showPage()

# ================= PÁGINA 6: Itaíba =================
def short(n):
    p = n.split(); suf = p[-1] in ('NETO', 'FILHO', 'JUNIOR', 'JÚNIOR')
    return title(' '.join([p[0]] + p[-2:] if suf else [p[0], p[-1]]))
y = H - 50
y = head(y, '4 · Itaíba', f"Na base, {pct(ITA[2])} dos votos" + (': mais que o dobro do segundo colocado' if B['top'][0]['v'] >= 2 * B['top'][1]['v'] else ''),
         f"Em Itaíba, Regina teve {fmt(B['top'][0]['v'])} votos, {pct(B['top'][0]['p'])} dos válidos para deputado estadual. Claudiano Filho (PP), eleito suplente, teve {pct(B['top'][1]['p'])}. Dados por seção do TSE ({sum(l['secoes'] for l in B['locais'])} seções, {len(B['locais'])} locais de votação).")
y = hint(y) - 4
text(M, y, 'Mais votados para deputado estadual em Itaíba', 'B', 10); y -= 16
it = [dict(lb=f"{short(t['nm'])} {t['n']}", v=t['v'], x=pct(t['p']), hl=t['n'] == EU, dim=t['n'] != EU,
           tip=f"{title(t['nm'])} ({t['n']}): {fmt(t['v'])} votos em Itaíba, {pct(t['p'])} dos válidos") for t in B['top'][:8]]
y = bars(M, y, CW, it, row=14, lw=170, vmax=B['top'][0]['v'], fs=8.5)
text(M, y - 2, f"Válidos para deputado estadual na cidade: {fmt(B['validos'])}. Brancos: {fmt(B['brancos'])}. Nulos: {fmt(B['nulos'])}.", 'R', 7.5, MUTED); y -= 26
text(M, y, 'Votos de Regina por bairro ou distrito do local de votação', 'B', 10); y -= 16
it = [dict(lb=title(b[0]), v=b[1], x=pct(b[3]) + ' dos válidos',
           tip=f"{title(b[0])}: {fmt(b[1])} votos de Regina, {pct(b[3])} dos {fmt(b[2])} válidos, {pct(100 * b[1] / B['top'][0]['v'])} dos votos dela na cidade") for b in B['bairros']]
y = bars(M, y, CW, it, row=14, lw=170, fs=8.5) - 18
text(M, y, 'Locais de votação', 'B', 10); y -= 14
cols = [('Local de votação', 0, 220), ('Bairro ou distrito', 220, 120), ('Seções', 340, 40), ('Votos', 380, 50), ('Válidos', 430, 50), ('% válidos', 480, CW - 480)]
c.setFont('SB', 8); c.setFillColor(INK2)
for nm, x, w in cols:
    (c.drawString if x < 340 else c.drawRightString)(M + x + (0 if x < 340 else w), y, nm)
y -= 5; c.setStrokeColor(INK); c.setLineWidth(0.8); c.line(M, y, W - M, y); y -= 11
for i, l in enumerate(B['locais']):
    if i % 2 == 0: c.setFillColor(HexColor('#f5f6f3')); c.rect(M, y - 3.5, CW, 13.2, fill=1, stroke=0)
    vals = [title(l['local']), title(l['bairro']), str(l['secoes']), fmt(l['votos']), fmt(l['validos']), pct(l['pct'])]
    for (nm, x, w), v in zip(cols, vals):
        if x < 340:
            c.setFont('R', 7.4); c.setFillColor(INK)
            while c.stringWidth(v, 'R', 7.4) > w - 6: v = v[:-2] + '…'
            c.drawString(M + x, y, v)
        else:
            c.setFont('SB' if nm == 'Votos' else 'R', 7.6); c.setFillColor(INK); c.drawRightString(M + x + w, y, v)
    tip(M, y - 3.5, CW, 13.2, f"{title(l['local'])} ({title(l['bairro'])}): {fmt(l['votos'])} votos de Regina em {l['secoes']} seções, {pct(l['pct'])} dos {fmt(l['validos'])} válidos")
    y -= 13.2
footer(); c.showPage()

# ================= PÁGINA 7: Itaíba 2022 x 2026 =================
CA = HexColor('#d9622b')
p1 = lambda v: f'{v:.1f}'.replace('.', ',') + '%'
pr = 100 * T['2026']['regina'] / T['2026']['validos']; pn = 100 * T['2022']['novaes'] / T['2022']['validos']
pc22 = 100 * T['2022']['claudiano22'] / T['2022']['validos']; pc26 = 100 * T['2026']['claudiano26'] / T['2026']['validos']
y = H - 50
y = head(y, '5 · Itaíba, 2022 × 2026', 'Regina ocupou o espaço que era de Rodrigo Novaes',
         f"Em 2022, Rodrigo Novaes teve {fmt(T['2022']['novaes'])} votos em Itaíba ({pct(pn)} dos válidos para deputado estadual). Em 2026, sem Novaes na disputa, Regina teve {fmt(T['2026']['regina'])} ({pct(pr)}). Nos distritos, a fatia dela é praticamente a mesma que ele tinha; no Centro, ela foi além, e a diferença saiu de Claudiano Filho, que caiu de {pct(pc22)} para {pct(pc26)}. Todos os percentuais são sobre os válidos para deputado estadual no local, em cada ano.")
y = hint(y) - 4
c.setFillColor(GRAY); c.circle(M + 4, y + 3, 3.2, fill=1, stroke=0); text(M + 11, y, '2022', 'R', 8, INK2)
c.setFillColor(ACC); c.circle(M + 48, y + 3, 3.2, fill=1, stroke=0); text(M + 55, y, 'Regina 2026', 'R', 8, INK2)
c.setFillColor(CA); c.circle(M + 118, y + 3, 3.2, fill=1, stroke=0); text(M + 125, y, 'Claudiano 2026', 'R', 8, INK2)
text(M + 205, y, 'Números: % dos válidos em 2022 → em 2026', 'R', 8, INK2); y -= 20
lw = 128; colw = (CW - lw - 16) / 2; vmax = max(max(b[2], b[4], b[6], b[8]) for b in X['bairros']) * 1.45
text(M + lw, y, 'Novaes 2022 → Regina 2026', 'B', 9.5); text(M + lw + colw + 16, y, 'Claudiano Filho', 'B', 9.5); y -= 16
for b in X['bairros']:
    c.setFont('R', 8.3); c.setFillColor(INK2); c.drawString(M, y, title(b[0])[:26])
    for j, (a, z, cor, nm) in enumerate([(b[4], b[2], ACC, 'Novaes em 2022 e Regina em 2026'), (b[6], b[8], CA, 'Claudiano Filho')]):
        x0 = M + lw + j * (colw + 16); X1 = x0 + a / vmax * colw; X2 = x0 + z / vmax * colw
        c.setStrokeColor(LINE); c.setLineWidth(1.4); c.line(x0, y + 2.5, x0 + colw, y + 2.5)
        c.setStrokeColor(HexColor('#c9ced2')); c.setLineWidth(2.2); c.line(min(X1, X2), y + 2.5, max(X1, X2), y + 2.5)
        c.setFillColor(GRAY); c.circle(X1, y + 2.5, 3.2, fill=1, stroke=0)
        c.setFillColor(cor); c.circle(X2, y + 2.5, 3.2, fill=1, stroke=0)
        c.setFont('R', 7); c.setFillColor(INK2); c.drawString(max(X1, X2) + 6, y, p1(a) + ' → ' + p1(z))
        tip(x0, y - 4, colw, 15, f"{nm}, {title(b[0])}: {pct(a)} dos válidos em 2022, {pct(z)} em 2026")
    y -= 17
y -= 12
text(M, y, 'Por local de votação', 'B', 10); y -= 13
y = text(M, y, "Como ler: '44,9% → 55,5%' quer dizer que, de cada 100 votos válidos para deputado estadual naquele local, cerca de 45 foram para Rodrigo Novaes em 2022 e cerca de 55 para Regina em 2026.", 'R', 7.8, INK2, CW, 10.5) - 6
cols = [('Local de votação', 0, 190), ('Votos: Novaes 2022 → Regina 2026', 190, 120), ('% dos válidos: Novaes → Regina', 310, 115), ('Claudiano: % dos válidos', 425, CW - 425)]
c.setFont('SB', 7.4); c.setFillColor(INK2)
for nm, x, w in cols:
    (c.drawString if x == 0 else c.drawRightString)(M + x + (0 if x == 0 else w), y, nm)
c.setFont('R', 6.8); c.setFillColor(MUTED); c.drawRightString(M + cols[3][1] + cols[3][2], y - 9, '2022 → 2026')
y -= 14; c.setStrokeColor(INK); c.setLineWidth(0.8); c.line(M, y, W - M, y); y -= 11
for i, r in enumerate(X['locais']):
    if i % 2 == 0: c.setFillColor(HexColor('#f5f6f3')); c.rect(M, y - 3.5, CW, 12.6, fill=1, stroke=0)
    vals = [title(r[0]), f'{fmt(r[4])} → {fmt(r[2])}', f'{p1(r[5])} → {p1(r[3])}', f'{p1(r[7])} → {p1(r[9])}']
    for (nm, x, w), v in zip(cols, vals):
        c.setFont('SB' if '%' in nm or 'Claudiano' in nm else 'R', 7.2); c.setFillColor(UP if '% dos válidos: N' in nm else DOWN if 'Claudiano' in nm else INK)
        if x == 0:
            while c.stringWidth(v, 'R', 7.2) > w - 6: v = v[:-2] + '…'
            c.drawString(M, y, v)
        else:
            c.drawRightString(M + x + w, y, v)
    tip(M, y - 3.5, CW, 12.6, f"{title(r[0])} ({title(r[1])}): Novaes 2022 {fmt(r[4])} votos ({pct(r[5])}); Regina 2026 {fmt(r[2])} votos ({pct(r[3])}); Claudiano {pct(r[7])} → {pct(r[9])}")
    y -= 12.6
if X['mudaram']['2026']:
    y -= 4; y = text(M, y, 'Local novo em 2026, fora da tabela: ' + ', '.join(title(n) for n in X['mudaram']['2026']) + '.', 'R', 7.5, MUTED, CW, 10.5)
y -= 14
# dois mapas lado a lado, mesma escala
text(M, y, 'Mapa dos locais de votação: os mesmos lugares, com a mesma escala de tamanho', 'B', 10); y -= 10
L = [dict(l, x=float(l['lon'].replace(',', '.')), yy=float(l['lat'].replace(',', '.'))) for l in B['locais'] if l['lat']]
n22 = {r[0]: (r[4], r[5]) for r in X['locais']}
mh = y - 60; mw = (CW - 14) / 2
x0, x1 = min(l['x'] for l in L), max(l['x'] for l in L); y0, y1 = min(l['yy'] for l in L), max(l['yy'] for l in L)
k = min((mw - 70) / (x1 - x0), (mh - 110) / (y1 - y0))
for j, (rot, cor) in enumerate([('Regina da Saúde, 2026', ACC), ('Rodrigo Novaes, 2022', CA)]):
    bx = M + j * (mw + 14); by = y - mh
    c.setStrokeColor(LINE); c.setLineWidth(0.8); c.roundRect(bx, by, mw, mh, 6, fill=0, stroke=1)
    text(bx + 8, y - 14, rot, 'SB', 8.5, INK)
    ox = bx + (mw - (x1 - x0) * k) / 2; oy = by + 22 + (mh - 44 - (y1 - y0) * k) / 2
    for l in sorted(L, key=lambda l: -l['votos']):
        v = l['votos'] if j == 0 else n22.get(l['local'], (0, 0))[0]
        if not v: continue
        cx = ox + (l['x'] - x0) * k; cy = oy + (l['yy'] - y0) * k; rr = 2 + math.sqrt(v) * 0.32
        c.setFillColor(cor); c.setStrokeColor(HexColor('#ffffff')); c.setLineWidth(0.8); c.circle(cx, cy, rr, fill=1, stroke=1)
        a = n22.get(l['local'])
        tip(cx - rr, cy - rr, 2 * rr, 2 * rr, f"{title(l['local'])} ({title(l['bairro'])}): Regina 2026 {fmt(l['votos'])} votos ({pct(l['pct'])})" + (f"; Novaes 2022 {fmt(a[0])} votos ({pct(a[1])})" if a else '; local novo em 2026'))
    grupos = {}
    for l in L: grupos.setdefault(l['bairro'], []).append(l)
    for bnm, a in grupos.items():
        vmx = max(math.sqrt(max(l['votos'], n22.get(l['local'], (0, 0))[0])) * 0.32 + 2 for l in a)
        cx = sum(ox + (l['x'] - x0) * k for l in a) / len(a); cy = min(oy + (l['yy'] - y0) * k for l in a) - vmx - 11
        s = title(bnm).upper(); c.setFont('SB', 6.3); tw = c.stringWidth(s, 'SB', 6.3)
        c.setFillColor(Color(1, 1, 1, alpha=0.85)); c.rect(cx - tw / 2 - 2, cy - 2, tw + 4, 8.5, fill=1, stroke=0)
        c.setFillColor(INK2); c.drawCentredString(cx, cy, s)
y -= mh + 12
text(M, y, 'Tamanho do círculo: votos no local. Sem ruas ao fundo; cada círculo está na posição informada pelo TSE.', 'R', 7.5, MUTED, CW, 10.5)
footer(); c.showPage()

# ================= PÁGINA 8: seções =================
S = D['secoes']
y = H - 50
y = head(y, '6 · Por seção eleitoral', f"Voto em {fmt(len(S))} seções; as 45 com mais votos",
         f"Algumas seções pequenas não têm urna própria: os eleitores delas votam na urna de outra seção do mesmo local. O resultado sai só na seção que tem a urna (consolidada), com os eleitores das duas somados. Exemplo: em Brejão, a seção 452 (63 eleitores) votou na urna da 181 (272), que aparece com 335 aptos. {sum(1 for s in S if s[9])} das seções com voto são consolidadas. A lista completa está no site e em dados/regina_da_saude_20123_por_secao.csv.")
y = hint(y) - 6
cols = [('Município', 0, 100), ('Zona', 100, 26), ('Seção', 126, 32), ('Local de votação', 168, 196), ('Aptos', 364, 40), ('Votos', 404, 40), ('Válidos', 444, 40), ('% válidos', 484, CW - 484)]
NUM = {'Zona', 'Seção', 'Aptos', 'Votos', 'Válidos', '% válidos'}
c.setFont('SB', 7.6); c.setFillColor(INK2)
for nm, x, w in cols:
    (c.drawRightString if nm in NUM else c.drawString)(M + x + (w if nm in NUM else 0), y, nm)
y -= 5; c.setStrokeColor(INK); c.setLineWidth(0.8); c.line(M, y, W - M, y); y -= 11
for i, s in enumerate(S[:45]):
    if i % 2 == 0: c.setFillColor(HexColor('#f5f6f3')); c.rect(M, y - 3.5, CW, 12.6, fill=1, stroke=0)
    vals = [title(s[0]), str(s[1]), str(s[2]), title(s[3]), fmt(s[5]), fmt(s[6]), fmt(s[7]), pct(s[8])]
    for (nm, x, w), v in zip(cols, vals):
        c.setFont('SB' if nm == 'Votos' else 'R', 7.2); c.setFillColor(INK)
        if nm in NUM:
            c.drawRightString(M + x + w, y, v)
        else:
            while c.stringWidth(v, 'R', 7.2) > w - 6: v = v[:-2] + '…'
            c.drawString(M + x, y, v)
    ag = f" · consolidada com as seções agregadas {s[9].replace(' ', ', ')}" if s[9] else ''
    tip(M, y - 3.5, CW, 12.6, f"{title(s[0])}, zona {s[1]}, seção {s[2]} ({title(s[3])}, {title(s[4])}): {fmt(s[6])} votos de Regina, {pct(s[8])} dos {fmt(s[7])} válidos, {fmt(s[5])} eleitores aptos{ag}")
    y -= 12.6
footer(); c.showPage()

# ================= PÁGINA 9: resultado oficial =================
y = H - 50
y = head(y, '7 · Resultado oficial', f"{POS - NE}ª suplente do Podemos: a vaga escapou por {fmt(O['faltaram'])} votos",
         f"O Podemos elegeu {NE} deputados estaduais. Regina foi a {POS}ª mais votada do partido, com {fmt(O['ela']['v'])} votos. O último eleito, {title(O['ultimo']['nm'])}, teve {fmt(O['ultimo']['v'])}. Com {fmt(O['faltaram'])} votos a mais ela teria passado à frente dele. Pelas regras do sistema proporcional, as vagas são primeiro divididas entre os partidos e depois preenchidas pelos mais votados de cada um; como {POS - NE}ª suplente, ela é {'a primeira chamada' if POS - NE == 1 else 'chamada na ordem da fila'} se um eleito do Podemos deixar o cargo.")
y = hint(y) - 4
text(M, y, 'Lista do Podemos (12 mais votados)', 'B', 10); y -= 16
it = [dict(lb=f"{i + 1}. {title(k['nm'])}", v=k['v'], x=k['st'], hl=k['n'] == EU, dim=k['n'] != EU and not k['e'],
           cut=f'linha de corte: {NE} vagas do Podemos' if i == NE else '',
           tip=f"{i + 1}º no Podemos: {title(k['nm'])} ({k['n']}), {fmt(k['v'])} votos · {k['st']}") for i, k in enumerate(O['lista'])]
y = bars(M, y, CW, it, row=14, lw=170, fs=8.5) - 16
text(M, y, f"Vagas por partido ou federação ({O['nv']} no total)", 'B', 10); y -= 16
it = [dict(lb=s['nm'], v=s['v'], x=f"{s['s']} vaga{'s' if s['s'] > 1 else ''}", hl=s['nm'] == 'PODE', dim=s['nm'] != 'PODE',
           tip=f"{s['nm']}: {fmt(s['v'])} votos válidos (nominais + legenda) · {s['s']} vaga{'s' if s['s'] > 1 else ''}") for s in O['vagas']]
y = bars(M, y, CW, it, row=14, lw=170, fs=8.5) - 10
y = text(M, y, 'Resultado proclamado pelo TSE.', 'R', 8, MUTED) - 14
text(M, y, 'Fontes', 'B', 10); y -= 14
y = text(M, y, 'API de resultados do TSE (votos por município e resultado oficial, 2026): resultados.tse.jus.br/oficial/ele2026/6259/dados/pe/. Portal de Dados Abertos do TSE (dadosabertos.tse.jus.br): votação por seção e locais de votação de 2022 e 2026. Contornos dos municípios: geodata-br, a partir de malhas do IBGE.', 'R', 8.5, INK2, CW, 12)
y = autor(y - 14)
footer(); c.showPage()
c.save()
print('páginas:', PAGE[0], '· campos de dica:', NT[0])
