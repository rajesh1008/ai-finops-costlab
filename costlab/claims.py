"""Chapter 48 (nineteenth run): a dated claims register. Each claim about the market carries what it rests on, how deeply the source was read, the date last checked, and an expiry
trigger. `due` lists claims whose check date is older than `max_age_days` or whose stated trigger date has passed. The claims below are the ones this book leans on that are known to expire; they
are written from the chapters and the sources opened or seen on 11 November 2026."""
from datetime import date, timedelta
CLAIMS = [
    ("FOCUS 1.5 is a working draft; ratification planned 3 Dec 2026", "focus.finops.org release scope, opened in full", date(2026, 11, 11), date(2026, 12, 3)),
    ("FOCUS 1.5 adds TokenDirection and TokenCacheAction as recommended, not required", "same page, opened in full", date(2026, 11, 11), date(2026, 12, 3)),
    ("FOCUS 1.5 does not model reasoning tokens, batch tiers or cache storage charges", "same page, opened in full", date(2026, 11, 11), date(2026, 12, 3)),
    ("claude-haiku-4-5 cache minimum prefix about 4,096 tokens (bracketed 4,092 to 4,126)", "Ch48 sweep, real calls", date(2026, 11, 11), None),
    ("claude-haiku-5-5 count_tokens exceeds usage by exactly 2", "Ch48 canary, real calls", date(2026, 11, 11), None),
    ("Placeholder price table (prices.py) matches the vendor page of 10 Nov 2026", "vendor page opened 10 Nov", date(2026, 11, 10), None),
    ("Singtel, Wiz, Schwab, Data Capital and NCS postings are open", "search excerpts", date(2026, 11, 11), date(2026, 11, 13)),
    ("Token consumption of coding agents varies up to 30x across runs of one task", "arXiv 2604.22750, excerpt", date(2026, 11, 11), None),
    ("Calibrated agent-cost intervals cover 82 percent at task start (nominal 90)", "arXiv 2609.35760, opened in full", date(2026, 11, 11), None),
]
def due(today, max_age_days=30):
    out = []
    for text, basis, checked, trigger in CLAIMS:
        reasons = []
        if (today - checked).days > max_age_days: reasons.append(f"checked {(today - checked).days} days ago")
        if trigger and today >= trigger: reasons.append(f"trigger date {trigger.isoformat()} reached")
        if reasons: out.append((text, basis, "; ".join(reasons)))
    return out
def upcoming(today, within_days=30):
    return sorted((t, text) for text, _, _, t in CLAIMS if t and today <= t <= today + timedelta(days=within_days))
