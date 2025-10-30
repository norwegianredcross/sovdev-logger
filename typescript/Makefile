.PHONY: lint
lint:
	@echo "Running TypeScript linting..."
	npm run lint

.PHONY: lint-fix
lint-fix:
	@echo "Running TypeScript linting with auto-fix..."
	npm run lint:fix

.PHONY: install
install:
	@echo "Installing dependencies..."
	npm install

.PHONY: build
build:
	@echo "Building TypeScript library..."
	npm run build

.PHONY: test
test:
	@echo "Running tests..."
	npm test

.PHONY: help
help:
	@echo "Available targets:"
	@echo "  lint      - Run linting checks (MANDATORY before build)"
	@echo "  lint-fix  - Run linting with auto-fix"
	@echo "  install   - Install dependencies"
	@echo "  build     - Build the library"
	@echo "  test      - Run tests"
	@echo "  help      - Show this help message"
