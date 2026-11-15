"""Arithmetic behind the forty-fifth run's Ch1 and Ch3 sections. Every input is invented and labelled so in the book."""
import math, random

def split_range(month, mixed, out_share_lo, out_share_hi, out_known, in_known):
    """The mixed line's output-dollar share is unknown. Return output share of month at the two ends."""
    f = lambda s: (out_known + s * mixed) / month
    return f(out_share_lo), f(out_share_hi), (in_known + (1 - out_share_hi) * mixed) / month, (in_known + (1 - out_share_lo) * mixed) / month

def compounding(start, g, months):
    """Bill in month `months` after the first, and sum of the next `months` bills, at monthly growth g."""
    last = start * (1 + g) ** months
    total = sum(start * (1 + g) ** k for k in range(1, months + 1))
    return last, total

def sample_size(p, e, z=1.96, pop=None):
    n = z * z * p * (1 - p) / (e * e)
    if pop: n = n / (1 + (n - 1) / pop)
    return math.ceil(n)

def queue_population(seed=45, n=400, mu=5.5, sigma=1.5, scale_total=108000.0):
    """Invented unowned queue: n lines with lognormal dollars, scaled to sum to scale_total."""
    r = random.Random(seed); raw = [math.exp(mu + sigma * r.gauss(0, 1)) for _ in range(n)]
    s = sum(raw); return sorted((x * scale_total / s for x in raw), reverse=True)

def top_k_share(lines, k): return sum(lines[:k]) / sum(lines)

def sample_estimate(lines, k, trials=2000, seed=7):
    """Estimate total dollars by scaling the sum of a uniform random sample of k lines; return mean, min, max of the estimates' relative error."""
    r = random.Random(seed); tot = sum(lines); errs = []
    for _ in range(trials):
        smp = r.sample(lines, k); est = sum(smp) * len(lines) / k; errs.append(est / tot - 1)
    errs.sort(); return sum(errs) / trials, errs[int(trials * 0.05)], errs[int(trials * 0.95)]

def price_rise(price, rise, segs):
    """segs: list of (customers, cost_to_serve, churn_if_rise). Returns profit before, after, customers before, after."""
    before = sum(n * (price - c) for n, c, _ in segs)
    after = sum(n * (1 - ch) * (price * (1 + rise) - c) for n, c, ch in segs)
    return before, after, sum(n for n, _, _ in segs), sum(n * (1 - ch) for n, _, ch in segs)

def breakeven_loss(price, rise, cost):
    """Share of customers that can leave after a price rise before profit falls, when all cost the same to serve."""
    return 1 - (price - cost) / (price * (1 + rise) - cost)

def series_count(cards):
    """Upper bound on distinct label combinations: product of the cardinalities."""
    n = 1
    for c in cards: n *= c
    return n

def occupied_series(tenants, products_per_tenant, features_per_product, models_per_feature, envs):
    """Combinations that actually occur when each tenant touches only some of the product space (invented averages)."""
    return tenants * products_per_tenant * features_per_product * models_per_feature * envs

def monthly_series_cost(series, per_1000=2.0):
    return series / 1000 * per_1000

if __name__ == "__main__":
    print("== Ch1 split range", [round(x, 4) for x in split_range(180000, 43400, 0.2, 0.6, 30750, 33600)])
    print("== Ch1 compounding 20%", [round(x) for x in compounding(180000, 0.20, 12)], "5%", [round(x) for x in compounding(180000, 0.05, 12)], "flat", 180000 * 12)
    print("== Ch3 sample sizes", sample_size(0.5, 0.05), sample_size(0.5, 0.05, pop=400), sample_size(0.2, 0.05), sample_size(0.5, 0.03))
    L = queue_population()
    print("== Ch3 queue top-k shares", [(k, round(top_k_share(L, k), 3)) for k in (5, 10, 20, 40, 100)], "largest", round(L[0]), "median", round(L[len(L)//2], 1))
    print("== Ch3 sample estimate k=40", [round(x, 3) for x in sample_estimate(L, 40)], "k=100", [round(x, 3) for x in sample_estimate(L, 100)])
    print("== Ch12 price rise", breakeven_loss(40, .10, 22), price_rise(40, .10, [(20, 60, .30), (80, 12.5, .05)]), price_rise(40, .10, [(20, 60, .10), (80, 12.5, .10)])[1], price_rise(40, .10, [(20, 60, 0.0), (80, 12.5, .20)])[1])
    print("== Ch6 series", series_count([7, 12, 2400, 6, 3]), occupied_series(2400, 2.5, 1.8, 1.6, 2), series_count([7, 12, 6, 3]), [round(monthly_series_cost(x), 2) for x in (3628800, 34560, 1512)])
