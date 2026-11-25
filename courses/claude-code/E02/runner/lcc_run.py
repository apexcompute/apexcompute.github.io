#!/usr/bin/env python3
# Copyright (c) 2026 the course author. MIT License, see LICENSE in the materials package.
"""lcc_run.py - run one chapter's code.py from learn-claude-code inside the course container and record every model call.

The repository's code is not changed. Before code.py runs, two things are replaced:
  1. anthropic.Anthropic: the API key is passed in when the client is built (the key is read from the first
     line of stdin; it never goes into an environment variable or onto disk);
  2. Messages.create: each call gets output_config.effort, and the request and reply are written to /out/trace.jsonl.
input() is replaced by answers taken in order from "inputs" in /out/spec.json (the REPL questions, the y/n
approvals), echoed to the terminal.
After reading the key as root, the process drops to uid 1000 before running: the agent's bash subprocesses
cannot read the key (once a process has changed identity, only root can read its memory and environment in
/proc, and there is no key file under /run).
A cost guard: after max_calls model calls (spec.json) the run stops with exit code 3.
"""
import builtins, ctypes, json, os, runpy, sys, time

SPEC = json.load(open("/out/spec.json", encoding="utf-8"))
KEY = sys.stdin.readline().strip()
sys.stdin = open(os.devnull)
if not KEY.startswith("sk-"):
    sys.exit("lcc_run: the first line of stdin is not an API key")
try:
    ctypes.CDLL(None).prctl(4, 0, 0, 0, 0)  # PR_SET_DUMPABLE = 0
except Exception:
    pass
os.setgroups([]); os.setgid(1000); os.setuid(1000)
os.environ.update(HOME="/home/student", USER="student", LOGNAME="student",
                  MODEL_ID=SPEC["model"], PYTHONUNBUFFERED="1")
for k in ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_BASE_URL"):
    os.environ.pop(k, None)

import anthropic
from anthropic.resources.messages import Messages
sys.path.insert(0, "/opt/lcc")
import verbose_fmt as VF

_Orig = anthropic.Anthropic
class _Client(_Orig):
    def __init__(self, *a, **kw):
        kw["api_key"] = KEY
        kw.setdefault("timeout", 120.0)   # a call stuck for 120 s is retried by the SDK
        kw.setdefault("max_retries", 3)
        kw.pop("base_url", None) if kw.get("base_url") is None else None
        super().__init__(*a, **kw)
anthropic.Anthropic = _Client

VERBOSE = SPEC.get("verbose", True)
MAX_CALLS = int(SPEC.get("max_calls") or 0)   # 0 = no limit
TRACE = open("/out/trace.jsonl", "a", encoding="utf-8")
_create = Messages.create
_n = [0]

def _dump(x):
    if hasattr(x, "model_dump"):
        return x.model_dump(mode="json", exclude_none=True)
    if isinstance(x, list):
        return [_dump(i) for i in x]
    if isinstance(x, dict):
        return {k: _dump(v) for k, v in x.items()}
    return x

def _say(s):
    if VERBOSE:
        print(s, flush=True)

def create(self, *a, **kw):
    if MAX_CALLS and _n[0] >= MAX_CALLS:
        print(f"lcc_run: stopped before call {_n[0] + 1}: max_calls = {MAX_CALLS} reached (cost guard)", flush=True)
        TRACE.flush()
        os._exit(3)
    kw.setdefault("output_config", {"effort": SPEC["effort"]})
    _n[0] += 1
    n = _n[0]
    req = {k: _dump(v) for k, v in kw.items() if k != "extra_headers"}
    if n == 1:
        _say(VF.banner(req, kw.get("model")))
    _say(VF.before_call(n, req))
    t0 = time.time()
    resp = _create(self, *a, **kw)
    dt = round(time.time() - t0, 2)   # the same rounded value goes to the screen and to the trace, so replay.py matches
    rd = _dump(resp)
    _say(VF.after_call(rd, dt))
    TRACE.write(json.dumps({"call": n, "t": round(t0, 3), "seconds": dt,
                            "request": req, "response": rd}, ensure_ascii=False) + "\n")
    TRACE.flush()
    return resp
Messages.create = create

_inputs = list(SPEC["inputs"])                 # answers to the REPL prompt, in order
_approvals = list(SPEC.get("approvals", []))   # answers to "Allow? [y/N]"-style approvals, in order; once used up, always "n"
def fake_input(prompt=""):
    clean = prompt.replace("\001", "").replace("\002", "")
    if "allow" in clean.lower() or "[y/n]" in clean.lower():
        ans = _approvals.pop(0) if _approvals else "n"
    elif _inputs:
        ans = _inputs.pop(0)
    else:
        print(clean + "q", flush=True)
        raise EOFError
    print(clean + ans, flush=True)
    return ans
builtins.input = fake_input

os.chdir("/workspace")
sys.argv = ["code.py"] + SPEC.get("argv", [])
sys.path.insert(0, os.path.dirname(SPEC["code"]))
runpy.run_path(SPEC["code"], run_name="__main__")
