"""v2 insights — two audiences, and every insight computed from its own section's data.

v1 generated one blanket set per window and repeated it everywhere. That was wrong.
Here, `section_insights` is called per cohort/section and sees only that data;
`brand_insights` and `growth_insights` build the two dedicated navigation sections.
"""
from collections import defaultdict
from engine import med

def rupees(v): return "₹" + format(int(round(v or 0)), ",")

def agg(rows):
    sp = sum(r["spend"] for r in rows); rev = sum(r["rev"] for r in rows)
    pur = sum(r["pur"] for r in rows); atc = sum(r["atc"] for r in rows)
    lpv = sum(r["lpv"] for r in rows); oc = sum(r["oc"] for r in rows)
    imp = sum(r["imps"] for r in rows)
    return dict(n=len(rows), spend=sp, rev=rev, pur=pur, atc=atc, lpv=lpv, oc=oc, imps=imp,
                aov=(rev/pur) if pur else 0, roas=(rev/sp) if sp else 0,
                cpm=(sp/imp*1000) if imp else 0,
                lpv2atc=(atc/lpv*100) if lpv else 0, clk2lpv=(lpv/oc*100) if oc else 0,
                atc2pur=(pur/atc*100) if atc else 0, cpa=(sp/pur) if pur else 0)

def _split(rows, key, minimum=2):
    d = defaultdict(list)
    for r in rows:
        v = r.get(key)
        if v: d[v].append(r)
    return {k: v for k, v in d.items() if len(v) >= minimum}

# ------------------------------------------------------------ per-section
def section_insights(rows, meta):
    """Insights computed from ONE cohort's own data. Never reused elsewhere."""
    if not rows: return []
    out, a = [], agg(rows)

    # winning format inside this cohort only
    fm = _split(rows, "fmt")
    if len(fm) >= 2:
        scored = sorted(((f, len(v), med([x["pre"] for x in v]) or 0,
                          med([x["post"] for x in v]) or 0, agg(v))
                         for f, v in fm.items()), key=lambda x: -(x[2]+x[3])/2)
        best, worst = scored[0], scored[-1]
        att = max(scored, key=lambda x: x[2]); sell = max(scored, key=lambda x: x[3])
        body = (f"In this group specifically, <b>{best[0]}</b> is performing best overall "
                f"({best[1]} live, {rupees(best[4]['spend'])}). ")
        if att[0] != sell[0]:
            body += (f"But the split matters: <b>{att[0]}</b> earns the most attention while "
                     f"<b>{sell[0]}</b> converts best. Briefing only the first would fill the "
                     f"funnel and starve the till.")
        else:
            body += (f"<b>{worst[0]}</b> is the weakest at {(worst[2]+worst[3])/2:.0f} against "
                     f"{(best[2]+best[3])/2:.0f} — worth asking whether it earns its slot here.")
        out.append(("Format that works in this group", body,
                    " · ".join(f"{f}: {n} live, pre {p:.0f} / post {q:.0f}"
                               for f, n, p, q, _ in scored)))

    # destination inside this cohort only
    de = _split(rows, "dest")
    if len(de) >= 2 and "PDP" in de and "PLP" in de:
        p, l = agg(de["PDP"]), agg(de["PLP"])
        better = "PDP" if p["lpv2atc"] > l["lpv2atc"] else "PLP"
        body = (f"Here, {better} creatives convert visitors to cart better "
                f"({max(p['lpv2atc'], l['lpv2atc']):.1f}% against "
                f"{min(p['lpv2atc'], l['lpv2atc']):.1f}%).")
        if p["aov"] and l["aov"] and abs(p["aov"]-l["aov"])/max(p["aov"], l["aov"]) > 0.12:
            rich = "PDP" if p["aov"] > l["aov"] else "PLP"
            body += (f" But {rich} orders are worth more ({rupees(max(p['aov'], l['aov']))} "
                     f"against {rupees(min(p['aov'], l['aov']))}), so the cheaper conversion "
                     f"is not automatically the better one in this group.")
        out.append(("Where to send people, in this group", body,
                    f"PDP: {len(de['PDP'])} creatives, {rupees(p['spend'])} · "
                    f"PLP: {len(de['PLP'])} creatives, {rupees(l['spend'])}"))

    # collection standing inside this cohort only
    co = _split(rows, "collection", 2)
    co = {k: v for k, v in co.items() if k != "Other"}
    if len(co) >= 2:
        s = sorted(((k, len(v), med([x["overall"] for x in v]) or 0, agg(v))
                    for k, v in co.items()), key=lambda x: -x[2])
        top, bot = s[0], s[-1]
        out.append(("Collections carrying this group",
                    f"<b>{top[0]}</b> is the strongest collection running here (median "
                    f"{top[2]:.0f} across {top[1]} creatives, {rupees(top[3]['spend'])}), and "
                    f"<b>{bot[0]}</b> the weakest ({bot[2]:.0f}). If the gap holds next week it "
                    f"is a product signal as much as a creative one — worth checking whether "
                    f"{bot[0]} is being asked to do something the range can't support.",
                    " · ".join(f"{k}: {n} live, median {m:.0f}" for k, n, m, _ in s[:6])))

    # angle, only once the nomenclature sheet is joined
    an = _split(rows, "angle")
    if len(an) >= 2:
        s = sorted(((k, len(v), med([x["overall"] for x in v]) or 0) for k, v in an.items()),
                   key=lambda x: -x[2])
        out.append(("Which angle lands here",
                    f"<b>{s[0][0]}</b> is the strongest angle in this group (median "
                    f"{s[0][2]:.0f} across {s[0][1]} creatives) and <b>{s[-1][0]}</b> the "
                    f"weakest ({s[-1][2]:.0f}). Angle is the closest thing in this data to a "
                    f"brief, so this is the most directly actionable line on the page.",
                    " · ".join(f"{k}: {n} live, median {m:.0f}" for k, n, m in s)))

    # the group's own funnel shape
    out.append(("How this group's funnel behaves",
                f"{int(a['oc']):,} clicks became {int(a['lpv']):,} page views "
                f"({a['clk2lpv']:.0f}%), then {int(a['atc']):,} carts "
                f"({a['lpv2atc']:.1f}%), then {int(a['pur']):,} orders "
                f"({a['atc2pur']:.1f}% of carts). "
                + ("With no orders at all this window, the only half of the funnel you can "
                   "read here is the top." if not a["pur"] else
                   f"An order here is worth {rupees(a['aov'])} and costs {rupees(a['cpa'])} "
                   f"to win."),
                f"{a['n']} creatives · {rupees(a['spend'])} · CPM {rupees(a['cpm'])} · "
                f"blended {a['roas']:.2f}x"))
    return out

# ------------------------------------------------------------ Brand section
def brand_insights(scored, cohorts):
    rows = list(scored.values())
    out = []
    by_cat = _split(rows, "category", 3)

    for cat, v in sorted(by_cat.items(), key=lambda x: -sum(r["spend"] for r in x[1])):
        a = agg(v)
        stages = defaultdict(list)
        for r in v: stages[r["funnel"]].append(r)
        parts = []
        for st in ("TOF", "MOF", "BOF"):
            if st not in stages: continue
            sa = agg(stages[st])
            parts.append(f"{st} runs {sa['n']} creatives on {rupees(sa['spend'])} at "
                         f"{sa['lpv2atc']:.1f}% to cart")
        fm = _split(v, "fmt")
        fbest = sorted(((f, med([x["overall"] for x in u]) or 0, len(u))
                        for f, u in fm.items()), key=lambda x: -x[1])
        body = (f"{'. '.join(parts)}. " if parts else "")
        if fbest:
            body += (f"Across the whole category <b>{fbest[0][0]}</b> leads on median score "
                     f"({fbest[0][1]:.0f} over {fbest[0][2]} creatives)")
            if len(fbest) > 1:
                body += f" and <b>{fbest[-1][0]}</b> trails ({fbest[-1][1]:.0f})"
            body += ". "
        if a["pur"]:
            body += (f"An order in {cat} is worth {rupees(a['aov'])}, so the same conversion "
                     f"improvement is worth more or less here than elsewhere — weigh creative "
                     f"effort accordingly.")
        out.append((f"{cat} — what the creative is doing", body,
                    f"{a['n']} creatives · {rupees(a['spend'])} · {int(a['pur'])} orders · "
                    f"AOV {rupees(a['aov'])} · {a['lpv2atc']:.1f}% to cart"))

    # stage-level read across all categories
    by_stage = _split(rows, "funnel", 3)
    for st, label in (("TOF", "Prospecting"), ("MOF", "Engaged"), ("BOF", "Existing customers")):
        if st not in by_stage: continue
        v = by_stage[st]; a = agg(v)
        fm = sorted(((f, med([x["overall"] for x in u]) or 0, len(u))
                     for f, u in _split(v, "fmt").items()), key=lambda x: -x[1])
        de = _split(v, "dest")
        dpart = ""
        if "PDP" in de and "PLP" in de:
            p, l = agg(de["PDP"]), agg(de["PLP"])
            dpart = (f" Destination matters differently at this stage: PDP converts at "
                     f"{p['lpv2atc']:.1f}% against PLP at {l['lpv2atc']:.1f}%.")
        out.append((f"{st} — {label}",
                    f"{a['n']} creatives on {rupees(a['spend'])}, reaching cart at "
                    f"{a['lpv2atc']:.1f}% and converting {a['atc2pur']:.1f}% of those carts. "
                    + (f"<b>{fm[0][0]}</b> is the strongest format at this stage "
                       f"({fm[0][1]:.0f} median). " if fm else "") + dpart,
                    f"AOV {rupees(a['aov'])} · CPM {rupees(a['cpm'])} · "
                    f"{int(a['pur'])} orders"))

    # variant spread — the strongest craft evidence available
    fam = defaultdict(list)
    for r in rows: fam[(r["cohort"], r["vkey"])].append(r)
    multi = [(max(x["overall"] for x in v) - min(x["overall"] for x in v), k, v)
             for k, v in fam.items() if len(v) > 1]
    big = [m for m in multi if m[0] >= 20]
    if multi:
        multi.sort(reverse=True, key=lambda x: x[0])
        w = multi[0]
        out.append(("Same idea, different execution",
                    f"<b>{len(big)} of {len(multi)}</b> concepts running more than one version "
                    f"show a gap of 20 points or more between best and worst. The widest is "
                    f"<i>{w[2][0]['theme']}</i> at {w[0]:.0f} points. Same product, same "
                    f"audience, same offer — the entire difference is execution. This is the "
                    f"cheapest place to find a win, because the shoot already happened.",
                    " · ".join(f"{v[0]['theme'][:32]}: {g:.0f} pts" for g, k, v in multi[:5])))
    return out

# ------------------------------------------------------------ Growth section
def growth_insights(scored, cohorts, totals):
    rows = list(scored.values())
    out = []
    a = agg(rows)

    # summary
    active = sum(1 for r in rows if r["status"] == "Active")
    ranked = sum(1 for r in rows if r["above_floor"])
    cat_spend = sorted(((k, sum(x["spend"] for x in v)) for k, v in _split(rows, "category", 1).items()),
                       key=lambda x: -x[1])
    stage_spend = sorted(((k, sum(x["spend"] for x in v)) for k, v in _split(rows, "funnel", 1).items()),
                         key=lambda x: -x[1])
    out.append(("Account summary",
                f"<b>{a['n']} creatives</b> carried spend this window — {active} still active, "
                f"{a['n']-active} paused. <b>{ranked}</b> cleared their cohort's spend floor and "
                f"are ranked; the remaining {a['n']-ranked} are shown but unranked. Total "
                f"<b>{rupees(a['spend'])}</b> producing {int(a['pur']):,} orders at "
                f"{rupees(a['cpa'])} each, {a['roas']:.2f}x blended.",
                "Spend by category — " + " · ".join(f"{k}: {rupees(v)}" for k, v in cat_spend) +
                " || By stage — " + " · ".join(f"{k}: {rupees(v)}" for k, v in stage_spend)))

    # attribution distortion between legacy and current
    legacy = [r for r in rows if "legacy" in r["role"]]
    current = [r for r in rows if r["role"] == "Prospecting — Scaling"]
    if legacy and current:
        L, C = agg(legacy), agg(current)
        out.append(("Legacy campaigns are flattered by their attribution window",
                    f"The legacy scaling campaigns (NB-008, NB-009, NB-010, FE-104) still run "
                    f"7-day click plus 1-day view; the current ones (NB-012, NB-014, NB-016) run "
                    f"7-day click only. Legacy reports {L['roas']:.2f}x on "
                    f"{rupees(L['spend'])} against {C['roas']:.2f}x on {rupees(C['spend'])} for "
                    f"current. Part of that gap is view-through credit the newer setup simply "
                    f"doesn't count. They are scored as separate cohorts here for exactly this "
                    f"reason — never compare a creative's ROAS across the two.",
                    f"Legacy: {L['n']} creatives, {int(L['pur'])} orders, AOV {rupees(L['aov'])} · "
                    f"Current: {C['n']} creatives, {int(C['pur'])} orders, AOV {rupees(C['aov'])}"))

    # testing throughput
    testing = [r for r in rows if r["role"] == "Prospecting — Testing"]
    scaling = [r for r in rows if "Scaling" in r["role"]]
    if testing and scaling:
        T, S = agg(testing), agg(scaling)
        share = T["spend"] / (T["spend"] + S["spend"]) * 100
        out.append(("Testing throughput and its share of spend",
                    f"Testing carries <b>{T['n']} creatives on {rupees(T['spend'])}</b>, which is "
                    f"{share:.1f}% of prospecting spend. "
                    + (f"That is thin for a portfolio meant to feed scaling — at this rate the "
                       f"scaling campaigns are being fed by very few proven ideas."
                       if share < 12 else
                       f"That is a healthy share; the pipeline into scaling is being fed.")
                    + f" Testing reaches cart at {T['lpv2atc']:.1f}% against {S['lpv2atc']:.1f}% "
                      f"in scaling, which is the gap to watch: if testing converts far worse, the "
                      f"selection criteria for promotion are doing real work.",
                    f"Testing: {T['n']} creatives, {rupees(T['spend'])}, {int(T['pur'])} orders · "
                    f"Scaling: {S['n']} creatives, {rupees(S['spend'])}, {int(S['pur'])} orders"))

    # concentration risk
    top = sorted(rows, key=lambda r: -r["spend"])
    if len(top) >= 10:
        t5 = sum(r["spend"] for r in top[:5]) / a["spend"] * 100
        out.append(("Spend concentration",
                    f"The top 5 creatives absorb <b>{t5:.0f}%</b> of all spend this window. "
                    + ("That is heavy concentration — performance is resting on very few "
                       "assets, and one of them fatiguing moves the whole account."
                       if t5 > 45 else
                       "That is a reasonably distributed book; no single creative is load-bearing.")
                    + f" The largest single spender is <i>{top[0]['theme']}</i> at "
                      f"{rupees(top[0]['spend'])}.",
                    " · ".join(f"{r['theme'][:28]}: {rupees(r['spend'])}" for r in top[:5])))

    # catalogue competitiveness
    beat = tot = 0
    for ck, m in cohorts.items():
        cats = m.get("catalogue") or []
        if not cats: continue
        best = max(x["roas"] for x in cats)
        members = [r for r in rows if r["cohort"] == ck]
        beat += sum(1 for r in members if r["roas"] > best); tot += len(members)
    if tot:
        pct = beat / tot * 100
        out.append(("Are we beating the catalogue?",
                    f"<b>{beat} of {tot}</b> hand-made creatives ({pct:.0f}%) beat the dynamic "
                    f"catalogue ad running alongside them. "
                    + ("That is low. Catalogue costs nothing to produce and needs no brief, so "
                       "every creative below it is effort better spent elsewhere."
                       if pct < 40 else
                       "The creative work is earning its place against the free alternative."),
                    f"Measured across {len(cohorts)} cohorts where a catalogue ad runs"))

    # zero-sales anomalies
    zero = [m for m in cohorts.values() if m["zero_sales"]]
    if zero:
        out.append(("Groups with no sales this window",
                    f"<b>{len(zero)} cohort{'s' if len(zero)>1 else ''}</b> recorded no orders at "
                    f"all: " + ", ".join(f"{m['cat']} {m['role']}" for m in zero) +
                    ". ROAS and purchase scores are zero for every creative in them, so Overall "
                    "reflects reach and cart behaviour only. Usually this means the campaign is "
                    "new or barely funded rather than that the creative failed — check spend "
                    "and days live before drawing any conclusion.",
                    " · ".join(f"{m['cat']} {m['role']}: {rupees(m['spend'])}, {m['n']} creatives"
                               for m in zero)))

    # nomenclature coverage
    tagged = sum(1 for r in rows if r.get("tagged"))
    out.append(("Creative tagging coverage",
                f"<b>{tagged} of {len(rows)}</b> creatives are matched to the Ad Nomenclature "
                f"sheet. " + ("Until that file is joined, the angle, silhouette and VO/AI "
                              "filters and every insight built on them stay empty — those are "
                              "the fields that explain *why* something worked rather than just "
                              "that it did."
                              if tagged == 0 else
                              "Untagged creatives still score normally; they just sit outside "
                              "the angle and silhouette analysis."),
                f"{len(rows)-tagged} creatives carry no nomenclature attributes"))
    return out
