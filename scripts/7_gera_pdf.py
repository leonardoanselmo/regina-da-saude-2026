"""Gera o relatório em PDF (relatorio/Izaias_Regis_5567_2026.pdf) com dicas ao passar o mouse.

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
C22 = {r[0]: r for r in D['comp']['comp']}

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
def binof(v): return 0 if not v else 1 if v < 10 else 2 if v < 50 else 3 if v < 200 else 4 if v < 1000 else 5

(RAIZ / 'relatorio').mkdir(exist_ok=True)
c = canvas.Canvas(str(RAIZ / 'relatorio' / 'Izaias_Regis_5567_2026.pdf'), pagesize=A4)
c.setTitle('Izaias Regis 5567 em 2026'); c.setAuthor('Dados: TSE'); c.setSubject('Votação para deputado federal em Pernambuco, 1º turno de 2026')
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
    c.drawString(M, 24, f"Fonte: TSE (resultados.tse.jus.br e dadosabertos.tse.jus.br), dados de {D['meta']['dg']} às {D['meta']['hg']}. Sujeitos a reprocessamento.")
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
                    v22 = C22.get(m[0] if m else '', [0, 0])[1]
                    t = f"{nm}: {fmt(v26)} voto{'s' if v26 != 1 else ''} em 2026" + (f" ({pct(m[2])} dos válidos)" if v26 else '') + f" · {fmt(v22)} em 2022"
                    tip(x0 + cstart * cell, y0 + h - (r + 1) * cell, (col - cstart) * cell, cell, t)
                cur, cstart = v, col

def legend(y):
    x = M
    for i, t in enumerate(['0', '1 a 9', '10 a 49', '50 a 199', '200 a 999', '1.000 ou mais']):
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

# ================= PÁGINA 1 =================
y = H - 50
text(M, y, 'ELEIÇÕES 2026 · PERNAMBUCO · DEPUTADO FEDERAL · 1º TURNO, 04/10/2026', 'SB', 7.5, MUTED)
y -= 34; c.setFont('B', 30); c.setFillColor(INK); c.drawString(M, y, 'Izaias Regis'); c.setFillColor(ACC); c.drawString(M + c.stringWidth('Izaias Regis ', 'B', 30), y, '5567')
y -= 20; y = text(M, y, 'Para onde foram os 11.673 votos do candidato do PSD: cidade por cidade, comparação com 2022, o mapa dentro de Garanhuns e a distância até uma vaga na Câmara.', 'R', 11, INK2, CW, 15)
y -= 6
warn = f"Dados do TSE de {D['meta']['dg']} às {D['meta']['hg']}. O TSE marca a totalização com o aviso \"{D['meta']['aviso']}\". Os números ainda podem mudar e nenhum eleito foi proclamado."
wl = simpleSplit(warn, 'R', 8.5, CW - 20)
c.setFillColor(WARNBG); c.roundRect(M, y - len(wl) * 12 - 6, CW, len(wl) * 12 + 12, 4, fill=1, stroke=0)
yy = text(M + 10, y - 6, warn, 'R', 8.5, WARNINK, CW - 20, 12); y = yy - 14
K = [('Votos em Pernambuco', '11.673', '0,22% dos válidos · 62º lugar', 'Total de votos nominais de Izaias Regis no estado: 11.673 (0,22% dos válidos), 62º colocado entre todos os candidatos.'),
     ('Vieram de Garanhuns', '71,9%', '8.397 votos, 11,65% da cidade', 'Garanhuns deu 8.397 dos 11.673 votos (71,9%). Na cidade, ele teve 11,65% dos votos válidos para deputado federal.'),
     ('Em 2022 (dep. estadual)', '27.104', '-57% de um pleito para o outro', 'Em 2022 foi eleito deputado estadual pelo PSDB (45678) com 27.104 votos. Em 2026 teve 11.673, queda de 57%.'),
     ('Votos a mais para se eleger', '~86.900', 'estimativa · ver página 10', 'Estimativa: o PSD deve ficar com 2 vagas. O último eleito estimado do partido, Guilherme Uchoa Junior, teve 98.569 votos, 86.896 a mais que Izaias.')]
kw = (CW - 3 * 8) / 4
for i, (a, b, s, t) in enumerate(K):
    x = M + i * (kw + 8)
    c.setStrokeColor(LINE); c.setFillColor(HexColor('#ffffff')); c.setLineWidth(0.8); c.roundRect(x, y - 58, kw, 58, 5, fill=1, stroke=1)
    text(x + 9, y - 14, a, 'R', 8, INK2); text(x + 9, y - 36, b, 'B', 19, INK); text(x + 9, y - 50, s, 'R', 7, MUTED)
    tip(x, y - 58, kw, 58, t)
y -= 80
y = head(y, '1 · Mapa', 'Os votos se concentram no Agreste Meridional', 'Cor pela quantidade de votos em cada município. Fernando de Noronha (0 votos) não aparece no mapa.')
y = hint(y)
legend(y - 8); y -= 18
feats = [f for f in GEO['features'] if f['properties']['id'] != '2605459']
mh = 215
draw_map(M, y - mh, CW, mh, (-41.40, -9.50, -34.80, -7.25), feats, cell=2.0)
y -= mh + 14
text(M, y, 'O mapa do Agreste Meridional, ampliado, está na página seguinte.', 'R', 8.5, INK2)
footer(); c.showPage()

# ================= PÁGINA 2: zoom =================
y = H - 50
y = head(y, '1 · Mapa ampliado', 'Garanhuns e vizinhos em detalhe', 'Recorte do Agreste Meridional. Os rótulos mostram as cidades com mais votos; as demais aparecem ao passar o mouse.')
y = hint(y); legend(y - 8); y -= 20
lab = {k for k, v in D['mapa'].items() if v[1] >= 90 and v[0] not in ('RECIFE', 'JABOATÃO DOS GUARARAPES', 'CARUARU', 'GRAVATÁ')}
mh = 520
draw_map(M, y - mh, CW, mh, (-37.15, -9.45, -35.75, -8.30), feats, label_ids=lab, cell=2.5)
y -= mh + 14
text(M, y, 'Cidades em destaque fora do recorte: Recife (418), Caruaru (207), Jaboatão dos Guararapes (188) e Gravatá (139).', 'R', 8.5, INK2)
footer(); c.showPage()

# ================= PÁGINA 3: municípios =================
y = H - 50
y = head(y, '2 · Por município', '106 municípios deram ao menos um voto', 'Escala logarítmica: cada marca vale 10 vezes a anterior, o que deixa visíveis as cidades com 1 voto. O número ao lado de cada barra é o valor exato; a % é sobre os votos válidos no município.')
y = hint(y) - 6
items = []
for nm, v, p in D['mun']:
    v22 = C22.get(nm, [0, 0])[1]
    items.append(dict(lb=title(nm), v=v, x=pct(p), hl=nm == 'GARANHUNS', tip=f"{title(nm)}: {fmt(v)} voto{'s' if v != 1 else ''} ({pct(p)} dos válidos) · 2022: {fmt(v22)} ({sgn(v - v22)})"))
half = 53; colw = (CW - 16) / 2
bars(M, y, colw, items[:half], row=11.6, lw=96, vmax=8397, log=True, vw=62, fs=7.3)
bars(M + colw + 16, y, colw, items[half:], row=11.6, lw=96, vmax=8397, log=True, vw=62, fs=7.3)
footer(); c.showPage()

# ================= PÁGINA 4: 2022 x 2026 =================
y = H - 50
y = head(y, '3 · 2022 × 2026', 'Queda de 27.104 para 11.673 votos, puxada por Garanhuns',
         'Em 2022 ele foi eleito deputado estadual pelo PSDB (número 45678, eleito por média). Em 2026 disputou deputado federal pelo PSD. Como os cargos são diferentes, a comparação mostra onde o eleitorado dele se manteve, não um confronto direto.')
y = hint(y) - 4
def dumb(y, rows, vmax, lw=130):
    tw = CW - lw - 60
    for nm, a, b, d in rows:
        c.setFont('R', 8.3); c.setFillColor(INK2); c.drawString(M, y, title(nm))
        x1 = M + lw + a / vmax * tw; x2 = M + lw + b / vmax * tw
        c.setStrokeColor(LINE); c.setLineWidth(1.6); c.line(M + lw, y + 2.5, M + lw + tw, y + 2.5)
        c.setStrokeColor(HexColor('#c9ced2')); c.setLineWidth(2.2); c.line(min(x1, x2), y + 2.5, max(x1, x2), y + 2.5)
        c.setFillColor(GRAY); c.circle(x1, y + 2.5, 3.2, fill=1, stroke=0)
        c.setFillColor(ACC); c.circle(x2, y + 2.5, 3.2, fill=1, stroke=0)
        c.setFont('SB', 8); c.setFillColor(UP if d > 0 else DOWN if d < 0 else INK); c.drawRightString(W - M, y, sgn(d))
        tip(M, y - 4, CW, 14, f"{title(nm)}: {fmt(a)} votos em 2022 (dep. estadual) · {fmt(b)} em 2026 (dep. federal) · variação {sgn(d)}")
        y -= 15
    return y
c.setFillColor(GRAY); c.circle(M + 4, y + 3, 3.2, fill=1, stroke=0); text(M + 11, y, '2022', 'R', 8, INK2)
c.setFillColor(ACC); c.circle(M + 48, y + 3, 3.2, fill=1, stroke=0); text(M + 55, y, '2026', 'R', 8, INK2)
text(M + 95, y, 'Coluna da direita: variação de votos', 'R', 8, INK2); y -= 18
text(M, y, 'Garanhuns', 'B', 10); y -= 15
g = C22['GARANHUNS']; y = dumb(y, [g], 24000)
text(M, y, '22.381 votos em 2022 · 8.397 em 2026 (-62%). Escala própria: de 0 a 24.000 votos.', 'R', 7.5, MUTED); y -= 20
text(M, y, 'Demais cidades (as 24 maiores somando os dois anos)', 'B', 10); y -= 15
others = [r for r in D['comp']['comp'] if r[0] != 'GARANHUNS'][:24]
y = dumb(y, others, max(max(r[1], r[2]) for r in others) * 1.05)
text(M, y, 'Escala de 0 a 750 votos.', 'R', 7.5, MUTED); y -= 22
comp = D['comp']['comp']
gan = sorted([r for r in comp if r[3] > 0], key=lambda r: -r[3])[:8]; per = sorted(comp, key=lambda r: r[3])[:8]
colw = (CW - 20) / 2
for j, (ttl, lst) in enumerate([('Onde cresceu', gan), ('Onde mais caiu', per)]):
    x = M + j * (colw + 20); yy = y
    text(x, yy, ttl, 'B', 10); yy -= 14
    for r in lst:
        c.setFont('R', 8.3); c.setFillColor(INK2); c.drawString(x, yy, title(r[0]))
        c.setFont('SB', 8.3); c.setFillColor(UP if r[3] > 0 else DOWN); c.drawRightString(x + colw, yy, sgn(r[3]))
        tip(x, yy - 3, colw, 12, f"{title(r[0])}: {fmt(r[1])} em 2022 · {fmt(r[2])} em 2026 · {sgn(r[3])}")
        yy -= 12
n22 = sum(1 for r in comp if r[1] > 0); n26 = sum(1 for r in comp if r[2] > 0)
y -= 14 + 8 * 12 + 8
text(M, y, f"Alcance: em 2022 teve voto em {n22} municípios; em 2026, em {n26}. Fora de Garanhuns, passou de {fmt(D['comp']['tot22'] - g[1])} para {fmt(11673 - g[2])} votos.", 'R', 9, INK2, CW, 13)
footer(); c.showPage()

# ================= PÁGINA 5: Garanhuns =================
G = D['gar']
y = H - 50
y = head(y, '4 · Garanhuns', 'Na própria cidade, ficou em 2º, bem atrás de Felipe Carreras',
         'Ex-prefeito de Garanhuns, Izaias teve 11,65% dos válidos para deputado federal na cidade. Felipe Carreras (PSB) teve 38,1%. Dados por seção do TSE (292 seções, 44 locais de votação).')
y = hint(y) - 4
def short(n):
    p = n.split(); suf = p[-1] in ('NETO', 'FILHO', 'JUNIOR', 'JÚNIOR')
    return title(' '.join([p[0]] + p[-2:] if suf else [p[0], p[-1]]))
text(M, y, 'Mais votados para deputado federal em Garanhuns', 'B', 10); y -= 16
it = [dict(lb=f"{short(t['nm'])} {t['n']}", v=t['v'], x=pct(t['p']), hl=t['n'] == '5567', dim=t['n'] != '5567',
           tip=f"{title(t['nm'])} ({t['n']}): {fmt(t['v'])} votos em Garanhuns, {pct(t['p'])} dos válidos") for t in G['top']]
y = bars(M, y, CW, it, row=14, lw=170, vmax=G['top'][0]['v'], fs=8.5)
text(M, y - 2, f"Válidos para deputado federal na cidade: {fmt(G['validos'])}. Brancos: {fmt(G['brancos'])}. Nulos: {fmt(G['nulos'])}.", 'R', 7.5, MUTED); y -= 26
text(M, y, 'Votos de Izaias por bairro do local de votação', 'B', 10); y -= 16
it = [dict(lb=title(b[0]), v=b[1], x=pct(b[3]) + ' dos válidos',
           tip=f"Bairro {title(b[0])}: {fmt(b[1])} votos de Izaias, {pct(b[3])} dos {fmt(b[2])} válidos, {pct(b[1] / 8397 * 100)} dos votos dele na cidade") for b in G['bairros']]
y = bars(M, y, CW, it, row=14, lw=170, fs=8.5)
hb = G['bairros'][0]
text(M, y - 2, f"{title(hb[0])} concentra {pct(100 * hb[1] / sum(l['votos'] for l in G['locais']))} dos votos dele na cidade.", 'R', 7.5, MUTED)
footer(); c.showPage()

# ================= PÁGINA 6: locais =================
y = H - 50
y = head(y, '4 · Garanhuns por local de votação', '44 locais de votação, ordenados por votos de Izaias')
y = hint(y) - 6
cols = [('Local de votação', 0, 230), ('Bairro', 230, 120), ('Seções', 350, 40), ('Votos', 390, 45), ('Válidos', 435, 45), ('% válidos', 480, CW - 480)]
c.setFont('SB', 8); c.setFillColor(INK2)
for nm, x, w in cols:
    (c.drawString if x < 350 else c.drawRightString)(M + x + (0 if x < 350 else w), y, nm)
y -= 5; c.setStrokeColor(INK); c.setLineWidth(0.8); c.line(M, y, W - M, y); y -= 11
for i, l in enumerate(G['locais']):
    if i % 2 == 0: c.setFillColor(HexColor('#f5f6f3')); c.rect(M, y - 3.5, CW, 13.2, fill=1, stroke=0)
    vals = [title(l['local']), title(l['bairro']), str(l['secoes']), fmt(l['votos']), fmt(l['validos']), pct(l['pct'])]
    for (nm, x, w), v in zip(cols, vals):
        if x < 350:
            c.setFont('R', 7.4); c.setFillColor(INK)
            while c.stringWidth(v, 'R', 7.4) > w - 6: v = v[:-2] + '…'
            c.drawString(M + x, y, v)
        else:
            c.setFont('SB' if nm == 'Votos' else 'R', 7.6); c.setFillColor(INK); c.drawRightString(M + x + w, y, v)
    tip(M, y - 3.5, CW, 13.2, f"{title(l['local'])} ({title(l['bairro'])}): {fmt(l['votos'])} votos de Izaias em {l['secoes']} seções, {pct(l['pct'])} dos {fmt(l['validos'])} válidos")
    y -= 13.2
footer(); c.showPage()

# ================= PÁGINAS 7 e 8: Garanhuns 2022 x 2026 =================
X = D['g2']; T = X['tot']
CA = HexColor('#d9622b')
def pp(v): return ('+' if v > 0 else '-' if v < 0 else '') + f'{abs(v):.1f}'.replace('.', ',') + ' p.p.'
piz22 = 100 * T['2022']['iz'] / T['2022']['val_iz']; piz26 = 100 * T['2026']['iz'] / T['2026']['val_iz']
pca22 = 100 * T['2022']['ca'] / T['2022']['val_fed']; pca26 = 100 * T['2026']['ca'] / T['2026']['val_fed']
y = H - 50
y = head(y, '5 · Garanhuns, 2022 × 2026', 'Izaias perdeu espaço em todos os bairros, e Felipe Carreras cresceu em todos',
         f"Na cidade, Izaias foi de {fmt(T['2022']['iz'])} votos ({pct(piz22)} dos válidos) para {fmt(T['2026']['iz'])} ({pct(piz26)}). Felipe Carreras foi de {fmt(T['2022']['ca'])} ({pct(pca22)}) para {fmt(T['2026']['ca'])} ({pct(pca26)}). Nos {len(X['locais'])} locais que existiam nas duas eleições, a queda de um e a alta do outro andam juntas, mas não de forma exata (correlação de {str(X['cor']).replace('.', ',')} entre as variações em pontos percentuais). Em 2022 Izaias disputou deputado estadual; Carreras disputou deputado federal nas duas. Cada percentual é sobre os válidos do cargo disputado no ano.")
y = hint(y) - 4
c.setFillColor(GRAY); c.circle(M + 4, y + 3, 3.2, fill=1, stroke=0); text(M + 11, y, '2022', 'R', 8, INK2)
c.setFillColor(ACC); c.circle(M + 48, y + 3, 3.2, fill=1, stroke=0); text(M + 55, y, 'Izaias 2026', 'R', 8, INK2)
c.setFillColor(CA); c.circle(M + 118, y + 3, 3.2, fill=1, stroke=0); text(M + 125, y, 'Carreras 2026', 'R', 8, INK2)
text(M + 200, y, 'Números: % dos válidos em 2022 → em 2026', 'R', 8, INK2); y -= 20
B = sorted([b for b in X['bairros'] if b[1] > 0], key=lambda b: -b[2])
lw = 128; colw = (CW - lw - 16) / 2; vmax = max(max(b[3], b[4], b[7], b[8]) for b in B) * 1.45
text(M + lw, y, 'Izaias', 'B', 9.5); text(M + lw + colw + 16, y, 'Felipe Carreras', 'B', 9.5); y -= 16
for b in B:
    c.setFont('R', 8.3); c.setFillColor(INK2); c.drawString(M, y, title(b[0])[:26])
    for j, (a, z, cor, nm) in enumerate([(b[3], b[4], ACC, 'Izaias'), (b[7], b[8], CA, 'Felipe Carreras')]):
        x0 = M + lw + j * (colw + 16); X1 = x0 + a / vmax * colw; X2 = x0 + z / vmax * colw
        c.setStrokeColor(LINE); c.setLineWidth(1.4); c.line(x0, y + 2.5, x0 + colw, y + 2.5)
        c.setStrokeColor(HexColor('#c9ced2')); c.setLineWidth(2.2); c.line(min(X1, X2), y + 2.5, max(X1, X2), y + 2.5)
        c.setFillColor(GRAY); c.circle(X1, y + 2.5, 3.2, fill=1, stroke=0)
        c.setFillColor(cor); c.circle(X2, y + 2.5, 3.2, fill=1, stroke=0)
        c.setFont('R', 7); c.setFillColor(INK2); c.drawString(max(X1, X2) + 6, y, f"{a:.1f}".replace('.', ',') + '% → ' + f"{z:.1f}".replace('.', ',') + '%')
        tip(x0, y - 4, colw, 15, f"{nm} em {title(b[0])}: {pct(a)} dos válidos em 2022, {pct(z)} em 2026 ({pp(z - a)})")
    y -= 17
y -= 10
text(M, y, 'Locais de votação que existiam nas duas eleições, ordenados pela queda de Izaias', 'B', 10); y -= 13
y = text(M, y, "Como ler: '27,9% → 6,3%' quer dizer que, de cada 100 votos válidos naquele local, cerca de 28 foram para o candidato em 2022 e cerca de 6 em 2026. Os percentuais permitem comparar locais que mudaram de tamanho entre as eleições.", 'R', 7.8, INK2, CW, 10.5) - 6
cols = [('Local de votação (2026)', 0, 175), ('Izaias: votos', 175, 72), ('Izaias: % dos válidos', 247, 92), ('Carreras: votos', 339, 84), ('Carreras: % dos válidos', 423, CW - 423)]
def cabecalho(y):
    c.setFont('SB', 7.6); c.setFillColor(INK2)
    for nm, x, w in cols:
        (c.drawString if x == 0 else c.drawRightString)(M + x + (0 if x == 0 else w), y, nm)
    c.setFont('R', 6.8); c.setFillColor(MUTED)
    for nm, x, w in cols[1:]:
        c.drawRightString(M + x + w, y - 9, '2022 → 2026')
    y -= 14; c.setStrokeColor(INK); c.setLineWidth(0.8); c.line(M, y, W - M, y); return y - 11
y = cabecalho(y)
LOC = sorted(X['locais'], key=lambda r: r[10] - r[9])
def linha_local(r, y, i):
    if i % 2 == 0: c.setFillColor(HexColor('#f5f6f3')); c.rect(M, y - 3.5, CW, 12.6, fill=1, stroke=0)
    p1 = lambda v: f'{v:.1f}'.replace('.', ',') + '%'
    vals = [title(r[0]), f'{fmt(r[2])} → {fmt(r[3])}', f'{p1(r[9])} → {p1(r[10])}', f'{fmt(r[4])} → {fmt(r[5])}', f'{p1(r[11])} → {p1(r[12])}']
    for (nm, x, w), v in zip(cols, vals):
        c.setFont('SB' if '%' in nm else 'R', 7.2); c.setFillColor(DOWN if nm == 'Izaias: % dos válidos' else UP if nm == 'Carreras: % dos válidos' else INK)
        if x == 0:
            while c.stringWidth(v, 'R', 7.2) > w - 6: v = v[:-2] + '…'
            c.drawString(M, y, v)
        else:
            c.drawRightString(M + x + w, y, v)
    antes = f" (em 2022: {title(r[8])})" if r[8] else ''
    tip(M, y - 3.5, CW, 12.6, f"{title(r[0])}{antes}, {title(r[1])}: Izaias {fmt(r[2])} -> {fmt(r[3])} votos ({pct(r[9])} -> {pct(r[10])}); Carreras {fmt(r[4])} -> {fmt(r[5])} ({pct(r[11])} -> {pct(r[12])})")
for i, r in enumerate(LOC[:12]):
    linha_local(r, y, i); y -= 12.6
footer(); c.showPage()

y = H - 50
y = head(y, '5 · Garanhuns, 2022 × 2026 (continuação)', 'Demais locais e mapa dos locais de votação')
y = hint(y) - 4
y = cabecalho(y)
for i, r in enumerate(LOC[12:]):
    linha_local(r, y, i); y -= 12.6
y -= 4
y = text(M, y, f"Locais que existiam só em 2022 ({', '.join(title(n) for n in X['mudaram']['2022'])}) somaram {fmt(X['resto']['2022'][0])} votos de Izaias; locais novos em 2026 ({', '.join(title(n) for n in X['mudaram']['2026'])}) somaram {fmt(X['resto']['2026'][0])}.", 'R', 7.5, MUTED, CW, 10.5) - 10
# mapa dos locais (área urbana), círculo = votos 2026, cor = % 2026
text(M, y, 'Mapa dos locais de votação (área urbana)', 'B', 10)
GV = [HexColor(h) for h in ['#c9dbf5', '#86ade6', '#3f78d0', '#173f8c']]
lx = M + 210
for i, tx in enumerate(['até 8%', '8 a 11%', '11 a 14%', '14% ou mais']):
    c.setFillColor(GV[i]); c.circle(lx + 4, y + 3, 4, fill=1, stroke=0); text(lx + 11, y, tx, 'R', 7.5, INK2); lx += 20 + c.stringWidth(tx, 'R', 7.5)
y -= 8
L = [dict(l, x=float(l['lon'].replace(',', '.')), yy=float(l['lat'].replace(',', '.'))) for l in G['locais'] if l['lat']]
urb = [l for l in L if -8.93 < l['yy'] < -8.85]; dist = [l for l in L if l not in urb]
mh = y - 70; mw = CW
x0, x1 = min(l['x'] for l in urb), max(l['x'] for l in urb); y0, y1 = min(l['yy'] for l in urb), max(l['yy'] for l in urb)
k = min((mw - 60) / (x1 - x0), (mh - 60) / (y1 - y0)); ox = M + (mw - (x1 - x0) * k) / 2; oy = (y - mh) + (mh - (y1 - y0) * k) / 2
c.setStrokeColor(LINE); c.setLineWidth(0.8); c.roundRect(M, y - mh, mw, mh, 6, fill=0, stroke=1)
dm = {r[0]: r for r in X['locais']}
for l in sorted(urb, key=lambda l: -l['votos']):
    cx = ox + (l['x'] - x0) * k; cy = oy + (l['yy'] - y0) * k; rr = 2 + math.sqrt(l['votos']) * 0.5
    p_ = l['pct']; c.setFillColor(GV[0 if p_ < 8 else 1 if p_ < 11 else 2 if p_ < 14 else 3])
    c.setStrokeColor(HexColor('#ffffff')); c.setLineWidth(0.8); c.circle(cx, cy, rr, fill=1, stroke=1)
    d = dm.get(l['local'])
    tip(cx - rr, cy - rr, 2 * rr, 2 * rr, f"{title(l['local'])} ({title(l['bairro'])}): {fmt(l['votos'])} votos, {pct(l['pct'])} dos válidos" + (f"; em 2022: {fmt(d[2])} votos ({pct(d[9])} dos válidos)" if d is not None else '; local novo em 2026'))
cent = {}
for l in urb: cent.setdefault(l['bairro'], []).append(l)
for bnm, a in cent.items():
    if len(a) < 2: continue
    cx = sum(ox + (l['x'] - x0) * k for l in a) / len(a); cy = max(oy + (l['yy'] - y0) * k for l in a) + 12
    s = title(bnm).upper(); c.setFont('SB', 6.5); tw = c.stringWidth(s, 'SB', 6.5)
    c.setFillColor(Color(1, 1, 1, alpha=0.8)); c.rect(cx - tw / 2 - 2, cy - 2, tw + 4, 8.5, fill=1, stroke=0)
    c.setFillColor(INK2); c.drawCentredString(cx, cy, s)
y -= mh + 12
text(M, y, 'Tamanho do círculo: votos de Izaias em 2026. Fora do recorte, nos distritos: ' + ', '.join(f"{title(l['bairro'].replace('DISTRITO DE ', ''))} ({fmt(l['votos'])} votos, {pct(l['pct'])})" for l in dist) + '.', 'R', 7.5, MUTED, CW, 10.5)
footer(); c.showPage()

# ================= PÁGINA 7: seções =================
S = D['secoes']
y = H - 50
y = head(y, '6 · Por seção eleitoral', f"Voto em {fmt(len(S))} seções; as 45 com mais votos",
         f"Algumas seções pequenas não têm urna própria: os eleitores delas votam na urna de outra seção do mesmo local. O resultado sai só na seção que tem a urna (consolidada), com os eleitores das duas somados. Exemplo: em Brejão, a seção 452 (63 eleitores) votou na urna da 181 (272), que aparece com 335 aptos. {sum(1 for s in S if s[9])} das seções com voto são consolidadas. A lista completa está no site e em dados/izaias_regis_5567_por_secao.csv.")
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
    tip(M, y - 3.5, CW, 12.6, f"{title(s[0])}, zona {s[1]}, seção {s[2]} ({title(s[3])}, {title(s[4])}): {fmt(s[6])} votos de Izaias, {pct(s[8])} dos {fmt(s[7])} válidos, {fmt(s[5])} eleitores aptos{ag}")
    y -= 12.6
footer(); c.showPage()

# ================= PÁGINA 8: PSD =================
y = H - 50
y = head(y, '7 · Quanto faltou', '7º colocado na lista do PSD, que deve ficar com 2 vagas',
         'O TSE ainda não marcou os eleitos (a totalização está em reprocessamento). Recalculei a distribuição das 25 vagas com o quociente eleitoral do TSE (210.580) e as regras de sobras: partido com 80% do quociente e candidato com 20%. Pelo cálculo, o PSD fica com 2 cadeiras. Para ser eleito, Izaias precisaria de cerca de 86.900 votos a mais, o suficiente para passar Guilherme Uchoa Junior (98.569). Para o PSD conquistar uma 3ª cadeira, o partido precisaria de cerca de 87.700 votos a mais no total.')
y = hint(y) - 4
text(M, y, 'Lista do PSD (12 mais votados)', 'B', 10); y -= 16
P = D['psd']; top = P[0]['v']
it = []
for i, k in enumerate(P):
    st = 'eleito (estimativa)' if i < 2 else f'{i - 1}º suplente (estimativa)'
    gap = '' if i < 2 else f" · faltariam {fmt(P[1]['v'] - k['v'] + 1)} votos para passar o 2º da lista"
    it.append(dict(lb=f"{i + 1}. {title(k['nm'])}", v=k['v'], hl=k['n'] == '5567', dim=k['n'] != '5567' and i >= 2,
                   cut='linha de corte estimada: 2 vagas' if i == 2 else '', tip=f"{i + 1}º no PSD: {title(k['nm'])} ({k['n']}), {fmt(k['v'])} votos · {st}{gap}"))
y = bars(M, y, CW, it, row=14, lw=170, fs=8.5) - 16
text(M, y, 'Vagas estimadas por partido ou federação', 'B', 10); y -= 16
QE = D['meta']['qe']
it = [dict(lb=s['nm'], v=s['v'], x=f"{s['s']} vaga{'s' if s['s'] > 1 else ''}", hl=s['nm'] == 'PSD', dim=s['nm'] != 'PSD',
           tip=f"{s['nm']}: {fmt(s['v'])} votos válidos (nominais + legenda) · quociente partidário {s['v'] // QE} · {s['s']} vaga{'s' if s['s'] > 1 else ''} estimada{'s' if s['s'] > 1 else ''}") for s in D['seats']]
y = bars(M, y, CW, it, row=14, lw=170, fs=8.5) - 10
y = text(M, y, 'Estimativa própria a partir dos votos publicados. O resultado oficial é o que o TSE proclamar.', 'R', 8, MUTED) - 14
text(M, y, 'Fontes', 'B', 10); y -= 14
y = text(M, y, 'API de resultados do TSE (votos por município, 2026): resultados.tse.jus.br/oficial/ele2026/6259/dados/pe/. Portal de Dados Abertos do TSE (dadosabertos.tse.jus.br): votação por seção e locais de votação de 2026; votação por município de 2022. Contornos dos municípios: geodata-br, a partir de malhas do IBGE.', 'R', 8.5, INK2, CW, 12)
y -= 22
c.setStrokeColor(LINE); c.setLineWidth(0.8); c.line(M, y + 8, W - M, y + 8)
text(M, y - 6, 'Desenvolvido pelo Engenheiro de IA Léo Ansélmo', 'SB', 10, INK)
footer(); c.showPage()
c.save()
print('campos de dica:', NT[0])
