"""Builds the JSON payload the dashboard app renders from."""
import json, re, datetime, statistics
from collections import OrderedDict, defaultdict
from engine import load, normalise, build, band, is_dead, med
from narrative import analysis, feedback, rupees, days_live
from insights import build_insights, agg

TODAY  = datetime.date(2026, 8, 31)
PULLED = "31 August 2026, 7:15 PM IST"
ACCOUNT = "1346208828785334"

WINDOWS = OrderedDict([("l7", "Last 7 days"), ("l14", "Last 14 days"),
                       ("mtd", "Month to date"), ("d90", "Last 90 days")])
WDATES  = {"l7": "24–30 Aug 2026", "l14": "17–30 Aug 2026",
           "mtd": "1–31 Aug 2026", "d90": "2 Jun – 30 Aug 2026"}
WIDER   = {"l7": "l14", "l14": "mtd", "mtd": "d90", "d90": None}
SPARK   = ["d90", "mtd", "l14", "l7"]
SOURCES = {"l7": "l7.json", "l14": "ads_14d.json", "mtd": "mtd.json", "d90": "d90.json"}

CAT_ORDER  = ["House & Home", "Womenswear", "Menswear", "Jewellery", "Mixed", "Unmapped"]
ROLE_ORDER = ["Prospecting — Testing", "Prospecting — Scaling",
              "Prospecting — Scaling (legacy)", "Engaged Audience", "Existing Customers"]

# ----------------------------------------------------------- collection parsing
COLLECTIONS = ["Godavari","Yamuna","Ganga","Sindhu","Dhara","Asfar","Firefly","Retro",
               "Wonderland","NicoBaraat","Kolva","Narsa","Kutch","Costa","Bageecha","Zenith",
               "Mistari","Rayh","Dune","Breeze","Abeer","Midnight","Vaya","Nihra","Tuni",
               "Kinaar","Hera","Mehfil","Wadi","Ceylong","Gelato","Sorbet","Zodiac","Mogra",
               "Espresso","Polka","Spiti","Mati","Bena","Mason","Roohi","Smridhi","Manmeet",
               "Anushka","Khushboo","Divjyot","Aman","Shlok","Sahal","Udit","Rashi","Afshan",
               "TSS","RPS","Core-Refresh","Alphabet"]
PRODUCTS = ["Barware","Drinkware","Dinnerset","Dinnerware","Serveware","Tableware","Decor",
            "Cushion","Lighting","Gifting","Rakhi","Kurta","Kurtas","Shirt","Shirts","Polo",
            "Trouser","Trousers","Dress","Dresses","Tunic","Coord","Coords","Kaftan","Shacket",
            "Bandhgala","Tops","Linen","Fragrance","Mugs","Bookend","Cups","Dining","Textile",
            "Champagne","Votive","Spice","Giftset","Bestseller","Workwear","Eveningwear"]

def find_token(name, pool):
    up = name.upper()
    for t in sorted(pool, key=len, reverse=True):
        if re.search(rf"(?<![A-Z]){re.escape(t.upper())}(?![A-Z])", up):
            return t
    return None

def collection_of(r):
    return find_token(r["name"], COLLECTIONS) or "Unnamed"

def product_of(r):
    return find_token(r["name"], PRODUCTS) or "Other"

# ----------------------------------------------------------- confidence
def confidence(r):
    d = days_live(r, TODAY)
    if r["atc"] >= 40 and d >= 14 and r["imps"] >= 50000:
        return "solid",  "Solid read", \
               f"{int(r['atc'])} carts over {d} days — enough volume to act on."
    if r["atc"] >= 15 and d >= 7:
        return "moderate", "Moderate read", \
               f"{int(r['atc'])} carts over {d} days — directionally reliable, not precise."
    return "thin", "Thin read", \
           f"Only {int(r['atc'])} carts over {d} days — treat as an early signal, not a verdict."

# ----------------------------------------------------------- projection for empty states
def projection(r, cohort):
    """When will this creative have enough data to score?"""
    d = max(days_live(r, TODAY), 1)
    rate = r["atc"] / d
    if rate <= 0:
        return "No carts yet at current spend — no reliable date to project."
    need = max(0, 15 - r["atc"])
    if need == 0: return None
    days = need / rate
    when = TODAY + datetime.timedelta(days=round(days))
    return (f"At the current rate ({rate:.1f} carts a day) this should have enough volume "
            f"to score around {when.strftime('%-d %B')}.")

# ----------------------------------------------------------- build
raw = {k: normalise(load(v)) for k, v in SOURCES.items()}
res = build(raw, order=tuple(WINDOWS))

def spark_for(ad_id):
    out = []
    for w in SPARK:
        s = res[w]["scored"].get(ad_id)
        out.append(round(s["overall"] or s["pre"]) if s and (s["overall"] or s["pre"]) else None)
    return out

payload = {"pulled": PULLED, "account": ACCOUNT,
           "windows": [{"k": k, "label": v, "dates": WDATES[k]} for k, v in WINDOWS.items()],
           "data": {}}

for wkey in WINDOWS:
    scored  = res[wkey]["scored"]
    cohorts = res[wkey]["cohorts"]
    other   = [(WINDOWS[k], res[k]["scored"]) for k in WINDOWS if k != wkey]
    wider   = WIDER[wkey]
    ads = []
    for s in scored.values():
        ck = s["cohort"]
        meta = cohorts[ck]
        cls, clabel, cnote = confidence(s)
        fb, blk = feedback(s, meta, scored, TODAY)
        cur = s["overall"] or s["pre"]
        prev = None
        if wider and s["id"] in res[wider]["scored"]:
            p = res[wider]["scored"][s["id"]]
            prev = p["overall"] or p["pre"]
        delta = round(cur - prev) if (cur and prev) else None
        ads.append(dict(
            id=s["id"], cid=s.get("creative_id") or "", n=s["name"], th=s["th"] if "th" in s else s["theme"],
            c=ck[0], r=ck[1], ck=f"{ck[0]} | {ck[1]}", f=s["fmt"], d=s["dest"],
            col=collection_of(s), pt=product_of(s), vk=s["vkey"],
            st="Active" if s["status"] == "ACTIVE" else "Paused",
            dl=days_live(s, TODAY), camp=s["campaign"],
            pre=None if s["pre"] is None else round(s["pre"]),
            post=None if s["post"] is None else round(s["post"]),
            ov=None if s["overall"] is None else round(s["overall"]),
            preB=band(s["pre"]), postB=band(s["post"]), ovB=band(s["overall"]),
            rk=s["rank"], of=s["of"], pct=s["pct"], rankable=s["rankable"],
            dead=is_dead(s["overall"]),
            conf=cls, confL=clabel, confN=cnote,
            delta=delta, spark=spark_for(s["id"]),
            an=analysis(s, meta, other), fb=fb, fbBlock=blk,
            proj=projection(s, meta) if s["post"] is None else None,
            m=dict(sp=round(s["spend"]), im=int(s["imps"]), cpm=round(s["cpm"], 1),
                   ctr=round(s["octr"], 2), c2l=round(s["clk2lpv"]), lpv=int(s["lpv"]),
                   l2a=round(s["lpv2atc"], 1), atc=int(s["atc"]),
                   cpa=round(s["cpatc"]) if s["cpatc"] else None, pur=int(s["pur"]),
                   rev=round(s["rev"]), roas=round(s["roas"], 2) if s["roas"] else None,
                   fq=round(s["freq"], 2),
                   aov=round(s["rev"] / s["pur"]) if s["pur"] else None),
        ))

    # ---- cohort meta + opening brief
    cmeta = {}
    for ck, m in cohorts.items():
        members = [a for a in ads if a["ck"] == f"{ck[0]} | {ck[1]}"]
        if not members: continue
        movers = [a for a in members if a["delta"] is not None]
        risers  = sorted(movers, key=lambda a: -a["delta"])[:1]
        fallers = sorted(movers, key=lambda a:  a["delta"])[:1]
        newish  = [a for a in members if a["dl"] <= 10]
        top3rd  = max(1, len(members) // 3)
        top_ids = [a["id"] for a in sorted(members, key=lambda a: -(a["ov"] or a["pre"] or 0))[:top3rd]]
        new_in_top = [a for a in newish if a["id"] in top_ids]

        brief = []
        if risers and risers[0]["delta"] >= 6:
            a = risers[0]
            brief.append(f"<b>{a['th']}</b> moved {a['delta']:+d} points against "
                         f"{WINDOWS[wider].lower()} and now sits {a['ovB'].lower()} for the group. "
                         f"Whatever it is doing, it is doing more of it.")
        if fallers and fallers[0]["delta"] <= -6:
            a = fallers[0]
            brief.append(f"<b>{a['th']}</b> dropped {a['delta']:+d} points over the same "
                         f"comparison. Worth a look before the next batch repeats it.")
        if new_in_top:
            brief.append(f"<b>{len(new_in_top)} of the {len(newish)} creatives launched in the "
                         f"last 10 days</b> already sit in the top third of this group — the "
                         f"latest batch is landing.")
        elif newish:
            brief.append(f"<b>None of the {len(newish)} creatives launched in the last 10 days</b> "
                         f"has reached the top third yet. The most recent batch has not produced "
                         f"a winner in this group.")
        gaps = []
        for a in members:
            if a["pre"] is not None and a["post"] is not None:
                gaps.append((a["post"] - a["pre"], a))
        att = [g for g in gaps if g[0] <= -18]
        if att:
            worst = min(att, key=lambda g: g[0])[1]
            brief.append(f"<b>{len(att)} creatives</b> are pulling attention well ahead of what "
                         f"they convert — <i>{worst['th']}</i> is the widest gap. That pattern is "
                         f"a destination or promise problem, not an image problem.")
        if not brief:
            brief.append("Nothing moved materially in this group over this window. "
                         "No action indicated — read it again next week.")

        fmts = defaultdict(list)
        for a in members: fmts[a["f"]].append(a)
        fstrip = sorted(
            [dict(f=f, n=len(v), sp=sum(x["m"]["sp"] for x in v),
                  pre=round(med([x["pre"] for x in v if x["pre"] is not None]) or 0),
                  post=round(med([x["post"] for x in v if x["post"] is not None]) or 0))
             for f, v in fmts.items()], key=lambda x: -x["sp"])

        cmeta[f"{ck[0]} | {ck[1]}"] = dict(
            cat=ck[0], role=ck[1], n=m["n"], spend=round(m["spend"]),
            atc=int(m["atc"]), pur=int(m["purchases"]), attribution=m["attribution"],
            profile=m["profile"], pcw=m["postclick_window"], pcq=m["postclick_quality"],
            pcAtc=int(m.get("post_atc", 0)), pcPur=int(m.get("post_pur", 0)),
            rankable=m["rankable"],
            cat_roas=round(max([x["roas"] for x in m["catalogue"]], default=0), 2),
            cat_spend=round(max([x["spend"] for x in m["catalogue"]], default=0)),
            beat=sum(1 for a in members if (a["m"]["roas"] or 0) > max(
                     [x["roas"] for x in m["catalogue"]], default=1e9)),
            brief=brief, fstrip=fstrip,
        )

    payload["data"][wkey] = dict(
        ads=ads, cohorts=cmeta,
        insights=[dict(t=t, b=b, d=d) for t, b, d in build_insights(scored, cohorts)],
        totals=dict(n=len(ads), sp=round(sum(a["m"]["sp"] for a in ads)),
                    pur=sum(a["m"]["pur"] for a in ads)),
    )

order = sorted(payload["data"]["d90"]["cohorts"].keys(),
               key=lambda k: (CAT_ORDER.index(k.split(" | ")[0]) if k.split(" | ")[0] in CAT_ORDER else 9,
                              ROLE_ORDER.index(k.split(" | ")[1]) if k.split(" | ")[1] in ROLE_ORDER else 9))
payload["cohortOrder"] = order

json.dump(payload, open("payload.json", "w"), separators=(",", ":"))
print("payload written")
for w in WINDOWS:
    print(f"  {w}: {len(payload['data'][w]['ads'])} ads, "
          f"{len(payload['data'][w]['cohorts'])} cohorts, "
          f"{len(payload['data'][w]['insights'])} insights")
