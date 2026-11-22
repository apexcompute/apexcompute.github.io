#!/usr/bin/env python3
# Copyright (c) 2026 the course author. MIT License, see LICENSE in the materials package.
"""count_runs.py - count the frozen runs of E01 by the rules fixed before the first run. No model is called.

    python3 count_runs.py              # the runs in frozen/
    python3 count_runs.py examples/results   # your own runs (made with runner/run_example.py)

Rules:
  ex2 (5 runs): does the reply to round 1 contain a tool_use block?
  ex3 (1 run):  how many tool_use blocks are in each reply?
  ex4 (5 runs): does any reply contain 2 or more tool_use blocks?
                is any tool output longer than 200 characters (so code.py's print(output[:200]) cuts it)?
Only runs whose meta.json says exit 0 are counted.
"""
import glob, json, os, sys

ROOT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "frozen")

def runs(name):
    out = []
    for d in sorted(glob.glob(os.path.join(ROOT, name))):
        m = os.path.join(d, "meta.json")
        if os.path.exists(m) and json.load(open(m, encoding="utf-8"))["exit"] == 0:
            out.append((os.path.basename(d), [json.loads(l) for l in open(os.path.join(d, "trace.jsonl"), encoding="utf-8")]))
    return out

def n_tool_use(call):
    return sum(1 for b in call["response"]["content"] if b["type"] == "tool_use")

def tool_outputs(calls):
    seen = []
    for c in calls:
        for m in c["request"]["messages"]:
            if isinstance(m["content"], list):
                for b in m["content"]:
                    if b.get("type") == "tool_result" and b["content"] not in seen:
                        seen.append(b["content"])
    return seen

ex2 = runs("ex2_r*")
hits = [name for name, cs in ex2 if n_tool_use(cs[0]) > 0]
print(f"ex2: {len(hits)} of {len(ex2)} runs have a tool_use block in the round 1 reply")

for name, cs in runs("ex3"):
    print(f"ex3: tool_use blocks per reply = {[n_tool_use(c) for c in cs]}")

ex4 = runs("ex4_r*")
multi = sum(any(n_tool_use(c) >= 2 for c in cs) for _, cs in ex4)
cut = sum(any(len(o) > 200 for o in tool_outputs(cs)) for _, cs in ex4)
print(f"ex4: {multi} of {len(ex4)} runs have a reply with 2 or more tool_use blocks")
print(f"ex4: {cut} of {len(ex4)} runs have a tool output longer than 200 characters")
for name, cs in ex4:
    print(f"  {name}: tool_use per reply {[n_tool_use(c) for c in cs]}, "
          f"tool output lengths {[len(o) for o in tool_outputs(cs)]}")
