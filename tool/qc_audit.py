#!/usr/bin/env python3
"""qc_audit: drive and document Blinkit and Amazon (Amazon Now) over ADB, for a read-only comparison.

Safety: every action first checks that the named app is in the foreground. Taps are refused when the target
(or anything inside it) is a payment, order, membership, login, address-change or consent control. On cart and
checkout screens a tap passes only if its label is on a short allowlist; unlabelled controls are refused.
Nothing here can place an order. The runs stop at the first screen that asks for payment.
"""
import argparse, csv, datetime as dt, json, os, re, subprocess, sys, time
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

APPS = {"blinkit": "com.grofers.customerapp", "amazon": "in.amazon.mShop.android.shopping"}
ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SCREENS = DATA / "screens"; DUMPS = DATA / "dumps"; TEXT = DATA / "text"
CSV_SCREENS = DATA / "screens.csv"; CSV_ACTIONS = DATA / "actions_log.csv"; CSV_FLOW = DATA / "flow_steps.csv"
HISTORY = DATA / "history_to_clean.md"; META = DATA / "app_meta.json"
COLS = ["id","timestamp","app","scenario","step","screen","via","signifies","note","source","privacy_check","dump_status","png","xml","text"]
ACOLS = ["timestamp","action","detail","result"]
FCOLS = ["timestamp","app","scenario","seq","action","detail","result"]
SCHEMAS = {
    "home_modules": ["app","cold_open","position","module_type","title","above_fold","sponsored","items_shown","evidence_id","note"],
    "search_results": ["app","scenario","query","rank","product","brand","pack","price","mrp","discount","eta","sponsored","in_stock","rating","evidence_id","note"],
    "recommendations": ["app","scenario","where_shown","trigger","items","relevance","sponsored","evidence_id","note"],
    "checkout": ["app","scenario","items","item_total","delivery_fee","handling_fee","small_cart_fee","surge_fee","tip","donation","discount","grand_total","eta","free_delivery_threshold","upsells","screens_to_stop","stop_screen_id","note"],
    "price_compare": ["product","pack","blinkit_price","blinkit_mrp","amazon_price","amazon_mrp","blinkit_eta","amazon_eta","blinkit_evidence","amazon_evidence","note"],
}

# ---- tap guard -------------------------------------------------------------------------------
STRONG = re.compile(r"place (your )?order|pay now|pay\s*(₹|rs\b)|proceed to pay|slide to pay|swipe to pay|buy now|confirm (order|payment)|"
                    r"cash on delivery|pay on delivery|pay with|make payment|complete (order|purchase)|one[- ]?click|1-click", re.I)
WORDS = (r"pay|payment|payments|confirm|prime|membership|gold|pass|upi|wallet|card|netbanking|sign ?in|sign ?up|log ?in|log ?out|sign ?out|"
         r"subscribe|change|edit|tip|donate|donation|gift|cod|apply|enable|allow|turn on|deny|accept|agree|continue with|share|"
         r"add address|add money|recharge|coupon|settings|profile|account|permission|wishlist|favou?rite|save|follow|notify|remind|rate|review this")
DENY_SHORT = re.compile(rf"\b({WORDS})\b", re.I)          # short labels: word anywhere
DENY_START = re.compile(rf"^\W*({WORDS})\b", re.I)        # labels of any length that start with one of them
DENY_RID = re.compile(r"(place_?order|buy_?now|pay_?now|payment|prime|wallet|upi|sign_?in|log_?in|one_?click)", re.I)
CHECKOUT_MARKERS = re.compile(r"bill details|\bto pay\b|grand total|order summary|payment method|select payment|item total|items total|"
                              r"delivery partner tip|order total|review your order|choose a payment|handling charge|delivery charge|subtotal", re.I)
COMMIT_VISIBLE = re.compile(r"place (your )?order|pay now|proceed to pay|slide to pay|swipe to pay|pay\s*(₹|rs\b)|use this payment method", re.I)
ALLOW_STRICT = re.compile(r"proceed( to (buy|checkout))?|view cart|go to cart|my cart|cart|back|navigate up|close|remove|delete|"
                          r"decrease( quantity)?|increase( quantity)?|minus|plus|[-+]", re.I)
SAFE_WORD = re.compile(r"^[A-Za-z0-9 ]+$")

def now(): return dt.datetime.now().isoformat(timespec="seconds")
def norm(s): return re.sub(r"\s+", " ", (s or "").replace("−", "-")).strip()
def label(n): return n["text"] or n["desc"]

B = re.compile(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]")
def nodes_of(xml):
    res = []
    def walk(el, parent):
        for n in el.findall("node"):
            m = B.match(n.get("bounds", "")); idx = parent
            if m:
                l, t, r, b = map(int, m.groups())
                res.append(dict(pkg=n.get("package",""), rid=n.get("resource-id",""), text=n.get("text",""), desc=n.get("content-desc",""),
                                cls=n.get("class",""), clickable=n.get("clickable")=="true", checkable=n.get("checkable")=="true",
                                focused=n.get("focused")=="true", l=l, t=t, r=r, b=b, parent=parent))
                idx = len(res) - 1
            walk(n, idx)
    walk(ET.fromstring(xml), None)
    return res

def intruders(nodes, pkgs):
    bad = set()
    for n in nodes:
        if n["pkg"] in pkgs: continue
        if n["pkg"] == "com.android.systemui" and (n["b"] <= 140 or re.search(r"nav|home|back|recent|gesture", n["rid"], re.I) or n["t"] >= 2250):
            continue
        bad.add(n["pkg"] or "unknown")
    return sorted(bad)

def area(n): return (n["r"]-n["l"]) * (n["b"]-n["t"])
def inside(n, x, y): return n["l"] <= x <= n["r"] and n["t"] <= y <= n["b"]
def within(m, n): return m is not n and n["l"] <= m["l"] and m["r"] <= n["r"] and n["t"] <= m["t"] and m["b"] <= n["b"]

def is_denied_label(lab):
    lab = norm(lab)
    if not lab: return False
    if STRONG.search(lab) or DENY_START.search(lab): return True
    return len(lab) <= 40 and bool(DENY_SHORT.search(lab))

FOOTER_MARK = re.compile(r"place order|proceed to pay|pay using|delivering to|use this payment|you pay", re.I)
def checkout_screen(nodes):
    """A cart/checkout screen shows bill words, or (when scrolled) just the sticky payment/address bar."""
    return any(label(n) and (CHECKOUT_MARKERS.search(label(n)) or FOOTER_MARK.search(label(n))) for n in nodes)
def commit_visible(nodes): return [label(n) for n in nodes if label(n) and COMMIT_VISIBLE.search(label(n))]

def tree_descendants(nodes, i):
    """Real parent/child descendants of node i (not geometric), skipping zero-size hidden nodes."""
    kids = {}
    for j, m in enumerate(nodes): kids.setdefault(m["parent"], []).append(j)
    out, stack = [], list(kids.get(i, []))
    while stack:
        j = stack.pop()
        if area(nodes[j]) > 0: out.append(j)
        stack.extend(kids.get(j, []))
    return out

def node_denied(m):
    if m["checkable"] or re.search(r"(Switch|CheckBox|ToggleButton|RadioButton)$", m["cls"]): return "toggle control"
    for lab in (m["text"], m["desc"]):
        if is_denied_label(lab): return f"label '{norm(lab)[:50]}'"
    if DENY_RID.search(m["rid"]): return f"id '{m['rid']}'"
    return ""

COMMIT_RID = re.compile(r"(place_?order|buy_?now|pay_?now|payment|one_?click)", re.I)
def node_commit(m):
    """Order/payment evidence only. Used when looking inside a wrapping element, where sibling buttons are normal."""
    for lab in (m["text"], m["desc"]):
        if lab and STRONG.search(norm(lab)): return f"label '{norm(lab)[:50]}' inside the tapped control"
    if COMMIT_RID.search(m["rid"]): return f"id '{m['rid']}' inside the tapped control"
    return ""

FOOTER_LABEL = re.compile(r"place order|proceed to pay|pay using|delivering to|you pay|view cart|proceed\b", re.I)
def footer_top(nodes, limit):
    """Top edge of a sticky bottom bar on a cart/checkout screen: the highest top edge among small ancestors of its payment/address labels."""
    top = None
    for i, n in enumerate(nodes):
        if area(n) > 0 and label(n) and FOOTER_LABEL.search(label(n)) and n["t"] > 1500:
            t, c = n["t"], i
            while c is not None and area(nodes[c]) <= limit:
                t = min(t, nodes[c]["t"]) if area(nodes[c]) > 0 else t; c = nodes[c]["parent"]
            top = t if top is None else min(top, t)
    return top

def check_tap(nodes, x, y, pkgs, W=1080, H=2400):
    """Pure decision: (allowed, reason). Refuses on doubt.
    Checked: every small element under the point; everything inside the tapped (smallest) element and inside any
    clickable element that contains it (a button wrapping a 'Place Order' label). Large containers do not drag in siblings."""
    if not nodes: return False, "no UI dump"
    bad = intruders(nodes, pkgs)
    if bad: return False, f"other app on screen {bad}"
    limit = 0.35 * W * H
    idx = [i for i, n in enumerate(nodes) if inside(n, x, y) and area(n) <= limit and area(n) > 0]
    if not idx: return False, "no small element under that point"
    for i in idx:
        why = node_denied(nodes[i])
        if why: return False, why
    # The control that actually receives the tap is the topmost clickable one: the last in dump (draw) order.
    clickable = [i for i in idx if nodes[i]["clickable"]]
    smallest = max(clickable) if clickable else min(idx, key=lambda i: area(nodes[i]))
    chain, c = [smallest], nodes[smallest]["parent"]
    while c is not None:
        if area(nodes[c]) <= limit and nodes[c]["clickable"]: chain.append(c)
        c = nodes[c]["parent"]
    for i in chain:
        for j in tree_descendants(nodes, i):
            why = node_commit(nodes[j])
            if why: return False, why
    if checkout_screen(nodes):
        ft = footer_top(nodes, limit)
        if ft is not None and y >= ft - 8: return False, "tap lands in the sticky payment/address bar"
        sm = nodes[smallest]
        labs = [norm(label(nodes[j])) for j in [smallest] + tree_descendants(nodes, smallest) if label(nodes[j])]
        if not labs: return False, "unlabelled control on a cart/checkout screen"
        if not ALLOW_STRICT.fullmatch(labs[0]): return False, f"'{labs[0][:40]}' is not on the cart/checkout allowlist"
    return True, ""

# ---- adb -------------------------------------------------------------------------------------
_SERIAL = None
def serial():
    global _SERIAL
    if _SERIAL is None:
        _SERIAL = os.environ.get("ANDROID_SERIAL", "")
        if not _SERIAL:
            out = subprocess.run(["adb","devices"], capture_output=True).stdout.decode()
            devs = [l.split()[0] for l in out.splitlines()[1:] if l.strip().endswith("device")]
            if len(devs) != 1: sys.exit(f"expected exactly one connected device, found {len(devs)}. Set ANDROID_SERIAL.")
            _SERIAL = devs[0]
    return _SERIAL

def adb(args, timeout=30, binary=False):
    r = subprocess.run(["adb","-s",serial()] + args, capture_output=True, timeout=timeout)
    return r.stdout if binary else r.stdout.decode("utf-8", "replace")

_WH = None
def screen_wh():
    global _WH
    if _WH is None:
        m = re.search(r"(\d+)x(\d+)", adb(["shell","wm","size"]))
        _WH = (int(m.group(1)), int(m.group(2))) if m else (1080, 2400)
    return _WH

def log_action(action, detail="", result="ok"):
    DATA.mkdir(exist_ok=True); new = not CSV_ACTIONS.exists()
    with open(CSV_ACTIONS, "a", newline="") as f:
        w = csv.writer(f)
        if new: w.writerow(ACOLS)
        w.writerow([now(), action, detail, result])

def log_flow(a, action, detail="", result="ok"):
    rows = list(csv.DictReader(open(CSV_FLOW))) if CSV_FLOW.exists() else []
    seq = sum(r["app"] == a.app and r["scenario"] == (a.scenario or "") for r in rows) + 1
    new = not CSV_FLOW.exists()
    with open(CSV_FLOW, "a", newline="") as f:
        w = csv.writer(f)
        if new: w.writerow(FCOLS)
        w.writerow([now(), a.app, a.scenario or "", seq, action, detail, result])

def log_history(kind, text):
    HISTORY.parent.mkdir(exist_ok=True)
    with open(HISTORY, "a") as f: f.write(f"- {now()} {kind}: {text}\n")

def foreground():
    for _ in range(4):
        m = re.search(r"mCurrentFocus=.*", adb(["shell","dumpsys window | grep mCurrentFocus"]))
        if m and "null" not in m.group(0): return m.group(0)
        time.sleep(0.5)
    return ""

def require_app(app):
    fg = foreground()
    if APPS[app] not in fg:
        log_action("guard", fg, f"REFUSED: {app} not in foreground")
        sys.exit(f"REFUSED: {app} is not the foreground app ({fg or 'unknown'}). Nothing captured or sent.")

def dump_ui():
    try: out = adb(["exec-out","uiautomator","dump","/dev/tty"], timeout=12)
    except subprocess.TimeoutExpired: return None
    i = out.find("</hierarchy>")
    if "<hierarchy" not in out or i < 0: return None
    return out[out.find("<?xml") if "<?xml" in out else out.find("<hierarchy"): i + len("</hierarchy>")]

def ui_nodes(tries=4):
    """Dump the UI, retrying: animated banners can make uiautomator fail a few times in a row."""
    for k in range(tries):
        x = dump_ui()
        if x:
            try: return x, nodes_of(x)
            except ET.ParseError: pass
        time.sleep(1.5)
    return None, []

# ---- capture ---------------------------------------------------------------------------------
def next_id():
    if not CSV_SCREENS.exists(): return 1
    return max([int(r["id"][1:]) for r in csv.DictReader(open(CSV_SCREENS))], default=0) + 1

def append_row(row):
    new = not CSV_SCREENS.exists()
    with open(CSV_SCREENS, "a", newline="") as f:
        w = csv.DictWriter(f, COLS)
        if new: w.writeheader()
        w.writerow(row)

PHONE = re.compile(r"(?<!\d)(\+?91[- ]?)?[6-9]\d{9}(?!\d)")
def redact(t): return PHONE.sub("[phone]", t)

def text_lines(nodes, pkg):
    H = screen_wh()[1] if serial() else 2400
    seen, out = set(), []
    for n in sorted(nodes, key=lambda n: (n["t"], n["l"])):
        lab = redact(norm(label(n)))
        if n["pkg"] == pkg and lab and 0 <= n["t"] < H and (n["t"], n["l"], lab) not in seen:
            seen.add((n["t"], n["l"], lab)); out.append(f'{n["t"]},{n["l"]},{n["r"]},{n["b"]}|{lab}')
    return out

def ocr_lines(path):
    try: out = subprocess.run(["tesseract", str(path), "stdout"], capture_output=True, timeout=40).stdout.decode("utf-8", "replace")
    except (OSError, subprocess.TimeoutExpired): return []
    return ["ocr|" + l.strip() for l in out.splitlines() if l.strip()]

def blank_png(path):
    try:
        from PIL import Image
        return all(hi == 0 for _, hi in Image.open(path).convert("RGB").getextrema())
    except Exception: return False

def do_capture(a, screen=None, via=None, note=""):
    require_app(a.app); pkg = APPS[a.app]
    SCREENS.mkdir(parents=True, exist_ok=True); DUMPS.mkdir(exist_ok=True); TEXT.mkdir(exist_ok=True)
    with ThreadPoolExecutor(1) as ex:
        fut = ex.submit(ui_nodes)
        png = adb(["exec-out","screencap","-p"], binary=True)
        xml, nodes = fut.result()
    if not png.startswith(b"\x89PNG"): sys.exit("screencap failed")
    bad = intruders(nodes, set(APPS.values())) if nodes else []
    if bad:
        log_action("capture", screen or "", f"DISCARDED: other app on screen {bad}")
        sys.exit(f"DISCARDED: other app content visible {bad}. Nothing saved.")
    if not nodes: require_app(a.app)
    sid = f"s{next_id():04d}"; p = SCREENS / f"{sid}.png"; p.write_bytes(png)
    if xml: (DUMPS / f"{sid}.xml").write_text(xml)
    lines = text_lines(nodes, pkg) if nodes else []
    flags = []
    if blank_png(p): flags.append("BLANK FRAME (screen may block screenshots)")
    if len(lines) < 12 and not flags: lines += ocr_lines(p); flags.append("thin UI dump, OCR added")
    (TEXT / f"{sid}.txt").write_text("\n".join(lines))
    rows = list(csv.DictReader(open(CSV_SCREENS))) if CSV_SCREENS.exists() else []
    step = getattr(a, "step", None) or sum(r["app"] == a.app and r["scenario"] == (a.scenario or "") for r in rows) + 1
    append_row(dict(id=sid, timestamp=now(), app=a.app, scenario=a.scenario or "", step=step, screen=screen or a.screen or "", via=via or a.via or "",
                    signifies=a.signifies or "", note="; ".join(filter(None, [note or a.note or "", *flags])),
                    source="uiautomator+screenshot" if nodes else "screenshot_only", privacy_check="concurrent" if nodes else "none",
                    dump_status="ok" if nodes else "failed", png=f"screens/{sid}.png", xml=f"dumps/{sid}.xml" if xml else "", text=f"text/{sid}.txt"))
    log_action("capture", f"{sid} {a.app} {screen or a.screen or ''}")
    cv = commit_visible(nodes) if nodes else []
    print(f"{sid} {'dump ok' if nodes else 'DUMP FAILED'} labels={len(lines)} {' | '.join(flags)}" + (f"\n!! COMMIT SCREEN: {cv[:3]} -> stop here, do not tap" if cv else ""))
    return sid

# ---- commands --------------------------------------------------------------------------------
def cmd_preflight(a):
    info = dict(time=now(), model=adb(["shell","getprop","ro.product.model"]).strip(), android=adb(["shell","getprop","ro.build.version.release"]).strip(),
                size=adb(["shell","wm","size"]).strip(), battery=re.findall(r"level: (\d+)", adb(["shell","dumpsys","battery"]))[:1],
                dnd_zen_mode=adb(["shell","settings","get","global","zen_mode"]).strip(),
                stay_on=adb(["shell","settings","get","global","stay_on_while_plugged_in"]).strip(), foreground=foreground())
    for k, pkg in APPS.items():
        out = adb(["shell","dumpsys","package",pkg])
        info[k] = dict(package=pkg, installed=bool(out.strip()) and "versionName" in out, version=(re.findall(r"versionName=(\S+)", out) or [None])[0])
    DATA.mkdir(exist_ok=True); META.write_text(json.dumps(info, indent=2)); print(json.dumps(info, indent=2))
    if info["dnd_zen_mode"] == "0": print("WARNING: Do Not Disturb is off; popups will make captures get discarded.")
    if info["stay_on"] in ("0", ""): print("WARNING: Stay awake is off.")

def launch_component(pkg):
    out = adb(["shell","cmd","package","resolve-activity","--brief",pkg]).strip().splitlines()
    return out[-1].strip() if out and "/" in out[-1] else None

def cmd_launch(a):
    adb(["shell","monkey","-p",APPS[a.app],"-c","android.intent.category.LAUNCHER","1"]); time.sleep(a.wait); log_action("launch", a.app); print("fg:", foreground()[-80:])

def cmd_cold(a):
    pkg = APPS[a.app]; adb(["shell","am","force-stop",pkg]); time.sleep(1.5)
    comp = launch_component(pkg); total = None
    if comp:
        out = adb(["shell","am","start","-W","-n",comp], timeout=40); m = re.search(r"TotalTime:\s*(\d+)", out); total = int(m.group(1)) if m else None
    else:
        adb(["shell","monkey","-p",pkg,"-c","android.intent.category.LAUNCHER","1"])
    time.sleep(a.wait); log_action("cold-open", a.app, f"am_total_ms={total}"); log_flow(a, "cold-open", f"am_total_ms={total}")
    log_history("COLD-OPEN", f"{a.app} home loaded")
    do_capture(a, screen=a.screen or f"{a.app} home (cold open)", via="force-stop + launch", note=f"am start TotalTime={total}ms")

def cmd_capture(a): do_capture(a)

def cmd_ui(a):
    require_app(a.app); _, nodes = ui_nodes()
    if not nodes: sys.exit("uiautomator dump failed")
    bad = intruders(nodes, set(APPS.values()))
    if bad: sys.exit(f"other app on screen {bad}; not printing")
    for l in text_lines(nodes, APPS[a.app]):
        print(l)

def guarded_tap(a, nodes, x, y, desc):
    ok, why = check_tap(nodes, x, y, set(APPS.values()), *screen_wh())
    if not ok:
        log_action("tap", f"{a.app} {x},{y} {desc}", f"REFUSED: {why}"); log_flow(a, "tap", f"{x},{y} {desc}", f"REFUSED: {why}"); sys.exit(f"REFUSED: {why}")
    adb(["shell","input","tap",str(x),str(y)]); log_action("tap", f"{a.app} {x},{y} {desc}"); log_flow(a, "tap", f"{x},{y} {desc}")
    time.sleep(a.wait)
    _, after = ui_nodes()
    cv = commit_visible(after) if after else []
    if cv: print(f"!! COMMIT SCREEN VISIBLE {cv[:3]}: capture it, then back out. Do not tap further.")
    if getattr(a, "shot", False): do_capture(a)
    else: print("fg:", foreground()[-70:])

def cmd_tap(a):
    require_app(a.app); _, nodes = ui_nodes(); guarded_tap(a, nodes, a.x, a.y, a.note or "")

def cmd_tap_text(a):
    require_app(a.app); _, nodes = ui_nodes()
    if not nodes: sys.exit("no UI dump")
    rx = re.compile(f"^{a.pattern}$" if a.exact else a.pattern, re.I)
    found = sorted([n for n in nodes if n["pkg"] == APPS[a.app] and any(rx.search(norm(s)) for s in (n["text"], n["desc"]) if s)], key=lambda n: (n["t"], n["l"]))
    if not found: sys.exit(f"no element matching {a.pattern!r}")
    if a.first_ok:
        ok_nodes = [n for n in found if check_tap(nodes, (n["l"]+n["r"])//2, (n["t"]+n["b"])//2, set(APPS.values()), *screen_wh())[0]]
        if not ok_nodes: sys.exit("no matching element is visible and allowed")
        n = ok_nodes[0]; return guarded_tap(a, nodes, (n["l"]+n["r"])//2, (n["t"]+n["b"])//2, f"text~{a.pattern} (first allowed)")
    if len(found) > 1 and a.nth is None:
        for i, n in enumerate(found): print(i, f'{n["l"]},{n["t"]},{n["r"]},{n["b"]}', repr(norm(label(n))[:70]))
        sys.exit("several matches: pass --nth N")
    n = found[a.nth or 0]; guarded_tap(a, nodes, (n["l"]+n["r"])//2, (n["t"]+n["b"])//2, f"text~{a.pattern}")

def cmd_add_plain(a):
    """Tap the nth ADD button that has no 'N options' label under it (so no variant sheet opens)."""
    require_app(a.app); _, nodes = ui_nodes()
    if not nodes: sys.exit("no UI dump")
    H = screen_wh()[1]
    adds = [n for n in nodes if n["pkg"] == APPS[a.app] and norm(label(n)) == "ADD" and area(n) > 0 and 300 < n["t"] < H - 330]
    opts = [n for n in nodes if "option" in norm(label(n)).lower() and area(n) > 0]
    plain = sorted([n for n in adds if not any(abs(o["l"] - n["l"]) < 80 and 0 <= o["t"] - n["t"] <= 140 for o in opts)], key=lambda n: (n["t"], n["l"]))
    if len(plain) <= a.nth: sys.exit(f"only {len(plain)} plain ADD buttons on screen")
    n = plain[a.nth]; guarded_tap(a, nodes, (n["l"]+n["r"])//2, (n["t"]+n["b"])//2, "plain ADD")

def yellow_buttons(png_bytes, H=2400):
    """Find the yellow square '+' add buttons in a screenshot (Amazon Now draws them as pixels, not UI nodes)."""
    import io
    from PIL import Image
    im = Image.open(io.BytesIO(png_bytes)).convert("RGB"); W, Hh = im.size; st = 6
    px = im.load(); gw, gh = W // st, Hh // st
    mask = [[(lambda c: c[0] > 235 and 195 < c[1] < 235 and c[2] < 70)(px[x*st, y*st]) for x in range(gw)] for y in range(gh)]
    seen, out = set(), []
    for y in range(gh):
        for x in range(gw):
            if mask[y][x] and (x, y) not in seen:
                stack, cells = [(x, y)], []; seen.add((x, y))
                while stack:
                    cx, cy = stack.pop(); cells.append((cx, cy))
                    for nx, ny in ((cx+1, cy), (cx-1, cy), (cx, cy+1), (cx, cy-1)):
                        if 0 <= nx < gw and 0 <= ny < gh and mask[ny][nx] and (nx, ny) not in seen: seen.add((nx, ny)); stack.append((nx, ny))
                xs = [c[0]*st for c in cells]; ys = [c[1]*st for c in cells]
                w, h = max(xs)-min(xs)+st, max(ys)-min(ys)+st
                if 55 <= w <= 125 and 55 <= h <= 125 and 0.7 < w/h < 1.4 and 450 < min(ys) < H - 400:
                    out.append(((min(xs)+max(xs)+st)//2, (min(ys)+max(ys)+st)//2))
    return sorted(out, key=lambda p: (p[1] // 60, p[0]))

def cmd_add_yellow(a):
    require_app(a.app)
    with ThreadPoolExecutor(1) as ex:
        fut = ex.submit(ui_nodes); png = adb(["exec-out","screencap","-p"], binary=True); _, nodes = fut.result()
    pts = yellow_buttons(png, screen_wh()[1])
    if len(pts) <= a.nth: sys.exit(f"only {len(pts)} yellow add buttons found")
    x, y = pts[a.nth]; guarded_tap(a, nodes, x, y, "yellow +")

def cmd_swipe(a):
    require_app(a.app)
    y1, y2 = (a.y, a.y - a.dist) if a.direction == "up" else (a.y - 900, a.y - 900 + a.dist)
    for i in range(a.n):
        adb(["shell","input","swipe","540",str(y1),"540",str(y2),str(a.dur)]); log_action("swipe", f"{a.app} {a.direction} {a.dist}px"); log_flow(a, "swipe", f"{a.direction} {a.dist}px")
        time.sleep(a.wait)
        if a.capture and (i+1) % a.every == 0: do_capture(a, screen=a.screen, via=f"{a.via or 'scroll'} {a.direction} #{i+1}")
    if not a.capture: print("fg:", foreground()[-70:])

def cmd_back(a):
    require_app(a.app); adb(["shell","input","keyevent","4"]); log_action("back", a.app); log_flow(a, "back"); time.sleep(a.wait)
    if APPS[a.app] not in foreground():
        adb(["shell","monkey","-p",APPS[a.app],"-c","android.intent.category.LAUNCHER","1"]); time.sleep(3); print("left the app via Back; relaunched"); return
    if a.shot: do_capture(a)
    else: print("fg ok")

def cmd_search(a):
    q = a.query
    if not SAFE_WORD.fullmatch(q): sys.exit("only letters, digits, spaces allowed in queries")
    require_app(a.app); pkg = APPS[a.app]; _, nodes = ui_nodes()
    if not nodes: sys.exit("no UI dump; cannot locate search box safely")
    if intruders(nodes, set(APPS.values())): sys.exit("other app on screen")
    box = next((n for n in nodes if n["cls"].endswith("EditText") and n["pkg"] == pkg), None)
    if not box:
        icon = next((n for n in nodes if n["pkg"] == pkg and re.search(r"search", norm(label(n)), re.I) and n["t"] < 700), None)
        if not icon: sys.exit("search box/icon not found on this screen")
        adb(["shell","input","tap",str((icon["l"]+icon["r"])//2),str((icon["t"]+icon["b"])//2)]); time.sleep(2.5)
        require_app(a.app); _, nodes = ui_nodes()
        box = next((n for n in nodes if n["cls"].endswith("EditText") and n["pkg"] == pkg), None)
        if not box: sys.exit("search box did not open")
    if not box["focused"] or box["text"]:
        adb(["shell","input","tap",str((box["l"]+box["r"])//2),str((box["t"]+box["b"])//2)]); time.sleep(1)
    if box["text"] and not re.search(r"search", box["text"], re.I):
        adb(["shell","input","keycombination","113","29"]); adb(["shell","input","keyevent","67"]); time.sleep(0.5)
    adb(["shell","input","text",q.replace(" ","%s")]); time.sleep(1); adb(["shell","input","keyevent","66"])
    log_action("search", f"{a.app} {q}"); log_flow(a, "search", q); log_history("SEARCH", f"{a.app}: {q}"); time.sleep(a.wait)
    print("searched:", q, "| fg ok" if APPS[a.app] in foreground() else "| LEFT THE APP")

def cmd_log_history(a): log_history(a.kind.upper(), a.text); print("logged")

def cmd_rec(a):
    if a.table not in SCHEMAS: sys.exit(f"table must be one of {list(SCHEMAS)}")
    row = {c: "" for c in SCHEMAS[a.table]}
    for kv in a.pairs:
        k, _, v = kv.partition("=")
        if k not in row: sys.exit(f"unknown column {k!r}; columns: {SCHEMAS[a.table]}")
        row[k] = v
    ev = row.get("evidence_id") or row.get("stop_screen_id")
    if ev and not (SCREENS / f"{ev}.png").exists(): sys.exit(f"no screenshot {ev} on disk")
    p = DATA / f"{a.table}.csv"; new = not p.exists()
    with open(p, "a", newline="") as f:
        w = csv.DictWriter(f, SCHEMAS[a.table])
        if new: w.writeheader()
        w.writerow(row)
    print("recorded", a.table)

def rewrite_screens(rows):
    with open(CSV_SCREENS, "w", newline="") as f:
        w = csv.DictWriter(f, COLS); w.writeheader(); w.writerows(rows)

def cmd_annotate(a):
    lo, hi = a.ids.split("-") if "-" in a.ids else (a.ids, a.ids)
    rows = list(csv.DictReader(open(CSV_SCREENS)))
    for r in rows:
        if int(lo[1:]) <= int(r["id"][1:]) <= int(hi[1:]):
            for k in ("screen","via","signifies","note","scenario","app"):
                if getattr(a, k, None): r[k] = getattr(a, k)
    rewrite_screens(rows); print("annotated", a.ids)

def cmd_delete(a):
    rows = list(csv.DictReader(open(CSV_SCREENS))); found = False
    for r in rows:
        if r["id"] == a.id:
            found = True
            for k in ("png","xml","text"):
                if r[k]: (DATA / r[k]).unlink(missing_ok=True); r[k] = ""
            r["source"] = "deleted"; r["signifies"] = f"DELETED: {a.reason}"; r["note"] = ""
    if not found: sys.exit("no such id")
    rewrite_screens(rows); log_action("delete", a.id, a.reason); print("deleted", a.id)

def cmd_contact(a):
    from PIL import Image, ImageDraw
    ids = []
    for part in a.ids.split(","):
        lo, hi = part.split("-") if "-" in part else (part, part)
        ids += [f"s{i:04d}" for i in range(int(lo[1:]), int(hi[1:]) + 1) if (SCREENS / f"s{i:04d}.png").exists()]
    w = a.width; h = int(w * 2400 / 1080); cols = a.cols; rows = (len(ids) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * w, rows * (h + 24)), "white"); d = ImageDraw.Draw(sheet)
    for k, sid in enumerate(ids):
        im = Image.open(SCREENS / f"{sid}.png").convert("RGB").resize((w, h)); x, y = (k % cols) * w, (k // cols) * (h + 24)
        sheet.paste(im, (x, y + 24)); d.text((x + 4, y + 6), sid, fill="black")
    out = DATA / "contact_sheets"; out.mkdir(exist_ok=True); p = out / f"{a.name}.png"; sheet.save(p); print(p)

def main():
    p = argparse.ArgumentParser(description=__doc__); sp = p.add_subparsers(dest="cmd", required=True)
    com = argparse.ArgumentParser(add_help=False)
    com.add_argument("--app", required=True, choices=list(APPS))
    for k in ("scenario","screen","via","signifies","note"): com.add_argument(f"--{k}")
    com.add_argument("--step", type=int); com.add_argument("--show", action="store_true")
    sp.add_parser("preflight").set_defaults(f=cmd_preflight)
    def add(name, f, *extra, **kw):
        s = sp.add_parser(name, parents=[com]); s.set_defaults(f=f); return s
    s = add("launch", cmd_launch); s.add_argument("--wait", type=float, default=4)
    s = add("cold-open", cmd_cold); s.add_argument("--wait", type=float, default=8)
    add("capture", cmd_capture); add("ui", cmd_ui)
    s = add("tap", cmd_tap); s.add_argument("x", type=int); s.add_argument("y", type=int); s.add_argument("--wait", type=float, default=2.0); s.add_argument("--shot", action="store_true")
    s = add("tap-text", cmd_tap_text); s.add_argument("pattern"); s.add_argument("--nth", type=int); s.add_argument("--exact", action="store_true"); s.add_argument("--first-ok", action="store_true")
    s.add_argument("--wait", type=float, default=2.0); s.add_argument("--shot", action="store_true")
    s = add("add-plain", cmd_add_plain); s.add_argument("--nth", type=int, default=0); s.add_argument("--wait", type=float, default=2.2); s.add_argument("--shot", action="store_true")
    s = add("add-yellow", cmd_add_yellow); s.add_argument("--nth", type=int, default=0); s.add_argument("--wait", type=float, default=2.2); s.add_argument("--shot", action="store_true")
    s = add("swipe", cmd_swipe); s.add_argument("direction", choices=["up","down"]); s.add_argument("--n", type=int, default=1); s.add_argument("--dist", type=int, default=900)
    s.add_argument("--dur", type=int, default=500); s.add_argument("--y", type=int, default=1900); s.add_argument("--wait", type=float, default=1.2); s.add_argument("--capture", action="store_true"); s.add_argument("--every", type=int, default=1)
    s = add("back", cmd_back); s.add_argument("--wait", type=float, default=1.2); s.add_argument("--shot", action="store_true")
    s = add("search", cmd_search); s.add_argument("query"); s.add_argument("--wait", type=float, default=4)
    s = sp.add_parser("log-history"); s.add_argument("kind"); s.add_argument("text"); s.set_defaults(f=cmd_log_history)
    s = sp.add_parser("rec"); s.add_argument("table"); s.add_argument("pairs", nargs="*"); s.set_defaults(f=cmd_rec)
    s = sp.add_parser("annotate"); s.add_argument("ids")
    for k in ("scenario","screen","via","signifies","note","app"): s.add_argument(f"--{k}")
    s.set_defaults(f=cmd_annotate)
    s = sp.add_parser("delete"); s.add_argument("id"); s.add_argument("reason"); s.set_defaults(f=cmd_delete)
    s = sp.add_parser("contact"); s.add_argument("ids"); s.add_argument("--name", required=True); s.add_argument("--cols", type=int, default=6); s.add_argument("--width", type=int, default=270); s.set_defaults(f=cmd_contact)
    a = p.parse_args(); a.f(a)

if __name__ == "__main__": main()
