import csv,re,sys,collections,itertools
sys.path.insert(0,'tool')
import qc_audit as q
rows={r['id']:r for r in csv.DictReader(open('data/screens.csv')) if r['source']!='deleted' and r['xml']}
HID=('Nestle Munch Max','Verka Cup Curd','Limca Lemon','Amul Gold Chocochips')
def nodes(i):
    try: return q.nodes_of(open('data/'+rows[i]['xml']).read())
    except Exception: return []
def names_now(ids):
    out=[]
    for i in ids:
        for n in nodes(i):
            L=q.label(n)
            if L.startswith('View details for '):
                x=L[17:]
                if x not in out: out.append(x)
    return out
def names_bl(ids):
    out=[]
    for i in ids:
        for n in sorted(nodes(i),key=lambda n:(n['t'],n['l'])):
            L=q.label(n)
            if 'is available for' in L and q.area(n)>0 and n['clickable'] and n['r']-n['l']<340 and not L.startswith(HID):
                x=L.split(' is available')[0]
                if x not in out: out.append(x)
    return out
NOW={'lip liner':['s0067'],'milk':['s0097'],'six staples':['s0159','s0160','s0161','s0162'],'party':['s0216'],'home':['s0039','s0040','s0041']}
BL={'pixel lights':['s0054','s0055'],'milk':['s0085','s0086'],'six staples':['s0139','s0140','s0141'],'party':['s0187','s0188','s0189']}
def ov(d,f):
    S={k:f(v) for k,v in d.items()}
    for k,v in S.items(): print('  ',k,len(v),v[:18])
    for a,b in itertools.combinations(S,2):
        A,B=set(S[a]),set(S[b]); print('   overlap',a,'/',b,len(A&B),'of',min(len(A),len(B)),round(len(A&B)/max(1,len(A|B)),2))
print('NOW'); ov(NOW,names_now)
print('BLINKIT'); ov(BL,names_bl)
print('== options share on Blinkit (unique cards)')
seen={}
inside=lambda m,n: n['l']<=m['l'] and m['r']<=n['r'] and n['t']<=m['t'] and m['b']<=n['b']
for i,r in rows.items():
    if r['app']!='blinkit': continue
    N=[n for n in nodes(i) if q.area(n)>0 and n['t']<2300]
    for c in N:
        L=q.label(c)
        if 'is available for' in L and c['clickable'] and c['r']-c['l']<340 and not L.startswith(HID):
            nm=L.split(' is available')[0]
            k=any('option' in q.label(m) for m in N if inside(m,c))
            seen[nm]=seen.get(nm,False) or k
print(len(seen),sum(seen.values()))
print('== Blinkit free delivery nudges outside checkout, and running total')
for i,r in rows.items():
    if r['app']=='blinkit':
        t=[q.label(n) for n in nodes(i) if q.area(n)>0 and re.search(r'Get FREE delivery|Add products worth|Free Pepsi|worth ₹\d+ more|FREE Delivery',q.label(n))]
        if t: print(i,r['screen'][:42],'|',t[:3])
print('== out of stock labels'); 
for app in('blinkit','amazon'):
    c=[(i) for i,r in rows.items() if r['app']==app and any(re.search(r'out of stock|currently unavailable|Notify',q.label(n),re.I) and q.area(n)>0 for n in nodes(i))]
    print(app,len(c),c[:12])
print('== now frequently bought contexts')
for i,r in rows.items():
    if r['app']=='amazon':
        for n in nodes(i):
            if re.search('frequently bought|favourites',q.label(n),re.I) and q.area(n)>0: print(i,r['scenario'],r['screen'][:40],q.label(n)[:70]);break
print('== Blinkit view cart pill text contains amount?')
c=collections.Counter()
for i,r in rows.items():
    if r['app']=='blinkit':
        L=[q.label(n) for n in nodes(i)]
        if 'View cart' in L:
            c['with pill']+=1
print(c)
print('== now popup/landing and store popup close labels per cold open')
for i,r in rows.items():
    if r['app']=='amazon' and 'cold open' in r['note'].lower() or (r['app']=='amazon' and 'TotalTime' in r['note']):
        L=[q.label(n) for n in nodes(i)]
        print(i,r['timestamp'][11:16],r['scenario'],'close' in L, r['note'][:50])
