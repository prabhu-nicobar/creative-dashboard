"""Derives the 'Insights For The Brand Team' block from the scored cohort data."""
import statistics
from collections import defaultdict
from engine import med

def rupees(v): return "₹" + format(int(round(v)), ",")

def agg(rows):
    s = sum(r["spend"] for r in rows); rev = sum(r["rev"] for r in rows)
    pur = sum(r["pur"] for r in rows); atc = sum(r["atc"] for r in rows)
    lpv = sum(r["lpv"] for r in rows); oc = sum(r["oc"] for r in rows)
    return dict(n=len(rows), spend=s, rev=rev, pur=pur, atc=atc, lpv=lpv, oc=oc,
                aov=(rev / pur) if pur else 0, roas=(rev / s) if s else 0,
                lpv2atc=(atc / lpv * 100) if lpv else 0,
                clk2lpv=(lpv / oc * 100) if oc else 0,
                atc2pur=(pur / atc * 100) if atc else 0)

def _fmt_pct(a, b):
    if not b: return ""
    return f"{(a-b)/b*100:+.0f}%"

def build_insights(scored, cohorts):
    rows = [r for r in scored.values()]
    out = []

    # ---------------------------------------------------------- 1. AOV
    by_cat = defaultdict(list)
    for r in rows: by_cat[r["category"]].append(r)
    aovs = [(c, agg(v)) for c, v in by_cat.items() if agg(v)["pur"] >= 10]
    aovs.sort(key=lambda x: -x[1]["aov"])
    if len(aovs) >= 2:
        hi, lo = aovs[0], aovs[-1]
        overall = agg(rows)
        body = (f"Average order value runs from <b>{rupees(lo[1]['aov'])}</b> in {lo[0]} to "
                f"<b>{rupees(hi[1]['aov'])}</b> in {hi[0]}, against {rupees(overall['aov'])} "
                f"across everything. Every {hi[0]} order is worth "
                f"{hi[1]['aov']/lo[1]['aov']:.1f}× a {lo[0]} one, so the same conversion lift is "
                f"worth {hi[1]['aov']/lo[1]['aov']:.1f}× more there. When you are choosing where "
                f"to spend creative effort, a small improvement in {hi[0]} beats a larger one in "
                f"{lo[0]} — and a {lo[0]} creative has to work considerably harder to justify the "
                f"same shoot.")
        detail = " · ".join(f"{c}: {rupees(a['aov'])} on {int(a['pur'])} orders" for c, a in aovs)
        out.append(("What an order is worth, by category", body, detail))

    # ---------------------------------------------------------- 2. PDP vs PLP
    pdp = [r for r in rows if r["dest"] == "PDP"]
    plp = [r for r in rows if r["dest"] == "PLP"]
    if len(pdp) >= 5 and len(plp) >= 5:
        a, b = agg(pdp), agg(plp)
        better = "PDP" if a["lpv2atc"] > b["lpv2atc"] else "PLP"
        worse = "PLP" if better == "PDP" else "PDP"
        bb, ww = (a, b) if better == "PDP" else (b, a)
        aov_note = ""
        if bb["aov"] and ww["aov"]:
            richer = "PDP" if a["aov"] > b["aov"] else "PLP"
            poorer = "PLP" if richer == "PDP" else "PDP"
            aov_note = (f" But the baskets differ: a {richer} order is worth "
                        f"{rupees(max(a['aov'], b['aov']))} against {rupees(min(a['aov'], b['aov']))} "
                        f"from a {poorer} one. So {poorer} may win on cart rate while {richer} wins "
                        f"on revenue — the two destinations are not interchangeable.")
        body = (f"Creatives pointing at a single product page convert visitors to cart at "
                f"<b>{a['lpv2atc']:.1f}%</b>; those pointing at a listing page convert at "
                f"<b>{b['lpv2atc']:.1f}%</b>. {better} is ahead by "
                f"{abs(a['lpv2atc']-b['lpv2atc'])/max(ww['lpv2atc'],0.01)*100:.0f}%.{aov_note} "
                f"The practical read: when a creative shows one hero product clearly, send it to "
                f"that product. When it shows a world or a mood, a listing page gives people "
                f"somewhere to land — but expect to lose more of them on the way to cart.")
        detail = (f"PDP: {len(pdp)} creatives, {rupees(a['spend'])}, {a['lpv2atc']:.1f}% to cart, "
                  f"AOV {rupees(a['aov'])} · PLP: {len(plp)} creatives, {rupees(b['spend'])}, "
                  f"{b['lpv2atc']:.1f}% to cart, AOV {rupees(b['aov'])}")
        out.append(("Where you send people changes what they do", body, detail))

    # ---------------------------------------------------------- 3. Format behaviour
    by_fmt = defaultdict(list)
    for r in rows: by_fmt[r["fmt"]].append(r)
    fmt_rows = []
    for f, v in by_fmt.items():
        if len(v) < 4: continue
        pre = med([x["pre"] for x in v if x["pre"] is not None]) or 0
        post = med([x["post"] for x in v if x["post"] is not None]) or 0
        fmt_rows.append((f, len(v), pre, post, agg(v)))
    if len(fmt_rows) >= 3:
        fmt_rows.sort(key=lambda x: -(x[2] + x[3]) / 2)
        best = fmt_rows[0]
        attention = max(fmt_rows, key=lambda x: x[2])
        selling = max(fmt_rows, key=lambda x: x[3])
        body = (f"Across every group, <b>{attention[0]}</b> is the strongest format at earning "
                f"attention (median pre-click {attention[2]:.0f}), while <b>{selling[0]}</b> is "
                f"the strongest at converting it (median post-click {selling[3]:.0f}). ")
        if attention[0] != selling[0]:
            body += (f"Those being different formats is the single most useful thing on this "
                     f"page: it means the format that gets you noticed is not the format that "
                     f"gets you paid, and a healthy plan needs both rather than doubling down "
                     f"on whichever one looks best this week.")
        else:
            body += (f"{attention[0]} leading on both ends is unusual and worth protecting — it "
                     f"is the format to build the next batch around.")
        detail = " · ".join(f"{f}: {n} live, pre {pre:.0f} / post {post:.0f}, "
                            f"{rupees(a['spend'])}"
                            for f, n, pre, post, a in fmt_rows)
        out.append(("Which formats do which job", body, detail))

    # ---------------------------------------------------------- 4. Funnel leak
    ov = agg(rows)
    leaks = []
    if ov["clk2lpv"] < 85:
        leaks.append(f"only <b>{ov['clk2lpv']:.0f} of every 100 clicks</b> becomes a page view — "
                     f"the rest are lost between the tap and the page loading")
    if ov["lpv2atc"]:
        leaks.append(f"<b>{ov['lpv2atc']:.1f}%</b> of people who reach a page add something "
                     f"to cart")
    if ov["atc2pur"]:
        leaks.append(f"<b>{ov['atc2pur']:.1f}%</b> of carts become orders")
    if leaks:
        body = ("Across everything running: " + "; ".join(leaks) + ". "
                "The biggest single loss in that chain is not usually the creative's fault — "
                "but it tells you where a creative can and can't help. If clicks aren't reaching "
                "the page, no new image fixes it. If people reach the page and don't add to "
                "cart, the creative promised something the page didn't deliver, and that is "
                "squarely a brief problem.")
        detail = (f"{int(ov['oc']):,} outbound clicks → {int(ov['lpv']):,} page views → "
                  f"{int(ov['atc']):,} carts → {int(ov['pur']):,} orders")
        out.append(("Where people fall out of the funnel", body, detail))

    # ---------------------------------------------------------- 5. Catalogue benchmark
    beat = tot = 0; cat_roas = []
    for ck, m in cohorts.items():
        cats = m.get("catalogue") or []
        if not cats: continue
        best = max(x["roas"] for x in cats)
        cat_roas.append(best)
        members = [r for r in rows if r["cohort"] == ck]
        beat += sum(1 for r in members if r["roas"] > best); tot += len(members)
    if tot:
        pct = beat / tot * 100
        body = (f"<b>{beat} of {tot}</b> hand-made creatives ({pct:.0f}%) are currently beating "
                f"the dynamic catalogue ad running alongside them in their own group. ")
        if pct < 40:
            body += ("That is a low share, and it is the number to move. The catalogue costs "
                     "nothing to produce and needs no brief — every creative that doesn't beat "
                     "it is effort that would have been better spent elsewhere. Look at the ones "
                     "that do beat it and ask what they have in common.")
        else:
            body += ("That is a healthy share — the creative work is earning its place against "
                     "the free alternative. Protect whatever the winners are doing.")
        detail = f"Catalogue ROAS in the groups where it runs: " + \
                 " · ".join(f"{r:.2f}x" for r in sorted(cat_roas, reverse=True))
        out.append(("Are we beating the catalogue?", body, detail))

    # ---------------------------------------------------------- 6. Variant spread
    fam = defaultdict(list)
    for r in rows:
        if r["pre"] is not None: fam[(r["cohort"], r["vkey"])].append(r)
        
    spreads = [(k, v) for k, v in fam.items() if len(v) >= 2]
    if spreads:
        gaps = []
        for k, v in spreads:
            vals = [x.get("overall") or x["pre"] for x in v]
            gaps.append((max(vals) - min(vals), k, v))
        gaps.sort(reverse=True, key=lambda x: x[0])
        big = [g for g in gaps if g[0] >= 20]
        if big:
            g = big[0]
            body = (f"<b>{len(big)} of {len(spreads)}</b> concepts running more than one version "
                    f"show a gap of 20 points or more between their best and worst version. The "
                    f"widest is <i>{g[2][0]['theme']}</i>, where versions of the same idea score "
                    f"{max(x.get('overall') or x['pre'] for x in g[2]):.0f} and "
                    f"{min(x.get('overall') or x['pre'] for x in g[2]):.0f}. Same product, same "
                    f"offer, same audience — so the entire difference is execution. This is the "
                    f"clearest evidence on the page that craft decisions move numbers, and the "
                    f"cheapest place to find a win is comparing versions you already shot.")
            detail = " · ".join(f"{k[1][:40]}: spread {gap:.0f}" for gap, k, v in gaps[:5])
            out.append(("Same idea, different execution", body, detail))

    return out
