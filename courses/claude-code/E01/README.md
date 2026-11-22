> **Watch and try it:** the video, a guess-first question and the interactive figures for this episode are on [the episode page](https://apexcompute.github.io/courses/claude-code/E01/).

# E01 A chat model can only "talk". How do we make it "do"? (s01 Agent Loop)

> This is the E01 folder of the materials for my study log of learn-claude-code. It follows the video.
> Each script starts with a copyright line. For the licence, see `LICENSE` and `NOTICE.md` one folder up.

## What is in this folder

| File or folder | What it does |
|---|---|
| `examples/ex1.yaml`–`ex4.yaml` | The four examples in the video: the chapter, the starting workspace, and the question we type |
| `seeds/notes_project/` | The small workspace for examples 1–3 (three notes, two logs, a README) |
| `seeds/server_project/` | The small workspace for example 4 (a config file, a long server log, a README) |
| `runner/` | The recorder. `Dockerfile` builds the course container. `lcc_run.py` runs the upstream `code.py` in the container without changing it, saves every request and reply, and prints the verbose view. `verbose_fmt.py` is the layout of that view. `replay.py` rebuilds the terminal from `trace.jsonl` without calling the model. `run_example.py` starts the container on your computer and runs one example. |
| `count_runs.py` | Counts the repeated runs by the rules we fixed before the first run |
| `config.yaml` | Model `claude-sonnet-5-5`, effort `medium`, the image, the upstream commit, where your key file is |
| `frozen/` | The real runs shown in the video. `verbose.log` is the terminal in the video. `terminal.log` is the same text as it was printed live. `trace.jsonl` holds every request and reply in full. `meta.json` has tokens, time and an estimated cost. |

The upstream code (`s01_agent_loop/code.py`) is not in these materials. In the top folder of the
materials, run `git clone https://github.com/shareAI-lab/learn-claude-code`, then
`git -C learn-claude-code checkout 448c75b`. This is the version used in the video. It is under the MIT licence.

## Free: no API key, no cost

```bash
cd E01
python3 -B runner/replay.py frozen/ex1             # print the terminal of example 1, rebuilt from the trace
python3 -B runner/replay.py frozen/ex1 --check     # check that the rebuilt text is the same as the live terminal
python3 -B count_runs.py                           # count the repeated runs of examples 2, 3 and 4
python3 -c "import json; [print(len(json.loads(l)['request']['messages'])) for l in open('frozen/ex3/trace.jsonl')]"
```

What you should see:

- `replay.py frozen/ex1` prints two rounds. The tool prints `3`, then `2 ./diary.txt`, `3 ./plan.txt`,
  `3 ./todo.txt`, `8 total`. The answer says 3 files with 2, 3 and 3 lines.
- `--check` prints `replay: OK, 2 calls, rebuilt text equals terminal.log (2376 bytes)`. It works for every
  folder in `frozen/`.
- `count_runs.py` prints:
  - `ex2: 0 of 5 runs have a tool_use block in the round 1 reply`
  - `ex3: tool_use blocks per reply = [1, 1, 0]`
  - `ex4: 0 of 5 runs have a reply with 2 or more tool_use blocks`
  - `ex4: 5 of 5 runs have a tool output longer than 200 characters`
- The last command prints `1`, `3`, `5`: how many messages each of the three rounds of example 3 sends.

`-B` only stops Python from writing a `__pycache__` folder.

## Run it yourself (needs your own Anthropic API key, you pay for what you use)

```bash
cd E01
docker build -t lcc-course-en:v0.1 runner/
echo "ANTHROPIC_API_KEY=your-key" > ../.env       # in the top folder of the materials; never commit it or send it to anyone
python3 runner/run_example.py examples/ex1.yaml   # results go to examples/results/ex1/
python3 runner/run_example.py examples/ex2.yaml --rep=1    # repeated example: run --rep=1 up to --rep=5
python3 -B count_runs.py examples/results          # count your own runs
```

You need Python 3 with PyYAML, and Docker. The key goes into the container only through a pipe.
The agent's bash commands inside the container cannot read it (see the top of `lcc_run.py`).
A run stops after 8 model calls (`max_calls` in `config.yaml`), so a run cannot go on and on.

**Cost.** These numbers come from the token counts in our traces, priced at the `config.yaml` prices
(2 US dollars per million input tokens, 10 per million output tokens):

| Example | Model calls | Input tokens | Output tokens | About |
|---|---|---|---|---|
| ex1 | 2 | 1032 | 210 | $0.004 |
| ex2 (each run) | 1 | 428 | 17 | $0.001 |
| ex3 | 3 | 1793 | 390 | $0.008 |
| ex4 (each run) | 3 | about 2930 | about 610 | $0.012 |

All 12 runs in `frozen/` together cost about $0.08. These prices are estimates. Prices can change, so check
Anthropic's own pricing page before you run.

The model's answers change a little from run to run. The numbers in the video come from `frozen/`:

- Example 1: 2 rounds, 1 tool run. Input 439, then 593 tokens. 3 txt files with 2, 3 and 3 lines.
- Example 2 (5 runs, fixed before the first run; `--rep=1` … `--rep=5`): in all 5 runs the round 1 reply has
  no `tool_use` block. Every answer is "2 to the power of 10 is **1024**." Each run: input 428, output 17 tokens.
- Example 3 (1 run, fixed before the run): 3 rounds, one `tool_use` block per reply. Input 458, 540, 795 tokens.
  The model wrote count.py, ran it, and ran `wc -w` in the same command. Both give diary 11, plan 12, todo 9.
- Example 4 (5 runs, fixed before the first run): every run has 3 rounds and one `tool_use` block per reply.
  Every run has tool outputs over 200 characters (365 and 1373). Every answer: no, the config says 8080,
  but the server listens on 8081 because the PORT environment variable overrides the config.

## Try it

1. The question at the end of the video. First ask the question of example 1 (when it ends, messages has 4
   items). Do not quit. Ask a second question. In round 1 of the second question, how many messages are sent?
   Read lines 134–146 of `code.py` first.
2. If you have a key: copy `examples/ex2.yaml` to a new file and change the question to the product of two
   four-digit numbers. Run it once. Is there a `tool_use` block in the round 1 reply? This is a single
   exploratory run, not the registered experiment from the video.
3. Free: open line 2 of `frozen/ex4_r1/trace.jsonl` and find the `content` of `messages[2]`. Compare it with
   lines 22–26 of `frozen/ex4_r1/verbose.log`. What is missing on the screen?

## Check your answers

1. 5. `history` is made only once (line 134). Line 145 adds one user message for each question. The 4
   messages from example 1 are all still there.
2. There is no fixed answer. Look at `response.content` in round 1 of `examples/results/<name>/verbose.log`.
3. The terminal prints only the first 200 characters of each tool output (line 118 of `code.py`). The
   trace has the whole output (365 characters): the `config` and `logs` folders, the two files the model
   found (`./logs/server.log`, `./config/server.ini`), and two lines saying `ss` and `netstat` are not installed.
