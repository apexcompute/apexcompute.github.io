# Copyright (c) 2026 the course author. MIT License, see LICENSE in the materials package.
"""verbose_fmt.py - lay out one model call (request and reply) as "verbose mode" terminal text.

The layout follows the verbose printing the author added while studying the first 8 chapters of the older
version in April 2026: at start-up MODEL / SYSTEM / TOOLS; each round lists the messages, then the reply's
stop_reason and content blocks. It only reads the JSON form of the request and the reply, so the live run
(lcc_run.py) and the replay afterwards (replay.py) print exactly the same text.
"""
import json

DIM, GREEN, CYAN, MAGENTA, BOLD, RESET = "\033[2m", "\033[32m", "\033[36m", "\033[35m", "\033[1m", "\033[0m"
PREVIEW = 60


def _short(s, n=PREVIEW):
    s = str(s).replace("\n", "\\n")
    return s if len(s) <= n else s[:n] + f"… ({len(s)} chars)"


def _block(b):
    t = b.get("type")
    if t == "text":
        return f'text: "{_short(b.get("text", ""))}"'
    if t == "tool_use":
        return f'tool_use: {b.get("name")}({_short(json.dumps(b.get("input", {}), ensure_ascii=False))})'
    if t == "tool_result":
        c = b.get("content", "")
        if isinstance(c, list):
            c = " ".join(x.get("text", "") for x in c if isinstance(x, dict))
        return f'tool_result: "{_short(c)}"'
    if t == "thinking":
        return "thinking (content not returned)"
    return t


def banner(req, model):
    tools = [t.get("name") for t in req.get("tools") or []]
    eff = (req.get("output_config") or {}).get("effort")
    return "\n".join([
        f"{BOLD}=== verbose mode ==={RESET}",
        f"{DIM}MODEL  = {model} (effort = {eff}){RESET}",
        f"{DIM}SYSTEM = {_short(req.get('system', ''), 200)}{RESET}",
        f"{DIM}TOOLS  = {json.dumps(tools, ensure_ascii=False)}{RESET}",
        ""])


def before_call(n, req):
    out = [f"{MAGENTA}{'─' * 16} Round {n}: sent to the model {'─' * 16}{RESET}", f"{DIM}messages = [{RESET}"]
    for i, m in enumerate(req.get("messages", [])):
        c = m.get("content")
        if isinstance(c, str):
            out.append(f'{DIM}  [{i}] {m["role"]}: "{_short(c)}"{RESET}')
        else:
            for b in c or []:
                out.append(f"{DIM}  [{i}] {m['role']}/{_block(b)}{RESET}")
    out.append(f"{DIM}]{RESET}")
    out.append(f"{CYAN}→ calling client.messages.create(...){RESET}")
    return "\n".join(out)


def after_call(resp, seconds):
    u = resp.get("usage", {})
    out = [f'{GREEN}response.stop_reason = "{resp.get("stop_reason")}"{RESET}', f"{GREEN}response.content = [{RESET}"]
    for b in resp.get("content", []):
        out.append(f"{GREEN}  {_block(b)}{RESET}")
    out.append(f"{GREEN}]{RESET}")
    out.append(f"{DIM}(input {u.get('input_tokens', 0)} tokens, output {u.get('output_tokens', 0)} tokens, {seconds:.1f} s){RESET}")
    # Same test as the upstream code.py: is there a tool_use block in the reply? (since upstream 168fff8 it no longer looks at stop_reason)
    if not any(b.get("type") == "tool_use" for b in resp.get("content", [])):
        out.append(f"{BOLD}No tool_use block in the reply → the loop ends, back to waiting for your input{RESET}")
    else:
        out.append(f"{CYAN}→ run the tools, put the results back into messages as tool_result, next round{RESET}")
    return "\n".join(out)
