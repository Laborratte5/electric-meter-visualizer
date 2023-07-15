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
