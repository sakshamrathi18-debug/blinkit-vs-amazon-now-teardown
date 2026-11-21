import sys
from PIL import Image
H=sys.argv[1]; S=H+'/assets/screens/'; C=H+'/assets/crops/'
J=[('blinkit-bill-rs17-milk-rs84','15-blinkit-bill-rs17-milk',(0,985,1080,1560)),
('blinkit-place-order-bar-rs84','15-blinkit-bill-rs17-milk',(0,2020,1080,2345)),
('amazon-now-bar-rs33-milk-rs63','16-amazon-now-checkout-rs33-milk',(0,1800,1080,2300)),
('amazon-now-saving-rs211-breakdown','21-amazon-now-saving-rs211',(0,350,1080,1000)),
('amazon-now-bar-add-rs442-for-rs200','22-amazon-now-bar-next-target',(0,1800,1080,2300)),
('blinkit-milk-first-row-ad-then-bought-earlier','07-blinkit-search-milk-ad-first',(0,1220,1080,2290)),
('amazon-now-milk-first-row-sponsored','08-amazon-now-search-milk-sponsored-first',(0,740,1080,1600)),
('amazon-now-lip-liner-then-okra','17-amazon-now-cart-lip-liner-okra',(0,990,1080,1790)),
('blinkit-lights-then-suggestions','19-blinkit-cart-lights-suggestions',(0,480,1080,1950)),
('blinkit-one-item-not-in-stock','23-blinkit-not-in-stock',(0,190,1080,800)),
('amazon-store-brownie-rs63-now-vs-rs120-normal','25-amazon-store-now-vs-normal-brownie',(0,430,1080,1720)),
('amazon-now-popup-diwali-ready','04-amazon-now-popup-diwali-ready',(0,1280,1080,2330)),
('amazon-store-now-tile-row','02-amazon-opens-on-main-store',(0,40,1080,320)),
('amazon-now-eta-23-mins','26-amazon-now-eta-23-mins',(0,190,1080,370)),
('amazon-now-eta-11-mins','05-amazon-now-home',(0,190,1080,370)),
('blinkit-eta-19-minutes','01-blinkit-home-diwali',(0,95,760,300)),
('blinkit-candle-3-left','24-blinkit-candle-3-left',(0,1200,1080,2240)),
('blinkit-feeling-under-the-weather','12-blinkit-under-the-weather-collection',(0,880,1080,1380)),
('amazon-now-zero-fees-cashback-strip','05-amazon-now-home',(0,1590,1080,2170)),
('blinkit-view-cart-pill-no-total','27-blinkit-after-add-people-also-bought',(0,2040,1080,2300)),
]
for n,s,b in J:
    Image.open(S+s+'.png').convert('RGB').crop(b).save(C+n+'.png',optimize=True)
