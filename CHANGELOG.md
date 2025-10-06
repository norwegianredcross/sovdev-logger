# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2025-10-06

### Initial Release

First public release of sovdev-logger - a structured logging library for OpenTelemetry with Norwegian Red Cross standards compliance.

#### Added

**Core Functionality:**
- TypeScript implementation with full OpenTelemetry integration
- Structured logging with Winston backend
- Automatic INTERNAL peer service generation for system identification
- Support for multiple peer services (external systems tracking)
- Transaction and session correlation via trace IDs
- Six standard log levels (error, warn, info, http, verbose, debug)

**OpenTelemetry Integration:**
- OTLP HTTP exporters for logs, metrics, and traces
- Automatic metrics generation (operations.total, errors.total, operation.duration, operations.active)
- Distributed tracing with automatic span creation
- Resource attributes following OpenTelemetry semantic conventions
- Integration with Loki (logs), Prometheus (metrics), and Tempo (traces)

**Logging Outputs:**
- Console logging with colorized output
- File logging with JSON format
- OTLP export to observability backends
- Configurable log levels and output formats

**Developer Experience:**
- Simple API: `sovdevInitializeLogger()` and `sovdevLog()`
- Automatic resource cleanup with `sovdevFlushAndShutdown()`
- Comprehensive TypeScript type definitions
- Environment variable support for configuration
- Detailed initialization feedback

**Testing & Quality:**
- 34 automated tests (18 unit, 16 integration, 10 E2E)
- Test coverage across all core functionality
- E2E tests with real observability stack (Loki, Prometheus, Tempo)
- GitHub Actions CI/CD pipeline
- Multi-version Node.js support (18, 20, 22)

**Documentation:**
- Comprehensive README with quick start guide
- Detailed data structure documentation
- Real-world examples (company lookup, batch processing)
- CONTRIBUTING.md with multi-language development guidelines
- MIT License

**Standards Compliance:**
- OpenTelemetry semantic conventions
- Norwegian data protection considerations (Loggeloven)
- Structured data format for GDPR compliance
- Service and resource attribution

#### Technical Details

**Dependencies:**
- @opentelemetry/api ^1.9.0
- @opentelemetry/sdk-node ^0.55.0
- winston ^3.17.0
- Full list in package.json

**Requirements:**
- Node.js >= 18.0.0
- TypeScript ^5.7.2 (for development)

**Package:**
- Published as `@sovdev/logger`
- ES modules and CommonJS support
- TypeScript declarations included

#### Future Plans

This initial release focuses on TypeScript. Future releases will include:
- Python implementation
- Go implementation
- C# implementation
- Rust implementation
- PHP implementation
- Java implementation

---

## Release Notes Format

For multi-language releases, we use the format `{language}-v{version}`:
- `typescript-v1.0.0`
- `python-v1.0.0` (future)
- `go-v1.0.0` (future)

Each language implementation maintains semantic versioning independently.
