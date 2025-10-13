# Python Implementation Guidelines - todo-lib

**Purpose**: Python-specific reference materials for implementing sovdev-logger
**Status**: Complete and ready for implementation
**Date**: 2025-10-12

**Important**: This folder provides Python-specific guides and examples. For authoritative specification and testing documentation, see:
- `specification/06-test-scenarios.md` - Complete test scenarios (source of truth)
- `specification/tools/README.md` - Tool documentation
- `specification/01-core-concepts.md` - Architecture and concepts

---

## Documents in This Folder

### 🚀 **QUICK-START.md** (START HERE)
   - **Size**: 12 KB
   - **Purpose**: Step-by-step implementation checklist
   - **Content**:
     - 4 phases with time estimates
     - Setup (30 min)
     - Core implementation (4-6 hours)
     - Testing (1-2 hours)
     - Documentation (1 hour)
     - Checklists for each phase

### 📖 **python-implementation-guide.md** (MAIN REFERENCE)
   - **Size**: 28 KB
   - **Purpose**: Complete implementation guide for Python developers
   - **Content**:
     - Dependencies and installation
     - Architecture overview (triple output pattern)
     - OpenTelemetry integration patterns
     - Logging library selection rationale
     - Complete API signatures
     - Module structure
     - Implementation patterns
     - File rotation setup
     - Exception handling
     - Complete code skeleton

### 🔬 **python-otel-research.md** (BACKGROUND)
   - **Size**: 29 KB
   - **Purpose**: Detailed research on OpenTelemetry Python SDK
   - **Content**:
     - How professional Python developers use OTEL
     - Provider initialization patterns
     - LoggingHandler integration
     - Comparison of logging libraries (structlog, loguru, stdlib)
     - Architecture decisions and rationale
     - Complete working examples

### 🔧 **python-specification-gaps.md** (REFERENCE)
   - **Size**: 22 KB
   - **Purpose**: Resolution of all specification gaps for Python
   - **Content**:
     - All 11 gaps identified in validation
     - Resolutions for each gap
     - Specification updates needed
     - Code examples for each resolution

---

## Implementation Workflow

### Phase 1: Setup (30 minutes)
1. Read `python-implementation-guide.md` sections 1-2
2. Create virtual environment
3. Install dependencies from `requirements.txt`
4. Set up package structure

### Phase 2: Core Implementation (4-6 hours)
1. Implement `SovdevLogger` class (use skeleton in guide)
2. Implement module-level API (`__init__.py`)
3. Implement `create_peer_services()`
4. Implement `SOVDEV_LOGLEVELS` enum
5. Test basic logging functionality

### Phase 3: Testing (2-3 hours)
1. Create E2E test (example in guide section 11)
2. Run test with local OTLP collector
3. Verify logs in Grafana
4. Run all 11 test scenarios from specification
5. Validate log format with tools

### Phase 4: Documentation (1 hour)
1. Update specification with Python examples
2. Document any implementation findings
3. Create Python-specific README

---

## Key Decisions Made

### 1. Logging Library: stdlib logging + python-json-logger
**Rationale**:
- ✅ Native OpenTelemetry LoggingHandler support
- ✅ Every Python developer knows it
- ✅ Built-in file rotation (RotatingFileHandler)
- ✅ JSON formatting via python-json-logger
- ✅ No learning curve

**Rejected alternatives**:
- ❌ loguru: Incompatible with OpenTelemetry LoggingHandler
- ❌ structlog: Too complex, steep learning curve

### 2. Flush Pattern: Synchronous
**Rationale**:
- ✅ OpenTelemetry Python uses sync `force_flush()` by default
- ✅ Safe to call in signal handlers and atexit
- ✅ No asyncio complexity
- ✅ Blocks until complete or timeout (30s)

**Difference from TypeScript**: TypeScript uses async/await, Python uses synchronous blocking

### 3. Module Structure: Module-level functions
**Rationale**:
- ✅ Matches TypeScript API
- ✅ Familiar to Python developers
- ✅ Simple to use (no class instantiation)
- ✅ Singleton managed internally

### 4. Exception Handling: Accept BaseException
**Rationale**:
- ✅ Catches all exceptions (including SystemExit, KeyboardInterrupt)
- ✅ More flexible than just Exception
- ✅ Standardize to "Error" in logs (language-agnostic)

### 5. Triple Output Architecture
**Rationale**:
- ✅ One log call → three outputs (console, file, OTLP)
- ✅ Uses stdlib logging's multi-handler capability
- ✅ Each handler has different formatter
- ✅ No custom multiplexing code needed

---

## Dependencies

```txt
# requirements.txt

# OpenTelemetry core
opentelemetry-api>=1.27.0,<2.0.0
opentelemetry-sdk>=1.27.0,<2.0.0

# OTLP exporter (HTTP)
opentelemetry-exporter-otlp-proto-http>=1.27.0,<2.0.0

# JSON logging
python-json-logger>=2.0.0,<3.0.0

# Type hints for Python < 3.9
typing-extensions>=4.0.0; python_version < "3.9"
```

**Python Version**: 3.8+ (3.11+ recommended)

---

## Quick Reference: API Signatures

```python
# Initialize
sovdev_initialize(
    service_name: str,
    service_version: str = "1.0.0",
    peer_services: Optional[Dict[str, str]] = None
) -> None

# Log transaction
sovdev_log(
    level: str,
    function_name: str,
    message: str,
    peer_service: str,
    input_json: Optional[Any] = None,
    response_json: Optional[Any] = None,
    exception: Optional[BaseException] = None,
    trace_id: Optional[str] = None
) -> None

# Flush (synchronous)
sovdev_flush() -> None

# Generate trace ID
sovdev_generate_trace_id() -> str

# Create peer services
create_peer_services(definitions: Dict[str, str]) -> PeerServices
```

---

## Common Issues and Solutions

### Issue 1: "Must call sovdev_initialize() first"
**Solution**: Call `sovdev_initialize()` before any logging calls

### Issue 2: Logs not appearing in Grafana
**Solution**:
1. Check `OTEL_EXPORTER_OTLP_LOGS_ENDPOINT` environment variable
2. Verify OpenTelemetry collector is running
3. Check OTLP headers configuration
4. Call `sovdev_flush()` before exit

### Issue 3: File rotation not working
**Solution**:
1. Check `maxBytes` is > 0
2. Check `backupCount` is > 0
3. Verify write permissions on log directory

### Issue 4: Import errors
**Solution**:
1. Verify all dependencies installed: `pip install -r requirements.txt`
2. Check Python version >= 3.8
3. Verify package structure matches guide

---

## Testing Checklist

- [ ] Basic log output to console
- [ ] JSON log output to file
- [ ] File rotation (create large log, verify rotation)
- [ ] OTLP export to Grafana
- [ ] Trace ID correlation
- [ ] Session ID consistency
- [ ] Exception handling with stack trace
- [ ] Credential removal from stack traces
- [ ] Signal handler flush (Ctrl+C)
- [ ] Exit handler flush (normal exit)
- [ ] All 11 test scenarios from specification

---

## Validation Commands

```bash
# Run E2E test
cd python/test/e2e/company-lookup
./run-test.sh

# Query Loki for logs
../../specification/tools/query-loki.sh sovdev-test-company-lookup-python

# Validate log format
../../specification/tools/validate-log-format.sh python/test/e2e/company-lookup/dev.log

# Query Prometheus for metrics
../../specification/tools/query-prometheus.sh sovdev-test-company-lookup-python

# Query Tempo for traces
../../specification/tools/query-tempo.sh <trace_id>
```

---

## Implementation Time Estimate

| Phase | Task | Time |
|-------|------|------|
| 1 | Setup and dependencies | 30 min |
| 2 | Core logger implementation | 2-3 hours |
| 3 | Module-level API | 1 hour |
| 4 | Helper functions | 1 hour |
| 5 | Exception handling | 1 hour |
| 6 | Testing | 2 hours |
| 7 | Documentation | 1 hour |
| **Total** | | **8-10 hours** |

**Confidence**: 95%

---

## Next Steps

1. ✅ Read `python-implementation-guide.md` (start to finish)
2. ✅ Set up Python virtual environment
3. ✅ Install dependencies
4. ✅ Begin implementation following guide
5. ✅ Test as you go
6. ✅ Run validation tools
7. ✅ Update specification with findings

---

**Status**: Ready for implementation
**Last updated**: 2025-10-12
**Maintained by**: sovdev-logger project
