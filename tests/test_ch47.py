import tempfile, os
from costlab.interviewgrade import extract, sample, first_sentence, pick_strong_rate, position_bias
DOC = '# Chapter 1\n\n## Interview Questions and Answers\n\n### Why?\n\nBecause the meter is the only place that knows the cost of a call. That is the whole answer.\n\nA weak answer: "Because finance asked."\n\n### Too short?\n\nShort.\n\nA weak answer: "No."\n'
def test_extract_and_filter():
    d = tempfile.mkdtemp(); open(os.path.join(d, "ch01-x.md"), "w").write(DOC)
    t = extract(os.path.join(d, "ch*.md")); assert len(t) == 1 and t[0]["weak"] == "Because finance asked." and t[0]["q"] == "Why?"
def test_first_sentence(): assert first_sentence("One. Two.") == "One." and first_sentence("none") == "none"
def test_rates():
    rows = [{"picked": "strong", "choice": "A"}, {"picked": "weak", "choice": "A"}]
    assert pick_strong_rate(rows) == 0.5 and position_bias(rows) == 1.0
def test_sample_deterministic(): assert sample(list(range(50)), 5) == sample(list(range(50)), 5)
from costlab.interviewgrade import h_longer, h_numbers, h_overlap, h_hedges
def test_heuristics():
    assert h_longer("a b c d", "a b", "q") and h_numbers("1 2 3", "none", "q") and h_hedges("do this first, then that", "do it", "q")
    assert h_overlap("the meter records cost", "totally unrelated words appear", "what does the meter record")
