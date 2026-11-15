#!/usr/bin/env python3
"""Chapter 46 offline baseline (no model, no API): match each of the 30 author-written vignettes to an anti-pattern by tf-idf word overlap against (N) the name plus the control, (V) the name only, (C) the control only."""
from costlab.antipatterns import AP, tfidf_match
docs = {"name only": [a[1] for a in AP], "control only": [a[2] for a in AP], "name + control": [a[1] + " " + a[2] for a in AP]}
for k, d in docs.items():
    pred = [tfidf_match(a[4], d) for a in AP]; ok = [p == i for i, p in enumerate(pred)]
    print(f"{k:15} correct {sum(ok)} of 30 ({sum(ok) / 30:.0%})")
    if k == "name + control":
        print("  misses:", ", ".join(f"{AP[i][0]}->{AP[p][0]}" for i, p in enumerate(pred) if p != i))
