"""v2 payload builder."""
import json, os, csv, datetime
from collections import OrderedDict, defaultdict
from engine import (load, normalise, build, band, is_dead, med,
                    derive_prior, decline_read, FLOORS, PRE, POST, SPLIT)
from narrative import analysis, feedback, rupees, days_live
from insights import section_insights, brand_insights, growth_insights, agg

TODAY   = datetime.date(2026, 9, 8)
PULLED  = "8 September 2026, 3:40 PM IST"
ACCOUNT = "1346208828785334"

WINDOWS = OrderedDict([("l7",  "Last 7 days"), ("l14", "Last 14 days"),
                       ("l30", "Last 30 days"), ("aug", "August")])
WDATES  = {"l7": "1–7 Sep 2026", "l14": "25 Aug – 7 Sep 2026",
           "l30": "9 Aug – 7 Sep 2026", "aug": "1–31 Aug 2026"}
# prior period for the decline read, derived by subtraction
PRIOR   = {"l7": ("l14", "the 7 days before that"),
           "l14": ("l30", "the two weeks before that")}
SOURCES = {k: f"{k}.json" for k in WINDOWS}

CAT_ORDER  = ["House & Home", "Womenswear", "Menswear", "Jewellery", "Mixed", "Unmapped"]
ROLE_ORDER = ["Prospecting — Testing", "Prospecting — Scaling",
              "Prospecting — Scaling (legacy)", "Engaged Audience", "Existing Customers"]

# ---------------------------------------------------------------- nomenclature
def load_nomenclature():
    """Attribute table is hard-coded in nomenclature.py — no external file needed."""
    from nomenclature import TABLE
    print(f"  nomenclature: {len(TABLE)} tagged ad names")
    return TABLE

# ---------------------------------------------------------------- confidence
def confidence(r, d):
    if r["pur"] >= 20 and d >= 14 and r["imps"] >= 50000:
        return "solid", "Solid read", (f"{int(r['pur'])} orders over {d} days — enough volume "
                                       f"to act on.")
    if r["pur"] >= 5 and d >= 7:
        return "moderate", "Moderate read", (f"{int(r['pur'])} orders over {d} days — "
                                             f"directionally reliable, not precise.")
    return "thin", "Thin read", (f"Only {int(r['pur'])} orders over {d} days — an early signal, "
                                 f"not a verdict.")

# ---------------------------------------------------------------- build
nomen = load_nomenclature()
raw = {k: normalise(load(v), nomen) for k, v in SOURCES.items()}
res = build(raw, tuple(WINDOWS))

def image_name(name):
    return "".join(c if c.isalnum() or c in "-_ ." else "_" for c in name)

payload = {"pulled": PULLED, "account": ACCOUNT,
           "windows": [{"k": k, "label": v, "dates": WDATES[k]} for k, v in WINDOWS.items()],
           "floors": FLOORS,
           "weights": {"pre": [[m, w] for m, _, w in PRE],
                       "post": [[m, w] for m, _, w in POST],
                       "split": SPLIT},
           "data": {}}

for wkey in WINDOWS:
    scored, cohorts = res[wkey]["scored"], res[wkey]["cohorts"]
    other = [(WINDOWS[k], res[k]["scored"]) for k in WINDOWS if k != wkey]

    prior, plabel = {}, None
    if wkey in PRIOR:
        wide, plabel = PRIOR[wkey]
        prior = derive_prior(raw[wide], raw[wkey])

    ads = []
    for s in scored.values():
        ck = s["cohort"]; meta = cohorts[ck]
        d = days_live(s, TODAY)
        cls, clabel, cnote = confidence(s, d)
        dec = decline_read(s, prior.get(s["id"])) if prior else None
        fb, blk = feedback(s, meta, scored, TODAY)
        ads.append(dict(
            id=s["id"], cid=s["creative_id"], n=s["name"], img=image_name(s["name"]),
            th=s["theme"], c=ck[0], r=ck[1], ck=f"{ck[0]} | {ck[1]}", fn=s["funnel"],
            f=s["fmt"], d=s["dest"], col=s["collection"], pt=s["product"],
            pship=s["partnership"], vk=s["vkey"], camp=s["campaign"],
            angle=s["angle"], sil=s["silhouette"], sub=s["subcategory"],
            vo=s["vo"], ai=s["ai"], tagged=s["tagged"],
            st=s["status"], dl=d,
            pre=round(s["pre"]), post=round(s["post"]), ov=round(s["overall"]),
            preB=band(s["pre"]), postB=band(s["post"]), ovB=band(s["overall"]),
            rk=s["rank"], of=s["of"], pct=s["pct"], ranked=s["above_floor"],
            floor=s["floor"], dead=is_dead(s["overall"]),
            small=s["small_sample"], zero=s["zero_sales_cohort"],
            conf=cls, confL=clabel, confN=cnote,
            dec=dec, decP=plabel,
            an=analysis(s, meta, plabel, dec, other), fb=fb, fbBlock=blk,
            m=dict(sp=round(s["spend"]), im=int(s["imps"]), cpm=round(s["cpm"], 1),
                   ctr=round(s["octr"], 2), c2l=round(s["clk2lpv"]), lpv=int(s["lpv"]),
                   l2a=round(s["lpv2atc"], 1), atc=int(s["atc"]),
                   cpa=round(s["cpatc"]) if s["cpatc"] else None, pur=int(s["pur"]),
                   rev=round(s["rev"]), roas=round(s["roas"], 2) if s["roas"] else None,
                   fq=round(s["freq"], 2), aov=round(s["rev"]/s["pur"]) if s["pur"] else None),
        ))

    cmeta = {}
    for ck, m in cohorts.items():
        members = [a for a in ads if a["ck"] == f"{ck[0]} | {ck[1]}"]
        if not members: continue
        rows = [scored[a["id"]] for a in members]
        movers = [(a, res[PRIOR[wkey][0]]["scored"].get(a["id"])) for a in members] if wkey in PRIOR else []
        brief = []
        deltas = [(a, a["ov"] - p["overall"]) for a, p in movers if p]
        if deltas:
            up = max(deltas, key=lambda x: x[1]); dn = min(deltas, key=lambda x: x[1])
            if up[1] >= 6:
                brief.append(f"<b>{up[0]['th']}</b> is {up[1]:+.0f} points against "
                             f"{WINDOWS[PRIOR[wkey][0]].lower()} and now reads "
                             f"{up[0]['ovB'].lower()} for the group.")
            if dn[1] <= -6:
                brief.append(f"<b>{dn[0]['th']}</b> is {dn[1]:+.0f} points over the same "
                             f"comparison — worth a look before the next batch repeats it.")
        declining = [a for a in members if a["dec"]]
        if declining:
            pre_d = [a for a in declining if a["dec"]["pre_down"]]
            post_d = [a for a in declining if a["dec"]["post_down"] and not a["dec"]["pre_down"]]
            if pre_d:
                brief.append(f"<b>{len(pre_d)} creative{'s' if len(pre_d)>1 else ''}</b> "
                             f"{'are' if len(pre_d)>1 else 'is'} losing attention against "
                             f"{plabel} — clicks falling or cost to serve rising. That is wear, "
                             f"and it does not get fixed after the click.")
            if post_d:
                brief.append(f"<b>{len(post_d)}</b> {'are' if len(post_d)>1 else 'is'} holding "
                             f"attention but converting worse than {plabel} — the change is "
                             f"happening after the click.")
        newish = [a for a in members if a["dl"] <= 10]
        if newish:
            ranked_m = sorted([a for a in members if a["ranked"]], key=lambda a: -a["ov"])
            top3 = {a["id"] for a in ranked_m[:max(1, len(ranked_m)//3)]}
            hits = [a for a in newish if a["id"] in top3]
            brief.append(f"<b>{len(hits)} of the {len(newish)} creatives launched in the last "
                         f"10 days</b> {'already sit' if hits else 'sit'} in the top third — "
                         + ("the latest batch is landing." if hits else
                            "the most recent batch has not produced a winner here yet."))
        gaps = [(a["post"] - a["pre"], a) for a in members]
        att = [g for g in gaps if g[0] <= -18]
        if att:
            w = min(att, key=lambda g: g[0])[1]
            brief.append(f"<b>{len(att)} creatives</b> pull attention well ahead of what they "
                         f"convert — <i>{w['th']}</i> is the widest gap. That is a destination "
                         f"or promise problem, not an image problem.")
        if m["zero_sales"]:
            brief.insert(0, "<b>No orders at all in this group this window.</b> ROAS and "
                            "purchase scores are zero for every creative here, so Overall "
                            "reflects reach and cart behaviour only.")
        if not brief:
            brief.append("Nothing moved materially in this group over this window.")

        fmts = defaultdict(list)
        for a in members: fmts[a["f"]].append(a)
        fstrip = sorted([dict(f=f, n=len(v), sp=sum(x["m"]["sp"] for x in v),
                              pre=round(med([x["pre"] for x in v]) or 0),
                              post=round(med([x["post"] for x in v]) or 0))
                         for f, v in fmts.items()], key=lambda x: -x["sp"])

        cmeta[f"{ck[0]} | {ck[1]}"] = dict(
            cat=ck[0], role=ck[1], funnel=m["funnel"], n=m["n"], ranked=m["ranked"],
            floor=m["floor"], profile=m["profile"], wPre=int(m["w_pre"]*100),
            wPost=int(m["w_post"]*100), spend=round(m["spend"]), atc=int(m["atc"]),
            pur=int(m["pur"]), rev=round(m["rev"]), zero=m["zero_sales"],
            attribution=m["attribution"],
            cat_roas=round(max([x["roas"] for x in m["catalogue"]], default=0), 2),
            cat_spend=round(max([x["spend"] for x in m["catalogue"]], default=0)),
            beat=sum(1 for a in members if (a["m"]["roas"] or 0) >
                     max([x["roas"] for x in m["catalogue"]], default=1e9)),
            brief=brief, fstrip=fstrip,
            ins=[dict(t=t, b=b, d=d) for t, b, d in section_insights(rows, m)],
        )

    T = agg([scored[a["id"]] for a in ads])
    payload["data"][wkey] = dict(
        ads=ads, cohorts=cmeta,
        brand=[dict(t=t, b=b, d=d) for t, b, d in brand_insights(scored, cohorts)],
        growth=[dict(t=t, b=b, d=d) for t, b, d in growth_insights(scored, cohorts, T)],
        totals=dict(n=len(ads), sp=round(T["spend"]), pur=int(T["pur"]),
                    rev=round(T["rev"]), atc=int(T["atc"]),
                    ranked=sum(1 for a in ads if a["ranked"]),
                    active=sum(1 for a in ads if a["st"] == "Active"),
                    tagged=sum(1 for a in ads if a["tagged"])),
        prior=plabel)

payload["cohortOrder"] = sorted(
    {k for w in WINDOWS for k in payload["data"][w]["cohorts"]},
    key=lambda k: (CAT_ORDER.index(k.split(" | ")[0]) if k.split(" | ")[0] in CAT_ORDER else 9,
                   ROLE_ORDER.index(k.split(" | ")[1]) if k.split(" | ")[1] in ROLE_ORDER else 9))

json.dump(payload, open("payload.json", "w"), separators=(",", ":"))
print("payload written")
for w in WINDOWS:
    d = payload["data"][w]
    print(f"  {w}: {d['totals']['n']} ads ({d['totals']['ranked']} ranked), "
          f"{len(d['cohorts'])} cohorts, brand {len(d['brand'])}, growth {len(d['growth'])}")
