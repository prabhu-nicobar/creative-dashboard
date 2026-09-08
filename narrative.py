"""v2 Analysis text and Creative Feedback — written for a brand manager."""
import datetime
from engine import med, band, SMALL_SAMPLE_PURCHASES

FB_MIN_DAYS, FB_MIN_IMPS, FB_MIN_SPEND = 5, 10000, 5000

def rupees(v): return "₹" + format(int(round(v or 0)), ",")

def days_live(row, today):
    try:
        y, m, d = [int(x) for x in row["created"].split("-")]
        return (today - datetime.date(y, m, d)).days
    except Exception:
        return 0

# ------------------------------------------------------------------ analysis
def analysis(s, cohort, prior_label, decline, other_windows):
    pre, post, ov = s["pre"], s["post"], s["overall"]
    pm, qm = cohort["pre_med"], cohort["post_med"]
    out = []
    HI, LO = 58, 42

    # 1 — the headline
    if cohort["zero_sales"]:
        out.append("Nothing in this whole group sold during this window, so return and orders "
                   "score zero for every creative here, this one included. What you can still "
                   "read is whether it earned attention and got people to the cart.")
    elif s["pur"] == 0:
        out.append("This brought people in but sold nothing in this window, so it scores zero "
                   "on return and on orders — together most of the sales half. It still earns "
                   "credit for getting people as far as the cart, and for how efficiently it "
                   "reached them in the first place.")
    elif pre >= HI and post >= HI:
        out.append("This works the whole way through — it earns the click and it sells.")
    elif pre >= HI and post <= LO:
        out.append("People stop and click on this, but very few of them buy. The image is "
                   "doing its job; what happens after the click isn't.")
    elif pre <= LO and post >= HI:
        out.append("Not many people click this, but the ones who do buy. The idea is landing "
                   "with the right person — it just isn't being noticed widely.")
    elif pre <= LO and post <= LO:
        out.append("This isn't landing at either end — it isn't drawing people in, and the "
                   "few who arrive don't buy.")
    elif post - pre >= 15:
        out.append("Quiet on the way in, strong on the way out. It doesn't stand out more "
                   "than the rest, yet the people it brings in buy at a better rate. That is "
                   "the profitable kind of average.")
    elif pre - post >= 15:
        out.append("This gets noticed more than it sells. It pulls people in ahead of the "
                   "group, then loses them before the order.")
    else:
        out.append("This sits around the middle of its group at both ends — no clear "
                   "strength, no clear problem.")

    # 2 — small sample warning, before any driver detail
    if s["small_sample"]:
        out.append(f"Treat the sales score carefully: it rests on {int(s['pur'])} "
                   f"order{'s' if s['pur'] != 1 else ''}. One more or one fewer would move it "
                   f"substantially.")

    # 3 — the specific driver
    drivers = []
    if pm.get("octr") and s["octr"]:
        d = (s["octr"] - pm["octr"]) / pm["octr"] * 100
        if abs(d) > 20:
            drivers.append(f"{'more' if d>0 else 'fewer'} people click it than the rest of "
                           f"the group ({abs(d):.0f}% {'above' if d>0 else 'below'})")
    if pm.get("cpm") and s["cpm"]:
        d = (s["cpm"] - pm["cpm"]) / pm["cpm"] * 100
        if abs(d) > 25:
            drivers.append(f"it costs {abs(d):.0f}% {'more' if d>0 else 'less'} to put in "
                           f"front of people than the group average")
    if s["clk2lpv"] and s["clk2lpv"] < 70:
        drivers.append(f"only {s['clk2lpv']:.0f} of every 100 clicks reaches the page, so a "
                       f"lot of interest leaks before anyone sees the product")
    if qm.get("lpv2atc") and s["lpv2atc"]:
        v, m = s["lpv2atc"], qm["lpv2atc"]
        d = (v - m) / m * 100
        if abs(d) > 30:
            drivers.append(f"{'more' if d>0 else 'fewer'} visitors add to cart than usual "
                           f"({v:.1f}% against {m:.1f}%)")
    if drivers:
        out.append("Specifically, " + "; ".join(drivers[:2]) + ".")

    # 4 — decline against its own prior period (this is where fatigue lives)
    if decline:
        bits = []
        if decline["pre_down"]:
            p = []
            if decline["ctr"] is not None and decline["ctr"] <= -15:
                p.append(f"{abs(decline['ctr']):.0f}% fewer people are clicking it")
            if decline["cpm"] is not None and decline["cpm"] <= -15:
                p.append(f"it costs {abs(decline['cpm']):.0f}% more to serve")
            bits.append("Against " + prior_label + ", " + " and ".join(p) +
                        ". That is the creative wearing out with the audience it is reaching, "
                        "and no change after the click will fix it.")
        if decline["post_down"]:
            p = []
            if decline["cart"] is not None and decline["cart"] <= -15:
                p.append(f"the share of visitors adding to cart is down {abs(decline['cart']):.0f}%")
            if decline["roas"] is not None and decline["roas"] <= -15:
                p.append(f"return on spend is down {abs(decline['roas']):.0f}%")
            lead = "" if decline["pre_down"] else "Against " + prior_label + ", "
            bits.append(lead + ("Meanwhile " if decline["pre_down"] else "") + " and ".join(p) +
                        (". Attention is holding up, so the change is happening after the "
                         "click rather than in the image." if not decline["pre_down"] else "."))
        out.extend(bits)

    # 5 — cross-window contrast
    for label, alt in other_windows:
        a = alt.get(s["id"])
        if not a: continue
        if abs(s["overall"] - a["overall"]) >= 8:
            direction = "better" if s["overall"] > a["overall"] else "worse"
            out.append(f"It also looks {direction} here than over {label.lower()} "
                       f"({s['overall']:.0f} against {a['overall']:.0f}) — read the two "
                       f"together before calling it a winner or a write-off.")
            break

    # 6 — what to brief next
    if cohort["zero_sales"] or s["pur"] == 0:
        pass
    elif pre >= HI and post <= LO:
        out.append("Next brief: keep this framing, point it somewhere that closes — a clearer "
                   "product page, or a tighter single-product shot.")
    elif pre <= LO and post >= HI:
        out.append("Next brief: keep the product and the story, rework the opening frame so "
                   "more people notice it.")
    elif pre >= HI and post >= HI:
        out.append("Next brief: make more like this — same treatment, different products.")
    elif pre <= LO and post <= LO:
        out.append("Next brief: don't iterate on this one. The concept isn't the problem to "
                   "solve here.")
    return " ".join(out)

# ------------------------------------------------------------------ feedback
def feedback(s, cohort, all_rows, today):
    d = days_live(s, today)
    if d < FB_MIN_DAYS or s["imps"] < FB_MIN_IMPS or s["spend"] < FB_MIN_SPEND:
        return None, (f"Not enough history to diagnose yet — {d} days live, "
                      f"{int(s['imps']):,} impressions, {rupees(s['spend'])} spent. "
                      f"Needs 5 days, 10,000 impressions and ₹5,000.")
    peers = [x for x in all_rows.values() if x["cohort"] == s["cohort"] and x["id"] != s["id"]]
    same_fmt = [x for x in peers if x["fmt"] == s["fmt"]]
    siblings = [x for x in peers if x["vkey"] == s["vkey"]]
    same_dest = [x for x in peers if x["dest"] and x["dest"] == s["dest"]]
    lines = []

    if same_fmt:
        fm = med([x["overall"] for x in same_fmt])
        if fm:
            lines.append(f"Against the other {len(same_fmt)+1} {s['fmt']} creatives in "
                         f"{s['category']} {s['role'].split('—')[0].strip().lower()}, this sits "
                         f"{'ahead of' if s['overall'] > fm else 'behind'} the middle "
                         f"({s['overall']:.0f} against {fm:.0f}).")
    else:
        lines.append(f"This is the only {s['fmt']} running in its group, so there is no "
                     f"like-for-like to compare it against.")

    if siblings:
        best = max(siblings, key=lambda x: x["overall"])
        if abs(best["overall"] - s["overall"]) >= 5:
            lines.append(f"It {'outperforms' if s['overall'] > best['overall'] else 'is beaten by'} "
                         f"its own sibling version ({s['overall']:.0f} against "
                         f"{best['overall']:.0f}) — same concept, different execution, so the "
                         f"gap is treatment rather than product.")

    if s["dest"] and same_dest:
        dm = med([x["lpv2atc"] for x in same_dest])
        if dm and s["lpv2atc"]:
            if s["lpv2atc"] < dm * 0.7:
                lines.append(f"It sends people to a {s['dest']} like its peers but converts "
                             f"visitors to cart at {s['lpv2atc']:.1f}% against {dm:.1f}% for the "
                             f"others — the destination isn't the difference, the promise the "
                             f"creative makes probably is.")
            elif s["lpv2atc"] > dm * 1.4:
                lines.append(f"Its {s['dest']} converts unusually well at {s['lpv2atc']:.1f}% "
                             f"against {dm:.1f}% — whatever this creative promises, the page "
                             f"delivers on it.")

    if s.get("angle"):
        peers_angle = [x for x in peers if x.get("angle") == s["angle"]]
        if peers_angle:
            am = med([x["overall"] for x in peers_angle])
            if am:
                lines.append(f"As a {s['angle']}-angle creative it sits "
                             f"{'above' if s['overall'] > am else 'below'} the {am:.0f} median "
                             f"for that angle in this group.")

    pm = cohort["pre_med"]
    if pm.get("cpm") and s["cpm"] and pm.get("octr") and s["octr"]:
        cheap  = s["cpm"] < pm["cpm"] * 0.8
        dear   = s["cpm"] > pm["cpm"] * 1.2
        sticky = s["octr"] > pm["octr"] * 1.2
        dull   = s["octr"] < pm["octr"] * 0.8
        if cheap and sticky:
            lines.append("Meta is serving it cheaply and people are clicking — that combination "
                         "usually means the frame reads clearly at thumbnail size.")
        elif dear and dull:
            lines.append("It is expensive to serve and under-clicked, which normally points at a "
                         "busy or low-contrast frame that doesn't survive being seen small.")
        elif cheap and dull:
            lines.append("Cheap to serve but under-clicked — plenty of people are seeing it and "
                         "scrolling past, so the issue is the hook, not the reach.")

    if d >= 30:
        lines.append(f"Live {d} days, long enough that the brand is clearly backing it — treat "
                     f"the read as settled rather than early.")
    elif d < 14:
        lines.append(f"Only {d} days live, so read this as a first indication rather than a "
                     f"verdict.")

    text = " ".join(lines[:4])
    if s["pur"] < SMALL_SAMPLE_PURCHASES:
        text += (f" (Sales commentary is held back — only {int(s['pur'])} "
                 f"order{'s' if s['pur'] != 1 else ''} so far.)")
    return text, None
