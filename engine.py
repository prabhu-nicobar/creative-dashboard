"""Nicobar Creative Dashboard — parsing, cohort assignment and scoring engine."""
import json, re, statistics, datetime
from collections import defaultdict

# ---------------------------------------------------------------- campaign map
CAMPAIGNS = {
 "120252436936770415": ("House & Home", "Prospecting — Testing",  "NB-011", "low",  "7d click"),
 "120252437283850415": ("House & Home", "Prospecting — Scaling",  "NB-012", "high", "7d click"),
 "120233715509180415": ("House & Home", "Prospecting — Scaling (legacy)", "NB-009", "high", "7d click + 1d view"),
 "120252491393710415": ("Womenswear",   "Prospecting — Testing",  "NB-013", "low",  "7d click"),
 "120252726847590415": ("Womenswear",   "Prospecting — Scaling",  "NB-014", "high", "7d click"),
 "120233622016290415": ("Womenswear",   "Prospecting — Scaling (legacy)", "NB-008", "high", "7d click + 1d view"),
 "120252726994950415": ("Menswear",     "Prospecting — Testing",  "NB-015", "low",  "7d click"),
 "120252763493400415": ("Menswear",     "Prospecting — Scaling",  "NB-016", "high", "7d click"),
 "120234793803270415": ("Menswear",     "Prospecting — Scaling (legacy)", "NB-010", "high", "7d click + 1d view"),
 "120215613504970415": ("Jewellery",    "Prospecting — Scaling",  "FE-104", "high", "7d click + 1d view"),
 "120252763633010415": (None, "Engaged Audience",   "NB-017", "high", "7d click"),
 "120226657999510415": (None, "Engaged Audience",   "NB-002", "high", "7d click + 1d view"),
 "120242266774960415": (None, "Existing Customers", "NB-019", "high", "7d click + 1d view"),
 "120242316351330415": (None, "Existing Customers", "NB-021", "high", "7d click + 1d view"),
 "120213134553500415": (None, "Existing Customers", "FE-100", "high", "7d click + 1d view"),
}

CATEGORY_TOKENS = [("-HH-", "House & Home"), ("-WW-", "Womenswear"),
                   ("-MW-", "Menswear"), ("-JW-", "Jewellery"), ("-ACC-", "Jewellery")]

# ---------------------------------------------------------------- parsing
def money(s):
    if s is None: return None
    v = re.sub(r"[^\d.]", "", str(s))
    return float(v) if v else None

def num(s):
    if s in (None, ""): return 0
    try: return float(s)
    except (TypeError, ValueError): return 0

def parse_category(name):
    up = name.upper()
    for tok, cat in CATEGORY_TOKENS:
        if tok in up: return cat
    if "-MIX-" in up: return "Mixed"
    return None

def parse_format(name):
    up = name.upper()
    if "CATALOGUE" in up or "CATALOG" in up: return "Catalogue"
    partnership = "PARTNERSHIP" in up or "CREATOR" in up
    base = None
    for k in ("SNG", "GIF", "CAROUSEL", "VIDEO"):
        # tolerate the FE-104-A01SNG- naming defect (missing hyphen)
        if re.search(rf"[-A-Z0-9]{k}[-]", up) or f"-{k}-" in up or f"{k}-" in up:
            base = {"SNG": "SNG", "GIF": "GIF", "CAROUSEL": "Carousel", "VIDEO": "Video"}[k]
            break
    if base is None: base = "SNG"
    if partnership and base == "Video": return "Video-Partnership"
    if partnership and base == "Carousel": return "Carousel-Partnership"
    return base

def parse_destination(name):
    up = name.upper()
    if "-PDP" in up: return "PDP"
    if "-PLP" in up: return "PLP"
    return None

def parse_theme(name):
    """Product / collection theme — the thing the creative is actually about."""
    stop = {"SNG","GIF","VIDEO","CAROUSEL","CATALOGUE","CATALOG","PDP","PLP","HH","WW",
            "MW","JW","ACC","MIX","A01","A02","A03","A04","A05","A06","A07","A08","A09",
            "PARTNERSHIP","COPY","V1","V2","V3","V4","AI","NEWAD","BOF","TOF","MOF"}
    parts = re.split(r"[-\s]+", name)
    out = []
    for p in parts:
        u = p.upper().strip()
        if not u or u in stop: continue
        if re.fullmatch(r"(NB|FE|ET|TH)\d*", u): continue
        if re.fullmatch(r"D-?\d+", u): continue
        if re.fullmatch(r"\d+", u): continue
        if re.fullmatch(r"(NB|FE|ET|TH)", u): continue
        if re.fullmatch(r"[A-Z]\d{2}", u): continue
        out.append(p.strip())
    return " ".join(out[:4]) if out else name

def variant_key(name):
    """Strip variant suffixes so V1/V2/V3 of one concept group together."""
    s = re.sub(r"[-\s]*[-\s](V\d|Copy(\s*\d)?)\b", "", name, flags=re.I)
    s = re.sub(r"[-\s]*\d{6}\s*$", "", s)
    return s.strip(" -")

def load(path):
    d = json.load(open(path))
    if isinstance(d, list) and d and isinstance(d[0], dict) and "text" in d[0]:
        d = json.loads(d[0]["text"])
    if isinstance(d, list):          # already a plain list of ad dicts
        return d
    e = d["ad_entities"]
    if isinstance(e, str): e = json.loads(e)
    return e

def normalise(entities):
    rows = {}
    for e in entities:
        spend = money(e.get("amount_spent"))
        imps  = num(e.get("impressions"))
        if not spend or spend <= 0 or imps <= 0:
            continue                                   # active spend only
        c = CAMPAIGNS.get(e.get("campaign_id"))
        if not c: continue
        cat = c[0] or parse_category(e["name"]) or "Unmapped"
        fmt = parse_format(e["name"])
        oc  = num(e.get("outbound_clicks"))
        lpv = num(e.get("omni_landing_page_view"))
        atc = num(e.get("omni_add_to_cart"))
        pur = num(e.get("omni_purchase"))
        rows[e["id"]] = dict(
            id=e["id"], creative_id=e.get("creative_id") or "", name=e["name"], campaign=c[2], category=cat, role=c[1],
            profile=c[3], attribution=c[4], fmt=fmt, theme=parse_theme(e["name"]),
            dest=parse_destination(e["name"]), vkey=variant_key(e["name"]),
            status=e.get("effective_status"), created=e.get("created_time", "")[:10],
            spend=spend, imps=imps, reach=num(e.get("reach")), freq=num(e.get("frequency")),
            cpm=money(e.get("cpm")) or 0, oc=oc,
            octr=num(e.get("outbound_clicks_ctr")), lpv=lpv, atc=atc, pur=pur,
            rev=money(e.get("omni_purchase_values")) or 0,
            roas=num(e.get("purchase_roas")),
            cpatc=money(e.get("cost_per_omni_add_to_cart")) or 0,
            ic=num(e.get("omni_initiated_checkout")),
            clk2lpv=(lpv / oc * 100) if oc else 0,
            lpv2atc=(atc / lpv * 100) if lpv else 0,
        )
    return rows

# ---------------------------------------------------------------- scoring
# metric -> (higher_is_better, block)
PRE  = [("cpm", False), ("octr", True), ("clk2lpv", True)]
POST = [("lpv2atc", True), ("cpatc", False), ("roas", True), ("pur", True)]

W_PRE  = {"high": {"cpm": .25, "octr": .325, "clk2lpv": .425},
          "low":  {"cpm": 1/3, "octr": 1/3,  "clk2lpv": 1/3}}
W_POST = {"high": {"lpv2atc": .167, "cpatc": .083, "roas": .50, "pur": .25},
          "low":  {"lpv2atc": .40,  "cpatc": .20,  "roas": .20, "pur": .20}}
W_OVERALL = {"high": 0.40, "low": 0.60}          # weight on pre-click

BANDS = [(65, "Strong"), (55, "Above par"), (45, "At par"), (35, "Below par"), (0, "Weak")]
DEAD  = [(52, 58), (42, 48)]

def band(score):
    if score is None: return "Data Inadequate"
    for lo, label in BANDS:
        if score >= lo: return label
    return "Weak"

def is_dead(score):
    return score is not None and any(lo <= score <= hi for lo, hi in DEAD)

def med(vals):
    vals = [v for v in vals if v is not None and v > 0]
    return statistics.median(vals) if vals else None

def metric_score(value, median, higher_better):
    """Cohort median anchors at 50; twice-median caps at 100."""
    if median in (None, 0): return None
    if value is None: return None
    ratio = (value / median) if higher_better else (median / max(value, 1e-9))
    return max(0.0, min(100.0, 50.0 * ratio))

def block_score(row, medians, weights, metrics):
    tot = acc = 0.0
    for m, higher in metrics:
        s = metric_score(row.get(m), medians.get(m), higher)
        if s is None: continue
        w = weights[m]; acc += s * w; tot += w
    return (acc / tot) if tot > 0 else None

# ---------------------------------------------------------------- cohort build
# Preferred floor — enough volume to rank post-click confidently.
POSTCLICK_FLOOR_ATC = 15      # cohort median ATC
POSTCLICK_FLOOR_PUR = 30      # cohort total purchases
# Minimum floor — thin, but real enough to show a Post-Click rank with a warning
# rather than leaving the brand team with a blank. Applied at the widest window only.
POSTCLICK_MIN_ATC = 20        # cohort total add-to-carts
POSTCLICK_MIN_PUR = 3         # cohort total purchases
MIN_COHORT_FOR_RANK = 5
RANK_EXEMPT = {("Menswear", "Prospecting — Testing")}   # too new to rank

def cohort_key(r): return (r["category"], r["role"])

def cohort_passes_postclick(rows):
    """Preferred floor: confident post-click ranking."""
    if not rows: return False
    m = med([r["atc"] for r in rows])
    return (m or 0) >= POSTCLICK_FLOOR_ATC and sum(r["pur"] for r in rows) >= POSTCLICK_FLOOR_PUR

def cohort_meets_minimum(rows):
    """Minimum floor: thin but readable — score it, and say so loudly."""
    if not rows: return False
    return (sum(r["atc"] for r in rows) >= POSTCLICK_MIN_ATC
            and sum(r["pur"] for r in rows) >= POSTCLICK_MIN_PUR)

def build(windows, order=("l7", "l14", "mtd")):
    """windows: {'l7': {id: row}, 'l14': ..., 'mtd': ...}. Returns nested results."""
    out = {}
    for wname in order:
        rows = windows[wname]
        scored = {}
        groups = defaultdict(list)
        for r in rows.values():
            if r["fmt"] == "Catalogue":   # benchmark only, never scored
                continue
            groups[cohort_key(r)].append(r)

        cohort_meta = {}
        for ck, members in groups.items():
            profile = members[0]["profile"]
            pre_med = {m: med([x[m] for x in members]) for m, _ in PRE}

            # ---- post-click window escalation, at cohort level -----------
            # Widen the window until the post-click read is trustworthy. Never blank
            # the rank while any real cart/order volume exists somewhere in 30 days.
            def widen(w):
                return [windows[w][r["id"]] for r in members if r["id"] in windows[w]]

            ladder = [wname] + [w for w in ("l14", "mtd") if w != wname]
            src, post_members, quality = wname, members, "none"
            for w in ladder:                       # first pass: preferred floor
                cand = widen(w)
                if cand and cohort_passes_postclick(cand):
                    src, post_members, quality = w, cand, "full"
                    break
            if quality == "none":                  # second pass: minimum floor
                for w in reversed(ladder):         # widest first
                    cand = widen(w)
                    if cand and cohort_meets_minimum(cand):
                        src, post_members, quality = w, cand, "thin"
                        break
            post_med = {m: med([x[m] for x in post_members]) for m, _ in POST}
            post_ok = quality != "none"

            rankable = len(members) >= MIN_COHORT_FOR_RANK and ck not in RANK_EXEMPT
            cohort_meta[ck] = dict(
                n=len(members), profile=profile, postclick_window=src,
                postclick_ok=post_ok, postclick_quality=quality, rankable=rankable,
                post_atc=sum(x["atc"] for x in post_members),
                post_pur=sum(x["pur"] for x in post_members),
                spend=sum(x["spend"] for x in members),
                purchases=sum(x["pur"] for x in members),
                atc=sum(x["atc"] for x in members),
                med_atc=med([x["atc"] for x in members]) or 0,
                attribution=members[0]["attribution"],
                catalogue=[x for x in rows.values()
                           if x["fmt"] == "Catalogue" and cohort_key(x) == ck],
                pre_med=pre_med, post_med=post_med,
            )

            post_by_id = {x["id"]: x for x in post_members}
            for r in members:
                pre = block_score(r, pre_med, W_PRE[profile], PRE)
                pr = post_by_id.get(r["id"])
                post = block_score(pr, post_med, W_POST[profile], POST) if (pr and post_ok) else None
                if pre is not None and post is not None:
                    w = W_OVERALL[profile]
                    overall = pre * w + post * (1 - w)
                elif pre is not None and not post_ok:
                    overall = None
                else:
                    overall = pre
                s = dict(r)
                s.update(pre=pre, post=post, overall=overall,
                         post_src=src, rankable=rankable, cohort=ck,
                         post_row=pr)
                scored[r["id"]] = s

        # percentile within cohort on overall (falls back to pre)
        for ck, members in groups.items():
            vals = sorted([scored[r["id"]].get("overall") or scored[r["id"]].get("pre") or 0
                           for r in members], reverse=True)
            for r in members:
                s = scored[r["id"]]
                v = s.get("overall") or s.get("pre") or 0
                s["pct"] = round(100 * (vals.index(v) + 1) / len(vals))
                s["rank"] = vals.index(v) + 1
                s["of"] = len(vals)
        out[wname] = dict(scored=scored, cohorts=cohort_meta)
    return out
