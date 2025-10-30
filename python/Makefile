.PHONY: lint
lint:
	@echo "Running Python linting..."
	@echo "1/3 - Running flake8..."
	flake8 src/
	@echo "2/3 - Running black (check only)..."
	black --check src/
	@echo "3/3 - Running mypy..."
	mypy src/
	@echo "✅ All linting checks passed!"

.PHONY: lint-fix
lint-fix:
	@echo "Running Python auto-formatting..."
	black src/
	@echo "✅ Formatting applied!"

.PHONY: install
install:
	@echo "Installing sovdev-logger in editable mode..."
	pip install -e .

.PHONY: help
help:
	@echo "Available targets:"
	@echo "  lint      - Run linting checks (MANDATORY before build)"
	@echo "  lint-fix  - Run auto-formatting with black"
	@echo "  install   - Install package in editable mode"
	@echo "  help      - Show this help message"
