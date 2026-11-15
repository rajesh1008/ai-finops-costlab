"""Chapter 40: the numbers behind a board pack line. Unit costs come from REAL usage fields (scripts/boardpack_lab.py); volumes, human handling cost, rework cost, platform cost and revenue per outcome are ASSUMED, labelled in the chapter.
Prices come from the dated placeholder table in prices.py."""
import random, re
from costlab.prices import PLACEHOLDER_USD_PER_MTIOK as P

DECLINE = re.compile(r"cannot answer|can't answer|can not answer|do not contain|does not contain|not contain|unable to|not enough information|not provided|not specified", re.I)

def classify(text, ok):
    """correct, decline or wrong. A scored-correct reply is correct even if it hedges."""
    if ok: return "correct"
    return "decline" if DECLINE.search(text or "") else "wrong"

def call_usd(model, tin, tout):
    r = P["anthropic:" + model]
    return (tin * r["input"] + tout * r["output"]) / 1e6

def list_price_per_mtok(model, out_share=0.25):
    """Blended list price per million tokens at an assumed output share (the 'price per token' a dashboard shows)."""
    r = P["anthropic:" + model]
    return (1 - out_share) * r["input"] + out_share * r["output"]

def loaded_cost(classes, inference, human=6.0, rework=4.0, platform=0.004):
    """Per-ticket loaded cost for a set of tickets, all of which end closed. A decline goes to a person (human). A wrong confident answer is reopened: a person handles it AND rework is paid.
    Platform cost (retrieval, orchestration, monitoring) is a per-call amount. Returns total dollars and a breakdown."""
    n = len(classes); d = sum(c == "decline" for c in classes); w = sum(c == "wrong" for c in classes)
    inf = sum(inference); plat = platform * n; hum = human * (d + w); rew = rework * w
    return {"n": n, "inference": inf, "platform": plat, "human": hum, "rework": rew, "total": inf + plat + hum + rew,
            "declines": d, "wrongs": w, "correct": n - d - w}

def cost_per_outcome(b): return b["total"] / b["n"]

def cost_per_correct_only(b):
    """Inference spend divided by correct answers only: the narrow metric that ignores what failures cost downstream."""
    return b["inference"] / b["correct"] if b["correct"] else float("inf")

def bootstrap_ci(values_fn, n, reps=2000, seed=7, lo=0.025, hi=0.975):
    rnd = random.Random(seed); xs = []
    for _ in range(reps):
        idx = [rnd.randrange(n) for _ in range(n)]
        xs.append(values_fn(idx))
    xs.sort(); return xs[int(lo * reps)], xs[int(hi * reps) - 1]

def margin(revenue_per_outcome, cost_per_outcome_):
    return (revenue_per_outcome - cost_per_outcome_) / revenue_per_outcome

def decision(margin_now, margin_prev, target=0.60, floor=0.30, measured=True):
    """Scale, fix or retire for one board line. Projected (unmeasured) lines are never scaled."""
    if not measured: return "fix"
    if margin_now >= target and margin_now >= margin_prev - 0.02: return "scale"
    if margin_now < floor and margin_prev < floor: return "retire"
    return "fix"
