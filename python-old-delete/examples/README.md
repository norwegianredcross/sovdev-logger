# sovdev-logger Examples

This directory contains real-world usage examples of the sovdev-logger library.

## What are Examples?

Examples are **copy-pasteable starter code** showing how to integrate sovdev-logger into your applications. They demonstrate common use cases and best practices.

## Installation

After the library is published to PyPI, install it with:

```bash
pip install sovdev-logger
```

For now (development), examples use the local source via `pip install -e ../..`.

## Available Examples

### 01. Basic Usage (`basic/`)

**What it shows:**
- Minimal setup to get started
- Simple initialization with `sovdev_initialize()`
- Basic logging with different log levels
- Console and file output

**Run it:**
```bash
cd examples/basic
python simple_logging.py
```

**When to use:**
- Your first time using sovdev-logger
- Simple console applications
- Quick prototyping

---

### Future Examples (To Be Added)

#### 02. Peer Services - Coming Soon

**What it will show:**
- Creating peer service mappings with `create_peer_services()`
- Tracking calls to external systems (APIs, databases)
- Using CMDB system IDs for correlation
- Distinguishing internal vs external operations

**Use case:** Microservices calling external systems

---

#### 03. FastAPI Integration - Coming Soon

**What it will show:**
- Integration with FastAPI
- Request/response logging middleware
- Automatic trace_id propagation
- Error handling

**Use case:** REST API services

---

#### 04. Batch Job Processing - Coming Soon

**What it will show:**
- Job lifecycle logging (Started, Progress, Completed)
- Progress tracking
- Error handling in batch operations
- Dual trace_id strategy (batch-level + item-level)

**Use case:** ETL jobs, data processing pipelines

---

#### 05. OTLP Integration - Coming Soon

**What it will show:**
- Configuring OTLP endpoints
- Environment variable setup
- Sending logs to Grafana Cloud / Azure Application Insights
- Verifying logs in observability platform

**Use case:** Production deployments with centralized logging

---

## Example Structure

Each example follows this structure:

```
examples/basic/
├── README.md              # Detailed explanation
├── requirements.txt       # Dependencies (or -e ../..)
├── .env.example           # Environment variables template
└── simple_logging.py      # Main example code
```

## Running Examples

### During Development (before PyPI publish)

Examples use local source code:

```bash
cd examples/basic
pip install -e ../..    # Install sovdev-logger from parent directory
python simple_logging.py
```

### After Publishing to PyPI

Users will install from PyPI:

```bash
mkdir my-project
cd my-project
pip install sovdev-logger
# Copy example code from docs
python app.py
```

## Difference from Tests

| Examples | Tests (test/e2e/) |
|----------|-------------------|
| Show **how to use** the library | Verify the library **works correctly** |
| Copy-paste starter code | Automated verification |
| Minimal, focused code | Comprehensive scenarios |
| Always use published package (or editable install during dev) | Always use local source |
| User-facing documentation | Developer tool |

**Examples** are for users learning the library.
**Tests** are for developers verifying the library.

## Best Practices for Examples

### Keep them Simple

✅ **Good Example:**
```python
from sovdev_logger import sovdev_initialize, sovdev_log, SOVDEV_LOG_LEVELS

sovdev_initialize('my-app')
sovdev_log(SOVDEV_LOG_LEVELS.INFO, 'main', 'Application started', None, None)
```

❌ **Bad Example** (too complex):
```python
# Don't: Add complex business logic, error handling, etc.
# Examples should be minimal and focused
```

### Include README.md

Every example should have a README explaining:
1. **What it demonstrates**
2. **How to run it**
3. **What output to expect**
4. **When to use this pattern**

### Use .env.example

Show users what environment variables are needed:

```bash
# .env.example
LOG_TO_CONSOLE=true
LOG_TO_FILE=true
SYSTEM_ID=my-app
```

### Keep Dependencies Minimal

Only include packages required for the example:
- ✅ `sovdev-logger` (the library)
- ✅ `fastapi` (if showing FastAPI integration)
- ❌ Don't add testing frameworks, linters, etc.

## Adding a New Example

1. **Create directory:**
   ```bash
   mkdir examples/my-new-example
   cd examples/my-new-example
   ```

2. **Create requirements.txt or use editable install:**
   ```bash
   # For development
   pip install -e ../..

   # Or create requirements.txt for published version
   echo "sovdev-logger>=1.0.0" > requirements.txt
   ```

3. **Create example.py** with focused example code

4. **Create README.md** explaining the example

5. **Create .env.example** with required environment variables

6. **Test it:**
   ```bash
   python example.py
   ```

7. **Update this README** to list your new example

## Documentation

Examples should be referenced in the main documentation:

- **python/README.md** - Links to examples for quick start
- **docs/README-configuration.md** - References examples for configuration patterns

## Getting Help

If an example doesn't work:
1. Check the example's README.md for prerequisites
2. Verify you installed the library (`pip install -e ../..` or `pip install sovdev-logger`)
3. Check environment variables in .env.example
4. Review the main sovdev-logger documentation
5. Open an issue on GitHub

## Contributing

To contribute a new example:
1. Follow the structure above
2. Keep it simple and focused
3. Test it thoroughly
4. Document it well
5. Submit a pull request
