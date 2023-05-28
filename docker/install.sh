#!/bin/bash
set -exu
set -o pipefail

#apt-get update
#apt-get install --no-install-recommends -y \
#		software-properties-common \
#		zlib1g-dev \
#		libncurses5-dev \
#		libgdbm-dev \
#		libnss3-dev \
#		libssl-dev \
#		libreadline-dev \
#		libffi-dev \
#		libsqlite3-dev \
#		wget \
#		git \
#		libbz2-dev


apt-get update
TZ=UTC apt-get install --no-install-recommends python3.11 python3.11-dev python3.11-venv -y

python3 -m venv .
bin/pip install --no-cache-dir -r requirements.txt
bin/python setup.py develop
bin/pip install --no-cache-dir supervisor

apt-get purge -y --auto-remove python3.11-dev
