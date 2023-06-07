#!/bin/bash
set -exu
set -o pipefail

# apt-get update
# TZ=UTC apt-get install --no-install-recommends python3.11 python3.11-dev python3.11-venv -y

python3 -m venv .venv
# .venv/bin/pip install --no-cache-dir .
# .venv/bin/pip install --no-cache-dir supervisor
.venv/bin/pip install --no-cache-dir poetry
.venv/bin/poetry config virtualenvs.create false --local
.venv/bin/poetry install

# apt-get purge -y --auto-remove python3.11-dev
