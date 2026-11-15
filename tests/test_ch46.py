from costlab.antipatterns import AP, ids, name_of, score
def test_thirty_unique(): assert len(AP) == 30 and len(set(ids())) == 30 and len({a[1] for a in AP}) == 30
def test_every_row_has_control_and_vignette(): assert all(len(a) == 5 and a[2].endswith(".") and len(a[4]) > 40 for a in AP)
def test_name_and_score(): assert name_of("A01") == "Reporting the mean" and score(["A01", "A02"], ["A01", "A03"]) == 0.5
from costlab.antipatterns import tfidf_match
def test_tfidf_picks_overlap(): assert tfidf_match("the dashboard shows an average", ["median and percentile reporting", "average dashboard figure"]) == 1
