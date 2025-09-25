PYTHON=python
PIP=$(PYTHON) -m pip

install:
	$(PIP) install -e .[test]

uninstall:
	$(PIP) uninstall crunch-convert

test:
	$(PYTHON) -m pytest -v

test-with-coverage:
	$(PYTHON) -m pytest --cov=crunch_convert --cov-report=html -v

build:
	rm -rf build *.egg-info dist
	python setup.py sdist bdist_wheel

.PHONY: install uninstall test build
