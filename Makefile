.PHONY: run-quadrant index web install build-docker run-docker

install:
	python3 -m venv .
	bin/pip install poetry
	bin/poetry config virtualenvs.create false --local
	bin/poetry install

run-quadrant:
	docker run --rm -p 6333:6333 -v storage:/qdrant/storage qdrant/qdrant

index:
	bin/python places/index.py places.sqlite

web:
	bin/python places/web.py

build-docker:
	docker build -t tarek/places .

run-docker:
	docker run -it --rm -p 6333:6333 -p 8080:8080 -v storage:/app/docker/storage tarek/places

lint:
	bin/ruff places

test:
	bin/pytest -sv places/tests

autoformat:
	bin/isort places
	bin/black places
