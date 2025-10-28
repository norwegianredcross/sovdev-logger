# OTEL SDK Comparison: TypeScript vs Python

## Summary

Python's OpenTelemetry SDK has several differences from TypeScript that require careful attention:
- Duration unit: Python uses nanoseconds by default, needs conversion to milliseconds
- Metric attributes: Must use explicit strings (no semantic conventions with dots)
- Time: Python uses `time.time()` returns seconds, needs multiplication to ms
- HTTP headers: Python's requests library should respect custom Host headers
- Async vs Sync: Python OTEL providers have synchronous flush() methods

## Comparison Table

| Aspect | TypeScript | Python | Issue? | Solution |
|--------|-----------|--------|---------|----------|
| **HTTP Headers** | Via `headers` option, works | Should work with `headers` param | Test required | Set headers in OTLP exporter config |
| **Attributes** | Underscores (peer_service) | Underscores required | Must avoid semconv | Use explicit attribute names |
| **Duration Unit** | Milliseconds (Date.now()) | time.time() returns seconds | YES | Multiply by 1000 for milliseconds |
| **Histogram Unit** | `unit: 'ms'` option | `unit='ms'` parameter | No | Pass unit to create_histogram() |
| **Semantic Conventions** | Manual attributes | Available but should avoid | YES | Use explicit strings, not semconv constants |
| **Flush** | async (Promise) | synchronous | No | Call flush() directly, no await needed |
| **Logging** | Python logging module | Python logging module | No | Use standard logging with OTLP handler |

## Key Differences

### 1. Time and Duration

**TypeScript:**
```typescript
const start = Date.now();  // milliseconds since epoch
// ... do work ...
const duration = Date.now() - start;  // milliseconds
histogram.record(duration, attributes);  // Already in ms
```

**Python:**
```python
import time
start = time.time()  # SECONDS since epoch (float)
# ... do work ...
duration = (time.time() - start) * 1000  # Convert to milliseconds
histogram.record(duration, attributes)  # Now in ms
```

**Issue:** Python's `time.time()` returns seconds (float), TypeScript's `Date.now()` returns milliseconds (int)

**Solution:** Always multiply Python time differences by 1000 to get milliseconds

### 2. Metric Attributes

**TypeScript (correct):**
```typescript
const attributes = {
  'service_name': serviceName,
  'peer_service': peerService,
  'log_level': level,
  'log_type': logType
};
```

**Python (WRONG - using semantic conventions):**
```python
from opentelemetry.semconv.trace import SpanAttributes
attributes = {
    SpanAttributes.PEER_SERVICE: peer_service,  # Results in "peer.service" with dot!
}
```

**Python (CORRECT - explicit strings):**
```python
attributes = {
    'service_name': service_name,
    'peer_service': peer_service,  # Explicit underscore
    'log_level': level,
    'log_type': log_type
}
```

**Issue:** Python semantic convention constants use dots (peer.service, service.name)

**Solution:** Never use semconv constants for attributes, always use explicit underscore strings

### 3. OpenTelemetry Providers

**TypeScript:**
```typescript
const provider = new LoggerProvider({ resource });
provider.addLogRecordProcessor(new BatchLogRecordProcessor(exporter));
logs.setGlobalLoggerProvider(provider);

// Later...
await provider.forceFlush();  // Returns Promise
await provider.shutdown();
```

**Python:**
```python
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor

provider = LoggerProvider(resource=resource)
provider.add_log_record_processor(BatchLogRecordProcessor(exporter))
logs.set_logger_provider(provider)

# Later...
provider.force_flush()  # Synchronous, returns boolean
provider.shutdown()
```

**Issue:** Python uses synchronous flush() while TypeScript uses async

**Solution:** No await needed in Python, just call `provider.force_flush()` directly

### 4. Histogram Creation

**TypeScript:**
```typescript
meter.createHistogram('sovdev.operation.duration', {
  description: 'Duration of operations in milliseconds',
  unit: 'ms'
});
```

**Python:**
```python
meter.create_histogram(
    name='sovdev.operation.duration',
    description='Duration of operations in milliseconds',
    unit='ms'
)
```

**Issue:** No difference, both support unit specification

**Solution:** Always specify unit='ms' for consistency

## Known Issues

### Issue 1: Python OpenTelemetry Logs Module Location

**When:** Importing OpenTelemetry logs SDK classes

**Symptom:** ImportError when trying to import from `opentelemetry.sdk.logs`

**Cause:** Python OTEL logs SDK uses `_logs` (with underscore) to indicate beta status

**Solution:**
```python
# WRONG
from opentelemetry.sdk.logs import LoggerProvider

# CORRECT
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
```

**Code:** See python/src/logger.py imports section

---

**Status:** Initial version based on specification study
**Last Updated:** 2025-10-28
**Next:** Will be updated as implementation progresses
