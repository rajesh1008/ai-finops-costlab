import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import gold_position_lab as g

def test_build_places_gold_at_position():
    for p, kind, q, ans in g.QS:
        for pos in (1, 6, 12):
            ps = g.build(p, pos).split("\n\n")
            assert len(ps) == 12 and ps[pos - 1].startswith(f"Plan {p}:")

def test_build_deterministic():
    assert g.build("Alder", 6) == g.build("Alder", 6)

def test_answers_unique_in_gold_passage():
    for p, kind, q, ans in g.QS:
        assert ans in g.passage(p)

def test_stored_run_has_60_rows_and_summarises():
    rows = [json.loads(l) for l in g.OUT.read_text().splitlines()]
    assert len(rows) == 60
    good = [r for r in rows if "error" not in r]
    assert all(r["ok"] == ("".join(c for c in r["reply"] if c.isdigit()) == r["answer"]) for r in good)
