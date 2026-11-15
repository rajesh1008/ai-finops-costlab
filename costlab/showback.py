"""Chapter 36: allocation rules for shared and metered AI spend. Pure functions, no network."""
from costlab.prices import PLACEHOLDER_USD_PER_MTIOK as P


def call_usd(model, inp=0, out=0, cr=0, cw=0, table=P):
    r = table["anthropic:" + model] if not model.startswith("anthropic:") else table[model]
    return (inp * r["input"] + out * r["output"] + cr * r["cache_read"] + cw * r["cache_write"]) / 1e6


def caller_pays(rows):
    """Each team pays what its own calls were billed (the writer carries the write)."""
    out = {}
    for r in rows:
        out[r["team"]] = out.get(r["team"], 0.0) + r["billed"]
    return out


def amortised(rows):
    """The platform pools every call's billed cost on the shared prefix and each call pays the same share of the
    prefix cost (write plus reads) plus its own suffix and output cost."""
    shared = sum(r["prefix_usd"] for r in rows)
    n = len(rows)
    out = {}
    for r in rows:
        out[r["team"]] = out.get(r["team"], 0.0) + r["own_usd"] + shared / n
    return out


def uncached_list(rows):
    """Requested-price rule: each team pays as if it had no cache; the platform keeps the difference."""
    out = {}
    for r in rows:
        out[r["team"]] = out.get(r["team"], 0.0) + r["uncached"]
    return out


def selfish_cache_choice(rows, rule):
    """Each team keeps caching on only if its bill under the rule beats its bill uncached. Returns per-team choice and
    the company total after choices (a team off the cache pays uncached cost; writes then fall on whoever is left)."""
    teams = sorted({r["team"] for r in rows})
    base = rule(rows)
    unc = uncached_list(rows)
    choice = {t: base[t] <= unc[t] for t in teams}
    return choice, base, unc


def headcount_split(total, headcount):
    s = sum(headcount.values())
    return {t: total * h / s for t, h in headcount.items()}


def misallocation(alloc, truth):
    """Half the sum of absolute differences as a share of the total (share of dollars charged to the wrong team)."""
    t = sum(truth.values())
    keys = set(alloc) | set(truth)
    return 0.5 * sum(abs(alloc.get(k, 0.0) - truth.get(k, 0.0)) for k in keys) / t


def monthly_tco(fee=0.0, infra=0.0, h_run=0.0, h_build=0.0, rate=0.0, months=24):
    """The build-versus-buy formula used in Chapter 38: F + I + H_run*R + H_build*R/M."""
    return fee + infra + h_run * rate + h_build * rate / months


def allocation_cost_per_mtok(usage_cost_per_mtok, utilisation):
    """Allocation-based cost per million tokens is usage-based cost divided by utilisation (the relation the OpenCost post states)."""
    return usage_cost_per_mtok / utilisation
