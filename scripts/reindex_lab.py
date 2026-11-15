#!/usr/bin/env python3
"""Chapter 23 lab (no API). SYNTHETIC corpus of 2,000 documents, 30 sentences each, chunk = 3 sentences, 30 days of change
(2 percent of documents edited a day, 30 percent of edits rewrite the whole document, 0.3 percent deleted, 0.3 percent added).
Counts chunks embedded per night under: full rebuild, document-hash replace, chunk-hash upsert. Then prices them at ASSUMED embedding prices."""
import random
from costlab.retrieval import make_corpus, edit_corpus, Index, reindex_cost, vector_footprint_gb
rnd = random.Random(7); corpus = make_corpus()
full = Index(); dh = Index(); ch = Index(); dh_noreconcile = Index()
base = full.embeddings_if_full_rebuild(corpus); dh.sync_doc_hash(corpus); ch.sync_chunk_hash(corpus); dh_noreconcile.sync_doc_hash(corpus, reconcile=False)
tot = {"full": 0, "doc_hash": 0, "chunk_hash": 0}; days = 30
for day in range(days):
    corpus = edit_corpus(corpus, rnd)
    tot["full"] += full.embeddings_if_full_rebuild(corpus)
    tot["doc_hash"] += dh.sync_doc_hash(corpus); tot["chunk_hash"] += ch.sync_chunk_hash(corpus); dh_noreconcile.sync_doc_hash(corpus, reconcile=False)
print(f"corpus: {len(corpus)} documents, {base} chunks at the start, {days} nightly runs")
for k, v in tot.items(): print(f"{k:11s} chunks embedded over {days} nights: {v:>9,}   per night {v/days:>9,.0f}   share of full {v/tot['full']:.4f}")
print(f"ghost documents left in the store after {days} nights without a deletion step: {len(dh_noreconcile.ghost_docs(corpus))} of {len(dh_noreconcile.docs)} (with reconciliation: {len(dh.ghost_docs(corpus))})")
print(f"chunk count: reconciled {dh.chunk_count():,}  unreconciled {dh_noreconcile.chunk_count():,}")
print("\nPriced at ASSUMED 120 tokens per chunk and embedding prices per million tokens (illustrative, three price points):")
for p in (0.02, 0.08, 0.13):
    print(f"  ${p:.2f}/M:  " + "  ".join(f"{k} ${v*120/1e6*p:,.4f}" for k, v in tot.items()))
print("\nScaled linearly to 500,000 documents with the same shape (assuming 10 chunks per document and 500 tokens per chunk, as in the sources' examples):")
sc = 500_000 / 2000
for k, v in tot.items():
    nights = v / (tot["full"] / days) ; print(f"  {k:11s} share of full {nights / days:.4f}")
print("\nVector footprint, ASSUMED 5M documents x 8 chunks, 1024 dimensions float32; and the same with 256 dimensions; and binary quantisation (1 bit per dimension):")
for nm, d, b in (("1024 dims float32", 1024, 4), ("256 dims float32", 256, 4), ("1024 dims binary", 1024, 1 / 8)):
    f = vector_footprint_gb(5_000_000, 8, d, b); print(f"  {nm:18s} raw {f['raw_gb']:8.1f} GB  index in memory {f['index_gb_low']:8.1f} to {f['index_gb_high']:8.1f} GB")
