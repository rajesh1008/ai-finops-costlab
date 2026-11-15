"""Chapter 31: the price of keeping a second vendor warm. ASSUMED parameters throughout; the structure is the point.
Annual value of optionality = P(event) x saving fraction x annual spend x share of the year left after the switch. Annual cost = standing cost of parity tests, a second contract and engineer time."""

def annual_value(spend, p_event, saving, year_share_left=0.5):
    return spend * p_event * saving * year_share_left

def breakeven_spend(standing_cost, p_event, saving, year_share_left=0.5):
    d = p_event * saving * year_share_left
    return float("inf") if d <= 0 else standing_cost / d

def switch_days(parity_ready, weeks_without=6.0):
    """Days to move a workload: a rehearsed switch is days; an unrehearsed one is weeks (ASSUMED, from the survey's median bands)."""
    return 5.0 if parity_ready else weeks_without * 7
