import json
from datetime import date
from pathlib import Path
from costlab.records import InvoiceLine
from costlab.ownership import build_queue
from costlab.coverage import gap_report, days_in

FIX = Path(__file__).resolve().parents[1] / "fixtures" / "fieldstone_invoices.json"


def test_queue_is_ranked_and_complete():
    lines = [InvoiceLine(**x) for x in json.loads(FIX.read_text())["lines"]]
    q = build_queue(lines)
    assert len(q) == 5                       # five lines have no owner tag
    assert q[0]["amount_usd"] == 43400 and q[0]["class"] == "mixed_unsplit"
    assert [r["amount_usd"] for r in q] == sorted([r["amount_usd"] for r in q], reverse=True)
    assert abs(sum(r["amount_usd"] for r in q) - 108000) < 1e-6
    assert q[-1]["cumulative_share"] == 1.0


def test_gap_flat_and_growing():
    days = days_in(date(2026, 10, 1), date(2026, 10, 31))
    kept = [d for d in days if d < date(2026, 10, 21)]
    flat = gap_report(date(2026, 10, 1), date(2026, 10, 31), kept, 1.0, 180000)
    grow = gap_report(date(2026, 10, 1), date(2026, 10, 31), kept, 1.2, 180000)
    assert flat["missing_days"] == 11
    assert abs(flat["dollar_share"] - 11 / 31) < 1e-12
    assert grow["dollar_share"] > flat["dollar_share"]
