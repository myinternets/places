- [Places](#places)
- [Install](#install)
  - [Local](#local)
  - [Docker](#docker)
- [Run](#run)
- [Indexing](#indexing)
- [View](#view)


**Experimental**


[![Ruff](https://github.com/myinternets/places/actions/workflows/ruff.yml/badge.svg?event=push)](https://github.com/myinternets/places/actions/workflows/ruff.yml)

[![Docker Image CI](https://github.com/myinternets/places/actions/workflows/docker-image.yml/badge.svg)](https://github.com/myinternets/places/actions/workflows/docker-image.yml)


Places
------

Semantic Search on your Browser History

## Install

Build the docker image containing Qdrant and the app, then run it

### Local

```sh
# GPU
make install 

# CPU only
make install-cpu
```

### Docker

Builds the places docker image

```sh
# builds the docker image
make build-app
```

Note: default install uses GPU, if you don't have one, you can change it to `make install-cpu`

## Run

```sh
# direct, without docker
make web

# runs the docker image
make run-app
```

## Indexing

Then index the Firefox data using the `index.py` script and the path
to the profile's `places.sqlite` file.

```sh
# from virtualenv (source .venv/bin/activate)
places index /path/to/places.sqlite

# or (if places.sqlite is in the current directory)
make index 
```

## View

Then open (even while it's indexing)  http://localhost:8080
