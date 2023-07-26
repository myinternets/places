.PHONY: clean run-service run-docker install build-app build-app-local test index

install:
	python3 -m venv .venv
	.venv/bin/pip install "torch==2.0.1" "torchvision==0.15.2"
	.venv/bin/pip install poetry
	.venv/bin/poetry config virtualenvs.create false --local
	.venv/bin/poetry install
	.venv/bin/places load

install-cpu:
	python3 -m venv .venv
	.venv/bin/pip install torch==2.0.1 torchvision==0.15.2 --index-url https://download.pytorch.org/whl/cpu
	.venv/bin/pip install poetry
	.venv/bin/poetry config virtualenvs.create false --local
	.venv/bin/poetry install
	.venv/bin/places load

index:
	.venv/bin/python places/index.py places.sqlite

run-service:
	- docker stop qdrant
	- docker rm qdrant
	- docker stop places
	- docker rm places
	docker run --name qdrant -d --rm -p 6333:6333 -v storage:/qdrant/storage qdrant/qdrant:v1.2.2
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

run-docker:
	- docker stop qdrant
	- docker stop places
	docker compose up -d

stop-docker:
	- docker stop qdrant
	- docker stop places
	- docker rm qdrant
	- docker rm places

lint:
	.venv/bin/isort places
	.venv/bin/black places
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
