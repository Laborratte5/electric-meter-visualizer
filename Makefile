PYTHON_PACKAGES=electric_meter_visualizer tests
PYTHON_VENV=poetry run

# code checks
.PHONY: check-format check-import-sorting check-style check-typing check
check-format:
	$(PYTHON_VENV) black --check $(PYTHON_PACKAGES)/

check-import-sorting:
	$(PYTHON_VENV) isort --check-only $(PYTHON_PACKAGES)/

check-style:
	$(PYTHON_VENV) flake8 $(PYTHON_PACKAGES)

check-typing:
	$(PYTHON_VENV) mypy $(PYTHON_PACKAGES)/

check: check-format check-import-sorting check-style check-typing

# automatic code fixes
.PHONY: fix clean
fix:
	$(PYTHON_VENV) black $(BLACK_FLAGS) $(PYTHON_PACKAGES)/
	$(PYTHON_VENV) isort $(ISORT_FLAGS) $(PYTHON_PACKAGES)/

clean:
	rm -rf ./**/__pycache__
	rm -rf ./.mypy_cache

.PHONY: doc
doc:
	$(PYTHON_VENV) pdoc3 --html --output-dir doc/ --force $(PYTHON_PACKAGES)
