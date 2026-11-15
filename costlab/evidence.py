"""Chapter 34: an evidence pack as code. A ledger of cost records with a hash chain, a recomputation of cost from tokens and a dated price table, a reconciliation to invoice lines by (model, day),
attribution coverage, a manifest with file digests, and an attribute-sampling calculator. Usage in the lab is REAL (token counts from recorded runs); tags, days and the invoice are SYNTHETIC.
No network, no clock: every date is passed in."""
import hashlib, json, math, random
from .prices import PLACEHOLDER_USD_PER_MTIOK

def sha(b):
    return hashlib.sha256(b if isinstance(b, bytes) else b.encode()).hexdigest()

def canon(rec):
    return json.dumps(rec, sort_keys=True, separators=(",", ":"))

def chain(records):
    """Return records with `prev` and `h` added. h = sha256(prev + canonical body). Head hash goes into the manifest."""
    out, prev = [], "0" * 64
    for r in records:
        body = {k: v for k, v in r.items() if k not in ("prev", "h")}
        h = sha(prev + canon(body)); out.append({**body, "prev": prev, "h": h}); prev = h
    return out, prev

def verify_chain(records, head=None):
    """Return (ok, first_bad_index, reason). With a head hash from the manifest, a truncated tail is also caught."""
    prev = "0" * 64
    for i, r in enumerate(records):
        body = {k: v for k, v in r.items() if k not in ("prev", "h")}
        if r["prev"] != prev: return False, i, "prev link broken"
        if sha(prev + canon(body)) != r["h"]: return False, i, "record changed"
        prev = r["h"]
    if head is not None and prev != head: return False, len(records), "head differs from manifest (tail removed or added)"
    return True, None, "ok"

def price_usd(model, inp, out, table=PLACEHOLDER_USD_PER_MTIOK, version=None):
    t = table.get("anthropic:" + model)
    if t is None: return None
    return inp / 1e6 * t["input"] + out / 1e6 * t["output"]

def recompute(records, table=PLACEHOLDER_USD_PER_MTIOK):
    """Cost per record from tokens and the price table. A record whose model has no price row gets None and is reported, not zero."""
    return [price_usd(r["model"], r["in"], r["out"], table) for r in records]

def coverage(records, keys=("team", "feature", "env")):
    """Share of recomputed spend whose record carries every key, plus the untagged dollars by missing key."""
    costs = recompute(records); tot = sum(c for c in costs if c is not None); ok = 0.0; miss = {k: 0.0 for k in keys}
    for r, c in zip(records, costs):
        if c is None: continue
        bad = [k for k in keys if not r.get(k)]
        if not bad: ok += c
        for k in bad: miss[k] += c
    return {"total_usd": tot, "attributed_usd": ok, "coverage": ok / tot if tot else 0.0, "missing_by_key_usd": miss}

def meter_lines(records, table=PLACEHOLDER_USD_PER_MTIOK, scale=1.0):
    """Group recomputed cost by (model, day). scale: each recorded call stands for this many calls (ASSUMED, linear)."""
    d = {}
    for r, c in zip(records, recompute(records, table)):
        if c is None: continue
        d[(r["model"], r["day"])] = d.get((r["model"], r["day"]), 0.0) + c * scale
    return d

def make_invoice(records, seed=0, dup_n=0, early_price_day=None, early_price_factor=1.0, credit_usd=0.0, table=PLACEHOLDER_USD_PER_MTIOK, scale=1.0):
    """A SYNTHETIC vendor invoice built from the same usage with planted defects, one line per (model, day), amounts rounded to cents per line.
    dup_n: that many records are billed twice (a retry billed as two calls). early_price_day: from that day the input rate is multiplied by early_price_factor (a price change effective earlier than announced).
    credit_usd: a negative line, a goodwill credit. scale: each recorded call stands for this many calls (ASSUMED, linear); the invoice rounds each line to cents after scaling."""
    rnd = random.Random(seed); lines = {}
    def add(r, mult=1.0):
        t = table["anthropic:" + r["model"]]; fin = t["input"] * (early_price_factor if (early_price_day is not None and r["day"] >= early_price_day) else 1.0)
        c = (r["in"] / 1e6 * fin + r["out"] / 1e6 * t["output"]) * mult * scale
        lines[(r["model"], r["day"])] = lines.get((r["model"], r["day"]), 0.0) + c
    for r in records: add(r)
    for r in rnd.sample(records, dup_n): add(r)
    inv = {k: round(v, 2) for k, v in lines.items()}
    if credit_usd: inv[("credit", 0)] = -round(credit_usd, 2)
    return inv

def reconcile_lines(meter, invoice, tolerance=0.02):
    """Per key (model, day): meter, invoice, gap, whether inside tolerance of the invoice line (cent-rounding floor of one cent). Keys only on one side are listed."""
    out = []
    for k in sorted(set(meter) | set(invoice), key=lambda x: (str(x[0]), x[1])):
        m, i = meter.get(k, 0.0), invoice.get(k, 0.0); gap = i - m
        ok = abs(gap) <= max(0.01, tolerance * abs(i)) if i else abs(gap) <= 0.01
        out.append({"key": k, "meter": m, "invoice": i, "gap": gap, "ok": ok})
    return out

def zero_failure_sample(p_max, confidence=0.95):
    """Smallest n such that, if the true error rate were at least p_max, seeing zero errors in n draws has probability at most 1 - confidence."""
    return math.ceil(math.log(1 - confidence) / math.log(1 - p_max))

def detect_prob(p_true, n):
    return 1 - (1 - p_true) ** n

def manifest(files, head_hash, as_of, price_table_name, notes):
    """files: dict name -> bytes. Returns a manifest dict with sha256 per file and the chain head."""
    return {"as_of": as_of, "price_table": price_table_name, "chain_head": head_hash,
            "files": {n: {"sha256": sha(b), "bytes": len(b)} for n, b in sorted(files.items())}, "notes": notes}

def verify_manifest(man, files):
    bad = []
    for n, meta in man["files"].items():
        if n not in files: bad.append((n, "missing"))
        elif sha(files[n]) != meta["sha256"]: bad.append((n, "changed"))
    return bad
