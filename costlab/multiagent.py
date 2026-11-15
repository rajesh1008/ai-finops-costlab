"""Chapter 25: coordination-tax arithmetic and role cost splits for multi-agent runs.
break_even_fraction and feasible implement equations (3) and (4) of Zettl and Gosmar (arXiv 2610.37700) as stated in the paper; they are checked against the paper's Table 1 in tests."""
def break_even_fraction(alpha, r):
    """Minimum routable fraction f* = (alpha-1)/(alpha(1-r)) for a decomposed pipeline to undercut one strong call (output-dominated cost). None if infeasible."""
    if alpha <= 0 or not 0 < r < 1: raise ValueError("alpha > 0 and 0 < r < 1 required")
    f = (alpha - 1) / (alpha * (1 - r))
    return None if alpha > 1 / r + 1e-12 else max(f, 0.0)

def feasible(alpha, r): return alpha < 1 / r

def pipeline_cost_ratio(alpha, f, r):
    """Cost of the decomposed pipeline over the single strong call: alpha * ((1-f) + f*r)."""
    return alpha * ((1 - f) + f * r)

def role_costs(roles, usd_in, usd_out):
    """roles: {name: [step,...]} with step {'in','out'}. Returns {name: dollars}."""
    return {k: sum(s["in"] / 1e6 * usd_in + s["out"] / 1e6 * usd_out for s in v) for k, v in roles.items()}

def overhead_share(costs):
    """Share of run cost spent by the supervisor roles (names starting with 'supervisor')."""
    tot = sum(costs.values())
    return sum(v for k, v in costs.items() if k.startswith("supervisor")) / tot if tot else 0.0

def parallel_latency_gain(worker_times):
    """Wall time of sequential workers over parallel workers (sum / max)."""
    return sum(worker_times) / max(worker_times)
