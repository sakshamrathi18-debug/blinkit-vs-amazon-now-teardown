import csv,re,sys,collections,statistics as st
sys.path.insert(0,'tool')
import qc_audit as q
rows=[r for r in csv.DictReader(open('data/screens.csv')) if r['source']!='deleted' and r['xml']]
BL=q.APPS['blinkit']; AM=q.APPS['amazon']
def nodes(r):
    try: return q.nodes_of(open('data/'+r['xml']).read())
    except Exception: return []
def vis(n): return q.area(n)>0 and n['t']<2300
inside=lambda m,n: n['l']<=m['l'] and m['r']<=n['r'] and n['t']<=m['t'] and m['b']<=n['b']
print("== BLINKIT result grid per query (first capture with cards)")
seen=set()
for r in rows:
    if r['app']!='blinkit' or 'results' not in r['screen'].lower(): continue
    N=[n for n in nodes(r) if n['pkg']==BL and vis(n)]
    cards=sorted([n for n in N if 'is available for' in q.label(n) and n['clickable']],key=lambda n:(n['t'],n['l']))
    if not cards: continue
    key=r['screen'].split(':')[-1].strip()
    tag='' if key not in seen else '(scroll)'
    if key in seen: continue
    seen.add(key)
    print('##',r['id'],key)
    for c in cards[:9]:
        kids=[q.label(m) for m in N if m is not c and inside(m,c) and q.label(m)]
        ad='AD' if 'Ad' in kids else ''
        be='BOUGHT' if any('Bought Earlier' in k for k in kids) else ''
        left=[k for k in kids if re.fullmatch(r'\d+ left',k)]
        unit=[k for k in kids if re.search(r'/(kg|100 ?g|pack|ml|100 ?ml|pc)',k)]
        print('  ',c['t'],c['l'],q.label(c)[:72].replace(' is available for',' ='),ad,be,left,unit,'opts' if any('option' in k for k in kids) else '')
print("== N left distribution blinkit"); c=collections.Counter()
for r in rows:
    if r['app']=='blinkit':
        for n in nodes(r):
            if vis(n) and re.fullmatch(r'\d+ left',q.label(n)): c[q.label(n)]+=1
print(sorted(c.items()))
print("== blinkit cards with/without N left, in viewport")
tot=lef=0
for r in rows:
    if r['app']=='blinkit' and r['scenario'] not in('livecheck',):
        N=[n for n in nodes(r) if vis(n)]
        cc=[n for n in N if 'is available for' in q.label(n) and n['clickable']]
        for c_ in cc:
            tot+=1
            if any(re.fullmatch(r'\d+ left',q.label(m)) and inside(m,c_) for m in N): lef+=1
print('cards',tot,'with N left',lef, round(lef/max(tot,1),3))
print("== candle trail: any capture mentioning Pranah with left/ad")
for r in rows:
    if r['app']=='blinkit':
        N=nodes(r)
        for c_ in N:
            if 'Jar Candle by Pranah' in q.label(c_) and q.area(c_)>0:
                kids=[q.label(m) for m in N if inside(m,c_) and q.label(m) and m is not c_]
                print(r['timestamp'][11:19],r['id'],q.label(c_)[:60],[k for k in kids if re.search('left|Ad|stock',k)]); break
print("== shipment strings"); S=collections.Counter()
for r in rows:
    for n in nodes(r):
        if 'Shipment of' in q.label(n): S[(r['id'],q.label(n))]+=1
print(sorted(S))
print("== reorder surfaces per app (labels)")
pat=re.compile(r'(order again|buy again|buy it again|reorder|previously|bought earlier|frequently bought|your favou?rites|favourites)',re.I)
C=collections.Counter()
for r in rows:
    surf='now' if r['app']=='amazon' and r['scenario']!='store_price_check' else r['app'] if r['app']=='blinkit' else 'store'
    for n in nodes(r):
        m=pat.search(q.label(n))
        if m and q.area(n)>0: C[(surf,m.group(1).lower())]+=1
print(sorted(C.items()))
print("== unit price labels by surface")
U=collections.Counter(); F=collections.Counter()
for r in rows:
    surf='blinkit' if r['app']=='blinkit' else ('store' if r['scenario']=='store_price_check' else 'amazon')
    F[surf]+=1
    for n in nodes(r):
        if q.area(n)>0 and re.search(r'₹[\d.,]+ ?/ ?(kg|100 ?g|pack|ml|100 ?ml|count|pc)',q.label(n)): U[surf]+=1
print(U,F)
print("== where the bill sits: frames in checkout scrolls with Bill labels and top y")
for r in rows:
    if 'checkout' in r['screen'].lower() and r['scenario'] in('explorer','exact_item','weekly_topup','occasion'):
        N=[n for n in nodes(r) if q.area(n)>0]
        for n in N:
            if re.fullmatch(r'Bill (details|Summary)',q.label(n)): print(r['id'],r['app'],r['scenario'],r['screen'][:40],'y',n['t']); break
        else: print(r['id'],r['app'],r['scenario'],r['screen'][:40],'-')
