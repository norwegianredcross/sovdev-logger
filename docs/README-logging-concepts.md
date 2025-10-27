# Logging Concepts: Distributed Tracing with Spans

**Date:** 2025-10-17
**Status:** DRAFT
**Purpose:** Explain distributed tracing concepts (trace_id, spans) and how to use the sovdev-logger library to implement distributed tracing in your applications.

---

## Table of Contents

1. [Introduction](#introduction)
2. [The Relationship Between trace_id and Spans](#the-relationship-between-trace_id-and-spans)
3. [Distributed Tracing: Spans (Operations with Timing)](#distributed-tracing-spans-operations-with-timing)
4. [Visual Examples](#visual-examples)
5. [When to Use Spans](#when-to-use-spans)
6. [Implementation: Manual Pattern](#implementation-manual-pattern)
7. [API Reference](#api-reference)
8. [Cross-Language Examples](#cross-language-examples)
9. [Summary](#summary)

---

## Introduction

### The Observability Challenge

When building distributed systems, you need to answer questions like:

- **"Why is this request slow?"** → Need to see timing breakdown
- **"Which operation is the bottleneck?"** → Need to see call hierarchy
- **"How did this request flow through our services?"** → Need to trace the path
- **"What happened during this transaction?"** → Need correlated logs

This document explains **distributed tracing with spans** - a powerful approach that automatically:

- **Groups related logs** under a trace_id
- **Tracks operation timing** (start, end, duration)
- **Shows call hierarchy** (parent-child relationships)
- **Enables visualization** in Grafana

---

## The Relationship Between trace_id and Spans

### Understanding the Hierarchy

**IMPORTANT:** trace_id is at a **HIGHER level** than spans. Think of it like a book:

```
📦 Trace = The entire book (the complete story of a request)
   │
   ├─ trace_id: "abc123..." ← The ISBN number (identifies the whole book)
   │
   └─ Contains multiple Spans (the chapters) ↓
      │
      ├─ 📖 Span 1: "readUser" (Chapter 1)
      │  ├─ trace_id: "abc123..." ← Which book does this chapter belong to?
      │  ├─ span_id: "def456..." ← This chapter's unique ID
      │  ├─ parent_span_id: null
      │  ├─ start_time: 10:00:00.000
      │  ├─ end_time: 10:00:00.200
      │  └─ duration: 200ms
      │
      ├─ 📖 Span 2: "calculate" (Chapter 2)
      │  ├─ trace_id: "abc123..." ← Same book!
      │  ├─ span_id: "ghi789..." ← Different chapter
      │  ├─ parent_span_id: null
      │  └─ duration: 50ms
      │
      └─ 📖 Span 3: "sendEmail" (Chapter 3)
         ├─ trace_id: "abc123..." ← Same book!
         ├─ span_id: "jkl012..." ← Different chapter
         ├─ parent_span_id: null
         └─ duration: 600ms
```

**Key Concepts:**
- **Trace** = The complete distributed operation (the whole book)
- **trace_id** = Identifier for the entire trace (ISBN number)
- **Span** = One operation within the trace (a chapter)
- **span_id** = Identifier for a specific span (chapter number)
- **parent_span_id** = Which span called this one (which chapter this is a subsection of)

### Hierarchy from Highest to Lowest

1. **Trace** - The complete story of a request flowing through your system
2. **trace_id** - The unique identifier grouping all related operations
3. **Spans** - Individual operations/chapters within that trace
4. **span_id** - Unique identifier for each specific operation

**trace_id groups spans together.** Multiple spans belong to one trace.

### How They Work Together

**When you create spans:**
- First span creates a new trace and generates a trace_id automatically
- All child spans (nested inside) inherit their parent's trace_id
- Logs inside any span automatically get the trace_id AND span_id from the active span
- No manual trace_id generation needed - spans handle it all

**trace_id is generated automatically by OpenTelemetry when you create a span:**
- You don't call `sovdev_generate_trace_id()` - it happens automatically
- Parent span creates trace_id, all children inherit it
- Same trace_id groups all related operations together
- Logs automatically detect and use the active span's trace_id

---

## Distributed Tracing: Spans (Operations with Timing)

### What is a Span?

**A span represents ONE OPERATION with start time, end time, and duration.**

Think of it as a **stopwatch for an operation** that records:

- **When it started** (timestamp)
- **When it finished** (timestamp)
- **How long it took** (duration = end - start)
- **Whether it succeeded or failed** (status)
- **Metadata about the operation** (attributes)
- **Which operation called it** (parent span ID)

### What is a Trace?

**A trace is a COLLECTION of related spans that share the same trace_id.**

It's like a video timeline with chapters - you see the complete story of a request flowing through your system.

### Example: Same Company Lookup with Spans

```typescript
const FUNCTIONNAME = 'lookupCompany';
const span = sovdev_start_span(FUNCTIONNAME);
try {
  sovdev_log(SOVDEV_LOGLEVELS.INFO, FUNCTIONNAME, 'Looking up company 971277882', PEER_SERVICES.BRREG, input);
  // ... HTTP call (auto-creates child span if HTTP instrumentation enabled) ...
  sovdev_log(SOVDEV_LOGLEVELS.INFO, FUNCTIONNAME, 'Company found: NORAD', PEER_SERVICES.BRREG, input, response);
  sovdev_end_span(span);
} catch (error) {
  sovdev_end_span(span, error);
  throw error;
}
```

### What You See in Grafana

```
┌─────────────────────────────────────────────────┐
│ Trace ID: 7c5d36d44e5a4a2f9b94e20299561c70      │
│                                                  │
│  Span: lookupCompany                            │
│  ├─ Start: 06:59:16.156                        │
│  ├─ End:   06:59:16.332                        │
│  ├─ Duration: 176ms ◄─── Automatically calculated │
│  ├─ Status: OK                                  │
│  ├─ Attributes:                                 │
│  │  ├─ organisasjonsnummer: 971277882          │
│  │  └─ peer_service: SYS1234567                │
│  │                                              │
│  └─ Child Span: HTTP GET brreg.no              │
│     ├─ Start: 06:59:16.157                    │
│     ├─ End:   06:59:16.331                    │
│     ├─ Duration: 174ms                         │
│     ├─ Status: 200 OK                          │
│     └─ Attributes:                             │
│        ├─ http.method: GET                     │
│        └─ http.url: https://data.brreg.no/... │
└─────────────────────────────────────────────────┘
```

### What You See in Loki (Enhanced)

Logs now include BOTH trace_id AND span_id:

```json
{"timestamp":"2025-10-17T06:59:16.156Z", "trace_id":"7c5d36d44e5a4a2f9b94e20299561c70", "span_id":"abc123def456", "message":"Looking up company 971277882"}
{"timestamp":"2025-10-17T06:59:16.332Z", "trace_id":"7c5d36d44e5a4a2f9b94e20299561c70", "span_id":"abc123def456", "message":"Company found: NORAD"}
```

### What You Can Now Do

✅ See timing automatically (176ms, no calculation needed)
✅ See call hierarchy (lookupCompany → HTTP GET)
✅ Identify bottlenecks (174ms spent in HTTP call = 98% of time)
✅ Click span in Grafana → jump to logs in Loki
✅ Click log in Loki → jump to trace in Grafana
✅ Visualize request flow in Grafana
✅ Query by duration: "Show me all lookups that took > 1 second"
✅ Track error propagation across services

### Trade-offs

**Advantages:**
- Automatic timing calculation
- Visual waterfall view
- Performance bottleneck identification
- Cross-service tracing
- Grafana integration

**Costs:**
- Slightly more complex API (start/end span)
- Small performance overhead (negligible in practice)
- Requires Tempo backend for visualization

---

## Visual Examples

### Example 1: Single Operation (One Span)

**Scenario:** Looking up one company

```
Timeline (176ms total):
┌────────────────────────────────────────┐
│ lookupCompany (971277882)              │
│ ├─ Start: 06:59:16.156                │
│ ├─ End:   06:59:16.332                │
│ └─ Duration: 176ms                     │
│    │                                   │
│    └─ HTTP GET brreg.no (174ms)       │ ← Auto-created child span
└────────────────────────────────────────┘
```

**Insights:**
- Total operation took 176ms
- 174ms spent in HTTP call (98% of time)
- Very little overhead (2ms for our code)

### Example 2: Batch Operation (Multiple Spans)

**Scenario:** Looking up 4 companies in sequence

```
Timeline (1850ms total):
┌─ Trace: company-lookup-service ─────────────────────────────────┐
│  Duration: 1850ms                                                │
│  │                                                                │
│  └─ Span: batch-lookup                                           │
│     Duration: 1700ms                                             │
│     │                                                             │
│     ├─ Span: lookupCompany (971277882)                          │
│     │  Duration: 176ms                                           │
│     │  └─ HTTP GET: 174ms                                        │
│     │                                                             │
│     ├─ [wait 100ms] ← Rate limiting delay                       │
│     │                                                             │
│     ├─ Span: lookupCompany (915933149)                          │
│     │  Duration: 138ms                                           │
│     │  └─ HTTP GET: 39ms ← Much faster! Cached?                 │
│     │                                                             │
│     ├─ [wait 100ms]                                              │
│     │                                                             │
│     ├─ Span: lookupCompany (974652846)                          │
│     │  Duration: 46ms                                            │
│     │  Status: ERROR ← Clearly marked as failed                 │
│     │  └─ HTTP GET: 38ms (404 NOT FOUND)                        │
│     │                                                             │
│     ├─ [wait 100ms]                                              │
│     │                                                             │
│     └─ Span: lookupCompany (916201478)                          │
│        Duration: 137ms                                           │
│        └─ HTTP GET: 37ms                                         │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

**Insights from this trace:**
- Total time: 1850ms (1700ms processing + 150ms shutdown)
- First lookup slower: 176ms vs ~138ms average (API warmup?)
- Second lookup much faster HTTP: 39ms vs 174ms (caching?)
- Failed lookup visible: Company 3 with 404 error
- Rate limiting working: 100ms gaps between lookups
- Bottleneck identified: 98% of time spent in HTTP calls

### Example 3: User Workflow (Read, Calculate, Send Email)

**Scenario:** Multi-step workflow with grouped operations

```
Timeline (850ms total):
┌─ Trace: 7c5d36d44e5a4a2f9b94e20299561c70 ────────────────────┐
│  Span: processUserWorkflow (Parent)                           │
│  Duration: 850ms                                               │
│  │                                                             │
│  ├─ Span: readUser (Child)                                    │
│  │  ├─ Start: 10:00:00.000                                   │
│  │  ├─ End:   10:00:00.200                                   │
│  │  └─ Duration: 200ms                                        │
│  │     └─ HTTP GET database: 195ms                           │
│  │                                                             │
│  ├─ Span: calculateRecommendations (Child)                    │
│  │  ├─ Start: 10:00:00.200                                   │
│  │  ├─ End:   10:00:00.250                                   │
│  │  └─ Duration: 50ms ← Fast! Pure calculation               │
│  │                                                             │
│  └─ Span: sendEmail (Child)                                   │
│     ├─ Start: 10:00:00.250                                   │
│     ├─ End:   10:00:00.850                                   │
│     └─ Duration: 600ms ← Slowest! Email service bottleneck   │
│        └─ HTTP POST email-service: 595ms                     │
└─────────────────────────────────────────────────────────────┘
```

**Insights:**
- All operations grouped under single trace_id
- Parent span shows total workflow time: 850ms
- Bottleneck identified: Email sending (70% of total time)
- Operations executed sequentially (no overlap)
- Can see exact start/end times for each step

**Alternative (Sibling spans without parent):**
```
Trace: 7c5d36d44e5a4a2f9b94e20299561c70
├─ readUser - 200ms
├─ calculateRecommendations - 50ms
└─ sendEmail - 600ms

(No parent span = no total time shown, but all three grouped by trace_id)
```

---

## When to Use Spans

### Always Use Spans for Distributed Tracing

**Spans should be used for:**
- ✅ **Production services** - Full observability and debugging capability
- ✅ **Operations that call external APIs** - Track timing and failures
- ✅ **Performance-critical code paths** - Identify bottlenecks
- ✅ **Debugging latency issues** - See exactly where time is spent
- ✅ **Multi-service architectures** - Trace requests across services
- ✅ **Batch processing jobs** - Track progress and failures
- ✅ **Simple scripts and utilities** - Even simple operations benefit from timing

**Why always use spans?**
- Automatic trace_id generation (no manual work)
- Automatic timing calculation (no manual timestamp math)
- Visual traces in Grafana (better than text logs)
- Logs automatically get trace_id from active spans (no parameters to pass)
- Minimal performance overhead (negligible in practice)

**Example:**
```typescript
const FUNCTIONNAME = 'processData';
const span = sovdev_start_span(FUNCTIONNAME);
try {
  sovdev_log(SOVDEV_LOGLEVELS.INFO, FUNCTIONNAME, 'Starting', PEER_SERVICES.INTERNAL, input);
  // Complex operations...
  sovdev_log(SOVDEV_LOGLEVELS.INFO, FUNCTIONNAME, 'Finished', PEER_SERVICES.INTERNAL, input, result);
  sovdev_end_span(span);
} catch (error) {
  sovdev_end_span(span, error);
  throw error;
}
```

### Progressive Enhancement

**Start simple, add spans when ready:**

```typescript
const FUNCTIONNAME = 'myFunction';

// Phase 1: Just logs (basic observability)
sovdev_log(SOVDEV_LOGLEVELS.INFO, FUNCTIONNAME, 'Processing', PEER_SERVICES.EXTERNAL_API, input);

// Phase 2: Add spans for timing and tracing (recommended)
const span = sovdev_start_span(FUNCTIONNAME);
try {
  sovdev_log(SOVDEV_LOGLEVELS.INFO, FUNCTIONNAME, 'Processing', PEER_SERVICES.EXTERNAL_API, input);
  sovdev_end_span(span);
} catch (error) {
  sovdev_end_span(span, error);
  throw error;
}
```

Logs work with or without spans. Adding spans enhances existing logs with trace_id and timing.

---

## Implementation: Manual Pattern

### Why Manual Pattern?

The manual start/end pattern is the **ONLY pattern that works naturally across all programming languages:**

- TypeScript/JavaScript ✅
- Python ✅
- C# ✅
- PHP ✅
- Go ✅

While less convenient than language-specific wrappers, it provides:
- **Universal**: Same conceptual pattern everywhere
- **Explicit**: Clear when span starts and ends
- **Teaching**: Easy to understand what's happening
- **Compatible**: Works with any language's error handling

### Basic Pattern

```
1. Start span (records start time)
2. Do operation (your business logic)
3. End span on success (records end time, calculates duration)
   OR
   End span on error (records end time, marks as failed)
```

### The Three Core Functions

```typescript
/**
 * Start a new span for an operation.
 * Returns a span handle that must be passed to sovdev_end_span().
 */
function sovdev_start_span(
  operation_name: string,
  attributes?: Record<string, any>
): SpanHandle

/**
 * End a span, recording its completion.
 * Call this in the success path.
 */
function sovdev_end_span(span: SpanHandle): void

/**
 * End a span with an error, marking it as failed.
 * Call this in the error path.
 */
function sovdev_end_span(span: SpanHandle, error: Error): void
```

### Important Rules

1. **Always end spans** - Memory leak if you forget!
2. **End on both success and error paths** - Use try/catch/finally
3. **Pass error to sovdev_end_span()** - Marks span as failed in Tempo
4. **Don't reuse span handles** - One span = one operation
5. **Logs inside span automatically get trace_id** - Don't pass trace_id parameter!

### When to Include Attributes

**Include attributes when:**
- ✅ Operations handle specific entities (user_id, order_id, company_id, etc.)
- ✅ You need to search/filter traces by parameters in Grafana
- ✅ Performance analysis requires grouping by input values
- ✅ Production services where debuggability is critical

**Attributes optional when:**
- ⚠️ Simple internal calculations with no external dependencies
- ⚠️ Prototype/development code
- ⚠️ Operations where timing alone is sufficient
- ⚠️ Very high-frequency operations (performance-sensitive)

**Example with attributes (Recommended):**
```typescript
const input = { userId: '123', orderId: '456' };
const span = sovdev_start_span(FUNCTIONNAME, input);
// Grafana shows: lookupOrder(userId=123, orderId=456) - 250ms
```

**Example without attributes (Simpler):**
```typescript
const span = sovdev_start_span(FUNCTIONNAME);
// Grafana shows: calculateDiscount() - 5ms
```

### Grouping Multiple Operations

**Use Case:** You want to group multiple separate operations under the same trace_id (e.g., read user, calculate something, send email).

**Recommended Approach: Parent Span with Child Spans**

```typescript
const FUNCTIONNAME = 'processUserWorkflow';

// Create parent span for the entire workflow
const workflowSpan = sovdev_start_span(FUNCTIONNAME, { userId: '123' });

try {
  // Child span 1: Read user
  const readSpan = sovdev_start_span('readUser');
  try {
    sovdev_log(SOVDEV_LOGLEVELS.INFO, FUNCTIONNAME, 'Reading user', PEER_SERVICES.DATABASE, input);
    const user = await readUser(userId);
    sovdev_end_span(readSpan);
  } catch (error) {
    sovdev_end_span(readSpan, error);
    throw error;
  }

  // Child span 2: Calculate
  const calcSpan = sovdev_start_span('calculateRecommendations');
  try {
    sovdev_log(SOVDEV_LOGLEVELS.INFO, FUNCTIONNAME, 'Calculating', PEER_SERVICES.INTERNAL, null);
    const recommendations = calculateRecommendations(user);
    sovdev_end_span(calcSpan);
  } catch (error) {
    sovdev_end_span(calcSpan, error);
    throw error;
  }

  // Child span 3: Send email
  const emailSpan = sovdev_start_span('sendEmail');
  try {
    sovdev_log(SOVDEV_LOGLEVELS.INFO, FUNCTIONNAME, 'Sending email', PEER_SERVICES.EMAIL_SERVICE, null);
    await sendEmail(user.email, recommendations);
    sovdev_end_span(emailSpan);
  } catch (error) {
    sovdev_end_span(emailSpan, error);
    throw error;
  }

  sovdev_end_span(workflowSpan);
} catch (error) {
  sovdev_end_span(workflowSpan, error);
  throw error;
}
```

**What you see in Grafana:**
```
Trace: 7c5d36d44e5a4a2f9b94e20299561c70
├─ processUserWorkflow (Parent) - 850ms
   ├─ readUser (Child) - 200ms
   ├─ calculateRecommendations (Child) - 50ms
   └─ sendEmail (Child) - 600ms
```

**How it works:**
- Parent span creates trace_id automatically
- All child spans automatically inherit parent's trace_id
- All logs inside any span get the shared trace_id automatically
- Parent span shows total workflow time (850ms)
- Child spans show individual operation times

---

## API Reference

### sovdev_start_span()

**Purpose:** Start a new span to track an operation's timing and hierarchy.

**Signature:**
```typescript
sovdev_start_span(operation_name: string, attributes?: object): SpanHandle
```

**Parameters:**
- `operation_name` (required) - Name of the operation (e.g., "lookupCompany", "processPayment")
- `attributes` (optional) - Metadata about the operation. Can include:
  - **Custom attributes**: `{ userId: "123", amount: 100 }` - Searchable in Grafana
  - **trace_id**: Reuse existing trace_id to group sibling spans
  - **Recommended**: Pass input data to make traces searchable by parameters
  - **Can be omitted**: For simple operations where span timing is sufficient

**Returns:** SpanHandle (opaque handle - must be passed to `sovdev_end_span()`)

**Example 1 (With attributes - Recommended for production):**
```typescript
const FUNCTIONNAME = 'lookupCompany';
const input = { organisasjonsnummer: '971277882' };

// Span attributes make traces searchable in Grafana
const span = sovdev_start_span(FUNCTIONNAME, input);
```

**Example 2 (Without attributes - Simpler for scripts):**
```typescript
const FUNCTIONNAME = 'calculateTotal';

// Just track timing, no searchable attributes
const span = sovdev_start_span(FUNCTIONNAME);
```

**What it does internally:**
1. Creates an OpenTelemetry span
2. Records start timestamp
3. **Determines trace_id automatically:**
   - If this span is nested inside an active parent span → Inherit parent's trace_id
   - Otherwise → Generate new trace_id (creates a new trace)
4. Generates unique span_id for this specific operation
5. **Sets span attributes** (if provided):
   - Makes traces searchable in Grafana (e.g., find all spans for a specific user_id)
   - Visible in Grafana trace view without drilling into logs
   - Useful for performance analysis by input parameters
6. Sets span as "active" (so logs and child spans can detect it)
7. Returns handle for later use

**Best Practices:**
- **With attributes**: Recommended for production - makes traces searchable and debuggable
- **Without attributes**: OK for simple operations where timing alone is sufficient
- **Key fields only**: Pass identifying fields (ids, keys) rather than full data structures
- **Child spans**: Automatically inherit parent's trace_id and appear nested in Grafana

**Remember:** trace_id identifies the entire trace (the book), span_id identifies this specific operation (the chapter)

### sovdev_end_span()

**Purpose:** End a span, recording completion and calculating duration.

**Signature (Success):**
```typescript
sovdev_end_span(span: SpanHandle): void
```

**Signature (Error):**
```typescript
sovdev_end_span(span: SpanHandle, error: Error): void
```

**Parameters:**
- `span` (required) - The handle returned from `sovdev_start_span()`
- `error` (optional) - If provided, marks span as failed

**Returns:** void

**Example (Success):**
```typescript
sovdev_end_span(span);
```

**Example (Error):**
```typescript
sovdev_end_span(span, error);
```

**What it does internally:**
1. Records end timestamp
2. Calculates duration (end - start)
3. Sets span status (OK or ERROR)
4. If error provided:
   - Sets status to ERROR
   - Records exception details
   - Adds error message and stack trace
5. Exports span to Tempo (via OTLP)
6. Removes span from "active" context

---

## Cross-Language Examples

### TypeScript

```typescript
async function lookupCompany(orgNumber: string): Promise<CompanyData> {
  const FUNCTIONNAME = 'lookupCompany';
  const input = { organisasjonsnummer: orgNumber };

  // Start span
  const span = sovdev_start_span(FUNCTIONNAME, input);

  try {
    // Logs automatically get trace_id from active span
    sovdev_log(SOVDEV_LOGLEVELS.INFO, FUNCTIONNAME, `Looking up ${orgNumber}`, PEER_SERVICES.BRREG, input);

    const data = await fetchCompanyData(orgNumber);

    sovdev_log(SOVDEV_LOGLEVELS.INFO, FUNCTIONNAME, `Found: ${data.navn}`, PEER_SERVICES.BRREG, input, {
      navn: data.navn,
      organisasjonsform: data.organisasjonsform?.beskrivelse
    });

    // End span on success
    sovdev_end_span(span);

    return data;

  } catch (error) {
    sovdev_log(SOVDEV_LOGLEVELS.ERROR, FUNCTIONNAME, `Failed to lookup ${orgNumber}`, PEER_SERVICES.BRREG, input, null, error);

    // End span on error
    sovdev_end_span(span, error);

    throw error;
  }
}
```

### Python

```python
async def lookup_company(org_number: str) -> CompanyData:
    FUNCTIONNAME = 'lookupCompany'
    input_data = {'organisasjonsnummer': org_number}

    # Start span
    span = sovdev_start_span(FUNCTIONNAME, input_data)

    try:
        # Logs automatically get trace_id from active span
        sovdev_log(SOVDEV_LOGLEVELS.INFO, FUNCTIONNAME, f'Looking up {org_number}', PEER_SERVICES.BRREG, input_data)

        data = await fetch_company_data(org_number)

        sovdev_log(SOVDEV_LOGLEVELS.INFO, FUNCTIONNAME, f'Found: {data.navn}', PEER_SERVICES.BRREG, input_data, {
            'navn': data.navn,
            'organisasjonsform': data.organisasjonsform.beskrivelse
        })

        # End span on success
        sovdev_end_span(span)

        return data

    except Exception as error:
        sovdev_log(SOVDEV_LOGLEVELS.ERROR, FUNCTIONNAME, f'Failed to lookup {org_number}', PEER_SERVICES.BRREG, input_data, None, error)

        # End span on error
        sovdev_end_span(span, error)

        raise
```

### Go

```go
func lookupCompany(orgNumber string) (*CompanyData, error) {
    const FUNCTIONNAME = "lookupCompany"
    input := map[string]interface{}{"organisasjonsnummer": orgNumber}

    // Start span
    span := sovdev_start_span(FUNCTIONNAME, input)
    defer sovdev_end_span(span)  // Go's defer handles cleanup automatically!

    // Logs automatically get trace_id from active span
    sovdev_log(SOVDEV_LOGLEVELS.INFO, FUNCTIONNAME, fmt.Sprintf("Looking up %s", orgNumber), PEER_SERVICES.BRREG, input, nil, nil)

    data, err := fetchCompanyData(orgNumber)
    if err != nil {
        sovdev_log(SOVDEV_LOGLEVELS.ERROR, FUNCTIONNAME, fmt.Sprintf("Failed to lookup %s", orgNumber), PEER_SERVICES.BRREG, input, nil, err)
        return nil, err
    }

    response := map[string]interface{}{
        "navn": data.Navn,
        "organisasjonsform": data.Organisasjonsform.Beskrivelse,
    }
    sovdev_log(SOVDEV_LOGLEVELS.INFO, FUNCTIONNAME, fmt.Sprintf("Found: %s", data.Navn), PEER_SERVICES.BRREG, input, response, nil)

    return data, nil
}
```

**Note:** Go's `defer` statement makes cleanup automatic - the span is always ended even if the function panics!

### C#

```csharp
public async Task<CompanyData> LookupCompany(string orgNumber)
{
    const string FUNCTIONNAME = "lookupCompany";
    var input = new { organisasjonsnummer = orgNumber };

    // Start span
    var span = sovdev_start_span(FUNCTIONNAME, input);

    try
    {
        // Logs automatically get trace_id from active span
        sovdev_log(SOVDEV_LOGLEVELS.INFO, FUNCTIONNAME, $"Looking up {orgNumber}", PEER_SERVICES.BRREG, input);

        var data = await FetchCompanyData(orgNumber);

        var response = new { navn = data.Navn, organisasjonsform = data.Organisasjonsform?.Beskrivelse };
        sovdev_log(SOVDEV_LOGLEVELS.INFO, FUNCTIONNAME, $"Found: {data.Navn}", PEER_SERVICES.BRREG, input, response);

        // End span on success
        sovdev_end_span(span);

        return data;
    }
    catch (Exception error)
    {
        sovdev_log(SOVDEV_LOGLEVELS.ERROR, FUNCTIONNAME, $"Failed to lookup {orgNumber}", PEER_SERVICES.BRREG, input, null, error);

        // End span on error
        sovdev_end_span(span, error);

        throw;
    }
}
```

### PHP

```php
function lookupCompany(string $orgNumber): CompanyData
{
    const FUNCTIONNAME = 'lookupCompany';
    $input = ['organisasjonsnummer' => $orgNumber];

    // Start span
    $span = sovdev_start_span(FUNCTIONNAME, $input);

    try {
        // Logs automatically get trace_id from active span
        sovdev_log(SOVDEV_LOGLEVELS::INFO, FUNCTIONNAME, "Looking up $orgNumber", PEER_SERVICES::BRREG, $input);

        $data = fetchCompanyData($orgNumber);

        $response = [
            'navn' => $data->navn,
            'organisasjonsform' => $data->organisasjonsform->beskrivelse
        ];
        sovdev_log(SOVDEV_LOGLEVELS::INFO, FUNCTIONNAME, "Found: {$data->navn}", PEER_SERVICES::BRREG, $input, $response);

        // End span on success
        sovdev_end_span($span);

        return $data;

    } catch (Exception $error) {
        sovdev_log(SOVDEV_LOGLEVELS::ERROR, FUNCTIONNAME, "Failed to lookup $orgNumber", PEER_SERVICES::BRREG, $input, null, $error);

        // End span on error
        sovdev_end_span($span, $error);

        throw $error;
    }
}
```

---

## Summary

### Quick Reference

| Approach | When to Use | What You Get | Complexity |
|----------|-------------|--------------|------------|
| **Manual spans** | All production code, recommended everywhere | Timing, hierarchy, traces in Grafana, automatic trace_id | Low |

### Key Takeaways

1. **Hierarchy** → Trace (book) > trace_id (ISBN) > Spans (chapters) > span_id (chapter numbers)
2. **trace_id = Automatically Generated** → Created by spans, groups all related operations
3. **Span = Stopwatch** → Records operation timing and creates/inherits trace_id
4. **Trace = Collection of Spans** → Shows complete request flow, identified by trace_id
5. **Manual pattern works everywhere** → Use this first (universal across languages)
6. **Logs auto-detect active spans** → No parameters needed - trace_id added automatically
7. **Always end spans** → Memory leak if you forget
8. **Progressive enhancement** → Start with logs, add spans when ready

**Think of it like a book:**
- **Trace** = The entire book (your complete request)
- **trace_id** = ISBN number (groups all chapters together)
- **Span** = A chapter in the book (one operation)
- **span_id** = Chapter number (identifies this specific operation)

---

**Last Updated:** 2025-10-17
**Status:** DRAFT - Target state documented (spans-only approach)
**Next Step:** Implement `sovdev_start_span()` and `sovdev_end_span()` in TypeScript (reference implementation), then Python and Go
**See Also:** terchris/plans-current/changing-traceid2span-plan.md for detailed implementation plan
