.PHONY: clean run-quadrant index web install build-app run-app

install:
	python3 -m venv .venv
	.venv/bin/pip install poetry
	.venv/bin/poetry config virtualenvs.create false --local
	.venv/bin/poetry install

run-quadrant:
	docker run --name qdrant -d --rm -p 6333:6333 -v storage:/qdrant/storage qdrant/qdrant:v1.2.2

index:
	.venv/bin/python places/index.py places.sqlite

web:
	.venv/bin/python places/web.py

build-app:
	docker build -t tarek/places .
	# docker build --progress=plain -t tarek/places . 2>&1 > /tmp/build.log

run-app:
	docker compose up -d
	# docker run --name places-app -d --rm -p 8080:8080 -v storage:/app/docker/storage tarek/places
	# docker run --name places-app -d --rm -p 6333:6333 -p 8080:8080 -v storage:/app/docker/storage tarek/places

lint:
	.venv/bin/ruff places

test:
	.venv/bin/pytest -sv places/tests

autoformat:
	.venv/bin/isort places
	.venv/bin/black places

clean:
	rm -rf places.egg-info
	rm -rf places/__pycache__
	rm -rf .pytest_cache
	rm -rf .nox
	rm -rf .mypy_cache
	rm -rf .cache
	rm -rf .venv
	rm -rf lib
	rm -rf lib64
	rm -rf share
	rm -rf bin
	rm -rf include
	rm -rf poetry.lock
	docker rm -f places-app qdrant 2>/dev/null || docker-compose kill && docker-compose rm -f 2>/dev/null || true
