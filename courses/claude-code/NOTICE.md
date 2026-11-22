# learn-claude-code study log: licence notes for the materials

Copyright (c) 2026 the course author (the author of this study log), not shareAI Lab or Anthropic.
The **scripts I wrote** for these materials (`.py` files and `Dockerfile`) are released under the MIT licence.
The full text is in `LICENSE` in this folder. Each script starts with a one-line copyright notice. This is a
record of how I studied the open-source repository learn-claude-code. It is not made by, and not linked to,
the authors of that repository or Anthropic.

- In each episode folder (`E01/`, ...), the scripts, the example files and the starting workspaces (`seeds/`)
  were written by the author of this study log. You may read, run, change and share them under the MIT licence;
  keep the copyright line and `LICENSE`. `frozen/` holds the records of the runs used in the video (the model's
  answers, and any code the model wrote). They are there for you to compare with, nothing more.
- These materials do **not** include the code or the notes of shareAI-lab/learn-claude-code. That repository
  is under the MIT licence (https://github.com/shareAI-lab/learn-claude-code; the video uses commit `448c75b`).
  Clone it yourself to run the examples, and use it under its own licence. One exception: the run records in
  `frozen/` (`trace.jsonl`, `verbose.log`) contain text the model read through the upstream code, such as the
  upstream system prompt. That text belongs to the upstream project and is under its MIT licence
  (Copyright (c) 2024 shareAI Lab).
- Third-party software needed to run the examples is not shipped with the materials. Install it yourself, under
  its own licence:
  - Docker, Python 3, PyYAML: to run the examples yourself.
  - Inside the course container: `anthropic==2.8.0`, `python-dotenv==1.1.1`, `pyyaml==6.0.2`, installed from
    PyPI when `runner/Dockerfile` is built.
  - Calling the model needs your own Anthropic API key, and you pay for what you use. Without a key you can still
    read the records in `frozen/` with `replay.py`.
- The folders in the materials are one folder per episode (`E01/`, ...), plus this file and `LICENSE`.

Provided as is, without any warranty.
