.PHONY: install test lint demo docker
install:
	pip install -e ".[dev]"
test:
	pytest -q
lint:
	ruff check src tests && mypy src
demo:
	sunset-engine scorecard
docker:
	docker build -t nist-rmf-governance-engine . && docker run --rm nist-rmf-governance-engine
