import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import brevity_lab as b
def test_expected_answers():
    assert abs(3400*1.0/1e6 + 900*5.0/1e6 - 0.0079) < 1e-12
    assert abs(0.17*2450 - 416.5) < 1e-9
    assert abs(0.1*3.0*2 - 0.60) < 1e-12
    assert round(18400/23) == 800
    assert abs(0.8*5 - 4.0) < 1e-12
    assert 1260*0.5 == 630 and abs(1200*0.0045*30 - 162) < 1e-9
    assert 12000*40 == 480000 and (65000-52000)/52000*100 == 25
    assert sum(2500*k for k in range(1, 10)) == 112500
def test_checker():
    assert b.ok("The cost is $1,620", "162") is False
    assert b.ok("**$162**", "162") is True
    assert b.ok("0.0079", "0.00790") is True
def test_run_file_has_no_errors():
    rows = [json.loads(l) for l in (Path(__file__).resolve().parents[1] / "runs" / "brevity-lab-2026-11-12.jsonl").read_text().splitlines()]
    assert len(rows) == 160 and not any("error" in r for r in rows)
