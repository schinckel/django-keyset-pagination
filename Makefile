.PHONY: clean format lint package test test-all test-postgres test-mysql

clean:
	rm -rf .coverage .pytest_cache .ruff_cache .tox build dist htmlcov src/*.egg-info

format:
	python -m ruff check --fix .
	python -m ruff format .

lint:
	python -m ruff check .
	python -m ruff format --check .

package:
	python -m build
	python -m twine check dist/*

test:
	tox -e py312-django52-sqlite

test-all:
	tox -p auto

test-postgres:
	tox -e py312-django52-postgres

test-mysql:
	tox -e py312-django52-mysql
