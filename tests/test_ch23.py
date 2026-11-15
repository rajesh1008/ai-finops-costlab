import json, random, pytest
from pathlib import Path
from costlab.retrieval import vector_footprint_gb, reindex_cost, context_cost_per_query, make_corpus, edit_corpus, Index, BM25, chunk_text
RUN = Path(__file__).resolve().parents[1] / "runs" / "retrieval-k-lab-2026-11-10.json"
def test_footprint_matches_source_example():
    f = vector_footprint_gb(1_000_000, 10, 1024)
    assert f["raw_gb"] == pytest.approx(40.96) and f["index_gb_high"] == pytest.approx(3 * 40.96)
def test_reindex_cost_and_context_cost():
    assert reindex_cost(500_000, 10, 500, 0.08) == pytest.approx(200.0)
    assert context_cost_per_query(8, 500, 2.5) == pytest.approx(0.01)
def test_hash_sync_embeds_only_changes_and_reconciles():
    rnd = random.Random(1); c = make_corpus(200); a = Index(); a.sync_doc_hash(c); b = Index(); b.sync_chunk_hash(c)
    c2 = edit_corpus(c, rnd, churn=0.05, delete=0.05, add=0.0)
    n_doc, n_chunk = a.sync_doc_hash(c2), b.sync_chunk_hash(c2)
    assert 0 < n_chunk <= n_doc < Index().embeddings_if_full_rebuild(c2)
    assert a.ghost_docs(c2) == [] and b.ghost_docs(c2) == []
def test_no_reconcile_leaves_ghosts():
    rnd = random.Random(2); c = make_corpus(100); a = Index(); a.sync_doc_hash(c, reconcile=False)
    c2 = edit_corpus(c, rnd, churn=0.0, delete=0.1, add=0.0); a.sync_doc_hash(c2, reconcile=False)
    assert len(a.ghost_docs(c2)) == 10
def test_bm25_finds_exact_clause():
    docs = [f"Clause {i}. tier {i % 7} window {30 + i % 12 * 15} days" for i in range(1, 100)]
    assert BM25(docs).search("clause 42", 1)[0] == 41
@pytest.mark.skipif(not RUN.exists(), reason="no recorded run")
def test_recorded_k_run_shape():
    d = json.load(open(RUN)); assert len([r for r in d["results"] if r["k"] == 4]) == 40 and d["recall"]["4"] == 1.0
