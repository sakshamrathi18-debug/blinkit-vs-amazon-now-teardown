"""Print compact product cards (title, price, MRP, delivery) parsed from Amazon store result captures."""
import re, sys, csv
from pathlib import Path
D = Path(__file__).resolve().parent.parent / "data"
rows = [r for r in csv.DictReader(open(D / "screens.csv")) if r["scenario"] == "store_price_check" and r["source"] != "deleted"]
price = re.compile(r"^(?:Amazon Now |Great Indian Festival |Limited time deal )?(₹[\d,]+(?:\.\d+)?)(?: \(.*?\))? ?(?:M\.R\.P:? ?(₹[\d,]+(?:\.\d+)?))? ?(\(\d+% off\))?")
for r in rows:
    lines = [l.split("|", 1)[1] for l in (D / r["text"]).read_text().splitlines() if "|" in l]
    print(f"=== {r['id']} {r['screen'][14:70]}")
    title, out, seen = "", [], set()
    for l in lines:
        if l.startswith(("ref=", "View Sponsored", "Sponsored Ad")): continue
        if len(l) > 28 and "out of 5" not in l and not l.startswith(("₹", "M.R.P", "FREE", "Prime", "Amazon", "Great", "Arrives", "Buy ", "Savings")) and "bought" not in l and "delivery" not in l.lower():
            title = l[:70]
        if re.match(r"^(Amazon Now |Great Indian Festival |Limited time deal )?₹[\d,]+.*(M\.R\.P|/kg|/100|/count|/100 g|\()", l) or re.match(r"^M\.R\.P", l):
            key = (title, l[:60])
            if key not in seen: seen.add(key); out.append(f"  {title} | {l[:90]}")
        elif re.search(r"FREE delivery|delivery by|Amazon Now|Fresh|Arrives|Only \d left|out of stock|Currently unavailable", l) and len(l) < 90:
            key = (title, l)
            if key not in seen: seen.add(key); out.append(f"     > {l}")
    print("\n".join(out[:16]))
