"""v2 payload builder."""
import json, os, csv, datetime
from collections import OrderedDict, defaultdict
from engine import (load, normalise, build, band, is_dead, med,
                    derive_prior, decline_read, format_baseline,
                    FLOORS, PRE, POST, SPLIT)
from narrative import analysis, feedback, rupees, days_live
from insights import (section_brand, section_growth, brand_insights,
                      growth_insights, patterns, agg)

TODAY   = datetime.date(2026, 9, 9)
PULLED  = "9 September 2026, 11:15 PM IST"
ACCOUNT = "1346208828785334"

WINDOWS = OrderedDict([("l7",  "Last 7 days"), ("l14", "Last 14 days"),
                       ("l30", "Last 30 days"), ("aug", "August")])
WDATES  = {"l7": "2–8 Sep 2026", "l14": "26 Aug – 8 Sep 2026",
           "l30": "10 Aug – 8 Sep 2026", "aug": "1–31 Aug 2026"}
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

# Format medians across 1 Aug -> today, so a card can say whether a Video-Partnership
# ad is weak in absolute terms or just weak for a Video-Partnership ad.
BASELINE = format_baseline(normalise(load("baseline.json"), nomen))
BASELINE_LABEL = "1 Aug – 9 Sep 2026"

def base_for(ck, fmt):
    """Cohort-specific format median, falling back to account-wide only when the
    cohort has too few of that format to read. The fallback is flagged so the card
    never implies a cohort median it does not have."""
    c = BASELINE.get(ck, {}).get(fmt)
    if c:
        return dict(pre=c["pre"], post=c["post"], ov=c["ov"], n=c["n"], scope="cohort")
    a = BASELINE.get("__all__", {}).get(fmt)
    if a:
        return dict(pre=a["pre"], post=a["post"], ov=a["ov"], n=a["n"], scope="account")
    return None
print(f"  format baseline: {len(BASELINE)-1} cohorts + account-wide, over {BASELINE_LABEL}")

def image_name(name):
    return "".join(c if c.isalnum() or c in "-_ ." else "_" for c in name)

payload = {"pulled": PULLED, "account": ACCOUNT,
           "windows": [{"k": k, "label": v, "dates": WDATES[k]} for k, v in WINDOWS.items()],
           "floors": FLOORS,
           "baseline": BASELINE, "baselineLabel": BASELINE_LABEL,
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
            pov=s["pov"], structure=s["structure"], persona=s["persona"],
            angleTxt=s["angle_text"], sil=s["silhouette"], sub=s["subcategory"],
            pcls=s["pclass"], src=s["asset_src"], occ=s["occasion"],
            vo=s["vo"], ai=s["ai"], tagged=s["tagged"],
            vid=(dict(plays=int(s["vplays"]), thru=int(s["vthru"]),
                      rate=round(s["vplays"] / s["imps"] * 100, 1) if s["imps"] else 0,
                      p25=round(s["v25"] / s["vplays"] * 100) if s["vplays"] else 0,
                      p50=round(s["v50"] / s["vplays"] * 100) if s["vplays"] else 0,
                      p100=round(s["v100"] / s["vplays"] * 100) if s["vplays"] else 0,
                      n25=int(s["v25"]), n50=int(s["v50"]), n100=int(s["v100"]))
                 if s["is_video"] and s["vplays"] else None),
            base=base_for(f"{ck[0]} | {ck[1]}", s["fmt"]),
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
            brief=brief, fstrip=fstrip, agg=False, subs=[f"{ck[0]} | {ck[1]}"],
            insB=[dict(t=t, b=b, d=d) for t, b, d in section_brand(rows, m)],
            insG=[dict(t=t, b=b, d=d) for t, b, d in section_growth(rows, m)],
        )

    # ---------------- aggregate roll-ups for the menu -------------------
    def rollup(label, members, sub_keys):
        if len(members) < 2 or len(sub_keys) < 2: return
        rows2 = [scored[a["id"]] for a in members]
        A = agg(rows2)
        fmts = defaultdict(list)
        for a2 in members: fmts[a2["f"]].append(a2)
        fstrip = sorted([dict(f=f, n=len(v), sp=sum(x["m"]["sp"] for x in v),
                              pre=round(med([x["pre"] for x in v]) or 0),
                              post=round(med([x["post"] for x in v]) or 0))
                         for f, v in fmts.items()], key=lambda x: -x["sp"])
        best = max(members, key=lambda a2: a2["ov"])
        worst = min(members, key=lambda a2: a2["ov"])
        brief = [f"This is a combined view of <b>{len(sub_keys)} groups</b>. Each creative keeps "
                 f"the score it earned inside its own group, so a 60 here and a 60 there are "
                 f"both 'ahead of its own peers' rather than the same absolute standard.",
                 f"Strongest is <b>{best['th']}</b> at {best['ov']}, weakest "
                 f"<b>{worst['th']}</b> at {worst['ov']}.",
                 f"{sum(1 for a2 in members if not a2['ranked'])} of {len(members)} sit below "
                 f"their group's spend floor and carry no rank."]
        pseudo = dict(floor=0, catalogue=[])
        cmeta[label] = dict(
            subs=sorted(sub_keys),
            cat=label.split(" | ")[0], role=label.split(" | ")[1],
            funnel="—", n=len(members),
            ranked=sum(1 for a2 in members if a2["ranked"]), floor=0, profile="mixed",
            wPre=0, wPost=0, spend=round(A["spend"]), atc=int(A["atc"]), pur=int(A["pur"]),
            rev=round(A["rev"]), zero=A["pur"] == 0, attribution="mixed",
            cat_roas=0, cat_spend=0, beat=0, brief=brief, fstrip=fstrip, agg=True,
            insB=[dict(t=t, b=b, d=d) for t, b, d in section_brand(rows2, pseudo)],
            insG=[dict(t=t, b=b, d=d) for t, b, d in section_growth(rows2, pseudo)])

    by_cat = defaultdict(list)
    for a2 in ads: by_cat[a2["c"]].append(a2)
    for cat, members in by_cat.items():
        pros = [a2 for a2 in members if a2["r"].startswith("Prospecting")]
        rollup(f"{cat} | Prospecting (All)", pros, {a2["ck"] for a2 in pros})
        rollup(f"{cat} | All audiences", members, {a2["ck"] for a2 in members})

    # ---------------- duplication: same creative running in more than one campaign
    dup = defaultdict(list)
    for a2 in ads:
        k = a2["cid"] or ("name:" + a2["img"])
        dup[k].append(a2)
    dups = []
    for k, group in dup.items():
        camps = {a2["camp"] for a2 in group}
        if len(camps) < 2: continue
        rows2 = [scored[a2["id"]] for a2 in group]
        A = agg(rows2)
        dups.append(dict(
            key=k, n=len(group), th=group[0]["th"], f=group[0]["f"],
            img=group[0]["img"], cid=group[0]["cid"],
            camps=sorted(camps), cohorts=sorted({a2["ck"] for a2 in group}),
            spend=round(A["spend"]), imps=int(A["imps"]), lpv=int(A["lpv"]),
            atc=int(A["atc"]), pur=int(A["pur"]), rev=round(A["rev"]),
            roas=round(A["roas"], 2), cpm=round(A["cpm"], 1),
            l2a=round(A["lpv2atc"], 1), c2l=round(A["clk2lpv"]),
            aov=round(A["aov"]) if A["pur"] else None,
            cpa=round(A["cpa"]) if A["pur"] else None,
            attributions=sorted({raw[wkey][a2["id"]]["attribution"] for a2 in group}),
            legs=sorted([dict(camp=a2["camp"], ck=a2["ck"], adid=a2["id"],
                              sp=a2["m"]["sp"], imp=a2["m"]["im"], pur=a2["m"]["pur"],
                              rev=a2["m"]["rev"], roas=a2["m"]["roas"], ov=a2["ov"],
                              pre=a2["pre"], post=a2["post"], ranked=a2["ranked"],
                              st=a2["st"]) for a2 in group], key=lambda x: -x["sp"]),
        ))
    dups.sort(key=lambda d: -d["spend"])

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
        prior=plabel, dups=dups)

# ---------------- patterns, computed once per window with the next as comparison
_order = list(WINDOWS)
for idx, wkey in enumerate(_order):
    byW = OrderedDict()
    for k in _order[idx:] + _order[:idx]:
        byW[k] = dict(label=WINDOWS[k], scored=res[k]["scored"])
    payload["data"][wkey]["patterns"] = [
        dict(t=t, b=b, d=d) for t, b, d in patterns(byW, res[wkey]["cohorts"])]

ROLE_SORT = ROLE_ORDER + ["Prospecting (All)", "All audiences"]
def _rk(k):
    c, r = k.split(" | ")
    agg_rank = 0 if r in ("Prospecting (All)", "All audiences") else 1
    return (CAT_ORDER.index(c) if c in CAT_ORDER else 9,
            agg_rank,
            ROLE_SORT.index(r) if r in ROLE_SORT else 9)
payload["cohortOrder"] = sorted(
    {k for w in WINDOWS for k in payload["data"][w]["cohorts"]}, key=_rk)

json.dump(payload, open("payload.json", "w"), separators=(",", ":"))
print("payload written")
for w in WINDOWS:
    d = payload["data"][w]
    print(f"  {w}: {d['totals']['n']} ads ({d['totals']['ranked']} ranked), "
          f"{len(d['cohorts'])} cohorts, brand {len(d['brand'])}, growth {len(d['growth'])}")
