from costlab.antipatterns import AP, tfidf_match
from costlab.antipatterns_extra import CAND
def test_six_candidates_with_distinct_ids():
    assert len(CAND) == 6 and len({c[0] for c in CAND}) == 6
def test_ids_do_not_collide_with_thirty():
    assert not ({c[0] for c in CAND} & {a[0] for a in AP})
def test_tuple_shape(): assert all(len(c) == 5 and all(isinstance(x, str) and x for x in c) for c in CAND)
def test_matcher_returns_an_existing_index():
    docs = [a[1] + " " + a[2] for a in AP]; assert all(0 <= tfidf_match(c[4], docs) < 30 for c in CAND)
