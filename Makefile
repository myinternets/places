.PHONY: clean run-quadrant index web install build-app run-app

install-cpu:
	python3 scripts/generate_pytorch_dep_urls.py
	python3 -m venv .venv
	.venv/bin/pip install -r torch-requirements.txt
	.venv/bin/pip install poetry
	.venv/bin/poetry config virtualenvs.create false --local
	.venv/bin/poetry install

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
	.venv/bin/places web

build-app:
	docker build -t tarek/places .
	# docker build --progress=plain -t tarek/places . 2>&1 > /tmp/build.log

run-app:
	docker compose up -d
	# docker run --name places -d --rm -p 8080:8080 -v storage:/app/docker/storage tarek/places
	# docker run --name places -d --rm -p 6333:6333 -p 8080:8080 -v storage:/app/docker/storage tarek/places

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
	rm -rf poetry.lock
	rm -rf ~/.cache/places/
	docker compose kill
	docker compose rm -f 2>/dev/null || true
	# docker rm -f places qdrant 2>/dev/null

build-webext:
	mkdir -p dist; cd firefox; rm -rf web-ext-artifacts; web-ext build -n places-0.0.1.xpi

sign-webext:
	web-ext sign -s firefox -a dist --api-key=$(AMO_JWT_ISSUER) --api-secret=$(AMO_JWT_SECRET)
