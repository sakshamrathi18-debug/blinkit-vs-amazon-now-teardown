import sys,re,csv
sys.path.insert(0,'tool')
import qc_audit as q
from PIL import Image,ImageDraw,ImageFont,ImageFilter
F='/System/Library/Fonts/Supplemental/Arial.ttf'; FB='/System/Library/Fonts/Supplemental/Arial Bold.ttf'
PII=re.compile(open('analysis/pii_patterns.txt').read().strip(),re.I)  # local only, gitignored
def load(sid):
    im=Image.open(f'data/screens/{sid}.png').convert('RGB')
    try: N=q.nodes_of(open(f'data/dumps/{sid}.xml').read())
    except Exception: N=[]
    return im,N
def mask(im,N,extra=()):
    d=ImageDraw.Draw(im)
    for n in N:
        if q.area(n)>0 and q.area(n)<200000 and PII.search(q.label(n)):
            box=(n['l']-6,n['t']-4,n['r']+6,n['b']+4)
            region=im.crop(box).filter(ImageFilter.GaussianBlur(22)); im.paste(region,box)
    for b in extra:
        region=im.crop(b).filter(ImageFilter.GaussianBlur(22)); im.paste(region,b)
    return im
def sheet(name,panels,w=400):
    h=int(w*2400/1080); cap=74; gap=20
    W=len(panels)*w+(len(panels)-1)*gap; S=Image.new('RGB',(W,h+cap),'white'); d=ImageDraw.Draw(S)
    fb=ImageFont.truetype(FB,20); fr=ImageFont.truetype(F,17)
    for i,p in enumerate(panels):
        im,N=load(p['id']); im=mask(im,N,p.get('extra',()))
        dd=ImageDraw.Draw(im)
        for b in p.get('outline',()): dd.rounded_rectangle(b,radius=20,outline=(214,40,57),width=10)
        x=i*(w+gap); S.paste(im.resize((w,h)),(x,cap))
        d.text((x+2,6),p['t'],font=fb,fill=(20,20,20)); d.text((x+2,36),p['s'],font=fr,fill=(90,90,90))
    S.save(f'analysis/figs/{name}.png',optimize=True); print(name,S.size)
sheet('first_screens',[
 dict(id='s0020',t='Blinkit',s='Festival takeover, no popup',extra=[(30,232,640,292)]),
 dict(id='s0036',t='Amazon on open',s='Main store; Now is tile 2',extra=[(130,490,930,570)]),
 dict(id='s0038',t='Amazon Now home',s='ETA, offers, sticky bar',extra=[(185,225,1000,350)])])
sheet('milk_search',[
 dict(id='s0114',t='Blinkit: "milk"',s='Paid Rs 57 first; your Rs 27 milk next',outline=[(26,1236,352,2262)]),
 dict(id='s0147',t='Amazon Now: "milk"',s='Paid Rs 54 first; Rs 33 Verka next',outline=[(38,756,520,1592)])])
sheet('cart_recs',[
 dict(id='s0067',t='Now, cart: lip liner',s='Okra, chilli, onion',extra=[(185,205,1000,345)]),
 dict(id='s0160',t='Now, cart: six staples',s='Okra, chilli, tomato',extra=[(185,205,1000,345)]),
 dict(id='s0054',t='Blinkit, cart: lights',s='Diyas, rangoli colours',extra=[(20,270,860,370),(120,2100,900,2160)]),
 dict(id='s0086',t='Blinkit, cart: milk',s='Paneer, coffee, bread',extra=[(120,2100,900,2160)])],w=300)
