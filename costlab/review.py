"""Chapter 37: a weekly AI cost review as code. SYNTHETIC Fieldstone weekly data with planted events, three review types, and a sequential-substitution decomposition."""
import random, statistics

PRODUCTS = ["support-agent", "handbook", "extraction", "search", "reports", "sales-email", "evals"]
PRICE = {"small": (1.0, 5.0), "big": (3.0, 15.0)}  # $ per million input, output (ASSUMED, synthetic)


def unit_cost(tok_in, tok_out, big_share, cache_hit, price_scale=1.0):
    """Cost per call: input tokens billed at 0.1x when read from cache (share cache_hit of input), mix of small and big model."""
    def one(m):
        pi, po = PRICE[m]
        return price_scale * ((tok_in * (1 - cache_hit) + tok_in * cache_hit * 0.1) * pi + tok_out * po) / 1e6
    return big_share * one("big") + (1 - big_share) * one("small")


CALL_SCALE = 11  # ASSUMED: puts the weekly total near $40k, about $175k a month
BASE = {  # calls per week, tokens in, tokens out, big share, cache hit
    "support-agent": (150_000, 2400, 260, 0.20, 0.60), "handbook": (90_000, 3100, 120, 0.05, 0.70),
    "extraction": (240_000, 1500, 220, 0.10, 0.20), "search": (900_000, 600, 90, 0.00, 0.30),
    "reports": (20_000, 5200, 900, 0.40, 0.10), "sales-email": (60_000, 700, 300, 0.10, 0.0), "evals": (110_000, 1800, 150, 0.30, 0.50)}

EVENTS = {  # week -> (product, field, factor or value, label)
    3: ("search", "calls", 2.4, "tenant spike (one tenant's script)"),
    5: ("support-agent", "price_scale", 1.30, "price change on the dear model"),
    7: ("handbook", "cache_hit", 0.10, "cache hit rate falls (prompt reordered)"),
    9: ("extraction", "tok_in", 1.8, "retry loop re-sends context"),
    10: ("support-agent", "big_share", 0.55, "router sends more to the dear model"),
    12: ("reports", "untagged", 0.5, "new feature ships untagged"),
}


def build(weeks=13, seed=370):
    rnd = random.Random(seed); out = []; state = {p: dict(zip(("calls", "tok_in", "tok_out", "big_share", "cache_hit"), (BASE[p][0] * CALL_SCALE,) + BASE[p][1:])) | {"price_scale": 1.0, "untagged": 0.03} for p in PRODUCTS}
    for w in range(1, weeks + 1):
        ev = EVENTS.get(w)
        for p in PRODUCTS:
            s = state[p]
            noise = rnd.gauss(1.0, 0.04)
            if ev and ev[0] == p:
                f, v = ev[1], ev[2]
                if f in ("calls", "tok_in", "price_scale"): s[f] = s[f] * v if w == w else s[f]
                else: s[f] = v
            row = {"week": w, "product": p, **{k: s[k] for k in s}}
            row["calls_obs"] = s["calls"] * noise
            row["cpc"] = unit_cost(s["tok_in"], s["tok_out"], s["big_share"], s["cache_hit"], s["price_scale"])
            row["spend"] = row["calls_obs"] * row["cpc"]
            row["event"] = ev[3] if ev and ev[0] == p else ""
            out.append(row)
        # events persist (state carried forward), except the spike, which fades after two weeks
        if w == 4: state["search"]["calls"] = BASE["search"][0] * CALL_SCALE
    return out


def decompose(a, b):
    """Spend change between row a (earlier) and row b (later) by sequential substitution: volume, tokens per call, mix, cache, price."""
    f = lambda calls, ti, big, ch, ps: calls * unit_cost(ti, b["tok_out"], big, ch, ps)
    c0 = a["calls_obs"] * a["cpc"]
    c1 = f(b["calls_obs"], a["tok_in"], a["big_share"], a["cache_hit"], a["price_scale"])
    c2 = f(b["calls_obs"], b["tok_in"], a["big_share"], a["cache_hit"], a["price_scale"])
    c3 = f(b["calls_obs"], b["tok_in"], b["big_share"], a["cache_hit"], a["price_scale"])
    c4 = f(b["calls_obs"], b["tok_in"], b["big_share"], b["cache_hit"], a["price_scale"])
    c5 = b["spend"]
    return {"volume": c1 - c0, "tokens_per_call": c2 - c1, "mix": c3 - c2, "cache": c4 - c3, "price": c5 - c4}


def review_total(rows, week, pct=0.15):
    tot = {w: sum(r["spend"] for r in rows if r["week"] == w) for w in {r["week"] for r in rows}}
    prev = [tot[w] for w in range(max(1, week - 4), week)]
    if not prev: return []
    return [("TOTAL", (tot[week] - statistics.median(prev)) / statistics.median(prev))] if abs(tot[week] - statistics.median(prev)) > pct * statistics.median(prev) else []


def review_product(rows, week, pct=0.25):
    out = []
    for p in PRODUCTS:
        s = {r["week"]: r["spend"] for r in rows if r["product"] == p}
        prev = [s[w] for w in range(max(1, week - 4), week)]
        if prev and abs(s[week] - statistics.median(prev)) > pct * statistics.median(prev): out.append((p, (s[week] - statistics.median(prev)) / statistics.median(prev)))
    return out


def review_driver(rows, week, share=0.08, untagged_floor=0.2):
    """Per product: any single driver moving spend by more than `share` of the product's prior spend, or untagged share above floor."""
    out = []
    for p in PRODUCTS:
        a = next(r for r in rows if r["product"] == p and r["week"] == week - 1); b = next(r for r in rows if r["product"] == p and r["week"] == week)
        d = decompose(a, b)
        for k, v in d.items():
            if k == "volume": thr = 0.30
            else: thr = share
            if abs(v) > thr * a["spend"]: out.append((p, k, v))
        if b["untagged"] > untagged_floor: out.append((p, "untagged", b["untagged"]))
    return out
