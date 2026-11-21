import sys,re
sys.path.insert(0,'tool')
import qc_audit as q
from PIL import Image,ImageFilter
H=sys.argv[1]
PII=re.compile(open('analysis/pii_patterns.txt').read().strip(),re.I)  # local only, gitignored
def blur(im,b):
    b=(max(0,b[0]),max(0,b[1]),min(im.width,b[2]),min(im.height,b[3]))
    r=im.crop(b).resize((max(1,(b[2]-b[0])//16),max(1,(b[3]-b[1])//16))).resize((b[2]-b[0],b[3]-b[1])).filter(ImageFilter.GaussianBlur(18)); im.paste(r,b)
def clean(sid,extra=()):
    im=Image.open(f'data/screens/{sid}.png').convert('RGB')
    try: N=q.nodes_of(open(f'data/dumps/{sid}.xml').read())
    except Exception: N=[]
    for n in N:
        if 0<q.area(n)<250000 and PII.search(q.label(n)): blur(im,(n['l']-8,n['t']-6,n['r']+8,n['b']+6))
    for b in extra: blur(im,b)
    return im
S=[ # name, sid, extra blur boxes
('01-blinkit-home-diwali','s0020',[(30,225,650,295)]),
('02-amazon-opens-on-main-store','s0036',[(130,495,930,575)]),
('03-amazon-popup-festival-on-open','s0022',[]),
('04-amazon-now-popup-diwali-ready','s0037',[(0,0,1080,750)]),
('05-amazon-now-home','s0038',[(180,220,1010,355),(120,100,300,180)]),
('06-amazon-now-recommended-staples','s0039',[]),
('07-blinkit-search-milk-ad-first','s0114',[]),
('08-amazon-now-search-milk-sponsored-first','s0147',[]),
('09-blinkit-search-keyboard-open','s0075',[]),
('10-blinkit-search-cold-cough','s0108',[]),
('11-amazon-now-search-cold-cough','s0103',[]),
('12-blinkit-under-the-weather-collection','s0111',[]),
('13-blinkit-charger-specs','s0220',[]),
('14-amazon-now-charger-discounts','s0224',[]),
('15-blinkit-bill-rs17-milk','s0087',[(120,2040,900,2165)]),
('16-amazon-now-checkout-rs33-milk','s0097',[(180,200,1010,345)]),
('17-amazon-now-cart-lip-liner-okra','s0067',[(180,200,1010,345)]),
('18-amazon-now-cart-staples-okra','s0160',[(180,200,1010,345)]),
('19-blinkit-cart-lights-suggestions','s0054',[(20,270,860,370),(120,2040,900,2165)]),
('20-blinkit-cart-milk-suggestions','s0086',[(120,2040,900,2165)]),
('21-amazon-now-saving-rs211','s0216',[(180,200,1010,345)]),
('22-amazon-now-bar-next-target','s0159',[(180,200,1010,345)]),
('23-blinkit-not-in-stock','s0187',[(20,800,1060,960),(120,2040,900,2165)]),
('24-blinkit-candle-3-left','s0173',[]),
('25-amazon-store-now-vs-normal-brownie','s0243',[]),
('26-amazon-now-eta-23-mins','s0061',[(180,220,1010,355),(120,100,300,180)]),
('27-blinkit-after-add-people-also-bought','s0134',[]),
('28-amazon-now-after-add-bought-together','s0154',[]),
('29-blinkit-out-of-stock-notify','s0131',[]),
('30-blinkit-cart-lights-extension-board','s0055',[(120,2040,900,2165)]),
('31-amazon-now-charger-rs301','s0225',[]),
]
for name,sid,ex in S:
    clean(sid,ex).save(f'{H}/assets/screens/{name}.png',optimize=True); print(name,sid)
