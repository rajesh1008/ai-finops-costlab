import sys, pathlib, json
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
import tool_index_lab as L
def test_corpus_deterministic_and_one_fact():
    a, b = L.corpus(3), L.corpus(3)
    assert a == b and len(a) == 10 and all(f"is {d['n']} units" in d["text"] for d in a)
def test_summarise():
    r = {"full": {"ok": True, "cost": 0.01, "in": 100}, "index": {"ok": False, "right_pick": True, "cost": 0.002, "in": 20}}
    s = L.summarise([r, r]); assert s["full_ok"] == 2 and s["index_ok"] == 0 and abs(s["index_cost"] - 0.002) < 1e-12
def test_committed_run_shape():
    rows = [json.loads(l) for l in L.OUT.read_text().splitlines()]
    assert len(rows) == 20
