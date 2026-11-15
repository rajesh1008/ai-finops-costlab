import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import ch47_run_sims as s
import history_cache_lab as h

RUN = Path(__file__).resolve().parents[1] / "runs" / "history-cache-lab-2026-11-13.jsonl"

def test_ch21_totals():
    assert [r[4] for r in s.ch21()] == [310, 1040, 2500]
def test_ch29_cascade():
    assert s.ch29()[0] == 0.0104 and s.ch29()[2] == 0.48
def test_ch32_false_block():
    assert s.ch32() == (1600, 3.2, 32, 288)
def test_ch35_sizes():
    assert s.ch35() == [9042, 25117]
def test_ch36_keys():
    assert s.ch36()["A"] == (65000.0, 60000, 53000.0)
def test_ch41_interval_minimum():
    r = s.ch41()
    assert r[(6, 30)][2] < r[(3, 30)][2] and r[(6, 30)][2] < r[(12, 30)][2]
def test_ch47_range():
    a = s.ch47(); assert a[0] == 9000 and a[3] == 3150 and a[4] == 28800
def test_ch48_cost_per_answer():
    assert s.ch48()[2] == 2.79
def test_history_lab_cost_function():
    u = {"in": 1_000_000, "out": 0, "cr": 1_000_000, "cw": 1_000_000}
    assert abs(h.cost(u) - (1.0 + 0.10 + 1.25)) < 1e-9
def test_history_lab_run_file():
    rows = [json.loads(l) for l in RUN.read_text().splitlines()]
    assert len(rows) == 12 and all("error" not in r for r in rows)
    assert sum(len(r["rows"]) for r in rows) == 120
    mean = {a: sum(sum(x["cost"] for x in r["rows"]) for r in rows if r["arm"] == a) / 4 for a in ("none", "static", "moving")}
    assert mean["moving"] < mean["static"] < mean["none"]
    assert abs(mean["none"] - 0.08153) < 1e-4
def test_history_lab_prompt_over_min():
    assert len(h.system_doc("x").split()) > 4000
