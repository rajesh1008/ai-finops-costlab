import math
from costlab.modelchange import *
def test_classify():
    assert classify('{"ref":"FS-1","days":30}', ["FS-1", "30"], True) == "correct"
    assert classify('{"ref":"FS-1","days":31}', ["FS-1", "30"], True) == "wrong"
    assert classify('{"ref":null,"days":null}', ["x"], False) == "correct_decline"
    assert classify('{"ref":null,"days":null}', ["x"], True) == "wrong_decline"
    assert classify("", ["x"], True) == "unparsed" and classify("```json {}```", ["x"], True) == "unparsed"
def test_break_even():
    assert math.isclose(break_even_failure_cost(0.4, 0.0, 0.1, 0.3), 1.0)
    assert break_even_failure_cost(0.4, 0.3, 0.1, 0.1) is None
def test_shim():
    assert classify("```json\n{\"ref\":null,\"days\":null}\n```", ["x"], False, shim=True) == "correct_decline"
    assert classify("Because x.\n{\"ref\":null,\"days\":null}", ["x"], False, shim=True) == "unparsed"
def test_binom_tail():
    assert math.isclose(binom_tail(10, 0, 0.3), 1.0) and math.isclose(binom_tail(2, 2, 0.5), 0.25)
def test_canary_detects_bad_candidate_faster_than_good():
    bad = canary_detect([1] * 3 + [0] * 7, 0.01, trials=200, max_n=300)
    good = canary_detect([0] * 100, 0.01, trials=50, max_n=300)
    assert statistics_median(bad) < 300 and good[0] == 301
def statistics_median(x): return x[len(x) // 2]
