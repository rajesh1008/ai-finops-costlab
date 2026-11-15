#!/usr/bin/env python3
"""Chapter 2 lab: the knowledge assistant's cost per answer with the human line included.

No API calls. All inputs are Fieldstone assumptions, printed so the reader can change them.
Rates for the token lines use the dated Haiku 4.5 placeholders in costlab/prices.py.
"""
from costlab.stack import AnswerCostInputs, answer_cost

IN, OUT = 1.00 / 1e6, 5.00 / 1e6          # placeholder USD per token
generation = 2_600 * IN + 350 * OUT       # 600 prompt + 2,000 retrieved + question; 350 out
retrieval_part = 2_000 * IN               # the share of those input tokens that came from retrieval
model_part = generation - retrieval_part
judge = (1_500 * IN + 150 * OUT) * 0.10   # a judge reads 10 percent of answers

inp = AnswerCostInputs(
    model_usd=model_part, retrieval_context_usd=retrieval_part,
    query_embedding_usd=40 * 0.02 / 1e6,   # 40-token query at an assumed $0.02 per million
    vector_store_usd=0.0008, judge_sample_usd=judge,
    review_rate=0.08, review_minutes=3.0, loaded_hourly_usd=60.0)
r = answer_cost(inp)
for k, v in r["lines"].items():
    print(f"{k:18s} ${v:.6f}  {r['shares'][k]*100:5.1f}%")
print(f"{'total':18s} ${r['total']:.6f}")
tokens_only = sum(v for k, v in r["lines"].items() if k != "human_review")
print(f"token-and-store lines only: ${tokens_only:.6f}  ({tokens_only / r['total'] * 100:.1f}% of total)")
