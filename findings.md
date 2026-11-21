# Amazon Now vs Blinkit: what the apps show and do

Phone: Samsung SM-G780F, Android 13. Blinkit 18.41.0, Amazon 32.19.0.300. One account, one address (Mohali, same in both apps), one evening (about 6:50 to 8:00 pm, 4 Nov 2026, Diwali week). No order was placed; every run stops at the first screen that asks to pay.
**Observed** = seen on screen (screenshot id given). **Inferred** = my reading of intent, not proven. Raw data: `teardown_data.xlsx` and `data/*.csv`.

## 1. What each app shows when it opens

| | Blinkit | Amazon (Amazon Now) |
|---|---|---|
| First screen | Quick-commerce home straight away: ETA headline ("19 minutes"), address, search, tabs (All, Party, Electronics, Beauty, Gifting, Decor), Diwali takeover with 5 big tiles and a Gift Shop (s0010) | The main Amazon store, not Now. Often a full-screen sale popup first (Great Indian Festival, "extra Rs250 cashback only for Prime", s0022); once a Prime upsell page appeared (not kept, it showed a saved bank account). "Now" is the 2nd tile in the top row (s0036) |
| Getting to quick delivery | 0 taps | 1 tap on "Now", plus another popup on Now ("Diwali Ready, get cashback everytime", Tata Sampann co-brand, s0037) |
| Now home | n/a | ETA badge (11 to 23 mins), address, shortcut row (Live now, Diwali, Beverages, Snacks), hero banner, welcome offer and cashback tiers, "Zero Fees", HDFC offer, sticky "Add items worth Rs99 to get free delivery" even with an empty cart (s0038, s0061) |
| Where groceries start | Category grid about 4 scrolls down; first screen is festive decor, gifting, appliances (s0010, s0014) | Staples (bhindi, chilli, onion with % off and +) at the first scroll in "Recommended for you" (s0039) |
| Personalisation | "Bought earlier" labels and "Curated for you" about 8 screens down (s0018) | "Recommended for you" tabs early (Top Picks, Fresh Vegetables, Drinks); no history label seen |
| Changes between opens | Theme green to red, ETA 19 to 15 mins, hero changed from Rangoli Stencil Rs109 to Diya Set Rs129 with MRP Rs349 (s0010, s0020, s0021) | Popup differs every open (Great Indian Festival, Prime upsell, Pay tile vs Flights tile); ETA 11 to 23 mins; hero carousel rotates (s0038, s0061) |
| Ads on home | "Featured", "Ad", "Sponsored" blocks (Torans, Thoughtful Gifts, Laneige, Red Rock Deli chips) | Brand-funded blocks (So Good, Pampers, Nivea/Pilgrim Beauty Store), Sponsored Dhanteras banner |

**Inferred:** Blinkit is built for the festival basket and gifting, so groceries sit below the fold. Amazon Now's home explains value (zero fees, cashback, free delivery) before showing products, and keeps Amazon's catalogue (electronics, books, extension boards) one scroll away (s0047).

## 2. Scenario results

| # | Scenario | Blinkit (observed) | Amazon Now (observed) | Evidence |
|---|---|---|---|---|
| 1 | Explorer, no goal | Top tile ("Lights, Diya & Diwali Decor", rotating product) opened a decor listing starting with pixel lights. Checkout in 3 taps. Rs176 total for a Rs129 item | Rotating hero banner opened a brand-funded Beauty Store (Powered by Nivea, Pilgrim); the slide tapped may differ from the "Deals You'll Love" slide captured earlier. Needed Now tile, popup closes, banner, +, Proceed. Rs99 total for a Rs69 item | s0049, s0062, checkout.csv |
| 2 | Exact item: amul taaza milk 500ml | Rewrote query to "amul taaza milk". Rank 1 Amul Gold 500 ml Rs36. Taaza exists only as 200 ml Tetra Pak (Rs17 single). Typo "amull milk" auto-corrected, but Country Delight ranked first | Kept the query. Rank 1 Verka 500 ml Rs33, then Amul curd, Amul Kool, lassi, ice cream. No Taaza at all. Typo corrected with a visible "Search instead for" link; Country Delight first | s0075-s0078, s0093-s0095, s0090, s0100 |
| 3 | Need: cold and cough | Autocomplete (Cough and cold medicine), filter chips (Cough Syrup, Lozenges, Vaporizer), "Feeling under the weather?" collection, mix of syrup, lozenges, balm, masks, steamers, ayurvedic. 2 of first 5 carry "Ad" | Narrower OTC brand set (Vicks, Dabur, Wellbeing, Hoop). 4 of first 12 Sponsored; same Dabur Honitus product at rank 1 and 3. No chips or collections | s0108-s0111, s0103-s0106 |
| 4 | Weekly top-up (6 items) | Rs778 of items, delivery free, Rs12 handling, total Rs790, ETA 13 mins, many add-on suggestions | Rs1,057 payable (Rs1,390 at MRP), delivery and handling free, Rs100 cashback so effective Rs957, ETA 11 mins. Atta pick was a Rs748 5 kg Khapli flour; Blinkit's atta pick was the 10 kg Aashirvaad pack (Rs457, Ad-labelled; its 5 kg is Rs244), so the two baskets are not like-for-like | s0139, s0159 |
| 5 | Occasion: birthday | Results promise 11 mins; search suggests candle, topper, mix; budget and Veg/Egg filters. The Ad-labelled Rs1,099 jar candle went out of stock at checkout ("1 item is not in stock"). Rs428 for 3 items | Packaged cakes and mixes only. 3 of 4 first picks Sponsored. Rs397 for 4 items (Rs468 at MRP), Rs100 cashback, ETA 11 mins | s0167-s0173, s0187, s0204-s0216 |
| 6 | Non-grocery: type c fast charger | Spec-led: wattage chips (12 to 65 W), amp tags, Type filter, Rating 4+, "N left" cues, ETA 11 to 15 mins | Discount-led: 65 to 80% off tags, Great Indian Festival badges, review counts; no wattage or Type filter; a cable appears inside charger results. 2 of first 6 Sponsored. **Main Amazon store, same query:** wattage chips (33w, 65w, 100w), Prime toggle, boAt sponsored carousel, 4 of first 6 results Sponsored, "bought in past month" proof, delivery by date (Thu 12 Nov), no Now or minutes badge | s0219-s0221, s0224-s0226, s0229-s0231 |

### Fees on very small baskets (same address, same evening)
| Basket | Blinkit | Amazon Now |
|---|---|---|
| Rs17 to Rs33 item | Rs17 item + Rs35 delivery + Rs12 handling + Rs20 small-cart = **Rs84** (fees Rs67) | Rs33 item + Rs30 delivery, handling waived = **Rs63** (fees Rs30) |
| Rs416 to Rs778 | Delivery free, Rs12 handling stays | Delivery and handling free, plus Rs100 cashback above Rs299 |

### Same product, both apps (price_compare.csv)
Verka 500 ml Rs33 vs Rs33; Vicks Dry+Wet syrup Rs99 vs Rs99; Portronics Adapto 20W Rs301 vs Rs301; Vicks cough drops Rs50 vs Rs47; Country Delight buffalo milk Rs59 vs Rs54 (Amazon Now cheaper in both of the last two). Prices were close; fees and promotions were the difference.

## 3. Which is more relevant, and what each seems to be trying to do

**More relevant (observed):** Blinkit for need-based and spec-led searches (scenarios 3 and 6) and for occasion browsing. Neither found the exact Amul Taaza 500 ml, but Blinkit stayed closer to milk. Amazon Now was more diluted on keyword searches and had more Sponsored cards in top results (3 of 4 picks in scenario 5).

**Blinkit, inferred intent:** win the occasion and the gift basket (festival takeover, tile heroes, price-drop and "N left" cues), grow basket size with checkout add-ons, and earn from ads and fees (handling and small-cart charges on every order).

**Amazon Now, inferred intent:** use the huge Amazon base as a funnel (popups, Prime-only cashback, the "Now" tile), remove fee friction (waived handling and delivery, cashback tiers Rs50/100/200 at 499/899/1,499), keep a free-delivery progress bar on every screen, and let brands pay for visibility (brand stores, Sponsored slots).

## 4. Do you pay more for quick delivery? (Amazon main store vs the quick-delivery prices)
Same address, same evening (8:05 to 8:20 pm). I looked up the items I picked in each app on Amazon's normal store (read-only, nothing added to any cart). Data: `data/store_price_check.csv`, sheet `store_price_check`, screenshots s0232 to s0267.

**What the main store shows (observed):** many grocery and daily-need listings carry two offers on the same product page: an **"Amazon Now" price with "FREE delivery within 12 mins on orders over Rs99"**, and a normal **"One-time purchase"** price with a delivery date (Prime, "Tomorrow, 5 Nov", "Fri, 6 Nov", "Wed, 11 Nov", up to "Tue, 17 Nov"). Amazon Fresh shows "Tomorrow 12 to 2 pm".

| Item | Quick-delivery price | Normal Amazon price and delivery | Difference |
|---|---|---|---|
| Portronics Adapto 20W charger | Rs301 (Blinkit and Now) | Rs301, Prime **Tomorrow** | none, and the normal one is 1-day |
| Vicks VapoRub 50 ml | Rs139 (Now); Rs160 (Blinkit, Ad) | Rs139, Wed 11 Nov | none vs Now; Blinkit Rs21 more |
| Vicks cough syrup 100 ml | Rs99 (both) | Rs99.22, Fri 6 Nov (pharmacy, free above Rs199 of pharmacy items) | none |
| Aashirvaad atta 5 kg | Rs244 (Blinkit) | Rs244, Now 12 mins | none |
| Aashirvaad atta 10 kg | Rs457 (Blinkit, Ad) | Rs449, Now 12 mins | Blinkit Rs8 more |
| Two Brothers Khapli flour 5 kg | Rs748 (Now) | Rs748 (with a Prime coupon, buy for Rs726) | none |
| IRIS Berry Pop jar candle | Rs139 (Now) | Rs149, Wed 11 Nov | normal Rs10 more, 7 days slower |
| Vicks cough drops, bag of 25 | Rs47 (Now); Rs50 (Blinkit) | Rs99, Fri 13 Nov | normal Rs52 more, 9 days slower |
| Fudge It brownie 120 g (extra example) | Rs63 (Now) | Rs120, Tue 17 Nov | normal Rs57 more, 12 days slower |

**Answer for these items (observed):** no, the item price was not higher for quick delivery. Amazon Now's price matched or was below the normal listing on every item where both were visible, before one Prime coupon (Two Brothers flour: normal Rs726 with coupon, Now Rs748), and Blinkit was equal or a little higher (Rs3 to Rs21; the two biggest gaps were on Ad-labelled picks). Where the normal price was higher it was a different seller or a looser MRP, and delivery was 1 to 12 days later.

**Where the real cost sits (observed):** in fees on small baskets, not in item prices. Blinkit charged Rs67 in fees on a Rs17 item (Rs35 delivery, Rs12 handling, Rs20 small-cart); Amazon Now charged Rs30 delivery on Rs33 to Rs69 baskets (handling waived). Both made delivery free at larger sizes (Rs416 or more). A normal Amazon listing also showed fees on small packs (a Rs70 delivery charge on a small RiteBite pack, free delivery only above Rs199 on pharmacy items).

**Limits for this check:** 11 items matched; 6 had no like-for-like on the store (Britannia pound cake, Party Propz balloons pack, Red Rock chips, Mars lip liner, WAAN pixel light) and the Propcon balloons lookup is invalid because the store search box changed my query to "popcorn metallic". Milk, eggs, onions, bananas and bread were not checked (perishables; Amazon Fresh slots were not opened). Prime status of this account was not checked, so "free delivery" labels may depend on Prime. One evening, one address, one account.

## 5. Limits and incidents (please read)
- One account, one address, one evening, Diwali week. Not representative of all users or times. Recommendations reflect this account's history.
- For adds I tapped the first plain ADD or first + on rank-1 results, so picks skew toward sponsored items (the candle, cake, chips). Totals are not like-for-like baskets.
- Scenarios 3 and 6 stop at search results, with no checkout. The main Amazon store charger search was run (results only): it has wattage filters and date-based delivery and showed no Now or minutes badge in the first 3 screens. **But grocery and daily-need listings on the main store do show Amazon Now (see section 4), so the two are joined at the listing level for those products.**
- Tap and scroll counts in `effort_summary` include retries and cart cleanup; use `checkout.csv` `screens_to_stop` for taps to checkout.
- No order was placed. **A Blinkit cart item is still there:** the out-of-stock Jar Candle by Pranah (Rs1,099). It cannot be ordered (Place Order is disabled). Clearing it needs the red x on the "not in stock" card, which my tap guard refuses by design, so it is yours to tap.
- Incidents: (1) one wishlist heart was tapped by mistake on Blinkit and undone. (2) Twice a tap landed on the sticky "Delivering to Home" bar and opened the address picker; nothing was selected and the address stayed Home. The guard was fixed (topmost control, sticky bar, scrolled-checkout detection) and tested (44 offline tests pass). (3) A payment-details capture and three address-picker captures with other people's details were deleted; phone numbers in saved text are redacted.
- Screenshots still show your address and name; keep `data/` local and blur before sharing.

Deeper analysis, corrections and shopper guidance: https://claude.ai/artifact/K1XQZKTySm1ZYH36mxEs3L
