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

On 16 November 2026 the suite ran 445 tests, all passing, with no API key set.

## Run the labs with your own key

costlab reads the key only from the `ANTHROPIC_API_KEY` environment variable. Nothing in the repository stores, prints or logs a key. Copy `.env.example` to `.env` (git ignores it) or export the variable in your shell:

```bash
export ANTHROPIC_API_KEY=your-key-here
python3 scripts/smoke_anthropic.py          # one tiny call to check the key works
python3 scripts/cache_experiment.py         # example: the Chapter 18 cache write-then-read lab
```

Scripts that call the API stop with `ANTHROPIC_API_KEY is not set` when the variable is missing. Most labs make tens to a few hundred short calls on Haiku-class models; check the docstring at the top of each script for the call count before you run it, and remember that you pay for those calls.

Rerunning a lab writes its output over the recorded file in `runs/`. Use `git diff runs/` to compare your results with the book's, and `git checkout runs/` to restore the originals.

## Real-API lab mode on xAI's Grok API (`xai-api`)

From 16 November 2026 new labs prefer real calls to xAI's Grok API over the keyless modes. `costlab/backends/xai.py` calls xAI's OpenAI-compatible Chat Completions endpoint (`https://api.x.ai/v1/chat/completions`) and records, for every call, what the response reports: prompt tokens, cached prompt tokens (`usage.prompt_tokens_details.cached_tokens`), completion tokens, reasoning tokens, xAI's own billed cost (`cost_in_usd_ticks`, 1 tick = 10^-10 USD) and wall-clock latency. It also prices the call itself at xAI's list prices (dated 16 November 2026, from https://docs.x.ai/docs/models and `GET /v1/models`); on the runs so far the two agree to the tick.

| Model | Input | Cached input | Output | Long-context rate (prompt of 200k tokens or more) |
|---|---:|---:|---:|---|
| `grok-4.20-0309-non-reasoning` (lab default) | $1.25 | $0.20 | $2.50 | $2.50 / $0.40 / $5.00 |
| `grok-4.3` | $1.25 | $0.20 | $2.50 | $2.50 / $0.40 / $5.00 |
| `grok-4.7` | $2.00 | $0.50 | $6.00 | $4.00 / $1.00 / $12.00 |

USD per million tokens. The `/v1/models` endpoint gives the same prices as integers in units of 10^-10 USD per token (12500 = $1.25 per million).

Outputs go to `runs/xai/` and start with a `mode: xai-api` line naming the model and the pricing date and source. A figure from this mode is a measurement on xAI's Grok API at xAI's prices. It is not a Claude measurement. Where an output has an "as-if Anthropic" column, that column re-prices the same xAI token counts at Anthropic list prices from `costlab/price_table.py` (cached tokens as cache reads). It is a comparison calculation only, because the tokenizer and model are different.

```bash
export XAI_API_KEY=your-xai-key-here
python3 scripts/xai_prompt_cache_lab.py      # 19 calls, $0.046 on the 16 November run, about 20 minutes because of the gaps
python3 scripts/xai_output_cap_lab.py         # 40 calls, about $0.039 on the 16 November run: four max_tokens caps on 10 open questions; only the 1,200 cap finished any reply
python3 scripts/xai_reasoning_lab.py         # 36 calls, about $0.036 on the 16 November run: direct answer, written working and hidden reasoning on 12 tasks
```

xAI caches matching prompt prefixes automatically. Setting the `x-grok-conv-id` header (the backend's `conv_id=` argument) sends calls to the same server, which makes a hit likelier but never certain. If the xAI call fails, labs fall back to the keyless modes below.

Before any commit, run `python3 scripts/secret_scan.py . --staged`. It looks for Anthropic and xAI keys, GitHub tokens and box-local paths.

## Keyless lab modes (no API credit needed)

From 16 November 2026 the Anthropic account behind the book had no API credit, so new labs run in one of two keyless modes. Every output they write starts with a `mode:` line and lives in its own folder, never mixed with the real-API recordings in `runs/`.

| Mode | Folder | What is measured | What is calculated |
|---|---|---|---|
| `local-model` | `runs/local-model/` | Token counts, latency and prefix-cache hits on a small open-weights model (Qwen2.5-1.5B-Instruct, GGUF Q4_K_M) served on CPU by llama.cpp's `llama-server` | Dollars, from Anthropic's published list prices in `costlab/price_table.py` |
| `simulated` | `runs/simulated/` | Nothing; no model is called | Dollars from the same price table and the token counts the lab states as assumptions |

`costlab/price_table.py` holds Anthropic's per-million-token prices (input, 5-minute and 1-hour cache writes, cache reads, output, the 50% batch discount and Haiku 5.5's long-prompt tier) with the date they were read and the source URL. `costlab/backends/local.py` talks to the local server and maps its numbers onto Anthropic's billing lines: tokens served from the local prefix cache are priced as cache reads, the uncached part of a declared prefix as a cache write, other prompt tokens as input and generated tokens as output. `costlab/backends/simulated.py` prices sessions under a 5-minute or 1-hour cache TTL with no model at all.

Read these outputs for what they are. A local-model figure is a measurement on a small open model with its own tokenizer, priced as if Anthropic had billed those tokens; a simulated figure is arithmetic. Neither is an Anthropic invoice measurement.

To run the local-model mode:

```bash
# download a llama.cpp release build (llama-*-bin-ubuntu-x64.tar.gz) and the model file
curl -L -o qwen2.5-1.5b-instruct-q4_k_m.gguf \
  https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF/resolve/main/qwen2.5-1.5b-instruct-q4_k_m.gguf
./llama-server -m qwen2.5-1.5b-instruct-q4_k_m.gguf --host 127.0.0.1 --port 8088 -t 4 -c 4096 --parallel 1
python3 scripts/local_prefix_cache_lab.py --priced-as claude-haiku-4-5
```

Set `COSTLAB_LOCAL_URL` if the server is elsewhere. The simulated mode needs nothing: `python3 scripts/sim_cache_gap_economics.py`. A bursty-traffic version (which cache lifetime wins when most gaps are short and some are long): `python3 scripts/sim_bursty_ttl_lab.py`.

## Recorded outputs

The files in `runs/` are the outputs printed in the book. The lab outputs were recorded from real Anthropic API calls made between 9 and 15 November 2026 (Asia/Calcutta time), mainly on `claude-haiku-4-5-20251001` and `claude-haiku-5-5`, with a few calls on `claude-sonnet-4-6`. Each file name carries its run date, and each script's docstring names the model it used. Simulation scripts (names ending in `_sim.py` and the `chNN_run_sims*.py` files) make no API calls; their outputs are deterministic and seeded.

Files in `runs/xai/` were recorded from real calls to xAI's Grok API on 16 November 2026 and priced at xAI's list prices; they are not Anthropic measurements. The first, `prompt-cache-gaps-2026-11-16.txt`, shows warm calls reusing 3,584 of about 3,695 prompt tokens at $0.00089 against $0.00450 for a cold call, one miss at a 30-second gap while a 10-minute gap still hit, and no reuse at all when the varying question comes before the shared text. The second, `thinking-three-ways-2026-11-16.txt`, runs 12 tasks three ways: the non-reasoning model answering directly (5 of 12 right, $0.0019), the same model writing short working (11 of 12, $0.0041) and the reasoning model (12 of 12, $0.0298, of which 9,877 output tokens were hidden reasoning billed at the output rate). The third, `output-caps-2026-11-16.txt`, sends 10 open questions with `max_tokens` of 60, 150, 400 and 1,200: caps up to 400 cut every reply (finish reason `length`, $0.0111 billed at the 400 cap for nothing finished), while at 1,200 all ten finished at a mean of 782 tokens and $0.0207.

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
| 17 | Routing and Cascades | `cascade.py`, `cascade_hard.py` | `billed_output_lab.py`, `xai_reasoning_lab.py`, `cascade_hard_lab.py`, `cascade_policies.py`, `ch48_run_sims2.py`, `confidence_cascade_lab.py` |
| 18 | Caching | `cachelab.py` | `cache_economics.py`, `cache_floor_repeats_lab.py`, `cache_health.py`, `cache_hierarchy_gap_lab.py`, `cache_hierarchy_lab.py`, `cache_hierarchy_sizes_lab.py`, `cache_layout_lab.py`, `cache_min_prefix_lab.py`, `cache_bigprefix_lab.py`, `ttl_bigprefix_lab.py`, `cache_pause_lab.py`, `cache_stagger_lab.py`, `cache_substagger_lab.py`, `cache_longreply_lab.py`, `cache_write_burst.py`, `history_cache_lab.py`, `semantic_cache_false_hits.py`, `xai_prompt_cache_lab.py` |
| 19 | Context Diet | `context.py`, `prices.py` | `compaction_cache_cost.py`, `compaction_lab.py`, `context_lab_summary.py`, `exchange_rate_toy.py`, `output_constraint_lab.py`, `prompt_diet_lab.py`, `tool_index_lab.py`, `tool_output_lab.py` |
| 20 | Batch, Async and Serving Modes | `serving.py` | `batch_scale_lab.py`, `batch_scale_summary.py`, `batch_summary.py`, `serving_economics.py` |
| 21 | Small Models, Fine-Tuning and Distillation | `smallmodels.py` | `small_model_lab.py`, `small_model_summary.py` |
| 22 | Retries, Loops and Waste | `retries.py` | `contamination_lab.py`, `contamination_summary.py`, `short_reply_lab.py`, `truncation_retry_lab.py`, `xai_output_cap_lab.py` |
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
