# Python Implementation Guide for sovdev-logger

**Version**: 1.0.0
**Date**: 2025-10-12
**Status**: Ready for Implementation
**Target Python Version**: 3.8+

---

## Table of Contents

1. [Overview](#overview)
2. [Dependencies](#dependencies)
3. [Architecture](#architecture)
4. [OpenTelemetry Integration](#opentelemetry-integration)
5. [Logging Library Selection](#logging-library-selection)
6. [API Signatures](#api-signatures)
7. [Module Structure](#module-structure)
8. [Implementation Patterns](#implementation-patterns)
9. [File Rotation](#file-rotation)
10. [Exception Handling](#exception-handling)
11. [Testing](#testing)
12. [Complete Example](#complete-example)

---

## Overview

### Goal

Implement a Python version of sovdev-logger that:
- ✅ Matches TypeScript functionality exactly
- ✅ Follows Python best practices
- ✅ Integrates with OpenTelemetry Python SDK
- ✅ Uses stdlib logging (not custom implementation)
- ✅ Provides synchronous API (no asyncio required)

### Key Differences from TypeScript

| Aspect | TypeScript | Python |
|--------|-----------|--------|
| **Logging library** | Winston | stdlib logging + python-json-logger |
| **Flush pattern** | async/await | Synchronous (blocks) |
| **File rotation** | winston-daily-rotate | RotatingFileHandler |
| **Exception type** | Error | BaseException |
| **Naming** | camelCase | snake_case |
| **Module pattern** | exports | Module-level functions |

---

## Dependencies

### Required Packages

```txt
# requirements.txt

# OpenTelemetry core
opentelemetry-api>=1.27.0,<2.0.0
opentelemetry-sdk>=1.27.0,<2.0.0

# OTLP exporter (HTTP recommended)
opentelemetry-exporter-otlp-proto-http>=1.27.0,<2.0.0

# JSON logging for structured output
python-json-logger>=2.0.0,<3.0.0

# Type hints for Python < 3.9
typing-extensions>=4.0.0; python_version < "3.9"
```

### Installation

```bash
pip install -r requirements.txt
```

### Python Version Support

- **Minimum**: Python 3.8
- **Recommended**: Python 3.11+
- **Tested**: 3.8, 3.9, 3.10, 3.11, 3.12

---

## Architecture

### Triple Output Pattern

Every log call produces three outputs simultaneously:

```
sovdev_log() call
      ↓
Python stdlib logger.info()
      ↓
      ├─> Console Handler → stdout (human-readable, colored)
      ├─> File Handler → dev.log (JSON, rotated)
      └─> OTLP Handler → Loki/Grafana (observability)
```

### Benefits

- ✅ Single log call, three destinations
- ✅ No custom file handling code
- ✅ Uses battle-tested stdlib logging
- ✅ OpenTelemetry native integration
- ✅ File rotation built-in

---

## OpenTelemetry Integration

### Provider Initialization

Initialize all three providers (Logs, Metrics, Traces):

```python
from opentelemetry import trace, metrics
from opentelemetry._logs import set_logger_provider
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk._logs import LoggerProvider
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
import os
import json

def initialize_opentelemetry(service_name: str, service_version: str):
    """Initialize OpenTelemetry providers."""

    # Shared resource for all providers
    resource = Resource.create({
        "service.name": service_name,
        "service.version": service_version,
        "telemetry.sdk.language": "python",
        "telemetry.sdk.name": "opentelemetry",
        "telemetry.sdk.version": "1.27.0"
    })

    # Parse OTLP headers from environment
    headers = parse_otel_headers()

    # 1. TracerProvider
    tracer_provider = TracerProvider(resource=resource)
    tracer_provider.add_span_processor(
        BatchSpanProcessor(
            OTLPSpanExporter(
                endpoint=os.getenv('OTEL_EXPORTER_OTLP_TRACES_ENDPOINT'),
                headers=headers
            )
        )
    )
    trace.set_tracer_provider(tracer_provider)

    # 2. LoggerProvider
    logger_provider = LoggerProvider(resource=resource)
    logger_provider.add_log_record_processor(
        BatchLogRecordProcessor(
            OTLPLogExporter(
                endpoint=os.getenv('OTEL_EXPORTER_OTLP_LOGS_ENDPOINT'),
                headers=headers
            )
        )
    )
    set_logger_provider(logger_provider)

    # 3. MeterProvider
    metric_reader = PeriodicExportingMetricReader(
        OTLPMetricExporter(
            endpoint=os.getenv('OTEL_EXPORTER_OTLP_METRICS_ENDPOINT'),
            headers=headers
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
    headers_str = os.getenv('OTEL_EXPORTER_OTLP_HEADERS', '{}')
    try:
        return json.loads(headers_str)
    except json.JSONDecodeError:
        return {}
```

### Key Points

- **Resource sharing**: All three providers use the same Resource object
- **Batch processing**: Logs and traces use batch processors (efficiency)
- **Periodic export**: Metrics exported every 60 seconds by default
- **Endpoint configuration**: Each provider can have separate OTLP endpoint

---

## Logging Library Selection

### Decision: stdlib logging + python-json-logger

**Rationale:**
1. ✅ OpenTelemetry LoggingHandler designed for stdlib logging
2. ✅ Every Python developer knows stdlib logging
3. ✅ RotatingFileHandler for file rotation
4. ✅ python-json-logger adds JSON formatting
5. ✅ Multiple handlers (console, file, OTLP) work simultaneously

### Setup Pattern

```python
import logging
from logging.handlers import RotatingFileHandler
from pythonjsonlogger import jsonlogger
from opentelemetry.sdk._logs import LoggingHandler
import os

def setup_logging(service_name: str, logger_provider):
    """Configure stdlib logging with three handlers."""

    logger = logging.getLogger(service_name)
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()

    # 1. Console Handler (human-readable)
    if os.getenv('LOG_TO_CONSOLE', 'true').lower() == 'true':
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(
            logging.Formatter('%(asctime)s [%(levelname)s] %(name)s - %(message)s')
        )
        logger.addHandler(console_handler)

    # 2. File Handler (JSON with rotation)
    if os.getenv('LOG_TO_FILE', 'true').lower() == 'true':
        file_handler = RotatingFileHandler(
            'dev.log',
            maxBytes=50 * 1024 * 1024,  # 50 MB
            backupCount=5
        )
        file_handler.setFormatter(jsonlogger.JsonFormatter())
        logger.addHandler(file_handler)

    # 3. OTLP Handler (OpenTelemetry)
    otlp_handler = LoggingHandler(
        level=logging.NOTSET,
        logger_provider=logger_provider
    )
    logger.addHandler(otlp_handler)

    return logger
```

---

## API Signatures

### sovdev_initialize

```python
from typing import Optional, Dict

def sovdev_initialize(
    service_name: str,
    service_version: str = "1.0.0",
    peer_services: Optional[Dict[str, str]] = None
) -> None:
    """
    Initialize the sovdev-logger.

    Args:
        service_name: Service identifier (from SYSTEM_ID env var)
        service_version: Service version (defaults to "1.0.0")
        peer_services: Peer service mapping from create_peer_services()

    Raises:
        ValueError: If service_name is empty

    Example:
        >>> PEER_SERVICES = create_peer_services({'BRREG': 'SYS1234567'})
        >>> sovdev_initialize('my-service', '1.0.0', PEER_SERVICES.mappings)
    """
```

### sovdev_log

```python
from typing import Optional, Any

def sovdev_log(
    level: str,
    function_name: str,
    message: str,
    peer_service: str,
    input_json: Optional[Any] = None,
    response_json: Optional[Any] = None,
    exception: Optional[BaseException] = None,
    trace_id: Optional[str] = None
) -> None:
    """
    Log a transaction with optional input/output and exception.

    Args:
        level: Log level (use SOVDEV_LOGLEVELS or string)
        function_name: Name of the function being logged
        message: Human-readable message
        peer_service: Target system identifier
        input_json: Request data (any JSON-serializable type)
        response_json: Response data (any JSON-serializable type)
        exception: Exception object (if logging error)
        trace_id: UUID for transaction correlation (auto-generated if None)

    Example:
        >>> sovdev_log(
        ...     SOVDEV_LOGLEVELS.INFO,
        ...     'fetch_data',
        ...     'Fetching company data',
        ...     PEER_SERVICES.BRREG,
        ...     input_json={'org_number': '123456789'}
        ... )
    """
```

### sovdev_flush

```python
def sovdev_flush() -> None:
    """
    Flush all pending logs, metrics, and traces.

    Blocks until all data is exported or 30-second timeout occurs.
    Safe to call from signal handlers and atexit hooks.

    Example:
        >>> import atexit
        >>> atexit.register(sovdev_flush)
    """
```

### sovdev_generate_trace_id

```python
def sovdev_generate_trace_id() -> str:
    """
    Generate UUID v4 for trace correlation.

    Returns:
        Lowercase UUID string with hyphens (36 characters)

    Example:
        >>> trace_id = sovdev_generate_trace_id()
        >>> trace_id
        '50ba0e1d-c46d-4dee-98d3-a0d3913f74ee'
    """
```

### create_peer_services

```python
from typing import Dict

class PeerServices:
    """Type-safe peer service constants."""
    mappings: Dict[str, str]
    INTERNAL: str
    # Dynamic attributes for each defined service

def create_peer_services(definitions: Dict[str, str]) -> PeerServices:
    """
    Create peer service mapping with INTERNAL auto-generated.

    Args:
        definitions: Mapping of service names to system IDs

    Returns:
        PeerServices object with attribute access

    Example:
        >>> PEER_SERVICES = create_peer_services({
        ...     'BRREG': 'SYS1234567',
        ...     'ALTINN': 'SYS7654321'
        ... })
        >>> PEER_SERVICES.BRREG  # Returns 'BRREG' (constant name)
        'BRREG'
        >>> PEER_SERVICES.mappings  # Returns full mapping
        {'BRREG': 'SYS1234567', 'ALTINN': 'SYS7654321'}
    """
```

### SOVDEV_LOGLEVELS

```python
from enum import Enum

class SOVDEV_LOGLEVELS(str, Enum):
    """Log levels matching OpenTelemetry severity numbers."""
    TRACE = "trace"
    DEBUG = "debug"
    INFO = "info"
    WARN = "warn"
    ERROR = "error"
    FATAL = "fatal"

# Usage: Both enum and string work
sovdev_log(SOVDEV_LOGLEVELS.INFO, ...)  # Type-safe
sovdev_log("info", ...)  # Also works
```

---

## Module Structure

### Pattern: Module-level Functions

```python
# sovdev_logger/__init__.py

from typing import Optional, Dict, Any
import uuid
import logging
from .logger import SovdevLogger

# Module-level singleton instance (private)
_logger_instance: Optional[SovdevLogger] = None

def sovdev_initialize(
    service_name: str,
    service_version: str = "1.0.0",
    peer_services: Optional[Dict[str, str]] = None
) -> None:
    """Initialize the logger."""
    global _logger_instance

    if _logger_instance is not None:
        # Idempotent: silently ignore subsequent calls
        return

    _logger_instance = SovdevLogger(service_name, service_version, peer_services)

def sovdev_log(
    level: str,
    function_name: str,
    message: str,
    peer_service: str,
    input_json: Optional[Any] = None,
    response_json: Optional[Any] = None,
    exception: Optional[BaseException] = None,
    trace_id: Optional[str] = None
) -> None:
    """Log a transaction."""
    if _logger_instance is None:
        raise RuntimeError("Must call sovdev_initialize() first")
    _logger_instance.log(
        level, function_name, message, peer_service,
        input_json, response_json, exception, trace_id
    )

def sovdev_flush() -> None:
    """Flush all pending logs."""
    if _logger_instance is not None:
        _logger_instance.flush()

def sovdev_generate_trace_id() -> str:
    """Generate UUID v4 for trace correlation."""
    return str(uuid.uuid4()).lower()

# Public API
__all__ = [
    'sovdev_initialize',
    'sovdev_log',
    'sovdev_log_job_status',
    'sovdev_log_job_progress',
    'sovdev_flush',
    'sovdev_generate_trace_id',
    'create_peer_services',
    'SOVDEV_LOGLEVELS'
]
```

### Usage

```python
from sovdev_logger import sovdev_initialize, sovdev_log, SOVDEV_LOGLEVELS

sovdev_initialize("my-service", "1.0.0")
sovdev_log(SOVDEV_LOGLEVELS.INFO, "main", "Application started", "INTERNAL")
```

---

## Implementation Patterns

### create_peer_services Implementation

```python
class PeerServices:
    """Type-safe peer service constants with attribute access."""

    def __init__(self, definitions: Dict[str, str]):
        # Store full mapping
        self.mappings = definitions

        # Create attribute for each service (returns key, not value)
        for service_name in definitions.keys():
            setattr(self, service_name, service_name)

        # Auto-generate INTERNAL
        self.INTERNAL = 'INTERNAL'

def create_peer_services(definitions: Dict[str, str]) -> PeerServices:
    """Create peer service mapping."""
    return PeerServices(definitions)

# Usage
PEER_SERVICES = create_peer_services({
    'BRREG': 'SYS1234567',
    'ALTINN': 'SYS7654321'
})

# Attribute access returns constant name
assert PEER_SERVICES.BRREG == 'BRREG'

# Mappings contain system IDs
assert PEER_SERVICES.mappings['BRREG'] == 'SYS1234567'
```

### Peer Service Resolution

```python
class SovdevLogger:
    def __init__(self, service_name: str, service_version: str, peer_services: Dict[str, str]):
        self._peer_services = peer_services or {}

    def log(self, ..., peer_service: str, ...):
        # Resolve peer_service to system ID if mapping exists
        resolved_peer_service = self._peer_services.get(
            peer_service,  # Key (e.g., 'BRREG')
            peer_service   # Fallback (e.g., 'INTERNAL')
        )

        # Log with resolved system ID
        log_entry = {
            'peer_service': resolved_peer_service,  # 'SYS1234567' or 'INTERNAL'
            ...
        }
```

### JSON Serialization

```python
import json

def serialize_json(obj: Any) -> str:
    """Serialize object to JSON string."""
    if obj is None:
        return "null"  # String "null", not JSON null
    try:
        return json.dumps(obj, ensure_ascii=False)
    except (TypeError, ValueError):
        return "[Serialization Error]"

# Usage
input_json_str = serialize_json({'org_number': '123456789'})
response_json_str = serialize_json(None)  # Returns "null"
```

---

## File Rotation

### RotatingFileHandler Configuration

```python
from logging.handlers import RotatingFileHandler

file_handler = RotatingFileHandler(
    filename='dev.log',
    maxBytes=50 * 1024 * 1024,  # 50 MB per file
    backupCount=5,  # Keep 5 backup files
    encoding='utf-8'
)
```

### Rotation Behavior

1. Logs write to `dev.log`
2. When `dev.log` reaches 50 MB:
   - `dev.log` → `dev.log.1`
   - `dev.log.1` → `dev.log.2`
   - `dev.log.2` → `dev.log.3`
   - `dev.log.3` → `dev.log.4`
   - `dev.log.4` → `dev.log.5`
   - `dev.log.5` deleted
   - New `dev.log` created
3. Total disk usage: ~250 MB maximum

---

## Exception Handling

### Exception Processing

```python
import traceback
import re

def process_exception(error: BaseException) -> dict:
    """Process exception for logging."""

    # Extract raw stack trace
    raw_stack = ''.join(traceback.format_exception(
        type(error), error, error.__traceback__
    ))

    # Remove credentials
    clean_stack = remove_credentials(raw_stack)

    # Limit to 350 characters
    limited_stack = clean_stack[:350]

    return {
        'exception_type': 'Error',  # Always "Error" (standardized)
        'exception_message': str(error),
        'exception_stack': limited_stack
    }

def remove_credentials(text: str) -> str:
    """Remove sensitive credentials from text."""

    patterns = [
        (r'Authorization[:\s]+[^\s,}]+', 'Authorization: [REDACTED]'),
        (r'Bearer\s+[A-Za-z0-9\-._~+/]+=*', 'Bearer [REDACTED]'),
        (r'api[-_]?key[:\s=]+[^\s,}]+', 'api_key=[REDACTED]'),
        (r'password[:\s=]+[^\s,}]+', 'password=[REDACTED]'),
        (r'pwd[:\s=]+[^\s,}]+', 'pwd=[REDACTED]'),
        (r'token[:\s=]+[^\s,}]+', 'token=[REDACTED]')
    ]

    result = text
    for pattern, replacement in patterns:
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)

    return result
```

### Exception Types

```python
# Python has BaseException (top level) and Exception (standard errors)
# Use BaseException to catch all (including SystemExit, KeyboardInterrupt)

try:
    # Code that may raise
    pass
except BaseException as e:
    sovdev_log(
        SOVDEV_LOGLEVELS.ERROR,
        'my_function',
        'Operation failed',
        PEER_SERVICES.INTERNAL,
        exception=e  # Pass exception object
    )
```

---

## Testing

**Complete test documentation**: See `specification/06-test-scenarios.md` for all 11 test scenarios and validation process.

This section provides Python-specific test code examples.

### Test Structure

```
sovdev-logger/
├── python/
│   ├── sovdev_logger/
│   │   ├── __init__.py
│   │   ├── logger.py
│   │   └── ...
│   └── test/
│       ├── unit/
│       │   ├── test_logger.py
│       │   └── test_utils.py
│       └── e2e/
│           └── company-lookup/
│               ├── company_lookup.py
│               ├── .env
│               └── run-test.sh
```

### E2E Test Example

```python
# test/e2e/company-lookup/company_lookup.py

import sys
import os

# Add parent to path
sys.path.insert(0, os.path.abspath('../../..'))

from sovdev_logger import (
    sovdev_initialize,
    sovdev_log,
    sovdev_flush,
    sovdev_generate_trace_id,
    create_peer_services,
    SOVDEV_LOGLEVELS
)

def main():
    """Run E2E test."""

    # Define peer services
    PEER_SERVICES = create_peer_services({
        'BRREG': 'SYS1234567',
        'ALTINN': 'SYS7654321'
    })

    # Initialize
    sovdev_initialize(
        'sovdev-test-company-lookup-python',
        '1.0.0',
        PEER_SERVICES.mappings
    )

    # Test basic log
    FUNCTIONNAME = 'lookupCompany'
    trace_id = sovdev_generate_trace_id()

    input_data = {'organisasjonsnummer': '123456789'}

    sovdev_log(
        SOVDEV_LOGLEVELS.INFO,
        FUNCTIONNAME,
        'Looking up company',
        PEER_SERVICES.BRREG,
        input_json=input_data,
        trace_id=trace_id
    )

    # Simulate response
    response_data = {'navn': 'Acme Corp'}

    sovdev_log(
        SOVDEV_LOGLEVELS.INFO,
        FUNCTIONNAME,
        'Company lookup successful',
        PEER_SERVICES.BRREG,
        input_json=input_data,
        response_json=response_data,
        trace_id=trace_id
    )

    # Flush before exit
    sovdev_flush()

if __name__ == '__main__':
    main()
```

### Running Tests

```bash
# Run E2E test
cd python/test/e2e/company-lookup
./run-test.sh

# Verify logs in Grafana
../../specification/tools/query-loki.sh sovdev-test-company-lookup-python
```

---

## Complete Example

### Full Implementation Skeleton

```python
# sovdev_logger/logger.py

import logging
import uuid
import json
import re
import traceback
import os
from typing import Optional, Dict, Any
from logging.handlers import RotatingFileHandler
from pythonjsonlogger import jsonlogger
from opentelemetry import trace, metrics
from opentelemetry._logs import set_logger_provider, get_logger_provider
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

class SovdevLogger:
    """Python implementation of sovdev-logger."""

    def __init__(
        self,
        service_name: str,
        service_version: str = "1.0.0",
        peer_services: Optional[Dict[str, str]] = None
    ):
        self._service_name = service_name
        self._service_version = service_version
        self._session_id = str(uuid.uuid4())
        self._peer_services = peer_services or {}

        # Initialize OpenTelemetry
        self._init_opentelemetry()

        # Setup logging
        self._logger = self._setup_logging()

    def _init_opentelemetry(self):
        """Initialize OpenTelemetry providers."""

        resource = Resource.create({
            "service.name": self._service_name,
            "service.version": self._service_version,
            "telemetry.sdk.language": "python"
        })

        headers = self._parse_otel_headers()

        # TracerProvider
        tracer_provider = TracerProvider(resource=resource)
        tracer_provider.add_span_processor(
            BatchSpanProcessor(
                OTLPSpanExporter(
                    endpoint=os.getenv('OTEL_EXPORTER_OTLP_TRACES_ENDPOINT'),
                    headers=headers
                )
            )
        )
        trace.set_tracer_provider(tracer_provider)
        self._tracer = trace.get_tracer(self._service_name, self._service_version)

        # LoggerProvider
        self._logger_provider = LoggerProvider(resource=resource)
        self._logger_provider.add_log_record_processor(
            BatchLogRecordProcessor(
                OTLPLogExporter(
                    endpoint=os.getenv('OTEL_EXPORTER_OTLP_LOGS_ENDPOINT'),
                    headers=headers
                )
            )
        )
        set_logger_provider(self._logger_provider)

        # MeterProvider
        metric_reader = PeriodicExportingMetricReader(
            OTLPMetricExporter(
                endpoint=os.getenv('OTEL_EXPORTER_OTLP_METRICS_ENDPOINT'),
                headers=headers
            )
        )
        meter_provider = MeterProvider(
            resource=resource,
            metric_readers=[metric_reader]
        )
        metrics.set_meter_provider(meter_provider)

    def _setup_logging(self) -> logging.Logger:
        """Configure stdlib logging with three handlers."""

        logger = logging.getLogger(self._service_name)
        logger.setLevel(logging.DEBUG)
        logger.handlers.clear()

        # Console handler
        if os.getenv('LOG_TO_CONSOLE', 'true').lower() == 'true':
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(
                logging.Formatter('%(asctime)s [%(levelname)s] %(name)s - %(message)s')
            )
            logger.addHandler(console_handler)

        # File handler (JSON with rotation)
        if os.getenv('LOG_TO_FILE', 'true').lower() == 'true':
            file_handler = RotatingFileHandler(
                'dev.log',
                maxBytes=50 * 1024 * 1024,
                backupCount=5
            )
            file_handler.setFormatter(jsonlogger.JsonFormatter())
            logger.addHandler(file_handler)

        # OTLP handler
        otlp_handler = LoggingHandler(
            level=logging.NOTSET,
            logger_provider=self._logger_provider
        )
        logger.addHandler(otlp_handler)

        return logger

    def log(
        self,
        level: str,
        function_name: str,
        message: str,
        peer_service: str,
        input_json: Optional[Any] = None,
        response_json: Optional[Any] = None,
        exception: Optional[BaseException] = None,
        trace_id: Optional[str] = None
    ):
        """Log a transaction with span creation."""

        # Generate IDs
        event_id = str(uuid.uuid4())
        if trace_id is None:
            trace_id = str(uuid.uuid4())

        # Resolve peer service
        resolved_peer_service = self._peer_services.get(
            peer_service,
            peer_service
        )

        # Serialize JSON
        input_json_str = self._serialize_json(input_json)
        response_json_str = self._serialize_json(response_json)

        # Build log entry
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

        # Add exception fields
        if exception:
            exception_details = self._process_exception(exception)
            log_entry.update(exception_details)

        # Create span and log
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
            # Log to all handlers
            log_level = getattr(logging, level.upper(), logging.INFO)
            self._logger.log(log_level, message, extra=log_entry)

            # Set span status
            if exception or level in ('error', 'fatal'):
                from opentelemetry.trace import StatusCode
                span.set_status(StatusCode.ERROR, message)

    def flush(self):
        """Flush all pending logs and traces."""

        # Flush OpenTelemetry providers
        get_logger_provider().force_flush(timeout_millis=30000)
        trace.get_tracer_provider().force_flush(timeout_millis=30000)
        metrics.get_meter_provider().force_flush(timeout_millis=30000)

        # Flush stdlib handlers
        for handler in self._logger.handlers:
            handler.flush()

    def _serialize_json(self, obj: Any) -> str:
        """Serialize to JSON string."""
        if obj is None:
            return "null"
        try:
            return json.dumps(obj, ensure_ascii=False)
        except (TypeError, ValueError):
            return "[Serialization Error]"

    def _process_exception(self, error: BaseException) -> dict:
        """Process exception for logging."""
        raw_stack = ''.join(traceback.format_exception(
            type(error), error, error.__traceback__
        ))
        clean_stack = self._remove_credentials(raw_stack)
        limited_stack = clean_stack[:350]

        return {
            'exception_type': 'Error',
            'exception_message': str(error),
            'exception_stack': limited_stack
        }

    def _remove_credentials(self, text: str) -> str:
        """Remove credentials from text."""
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
        """Parse OTLP headers from environment."""
        headers_str = os.getenv('OTEL_EXPORTER_OTLP_HEADERS', '{}')
        try:
            return json.loads(headers_str)
        except json.JSONDecodeError:
            return {}
```

---

## Quick Start Checklist

- [ ] Install dependencies (`pip install -r requirements.txt`)
- [ ] Create `sovdev_logger/` package directory
- [ ] Implement `logger.py` (SovdevLogger class)
- [ ] Implement `__init__.py` (module-level API)
- [ ] Implement `create_peer_services()`
- [ ] Implement `SOVDEV_LOGLEVELS` enum
- [ ] Create E2E test in `test/e2e/company-lookup/`
- [ ] Test with local OpenTelemetry collector
- [ ] Verify logs in Grafana
- [ ] Run all 11 test scenarios from specification
- [ ] Validate with `validate-log-format.sh`

---

**Guide Version**: 1.0.0
**Last Updated**: 2025-10-12
**Ready for Implementation**: ✅ YES
**Estimated Implementation Time**: 6-8 hours
