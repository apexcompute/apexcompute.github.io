> **Watch and try it:** the video, a guess-first question and the interactive figures for this episode are on [the episode page](https://apexcompute.github.io/courses/claude-code/E02/).

# E02 With more tools, does the loop have to change? (s02 Tool Use)

> This is the E02 folder of the materials for my study log of learn-claude-code. It follows the video.
> Each script starts with a copyright line. For the licence, see `LICENSE` and `NOTICE.md` one folder up.

## What is in this folder

| File or folder | What it does |
|---|---|
| `examples/ex1.yaml`–`ex3.yaml` | The three examples in the video: the chapter, the starting workspace, and the request we type |
| `seeds/notes_project/` | The small workspace for all three examples (three notes, two logs, a README) |
| `runner/` | The recorder (the same as in E01). `Dockerfile` builds the course container. `lcc_run.py` runs the upstream `code.py` in the container without changing it, saves every request and reply, and prints the verbose view. `verbose_fmt.py` is the layout of that view. `replay.py` rebuilds the terminal from `trace.jsonl` without calling the model. `run_example.py` starts the container on your computer and runs one example. |
| `count_runs.py` | Counts the repeated runs by the rules we fixed before the first run |
| `config.yaml` | Model `claude-sonnet-5-5`, effort `medium`, the image, the upstream commit, where your key file is |
| `frozen/` | The real runs shown in the video. `verbose.log` is the terminal in the video. `terminal.log` is the same text as it was printed live. `trace.jsonl` holds every request and reply in full. `meta.json` has tokens, time and an estimated cost. `workspace_after/` is the workspace when the run ended. |

The upstream code (`s01_agent_loop/code.py`, `s02_tool_use/code.py`) is not in these materials. In the top
folder of the materials, run `git clone https://github.com/shareAI-lab/learn-claude-code`, then
`git -C learn-claude-code checkout 448c75b`. This is the version used in the video. It is under the MIT licence.

## Free: no API key, no cost

```bash
cd E02
python3 -B runner/replay.py frozen/ex1             # the bash-only version: one sed command
python3 -B runner/replay.py frozen/ex2_r1          # the five-tool version: one edit_file call
python3 -B runner/replay.py frozen/ex3_r2 --check  # check that the rebuilt text is the same as the live terminal
python3 -B count_runs.py                           # count the repeated runs of examples 2 and 3
python3 -c "import json; [print(b['input']) for l in open('frozen/ex3_r2/trace.jsonl') for b in json.loads(l)['response']['content'] if b['type'] == 'tool_use']"
```

What you should see:

- `replay.py frozen/ex1` prints two rounds. The yellow command uses `sed -i` and then `grep -n "milk"`,
  which prints `1:Buy soy milk`.
- `replay.py frozen/ex2_r1` prints `> edit_file` and `Edited notes/todo.txt`. The terminal of s02 does not
  print the command, only the tool name and its result.
- `--check` prints `replay: OK, 3 calls, rebuilt text equals terminal.log (…)`. It works for every folder in `frozen/`.
- `count_runs.py` prints:
  - `ex2: … edit_file in 5 of 5 runs; todo.txt changed in 5 of 5`
  - one line per ex3 run: `ex3_r1` to `ex3_r4` use `['glob', 'bash']`, `ex3_r5` uses `['bash', 'bash']`; every run
    has 3 calls and a correct `summary.md`
  - `ex3: only bash in 1 of 5 runs; mixed in 4`
- The last command prints the two tool inputs of `ex3_r2`: the glob pattern, then the full bash command that
  reads the first line of each note and writes `summary.md`. The terminal never printed that command.

`-B` only stops Python from writing a `__pycache__` folder.

## Run it yourself (needs your own Anthropic API key, you pay for what you use)

```bash
cd E02
docker build -t lcc-course-en:v0.1 runner/
echo "ANTHROPIC_API_KEY=your-key" > ../.env       # in the top folder of the materials; never commit it or send it to anyone
python3 runner/run_example.py examples/ex1.yaml   # results go to examples/results/ex1/
python3 runner/run_example.py examples/ex2.yaml --rep=1    # repeated example: run --rep=1 up to --rep=5
python3 -B count_runs.py examples/results          # count your own runs
```

You need Python 3 with PyYAML, and Docker. The key goes into the container only through a pipe.
The agent's commands inside the container cannot read it (see the top of `lcc_run.py`).
A run stops after 8 model calls (`max_calls` in `config.yaml`).

**Cost.** These numbers come from the token counts in our traces, priced at the `config.yaml` prices
(2 US dollars per million input tokens, 10 per million output tokens):

| Example | Model calls | Input tokens | Output tokens | About |
|---|---|---|---|---|
| ex1 | 2 | 1002 | 160 | $0.004 |
| ex2 (each run) | 2 | 1733 | about 160 | $0.005 |
| ex3 (each run) | 3 | about 2770 | about 280 | $0.008 |

All 11 runs in `frozen/` together cost about $0.07. Prices can change, so check Anthropic's own pricing page
before you run.

The model's answers change from run to run. The numbers in the video come from `frozen/`:

- Example 1 (s01, bash only, 1 run): 2 rounds. Round 1 input 444 tokens, round 2 input 558.
- Example 2 (s02, 5 runs, fixed before the first run): every run calls `edit_file` first and changes the file
  correctly. Round 1 input 803 tokens, round 2 input 930, in every run. Every answer says it did not open the
  file again to check.
- Same request, round 1: 803 − 444 = 359 more input tokens with five tools. The messages are the same; the
  system prompt differs by one word; the tool definitions grow from 165 to 1039 characters of JSON.
- Example 3 (s02, 5 runs, fixed before the first run): runs 1–4 use `glob`, then one `bash` command that reads
  and writes; run 5 uses `bash` twice. No run calls `read_file` or `write_file`. Every run writes a correct
  `summary.md` with bash.

## Try it

1. The question at the end of the video. Say the model writes a tool name that is not in `TOOL_HANDLERS`, for
   example `read`. Does the program crash, or keep looping? Read lines 177–183 of `s02_tool_use/code.py`.
2. If you have a key: copy `examples/ex3.yaml` to a new file and add "Use read_file and write_file." to the
   request. Run it once. Do the tool names change? This is a single exploratory run, not the registered
   experiment from the video.
3. Free: in `frozen/ex2_r1/trace.jsonl`, compare the `tools` list of the request on line 1 with the one in
   `frozen/ex1/trace.jsonl`. How many tool definitions does each have, and which fields does `edit_file` require?

## Check your answers

1. It keeps looping. Line 180 uses `TOOL_HANDLERS.get(block.name)`, which gives `None` for an unknown name.
   Line 181 then sets the output to `Unknown: read`, and line 183 sends that back as a `tool_result`. The model
   reads it in the next round.
2. There is no fixed answer. Look at the `> name` lines in `examples/results/<name>/verbose.log`.
3. s01 has 1 tool (bash); s02 has 5. `edit_file` requires `path`, `old_text` and `new_text`.
