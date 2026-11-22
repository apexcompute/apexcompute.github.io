# Copyright (c) 2026 the course author. MIT License, see LICENSE in the materials package.
# Course container for running each chapter's code.py from learn-claude-code: Python + pinned dependencies,
# no credentials, none of the author's files.
FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/* \
 && pip install --no-cache-dir anthropic==2.8.0 python-dotenv==1.1.1 pyyaml==6.0.2 \
 && useradd -m -u 1000 -s /bin/bash student && mkdir -p /workspace /out /course && chown student:student /workspace /out
COPY lcc_run.py verbose_fmt.py /opt/lcc/
WORKDIR /workspace
ENTRYPOINT ["python3", "/opt/lcc/lcc_run.py"]
