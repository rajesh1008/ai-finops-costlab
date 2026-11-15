import json
from pathlib import Path
from costlab.invoice import parse_mixed_model_line, summarise
from costlab.records import InvoiceLine
from costlab.taxonomy import classify_line


FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "fieldstone_invoices.json"


def test_classify_reasoning_tokens():
    assert classify_line("reasoning tokens billed as output", "output_tokens") == "reasoning_tokens"


def test_mixed_model_line_splits_two_models():
    models = parse_mixed_model_line("gpt-4o and gpt-4o-mini")
    assert "gpt-4o" in models
    assert "gpt-4o-mini" in models


def test_fieldstone_baseline_unattributed():
    data = json.loads(FIXTURE.read_text())
    lines = [InvoiceLine(**row) for row in data["lines"]]
    summary = summarise(lines)
    assert summary["total_usd"] == 180000.0
    assert summary["attribution_coverage"] < 0.5


def test_mixed_line_is_not_classified_as_output_tokens():
    # v0.1 filed the 43,400 dollar mixed OpenAI line under output_tokens because the word matched first.
    assert classify_line("input and output mixed gpt-4o and gpt-4o-mini", "mixed") == "mixed_unsplit"


def test_embeddings_not_filed_as_input_tokens():
    assert classify_line("embeddings", "input_tokens") == "embeddings"


def test_gpu_endpoint_hours_are_hosted_capacity():
    assert classify_line("GPU inference endpoint hours", "hours") == "hosted_capacity"
