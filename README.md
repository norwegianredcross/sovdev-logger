# sovdev-logger

**Multi-language structured logging with zero-effort observability**

One log call. Complete observability. Available for TypeScript, Python, C#, Go, Rust, PHP, and more.

---

## What is sovdev-logger?

Stop writing separate code for logs, metrics, and traces. Write one log entry and automatically get:

- ✅ **Structured logs** (Azure Log Analytics, Loki, or local files)
- ✅ **Metrics dashboards** (Azure Monitor, Prometheus, Grafana)
- ✅ **Distributed traces** (Azure Application Insights, Tempo)
- ✅ **Service dependency maps** (automatic correlation)

**Works with any OpenTelemetry-compatible backend**: Azure Monitor, Grafana Cloud, Datadog, New Relic, Honeycomb, or self-hosted infrastructure.

---

## The Problem: Traditional Observability is Complex

```typescript
// Traditional approach: 20+ lines per operation
logger.info('Payment processed', { orderId: '123' });
paymentCounter.inc();
paymentDuration.observe(duration);
const span = tracer.startSpan('processPayment');
span.setAttributes({ orderId: '123' });
span.end();
// ... manually correlate logs, metrics, traces
```

## The Solution: Zero-Effort Observability

```typescript
// sovdev-logger: 1 line, complete observability
const FUNCTIONNAME = 'processPayment';
const input = { orderId: '123', amount: 99.99 };
const output = { transactionId: 'tx-456', status: 'approved' };

sovdev_log(INFO, FUNCTIONNAME, 'Payment processed', PEER_SERVICES.PAYMENT_GATEWAY, input, output);
// ↑ Automatic logs + metrics + traces + correlation
```

**Result**: 95% less instrumentation code, complete observability out of the box.

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

## Supported Languages

| Language | Status | Documentation |
|----------|--------|---------------|
| **TypeScript** | ✅ Available | [typescript/README.md](typescript/README.md) |
| **Go** | ✅ Available | [go/README.md](go/README.md) |
| **Python** | ✅ Available | [python/README.md](python/README.md) |
| **C#** | 📅 Planned | - |
| **Rust** | 📅 Planned | - |
| **PHP** | 📅 Planned | - |

---

## 👥 Choose Your Path

### For Library Users
**You want to USE sovdev-logger in your application**

**→ Quick Start:**
1. Choose your language: [TypeScript](typescript/README.md) | [Go](go/README.md) | [Python](python/README.md)
2. Read [Configuration Guide](docs/README-configuration.md)
3. See [Examples](#example-typescript) below or in [Log Data Structure](docs/logging-data.md)
4. [Verify logs in Grafana](docs/README-observability-architecture.md)

### For Language Implementers
**You want to IMPLEMENT sovdev-logger in a new language**

**→ Implementation Guide:**
1. **Understand the development environment** - [specification/05-environment-configuration.md](specification/05-environment-configuration.md)
2. Read [specification/README.md](specification/README.md) - Complete implementation guide
3. Read [specification/10-otel-sdk.md](specification/10-otel-sdk.md) ⚠️ **CRITICAL**: OTEL SDK differences
4. Copy [specification/11-llm-checklist-template.md](specification/11-llm-checklist-template.md) to track progress
5. Study [typescript/src/logger.ts](typescript/src/logger.ts) - Reference implementation

**Current implementations:**
- ✅ TypeScript (complete) - [typescript/](typescript/)
- ✅ Go (complete) - [go/](go/)
- ✅ Python (complete) - [python/](python/)

**Validation (run in DevContainer):**
```bash
# Direct (if inside VSCode DevContainer)
./specification/tools/run-company-lookup-validate.sh {language}

# Or via wrapper (from host machine)
./specification/tools/in-devcontainer.sh -e "cd /workspace/specification/tools && ./run-company-lookup-validate.sh {language}"
```

---

## Quick Start

### TypeScript/JavaScript

```bash
npm install @sovdev/logger
```

See [typescript/README.md](typescript/README.md) for complete documentation.

### Go

```bash
go get github.com/norwegianredcross/sovdev-logger
```

See [go/README.md](go/README.md) for complete documentation.

### Python

```bash
pip install sovdev-logger
```

See [python/README.md](python/README.md) for complete documentation.

### C# (Planned)

```bash
dotnet add package SovdevLogger
```

---

## For Microsoft/Azure Developers

**"I only know Azure Monitor and Application Insights..."**

Good news! This library uses **OpenTelemetry** - Microsoft's recommended standard for observability. Your code works with **both** Azure and open-source tools:

```typescript
// Same code works everywhere
sovdev_log(INFO, FUNCTIONNAME, 'Order processed', PEER_SERVICES.INTERNAL, input, output);
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

**→ Complete Azure setup guide**: [Microsoft/Azure Integration](docs/README-microsoft-opentelemetry.md)

---

## See It In Action

![Grafana Dashboard showing structured logs with trace correlation](docs/images/dashboard-sovdevlogger.png)
*Logs visualized in Grafana with automatic traceId correlation, service tracking, and peer service mapping*

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

Every log call generates:
- **Logs**: Structured JSON with full context (what happened, input, output)
- **Metrics**: Counters, histograms, gauges for Azure Monitor, Prometheus, or Grafana
- **Traces**: Distributed tracing spans with automatic correlation (Azure Application Insights, Tempo)
- **Service Maps**: Automatic dependency graphs showing system-to-system calls
- **File Logs**: Optional JSON files for local development and debugging

**No extra code required.**

---

## Log Structure (Consistent Across All Languages)

All sovdev-logger implementations produce **identical log structures** with **snake_case field naming** (underscores, not dots or camelCase):

### Standard Fields (Every Log Entry)

```json
{
  "event_id": "uuid-v4-identifier",
  "service_name": "your-service-name",
  "service_version": "1.0.0",
  "function_name": "functionName",
  "level": "info|warn|error|debug|fatal",
  "log_type": "transaction|job.status|job.progress",
  "message": "Human-readable message",
  "timestamp": "2025-10-10T19:38:39.109Z",
  "trace_id": "32-char-hex-trace-identifier",
  "span_id": "16-char-hex-span-identifier",
  "peer_service": "external-system-identifier"
}
```

### Contextual Fields (Optional)

```json
{
  "input_json": { "orderId": "123" },
  "response_json": { "status": "success" }
}
```

### Exception Fields (When Logging Errors)

```json
{
  "exception_type": "Error",
  "exception_message": "HTTP 404: Not found",
  "exception_stacktrace": "Error: HTTP 404...\n    at function (/path/file.ts:50:20)\n    ..."
}
```

**Key Principles:**
- ✅ **Consistent naming**: All languages use identical field names (`service_name`, `function_name`, `trace_id`, `span_id`)
- ✅ **snake_case convention**: All field names use underscores (not dots, not camelCase)
- ✅ **Flat structure**: Exception fields at top level (`exception_type`, not `exception.type`)
- ✅ **OpenTelemetry compatible**: Works with Loki, Tempo, Prometheus, Azure Monitor
- ✅ **Language agnostic**: TypeScript, Python, C#, Go, Rust, PHP all produce same structure

**Why snake_case?**

OpenTelemetry automatically converts dot notation (`service.name`) to underscores (`service_name`) when storing in backends. Using snake_case directly avoids transformation inconsistencies and ensures fields are stored and retrieved with the same names across all systems (Grafana, Loki, Prometheus, Azure Monitor).

---

## Example: TypeScript

```typescript
import { sovdev_initialize, sovdev_log, sovdev_flush, SOVDEV_LOGLEVELS, create_peer_services } from '@sovdev/logger';

// Define external systems your app calls
const PEER_SERVICES = create_peer_services({
  PAYMENT_GATEWAY: 'SYS2034567'  // INTERNAL is auto-generated
});

// Initialize at app startup (before any logging)
sovdev_initialize(
  'my-payment-service',      // Service name
  '1.0.0',                   // Version (optional, auto-detected from package.json)
  PEER_SERVICES.mappings     // Peer service mappings (optional)
);

async function processPayment(orderId: string, amount: number) {
  const FUNCTIONNAME = 'processPayment';

  const input = { orderId, amount };

  try {
    const result = await paymentGateway.charge(orderId, amount);
    const output = { transactionId: result.id, status: 'approved' };

    sovdev_log(
      SOVDEV_LOGLEVELS.INFO,
      FUNCTIONNAME,
      'Payment processed successfully',
      PEER_SERVICES.PAYMENT_GATEWAY,  // Tracks call to external system
      input,
      output
    );

    return result;
  } catch (error) {
    sovdev_log(
      SOVDEV_LOGLEVELS.ERROR,
      FUNCTIONNAME,
      'Payment failed',
      PEER_SERVICES.PAYMENT_GATEWAY,
      input,
      { status: 'failed', reason: error.message },
      error
    );
    throw error;
  }
}

// Flush before exit (CRITICAL - prevents log loss!)
process.on('beforeExit', async () => {
  await sovdev_flush();
});
```

---

## Configuration

**Local Development:** No configuration needed! Just install and use. Logs to console and `./logs/` directory.

**Production/Observability Stack:** Configure OTLP endpoints via environment variables. See [Configuration Guide](docs/README-configuration.md) for complete setup.

---

## Documentation

### Quick Start by Language

- **TypeScript**: [typescript/README.md](typescript/README.md) - Complete API reference, examples, patterns
- **Go**: [go/README.md](go/README.md) - Complete implementation with Go conventions
- **Python**: [python/README.md](python/README.md) - Complete implementation with Python PEP 8 style

### Detailed Documentation

- **[Configuration Guide](docs/README-configuration.md)** - Environment variables, OTLP setup, file logging
- **[Log Data Structure](docs/logging-data.md)** - Field reference, logging patterns, correlation strategies
- **[Observability Architecture](docs/README-observability-architecture.md)** - Dashboard setup, service name naming, verification
- **[Loggeloven Compliance](docs/README-loggeloven.md)** - Norwegian Red Cross logging requirements
- **[Microsoft/Azure Integration](docs/README-microsoft-opentelemetry.md)** - Azure Monitor, Application Insights setup

---

## License

MIT License - Copyright (c) 2025 Norwegian Red Cross

See [LICENSE](LICENSE) for details.

---

## Support

- **GitHub Issues**: [https://github.com/norwegianredcross/sovdev-logger/issues](https://github.com/norwegianredcross/sovdev-logger/issues)
- **Documentation**: See language-specific README files in each directory

---

## Repository Status

This repository implements a multi-language logging library with identical output across all languages.

**Development Status:**

- ✅ **Specification v1.1.0** - Complete implementation guide
- ✅ **TypeScript** - Complete, reference implementation (snake_case API)
- ✅ **Go** - Complete, validated (PascalCase API per Go conventions)
- ✅ **Python** - Complete, validated (snake_case API)
- 📅 **C#, Rust, PHP** - Planned for 2025

**All implementations follow:**
- Identical API (8 functions)
- Identical output format (JSON with snake_case fields)
- Identical validation requirements
- Source of truth: [specification/](specification/)
