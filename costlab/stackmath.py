"""Chapter 43: arithmetic for stacking levers. Savings measured per arm against a baseline; the naive sum of single-lever savings versus the measured combined saving."""
def arm_cost(rows, price):
    """rows: dicts with in, out, cr, cw. price: dict input, output, cache_read, cache_write per million tokens. Returns total USD."""
    return sum(r["in"] * price["input"] + r["out"] * price["output"] + r["cr"] * price["cache_read"] + r["cw"] * price["cache_write"] for r in rows) / 1e6

def per_1000(total, n): return 1000.0 * total / n if n else 0.0

def saving(base, new): return 1.0 - new / base if base else 0.0

def naive_stack(savings):
    """Naive: apply each single-lever saving in turn as if independent: 1 - prod(1 - s)."""
    p = 1.0
    for s in savings: p *= (1.0 - s)
    return 1.0 - p

def additive_stack(savings): return sum(savings)

def reprice(cost_per_outcome, target_margin): 
    """Price that yields target gross margin on a cost per outcome."""
    if not 0 <= target_margin < 1: raise ValueError("margin must be in [0, 1)")
    return cost_per_outcome / (1.0 - target_margin)

def plan_revenue(seats, base, included, overage_price, light_share, light_mean, heavy_mean):
    """COMPOSED plan: `seats` pay `base`, `included` outcomes per seat, `overage_price` per extra outcome. Light seats average `light_mean` outcomes, heavy seats `heavy_mean`.
    Returns revenue, outcomes, overage outcomes."""
    light = round(seats * light_share); heavy = seats - light
    out = light * light_mean + heavy * heavy_mean
    over = light * max(light_mean - included, 0) + heavy * max(heavy_mean - included, 0)
    return {"revenue": seats * base + over * overage_price, "outcomes": out, "overage_outcomes": over}

def gross_margin(revenue, cost): return (revenue - cost) / revenue if revenue else 0.0
