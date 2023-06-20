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
    && rm -rf /var/lib/apt/lists/*

# upgrade pip
RUN pip install --no-cache-dir --upgrade pip

# make dir /app and copy requirements.txt and docker folder
RUN mkdir -p /app
WORKDIR /app

# copy scripts/generate_pytorch_dep_urls.py
COPY scripts/generate_pytorch_dep_urls.py /app/scripts/
RUN python scripts/generate_pytorch_dep_urls.py

# CPU-specific pytorch hack to prevent bloated image
# Else it ends up installing CUDA libs on a CPU only arch
# TODO: have an option to use GPU libs when available
RUN --mount=type=cache,target=/home/.cache/pip \
    pip install --no-cache-dir -r torch-requirements.txt

# install poetry
RUN --mount=type=cache,target=/home/.cache/pip \
    pip install --no-cache-dir poetry \
    && poetry config virtualenvs.create false

# TODO: copy poetry.lock once stable
COPY poetry.toml pyproject.toml /app/

# install Python dependencies
RUN --mount=type=cache,target=/home/.cache/pypoetry/cache \
    --mount=type=cache,target=/home/.cache/pypoetry/artifacts \
    poetry install --only main --no-interaction --no-ansi

RUN mkdir -p /app/logs
RUN mkdir -p /app/share

RUN python -m nltk.downloader punkt
RUN python -c 'from sentence_transformers import SentenceTransformer; SentenceTransformer("distiluse-base-multilingual-cased-v1")'

# copy the source code
COPY . /app

# TODO: don't run as root - add logic to entrypoint
COPY docker/docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

EXPOSE 8080
ENV PYTHONPATH /app:$PYTHONPATH

ENTRYPOINT ["docker-entrypoint.sh"]