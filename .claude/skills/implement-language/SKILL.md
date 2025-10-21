---
description: "Systematically implement sovdev-logger in a new programming language following the specification checklist. Use when implementing Python, Go, Rust, C#, PHP, or other languages."
---

# Implement Language Skill

When the user asks to implement sovdev-logger in a new programming language, guide them through the complete 7-phase systematic process.

## Before You Start

**CRITICAL**: This is not a simple code translation task. Each language's OpenTelemetry SDK behaves differently. You MUST study both the TypeScript reference AND the target language SDK before writing code.

**Common mistakes to prevent**:
- ❌ Skipping language toolchain verification
- ❌ Not studying OTEL SDK differences
- ❌ Claiming "complete" without Grafana validation
- ❌ Using semantic convention defaults (dots) instead of underscores
- ❌ Forgetting to create SDK comparison document

## Phase 0: Pre-Implementation Setup

**MUST complete ALL items before writing any code.**

### 1. Read CRITICAL Documents

Read these documents in order:
1. `specification/11-otel-sdk.md` - **⚠️ CRITICAL**: OpenTelemetry SDK differences between languages
2. `specification/12-llm-checklist-template.md` - Systematic implementation checklist
3. `specification/00-design-principles.md` - Core philosophy
4. `specification/01-api-contract.md` - API requirements (8 functions)
5. `specification/10-development-loop.md` - Iterative development workflow

### 2. Copy Checklist Template

Create workspace and copy checklist:
```bash
mkdir -p {language}/llm-work {language}/test/e2e/company-lookup
cp specification/12-llm-checklist-template.md {language}/llm-work/llm-checklist-{language}.md
```

**Update checklist header** with language name and date.

### 3. Verify Language Toolchain

**Before coding**, verify the language runtime is installed in DevContainer:

```bash
# Check if language is installed
./specification/tools/in-devcontainer.sh -e "{language-version-command}"

# Examples:
# Python: python3 --version
# Go: go version
# Rust: rustc --version
# C#: dotnet --version
# PHP: php --version
```

**If not installed**: Run `.devcontainer/additions/install-dev-{language}.sh` if it exists.

**Update checklist**: Mark "Checked if language is installed" as complete.

### 4. Verify OpenTelemetry SDK Exists

Visit https://opentelemetry.io/docs/languages/ and verify:
- ✅ SDK exists for the language
- ✅ SDK status (Stable/Beta/Alpha)
- ✅ SDK supports: Logs ✅ Metrics ✅ Traces ✅

**Document in checklist**: SDK status and any limitations.

### 5. Study TypeScript Reference Implementation

Read and understand:
- `typescript/src/logger.ts` - The source of truth
- TypeScript OTEL SDK docs: https://opentelemetry.io/docs/languages/js/

**Understand how TypeScript**:
- Initializes providers (log, metric, trace)
- Configures OTLP exporters
- Sets headers (`Host: otel.localhost`)
- Creates metric instruments
- Sets metric attributes (underscore notation: `peer_service`, `log_type`, `log_level`)
- Records duration (milliseconds via Date.now())
- Specifies histogram unit (`unit: 'ms'`)

**Update checklist**: Mark all TypeScript understanding items as complete.

### 6. Study Target Language OTEL SDK

Read target language OTEL SDK documentation:
- Getting Started guide
- Logs API documentation
- Metrics API documentation
- Traces API documentation
- OTLP HTTP Exporter documentation

**Answer these critical questions** (document in SDK comparison):

| Question | TypeScript Answer | {Language} Answer | Issue? | Workaround? |
|----------|-------------------|-------------------|---------|-------------|
| HTTP headers work? | Yes via `headers` | ? | ? | ? |
| Attribute notation? | Underscores (`peer_service`) | ? | ? | ? |
| Time unit? | Milliseconds (Date.now()) | ? | ? | ? |
| Histogram unit? | `unit: 'ms'` option | ? | ? | ? |
| Semantic conventions? | Manual attributes | ? | ? | ? |

### 7. Create SDK Comparison Document

Create `{language}/llm-work/otel-sdk-comparison.md` documenting:
- HTTP client behavior (can it set custom Host header?)
- Metric attribute patterns (dots vs underscores)
- Duration/time handling (seconds? milliseconds? nanoseconds?)
- Histogram configuration (how to specify unit?)
- Known issues and workarounds

**Template available**: See `specification/11-otel-sdk.md` for comparison template.

**Update checklist**: Mark "Created SDK comparison document" as complete.

## Phase 1-6: Implementation

Follow the checklist systematically at `{language}/llm-work/llm-checklist-{language}.md`.

### Key Principles

1. **Use Established Logging Libraries** (DO NOT reinvent)
   - TypeScript: Winston
   - Python: logging stdlib + RotatingFileHandler
   - Go: zap or logrus + lumberjack
   - Java: SLF4J + Logback
   - C#: Serilog or NLog
   - PHP: Monolog
   - Rust: tracing or log + env_logger

2. **Build Library Before Testing**
   Each language has a build script: `{language}/build-sovdevlogger.sh`
   ```bash
   ./specification/tools/in-devcontainer.sh -e "cd /workspace/{language} && ./build-sovdevlogger.sh"
   ```

3. **API Naming Conventions**
   - TypeScript/Python: snake_case (`sovdev_log`, `sovdev_initialize`)
   - Go: PascalCase (`SovdevLog`, `SovdevInitialize`) - Go exported function convention
   - **Field names**: ALWAYS snake_case (`service_name`, `function_name`, `trace_id`)

4. **All 8 API Functions Required**
   - `SovdevInitialize(serviceName, serviceVersion, peerServices)`
   - `SovdevLog(level, functionName, message, peerService, input, response, error, traceId)`
   - `SovdevLogJobStatus(level, functionName, jobName, status, peerService, metadata, traceId)`
   - `SovdevLogJobProgress(level, functionName, itemName, current, total, peerService, metadata, traceId)`
   - `SovdevGenerateTraceID()`
   - `SovdevFlush()`
   - `CreatePeerServices(mappings)`
   - `SOVDEV_LOGLEVELS` (DEBUG, INFO, WARN, ERROR, FATAL)

5. **File Logging Configuration**
   - Main log: 50 MB max, 5 files
   - Error log: 10 MB max, 3 files
   - Use language's established file rotation library

6. **Development Loop** (use for rapid iteration)
   - Edit code
   - Build library: `./build-sovdevlogger.sh`
   - Run test: `./specification/tools/run-company-lookup.sh {language}`
   - Validate logs FIRST: `./specification/tools/validate-log-format.sh {language}/test/e2e/company-lookup/logs/dev.log`
   - Validate OTLP SECOND: `./specification/tools/run-full-validation.sh {language}`

## Phase 5: Validation (CRITICAL)

**DO NOT claim implementation complete until ALL of these pass:**

### 1. File Log Validation
```bash
./specification/tools/in-devcontainer.sh -e "cd /workspace/specification/tools && ./validate-log-format.sh {language}/test/e2e/company-lookup/logs/dev.log"
```

Expected: ✅ PASS with 17 log entries, 13 unique trace IDs

### 2. OTLP Validation
```bash
sleep 10  # Wait for propagation
./specification/tools/in-devcontainer.sh -e "cd /workspace/specification/tools && ./run-full-validation.sh {language}"
```

Expected: ✅ Logs in Loki, metrics in Prometheus, traces in Tempo

### 3. Grafana Dashboard Validation (MOST CRITICAL - Often Skipped!)

**Open**: http://grafana.localhost
**Navigate to**: Structured Logging Testing Dashboard

**Verify ALL 3 panels show data for BOTH languages**:

**Panel 1: Total Operations**
- [ ] TypeScript shows "Last" value
- [ ] {Language} shows "Last" value
- [ ] TypeScript shows "Max" value
- [ ] {Language} shows "Max" value

**Panel 2: Error Rate**
- [ ] TypeScript shows "Last %" value
- [ ] {Language} shows "Last %" value
- [ ] TypeScript shows "Max %" value
- [ ] {Language} shows "Max %" value

**Panel 3: Average Operation Duration**
- [ ] TypeScript shows entries for all peer services
- [ ] {Language} shows entries for all peer services
- [ ] Values are in milliseconds (e.g., 0.538 ms, NOT 0.000538)

**If ANY panel missing data**: Implementation is NOT complete. Debug using query tools.

### 4. Metric Label Comparison

Compare metric labels between TypeScript and new language:

```bash
./specification/tools/in-devcontainer.sh -e "cd /workspace/specification/tools && ./query-prometheus.sh 'sovdev_operations_total{service_name=~\".*typescript.*\"}' > /tmp/ts.txt"

./specification/tools/in-devcontainer.sh -e "cd /workspace/specification/tools && ./query-prometheus.sh 'sovdev_operations_total{service_name=~\".*{language}.*\"}' > /tmp/lang.txt"
```

**Verify labels IDENTICAL**:
- ✅ `peer_service` (underscore, NOT peer.service)
- ✅ `log_type` (underscore, NOT log.type or function.name)
- ✅ `log_level` (underscore, NOT log.level)
- ✅ `service_name`
- ✅ `service_version`

**Common mistake**: Using semantic convention defaults (dots) instead of manual underscores.

## Completion Criteria

**DO NOT claim implementation complete until ALL checked:**

- [ ] ✅ Language toolchain installed and verified
- [ ] ✅ OTEL SDK verified (Stable/Beta, supports logs/metrics/traces)
- [ ] ✅ TypeScript reference studied and understood
- [ ] ✅ Target language SDK studied and understood
- [ ] ✅ SDK comparison document created and complete
- [ ] ✅ All 8 API functions implemented
- [ ] ✅ File logging works with rotation
- [ ] ✅ OTLP export works (logs, metrics, traces)
- [ ] ✅ E2E test implemented and passes
- [ ] ✅ File log validation PASSES
- [ ] ✅ OTLP validation PASSES
- [ ] ✅ **Grafana dashboard shows data in ALL 3 panels for this language**
- [ ] ✅ Metric labels IDENTICAL to TypeScript (underscores, correct names)
- [ ] ✅ Duration values in milliseconds
- [ ] ✅ Histogram has unit specification
- [ ] ✅ Documentation complete

**Only when ALL items above are checked: "Implementation COMPLETE ✅"**

## Anti-Patterns to Avoid

From Go and Python implementation experience:

❌ **DON'T**: Skip language toolchain verification
✅ **DO**: Check toolchain first, install if needed

❌ **DON'T**: Use semantic convention defaults (peer.service, log.level)
✅ **DO**: Manually set attributes with underscores (peer_service, log_level)

❌ **DON'T**: Claim complete without Grafana validation
✅ **DO**: Verify ALL 3 Grafana panels show data

❌ **DON'T**: Forget SDK comparison document
✅ **DO**: Create comparison before coding

❌ **DON'T**: Implement custom file writing/rotation
✅ **DO**: Use established logging libraries

❌ **DON'T**: Record duration in seconds (Go default)
✅ **DO**: Convert to milliseconds for consistency

## Getting Help

**Specification issues**: See `specification/` documents (00-12)
**Tool usage**: See `specification/tools/README.md`
**DevContainer problems**: See `specification/05-environment-configuration.md`
**OTEL SDK issues**: See `specification/11-otel-sdk.md` Language-Specific Known Issues

## Success

When implementation is complete:
1. Update `{language}/llm-work/llm-checklist-{language}.md` - mark all items complete
2. Document any issues encountered in checklist "Issues Encountered" section
3. Create `{language}/README.md` with quick start guide
4. Celebrate! 🎉 The implementation is production-ready.

---

**Remember**: Specification is source of truth. When in doubt, check `specification/` folder or ask for clarification.
