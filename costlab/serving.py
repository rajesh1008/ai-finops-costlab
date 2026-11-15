"""Chapter 20: serving-mode arithmetic. Batch factor 0.5 from the vendor page (opened 10 Nov 2026). Self-host numbers are ASSUMED inputs."""

def batch_cost(sync_usd, share_batchable, factor=0.5):
    """Blended cost when `share_batchable` of the spend can move to a batch at `factor` of the price."""
    return sync_usd * (1 - share_batchable) + sync_usd * share_batchable * factor

def effective_self_host_per_mtok(hourly_usd, tokens_per_sec, utilisation):
    """USD per million output tokens: H * 1e6 / (3600 * theta * U). The 1/U term is the whole point."""
    return hourly_usd * 1e6 / (3600 * tokens_per_sec * utilisation)

def breakeven_utilisation(hourly_usd, tokens_per_sec, api_usd_per_mtok):
    """U* = H * 1e6 / (3600 * theta * C_api). Above 1.0 means self-hosting can never win at that throughput."""
    return hourly_usd * 1e6 / (3600 * tokens_per_sec * api_usd_per_mtok)

def breakeven_tokens_per_hour(hourly_usd, api_usd_per_mtok):
    """Output tokens an hour a GPU must sustain to match the API price, before utilisation and staff."""
    return hourly_usd / api_usd_per_mtok * 1e6

def committed_capacity_cost(units, unit_hourly, hours=730):
    return units * unit_hourly * hours

def units_needed(peak_tokens_per_sec, unit_tokens_per_sec, headroom=0.7):
    """Units to serve a peak while running at `headroom` of capacity at that peak."""
    import math
    return math.ceil(peak_tokens_per_sec / (unit_tokens_per_sec * headroom))
