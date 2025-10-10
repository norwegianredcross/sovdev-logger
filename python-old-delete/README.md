# sovdev-logger

**One log call. Complete observability.**

Stop writing separate code for logs, metrics, and traces. Write one log entry and automatically get:
- ✅ **Structured logs** (Azure Log Analytics, Loki, or local files)
- ✅ **Metrics dashboards** (Azure Monitor, Prometheus, Grafana)
- ✅ **Distributed traces** (Azure Application Insights, Tempo)
- ✅ **Service dependency maps** (automatic correlation)

---

## Who Do You Write Logs For?

You write code for yourself during development. But **you write logs for the operations engineer staring at a screen at 7 PM on Friday.**

Picture this: Your application just crashed in production. Everyone on your team has left for the weekend. The ops engineer who got the alert doesn't know your codebase, doesn't know your business logic, and definitely doesn't want to be there right now. They're trying to piece together what went wrong from cryptic error messages and scattered log entries.

**Make their job easy.**

Good logging is the difference between:

- ❌ "Some null reference exception occurred somewhere" *(cue 3-hour debugging session)*
- ✅ "User authentication failed for email 'john@company.com' - invalid password attempt #3, account locked for security" *(fixed in 5 minutes)*

When you write clear, contextual logs, you're not just debugging future problems—**you're earning respect**. That ops engineer will look up who wrote this beautifully logged code and think: *"Now THIS is a developer who knows what they're doing."*

Help them get home to their family. Help yourself build a reputation as someone who writes production-ready code.

**Your future self (and your colleagues) will thank you.**

---

## The Problem: Traditional Observability is Complex

```python
# Traditional approach: 20+ lines per operation
logger.info('Payment processed', extra={'order_id': '123'})
payment_counter.inc()
payment_duration.observe(duration)
span = tracer.start_span('process_payment')
span.set_attributes({'order_id': '123'})
span.end()
# ... manually correlate logs, metrics, traces
```

## The Solution: Zero-Effort Observability

```python
# sovdev-logger: 1 line, complete observability
FUNCTION_NAME = 'process_payment'
input_data = {'order_id': '123', 'amount': 99.99}
output_data = {'transaction_id': 'tx-456', 'status': 'approved'}

sovdev_log(INFO, FUNCTION_NAME, 'Payment processed', PEER_SERVICES.PAYMENT_GATEWAY, input_data, output_data)
# ↑ Automatic logs + metrics + traces + correlation
```

**Result**: 95% less instrumentation code, complete observability out of the box.

---

## Quick Start (60 Seconds)

### 1. Install

```bash
pip install sovdev-logger
```

### 2. Basic Usage (Console + File Logging)

Create `test.py`:

```python
from sovdev_logger import sovdev_initialize, sovdev_log, sovdev_flush, SOVDEV_LOG_LEVELS, create_peer_services

# INTERNAL is auto-generated, just pass empty dict if no external systems
PEER_SERVICES = create_peer_services({})

async def main():
    FUNCTION_NAME = 'main'

    # Initialize
    sovdev_initialize('my-app')

    # Log with full context
    input_data = {'user_id': '123', 'action': 'process_order'}
    output_data = {'order_id': '456', 'status': 'success'}

    sovdev_log(
        SOVDEV_LOG_LEVELS.INFO,
        FUNCTION_NAME,
        'Order processed successfully',
        PEER_SERVICES.INTERNAL,
        input_data,
        output_data
    )

    # Flush before exit (CRITICAL!)
    sovdev_flush()

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
```

### 3. Run

```bash
python test.py
```

### 4. See Results

- ✅ **Console**: Human-readable colored output
- ✅ **File**: Structured JSON in `./logs/dev.log`
- 📊 **Want Grafana dashboards?** → See examples/ directory

---

## What You Get Automatically

```
┌─────────────────────────────────────────────────────┐
│  Your Code: sovdev_log(...)                        │
│             ↓                                       │
│  One Log Call                                       │
└──────────────┬──────────────────────────────────────┘
               │
    ┌──────────┼──────────┬──────────┐
    ↓          ↓          ↓          ↓
┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
│ Logs   │ │Metrics │ │Traces  │ │ File   │
│Azure LA│ │Azure   │ │App     │ │ (JSON) │
│  Loki  │ │Monitor │ │Insights│ │        │
│        │ │Grafana │ │ Tempo  │ │        │
└────────┘ └────────┘ └────────┘ └────────┘
```

Every `sovdev_log()` call generates:
- **Logs**: Structured JSON with full context (what happened, input, output)
- **Metrics**: Counters and histograms for Azure Monitor, Prometheus, or Grafana
- **Traces**: Distributed tracing spans with automatic correlation (Azure Application Insights, Tempo)
- **Service Maps**: Automatic dependency graphs showing system-to-system calls
- **File Logs**: Optional JSON files for local development and debugging

**No extra code required.**

---

## For Microsoft/Azure Developers

**"I only know Azure Monitor and Application Insights..."**

Good news! This library uses **OpenTelemetry** - Microsoft's recommended standard for observability. Your code works with **both** Azure and open-source tools:

```python
# Same code works everywhere
sovdev_log(INFO, FUNCTION_NAME, 'Order processed', PEER_SERVICES.INTERNAL, input_data, output_data)
```

**Where your logs go**:

| Environment | Logs | Metrics | Traces |
|------------|------|---------|---------|
| **Azure Production** | Azure Log Analytics | Azure Monitor | Application Insights |
| **Local Development** | Console + JSON files | Grafana (optional) | Tempo (optional) |
| **On-Premises** | Loki | Prometheus | Tempo |

**Key benefits for Azure developers**:
- ✅ **No vendor lock-in**: Write once, deploy anywhere (Azure, AWS, on-prem)
- ✅ **Local testing**: Full observability stack on your laptop (no cloud costs)
- ✅ **Azure-compatible**: OpenTelemetry Protocol (OTLP) works with Azure Monitor
- ✅ **Future-proof**: Microsoft recommends OpenTelemetry for new applications

---

## Common Logging Patterns

### Pattern 1: Single Transaction (API Call, Database Query)

```python
# Define peer services once at the top of your file
PEER_SERVICES = create_peer_services({
    'PAYMENT_GATEWAY': 'SYS2034567'   # External payment system (system ID)
    # INTERNAL is auto-generated - no need to declare it
})

async def process_payment(order_id: str, amount: float):
    # BEST PRACTICE: Use FUNCTION_NAME constant at start of every function
    FUNCTION_NAME = 'process_payment'

    # Capture input BEFORE the operation
    input_data = {'order_id': order_id, 'amount': amount, 'currency': 'USD'}

    try:
        # Call external system
        result = await payment_gateway.charge(order_id, amount)

        # Capture output AFTER the operation
        output_data = {'transaction_id': result.id, 'status': 'approved'}

        # Log success: input + output = complete audit trail
        sovdev_log(
            SOVDEV_LOG_LEVELS.INFO,
            FUNCTION_NAME,
            'Payment processed successfully',
            PEER_SERVICES.PAYMENT_GATEWAY,  # Track external dependency
            input_data,
            output_data
        )

        return result
    except Exception as error:
        # Capture error output
        output_data = {'status': 'failed', 'reason': str(error)}

        # Log failure: input + output + exception
        sovdev_log(
            SOVDEV_LOG_LEVELS.ERROR,
            FUNCTION_NAME,
            'Payment failed',
            PEER_SERVICES.PAYMENT_GATEWAY,  # Still track peer service on error
            input_data,
            output_data,
            error  # Exception object for stack trace
        )
        raise
```

---

## Configuration

### Environment Variables

```bash
# System identification
SYSTEM_ID=my-app-name                           # Required: Your service name

# Console logging (enabled by default in dev)
LOG_TO_CONSOLE=true                              # Optional: Console output

# File logging (disabled by default)
LOG_TO_FILE=true                                 # Optional: Enable file logging
LOG_FILE_PATH=./logs/app.log                    # Optional: Custom log file path

# OpenTelemetry endpoints (for Grafana/Azure)
OTEL_EXPORTER_OTLP_LOGS_ENDPOINT=http://127.0.0.1/v1/logs
OTEL_EXPORTER_OTLP_METRICS_ENDPOINT=http://127.0.0.1/v1/metrics
OTEL_EXPORTER_OTLP_TRACES_ENDPOINT=http://127.0.0.1/v1/traces
OTEL_EXPORTER_OTLP_HEADERS={"Host":"otel.localhost"}  # For Traefik routing
```

---

## API Reference

### Core Functions

#### `sovdev_initialize(service_name: str, service_version: str = 'auto', system_ids: dict = None)`

Initialize the logging system. Call once at application startup.

**Parameters**:
- `service_name` (str): Your application name (e.g., 'payment-service')
- `service_version` (str): Version string or 'auto' to detect from environment
- `system_ids` (dict): Dictionary mapping peer service names to system IDs

**Example**:
```python
sovdev_initialize('my-app', '1.0.0', {'PAYMENT_API': 'SYS123456'})
```

#### `sovdev_log(level, function_name, message, peer_service, input_data=None, output_data=None, exception=None)`

Log an entry with automatic metrics and trace generation.

**Parameters**:
- `level`: Log level from `SOVDEV_LOG_LEVELS` (TRACE, DEBUG, INFO, WARN, ERROR, FATAL)
- `function_name` (str): Name of the function/operation
- `message` (str): Human-readable description
- `peer_service` (str): Peer service identifier from `PEER_SERVICES`
- `input_data` (dict): Input parameters (optional)
- `output_data` (dict): Output/result data (optional)
- `exception` (Exception): Exception object for errors (optional)

#### `sovdev_flush(timeout_ms: int = 30000)`

Flush all pending telemetry. **MUST call before application exit**.

**Parameters**:
- `timeout_ms` (int): Maximum wait time in milliseconds

---

## Testing

### Run Unit Tests

```bash
pytest test/unit/ -v
```

### Run Integration Tests

```bash
pytest test/integration/ -v
```

### Run E2E Tests (requires Kubernetes)

```bash
./test/e2e-test.sh
```

---

## Examples

See the `examples/` directory for:
- **basic/**: Simple logging examples
- Full examples with Kubernetes integration

---

## License

MIT

---

## Contributing

See [CHANGELOG.md](CHANGELOG.md) for version history.

## Support

For issues and questions: https://github.com/norwegianredcross/sovdev-logger/issues
