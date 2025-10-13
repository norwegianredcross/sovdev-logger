# Python OpenTelemetry and Logging Library Research

**Date**: 2025-10-12
**Purpose**: Research how professional Python developers use OpenTelemetry SDK and select logging libraries
**Context**: Preparing for sovdev-logger Python implementation

---

## Executive Summary

### Key Findings

1. **OpenTelemetry Python SDK** (v1.37.0, latest as of Sept 2025)
   - Well-established with comprehensive documentation
   - Requires Python 3.9+ officially
   - Provides `LoggerProvider`, `MeterProvider`, `TracerProvider`
   - Integrates seamlessly with Python's stdlib logging via `LoggingHandler`

2. **Logging Library Selection** (Winston equivalent)
   - **Winner for sovdev-logger**: **Python stdlib logging + python-json-logger**
   - **Alternative**: structlog (more powerful but more complex)
   - **Not recommended**: loguru (incompatible philosophy with our needs)

3. **Integration Pattern**
   - Use stdlib `logging` with `RotatingFileHandler` for file output
   - Use `python-json-logger` for JSON formatting
   - Use OpenTelemetry `LoggingHandler` for OTLP export
   - Single log call → three outputs (console, file, OTLP)

---

## Part 1: OpenTelemetry Python SDK

### Installation

Professional Python developers install OpenTelemetry with:

```bash
# Core packages
pip install opentelemetry-api==1.27.0
pip install opentelemetry-sdk==1.27.0

# OTLP exporter (HTTP recommended for simplicity)
pip install opentelemetry-exporter-otlp-proto-http==1.27.0

# Alternative: gRPC exporter (better performance, more complex)
pip install opentelemetry-exporter-otlp-proto-grpc==1.27.0
```

**Key packages:**
- `opentelemetry-api`: Core API interfaces
- `opentelemetry-sdk`: Implementation (providers, processors, exporters)
- `opentelemetry-exporter-otlp-proto-http`: OTLP HTTP exporter

### Python Version Support

- **Official**: Python 3.9+
- **Practical**: Python 3.8 works but lacks some features
- **Recommendation for sovdev-logger**: Python 3.8+ (broader compatibility)

---

## Part 2: Provider Initialization Patterns

### Complete Setup Pattern (All Three Providers)

Professional Python developers initialize all three providers together:

```python
from opentelemetry import trace, metrics
from opentelemetry._logs import set_logger_provider
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
import logging

def initialize_opentelemetry(service_name: str, service_version: str):
    """Initialize OpenTelemetry providers for logs, metrics, and traces."""

    # Shared resource for consistent service identification
    resource = Resource.create({
        "service.name": service_name,
        "service.version": service_version,
        "telemetry.sdk.language": "python",
        "telemetry.sdk.name": "opentelemetry",
        "telemetry.sdk.version": "1.27.0"
    })

    # 1. Initialize TracerProvider
    tracer_provider = TracerProvider(resource=resource)
    tracer_provider.add_span_processor(
        BatchSpanProcessor(
            OTLPSpanExporter(
                endpoint=os.getenv('OTEL_EXPORTER_OTLP_TRACES_ENDPOINT'),
                headers=parse_otel_headers()
            )
        )
    )
    trace.set_tracer_provider(tracer_provider)

    # 2. Initialize LoggerProvider
    logger_provider = LoggerProvider(resource=resource)
    logger_provider.add_log_record_processor(
        BatchLogRecordProcessor(
            OTLPLogExporter(
                endpoint=os.getenv('OTEL_EXPORTER_OTLP_LOGS_ENDPOINT'),
                headers=parse_otel_headers()
            )
        )
    )
    set_logger_provider(logger_provider)

    # 3. Initialize MeterProvider
    metric_reader = PeriodicExportingMetricReader(
        OTLPMetricExporter(
            endpoint=os.getenv('OTEL_EXPORTER_OTLP_METRICS_ENDPOINT'),
            headers=parse_otel_headers()
        )
    )
    meter_provider = MeterProvider(
        resource=resource,
        metric_readers=[metric_reader]
    )
    metrics.set_meter_provider(meter_provider)

    return tracer_provider, logger_provider, meter_provider

def parse_otel_headers():
    """Parse OTEL_EXPORTER_OTLP_HEADERS from environment."""
    import json
    headers_str = os.getenv('OTEL_EXPORTER_OTLP_HEADERS', '{}')
    try:
        return json.loads(headers_str)
    except json.JSONDecodeError:
        return {}
```

### Key Observations

1. **Resource Sharing**: All three providers share the same `Resource` object
2. **Batch Processing**: Logs and traces use batch processors for efficiency
3. **Periodic Export**: Metrics use `PeriodicExportingMetricReader` (default 60s interval)
4. **Global State**: Providers are set globally via `set_*_provider()` functions
5. **Endpoint Configuration**: Each provider can have separate OTLP endpoints

---

## Part 3: OpenTelemetry LoggingHandler Integration

### How Professional Python Developers Integrate OTLP Logging

The standard pattern is to **attach OpenTelemetry LoggingHandler to Python's logging system**:

```python
import logging
from opentelemetry._logs import set_logger_provider
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
from opentelemetry.sdk.resources import Resource

# Create LoggerProvider
logger_provider = LoggerProvider(
    resource=Resource.create({
        "service.name": "my-service",
        "service.version": "1.0.0"
    })
)

# Add OTLP exporter
logger_provider.add_log_record_processor(
    BatchLogRecordProcessor(OTLPLogExporter())
)

# Set global provider
set_logger_provider(logger_provider)

# Attach to Python logging
handler = LoggingHandler(
    level=logging.NOTSET,  # Capture all levels
    logger_provider=logger_provider
)

# Add to root logger (affects all loggers)
logging.getLogger().addHandler(handler)

# Now any logging call exports to OTLP
logger = logging.getLogger(__name__)
logger.info("This goes to OTLP!")
```

### Key Advantages

1. **Zero code changes**: Existing `logging.info()` calls work automatically
2. **Automatic trace context**: OpenTelemetry injects trace_id and span_id into logs
3. **Multiple handlers**: Can have file handler + OTLP handler simultaneously
4. **Standard library**: No additional logging library needed

---

## Part 4: Python Logging Library Selection

### The Question: What is Python's Winston?

**Context**: Winston (TypeScript/Node.js) provides:
- Structured logging
- Multiple transports (console, file, HTTP)
- JSON output
- File rotation
- Log levels
- Formatters

### Python Options Analysis

#### Option 1: **Python stdlib logging** (Built-in)

**Pros:**
- ✅ Built into Python (no dependency)
- ✅ Battle-tested since Python 2.3
- ✅ Comprehensive handler ecosystem (RotatingFileHandler, etc.)
- ✅ All Python developers know it
- ✅ OpenTelemetry `LoggingHandler` designed for it

**Cons:**
- ❌ No built-in JSON output (need `python-json-logger`)
- ❌ Verbose configuration
- ❌ Not designed for structured logging

**Verdict**: **Best match for sovdev-logger requirements**

---

#### Option 2: **python-json-logger** (Adds JSON to stdlib)

**Installation:**
```bash
pip install python-json-logger
```

**Usage:**
```python
from pythonjsonlogger import jsonlogger
import logging

logHandler = logging.FileHandler('dev.log')
formatter = jsonlogger.JsonFormatter()
logHandler.setFormatter(formatter)

logger = logging.getLogger()
logger.addHandler(logHandler)

# Outputs JSON
logger.info("test message", extra={"trace_id": "abc123", "user_id": 42})
```

**Output:**
```json
{"message": "test message", "trace_id": "abc123", "user_id": 42, "timestamp": "2025-10-12T10:30:00"}
```

**Verdict**: **Perfect complement to stdlib logging for sovdev-logger**

---

#### Option 3: **structlog** (Structured logging library)

**GitHub Stars**: 3.5k
**Popularity**: Medium-high
**Philosophy**: "Everything is about functions that take and return dictionaries"

**Pros:**
- ✅ Designed specifically for structured logging
- ✅ Very flexible (can wrap stdlib logging or work independently)
- ✅ Excellent performance
- ✅ Context binding built-in
- ✅ Production-proven since 2013
- ✅ OpenTelemetry integration

**Cons:**
- ❌ Steeper learning curve
- ❌ More complex configuration
- ❌ Requires understanding processors and context vars

**Example:**
```python
import structlog

structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ]
)

log = structlog.get_logger()
log.info("user logged in", user_id=42, trace_id="abc123")
```

**Output:**
```json
{"event": "user logged in", "user_id": 42, "trace_id": "abc123", "timestamp": "2025-10-12T10:30:00", "level": "info"}
```

**Verdict**: **Powerful but over-engineered for sovdev-logger's needs**

---

#### Option 4: **loguru** (Simple logging library)

**GitHub Stars**: 15k+
**Popularity**: Highest
**Philosophy**: "Python logging made stupidly simple"

**Pros:**
- ✅ Extremely easy to use
- ✅ One-line setup: `from loguru import logger`
- ✅ Built-in rotation, retention, compression
- ✅ Colorized console output
- ✅ JSON serialization support
- ✅ Context binding

**Cons:**
- ❌ **CRITICAL**: Not compatible with OpenTelemetry `LoggingHandler`
- ❌ Uses own logger (not stdlib), requires adapter
- ❌ Pre-configured (less control)
- ❌ Global singleton logger (conflicts with our design)

**Example:**
```python
from loguru import logger

# Pre-configured, works immediately
logger.info("It just works!")

# Add file with rotation
logger.add("file_{time}.log", rotation="500 MB")

# JSON output
logger.add("file.log", serialize=True)
```

**Verdict**: **NOT SUITABLE for sovdev-logger** (incompatible with OpenTelemetry integration)

---

### Comparison Table

| Feature | stdlib logging | python-json-logger | structlog | loguru |
|---------|---------------|-------------------|-----------|--------|
| **Built-in** | ✅ Yes | ❌ No | ❌ No | ❌ No |
| **OTEL Integration** | ✅ Native | ✅ Via stdlib | ⚠️ Requires adapter | ❌ Difficult |
| **JSON Output** | ⚠️ Via formatter | ✅ Yes | ✅ Yes | ✅ Yes |
| **File Rotation** | ✅ RotatingFileHandler | ✅ Via stdlib | ✅ Via stdlib | ✅ Built-in |
| **Structured Logging** | ⚠️ Via extra= | ✅ Yes | ✅ Yes | ✅ Yes |
| **Complexity** | Medium | Low | High | Very Low |
| **Control** | High | High | Very High | Low |
| **Learning Curve** | Flat (known) | Flat | Steep | Flat |
| **sovdev-logger Fit** | ✅ Excellent | ✅ Perfect | ⚠️ Overkill | ❌ Poor |

---

## Part 5: Recommended Architecture for sovdev-logger Python

### Decision: **stdlib logging + python-json-logger**

**Rationale:**
1. ✅ **OpenTelemetry compatibility**: `LoggingHandler` is designed for stdlib logging
2. ✅ **Zero learning curve**: All Python developers know stdlib logging
3. ✅ **Battle-tested**: Used in production for decades
4. ✅ **File rotation**: `RotatingFileHandler` is robust and well-documented
5. ✅ **JSON output**: `python-json-logger` adds structured logging
6. ✅ **Multiple transports**: Easy to add multiple handlers (file, console, OTLP)
7. ✅ **Consistent with specification**: Matches "use established libraries" principle

### Architecture Diagram

```
sovdev_log() call
      |
      ├─> Python stdlib logger.info()
      |         |
      |         ├─> Console Handler (pretty format for dev)
      |         ├─> File Handler (JSON format via python-json-logger)
      |         └─> OTLP Handler (OpenTelemetry LoggingHandler → Loki)
      |
      └─> Create span (OpenTelemetry tracer → Tempo)
```

### Complete Implementation Pattern

```python
import logging
from logging.handlers import RotatingFileHandler
from pythonjsonlogger import jsonlogger
from opentelemetry._logs import set_logger_provider
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry import trace
import json
import os

class SovdevLogger:
    """Python implementation of sovdev-logger."""

    def __init__(self):
        self._service_name = None
        self._service_version = None
        self._session_id = None
        self._peer_services = {}
        self._file_logger = None
        self._console_logger = None
        self._otlp_logger_provider = None
        self._tracer = None

    def initialize(
        self,
        service_name: str,
        service_version: str = "1.0.0",
        peer_services: dict = None
    ):
        """Initialize sovdev-logger with service information."""
        self._service_name = service_name
        self._service_version = service_version
        self._session_id = str(uuid.uuid4())
        self._peer_services = peer_services or {}

        # Create resource
        resource = Resource.create({
            "service.name": service_name,
            "service.version": service_version,
            "telemetry.sdk.language": "python"
        })

        # Initialize OpenTelemetry LoggerProvider
        self._otlp_logger_provider = LoggerProvider(resource=resource)
        self._otlp_logger_provider.add_log_record_processor(
            BatchLogRecordProcessor(
                OTLPLogExporter(
                    endpoint=os.getenv('OTEL_EXPORTER_OTLP_LOGS_ENDPOINT'),
                    headers=self._parse_otel_headers()
                )
            )
        )
        set_logger_provider(self._otlp_logger_provider)

        # Initialize TracerProvider
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

        tracer_provider = TracerProvider(resource=resource)
        tracer_provider.add_span_processor(
            BatchSpanProcessor(
                OTLPSpanExporter(
                    endpoint=os.getenv('OTEL_EXPORTER_OTLP_TRACES_ENDPOINT'),
                    headers=self._parse_otel_headers()
                )
            )
        )
        trace.set_tracer_provider(tracer_provider)
        self._tracer = trace.get_tracer(service_name, service_version)

        # Set up Python stdlib logging with three handlers
        self._setup_logging()

    def _setup_logging(self):
        """Configure Python logging with console, file, and OTLP handlers."""

        # Create base logger
        logger = logging.getLogger(self._service_name)
        logger.setLevel(logging.DEBUG)
        logger.handlers.clear()  # Remove any existing handlers

        # 1. Console Handler (human-readable, colored for dev)
        if os.getenv('LOG_TO_CONSOLE', 'true').lower() == 'true':
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.DEBUG)
            console_formatter = logging.Formatter(
                '%(asctime)s [%(levelname)s] %(name)s - %(message)s'
            )
            console_handler.setFormatter(console_formatter)
            logger.addHandler(console_handler)

        # 2. File Handler (JSON format, rotating)
        if os.getenv('LOG_TO_FILE', 'true').lower() == 'true':
            file_handler = RotatingFileHandler(
                'dev.log',
                maxBytes=50 * 1024 * 1024,  # 50 MB
                backupCount=5
            )
            file_handler.setLevel(logging.DEBUG)

            # Use python-json-logger for JSON formatting
            json_formatter = jsonlogger.JsonFormatter(
                '%(timestamp)s %(level)s %(name)s %(message)s',
                rename_fields={
                    'levelname': 'level',
                    'name': 'logger',
                    'asctime': 'timestamp'
                }
            )
            file_handler.setFormatter(json_formatter)
            logger.addHandler(file_handler)

        # 3. OTLP Handler (exports to Loki via OpenTelemetry)
        otlp_handler = LoggingHandler(
            level=logging.NOTSET,
            logger_provider=self._otlp_logger_provider
        )
        logger.addHandler(otlp_handler)

        self._file_logger = logger

    def log(
        self,
        level: str,
        function_name: str,
        message: str,
        peer_service: str,
        input_json=None,
        response_json=None,
        exception=None,
        trace_id=None
    ):
        """Log a transaction with automatic span creation."""

        # Generate IDs
        event_id = str(uuid.uuid4())
        if trace_id is None:
            trace_id = str(uuid.uuid4())

        # Resolve peer_service
        resolved_peer_service = self._peer_services.get(
            peer_service,
            peer_service
        )

        # Serialize JSON
        input_json_str = self._serialize_json(input_json)
        response_json_str = self._serialize_json(response_json)

        # Build structured log entry
        log_entry = {
            'service_name': self._service_name,
            'service_version': self._service_version,
            'session_id': self._session_id,
            'peer_service': resolved_peer_service,
            'function_name': function_name,
            'log_type': 'transaction',
            'message': message,
            'trace_id': trace_id,
            'event_id': event_id,
            'input_json': input_json_str,
            'response_json': response_json_str
        }

        # Add exception fields if present
        if exception:
            exception_details = self._process_exception(exception)
            log_entry.update(exception_details)

        # Create span
        with self._tracer.start_as_current_span(
            function_name,
            attributes={
                'service.name': self._service_name,
                'peer.service': resolved_peer_service,
                'function.name': function_name,
                'trace.id': trace_id,
                'event.id': event_id
            }
        ) as span:
            # Log via Python stdlib (goes to all handlers)
            log_level = getattr(logging, level.upper(), logging.INFO)
            self._file_logger.log(
                log_level,
                message,
                extra=log_entry  # All fields added as extra
            )

            # Set span status
            if exception or level in ('error', 'fatal'):
                from opentelemetry.trace import StatusCode
                span.set_status(StatusCode.ERROR, message)

    def _serialize_json(self, obj):
        """Serialize object to JSON string."""
        if obj is None:
            return "null"
        try:
            return json.dumps(obj, ensure_ascii=False)
        except (TypeError, ValueError):
            return "[Serialization Error]"

    def _process_exception(self, error):
        """Process exception for logging."""
        import traceback

        # Extract stack trace
        raw_stack = ''.join(traceback.format_exception(
            type(error), error, error.__traceback__
        ))

        # Remove credentials
        clean_stack = self._remove_credentials(raw_stack)

        # Limit to 350 characters
        limited_stack = clean_stack[:350]

        return {
            'exception_type': 'Error',  # Standardized
            'exception_message': str(error),
            'exception_stack': limited_stack
        }

    def _remove_credentials(self, text):
        """Remove sensitive credentials from text."""
        import re

        patterns = [
            (r'Authorization[:\s]+[^\s,}]+', 'Authorization: [REDACTED]'),
            (r'Bearer\s+[A-Za-z0-9\-._~+/]+=*', 'Bearer [REDACTED]'),
            (r'api[-_]?key[:\s=]+[^\s,}]+', 'api_key=[REDACTED]'),
            (r'password[:\s=]+[^\s,}]+', 'password=[REDACTED]')
        ]

        result = text
        for pattern, replacement in patterns:
            result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)

        return result

    def _parse_otel_headers(self):
        """Parse OTEL_EXPORTER_OTLP_HEADERS from environment."""
        headers_str = os.getenv('OTEL_EXPORTER_OTLP_HEADERS', '{}')
        try:
            return json.loads(headers_str)
        except json.JSONDecodeError:
            return {}

    def flush(self):
        """Flush all pending logs and traces."""
        # Flush OpenTelemetry providers
        if self._otlp_logger_provider:
            self._otlp_logger_provider.force_flush()

        # Flush stdlib logging handlers
        for handler in self._file_logger.handlers:
            handler.flush()

# Global instance (module-level pattern)
_logger_instance = None

def sovdev_initialize(service_name, service_version="1.0.0", peer_services=None):
    """Initialize sovdev-logger."""
    global _logger_instance
    _logger_instance = SovdevLogger()
    _logger_instance.initialize(service_name, service_version, peer_services)

def sovdev_log(level, function_name, message, peer_service,
               input_json=None, response_json=None, exception=None, trace_id=None):
    """Log a transaction."""
    if _logger_instance is None:
        raise RuntimeError("Must call sovdev_initialize() first")
    _logger_instance.log(
        level, function_name, message, peer_service,
        input_json, response_json, exception, trace_id
    )

def sovdev_flush():
    """Flush all pending logs."""
    if _logger_instance:
        _logger_instance.flush()
```

---

## Part 6: File Rotation with RotatingFileHandler

### How Professional Python Developers Use It

```python
from logging.handlers import RotatingFileHandler
import logging

# Create rotating file handler
handler = RotatingFileHandler(
    filename='dev.log',
    maxBytes=50 * 1024 * 1024,  # 50 MB per file
    backupCount=5,  # Keep 5 backup files (total 250 MB)
    encoding='utf-8'
)

# Set formatter
formatter = logging.Formatter('%(asctime)s - %(message)s')
handler.setFormatter(formatter)

# Add to logger
logger = logging.getLogger('my-app')
logger.addHandler(handler)
```

### How Rotation Works

1. Log writes to `dev.log`
2. When `dev.log` reaches 50 MB:
   - `dev.log` → `dev.log.1`
   - `dev.log.1` → `dev.log.2`
   - `dev.log.2` → `dev.log.3`
   - `dev.log.3` → `dev.log.4`
   - `dev.log.4` → `dev.log.5`
   - `dev.log.5` is deleted
   - New `dev.log` created
3. Total disk usage: ~250 MB maximum

### Key Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `maxBytes` | int | Max file size in bytes | `50 * 1024 * 1024` (50 MB) |
| `backupCount` | int | Number of backup files | `5` |
| `encoding` | str | File encoding | `'utf-8'` |

**Note**: If `maxBytes=0` or `backupCount=0`, rotation is disabled.

---

## Part 7: Synchronous vs Asynchronous Flush

### OpenTelemetry Provider Flush Pattern

OpenTelemetry providers have `force_flush()` methods that are **synchronous by default**:

```python
from opentelemetry._logs import get_logger_provider
from opentelemetry.trace import get_tracer_provider
from opentelemetry.metrics import get_meter_provider

def sovdev_flush():
    """Flush all OpenTelemetry providers (synchronous)."""

    # Flush logs (blocks until complete or timeout)
    logger_provider = get_logger_provider()
    logger_provider.force_flush(timeout_millis=30000)  # 30 second timeout

    # Flush traces
    tracer_provider = get_tracer_provider()
    tracer_provider.force_flush(timeout_millis=30000)

    # Flush metrics
    meter_provider = get_meter_provider()
    meter_provider.force_flush(timeout_millis=30000)
```

### Key Observation

✅ **OpenTelemetry Python uses SYNCHRONOUS flush by default**

This is different from TypeScript where flush is async. For Python:
- `force_flush()` blocks the calling thread
- Returns `True` if successful, `False` if timeout
- Default timeout is 30 seconds
- Safe to call in signal handlers and exit handlers

### Recommended sovdev_flush Implementation

```python
def sovdev_flush():
    """
    Flush all pending logs, metrics, and traces.

    Blocks until all data is exported or timeout occurs.
    Safe to call from signal handlers and atexit.
    """
    from opentelemetry._logs import get_logger_provider
    from opentelemetry.trace import get_tracer_provider
    from opentelemetry.metrics import get_meter_provider
    import logging

    # Flush OpenTelemetry providers
    get_logger_provider().force_flush(timeout_millis=30000)
    get_tracer_provider().force_flush(timeout_millis=30000)
    get_meter_provider().force_flush(timeout_millis=30000)

    # Flush stdlib logging handlers
    for handler in logging.getLogger().handlers:
        handler.flush()
```

**Usage in signal handlers:**
```python
import signal
import atexit

# Register flush on exit
atexit.register(sovdev_flush)

# Register flush on signals
def signal_handler(signum, frame):
    sovdev_flush()  # Synchronous - safe to call here
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)
```

---

## Part 8: Dependencies and Requirements

### Required Packages for sovdev-logger Python

```txt
# requirements.txt

# OpenTelemetry core
opentelemetry-api>=1.27.0,<2.0.0
opentelemetry-sdk>=1.27.0,<2.0.0

# OTLP exporters (HTTP recommended)
opentelemetry-exporter-otlp-proto-http>=1.27.0,<2.0.0

# JSON logging
python-json-logger>=2.0.0,<3.0.0

# Type hints for Python < 3.9
typing-extensions>=4.0.0; python_version < "3.9"
```

### Optional Test Dependencies

```txt
# test-requirements.txt

# Testing framework
pytest>=7.4.0
pytest-cov>=4.1.0

# Async testing (if needed)
pytest-asyncio>=0.21.0
```

### Python Version Requirement

```python
# setup.py or pyproject.toml
python_requires = ">=3.8"
```

**Recommendation**: Support Python 3.8+ for broader compatibility

---

## Part 9: Summary and Recommendations

### Key Decisions for sovdev-logger Python

1. **Logging Library**: ✅ Python stdlib `logging` + `python-json-logger`
   - Reason: Best OpenTelemetry integration, familiar to all Python developers

2. **OpenTelemetry Integration**: ✅ Use `LoggingHandler`
   - Reason: Zero-friction integration with stdlib logging

3. **File Rotation**: ✅ Use `RotatingFileHandler`
   - Reason: Built-in, reliable, well-documented

4. **Flush Pattern**: ✅ Synchronous `sovdev_flush()`
   - Reason: OpenTelemetry Python uses sync by default, safe in signal handlers

5. **Architecture**: ✅ Module-level functions with global instance
   - Reason: Matches TypeScript pattern, simple API

### Implementation Effort Estimate

With this research complete:
- **Setup and initialization**: 2 hours
- **Core logging implementation**: 2-3 hours
- **Exception handling**: 1 hour
- **Testing**: 2 hours
- **Documentation**: 1 hour

**Total**: 8-9 hours (matches earlier estimate)

### Confidence Level

**95%** - This architecture is proven and follows Python best practices

---

## Part 10: Comparison to TypeScript Winston

### What TypeScript sovdev-logger Uses

- **Winston**: Feature-rich logging library
  - Multiple transports
  - JSON formatting
  - File rotation
  - Custom formatters

### What Python sovdev-logger Will Use

- **stdlib logging**: Core logging infrastructure
- **python-json-logger**: JSON formatting (equivalent to Winston JSON formatter)
- **RotatingFileHandler**: File rotation (equivalent to Winston rotation)
- **LoggingHandler**: OTLP transport (equivalent to custom Winston transport)

### Feature Parity

| Feature | TypeScript (Winston) | Python (stdlib logging) |
|---------|---------------------|------------------------|
| Multiple transports | ✅ Winston transports | ✅ Multiple handlers |
| JSON output | ✅ Winston format | ✅ python-json-logger |
| File rotation | ✅ winston-daily-rotate | ✅ RotatingFileHandler |
| Console output | ✅ Winston console | ✅ StreamHandler |
| OTLP export | ✅ Custom transport | ✅ LoggingHandler |
| Log levels | ✅ Winston levels | ✅ logging levels |
| Structured logging | ✅ Winston metadata | ✅ extra= parameter |

**Verdict**: ✅ **Full feature parity achieved with stdlib logging**

---

## Appendix: Additional Resources

### Official Documentation

- **OpenTelemetry Python**: https://opentelemetry.io/docs/languages/python/
- **Python logging**: https://docs.python.org/3/library/logging.html
- **python-json-logger**: https://github.com/madzak/python-json-logger
- **structlog**: https://www.structlog.org/

### Community Resources

- **Better Stack Python Logging Guide**: https://betterstack.com/community/guides/logging/
- **Real Python Logging Tutorial**: https://realpython.com/python-logging/

---

**Research completed**: 2025-10-12
**Ready for Python implementation**: ✅ YES
**Confidence level**: 95%
**Next step**: Begin Python implementation with clear understanding of ecosystem
