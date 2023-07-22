.PHONY: clean run-quadrant index web install build-app run-app test

install:
	python3 -m venv .venv
	.venv/bin/pip install "torch==2.0.1" "torchvision==0.15.2"
	.venv/bin/pip install poetry
	.venv/bin/poetry config virtualenvs.create false --local
	.venv/bin/poetry install
	.venv/bin/python -m nltk.downloader punkt
	.venv/bin/python -m nltk.downloader bcp47

install-cpu:
	python3 -m venv .venv
	.venv/bin/pip install torch==2.0.1 torchvision==0.15.2 --index-url https://download.pytorch.org/whl/cpu
	.venv/bin/pip install poetry
	.venv/bin/poetry config virtualenvs.create false --local
	.venv/bin/poetry install
	.venv/bin/python -m nltk.downloader punkt
	.venv/bin/python -m nltk.downloader bcp47


run-quadrant:
	docker run --name qdrant -d --rm -p 6333:6333 -v storage:/qdrant/storage qdrant/qdrant:v1.2.2

index:
	.venv/bin/python places/index.py places.sqlite

web:
	.venv/bin/places web

build-app:
	- docker buildx create --name builder
	- docker buildx use builder
	docker buildx build  --tag tarekziade/places --file Dockerfile --platform=linux/amd64,linux/arm64 .
        # should use push

build-app-local:
	- docker buildx create --name builder
	- docker buildx use builder
	docker buildx build  --load --tag tarekziade/places --file Dockerfile .


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
	mkdir -p dist; cd firefox; rm -rf web-ext-artifacts; web-ext build -n places-0.0.4.xpi

sign-webext:
	web-ext sign -s firefox -a dist --api-key=$(AMO_JWT_ISSUER) --api-secret=$(AMO_JWT_SECRET)
