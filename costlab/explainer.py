"""Chapter 38: scenarios for an agent that explains a week-over-week change. SYNTHETIC; the true driver is known by construction."""
import random
from costlab.review import BASE, CALL_SCALE, unit_cost, PRODUCTS

DRIVERS = ["volume", "price", "cache", "tokens_per_call", "mix", "untagged"]
CHANGE = {"volume": ("calls", 2.2), "price": ("price_scale", 1.3), "cache": ("cache_hit", None), "tokens_per_call": ("tok_in", 1.8), "mix": ("big_share", None), "untagged": ("untagged", 0.5)}


def row(p, st, rnd):
    r = dict(st); r["calls_obs"] = st["calls"] * rnd.gauss(1.0, 0.03)
    r["cpc"] = unit_cost(st["tok_in"], st["tok_out"], st["big_share"], st["cache_hit"], st["price_scale"]); r["spend"] = r["calls_obs"] * r["cpc"]
    return r


def scenario(p, driver, seed):
    rnd = random.Random(seed)
    c, t, o, b, h = BASE[p]
    st = {"calls": c * CALL_SCALE, "tok_in": t, "tok_out": o, "big_share": max(b, 0.05), "cache_hit": max(h, 0.3), "price_scale": 1.0, "untagged": 0.03}
    a = row(p, st, rnd); st2 = dict(st); f, v = CHANGE[driver]
    if driver == "cache": st2["cache_hit"] = 0.05
    elif driver == "mix": st2["big_share"] = min(1.0, st["big_share"] + 0.35)
    else: st2[f] = st[f] * v if f != "untagged" else v
    return a, row(p, st2, rnd)


def table(p, a, b, detail):
    if not detail:
        return (f"Product: {p}\nweek | spend_usd | calls\nprev | {a['spend']:.0f} | {a['calls_obs']:.0f}\nthis | {b['spend']:.0f} | {b['calls_obs']:.0f}")
    cols = ["spend_usd", "calls", "input_tokens_per_call", "output_tokens_per_call", "dear_model_share", "cache_read_share_of_input", "price_index", "untagged_share"]
    f = lambda r: f"{r['spend']:.0f} | {r['calls_obs']:.0f} | {r['tok_in']:.0f} | {r['tok_out']:.0f} | {r['big_share']:.2f} | {r['cache_hit']:.2f} | {r['price_scale']:.2f} | {r['untagged']:.2f}"
    return f"Product: {p}\nweek | " + " | ".join(cols) + f"\nprev | {f(a)}\nthis | {f(b)}"
