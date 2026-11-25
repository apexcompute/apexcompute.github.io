#!/usr/bin/env python3
# Copyright (c) 2026 the course author. MIT License, see LICENSE in the materials package.
"""count_runs.py - count the frozen runs of E02 by the rules fixed before the first run. No model is called.

    python3 count_runs.py                    # the runs in frozen/
    python3 count_runs.py examples/results   # your own runs (made with runner/run_example.py)

Rules:
  ex2 (5 runs): which tool does the first tool call use? Is notes/todo.txt changed (a line "Buy soy milk",
                no line that is exactly "Buy milk")?
  ex3 (5 runs): which tools does the whole run use? only_bash / mixed / only_dedicated / no_tool.
                Does summary.md hold the first line of all three notes?
Only runs whose meta.json says exit 0 are counted. The workspace checks need workspace_after/ (frozen/ has it).
"""
import glob, json, os, sys

ROOT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "frozen")
FIRST = ["Learned while loops today.", "Mon: finish chapter three", "Buy milk"]

def runs(name):
    out = []
    for d in sorted(glob.glob(os.path.join(ROOT, name))):
        m = os.path.join(d, "meta.json")
        if os.path.exists(m) and json.load(open(m, encoding="utf-8"))["exit"] == 0:
            out.append((d, [json.loads(l) for l in open(os.path.join(d, "trace.jsonl"), encoding="utf-8")]))
    return out

def tools(calls):
    return [b["name"] for c in calls for b in c["response"]["content"] if b["type"] == "tool_use"]

def read(d, *p):
    f = os.path.join(d, "workspace_after", *p)
    return open(f, encoding="utf-8").read() if os.path.exists(f) else None

r2 = runs("ex2_r*")
first = [tools(c[:1])[0] if tools(c[:1]) else None for _, c in r2]
done2 = [(t := read(d, "notes", "todo.txt")) is not None and "Buy soy milk" in t.splitlines()
         and "Buy milk" not in t.splitlines() for d, _ in r2]
print(f"ex2: first tool = {first}; edit_file in {first.count('edit_file')} of {len(r2)} runs; "
      f"todo.txt changed in {sum(done2)} of {len(r2)}")
r3 = runs("ex3_r*")
cats = []
for d, c in r3:
    t = tools(c)
    cats.append("no_tool" if not t else "only_bash" if set(t) == {"bash"} else "only_dedicated" if "bash" not in t else "mixed")
    s = read(d, "summary.md")
    print(f"  {os.path.basename(d)}: tools {t}, {len(c)} calls, summary.md ok: {s is not None and all(x in s for x in FIRST)}")
print(f"ex3: only bash in {cats.count('only_bash')} of {len(r3)} runs; mixed in {cats.count('mixed')}")
