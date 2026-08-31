"""Plain-language Analysis view + creative Feedback for the brand team."""
import statistics
from engine import med, band

FEEDBACK_MIN_DAYS  = 5
FEEDBACK_MIN_IMPS  = 10000
FEEDBACK_MIN_SPEND = 5000
FEEDBACK_MIN_ATC   = 15     # extra gate for post-click commentary

def rupees(v):
    return "₹" + format(int(round(v)), ",")

def days_live(row, today):
    try:
        y, m, d = [int(x) for x in row["created"].split("-")]
        return (today - __import__("datetime").date(y, m, d)).days
    except Exception:
        return 0

def _cmp(v, m, unit="", better_low=False):
    if not m: return ""
    pct = (v - m) / m * 100
    word = "below" if pct < 0 else "above"
    good = (pct < 0) if better_low else (pct > 0)
    return f"{abs(pct):.0f}% {word} the cohort{unit}", good

# ------------------------------------------------------------------ analysis
def analysis(s, cohort, other_windows):
    """3–4 sentences, written for a brand manager. No jargon left unexplained."""
    pre, post = s.get("pre"), s.get("post")
    pm, qm = cohort["pre_med"], cohort["post_med"]
    out = []

    # 1. the headline — what kind of creative is this
    if pre is None:
        out.append("There isn't enough delivery yet to say how this one is doing.")
    elif post is None:
        out.append(f"This creative is pulling attention {band(pre).lower()} for its group, "
                   f"but the cohort hasn't produced enough carts or orders yet to judge "
                   f"whether that attention turns into sales.")
    else:
        HI, LO = 58, 42
        gap = post - pre
        if pre >= HI and post >= HI:
            out.append("This one works the whole way through — it earns the click and it sells.")
        elif pre >= HI and post <= LO:
            out.append("People stop and click on this, but very few of them buy. "
                       "The image is doing its job; what happens after the click isn't.")
        elif pre <= LO and post >= HI:
            out.append("Not many people click this, but the ones who do buy. "
                       "The idea is landing with the right person — it just isn't being "
                       "noticed widely.")
        elif pre <= LO and post <= LO:
            out.append("This isn't landing at either end — it isn't drawing people in, "
                       "and the few who arrive don't buy.")
        elif gap >= 15:
            out.append("This one is quiet on the way in but strong on the way out — it doesn't "
                       "stand out more than the rest, yet the people it does bring in buy at a "
                       "noticeably better rate. That is the profitable kind of average.")
        elif gap <= -15 and pre >= 50:
            out.append("This gets noticed more than it sells. It pulls people in ahead of the "
                       "group, then loses them before the order.")
        elif gap <= -15:
            out.append("This is behind its group at both ends, but the drop is much sharper "
                       "after the click than before it — people are reaching the page and "
                       "then leaving.")
        else:
            out.append("This sits around the middle of its group on both attention and sales — "
                       "no clear strength, no clear problem.")

    # 2. the specific driver
    drivers = []
    if pm.get("octr") and s["octr"]:
        d = (s["octr"] - pm["octr"]) / pm["octr"] * 100
        if abs(d) > 20:
            drivers.append(f"{'more' if d>0 else 'fewer'} people click it than the rest "
                           f"of the group ({abs(d):.0f}% {'above' if d>0 else 'below'})")
    if pm.get("cpm") and s["cpm"]:
        d = (s["cpm"] - pm["cpm"]) / pm["cpm"] * 100
        if abs(d) > 25:
            drivers.append(f"it costs {abs(d):.0f}% {'more' if d>0 else 'less'} to put "
                           f"in front of people than the group average")
    if pm.get("clk2lpv") and s["clk2lpv"] and s["clk2lpv"] < 70:
        drivers.append(f"only {s['clk2lpv']:.0f} of every 100 clicks actually reach the page — "
                       f"a lot of interest is leaking before anyone sees the product")
    if qm.get("lpv2atc") and s.get("post_row") and s["post_row"]["lpv2atc"]:
        v, m = s["post_row"]["lpv2atc"], qm["lpv2atc"]
        d = (v - m) / m * 100
        if abs(d) > 30:
            drivers.append(f"{'more' if d>0 else 'fewer'} visitors add to cart than usual "
                           f"({v:.1f}% against {m:.1f}%)")
    if drivers:
        out.append("Specifically, " + "; ".join(drivers[:2]) + ".")

    # 3. cross-window contrast — the point of the toggle
    for label, alt in other_windows:
        a = alt.get(s["id"])
        if not a: continue
        av = a.get("overall") or a.get("pre")
        cv = s.get("overall") or s.get("pre")
        if av and cv and abs(cv - av) >= 8:
            direction = "better" if cv > av else "worse"
            out.append(f"Worth noting it looks {direction} here than over {label} "
                       f"({cv:.0f} against {av:.0f}) — read the two together before "
                       f"deciding it's a winner or a write-off.")
            break

    # 4. what to do about it
    if pre is not None and post is not None:
        if pre >= 55 and post < 45:
            out.append("Next brief: keep this framing, but point it somewhere that "
                       "closes — a clearer product page, or a tighter single-product shot.")
        elif pre < 45 and post >= 55:
            out.append("Next brief: keep the product and the story, rework the opening "
                       "frame so more people notice it.")
        elif pre >= 55 and post >= 55:
            out.append("Next brief: make more like this — same treatment, different products.")
        elif pre < 45 and post < 45:
            out.append("Next brief: don't iterate on this one. The concept isn't the problem "
                       "to solve here.")
    return " ".join(out)

# ------------------------------------------------------------------ feedback
def feedback(s, cohort, all_rows, today):
    """Creative diagnosis referencing peers and siblings. Gated by the eligibility floor."""
    d = days_live(s, today)
    if d < FEEDBACK_MIN_DAYS or s["imps"] < FEEDBACK_MIN_IMPS or s["spend"] < FEEDBACK_MIN_SPEND:
        return None, f"Not enough history to diagnose yet — {d} days live, " \
                     f"{int(s['imps']):,} impressions, {rupees(s['spend'])} spent. " \
                     f"Needs {FEEDBACK_MIN_DAYS} days, 10,000 impressions and ₹5,000."

    peers = [x for x in all_rows.values() if x["cohort"] == s["cohort"] and x["id"] != s["id"]]
    same_fmt = [x for x in peers if x["fmt"] == s["fmt"]]
    siblings = [x for x in peers if x["vkey"] == s["vkey"]]
    same_dest = [x for x in peers if x["dest"] and x["dest"] == s["dest"]]
    lines = []

    # format standing
    if same_fmt:
        fmt_med = med([x.get("overall") or x.get("pre") or 0 for x in same_fmt])
        mine = s.get("overall") or s.get("pre") or 0
        if fmt_med:
            verb = "ahead of" if mine > fmt_med else "behind"
            lines.append(f"Against the other {len(same_fmt)+1} {s['fmt']} creatives in "
                         f"{s['category']} {s['role'].split('—')[0].strip().lower()}, this sits "
                         f"{verb} the middle ({mine:.0f} against {fmt_med:.0f}).")
    else:
        lines.append(f"This is the only {s['fmt']} running in its group right now, "
                     f"so there is no like-for-like to compare it against.")

    # variant / sibling comparison — the most brief-shaped signal there is
    if siblings:
        best = max(siblings, key=lambda x: x.get("overall") or x.get("pre") or 0)
        bv = best.get("overall") or best.get("pre") or 0
        mine = s.get("overall") or s.get("pre") or 0
        if abs(bv - mine) >= 5:
            better = "outperforms" if mine > bv else "is beaten by"
            lines.append(f"It {better} its own variant {best['name'].split('-')[-2:][0]} "
                         f"({mine:.0f} against {bv:.0f}) — same concept, different execution, "
                         f"so the gap is the treatment rather than the product.")

    # destination signal
    if s["dest"] and same_dest:
        dm = med([x["lpv2atc"] for x in same_dest])
        if dm and s["lpv2atc"]:
            if s["lpv2atc"] < dm * 0.7:
                lines.append(f"It sends people to a {s['dest']} like its peers, but converts "
                             f"visitors to cart at {s['lpv2atc']:.1f}% against {dm:.1f}% for the "
                             f"others — the destination isn't the difference, the promise the "
                             f"creative makes probably is.")
            elif s["lpv2atc"] > dm * 1.4:
                lines.append(f"Its {s['dest']} converts unusually well at {s['lpv2atc']:.1f}% "
                             f"against {dm:.1f}% — whatever this creative promises, the page "
                             f"delivers on it.")

    # attention vs cost read — the closest we get to a craft observation from numbers alone
    pm = cohort["pre_med"]
    if pm.get("cpm") and s["cpm"] and pm.get("octr") and s["octr"]:
        cheap  = s["cpm"]  < pm["cpm"]  * 0.8
        dear   = s["cpm"]  > pm["cpm"]  * 1.2
        sticky = s["octr"] > pm["octr"] * 1.2
        dull   = s["octr"] < pm["octr"] * 0.8
        if cheap and sticky:
            lines.append("Meta is serving it cheaply and people are clicking — that combination "
                         "usually means the frame reads clearly at thumbnail size.")
        elif dear and dull:
            lines.append("It is expensive to serve and under-clicked, which normally points at a "
                         "busy or low-contrast frame that doesn't survive being seen small.")
        elif cheap and dull:
            lines.append("It is cheap to serve but under-clicked — plenty of people are seeing it "
                         "and scrolling past, so the issue is the hook, not the reach.")

    if d >= 30:
        lines.append(f"It has been live {d} days, which is long enough that the brand is clearly "
                     f"backing it; treat the read as settled rather than early.")
    elif d < 14:
        lines.append(f"Only {d} days live — early, so read this as a first indication rather than "
                     f"a verdict.")

    text = " ".join(lines[:4])
    if s["atc"] < FEEDBACK_MIN_ATC:
        text += (f" (Cart and order commentary is held back here — only {int(s['atc'])} "
                 f"add-to-carts so far, below the 15 needed to say anything reliable.)")
    return text, None
