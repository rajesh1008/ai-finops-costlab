# costlab: code for *AI FinOps*

costlab is the working code that accompanies the book **AI FinOps: Controlling LLM, Token and Agent Costs in Production** by Rajesh Ranjan Mahapatra. It is a small cost ledger built from scratch in Python: a gateway Meter that records every model call, structured cost records that keep measured, estimated and billed figures apart, an attribution hierarchy, cost per outcome, budgets and kill switches, caching and routing experiments, and the labs that produced the numbers printed in the book.

Every example follows Fieldstone Analytics, the book's running case. Fieldstone is a fictional company. Its invoices, customers and amounts are synthetic and illustrative, not market benchmarks.

## Requirements

- Python 3.12 or later (tested on 3.13)
- An Anthropic API key, only if you want to rerun the labs that make real calls. The test suite needs no key and makes no network calls.

## Install

```bash
git clone https://github.com/rajesh1008/ai-finops-costlab.git
cd ai-finops-costlab
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
python3 -m pip install -e ".[dev]"
```

The `dev` extra installs pytest plus numpy, scipy, DuckDB and pandas, which some scripts and tests use. If you only want to run the labs, `pip install -e ".[labs]"` is enough.

## Run the tests

```bash
python3 -m pytest
```

On 15 November 2026 the suite ran 399 tests, all passing, with no API key set.

## Run the labs with your own key

costlab reads the key only from the `ANTHROPIC_API_KEY` environment variable. Nothing in the repository stores, prints or logs a key. Copy `.env.example` to `.env` (git ignores it) or export the variable in your shell:

```bash
export ANTHROPIC_API_KEY=your-key-here
python3 scripts/smoke_anthropic.py          # one tiny call to check the key works
python3 scripts/cache_experiment.py         # example: the Chapter 18 cache write-then-read lab
```

Scripts that call the API stop with `ANTHROPIC_API_KEY is not set` when the variable is missing. Most labs make tens to a few hundred short calls on Haiku-class models; check the docstring at the top of each script for the call count before you run it, and remember that you pay for those calls.

Rerunning a lab writes its output over the recorded file in `runs/`. Use `git diff runs/` to compare your results with the book's, and `git checkout runs/` to restore the originals.

## Recorded outputs

The files in `runs/` are the outputs printed in the book. The lab outputs were recorded from real Anthropic API calls made between 9 and 15 November 2026 (Asia/Calcutta time), mainly on `claude-haiku-4-5-20251001` and `claude-haiku-5-5`, with a few calls on `claude-sonnet-4-6`. Each file name carries its run date, and each script's docstring names the model it used. Simulation scripts (names ending in `_sim.py` and the `chNN_run_sims*.py` files) make no API calls; their outputs are deterministic and seeded.

Two files, `runs/api-blocked-2026-11-10.txt` and `runs/api-blocked-2026-11-11.txt`, record the periods when the account had no API credit. Labs that could not run were left unrun; no output was invented to fill the gap.

Prices in `costlab/prices.py` are dated placeholders taken from vendor pages on the dates shown in that file. Check current vendor pricing before you reuse any cost figure.

## Layout

| Path | What is there |
|---|---|
| `costlab/` | The package: Meter, cost records, prices, attribution, budgets, caching, routing and the other building blocks (63 files) |
| `scripts/` | One script per lab or simulation; most docstrings name the chapter, the model and the number of calls |
| `tests/` | pytest suite, mostly named by chapter (`test_ch18.py` and so on) |
| `runs/` | Recorded outputs from the real-call labs and simulations |
| `fixtures/` | Synthetic Fieldstone invoices used by the early chapters |

## Chapter map

The table lists the package modules and scripts each chapter refers to. Tests follow the chapter number in their file name. Script names that start with a chapter number (for example `ch45_run_sims.py`) are named after the run that produced them, so they can serve several chapters.

| Ch | Chapter | Package modules (`costlab/`) | Scripts (`scripts/`) |
|---:|---|---|---|
| 1 | A Hundred and Eighty Thousand Dollars Nobody Can Explain | `gateway.py`, `prices.py` | `ch45_run_sims.py` |
| 2 | The Anatomy of an AI Bill | `prices.py` | `billed_output_lab.py`, `cache_experiment.py`, `ch48_run_sims3.py`, `cost_stack.py`, `reasoning_tokens.py`, `reasoning_trials.py`, `tier_boundary.py`, `tool_floor_lab.py` |
| 3 | Measuring Fieldstone Before Changing Anything | shared modules only | `ch45_run_sims.py`, `outcome_table.py`, `ownership_queue.py`, `retention_gap.py`, `spend_to_revenue.py` |
| 4 | Value Before Cost | `outcome.py` | `ch48_run_sims.py`, `outcome_denominators.py` |
| 5 | The Gateway as the Meter | shared modules only | `gateway_reconcile.py`, `tags_demo.py` |
| 6 | Tagging, Hierarchies and Attribution | `hierarchy.py` | `ch45_run_sims.py`, `hierarchy_rename.py` |
| 7 | Sessions, Agents and the Cost of a Conversation | `runs_graph.py`, `waste.py` | `ch35_run_sims.py`, `ch44_run_sims.py`, `context_growth.py`, `fieldstone_session_table.py`, `fold_rules_lab.py`, `fold_summary_lab.py`, `loop_injection.py`, `null_session.py`, `retry_waste.py`, `self_predict_lab.py`, `session_percentiles_demo.py` |
| 8 | Structured Cost Records | `focus.py`, `stopreason.py` | `ch44_run_sims.py` |
| 9 | Cost Observability | `stopreason.py`, `views.py` | `histogram_percentile_sim.py`, `otel_mapping.py`, `three_views.py`, `cache_write_burst.py` |
| 10 | Anomaly Detection, Alerts and Runaway-Cost Response | shared modules only | `alert_threshold_sim.py`, `anomaly_detectors.py`, `ch46_run_sims.py` |
| 11 | Cost per Outcome | `prices.py` | `cpo_bootstrap_sim.py`, `cpo_repeats_lab.py`, `cpst_ledger.py` |
| 12 | Margin, Pricing and the Product That Loses Money on Every User | shared modules only | `billed_output_lab.py`, `ch45_run_sims.py`, `ch48_run_sims3.py`, `margin_by_customer.py`, `margin_runaway_sim.py` |
| 13 | Forecasting AI Spend | shared modules only | `ch42_run_sims.py`, `forecast_backtest.py`, `repeat_spread_lab.py`, `repeat_spread_summary.py`, `variance_decomp.py` |
| 14 | Benchmarking Spend | shared modules only | `peer_rank_sim.py`, `price_decay_migration.py` |
| 15 | Pricing Agents | shared modules only | `ch44_run_sims.py`, `pricing_outcomes.py` |
| 16 | The Autonomy Decision as a Cost Decision | shared modules only | `ch44_run_sims.py`, `rule_first_lab.py`, `rule_first_summary.py`, `triage_breakeven.py`, `triage_rules_vs_llm.py` |
| 17 | Routing and Cascades | `cascade.py`, `cascade_hard.py` | `billed_output_lab.py`, `cascade_hard_lab.py`, `cascade_policies.py`, `ch48_run_sims2.py`, `confidence_cascade_lab.py` |
| 18 | Caching | `cachelab.py` | `cache_economics.py`, `cache_floor_repeats_lab.py`, `cache_health.py`, `cache_hierarchy_gap_lab.py`, `cache_hierarchy_lab.py`, `cache_hierarchy_sizes_lab.py`, `cache_layout_lab.py`, `cache_min_prefix_lab.py`, `cache_bigprefix_lab.py`, `cache_pause_lab.py`, `cache_stagger_lab.py`, `cache_substagger_lab.py`, `cache_longreply_lab.py`, `cache_write_burst.py`, `history_cache_lab.py`, `semantic_cache_false_hits.py` |
| 19 | Context Diet | `context.py`, `prices.py` | `compaction_cache_cost.py`, `compaction_lab.py`, `context_lab_summary.py`, `exchange_rate_toy.py`, `output_constraint_lab.py`, `prompt_diet_lab.py`, `tool_index_lab.py`, `tool_output_lab.py` |
| 20 | Batch, Async and Serving Modes | `serving.py` | `batch_scale_lab.py`, `batch_scale_summary.py`, `batch_summary.py`, `serving_economics.py` |
| 21 | Small Models, Fine-Tuning and Distillation | `smallmodels.py` | `small_model_lab.py`, `small_model_summary.py` |
| 22 | Retries, Loops and Waste | `retries.py` | `contamination_lab.py`, `contamination_summary.py`, `short_reply_lab.py`, `truncation_retry_lab.py` |
| 23 | The Retrieval Bill | `retrieval.py` | `reindex_lab.py`, `retrieval_k_summary.py`, `selector_answerer_lab.py` |
| 24 | What an Agent Run Costs and Why It Is Not a Call | `prices.py` | `agent_run_summary.py`, `run_forecast_replay.py` |
| 25 | Multi-Agent Cost | shared modules only | `cache_race_lab.py`, `ch36_run_sims.py`, `ch44_run_sims.py`, `ch48_run_sims.py`, `fanout_lab.py`, `multi_agent_lab.py`, `multi_agent_summary.py` |
| 26 | Budgets, Quotas and Kill Switches for Agents | `budgets.py` | `budget_policy_lab.py`, `budget_policy_summary.py`, `ch36_run_sims.py`, `maxtokens_lab.py`, `maxtokens_probe.py` |
| 27 | The Degradation Ladder | shared modules only | `ch43_run_sims.py`, `output_cap_lab.py` |
| 28 | Shadow Mode Economics | shared modules only | `ch44_run_sims.py` |
| 29 | The Cost of Knowing | shared modules only | `judge_cost_lab.py`, `output_variance_lab.py` |
| 30 | Vendor Contracts, Commitments and the Price Cut You Did Not Get | shared modules only | `ch35_run_sims.py`, `commit_lab.py`, `contract_structures.py`, `tokenizer_lab.py` |
| 31 | Multi-Vendor, Multi-Cloud and the Cost of Optionality | shared modules only | `ch35_run_sims.py`, `ch43_run_sims.py`, `optionality_lab.py`, `portability_lab.py`, `portability_summary.py` |
| 32 | Cost Policy as Code | `policy.py` | `policy_lab.py` |
| 33 | Customer-Facing Caps, Fair Use and the Power User Who Was Not Abusing Anything | shared modules only | `ch36_run_sims.py`, `ch44_run_sims.py`, `fair_use_lab.py` |
| 34 | The Cost Evidence Pack | `evidence.py`, `focus.py`, `prices.py` | `evidence_focus_check.py`, `evidence_pack_lab.py` |
| 35 | Cost, Risk and the Model Change That Saved Money and Broke the Product | `modelchange.py` | `ch44_run_sims.py`, `model_change_followup.py`, `model_change_summary.py` |
| 36 | Showback, Chargeback and the Incentives They Create | shared modules only | `ch36_run_sims.py`, `showback_summary.py` |
| 37 | Who Does AI FinOps | `review.py` | `review_lab.py` |
| 38 | FinOps Tooling | `explainer.py` | `explainer_lab.py`, `explainer_summary.py`, `tooling_lab.py` |
| 39 | Cost-Aware Engineering Without Fear | shared modules only | `pr_estimate_lab.py`, `pr_estimate_summary.py` |
| 40 | The Board Pack | `boardpack.py` | `ch36_run_sims.py` |
| 41 | The AI FinOps Maturity Model and Where You Are | shared modules only | `maturity_lab_g2.py` |
| 42 | Quarter One | `firstmeter.py`, `firstmeter_hard.py` | `bypass_injection.py`, `firstmeter_hard_lab.py`, `firstmeter_summary.py` |
| 43 | Quarter Two | shared modules only | `ch44_run_sims.py`, `eval_subset_sim.py` |
| 44 | Quarter Three | `segments.py` | `killswitch_lab.py`, `killswitch_pages_lab.py`, `loop_growth_lab.py` |
| 45 | Quarter Four | shared modules only | `forecast_variance_lab.py`, `interval_coverage_sim.py` |
| 46 | Thirty Anti-Patterns in AI FinOps, and the Control That Stops Each | `antipatterns_extra.py` | `antipattern_baseline.py`, `antipattern_extra_lab.py`, `antipattern_lab.py`, `ch48_run_sims.py` |
| 47 | The AI FinOps Interview, From Both Sides | shared modules only | `ch44_run_sims.py`, `interview_baseline.py`, `interview_grade_lab.py`, `interview_plausible_h55gen_lab.py`, `interview_plausible_h55match_lab.py`, `interview_plausible_lab.py`, `interview_plausible_summary.py` |
| 48 | What Will Change and What Will Not | `canary.py`, `claims.py`, `prices.py` | `canary_edge_lab.py`, `canary_lab.py` |

## Licence

MIT. See `LICENSE`. Copyright (c) 2026 Rajesh Ranjan Mahapatra.
