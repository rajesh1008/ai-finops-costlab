from collections import defaultdict
from typing import Iterable
from .records import InvoiceLine
from .taxonomy import classify_line


def parse_mixed_model_line(description: str) -> list[str]:
    """Failure injection helper: split a line that names two models."""
    parts = [p.strip() for p in description.replace(" and ", ",").split(",")]
    models = [p for p in parts if p]
    return models


def summarise(lines: Iterable[InvoiceLine]) -> dict:
    by_class = defaultdict(float)
    by_owner = defaultdict(float)
    unknown = 0.0
    total = 0.0
    for line in lines:
        klass = classify_line(line.description, line.unit)
        by_class[klass] += line.amount_usd
        total += line.amount_usd
        owner = line.product_tag or "unattributed"
        by_owner[owner] += line.amount_usd
        if owner == "unattributed":
            unknown += line.amount_usd
    coverage = 0.0 if total == 0 else (total - unknown) / total
    return {
        "total_usd": round(total, 2),
        "unattributed_usd": round(unknown, 2),
        "attribution_coverage": round(coverage, 4),
        "by_class": dict(by_class),
        "by_owner": dict(by_owner),
    }
