#!/usr/bin/env python3
"""Chapter 3 failure injection: the gateway log stops eleven days before the month ends.

Synthetic: one record per day for 20 October to 31 October is removed. The invoice total is the
Fieldstone fixture's $180,000. Growth within the month is the book's 20 percent assumption.
"""
from datetime import date
from costlab.coverage import days_in, gap_report

start, end = date(2026, 10, 1), date(2026, 10, 31)
all_days = days_in(start, end)
kept = [d for d in all_days if d < date(2026, 10, 21)]   # log ends on 20 October: 11 days missing
for label, g in (("flat", 1.0), ("20% month growth", 1.20)):
    r = gap_report(start, end, kept, monthly_growth=g, invoice_total=180_000)
    print(f"{label:18s} missing {r['missing_days']} of {r['days']} days ({r['day_share']:.1%} of days) "
          f"= {r['dollar_share']:.1%} of dollars = ${r['usd_at_risk']:,.0f} from {r['missing_from']}")
