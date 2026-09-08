"""Nicobar Creative Dashboard v2 — parsing, cohorts, scoring.

Key differences from v1:
  * Flat metric weights everywhere; only the Pre/Post split varies by cohort type.
  * A zero is a real zero. Weights are retained, never redistributed, and
    "Data Inadequate" no longer exists for legitimately-zero values.
  * Spend floors govern RANKING POSITION only, never scoring.
  * No post-click window escalation. Every score comes from its own window.
  * Funnel stage comes from the CAMPAIGN, never the ad name.
"""
import json, re, statistics, datetime
from collections import defaultdict

# ------------------------------------------------------------------ campaigns
# (category, role, code, funnel, attribution)
CAMPAIGNS = {
 "120252436936770415": ("House & Home", "Prospecting — Testing",          "NB-011", "TOF", "7d click"),
 "120252437283850415": ("House & Home", "Prospecting — Scaling",          "NB-012", "TOF", "7d click"),
 "120233715509180415": ("House & Home", "Prospecting — Scaling (legacy)", "NB-009", "TOF", "7d click + 1d view"),
 "120252491393710415": ("Womenswear",   "Prospecting — Testing",          "NB-013", "TOF", "7d click"),
 "120252726847590415": ("Womenswear",   "Prospecting — Scaling",          "NB-014", "TOF", "7d click"),
 "120233622016290415": ("Womenswear",   "Prospecting — Scaling (legacy)", "NB-008", "TOF", "7d click + 1d view"),
 "120252726994950415": ("Menswear",     "Prospecting — Testing",          "NB-015", "TOF", "7d click"),
 "120252763493400415": ("Menswear",     "Prospecting — Scaling",          "NB-016", "TOF", "7d click"),
 "120234793803270415": ("Menswear",     "Prospecting — Scaling (legacy)", "NB-010", "TOF", "7d click + 1d view"),
 "120215613504970415": ("Jewellery",    "Prospecting — Scaling",          "FE-104", "TOF", "7d click + 1d view"),
 "120252763633010415": (None, "Engaged Audience",   "NB-017", "MOF", "7d click"),
 "120226657999510415": (None, "Engaged Audience",   "NB-002", "MOF", "7d click + 1d view"),
 "120242266774960415": (None, "Existing Customers", "NB-019", "BOF", "7d click + 1d view"),
 "120242316351330415": (None, "Existing Customers", "NB-021", "BOF", "7d click + 1d view"),
 "120213134553500415": (None, "Existing Customers", "FE-100", "BOF", "7d click + 1d view"),
}

# ------------------------------------------------------------------ scoring
# Flat weights. Same metrics, same weights, every cohort.
PRE  = [("cpm", False, 40), ("octr", True, 30), ("clk2lpv", True, 30)]
POST = [("roas", True, 45), ("cpatc", False, 20), ("pur", True, 20), ("lpv2atc", True, 15)]

# Only the Pre/Post split varies.
SPLIT = {"testing": (0.40, 0.60), "other": (0.20, 0.80)}

# Spend floors — RANKING ONLY. Never affects scoring.
FLOORS = {"Prospecting — Testing": 2000,
          "Prospecting — Scaling": 5000,
          "Prospecting — Scaling (legacy)": 5000,
          "Engaged Audience": 2000,
          "Existing Customers": 2000}

BANDS = [(65, "Strong"), (55, "Above par"), (45, "At par"), (35, "Below par"), (0, "Weak")]
DEAD  = [(52, 58), (42, 48)]
SMALL_SAMPLE_PURCHASES = 5      # flag a strong post-click score built on fewer

CATEGORY_TOKENS = [("-HH-", "House & Home"), ("-WW-", "Womenswear"),
                   ("-MW-", "Menswear"), ("-JW-", "Jewellery"), ("-ACC-", "Jewellery")]

COLLECTIONS = ["Godavari","Yamuna","Ganga","Sindhu","Dhara","Asfar","Firefly","Retro",
               "Wonderland","NicoBaraat","Kolva","Narsa","Kutch","Costa","Bageecha","Zenith",
               "Mistari","Rayh","Dune","Breeze","Abeer","Midnight","Vaya","Nihra","Tuni",
               "Kinaar","Hera","Mehfil","Wadi","Ceylong","Gelato","Sorbet","Zodiac","Mogra",
               "Espresso","Polka","Spiti","Mati","Bena","Mason","Roohi","Nicosera","Core",
               "TSS","RPS","Alphabet","Brass","Rakhi"]
PRODUCTS = ["Barware","Drinkware","Dinnerset","Dinnerware","Serveware","Tableware","Decor",
            "Cushion","Lighting","Gifting","Rakhi","Kurta","Kurtas","Shirt","Shirts","Polo",
            "Trouser","Trousers","Dress","Dresses","Tunic","Coord","Coords","Kaftan","Shacket",
            "Bandhgala","Tops","Linen","Fragrance","Mugs","Bookend","Cups","Giftset","Platter"]

# ------------------------------------------------------------------ parsing
def money(s):
    if s is None: return None
    v = re.sub(r"[^\d.]", "", str(s))
    return float(v) if v else None

def num(s):
    if s in (None, ""): return 0.0
    try: return float(s)
    except (TypeError, ValueError): return 0.0

def parse_category(name):
    up = name.upper()
    for tok, cat in CATEGORY_TOKENS:
        if tok in up: return cat
    if "-MIX-" in up: return "Mixed"
    return None

def parse_format(name):
    up = name.upper()
    if "CATALOGUE" in up or "CATALOG" in up or "DPA" in up: return "Catalogue/Dynamic"
    partnership = "PARTNERSHIP" in up or "CREATOR" in up
    base = "SNG"
    for k, label in (("CAROUSEL","Carousel"), ("VIDEO","Video"), ("GIF","GIF"), ("SNG","SNG")):
        if re.search(rf"(?<![A-Z]){k}(?![A-Z])", up):
            base = label; break
    if partnership: return base + "-Partnership"
    return base

def parse_destination(name):
    up = name.upper()
    if "-PDP" in up: return "PDP"
    if "-PLP" in up: return "PLP"
    return None

def find_token(name, pool):
    up = name.upper()
    for t in sorted(pool, key=len, reverse=True):
        if re.search(rf"(?<![A-Z]){re.escape(t.upper())}(?![A-Z])", up): return t
    return None

def parse_theme(name):
    stop = {"SNG","GIF","VIDEO","CAROUSEL","CATALOGUE","CATALOG","PDP","PLP","HH","WW",
            "MW","JW","ACC","MIX","PARTNERSHIP","COPY","AI","NEWAD","BOF","TOF","MOF","DPA"}
    out = []
    for p in re.split(r"[-\s]+", name):
        u = p.upper().strip()
        if not u or u in stop: continue
        if re.fullmatch(r"(NB|FE|ET|TH)", u): continue
        if re.fullmatch(r"[A-Z]\d{2}", u): continue
        if re.fullmatch(r"V\d", u): continue
        if re.fullmatch(r"D-?\d+", u): continue
        if re.fullmatch(r"\d+", u): continue
        out.append(p.strip())
    return " ".join(out[:4]) if out else name

def variant_key(name):
    s = re.sub(r"[-\s]+(V\d|Copy(\s*\d)?)\b", "", name, flags=re.I)
    s = re.sub(r"[-\s]*\d{6}\s*$", "", s)
    return s.strip(" -")

def load(path):
    d = json.load(open(path))
    if isinstance(d, list) and d and isinstance(d[0], dict) and "text" in d[0]: 
        d = json.loads(d[0]["text"])
    if isinstance(d, list): return d
    e = d["ad_entities"]
    return json.loads(e) if isinstance(e, str) else e

# ------------------------------------------------------------------ normalise
def normalise(entities, nomen=None):
    from nomenclature import lookup as nlookup
    nomen = nomen or {}
    rows = {}
    for e in entities:
        spend = money(e.get("amount_spent")); imps = num(e.get("impressions"))
        if not spend or spend <= 0 or imps <= 0: continue
        c = CAMPAIGNS.get(e.get("campaign_id"))
        if not c: continue
        name = e["name"]
        cat = c[0] or parse_category(name) or "Unmapped"
        oc  = num(e.get("outbound_clicks")); lpv = num(e.get("omni_landing_page_view"))
        atc = num(e.get("omni_add_to_cart")); pur = num(e.get("omni_purchase"))
        tag = nlookup(name, nomen) if nomen else {}
        fmt = parse_format(name)
        rows[e["id"]] = dict(
            id=e["id"], creative_id=e.get("creative_id") or "", name=name,
            campaign=c[2], category=cat, role=c[1], funnel=c[3], attribution=c[4],
            fmt=fmt, theme=parse_theme(name), dest=parse_destination(name),
            collection=find_token(name, COLLECTIONS) or "Other",
            product=find_token(name, PRODUCTS) or "Other",
            vkey=variant_key(name),
            partnership="Partnership" if "Partnership" in fmt else "Non-Partnership",
            # nomenclature attributes — empty until the sheet is joined
            angle=tag.get("angle"), silhouette=tag.get("silhouette"),
            subcategory=tag.get("subcategory"), pclass=tag.get("class"),
            sheet_collection=tag.get("collection_sheet"),
            vo=tag.get("vo"), ai=tag.get("ai"), tagged=bool(tag),
            status="Active" if e.get("effective_status") == "ACTIVE" else "Paused",
            created=(e.get("created_time") or "")[:10],
            spend=spend, imps=imps, reach=num(e.get("reach")), freq=num(e.get("frequency")),
            cpm=money(e.get("cpm")) or 0.0, oc=oc, octr=num(e.get("outbound_clicks_ctr")),
            lpv=lpv, atc=atc, pur=pur,
            rev=money(e.get("omni_purchase_values")) or 0.0,
            roas=num(e.get("purchase_roas")),
            cpatc=money(e.get("cost_per_omni_add_to_cart")) or 0.0,
            ic=num(e.get("omni_initiated_checkout")),
            clk2lpv=(lpv / oc * 100) if oc else 0.0,
            lpv2atc=(atc / lpv * 100) if lpv else 0.0,
        )
    return rows

# ------------------------------------------------------------------ helpers
def band(score):
    if score is None: return "Not available"
    for lo, label in BANDS:
        if score >= lo: return label
    return "Weak"

def is_dead(score):
    return score is not None and any(lo <= score <= hi for lo, hi in DEAD)

def med(vals):
    vals = [v for v in vals if v is not None and v > 0]
    return statistics.median(vals) if vals else None

def metric_score(value, median, higher_better):
    """Cohort median anchors at 50; twice-median caps at 100.

    A legitimately zero value scores 0 — it is not missing data. Where the whole
    cohort is zero (median is None) every ad scores 0 on that metric and the
    weight is still counted, so Overall falls rather than being redistributed.
    """
    if value is None: return 0.0
    if median in (None, 0): return 0.0
    if higher_better:
        if value <= 0: return 0.0
        ratio = value / median
    else:
        if value <= 0: return 0.0          # no cost recorded = no delivery credit
        ratio = median / value
    return max(0.0, min(100.0, 50.0 * ratio))

def block_score(row, medians, metrics):
    """Weights are ALWAYS retained. Never redistributed."""
    total = sum(w for _, _, w in metrics)
    acc = sum(metric_score(row.get(m), medians.get(m), hi) * w for m, hi, w in metrics)
    return acc / total

def profile_of(role):
    return "testing" if role == "Prospecting — Testing" else "other"

def cohort_key(r): return (r["category"], r["role"])

# ------------------------------------------------------------------ build
def build(windows, order):
    out = {}
    for wname in order:
        rows = windows[wname]
        groups = defaultdict(list)
        for r in rows.values():
            if r["fmt"] == "Catalogue/Dynamic": continue     # benchmark only
            groups[cohort_key(r)].append(r)

        scored, cmeta = {}, {}
        for ck, members in groups.items():
            role = members[0]["role"]
            floor = FLOORS.get(role, 2000)
            # medians come from ABOVE-FLOOR ads only; sub-floor ads are scored
            # against the benchmark but never help set it
            basis = [m for m in members if m["spend"] >= floor] or members
            pre_med  = {m: med([x[m] for x in basis]) for m, _, _ in PRE}
            post_med = {m: med([x[m] for x in basis]) for m, _, _ in POST}

            tot_pur = sum(x["pur"] for x in members)
            zero_sales = tot_pur == 0
            w_pre, w_post = SPLIT[profile_of(role)]

            for r in members:
                pre  = block_score(r, pre_med,  PRE)
                post = block_score(r, post_med, POST)
                overall = pre * w_pre + post * w_post
                s = dict(r)
                s.update(pre=pre, post=post, overall=overall, cohort=ck,
                         above_floor=r["spend"] >= floor, floor=floor,
                         small_sample=(r["pur"] < SMALL_SAMPLE_PURCHASES and post >= 55),
                         zero_sales_cohort=zero_sales)
                scored[r["id"]] = s

            ranked = sorted([scored[m["id"]] for m in members if scored[m["id"]]["above_floor"]],
                            key=lambda x: -x["overall"])
            for i, s in enumerate(ranked, 1):
                s["rank"], s["of"] = i, len(ranked)
                s["pct"] = round(100 * i / len(ranked))
            for m in members:
                s = scored[m["id"]]
                s.setdefault("rank", None); s.setdefault("of", len(ranked)); s.setdefault("pct", None)

            cmeta[ck] = dict(
                cat=ck[0], role=ck[1], funnel=members[0]["funnel"], n=len(members),
                ranked=len(ranked), floor=floor, profile=profile_of(role),
                w_pre=w_pre, w_post=w_post,
                spend=sum(x["spend"] for x in members),
                atc=sum(x["atc"] for x in members), pur=tot_pur,
                rev=sum(x["rev"] for x in members),
                zero_sales=zero_sales, attribution=members[0]["attribution"],
                catalogue=[x for x in rows.values()
                           if x["fmt"] == "Catalogue/Dynamic" and cohort_key(x) == ck],
                pre_med=pre_med, post_med=post_med,
            )
        out[wname] = dict(scored=scored, cohorts=cmeta)
    return out

# ------------------------------------------------------------------ decline
def derive_prior(wide_rows, narrow_rows):
    """Prior period = wide window minus narrow window, by subtraction.

    Only RATE metrics are trustworthy here — the day counts are uneven
    (L30 minus L14 leaves 16 days, not 14), so volumes are not comparable.
    """
    prior = {}
    for aid, w in wide_rows.items():
        n = narrow_rows.get(aid)
        if not n: continue
        d = {k: w[k] - n[k] for k in ("spend", "imps", "oc", "lpv", "atc", "pur", "rev")}
        if d["imps"] <= 0 or d["spend"] <= 0: continue
        prior[aid] = dict(
            cpm=d["spend"] / d["imps"] * 1000,
            octr=(d["oc"] / d["imps"] * 100) if d["imps"] else 0,
            clk2lpv=(d["lpv"] / d["oc"] * 100) if d["oc"] else 0,
            lpv2atc=(d["atc"] / d["lpv"] * 100) if d["lpv"] else 0,
            roas=(d["rev"] / d["spend"]) if d["spend"] else 0,
        )
    return prior

def decline_read(cur, prior):
    """Fatigue surfaces only as decline against the ad's own prior performance."""
    if not prior: return None
    def ch(k, better_low=False):
        a, b = cur.get(k, 0), prior.get(k, 0)
        if not b: return None
        p = (a - b) / b * 100
        return -p if better_low else p
    ctr, cpm, cart, roas = ch("octr"), ch("cpm", True), ch("lpv2atc"), ch("roas")
    pre_down  = [x for x in (ctr, cpm) if x is not None and x <= -15]
    post_down = [x for x in (cart, roas) if x is not None and x <= -15]
    if not pre_down and not post_down: return None
    return dict(ctr=ctr, cpm=cpm, cart=cart, roas=roas,
                pre_down=bool(pre_down), post_down=bool(post_down))
