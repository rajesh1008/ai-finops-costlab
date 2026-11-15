import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
import cache_pause_lab as L
def test_cost_write_and_read():
    assert abs(L.cost({"in": 0, "out": 0, "cr": 0, "cw": 1_000_000}) - 1.25) < 1e-9
    assert abs(L.cost({"in": 0, "out": 0, "cr": 1_000_000, "cw": 0}) - 0.10) < 1e-9
def test_summarise_hits():
    rows = [{"arm": "gap30", "rep": 0, "rows": [{"cost": 0.01, "cr": 0}, {"cost": 0.001, "cr": 5000}]},
            {"arm": "gap30", "rep": 1, "rows": [{"cost": 0.01, "cr": 0}, {"cost": 0.01, "cr": 0}]}]
    s = L.summarise(rows)["gap30"]
    assert s["final_call_hits"] == 1 and abs(s["mean_final_cost"] - 0.0055) < 1e-9
def test_doc_is_deterministic_and_long():
    assert L.doc("a") == L.doc("a") and L.doc("a") != L.doc("b") and len(L.doc("a").split()) > 4000
def test_committed_run_shape():
    import json
    p = L.OUT
    rows = [json.loads(l) for l in p.read_text().splitlines()]
    s = L.summarise(rows)
    assert len(rows) == 15 and all("error" not in r for r in rows)
    assert s["gap240"]["final_call_hits"] == 3 and s["gap330"]["final_call_hits"] == 0 and s["keepwarm600"]["final_call_hits"] == 3
    assert sum(len(r["rows"]) for r in rows) == 36
