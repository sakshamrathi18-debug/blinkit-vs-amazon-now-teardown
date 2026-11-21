import csv,re,sys,collections,statistics as st
sys.path.insert(0,'tool')
import qc_audit as q
rows=[r for r in csv.DictReader(open('data/screens.csv')) if r['source']!='deleted' and r['xml']]
HID=('Nestle Munch Max','Verka Cup Curd','Limca Lemon','Amul Gold Chocochips')
def nodes(r):
    try: return q.nodes_of(open('data/'+r['xml']).read())
    except Exception: return []
inside=lambda m,n: n['l']<=m['l'] and m['r']<=n['r'] and n['t']<=m['t'] and m['b']<=n['b']
BL=q.APPS['blinkit']
print('== reorder labels'); pat=re.compile(r'(order again|buy again|buy it again|reorder|previously|bought earlier|frequently bought|favourites)',re.I); C=collections.Counter()
for r in rows:
    surf='blinkit' if r['app']=='blinkit' else ('store' if r['scenario']=='store_price_check' else 'amazon')
    for n in nodes(r):
        m=pat.search(q.label(n))
        if m and q.area(n)>0: C[(surf,m.group(1).lower())]+=1
print(sorted(C.items()))
# unique products visible on blinkit with scarcity
seen={};
for r in rows:
    if r['app']!='blinkit': continue
    N=[n for n in nodes(r) if q.area(n)>0 and n['t']<2300]
    for c in N:
        L=q.label(c)
        if 'is available for' in L and c['clickable'] and not L.startswith(HID) and c['r']-c['l']<340:
            name=L.split(' is available')[0]
            kids=[q.label(m) for m in N if m is not c and inside(m,c)]
            k=[x for x in kids if re.fullmatch(r'\d+ left',x)]
            d=seen.setdefault(name,dict(left=set(),ad=False,be=False,price=L.split('for ')[1]))
            if k: d['left'].add(k[0])
            if 'Ad' in kids: d['ad']=True
            if any('Bought Earlier' in x for x in kids): d['be']=True
tot=len(seen); wl=sum(1 for d in seen.values() if d['left']); print('unique blinkit products',tot,'with N left',wl,round(wl/tot,3),'ad',sum(d['ad'] for d in seen.values()),'bought earlier',sum(d['be'] for d in seen.values()))
multi=[(k,sorted(d['left'])) for k,d in seen.items() if len(d['left'])>1]; print('products whose N left changed',multi[:10],len(multi))
print('== first row per query blinkit (clean)')
done=set()
for r in rows:
    if r['app']!='blinkit' or not r['screen'].lower().startswith(('blinkit results','blinkit search results')) or 'scroll' in r['screen']: continue
    key=r['screen'].split(':')[-1].strip()
    N=[n for n in nodes(r) if q.area(n)>0]
    c=sorted([n for n in N if 'is available for' in q.label(n) and n['clickable'] and not q.label(n).startswith(HID) and n['t']<2300],key=lambda n:(n['t'],n['l']))
    if not c: continue
    names=[q.label(x).split(' is available for')[0][:34]+' = '+q.label(x).split(' is available for ')[1][:18] for x in c[:3]]
    flags=[('AD' if any(q.label(m)=='Ad' and inside(m,x) for m in N) else '')+(' BE' if any('Bought Earlier' in q.label(m) and inside(m,x) for m in N) else '') for x in c[:3]]
    print(r['id'],key,'|',list(zip(names,flags)))
print('== density: visible add buttons per scroll frame')
d=collections.defaultdict(list)
for r in rows:
    if 'scroll' not in r['via'].lower(): continue
    N=[n for n in nodes(r) if q.area(n)>0 and 150<n['t']<2250]
    if r['app']=='blinkit' and r['scenario'] in('exact_item','need_based','occasion','non_grocery') and 'results' in r['screen'].lower():
        d['blinkit results'].append(sum(q.label(n)=='ADD' for n in N))
    if r['app']=='amazon' and r['scenario']=='store_price_check':
        d['store results'].append(sum(q.label(n)=='Add to cart' for n in N))
    if r['app']=='amazon' and r['scenario'] in('exact_item','need_based','occasion','non_grocery') and 'results' in r['screen'].lower():
        png=open('data/'+r['png'],'rb').read(); d['now results'].append(len(q.yellow_buttons(png)))
for k,v in d.items(): print(k,len(v),'median',st.median(v),'range',min(v),max(v))
print('== cold start medians')
T=collections.defaultdict(list)
for r in csv.DictReader(open('data/screens.csv')):
    m=re.search(r'TotalTime=(\d+)',r['note'])
    if m: T[r['app']].append(int(m.group(1)))
for k,v in T.items(): print(k,len(v),st.median(v),min(v),max(v))
print('== discount by surface, from csv rows')
for r in csv.DictReader(open('data/search_results.csv')):
    try:
        p=float(r['price']);m=float(r['mrp'])
        print(r['app'],r['scenario'][:6],r['product'][:40],p,m,round(100*(1-p/m)))
    except: pass
