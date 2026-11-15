from costlab.segments import single, compose, trace_triple, total_from_triple, total, repeated_input_share, quadratic_fit
CALLS = [(1000, 50), (1200, 60), (1500, 40), (1500, 30)]
def test_total_matches_identity(): assert total_from_triple(trace_triple(CALLS), CALLS[0][0]) == total(CALLS)
def test_associative():
    s = [single(CALLS, k) for k in range(4)]
    assert compose(compose(s[0], s[1]), compose(s[2], s[3])) == compose(s[0], compose(s[1], compose(s[2], s[3])))
def test_paper_worked_numbers():
    assert 6 * 129_714 + 9_181 == 787_465 and 787_465 - 9_181 == 778_284
def test_repeated_share(): assert 0.7 < repeated_input_share(CALLS) < 1.0
def test_quadratic_fit_exact_for_linear():
    c = [(1000 + 100 * k, 10) for k in range(5)]; g, t = quadratic_fit(c); assert g == 100 and t == total(c)
def test_single_call(): assert single([(500, 20)], 0) == (1, 0, 20)
