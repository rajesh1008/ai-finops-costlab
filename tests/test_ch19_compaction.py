import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from compaction_lab import make_steps, history, questions, correct, summarise, VARIANTS, STEPS

def test_steps_reproducible():
    assert make_steps() == make_steps() and len(make_steps()) == STEPS

def test_history_sizes_order():
    s = make_steps(); n = {v: len(history(v, s, "short summary")) for v in VARIANTS}
    assert n["full"] > n["digest"] and n["full"] > n["window"] and n["full"] > n["model_summary"]

def test_digest_keeps_id_not_carrier():
    s = make_steps(); q = questions(s); d = history("digest", s)
    assert q[0][1] in d and q[1][1] not in d and q[2][1] in d

def test_window_drops_step3_keeps_step13():
    s = make_steps(); q = questions(s); w = history("window", s)
    assert q[0][1] not in w and q[2][1] in w

def test_correct():
    assert correct("**CR123456**", "CR123456") and not correct("CR123457", "CR123456")

def test_summarise():
    rows = [{"model": "m", "variant": "full", "q": 0, "input": 100, "ok": True}, {"model": "m", "variant": "full", "q": 0, "input": 300, "ok": False}]
    assert summarise(rows)["m"]["full"]["mean_input"] == 200
