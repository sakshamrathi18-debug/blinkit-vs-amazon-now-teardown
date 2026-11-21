"""Build teardown_data.xlsx from the CSVs, plus per-scenario effort counts from flow_steps.csv."""
import csv, collections
from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
D = Path(__file__).resolve().parent.parent / "data"; OUT = D.parent / "teardown_data.xlsx"
def rows(name):
    p = D / name
    return list(csv.reader(open(p))) if p.exists() else []
wb = Workbook(); wb.remove(wb.active)
def sheet(title, data, widths=None):
    ws = wb.create_sheet(title[:31])
    for r in data: ws.append(r)
    if data:
        for c in ws[1]: c.font = Font(bold=True, color="FFFFFF"); c.fill = PatternFill("solid", fgColor="1F3A5F")
        ws.freeze_panes = "A2"
        for i, col in enumerate(ws.columns):
            m = max((len(str(c.value or "")) for c in col), default=8)
            ws.column_dimensions[col[0].column_letter].width = min(max(10, m + 2), 60)
        for r in ws.iter_rows(min_row=2):
            for c in r: c.alignment = Alignment(wrap_text=True, vertical="top")
    return ws
norm = lambda a: "amazon_now" if a == "amazon" else a
flow = rows("flow_steps.csv"); eff = collections.defaultdict(lambda: collections.Counter())
for r in flow[1:]:
    k = (norm(r[1]), r[2]); a = r[4]
    if a == "tap" and "REFUSED" not in r[6]: eff[k]["taps"] += 1
    elif a == "tap": eff[k]["refused_taps"] += 1
    elif a in ("swipe", "back", "search", "cold-open"): eff[k][a + "s" if a != "swipe" else "scrolls"] += 1
shots = collections.Counter((norm(r[2]), r[3]) for r in rows("screens.csv")[1:] if r[9] != "deleted")
keys = sorted(set(eff) | set(shots))
summary = [["app", "scenario", "taps", "refused_taps", "scrolls", "searches", "backs", "cold_opens", "screens_captured"]]
for k in keys: summary.append([k[0], k[1], eff[k]["taps"], eff[k]["refused_taps"], eff[k]["scrolls"], eff[k]["searchs"] + eff[k]["searches"], eff[k]["backs"], eff[k]["cold-opens"], shots[k]])
readme = [["Amazon Now vs Blinkit teardown data"], ["Phone: Samsung SM-G780F, Android 13. Blinkit 18.41.0, Amazon 32.19.0.300. One account, one address (Mohali), one evening (about 6:50 to 8:00 pm, 2026-11-04)."],
 ["Stop point: no order was placed. Runs stop at the first screen that asks to pay."], ["app values: blinkit, amazon_now (inside Amazon app), amazon_store (main Amazon home)."],
 ["Picks: for adds, the first plain ADD (Blinkit) or first + (Amazon Now) was tapped, so picks are rank-1 results, often sponsored."],
 ["evidence_id / stop_screen_id refer to data/screens/<id>.png. Relevance ratings are my judgement; the 'relevance' column is editable."],
 ["Effort counts in effort_summary include retries and cart cleanup, so use checkout.csv screens_to_stop for the clean taps-to-checkout comparison."],
 ["Privacy: screenshots show the user's address and a recent order; keep data/ local and blur before sharing."]]
sheet("README", readme)
sheet("effort_summary", summary)
for n, f in (("screens", "screens.csv"), ("flow_steps", "flow_steps.csv"), ("home_modules", "home_modules.csv"), ("search_results", "search_results.csv"),
             ("recommendations", "recommendations.csv"), ("checkout", "checkout.csv"), ("price_compare", "price_compare.csv"), ("store_price_check", "store_price_check.csv")):
    sheet(n, rows(f))
wb.save(OUT); print(OUT)
for r in summary: print(r)
