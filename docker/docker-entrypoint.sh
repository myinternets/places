#!/bin/bash

set -e

# Wait for the qdrant service to become available
# while ! nc -z qdrant 6333; do
#   sleep 1
# done

# Start supervisord
# exec supervisord -c /app/docker/supervisord.conf

/usr/local/bin/python /app/places/web.py
