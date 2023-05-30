#!/bin/bash
set -exu
set -o pipefail

MACHINE_TYPE=`uname -m`
if [ ${MACHINE_TYPE} == 'x86_64' ]; then
  /app/docker/qdrant_x86_64
else
  /app/docker/qdrant_aarch64
fi
