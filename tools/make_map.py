#!/usr/bin/env python3
"""春秋時代（呉・越・楚）の略図を、インラインSVGとして tools/map-goetsu.svg に書き出す。

海岸線と湖は basemap（GSHHS）の実データ、長江は主要都市を通る曲線、国のまとまりは目安の楕円。
使い方:  pip install basemap  →  python3 tools/make_map.py
"""
import math, os, sys
from mpl_toolkits.basemap import Basemap

LON0, LON1, LAT0, LAT1 = 110.8, 123.2, 27.6, 34.4
COS = math.cos(math.radians(31))
S = 720 / ((LON1 - LON0) * COS)
W, H = 720, round((LAT1 - LAT0) * S)


def X(lon): return (lon - LON0) * COS * S
def Y(lat): return (LAT1 - lat) * S


def path(xs, ys):
    pts = ['%.1f,%.1f' % (X(x), Y(y)) for x, y in zip(xs, ys)]
    return 'M' + 'L'.join(pts) + 'Z'


def smooth(points):
    """Catmull-Rom → Bezier"""
    P = [(X(a), Y(b)) for a, b in points]
    d = 'M%.1f,%.1f' % P[0]
    for i in range(len(P) - 1):
        p0 = P[i - 1] if i > 0 else P[i]
        p1, p2 = P[i], P[i + 1]
        p3 = P[i + 2] if i + 2 < len(P) else P[i + 1]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += 'C%.1f,%.1f %.1f,%.1f %.1f,%.1f' % (c1 + c2 + p2)
    return d


def blob(points):
    return smooth(points + [points[0], points[1]]).replace('M', 'M', 1)


m = Basemap(llcrnrlon=107, urcrnrlon=124, llcrnrlat=26, urcrnrlat=35.6, projection='cyl', resolution='i')
land, lakes = [], []
for (xs, ys), t in zip(m.coastpolygons, m.coastpolygontypes):
    if max(xs) < LON0 - 1 or min(xs) > LON1 + 1 or max(ys) < LAT0 - 1 or min(ys) > LAT1 + 1:
        continue
    if t == 1:
        land.append(path(xs, ys))
    elif t == 2 and len(xs) >= 10:
        lakes.append(path(xs, ys))

# 長江（上流→河口）：荊州・城陵磯・武漢・九江・安慶・蕪湖・南京・鎮江・江陰・河口
CHANGJIANG = [(110.6, 30.9), (111.3, 30.7), (112.25, 30.33), (112.95, 29.7), (113.15, 29.45), (113.9, 29.95), (114.3, 30.58),
              (115.0, 30.2), (116.0, 29.72), (117.05, 30.52), (117.8, 30.93), (118.4, 31.35), (118.78, 32.06), (119.45, 32.22),
              (120.3, 31.95), (121.0, 31.78), (121.9, 31.62)]

# 国のまとまり（目安）。海にはみ出す分は陸地で切り取る
STATES = {
    'chu': [(109.5, 33.4), (113.5, 34.0), (116.8, 33.4), (117.4, 31.0), (116.0, 29.0), (113.6, 27.8), (110.8, 27.5), (110.0, 29.6)],
    'go': [(118.0, 33.0), (120.2, 33.4), (122.0, 32.4), (122.0, 31.3), (121.0, 30.85), (120.1, 30.85), (119.0, 30.7), (118.2, 31.0), (117.7, 31.9)],
    'etsu': [(118.7, 30.45), (120.4, 30.6), (122.0, 30.2), (122.0, 29.2), (121.6, 28.0), (120.4, 27.5), (118.6, 27.7), (118.0, 29.0)],
}

out = []
a = out.append
a('<svg class="mapsvg" viewBox="0 0 %d %d" role="img" aria-labelledby="mapT mapD" xmlns="http://www.w3.org/2000/svg">' % (W, H))
a('<title id="mapT">春秋時代の呉・越・楚の位置</title>')
a('<desc id="mapD">長江の下流の北側に呉、その南に越、長江の中流に楚がある。呉の都は姑蘇、越は会稽山のあたり、楚の都は郢。</desc>')
a('<defs><clipPath id="landclip"><path d="%s"/></clipPath><clipPath id="frame"><rect width="%d" height="%d" rx="14"/></clipPath></defs>' % (' '.join(land), W, H))
a('<g clip-path="url(#frame)">')
a('<rect width="%d" height="%d" class="m-sea"/>' % (W, H))
a('<path d="%s" class="m-land"/>' % ' '.join(land))
for st, pts in STATES.items():
    a('<path d="%s" class="m-%s" clip-path="url(#landclip)"/>' % (blob(pts), st))
for l in lakes:
    a('<path d="%s" class="m-lake"/>' % l)
a('<path d="%s" class="m-river"/>' % smooth(CHANGJIANG))
# 国名
for txt, (lo, la), cls in [('楚', (112.4, 32.3), 'chu'), ('呉', (119.2, 32.45), 'go'), ('越', (119.6, 28.8), 'etsu')]:
    a('<text x="%.0f" y="%.0f" class="m-state m-t-%s">%s</text>' % (X(lo), Y(la), cls, txt))
# 地名ラベル
a('<text x="%.0f" y="%.0f" class="m-lbl m-river-t">長江</text>' % (X(116.55), Y(30.35)))
a('<text x="%.0f" y="%.0f" class="m-lbl m-lake-t">太湖</text>' % (X(119.55), Y(31.6)))
a('<text x="%d" y="%.0f" text-anchor="end" class="m-lbl m-sea-t">東シナ海</text>' % (W-12, Y(29.2)))
# いまの都市（目安）
for nm, (lo, la), dx, dy, anc in [('武漢', (114.3, 30.58), 0, 24, 'middle'), ('南京', (118.78, 32.06), -10, -8, 'end'),
                                  ('上海', (121.47, 31.23), 12, 6, 'start'), ('杭州', (120.16, 30.27), -12, 14, 'end')]:
    a('<circle cx="%.1f" cy="%.1f" r="4" class="m-city"/>' % (X(lo), Y(la)))
    a('<text x="%.1f" y="%.1f" text-anchor="%s" class="m-city-t">%s</text>' % (X(lo) + dx, Y(la) + dy, anc, nm))
# 番号つきの印
for n, (lo, la) in [(1, (112.25, 30.33)), (2, (120.62, 31.32)), (3, (120.1, 31.02)), (4, (120.88, 29.92))]:
    a('<g class="m-pin"><circle cx="%.1f" cy="%.1f" r="14"/><text x="%.1f" y="%.1f">%d</text></g>' % (X(lo), Y(la), X(lo), Y(la) + 6.5, n))
a('</g><rect width="%d" height="%d" rx="14" class="m-frame"/></svg>' % (W, H))

here = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(here, 'map-goetsu.svg'), 'w', encoding='utf-8') as f:
    f.write('\n'.join(out))
print('ok', W, H, 'land', len(land), 'lakes', len(lakes), 'bytes', sum(len(s) for s in out))
