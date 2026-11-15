import json, pathlib
RUN = pathlib.Path(__file__).resolve().parents[1] / "runs" / "session-replay-lab-2026-11-13.jsonl"

def rows():
    return [json.loads(l) for l in RUN.read_text().splitlines()]

def test_stored_run_shape():
    r = rows()
    assert len(r) == 6 and all("error" not in x and len(x["turns"]) == 12 for x in r)

def test_plain_input_grows_every_turn():
    for x in rows():
        if x["mode"] == "plain":
            ins = [t["in"] for t in x["turns"]]
            assert all(b > a for a, b in zip(ins, ins[1:]))

def test_fold_drops_input_after_turn_six():
    for x in rows():
        if x["mode"] == "folded":
            ins = [t["in"] for t in x["turns"]]
            assert ins[6] < ins[5]
