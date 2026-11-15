import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from alert_threshold_sim import make, evaluate, rule_mean7, rule_same_weekday

def test_reproducible():
    assert make() == make()

def test_flat_weekday_pattern_trips_mean_rule_on_mondays():
    x = [4000.0 if d % 7 < 5 else 1500.0 for d in range(60)]
    mondays = [d for d in range(28, 60) if d % 7 == 0]
    assert all(rule_mean7(x, d) for d in mondays)
    assert not any(rule_same_weekday(x, d) for d in range(28, 60))

def test_evaluate_counts_are_consistent():
    x, spots = make()
    for v in evaluate(x, spots).values():
        assert v["alerts"] == v["false"] + v["caught"]
