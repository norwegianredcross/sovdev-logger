# Advanced Example - Company Lookup Service

Real-world example demonstrating sovdev-logger advanced features with Norwegian company registry integration.

## Features Demonstrated

1. **Job Status Logging**: Track job lifecycle (Started/Completed/Failed)
2. **Progress Logging**: Monitor batch processing progress
3. **Error Handling**: Log API errors with full context
4. **Real API Integration**: Fetch data from Brønnøysund Registry
5. **Multiple Transports**: Console + File + OTLP simultaneously
6. **Graceful Shutdown**: Proper log flushing before exit (prevents log loss)

## Why Log Flushing Matters

This example demonstrates the importance of calling `flushSovdevLogs()`:

- **Job Completion Logs**: Without flushing, the final "Completed" status might be lost
- **Error Logs**: Critical error information could disappear if not flushed
- **Batch Statistics**: Summary data might not reach the OTLP collector

OpenTelemetry batches logs for efficiency. When your application exits, unflushed logs in the buffer are **permanently lost**. Always flush before exit, even on errors!

## Setup

```bash
# 1. Build the main package first (from typescript/ directory)
cd ../..
npm run build

# 2. Install example dependencies
cd examples/advanced
npm install

# 3. Create logs directory
mkdir -p logs

# 4. Copy and configure environment
cp .env.example .env

# IMPORTANT: The .env.example already has correct OTLP configuration
# Three critical variables are pre-configured:
#   OTEL_EXPORTER_OTLP_LOGS_ENDPOINT=http://127.0.0.1/v1/logs
#   OTEL_EXPORTER_OTLP_TRACES_ENDPOINT=http://127.0.0.1/v1/traces
#   OTEL_EXPORTER_OTLP_HEADERS={"Host":"otel.localhost"}
#
# These are required for logs to reach the OTLP collector through Traefik
```

## Run

```bash
# Run the company lookup
npm start

# Watch file logs in real-time (in another terminal)
npm run logs
```

## What This Example Does

The example performs a batch lookup of Norwegian organizations:

1. Initializes the logger with system ID "company-lookup-service"
2. Starts a batch job to lookup multiple companies
3. For each company:
   - Logs progress (X/Total)
   - Fetches data from Brønnøysund API
   - Logs success or error with full context
4. Logs job completion with statistics
5. Flushes all logs before exit

## Expected Output

### Console Output
- Colored, human-readable logs with timestamps
- Progress indicators for batch processing
- Error messages for failed lookups

### File Output (`logs/company-lookup.log`)
- Structured JSON logs with all fields
- Searchable by systemId, functionName, etc.
- Full request/response context

### OTLP Output (if configured)
- Logs sent to Loki for querying in Grafana
- Traces sent to Tempo
- Automatic correlation via trace IDs

## Log Structure Example

```json
{
  "timestamp": "2025-10-03T07:30:00.000Z",
  "level": "INFO",
  "systemId": "company-lookup-service",
  "functionName": "batchLookup",
  "message": "Processing 971277882 (1/4)",
  "correlationId": "uuid-here",
  "inputJSON": {
    "jobName": "CompanyLookupBatch",
    "itemId": "971277882",
    "currentItem": 1,
    "totalItems": 4,
    "progressPercentage": 25
  }
}
```

## Companies Used in Example

- `971277882` - Norges Røde Kors (Norwegian Red Cross)
- `915933149` - Røde Kors Hjelpekorps
- `974652846` - Invalid number (demonstrates error handling)
- `916201478` - Norsk Folkehjelp
