import json, random, pytest
from pathlib import Path
from costlab.retrieval import BM25
from costlab.ladder import *
RUNS = Path(__file__).resolve().parents[1] / "runs"
C = clauses(); BM = BM25([c["text"] for c in C])
def test_escalation_chain_matches_earlier_labs():
    assert nxt(1) == 49 and ref(1) == "FS-1013" and days(1) == 45
def test_questions_are_reproducible_and_mixed():
    a = make_questions(200, 5); assert a == make_questions(200, 5) and {q["t"] for q in a} == {"A", "B", "C"}
def test_score_needs_every_token():
    assert score("FS-1013, 45 days", ["FS-1013", "45"]); assert not score("FS-1013, 450 days", ["FS-1013", "45"]); assert not score("FS-10130, 45", ["FS-1013", "45"]); assert not score("", ["45"])
def test_deterministic_rung_answers_a_and_b_and_abstains_on_c():
    for q in make_questions(60, 3):
        a = deterministic_answer(q["q"], BM, C)
        if q["t"] == "C": assert a is None
        elif a is not None: assert score(a, q["gold"])   # it may abstain when the numeric lookup misses (clause numbers collide with day counts in BM25)
def test_cache_hit_miss_and_limit():
    c = ExactCache(limit=2); assert c.get("What is X?") is None; c.put("What is X?", 1); assert c.get("what is  x") == 1; c.put("b", 2); c.put("c", 3); assert c.get("What is X?") is None and c.hits == 1
def test_zipf_stream_is_skewed():
    s = zipf_stream(5000, 100, 1.0, 1); from collections import Counter; top = Counter(s).most_common(1)[0][1]; assert top > 5000 / 100 * 3
def _table(n=50):
    return {q: {"key": f"k{q}", "stale": False, "full": (0.003, True), "reduced": (0.0001, True if q % 2 else None), "deterministic": (0.0, True if q % 3 == 0 else None)} for q in range(n)}
def test_cliff_never_exceeds_budget_and_turns_off():
    T = _table(); stream = list(range(50)) * 4; r = run_ladder(stream, T, 0.15, "cliff", {"full": 0.003, "reduced": 0.0001})
    assert r["spend"] <= 0.15 + 1e-9 and r["off"] > 0 and r["correct"] + r["wrong"] + r["off"] == 200
def test_ladder_degrades_instead_of_stopping():
    T = _table(); stream = list(range(50)) * 4; cm = {"full": 0.003, "reduced": 0.0001}
    a = run_ladder(stream, T, 0.15, "cliff", cm); b = run_ladder(stream, T, 0.15, "ladder_naive", cm)
    assert b["spend"] <= 0.15 + 1e-9 and b["by_rung"]["reduced"] > 0 and b["correct"] > a["correct"]
def test_decline_is_off_not_wrong():
    T = {0: {"key": "k", "stale": False, "full": (0.003, True), "reduced": (0.0001, None), "deterministic": (0.0, None)}}
    r = run_ladder([0], T, 0.0002, "ladder_naive", {"full": 0.003, "reduced": 0.0001}); assert r["off"] == 1 and r["wrong"] == 0
def test_stale_cache_answer_is_wrong():
    T = {0: {"key": "k", "stale": True, "full": (0.003, True), "reduced": (0.0001, True), "deterministic": (0.0, True)}}
    r = run_ladder([0, 0], T, 1.0, "cliff_cache", {"full": 0.003, "reduced": 0.0001}); assert r["correct"] == 1 and r["wrong"] == 1
def test_wilson_contains_p_and_shrinks():
    lo, hi = wilson(50, 100); assert lo < 0.5 < hi; lo2, hi2 = wilson(500, 1000); assert hi2 - lo2 < hi - lo
def test_paired_diff_counts():
    m, se, bw, aw = paired_diff([1, 0, 1, 0], [1, 1, 0, 0]); assert (bw, aw) == (1, 1) and m == 0
def test_ppi_is_unbiased_with_perfect_judge_and_corrects_a_biased_one():
    g = [1] * 30 + [0] * 70; est, se = ppi_mean(g, g[:20], g[:20]); assert est == pytest.approx(0.30)
    judge = [1] * 50 + [0] * 50; gold = [1] * 30 + [0] * 70   # judge says 0.5, truth 0.3; a calibration set drawn from the same items reveals the bias
    est, se = ppi_mean(judge, judge, gold); assert est == pytest.approx(0.30)
def test_usd():
    assert usd(1_000_000, 1_000_000, (1.0, 5.0)) == 6.0
@pytest.mark.skipif(not (RUNS / "ladder-lab-2026-11-10.json").exists(), reason="no recorded run")
def test_recorded_ladder_lab():
    d = json.load(open(RUNS / "ladder-lab-2026-11-10.json")); assert len(d["results"]) == 240 and {r["rung"] for r in d["results"]} == {"full", "reduced"} and all(r["status"] != "api_error" for r in d["results"])
    assert all(len(r["steps"]) <= 8 for r in d["results"])
@pytest.mark.skipif(not (RUNS / "shadow-lab-2026-11-10.json").exists(), reason="no recorded run")
def test_recorded_shadow_lab():
    d = json.load(open(RUNS / "shadow-lab-2026-11-10.json")); assert len(d["results"]) == 600 and all(r["error"] is None for r in d["results"])
    q = d["questions"]; assert all(score(r["answer"], q[r["q"]]["gold"]) == r["ok"] for r in d["results"])
@pytest.mark.skipif(not (RUNS / "judge-lab-2026-11-10.json").exists(), reason="no recorded run")
def test_recorded_judge_lab():
    d = json.load(open(RUNS / "judge-lab-2026-11-10.json")); assert len(d["results"]) == len(d["items"]) * len(d["judges"]); assert all(r["error"] is None for r in d["results"])
    assert sum(1 for i in d["items"] if i["kind"] == "corrupted" and i["gold_ok"]) <= 2   # the scorer is the label; a corruption can leave a passing answer when the recorded answer named a different clause
