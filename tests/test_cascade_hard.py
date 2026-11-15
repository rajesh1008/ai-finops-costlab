import pytest
from costlab.cascade_hard import make_hard, safe_eval
def test_problem_count_and_exact(): p = make_hard(); assert len(p) == 40 and all(isinstance(x["answer"], float) for x in p)
def test_safe_eval_arithmetic(): assert safe_eval("(2+3)*4/8") == 2.5
def test_safe_eval_rejects_calls():
    with pytest.raises(ValueError): safe_eval("__import__('os').system('x')")
def test_safe_eval_rejects_names():
    with pytest.raises(ValueError): safe_eval("a+1")
def test_known_answer():
    s, p, d, r, m, t = 20, 50, 10, 4, 3, 10
    assert round((s * p * 0.9 - r * p * 0.9 * 9 / 12) * 1.1, 2) == 841.5
    assert safe_eval("(20*50*0.9 - 4*50*0.9*9/12)*1.1") - 841.5 < 1e-9
