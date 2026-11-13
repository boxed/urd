.PHONY: clean-pyc clean-build docs clean lint test coverage docs dist tag release-check

help:
	@echo "clean-build - remove build artifacts"
	@echo "clean-pyc - remove Python file artifacts"
	@echo "lint - check style with flake8"
	@echo "test - run tests"
	@echo "coverage - check code coverage quickly with the default Python"
	@echo "docs - generate Sphinx HTML documentation, including API docs"
	@echo "dist - package"
	@echo "tag - set a tag with the current version number"
	@echo "release-check - check release tag"

clean: clean-build clean-pyc
	rm -rf htmlcov/
	rm -rf venv

clean-build:
	rm -fr build/
	rm -fr dist/
	rm -fr lib/*.egg-info

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name "__pycache__" -type d -delete

clean-docs:
	rm -f docs/tri*.rst


test:
	pytest

dist: clean-build
	uv build
	ls -l dist

VERSION = $(shell sed -n "s/^__version__ = '\(.*\)'/\1/p" urd/__init__.py)

tag:
	git tag --annotate $(VERSION) --message "Version $(VERSION)"

release-check:
	@test "$$(git describe HEAD)" = "$(VERSION)" || (echo "Missing $(VERSION) tag on release" && exit 1)

venv:
	python -m venv venv


makemessages:
	(cd urd && django-admin makemessages -a)
	(cd examples && django-admin makemessages -a)


compilemessages:
	(cd urd && django-admin compilemessages)
	(cd examples && django-admin compilemessages)

release:
	rm -rf dist/ build/ && uv build && twine upload dist/*
