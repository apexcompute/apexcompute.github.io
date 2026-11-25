#!/usr/bin/env python3
# Copyright (c) 2026 the course author. MIT License, see LICENSE in the materials package.
"""run_example.py - run one example on the host: prepare a workspace, start the course container, pass the key in
through a pipe, and after the run scan the results for the key and for the host's machine name.

    python3 run_example.py ../E01/ex1.yaml                 # results go to ../E01/results/ex1/
    python3 run_example.py ../E01/ex1.yaml --dry           # only print what would be done
    python3 run_example.py ../E01/ex2.yaml --rep=3         # 3rd repetition of a repeated example -> results/ex2_r3/
    python3 run_example.py ../E01/ex3.yaml --max-calls=6   # stop after 6 model calls (cost guard; default in config.yaml)

An example file (yaml) has: chapter (upstream chapter folder), seed (folder with the workspace's starting files,
relative to the example file), inputs (strings that answer input() in order). Model, effort, image and upstream
commit live in ../config.yaml, not in the example file.
"""
import json, os, re, shutil, socket, subprocess, sys, tempfile, time
import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
CFG = yaml.safe_load(open(os.path.join(HERE, "..", "config.yaml"), encoding="utf-8"))

def _mk(d):
    os.makedirs(d, exist_ok=True); return d

def read_key():
    env = os.path.expanduser(CFG["key_env_file"])
    for line in open(env, encoding="utf-8"):
        m = re.match(r"\s*ANTHROPIC_API_KEY\s*=\s*['\"]?([^'\"\s]+)", line)
        if m:
            return m.group(1)
    sys.exit("ANTHROPIC_API_KEY not found in key_env_file")

def mask_host(out):
    """Replace the host's machine name with <HOST> in every result file (none expected: the container has a fixed hostname)."""
    host = socket.gethostname().split(".")[0]
    hit = []
    if len(host) < 3:
        return hit
    for root, _, files in os.walk(out):
        for f in files:
            p = os.path.join(root, f)
            b = open(p, "rb").read()
            nb = re.sub(re.escape(host).encode(), b"<HOST>", b, flags=re.I)
            if nb != b:
                open(p, "wb").write(nb); hit.append(os.path.relpath(p, out))
    return hit

def main():
    spec_path = os.path.abspath(sys.argv[1]); dry = "--dry" in sys.argv
    ex = yaml.safe_load(open(spec_path, encoding="utf-8"))
    name = os.path.splitext(os.path.basename(spec_path))[0]
    max_calls = CFG.get("max_calls", 0)
    for a in sys.argv[2:]:
        if a.startswith("--rep="):
            name += "_r" + a.split("=", 1)[1]
        if a.startswith("--max-calls="):
            max_calls = int(a.split("=", 1)[1])
    out = os.path.join(os.path.dirname(spec_path), "results", name)
    fork = os.path.abspath(os.path.join(HERE, "..", CFG["fork_dir"]))
    head = subprocess.run(["git", "-C", fork, "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
    if os.path.exists(out) and not dry:
        sys.exit(f"{out} already exists; move it away before re-running (existing results are never overwritten)")
    spec = {"model": CFG["model"], "effort": CFG["effort"], "inputs": ex["inputs"], "approvals": ex.get("approvals", []),
            "code": f"/course/{ex['chapter']}/code.py", "verbose": ex.get("verbose", True), "argv": ex.get("argv", []),
            "max_calls": max_calls}
    if dry:   # print only: no workspace, no results folder
        print(json.dumps(spec, ensure_ascii=False))
        print("docker run ... -v <fork>/%s:/course/%s:ro -v <workspace>:/workspace -v %s:/out %s"
              % (ex["chapter"], ex["chapter"], out, CFG["image"]))
        return
    work = tempfile.mkdtemp(prefix="lcc_ws_", dir=_mk(os.path.join(HERE, "..", CFG["scratch"])))
    seed = ex.get("seed")
    if seed:
        shutil.copytree(os.path.join(os.path.dirname(spec_path), seed), work, dirs_exist_ok=True)
    os.makedirs(out)
    json.dump(spec, open(os.path.join(out, "spec.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    cmd = ["docker", "run", "--rm", "-i", "--log-driver", "none", "--hostname", CFG["hostname"],
           "--dns-search", ".", "--cap-drop", "ALL", "--cap-add", "SETUID", "--cap-add", "SETGID",
           "--security-opt", "no-new-privileges", "--memory", "2g", "--pids-limit", "256",
           "-v", f"{fork}/{ex['chapter']}:/course/{ex['chapter']}:ro",
           "-v", f"{work}:/workspace", "-v", f"{out}:/out", CFG["image"]]
    os.chmod(out, 0o777); os.chmod(work, 0o777)
    t0 = time.time()
    with open(os.path.join(out, "terminal.log"), "wb") as log:
        p = subprocess.run(cmd, input=(read_key() + "\n").encode(), stdout=log, stderr=subprocess.STDOUT)
    # keep the workspace's final state too (the recording and the script look at it)
    shutil.copytree(work, os.path.join(out, "workspace_after"), dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns("__pycache__"))
    meta = {"example": name, "chapter": ex["chapter"], "model": CFG["model"], "effort": CFG["effort"],
            "image": CFG["image"], "fork_head": head, "upstream": CFG["upstream_commit"],
            "exit": p.returncode, "wall_seconds": round(time.time() - t0, 1), "max_calls": max_calls}
    tin = tout = calls = 0
    for line in open(os.path.join(out, "trace.jsonl"), encoding="utf-8") if os.path.exists(os.path.join(out, "trace.jsonl")) else []:
        r = json.loads(line); u = r["response"]["usage"]; calls += 1
        tin += u.get("input_tokens", 0) + u.get("cache_read_input_tokens", 0) + u.get("cache_creation_input_tokens", 0)
        tout += u.get("output_tokens", 0)
    pr = CFG["price_per_mtok"]
    meta.update(calls=calls, input_tokens=tin, output_tokens=tout,
                cost_usd_upper=round(tin / 1e6 * pr["input"] + tout / 1e6 * pr["output"], 4))
    json.dump(meta, open(os.path.join(out, "meta.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    shutil.rmtree(work, ignore_errors=True)
    # scan for the key: verbatim, and 24-character pieces from both ends
    key = read_key(); bad = []
    for root, _, files in os.walk(out):
        for f in files:
            b = open(os.path.join(root, f), "rb").read()
            if key.encode() in b or key[-24:].encode() in b or key[3:27].encode() in b:
                bad.append(os.path.join(root, f))
    if bad:
        open(os.path.join(out, "SECRET_FOUND.txt"), "w").write("\n".join(bad))
        sys.exit(f"the key is in the results, see {out}/SECRET_FOUND.txt; these results must not be used")
    masked = mask_host(out)
    if masked:
        print("host name replaced with <HOST> in: " + ", ".join(masked))
    # verbose.log for the screen: rebuilt from trace.jsonl by replay.py; it must equal the live terminal.log
    subprocess.run([sys.executable, os.path.join(HERE, "replay.py"), out, "--write"], check=True)
    print(json.dumps(meta, ensure_ascii=False))

if __name__ == "__main__":
    main()
