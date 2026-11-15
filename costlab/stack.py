"""Full cost of one answer: model, retrieval, judge sampling and human review.

Every input is a Fieldstone assumption (illustrative). The point of the function is the
structure: a human line sits in the same table as the token lines so its share is visible.
"""
from dataclasses import dataclass


@dataclass
class AnswerCostInputs:
    model_usd: float
    retrieval_context_usd: float   # tokens of retrieved chunks, billed on the model call
    query_embedding_usd: float
    vector_store_usd: float
    judge_sample_usd: float        # judge cost spread over every answer
    review_rate: float             # share of answers a person reviews
    review_minutes: float
    loaded_hourly_usd: float


def answer_cost(i: AnswerCostInputs) -> dict:
    review = i.review_rate * (i.review_minutes / 60.0) * i.loaded_hourly_usd
    lines = {
        "model": i.model_usd,
        "retrieval_context": i.retrieval_context_usd,
        "query_embedding": i.query_embedding_usd,
        "vector_store": i.vector_store_usd,
        "judge_sample": i.judge_sample_usd,
        "human_review": review,
    }
    total = sum(lines.values())
    return {"lines": lines, "total": total,
            "shares": {k: v / total for k, v in lines.items()}}
