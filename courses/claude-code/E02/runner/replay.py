#!/usr/bin/env python3
# Copyright (c) 2026 the course author. MIT License, see LICENSE in the materials package.
"""replay.py - rebuild the verbose terminal of one run from trace.jsonl + terminal.log (no model is called).

    python3 replay.py ../E01/results/ex1            # print to the screen
    python3 replay.py ../E01/results/ex1 --write    # write verbose.log
    python3 replay.py ../E01/results/ex1 --check    # check that the rebuilt text equals terminal.log byte for byte

Every verbose block (MODEL / SYSTEM / TOOLS, "Round n: sent to the model", the reply) is generated again from
the request and reply saved in trace.jsonl with verbose_fmt; everything code.py printed itself (the $ commands,
their output, the final answer) is taken from terminal.log unchanged and stays where it was. If a block that
the trace says should be there cannot be found in terminal.log, the run is reported as inconsistent.
"""
import json, os, sys
sys.dont_write_bytecode = True   # no __pycache__ next to the runner (it would hold local paths)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import verbose_fmt as VF

d = sys.argv[1]
calls = [json.loads(l) for l in open(os.path.join(d, "trace.jsonl"), encoding="utf-8")]
model = json.load(open(os.path.join(d, "meta.json"), encoding="utf-8"))["model"]
live = open(os.path.join(d, "terminal.log"), encoding="utf-8").read()

out, pos = [], 0
for c in calls:
    head = (VF.banner(c["request"], model) + "\n" if c["call"] == 1 else "") + VF.before_call(c["call"], c["request"]) + "\n"
    tail = VF.after_call(c["response"], c["seconds"]) + "\n"
    for blk in (head, tail):
        i = live.find(blk, pos)
        if i < 0:
            sys.exit(f"replay: call {c['call']}: block not found in terminal.log; trace and terminal disagree")
        out.append(live[pos:i])      # what code.py printed in between, unchanged
        out.append(blk)              # regenerated from the trace
        pos = i + len(blk)
out.append(live[pos:])
text = "".join(out)

if "--check" in sys.argv:
    if text == live:
        print(f"replay: OK, {len(calls)} calls, rebuilt text equals terminal.log ({len(text.encode())} bytes)")
    else:
        sys.exit("replay: rebuilt text differs from terminal.log")
elif "--write" in sys.argv:
    open(os.path.join(d, "verbose.log"), "w", encoding="utf-8").write(text)
else:
    print(text, end="")
