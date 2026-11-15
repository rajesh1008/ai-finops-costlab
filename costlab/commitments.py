"""Chapter 30: commitment arithmetic. SYNTHETIC usage paths and ASSUMED discounts; nothing here is a vendor term.
Three shapes: a spend commitment (dollar floor over a term), a price move that leaves the commitment denominated in old-price dollars, and provisioned capacity against a diurnal demand curve."""
import math, random

def spend_commit(usage_at_list, discount, commit_discounted):
    """usage_at_list: list of monthly spend at LIST price. Pay discounted usage, but at least `commit_discounted` over the whole term (full-period model).
    Returns dict(paid, used, shortfall, effective_discount_on_usage)."""
    used = sum(usage_at_list) * (1 - discount)
    paid = max(used, commit_discounted)
    return {"paid": paid, "used": used, "shortfall": max(0.0, commit_discounted - used), "list": sum(usage_at_list),
            "effective_vs_list": paid / sum(usage_at_list) if usage_at_list else float("nan")}

def monthly_floor_commit(usage_at_list, discount, floor_per_month):
    """Use-it-or-lose-it each month (continuous model)."""
    paid = sum(max(u * (1 - discount), floor_per_month) for u in usage_at_list)
    used = sum(u * (1 - discount) for u in usage_at_list)
    return {"paid": paid, "used": used, "shortfall": paid - used, "list": sum(usage_at_list)}

def usage_path(months, start, growth, seed=0, noise=0.05):
    rnd = random.Random(seed); out = []; v = start
    for _ in range(months):
        out.append(v * rnd.lognormvariate(0, noise)); v *= 1 + growth
    return out

def price_cut_path(list_usage, cut_month, task_cost_ratio):
    """Same work, but from `cut_month` (1-based) the list price per task is `task_cost_ratio` of before (migration to a newer model)."""
    return [u * (task_cost_ratio if m >= cut_month else 1.0) for m, u in enumerate(list_usage, start=1)]

def breakeven_utilisation(provisioned_unit_cost_per_token_at_full, ondemand_cost_per_token):
    """Utilisation at which provisioned equals on-demand per token. Above 1.0 means provisioned never wins on unit cost."""
    return provisioned_unit_cost_per_token_at_full / ondemand_cost_per_token

def diurnal_demand(hours=24 * 30, peak=1000.0, trough_share=0.1, weekend_share=0.5, seed=0, noise=0.1):
    """Tokens per minute demanded per hour: business-hours hump, quiet nights, quieter weekends. SYNTHETIC."""
    rnd = random.Random(seed); out = []
    for h in range(hours):
        hod = h % 24; dow = (h // 24) % 7
        base = trough_share + (1 - trough_share) * max(0.0, math.sin(math.pi * (hod - 7) / 12)) if 7 <= hod <= 19 else trough_share
        if dow >= 5: base *= weekend_share
        out.append(peak * base * rnd.lognormvariate(0, noise))
    return out

def provisioned_cost(demand, capacity, capacity_price_per_unit_hour, ondemand_price_per_unit_hour, spillover=True):
    """Per hour: pay capacity always; demand above capacity spills to on-demand (if spillover) or is dropped (counted)."""
    paid = len(demand) * capacity * capacity_price_per_unit_hour
    spill = sum(max(0.0, d - capacity) for d in demand) * ondemand_price_per_unit_hour if spillover else 0.0
    dropped = 0.0 if spillover else sum(max(0.0, d - capacity) for d in demand)
    served_by_cap = sum(min(d, capacity) for d in demand)
    util = served_by_cap / (len(demand) * capacity) if capacity > 0 else float("nan")
    return {"capacity_cost": paid, "spill_cost": spill, "total": paid + spill, "utilisation": util, "dropped": dropped}

def eligible_only_old_model(usage_old_list, usage_new_list, discount, commit_discounted):
    """Failure injection: the commitment counts spend on the old model only. Spend on the new model is paid at list and does not count toward the commit.
    Returns dict(paid, shortfall, new_model_list_paid)."""
    used = sum(usage_old_list) * (1 - discount)
    short = max(0.0, commit_discounted - used)
    new_paid = sum(usage_new_list)
    return {"paid": max(used, commit_discounted) + new_paid, "used": used, "shortfall": short, "new_list": new_paid}

def commit_with_protection(usage_at_old_list, discount, commit_discounted, cut_month, task_cost_ratio, ramp=None):
    """Price protection as I would draft it: from the month the list price per task falls to `task_cost_ratio`, the commit is scaled by that ratio for the remaining months
    (commit stated in work, not in dollars). `ramp` optionally gives a list of monthly fractions of the commit that fall due each month (sums to 1)."""
    n = len(usage_at_old_list); ramp = ramp or [1.0 / n] * n
    paid_floor = 0.0; used = 0.0
    for m, (u, f) in enumerate(zip(usage_at_old_list, ramp), start=1):
        scale = task_cost_ratio if m >= cut_month else 1.0
        spend = u * scale * (1 - discount); used += spend; paid_floor += commit_discounted * f * scale
    paid = max(used, paid_floor)
    return {"paid": paid, "used": used, "shortfall": max(0.0, paid_floor - used), "list": sum(u * (task_cost_ratio if m >= cut_month else 1.0) for m, u in enumerate(usage_at_old_list, start=1))}
