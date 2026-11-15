"""Chapter 23: the retrieval bill. Footprint and re-index arithmetic, a pure-python BM25, and a content-hash incremental indexer.
Sizes and price inputs are ASSUMED unless a source is cited in the chapter. Synthetic corpus only."""
import math, re, hashlib, random
from collections import Counter

def vector_footprint_gb(docs, chunks_per_doc, dims, bytes_per_number=4, hnsw_overhead=(1.5, 3.0)):
    """Raw vector bytes, and the in-memory index range if the HNSW graph adds the stated multiple (Kognita: often 1.5 to 3x)."""
    n = docs * chunks_per_doc; raw = n * dims * bytes_per_number / 1e9
    return {"vectors": n, "raw_gb": raw, "index_gb_low": raw * hnsw_overhead[0], "index_gb_high": raw * hnsw_overhead[1]}

def reindex_cost(docs, chunks_per_doc, tokens_per_chunk, usd_per_mtok):
    return docs * chunks_per_doc * tokens_per_chunk / 1e6 * usd_per_mtok

def context_cost_per_query(k, chunk_tokens, usd_per_mtok_in, fixed_tokens=0):
    return (k * chunk_tokens + fixed_tokens) / 1e6 * usd_per_mtok_in

def chunk_text(text, size=3):
    """Chunk = `size` consecutive sentences. Deliberately simple."""
    s = [x.strip() for x in re.split(r"(?<=[.!?])\s+", text) if x.strip()]
    return [" ".join(s[i:i + size]) for i in range(0, len(s), size)]

def h(x): return hashlib.sha256(x.encode()).hexdigest()

class Index:
    """Toy vector store: maps chunk id -> chunk hash. 'Embedding' is counted, not computed."""
    def __init__(self): self.docs = {}      # doc_id -> {"dochash":..., "chunks": [chunkhash]}
    def embeddings_if_full_rebuild(self, corpus): return sum(len(chunk_text(t)) for t in corpus.values())
    def sync_doc_hash(self, corpus, reconcile=True):
        """Replace mode: re-chunk and re-embed any doc whose hash changed. Returns chunks embedded."""
        n = 0
        for d, t in corpus.items():
            dh = h(t)
            if d in self.docs and self.docs[d]["dochash"] == dh: continue
            ch = [h(c) for c in chunk_text(t)]; self.docs[d] = {"dochash": dh, "chunks": ch}; n += len(ch)
        if reconcile:
            for d in [d for d in self.docs if d not in corpus]: del self.docs[d]
        return n
    def sync_chunk_hash(self, corpus, reconcile=True):
        """Upsert mode: embed only chunks whose hash is new for that doc."""
        n = 0
        for d, t in corpus.items():
            ch = [h(c) for c in chunk_text(t)]; old = set(self.docs.get(d, {}).get("chunks", []))
            n += sum(1 for c in ch if c not in old); self.docs[d] = {"dochash": h(t), "chunks": ch}
        if reconcile:
            for d in [d for d in self.docs if d not in corpus]: del self.docs[d]
        return n
    def ghost_docs(self, corpus): return [d for d in self.docs if d not in corpus]
    def chunk_count(self): return sum(len(v["chunks"]) for v in self.docs.values())

def make_corpus(n_docs=2000, seed=23, sentences=30):
    rnd = random.Random(seed); topics = ["export", "retention", "billing", "login", "seats", "invoice", "plan", "audit", "backup", "sso"]
    corpus = {}
    for i in range(n_docs):
        corpus[f"doc{i}"] = " ".join(f"Section {j} of document {i} covers {rnd.choice(topics)} rule {rnd.randint(100, 999)} for tier {rnd.randint(1, 7)}." for j in range(sentences))
    return corpus

def edit_corpus(corpus, rnd, churn=0.02, whole_share=0.3, delete=0.003, add=0.003):
    """One day of change. Most edits touch one sentence; whole_share of edits rewrite the document; some docs are deleted or added."""
    c = dict(corpus); ids = list(c)
    for d in rnd.sample(ids, int(len(ids) * churn)):
        s = c[d].split(". ") if False else re.split(r"(?<=\.)\s+", c[d])
        if rnd.random() < whole_share: s = [x + f" Rev{rnd.randint(1, 9999)}." for x in s]
        else: k = rnd.randrange(len(s)); s[k] = s[k] + f" Updated {rnd.randint(1, 9999)}."
        c[d] = " ".join(s)
    for d in rnd.sample(ids, int(len(ids) * delete)): c.pop(d, None)
    for i in range(int(len(ids) * add)): c[f"new{rnd.randint(0, 10**9)}"] = " ".join(f"New section {j} rule {rnd.randint(100, 999)}." for j in range(30))
    return c

# --- BM25 -------------------------------------------------------------------------------------------------
def toks(t): return re.findall(r"[a-z0-9]+", t.lower())
class BM25:
    def __init__(self, docs, k1=1.5, b=0.75):
        self.docs = docs; self.tf = [Counter(toks(d)) for d in docs]; self.len = [sum(c.values()) for c in self.tf]
        self.avg = sum(self.len) / len(docs); self.k1, self.b = k1, b; df = Counter()
        for c in self.tf: df.update(c.keys())
        self.idf = {w: math.log(1 + (len(docs) - n + 0.5) / (n + 0.5)) for w, n in df.items()}
    def search(self, q, k):
        qs = toks(q); sc = []
        for i, c in enumerate(self.tf):
            s = 0.0
            for w in qs:
                f = c.get(w, 0)
                if f: s += self.idf[w] * f * (self.k1 + 1) / (f + self.k1 * (1 - self.b + self.b * self.len[i] / self.avg))
            sc.append((s, i))
        sc.sort(key=lambda x: (-x[0], x[1])); return [i for s, i in sc[:k]]
