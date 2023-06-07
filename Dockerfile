FROM python:3.11-slim-buster

# ENV DEBIAN_FRONTEND=noninteractive

# make dir /app and copy requirements.txt and docker folder
RUN mkdir -p /app
# COPY requirements.txt /app/requirements.txt
WORKDIR /app

RUN pip install --no-cache-dir poetry \
    && poetry config virtualenvs.create false

# && poetry config experimental.new-installer false

COPY poetry.toml pyproject.toml /app/

# RUN bash docker/install.sh

# COPY poetry.lock /
RUN --mount=type=cache,target=/home/.cache/pypoetry/cache \
    --mount=type=cache,target=/home/.cache/pypoetry/artifacts \
    poetry install --no-dev --no-interaction --no-ansi

RUN mkdir -p /app/logs
RUN mkdir -p /app/share

# RUN pip install --no-cache-dir supervisor

# RUN apt-get update && apt-get install -y netcat

# copy last so any changes to the code don't invalidate the cache
# COPY docker /app/docker
# COPY docker/supervisord.conf /app/docker/supervisord.conf

COPY . /app

# EXPOSE 6333

# CMD ["/app/.venv/bin/supervisord", "-c", "/app/docker/supervisord.conf"]

# run supervisord in foreground (we don't have a .venv anymore, we directly installed via pip)
# CMD ["supervisord", "-c", "/app/docker/supervisord.conf"]

COPY docker/docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

EXPOSE 8080

ENTRYPOINT ["docker-entrypoint.sh"]