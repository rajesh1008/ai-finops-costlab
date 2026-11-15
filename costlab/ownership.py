"""Ownership queue: every invoice line without an accepted owner, ranked by dollars.

A tag on a line is a claim, not an owner. This module only handles the first test, whether a
tag exists, and gives each unowned line a reason code and the evidence that would close it.
Closing a line (an owner accepting it) is a human step recorded outside the code.
"""
from .records import InvoiceLine
from .taxonomy import classify_line

EVIDENCE = {
    "mixed_unsplit": "vendor usage export by model; gateway log for the same period",
    "hosted_capacity": "list of workloads on the endpoint or block; hourly utilisation from the meter",
    "evaluation": "contract (platform fee versus usage); list of suites and who runs them",
    "observability": "retention settings by data source; the team that owns each source",
    "output_tokens": "API key or project that produced the usage; gateway log if the key is behind it",
    "input_tokens": "API key or project that produced the usage; gateway log if the key is behind it",
}


def reason_for(line: InvoiceLine) -> str:
    klass = classify_line(line.description, line.unit)
    if klass == "mixed_unsplit":
        return "mixed line: names more than one model"
    if line.product_tag is None:
        return "no product tag"
    return "owned"


def build_queue(lines: list[InvoiceLine]) -> list[dict]:
    rows = []
    for l in lines:
        reason = reason_for(l)
        if reason == "owned":
            continue
        klass = classify_line(l.description, l.unit)
        rows.append({"vendor": l.vendor, "class": klass, "amount_usd": l.amount_usd,
                     "reason": reason, "evidence_to_close": EVIDENCE.get(klass, "invoice contract and a named requester")})
    rows.sort(key=lambda r: r["amount_usd"], reverse=True)
    total = sum(r["amount_usd"] for r in rows) or 1.0
    run = 0.0
    for r in rows:
        run += r["amount_usd"]
        r["cumulative_share"] = round(run / total, 4)
    return rows
