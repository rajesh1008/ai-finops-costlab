import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from tool_output_lab import make_table, render, questions, correct, rescore, summarise, VARIANTS

def test_table_reproducible():
    assert make_table() == make_table() and len(make_table()) == 120

def test_variants_shrink_in_order():
    rows = make_table(); n = {v: len(render(rows, v)) for v in VARIANTS}
    assert n["pretty_full"] > n["compact_full"] > n["projected"] > n["top20_projected"]

def test_variants_keep_the_same_facts():
    rows = make_table()
    assert json.loads(render(rows, "compact_full")) == rows
    assert [r["invoice_id"] for r in json.loads(render(rows, "projected"))] == [r["invoice_id"] for r in rows]
    assert len(json.loads(render(rows, "top20_projected"))) == 20

def test_questions_answerable_from_projection_but_maybe_not_top20():
    rows = make_table(); qs = questions(rows)
    ids = {r["invoice_id"] for r in json.loads(render(rows, "projected"))}
    assert qs[0][1] in ids and len(qs) == 3

def test_correct_checker():
    assert correct("INV-0042.", "INV-0042") and correct("The count is 24", "24") and not correct("25", "24")

def test_summarise():
    rows = [{"model": "m", "variant": "projected", "q": 0, "input": 100, "ok": True}, {"model": "m", "variant": "projected", "q": 0, "input": 300, "ok": False}]
    s = summarise(rows)["m"]["projected"]
    assert s["mean_input"] == 200 and s["correct"] == 1

def test_checker_does_not_accept_substring_of_longer_number():
    assert not correct("The count is 124", "24")

def test_bold_answer_counts_and_prefix_does_not():
    assert correct("the largest is **INV-0069**.", "INV-0069")
    assert not correct("INV-00690", "INV-0069")

def test_rescore_only_adds():
    qs = [("q", "INV-0069")]
    rows = [{"q": 0, "ok": False, "reply": "**INV-0069**"}, {"q": 0, "ok": False, "reply": "INV-0039"}, {"q": 0, "ok": True, "reply": ""}]
    assert [r["ok"] for r in rescore(rows, qs)] == [True, False, True]
