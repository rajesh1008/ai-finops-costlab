import sys, pathlib, json
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
import short_reply_lab as S
def test_committed_run_shape():
    rows = [json.loads(l) for l in S.OUT.read_text().splitlines()]
    assert len(rows) == 100 and all("error" not in x for x in rows)
    assert all(x["text"] for x in rows)
def test_no_short_replies_in_either_arm():
    rows = [json.loads(l) for l in S.OUT.read_text().splitlines()]
    s = S.summarise(rows)
    assert s["A_terse_line"]["short"] == 0 and s["B_neutral_line"]["short"] == 0
    assert s["A_terse_line"]["min_out"] > 300
def test_summarise_counts_short():
    rows = [{"arm": "A_terse_line", "out": 5, "stop": "end_turn", "cost": 0.01}, {"arm": "A_terse_line", "out": 400, "stop": "max_tokens", "cost": 0.02}]
    s = S.summarise(rows)["A_terse_line"]
    assert s["short"] == 1 and s["max_tokens_stops"] == 1
