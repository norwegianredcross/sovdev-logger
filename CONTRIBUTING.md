# Contributing to sovdev-logger

Thank you for your interest in contributing to sovdev-logger! This document provides guidelines for contributing to this multi-language structured logging library.

---

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [Coding Standards](#coding-standards)
- [Submitting Changes](#submitting-changes)
- [Adding New Language Support](#adding-new-language-support)

---

## Code of Conduct

This project follows the Norwegian Red Cross code of conduct. Be respectful, inclusive, and constructive in all interactions.

---

## How Can I Contribute?

### Reporting Bugs

- Check if the bug has already been reported in [GitHub Issues](https://github.com/norwegianredcross/sovdev-logger/issues)
- If not, create a new issue with:
  - Clear title and description
  - Steps to reproduce
  - Expected vs actual behavior
  - Language/environment details (TypeScript version, Node.js version, etc.)
  - Log output or error messages

### Suggesting Enhancements

- Open an issue describing:
  - What problem does it solve?
  - How would it work?
  - Example code showing the proposed feature
  - Which language(s) would it affect?

### Pull Requests

We welcome pull requests! See [Submitting Changes](#submitting-changes) below.

---

## Development Setup

### TypeScript

```bash
cd typescript
npm install
npm run build
npm test
```

### Python (Coming Soon)

```bash
cd python
pip install -e .
pytest
```

### Other Languages

See language-specific README files in each directory.

---

## Project Structure

```
sovdev-logger/
├── README.md                 # Main repository overview
├── LICENSE                   # MIT license
├── CONTRIBUTING.md          # This file
├── CHANGELOG.md            # Version history
├── .gitignore              # Multi-language gitignore
│
├── docs/                   # Shared documentation
│   ├── README-configuration.md
│   ├── README-loggeloven.md
│   ├── README-microsoft-opentelemetry.md
│   ├── README-observability-architecture.md
│   └── logging-data.md
│
├── specification/          # Language-agnostic specification
│   ├── README.md
│   ├── 00-design-principles.md
│   ├── 01-api-contract.md
│   ├── 02-field-definitions.md
│   ├── 04-error-handling.md
│   ├── 05-environment-configuration.md
│   ├── 06-test-scenarios.md
│   ├── 08-anti-patterns.md
│   ├── schemas/           # JSON schemas for validation
│   ├── tests/             # Python validators
│   └── tools/             # Bash verification scripts
│
├── typescript/             # TypeScript implementation
│   ├── README.md          # TypeScript-specific docs
│   ├── package.json
│   ├── src/               # Source code
│   ├── examples/          # Usage examples
│   └── test/              # Test suite
│
├── python/                # Python implementation (coming soon)
│   ├── README.md
│   ├── setup.py
│   ├── sovdev_logger/
│   └── tests/
│
└── [other languages]/     # Additional language implementations
```

---

## Coding Standards

### General Principles

1. **Consistency**: Follow the existing patterns in each language implementation
2. **Documentation**: Update README files when adding features
3. **Testing**: Add tests for new functionality
4. **Examples**: Provide working examples for new features

### Language-Specific Standards

#### TypeScript

- Follow existing code style (see `typescript/.eslintrc` if available)
- Use TypeScript strict mode
- Export types and interfaces for public API
- Prefer `const` over `let`, avoid `var`
- Use async/await over callbacks
- Document public functions with JSDoc comments

**Example:**

```typescript
/**
 * Initialize the sovdev-logger with service information.
 *
 * @param service_name - Unique identifier for your service
 * @param service_version - Version of your service (optional)
 * @param peer_services - Peer service mappings (optional)
 */
export function sovdev_initialize(
  service_name: string,
  service_version?: string,
  peer_services?: Record<string, string>
): void {
  // Implementation...
}
```

#### Python (Coming Soon)

- Follow PEP 8 style guide
- Use type hints
- Document with docstrings (Google style)
- Use pytest for testing

#### Other Languages

See language-specific README files for coding standards.

---

## Submitting Changes

### Fork & Pull Request Workflow

1. **Fork** the repository to your GitHub account

2. **Clone** your fork locally:
   ```bash
   git clone git@github.com:YOUR_USERNAME/sovdev-logger.git
   cd sovdev-logger
   ```

3. **Add upstream remote**:
   ```bash
   git remote add upstream git@github.com:norwegianredcross/sovdev-logger.git
   ```

4. **Create a feature branch**:
   ```bash
   git checkout -b feature/add-new-logging-pattern
   ```

5. **Make your changes**:
   - Write code
   - Add tests
   - Update documentation
   - Ensure tests pass

6. **Commit your changes**:
   ```bash
   git add .
   git commit -m "Add new logging pattern for async operations"
   ```

7. **Push to your fork**:
   ```bash
   git push origin feature/add-new-logging-pattern
   ```

8. **Create Pull Request**:
   - Go to GitHub
   - Click "Compare & pull request"
   - Fill in description explaining your changes
   - Link any related issues

### Pull Request Guidelines

**Title Format:**
```
[Language] Brief description of change

Examples:
[TypeScript] Add support for custom trace IDs
[Python] Fix log rotation configuration
[Docs] Update Azure Monitor configuration guide
```

**Description:**
- What does this PR do?
- Why is it needed?
- How does it work?
- Any breaking changes?
- Related issues (use "Fixes #123" to auto-close)

**Before Submitting:**
- [ ] Code follows language-specific style guidelines
- [ ] Tests added/updated and passing
- [ ] Documentation updated (README, comments, examples)
- [ ] No breaking changes (or clearly documented if unavoidable)
- [ ] Commit messages are clear and descriptive

---

## Adding New Language Support

Want to implement sovdev-logger in a new language? Great! Follow these steps:

### 1. Create Directory Structure

```bash
mkdir -p NEW_LANGUAGE/src
mkdir -p NEW_LANGUAGE/examples
mkdir -p NEW_LANGUAGE/tests
```

### 2. Core Requirements

Your implementation must:

- ✅ Support all log levels (DEBUG, INFO, WARN, ERROR, FATAL)
- ✅ Generate structured JSON logs
- ✅ Support OpenTelemetry Protocol (OTLP) export
- ✅ Auto-generate logs, metrics, and traces from one call
- ✅ Support peer service tracking
- ✅ Provide `sovdev_log()`, `sovdev_log_job_status()`, `sovdev_log_job_progress()` functions
- ✅ Support trace correlation via trace_id
- ✅ Include console and file logging options
- ✅ Automatically flush logs before application exit

### 3. API Compatibility

Match the TypeScript API as closely as possible in your language:

**TypeScript:**
```typescript
sovdev_log(level, function_name, message, peer_service, input_json, response_json, exception_object, trace_id)
```

**Python (example):**
```python
sovdev_log(level, function_name, message, peer_service, input_json=None, response_json=None, exception=None, trace_id=None)
```

### 4. Documentation

Create `NEW_LANGUAGE/README.md` with:
- Installation instructions
- Quick start (60 seconds)
- Common patterns
- Configuration options
- Examples matching TypeScript examples
- API reference

### 5. Examples

Provide working examples in `NEW_LANGUAGE/examples/`:
- Basic usage (console + file logging)
- Advanced usage (batch processing, external APIs)
- Azure Monitor integration
- Grafana/Loki integration

### 6. Testing

Add tests covering:
- Basic logging functionality
- Job status/progress logging
- Trace correlation
- OTLP export (mock)
- Error handling

### 7. Submit Pull Request

Once complete, submit a PR with:
- Implementation code
- Tests
- Documentation
- Examples
- Update main README.md to show language as "✅ Available"

---

## Questions?

- **GitHub Issues**: [https://github.com/norwegianredcross/sovdev-logger/issues](https://github.com/norwegianredcross/sovdev-logger/issues)
- **Discussions**: Use GitHub Discussions for questions and ideas

---

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
