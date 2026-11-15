#!/usr/bin/env python3
"""Chapter 3: the seven-product table and the 'known' test. No API calls.

All figures are Fieldstone assumptions (synthetic). The rule for 'known' is the book's: a signed
definition, a count, a cost from a measured source for the same period, and a person who can say
what was included. Costs here come from the October fixture's tagged lines where one exists; the
three products with no tagged line carry an assumed cost, marked so.
"""
rows = [
 # product, cost_usd, cost_kind, count_assumed, signed_def, cost_measured_source, named_person
 ("support-agent",        25_350, "tagged invoice lines", 41_000, False, True,  True),
 ("nl-query",             21_000, "tagged invoice line",  60_000, False, True,  True),
 ("knowledge-assistant",  11_750, "tagged line (embeddings only)", 90_000, False, False, True),
 ("report-pipeline",      13_900, "tagged line (provisioned capacity)", 12_000, False, True,  True),
 ("contract-extraction",   9_000, "assumed",  8_500, False, False, False),
 ("data-prep-assistant",   4_000, "assumed", 15_000, False, False, False),
 ("alert-explainer",       1_500, "assumed", 30_000, False, False, False),
]
print(f"{'product':22s}{'cost':>9s}  {'outcomes':>9s}  {'$/outcome':>9s}  signed count measured person  known")
known = 0
for p, c, kind, n, signed, meas, person in rows:
    ok = signed and n > 0 and meas and person
    known += ok
    print(f"{p:22s}{c:>9,d}  {n:>9,d}  {c/n:>9.3f}  {str(signed):6s} {'yes':5s} {str(meas):8s} {str(person):6s} {'yes' if ok else 'no'}   [{kind}]")
print(f"\nknown by the four-part rule: {known} of {len(rows)}  (the scoreboard says 2 of 7)")
print("naive $/outcome ranks the products using counts nobody signed; read the column as arithmetic, not as a finding")
