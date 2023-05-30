#!/bin/bash
set -exu
set -o pipefail

apt-get update
TZ=UTC apt-get install --no-install-recommends python3.11 python3.11-dev python3.11-venv -y

python3 -m venv .
bin/pip install --no-cache-dir -r requirements.txt
bin/python setup.py develop
bin/pip install --no-cache-dir supervisor

apt-get purge -y --auto-remove python3.11-dev
