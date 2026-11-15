#!/usr/bin/env python3
"""Chapter 47 offline baseline (no model, no API): how often do four surface heuristics prefer the strong answer over the weak one, over every Q/strong/weak triple in the manuscript?
Also the truncated condition (strong cut to its first sentence)."""
import statistics as st
from pathlib import Path
from costlab.interviewgrade import extract, first_sentence, words, HEUR
T = extract(str(Path(__file__).resolve().parents[3] / "02-manuscript" / "ch*.md"))
print("triples", len(T), "from chapters", sorted({t["file"] for t in T})[:3], "...", sorted({t["file"] for t in T})[-1])
ws = [len(words(t["strong"])) for t in T]; ww = [len(words(t["weak"])) for t in T]
print(f"median words: strong {st.median(ws)}, weak {st.median(ww)}; strong longer in {sum(a > b for a, b in zip(ws, ww))} of {len(T)}")
for name, h in HEUR.items():
    full = sum(h(t["strong"], t["weak"], t["q"]) for t in T); tr = sum(h(first_sentence(t["strong"]), t["weak"], t["q"]) for t in T)
    print(f"{name:22} full {full}/{len(T)} ({full / len(T):.0%})   first sentence only {tr}/{len(T)} ({tr / len(T):.0%})")
