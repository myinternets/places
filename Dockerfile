FROM python:3.11-slim-buster

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    python3-dev \
    python3-pip \
    libpoppler-cpp-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# upgrade pip
RUN pip install --no-cache-dir --upgrade pip

# make dir /app and copy requirements.txt and docker folder
RUN mkdir -p /app
WORKDIR /app

# install poetry
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir poetry \
    && poetry config virtualenvs.create false

# TODO: copy poetry.lock once stable
COPY poetry.toml pyproject.toml /app/

# install Python dependencies
RUN --mount=type=cache,target=/root/.cache/pypoetry \
    poetry install --only main --no-interaction --no-ansi

RUN --mount=type=cache,target=/root/.cache/pip \
    pip install torch==2.0.1 torchvision==0.15.2 \
      --index-url https://download.pytorch.org/whl/cpu

RUN mkdir -p /app/logs
RUN mkdir -p /app/share

# copy the source code
COPY . /app

# install the app
RUN --mount=type=cache,target=/root/.cache/pypoetry \
    pip install -e /app/

# load all the models
RUN places load

# TODO: don't run as root - add logic to entrypoint
COPY docker/docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

EXPOSE 8080
ENV PYTHONPATH /app:$PYTHONPATH

ENTRYPOINT ["docker-entrypoint.sh"]
