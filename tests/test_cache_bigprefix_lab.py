import sys, pathlib, json
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
import cache_bigprefix_lab as B
def test_committed_run_shape():
    rows = [json.loads(l) for l in B.OUT.read_text().splitlines()]
    assert len(rows) == 8 and all("error" not in u for r in rows for u in r["rows"])
    s = B.summarise(rows)
    assert all(29000 < s[g]["prefix_tokens"] < 33000 for g in s)
def test_simultaneous_never_reads_and_costs_more_than_uncached():
    rows = [json.loads(l) for l in B.OUT.read_text().splitlines()]
    s = B.summarise(rows)
    assert s[0]["reads"] == 0
    uncached = 4 * s[0]["prefix_tokens"] / 1e6
    assert s[0]["mean_cost_per_chain"] > uncached and s[1]["mean_cost_per_chain"] < 0.5 * uncached
