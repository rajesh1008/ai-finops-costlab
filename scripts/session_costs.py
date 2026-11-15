#!/usr/bin/env python3
"""Join Meter records into sessions with DuckDB and print cost per session, sorted by cost."""
import sys
from pathlib import Path
import duckdb

log = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1] / "runs" / "meter-2026-11-10.jsonl"
con = duckdb.connect()
con.execute(f"""
create view calls as
select json_extract_string(notes, '$.session_id') as session_id,
       cast(json_extract_string(notes, '$.step') as int) as step,
       cast(json_extract_string(notes, '$.latency_ms') as int) as latency_ms,
       input_tokens, output_tokens, cache_read_tokens, cache_write_tokens, estimated_cost_usd
from read_json_auto('{log}', format='newline_delimited')
""")
print(con.execute("""
select session_id, count(*) as calls, sum(input_tokens) as input_tok, sum(output_tokens) as output_tok,
       round(sum(estimated_cost_usd), 5) as est_usd
from calls group by session_id order by est_usd desc
""").df().to_string(index=False))
print()
print(con.execute("""
select count(distinct session_id) as sessions, count(*) as calls,
       round(sum(estimated_cost_usd), 5) as total_usd,
       round(sum(estimated_cost_usd)/count(distinct session_id), 5) as mean_per_session
from calls
""").df().to_string(index=False))
