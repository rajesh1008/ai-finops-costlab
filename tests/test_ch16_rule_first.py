import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from rule_first_lab import rule, make
from rule_first_summary import summarise

def test_rule_formats():
    assert rule("2026-03-12") == "2026-03-12"
    assert rule("12 March 2026") == "2026-03-12"
    assert rule("March 12, 2026") == "2026-03-12"
    assert rule("12-Mar-2026") == "2026-03-12"
    assert rule("20260312") is None

def test_slash_slip_is_deliberate():
    assert rule("03/04/2026") == "2026-03-04"      # house convention says 3 April, rule says 4 March
    assert rule("25/04/2026") == "2026-04-25"      # unambiguous case is right

def test_make_is_reproducible():
    a, b = make(), make()
    assert a == b and len(a) == 60

def test_summarise_counts():
    rows = [{"model": "m", "fmt": "iso", "text": "2026-03-12", "truth": "2026-03-12", "answer": "2026-03-12", "in": 100, "out": 10},
            {"model": "m", "fmt": "compact", "text": "20260312", "truth": "2026-03-12", "answer": "2026-12-03", "in": 100, "out": 10}]
    s = summarise(rows)["m"]
    assert s["rule_handles"] == 1 and s["model_only_correct"] == 1 and s["hybrid_correct"] == 1
