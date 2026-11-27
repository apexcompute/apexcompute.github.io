#!/usr/bin/env python3
# Copyright (c) 2026 the course author. MIT License, see LICENSE in the materials package.
"""gate_check.py (E03) - run s03's first two permission gates on command strings, without a model and without
running any command.  The gate code is not retyped: the lines of s03_permission/code.py from "# Gate 1" to
check_rules (DENY_LIST, check_deny_list, DESTRUCTIVE_COMMAND_WORD, contains_destructive_command, PERMISSION_RULES,
check_rules) are read from the upstream file and executed as they are.

    python3 -B gate_check.py [path/to/learn-claude-code]   # default: ../learn-claude-code (clone it there)
Writes gate_check_out.json here (frozen/gate_check.json is the one used in the video): for each command, gate 1 (deny list) and gate 2 (rule match) as code.py decides.
Commands: every bash command the model wrote in this episode's runs (from frozen/*/trace.jsonl), plus three
commands written by us that delete the same file in other ways (marked "ours").
"""
import glob, json, os, re, sys
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
FORK = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "learn-claude-code")
src = open(os.path.join(FORK, "s03_permission", "code.py"), encoding="utf-8").read().splitlines()
a = next(i for i, l in enumerate(src) if l.startswith("# Gate 1"))
b = next(i for i, l in enumerate(src) if l.startswith("# Gate 3"))
ns = {"re": re, "WORKDIR": Path("/workspace")}
exec("\n".join(src[a:b]), ns)
OURS = ["find logs -name app1.log -delete",
        "python3 -c \"import os; os.remove('logs/app1.log')\"",
        "unlink logs/app1.log"]
rows, seen = [], set()
for d in sorted(glob.glob(os.path.join(HERE, "frozen", "*", "trace.jsonl"))):
    run = os.path.basename(os.path.dirname(d))
    for line in open(d, encoding="utf-8"):
        for blk in json.loads(line)["response"]["content"]:
            if blk["type"] == "tool_use" and blk["name"] == "bash":
                c = blk["input"]["command"]
                if c not in seen:
                    seen.add(c)
                    rows.append({"command": c, "who": "model", "first_seen": run})
rows += [{"command": c, "who": "ours", "first_seen": None} for c in OURS]
for r in rows:
    r["gate1_deny_list"] = ns["check_deny_list"](r["command"])
    r["gate2_rule"] = ns["check_rules"]("bash", {"command": r["command"]})
    r["regex_match"] = ns["contains_destructive_command"](r["command"])
out = {"code": "s03_permission/code.py lines %d-%d (executed as written)" % (a + 1, b), "rows": rows}
json.dump(out, open(os.path.join(HERE, "gate_check_out.json"), "w", encoding="utf-8"), indent=1)
for r in rows:
    print(f"{r['who']:5s} gate1={str(r['gate1_deny_list'] is not None):5s} gate2={str(r['gate2_rule'] is not None):5s}  {r['command']}")
