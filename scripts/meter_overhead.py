#!/usr/bin/env python3
"""Chapter 5: what the in-process Meter wrapper adds per call, measured on this box.

No network and no API: a fake client returns instantly, so every microsecond measured is the
wrapper's own work (price estimate, record build, one JSON line appended to a file). This is NOT
a gateway benchmark and says nothing about a network proxy's overhead.
"""
import statistics, tempfile, time
from pathlib import Path
from types import SimpleNamespace
from costlab.gateway import Meter

class M:
    def create(self, **kw):
        u = SimpleNamespace(input_tokens=800, output_tokens=200, cache_read_input_tokens=0, cache_creation_input_tokens=0)
        return SimpleNamespace(usage=u, model=kw["model"], stop_reason="end_turn", content=[])

client = SimpleNamespace(messages=M())
with tempfile.TemporaryDirectory() as d:
    m = Meter(client, Path(d) / "m.jsonl", product="support-agent")
    times = []
    for i in range(5000):
        t = time.perf_counter()
        m.call(model="claude-haiku-4-5-20251001", session_id="s", step=i, feature="chat", max_tokens=10)
        times.append((time.perf_counter() - t) * 1e6)
times.sort()
print(f"calls 5000  median {statistics.median(times):.0f} us  p95 {times[int(.95*5000)]:.0f} us  p99 {times[int(.99*5000)]:.0f} us  max {times[-1]:.0f} us")
