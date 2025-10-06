/**
 * Sovdev Logger - TypeScript Implementation
 *
 * Structured logging library implementing Winston best practices:
 * - Multiple simultaneous transports (console + file + OTLP)
 * - OpenTelemetry auto-instrumentation (no manual trace injection)
 * - Proper transport separation and formatting
 * - Enhanced OTLP log exporter configuration
 *
 * Implements "Loggeloven av 2025" requirements with the new standardized API
 * that is consistent across all programming languages (TypeScript, C#, PHP, Python).
 *
 * Features:
 * - Structured JSON logging with required fields
 * - Full OpenTelemetry integration (traces AND logs)
 * - Security-aware error handling (removes auth credentials)
 * - Consistent field naming (camelCase)
 * - Simple function-based API identical across languages
 * - Winston best practices implementation
 */

import winston from 'winston';
import TransportStream from 'winston-transport';
import { NodeSDK } from '@opentelemetry/sdk-node';
import { Resource } from '@opentelemetry/resources';
import { ATTR_SERVICE_NAME, ATTR_SERVICE_VERSION } from '@opentelemetry/semantic-conventions';
import { SEMRESATTRS_DEPLOYMENT_ENVIRONMENT } from '@opentelemetry/semantic-conventions';
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-http';
import { OTLPLogExporter } from '@opentelemetry/exporter-logs-otlp-http';
import { OTLPMetricExporter } from '@opentelemetry/exporter-metrics-otlp-http';
import { getNodeAutoInstrumentations } from '@opentelemetry/auto-instrumentations-node';
import { BatchLogRecordProcessor, LoggerProvider } from '@opentelemetry/sdk-logs';
import { PeriodicExportingMetricReader, MeterProvider } from '@opentelemetry/sdk-metrics';
import { BatchSpanProcessor, BasicTracerProvider } from '@opentelemetry/sdk-trace-base';
import { metrics, Counter, Histogram, UpDownCounter } from '@opentelemetry/api';
import { trace, Span, SpanStatusCode, context } from '@opentelemetry/api';
import { logs, SeverityNumber } from '@opentelemetry/api-logs';
import { v4 as uuidv4 } from 'uuid';
import { readFileSync } from 'fs';
import { join } from 'path';

// Import log levels from separate module
import { SOVDEV_LOGLEVELS, SovdevLogLevel } from './logLevels';

// =============================================================================
// TYPE DEFINITIONS
// =============================================================================

// =============================================================================
// OPENTELEMETRY METRICS CONFIGURATION
// =============================================================================

/**
 * Global metrics instances - automatically track operations
 */
interface SovdevMetrics {
  operationCounter: Counter;           // Total operations by service, peer, level
  errorCounter: Counter;               // Total errors by service, peer, exception type
  operationDuration: Histogram;        // Operation duration distribution
  activeOperations: UpDownCounter;     // Currently active operations
}

let globalMetrics: SovdevMetrics | null = null;
let globalMeterProvider: MeterProvider | null = null;
let globalTracerProvider: BasicTracerProvider | null = null;

/**
 * Auto-detect service version from environment or package.json
 */
function getServiceVersion(): string {
  // Try environment variables first (from CI/deployment)
  if (process.env.SERVICE_VERSION) {
    return process.env.SERVICE_VERSION;
  }

  if (process.env.npm_package_version) {
    return process.env.npm_package_version;
  }

  // Try reading package.json
  try {
    const packageJson = JSON.parse(
      readFileSync(join(process.cwd(), 'package.json'), 'utf8')
    );
    return packageJson.version || 'unknown';
  } catch {
    return 'unknown';
  }
}

/**
 * Complete structured log entry format - complies with "Loggeloven av 2025"
 * Uses OpenTelemetry/Elastic ECS standard field names for correlation
 */
interface StructuredLogEntry {
  // Required fields
  timestamp: string;
  level: string;

  // OTEL standard resource attributes
  "service.name": string;      // Service identifier (OTEL standard)
  "service.version": string;   // Service version (OTEL standard)
  "peer.service": string;      // Target system/service (OTEL standard)

  functionName: string;
  message: string;

  // Correlation fields (OpenTelemetry/ECS standard)
  traceId: string;      // Business transaction identifier (links related operations)
  eventId: string;      // Unique identifier for this log entry

  // Log classification
  logType: string;      // Type of log: "transaction", "job.status", "job.progress"

  // Context fields
  inputJSON?: any;
  responseJSON?: any;
  exception?: {
    type: string;
    message: string;
    stack?: string;
  };
}

// =============================================================================
// WINSTON TRANSPORT CONFIGURATION (BEST PRACTICES)
// =============================================================================

/**
 * Custom Winston transport that sends logs to OpenTelemetry OTLP
 */
class OpenTelemetryWinstonTransport extends TransportStream {
  private otelLogger: any;

  constructor(options: any = {}) {
    super(options);
    // Get OpenTelemetry logger instance using the serviceName from options
    this.otelLogger = logs.getLogger(options.serviceName || 'default', '1.0.0');
  }

  log(info: any, callback: Function) {
    // Map Winston levels to OpenTelemetry severity
    const severityMap: { [key: string]: SeverityNumber } = {
      'debug': SeverityNumber.DEBUG,
      'info': SeverityNumber.INFO,
      'warn': SeverityNumber.WARN,
      'error': SeverityNumber.ERROR,
      'fatal': SeverityNumber.FATAL
    };

    try {
      // Build attributes object with OTEL standard fields
      const attributes: any = {
        "service.name": info["service.name"],
        "service.version": info["service.version"],
        "peer.service": info["peer.service"],
        functionName: info.functionName,
        timestamp: info.timestamp
      };

      // Add correlation fields (OpenTelemetry/ECS standard)
      if (info.traceId) {
        attributes.traceId = info.traceId;
      }
      if (info.eventId) {
        attributes.eventId = info.eventId;
      }

      // Add log classification
      if (info.logType) {
        attributes.logType = info.logType;
      }

      // Serialize inputJSON and responseJSON as JSON strings for OTLP
      if (info.inputJSON !== undefined) {
        attributes.inputJSON = JSON.stringify(info.inputJSON);
      }

      if (info.responseJSON !== undefined) {
        attributes.responseJSON = JSON.stringify(info.responseJSON);
      }

      // Add exception details if present
      if (info.exception) {
        attributes.exceptionType = info.exception.type;
        attributes.exceptionMessage = info.exception.message;
        if (info.exception.stack) {
          attributes.exceptionStack = info.exception.stack;
        }
      }

      // Emit log record to OpenTelemetry
      this.otelLogger.emit({
        severityNumber: severityMap[info.level] || SeverityNumber.INFO,
        severityText: info.level.toUpperCase(),
        body: info.message,
        attributes
      });
    } catch (err) {
      // Don't fail Winston if OTLP fails
      console.error('❌ OpenTelemetry Winston transport failed:', err);
    }

    // Call callback to indicate transport is done
    if (callback) {
      callback();
    }
  }
}

/**
 * Create Winston transports following best practices
 * - Console: Smart default (auto-enabled if no OTLP), or explicit via LOG_TO_CONSOLE
 * - File: Smart default (enabled), or explicit via LOG_TO_FILE
 * - OpenTelemetry: OTLP transport for centralized logging (always enabled)
 * - Multiple simultaneous transports (not either/or)
 */
function createTransports(serviceName?: string): winston.transport[] {
  const transports: winston.transport[] = [];

  // 1. CONSOLE TRANSPORT: Optional, controlled by LOG_TO_CONSOLE environment variable
  //    Smart default: enabled if no OTLP endpoint configured (fallback), otherwise disabled
  const isDevelopment = process.env.NODE_ENV !== 'production';
  const hasOtlpEndpoint = !!process.env.OTEL_EXPORTER_OTLP_LOGS_ENDPOINT;
  const logToConsole = process.env.LOG_TO_CONSOLE !== undefined
    ? process.env.LOG_TO_CONSOLE === 'true'
    : !hasOtlpEndpoint; // Auto-enable if no OTLP configured

  if (logToConsole) {
    // Colored output for human readability (development mode)
    if (isDevelopment) {
      transports.push(
        new winston.transports.Console({
          format: winston.format.combine(
            winston.format.colorize({ all: true }),
            winston.format.timestamp({ format: 'HH:mm:ss' }),
            winston.format.printf((info) => {
              const serviceName = info["service.name"] || 'unknown';
              return `${info.timestamp} [${info.level}] ${serviceName}:${info.functionName} - ${info.message}`;
            })
          )
        })
      );
    } else {
      // JSON output for production (no colors, structured)
      transports.push(
        new winston.transports.Console({
          format: winston.format.combine(
            winston.format.timestamp(),
            winston.format.json()
          )
        })
      );
    }
  }

  // 2. FILE TRANSPORT: Smart default (enabled unless explicitly disabled)
  const logToFile = process.env.LOG_TO_FILE !== undefined
    ? process.env.LOG_TO_FILE === 'true'
    : true; // Default: enabled

  if (logToFile) {
    const logFilePath = process.env.LOG_FILE_PATH || './logs/dev.log';

    transports.push(
      new winston.transports.File({
        filename: logFilePath,
        format: winston.format.combine(
          winston.format.timestamp(),
          winston.format.json()
        ),
        maxsize: 50 * 1024 * 1024, // 50MB max file size
        maxFiles: 5, // Keep 5 rotated files
        tailable: true // Use rotating file names
      })
    );

    console.log(`📝 File logging enabled: ${logFilePath}`);
  }

  // 3. ERROR FILE TRANSPORT: Separate file for errors only (best practice)
  if (logToFile) {
    const errorLogPath = process.env.ERROR_LOG_PATH || './logs/error.log';
    
    transports.push(
      new winston.transports.File({
        filename: errorLogPath,
        level: 'error',
        format: winston.format.combine(
          winston.format.timestamp(),
          winston.format.json()
        ),
        maxsize: 10 * 1024 * 1024, // 10MB max file size
        maxFiles: 3 // Keep 3 rotated error files
      })
    );
  }

  // 4. OPENTELEMETRY TRANSPORT: Always enabled for centralized logging
  if (serviceName) {
    transports.push(
      new OpenTelemetryWinstonTransport({
        serviceName: serviceName,
        level: 'silly' // Include all levels
      })
    );
    console.log('📡 OpenTelemetry Winston transport configured');
  }

  return transports;
}

/**
 * Winston logger configuration for structured output
 * Uses multiple simultaneous transports following best practices
 */
let baseLogger: winston.Logger;

/**
 * Initialize Winston logger with serviceName for OpenTelemetry transport
 */
function initializeWinstonLogger(serviceName: string): void {
  baseLogger = winston.createLogger({
    level: 'silly', // Include all levels (silly = trace)
    transports: createTransports(serviceName),
    exitOnError: false // Don't exit on handled exceptions
  });
}

// =============================================================================
// INTERNAL LOGGER IMPLEMENTATION
// =============================================================================

/**
 * Internal logger class - handles all complexity, hidden from developers
 * IMPROVED: No manual trace injection - relies on OpenTelemetry auto-instrumentation
 */
class InternalSovdevLogger {
  private readonly serviceName: string;
  private readonly serviceVersion: string;
  private readonly systemIdsMapping: Record<string, string>;

  constructor(serviceName: string, serviceVersion: string, systemIds: Record<string, string> = {}) {
    this.serviceName = serviceName;
    this.serviceVersion = serviceVersion;
    this.systemIdsMapping = systemIds;
  }

  /**
   * Resolve friendly name to CMDB ID or service name for internal operations
   */
  private resolvePeerService(friendlyName?: string): string {
    // Default to INTERNAL if no peer service provided
    const effectiveName = friendlyName || "INTERNAL";

    // If INTERNAL, use the service's own name
    if (effectiveName === "INTERNAL") {
      return this.serviceName;
    }

    // Try to resolve from mapping
    const resolvedId = this.systemIdsMapping[effectiveName];
    if (!resolvedId) {
      console.warn(`⚠️ Unknown peer service: ${effectiveName}. Available: ${Object.keys(this.systemIdsMapping).join(', ')} or INTERNAL`);
      return effectiveName; // Use as-is if not found
    }
    return resolvedId;
  }

  /**
   * Create a complete structured log entry with all required fields
   * Uses OpenTelemetry/ECS standard field names for correlation
   */
  private createLogEntry(
    level: SovdevLogLevel,
    functionName: string,
    message: string,
    peerService?: string,
    exceptionObject?: any,
    inputJSON?: any,
    responseJSON?: any,
    traceId?: string,
    logType?: string
  ): StructuredLogEntry {
    // Generate unique event ID for this log entry
    const eventId = uuidv4();

    // Use provided traceId or generate new one
    const finalTraceId = traceId || uuidv4();

    // Resolve friendly name to CMDB ID (defaults to service.name for INTERNAL)
    const resolvedPeerService = this.resolvePeerService(peerService);

    // Process exception object if provided
    let processedException;
    if (exceptionObject) {
      processedException = this.processException(exceptionObject);
    }

    // Create the complete log entry with OTEL standard fields
    const logEntry: StructuredLogEntry = {
      timestamp: new Date().toISOString(),
      level,
      "service.name": this.serviceName,
      "service.version": this.serviceVersion,
      "peer.service": resolvedPeerService,
      functionName,
      message,
      traceId: finalTraceId,
      eventId: eventId,
      logType: logType || 'transaction',  // Default to transaction if not specified
      inputJSON,
      responseJSON,
      exception: processedException
    };

    // Remove undefined fields for cleaner JSON
    return this.removeUndefinedFields(logEntry);
  }

  /**
   * Process exception objects with security cleanup and standardization
   */
  private processException(exceptionObject: any): { type: string; message: string; stack?: string } {
    let cleanException = exceptionObject;
    
    // Security: Remove sensitive data from axios errors
    if (typeof exceptionObject === 'object' && exceptionObject !== null) {
      if (exceptionObject.config?.auth) {
        cleanException = { ...exceptionObject };
        delete cleanException.config.auth;
      }
      if (exceptionObject.config?.headers?.Authorization) {
        cleanException = { ...cleanException };
        delete cleanException.config.headers.Authorization;
      }
    }

    // Extract exception information
    if (typeof cleanException === 'object' && cleanException !== null) {
      let stackTrace = cleanException.stack || '';
      
      // Limit stack trace to 350 characters
      if (stackTrace.length > 350) {
        stackTrace = stackTrace.substring(0, 350);
      }

      return {
        type: cleanException.constructor?.name || cleanException.name || 'Error',
        message: cleanException.message || String(cleanException),
        stack: stackTrace
      };
    } else {
      return {
        type: 'Unknown',
        message: String(cleanException)
      };
    }
  }

  /**
   * Remove undefined fields for cleaner JSON output
   */
  private removeUndefinedFields(obj: any): any {
    return Object.fromEntries(
      Object.entries(obj).filter(([_, value]) => value !== undefined)
    );
  }

  /**
   * Write log entry using Winston (multiple transports including OTLP)
   * IMPROVED: Automatically emit metrics AND trace spans for complete observability
   */
  private writeLog(level: string, logEntry: StructuredLogEntry): void {
    const startTime = Date.now();
    let span: Span | undefined;

    try {
      // Create automatic trace span (zero developer effort)
      if (globalTracerProvider) {
        const tracer = trace.getTracer(logEntry['service.name'], logEntry['service.version']);

        // Create span with operation name from function + log type
        const spanName = `${logEntry.functionName} [${logEntry.logType}]`;
        span = tracer.startSpan(spanName, {
          attributes: {
            'service.name': logEntry['service.name'],
            'service.version': logEntry['service.version'],
            'peer.service': logEntry['peer.service'],
            'log.level': level,
            'log.type': logEntry.logType,
            'function.name': logEntry.functionName,
            'trace.id': logEntry.traceId,
            'event.id': logEntry.eventId
          }
        });

        // Add input/response data as span events
        if (logEntry.inputJSON) {
          span.addEvent('input', { 'input.data': JSON.stringify(logEntry.inputJSON) });
        }
        if (logEntry.responseJSON) {
          span.addEvent('response', { 'response.data': JSON.stringify(logEntry.responseJSON) });
        }

        // Mark span as error if exception present
        if (logEntry.exception) {
          span.setStatus({ code: SpanStatusCode.ERROR, message: logEntry.exception.message });
          span.recordException({
            name: logEntry.exception.type,
            message: logEntry.exception.message,
            stack: logEntry.exception.stack
          });
        } else if (level === 'ERROR' || level === 'FATAL') {
          span.setStatus({ code: SpanStatusCode.ERROR, message: logEntry.message });
        } else {
          span.setStatus({ code: SpanStatusCode.OK });
        }
      }

      // Emit metrics automatically (zero developer effort)
      if (globalMetrics) {
        const attributes = {
          'service.name': logEntry['service.name'],
          'service.version': logEntry['service.version'],
          'peer.service': logEntry['peer.service'],
          'log.level': level,
          'log.type': logEntry.logType
        };

        // Increment active operations
        globalMetrics.activeOperations.add(1, attributes);

        // Increment operation counter
        globalMetrics.operationCounter.add(1, attributes);

        // Track errors separately
        if (level === 'ERROR' || level === 'FATAL' || logEntry.exception) {
          const errorAttributes = {
            ...attributes,
            'exception.type': logEntry.exception?.type || 'Unknown'
          };
          globalMetrics.errorCounter.add(1, errorAttributes);
        }
      }

      // Send to Winston - Winston will handle all transports including OTLP
      const winstonLevel = this.mapToWinstonLevel(level);
      baseLogger.log(winstonLevel, logEntry);

      // Record operation duration and decrement active operations
      if (globalMetrics) {
        const duration = Date.now() - startTime;
        const attributes = {
          'service.name': logEntry['service.name'],
          'service.version': logEntry['service.version'],
          'peer.service': logEntry['peer.service'],
          'log.level': level,
          'log.type': logEntry.logType
        };
        globalMetrics.operationDuration.record(duration, attributes);
        globalMetrics.activeOperations.add(-1, attributes);
      }

      // End the span
      if (span) {
        span.end();
      }

    } catch (err) {
      // Fallback - logging should never break the application
      console.error('Sovdev Logger failed:', err);
      console.log(JSON.stringify(logEntry));

      // Mark span as error and end it
      if (span) {
        span.setStatus({ code: SpanStatusCode.ERROR, message: String(err) });
        span.end();
      }

      // Decrement active operations on error
      if (globalMetrics) {
        const attributes = {
          'service.name': logEntry['service.name'],
          'service.version': logEntry['service.version'],
          'peer.service': logEntry['peer.service'],
          'log.level': level,
          'log.type': logEntry.logType
        };
        globalMetrics.activeOperations.add(-1, attributes);
      }
    }
  }


  /**
   * Map custom log levels to Winston levels
   * IMPROVED: Better level mapping strategy
   */
  private mapToWinstonLevel(level: string): string {
    switch (level) {
      case 'TRACE': return 'debug';  // Winston doesn't have trace, map to debug
      case 'DEBUG': return 'debug';
      case 'INFO': return 'info';
      case 'WARN': return 'warn';
      case 'ERROR': return 'error';
      case 'FATAL': return 'error';  // Winston doesn't have fatal, map to error
      default: return 'info';
    }
  }


  /**
   * Main logging method - for transaction/request-response logs
   */
  public log(
    level: SovdevLogLevel,
    functionName: string,
    message: string,
    peerService: string,
    inputJSON?: any,
    responseJSON?: any,
    exceptionObject?: any,
    traceId?: string
  ): void {
    const logEntry = this.createLogEntry(level, functionName, message, peerService, exceptionObject, inputJSON, responseJSON, traceId, 'transaction');
    this.writeLog(level, logEntry);
  }

  /**
   * Job status logging - for batch job start/complete/failed events
   */
  public logJobStatus(
    level: SovdevLogLevel,
    functionName: string,
    jobName: string,
    status: string,
    peerService: string,
    inputJSON?: any,
    traceId?: string
  ): void {
    const message = `Job ${status}: ${jobName}`;
    const contextInput = {
      jobName,
      jobStatus: status,
      ...inputJSON
    };

    const logEntry = this.createLogEntry(level, functionName, message, peerService, null, contextInput, null, traceId, 'job.status');
    this.writeLog(level, logEntry);
  }

  /**
   * Job progress logging - for tracking batch processing progress (X of Y)
   */
  public logJobProgress(
    level: SovdevLogLevel,
    functionName: string,
    jobName: string,
    itemId: string,
    current: number,
    total: number,
    peerService: string,
    inputJSON?: any,
    traceId?: string
  ): void {
    const message = `Processing ${itemId} (${current}/${total})`;
    const contextInput = {
      jobName,
      itemId,
      currentItem: current,
      totalItems: total,
      progressPercentage: Math.round((current / total) * 100),
      ...inputJSON
    };

    const logEntry = this.createLogEntry(level, functionName, message, peerService, null, contextInput, null, traceId, 'job.progress');
    this.writeLog(level, logEntry);
  }
}

// =============================================================================
// OPENTELEMETRY CONFIGURATION (IMPROVED)
// =============================================================================

/**
 * Configure OpenTelemetry Metrics
 * Creates automatic metrics for operations, errors, duration, and active operations
 */
function configureMetrics(serviceName: string, serviceVersion: string, sessionId: string): MeterProvider | null {
  try {
    const resource = new Resource({
      [ATTR_SERVICE_NAME]: serviceName,
      [ATTR_SERVICE_VERSION]: serviceVersion,
      [SEMRESATTRS_DEPLOYMENT_ENVIRONMENT]: process.env.NODE_ENV || 'development',
      'session.id': sessionId  // OTEL semantic convention for execution grouping
    });

    // Configure metric exporter with cumulative temporality for Prometheus compatibility
    const metricExporter = new OTLPMetricExporter({
      url: process.env.OTEL_EXPORTER_OTLP_METRICS_ENDPOINT || 'http://localhost:4318/v1/metrics',
      headers: process.env.OTEL_EXPORTER_OTLP_HEADERS ?
        JSON.parse(process.env.OTEL_EXPORTER_OTLP_HEADERS) : {},
      temporalityPreference: 1, // 1 = CUMULATIVE (Prometheus compatible)
    });

    // Create periodic metric reader (export every 10 seconds)
    const metricReader = new PeriodicExportingMetricReader({
      exporter: metricExporter,
      exportIntervalMillis: 10000, // 10 seconds
    });

    // Create MeterProvider
    const meterProvider = new MeterProvider({
      resource,
      readers: [metricReader],
    });

    // Set global meter provider
    metrics.setGlobalMeterProvider(meterProvider);

    // Create meter and metrics
    const meter = meterProvider.getMeter(serviceName, serviceVersion);

    globalMetrics = {
      operationCounter: meter.createCounter('sovdev.operations.total', {
        description: 'Total number of operations by service, peer service, and log level',
        unit: '1'
      }),

      errorCounter: meter.createCounter('sovdev.errors.total', {
        description: 'Total number of errors by service, peer service, and exception type',
        unit: '1'
      }),

      operationDuration: meter.createHistogram('sovdev.operation.duration', {
        description: 'Duration of operations in milliseconds',
        unit: 'ms'
      }),

      activeOperations: meter.createUpDownCounter('sovdev.operations.active', {
        description: 'Number of currently active operations',
        unit: '1'
      })
    };

    console.log('📊 OTLP Metrics configured for:', process.env.OTEL_EXPORTER_OTLP_METRICS_ENDPOINT || 'http://localhost:4318/v1/metrics');
    console.log('📊 Metrics: operations.total, errors.total, operation.duration, operations.active');
    console.log('📊 Temporality: CUMULATIVE (Prometheus compatible)');

    return meterProvider;

  } catch (error) {
    console.warn('⚠️  Metrics configuration failed:', error);
    return null;
  }
}

/**
 * Configure OpenTelemetry with both trace AND log exporters
 * IMPROVED: Full OTLP integration for complete observability
 */
function configureOpenTelemetry(serviceName: string, serviceVersion: string, sessionId: string): { sdk: NodeSDK | null, loggerProvider: LoggerProvider | null, tracerProvider: BasicTracerProvider | null } {
  try {
    const resource = new Resource({
      [ATTR_SERVICE_NAME]: serviceName,
      [ATTR_SERVICE_VERSION]: serviceVersion,
      [SEMRESATTRS_DEPLOYMENT_ENVIRONMENT]: process.env.NODE_ENV || 'development',
      'session.id': sessionId  // OTEL semantic convention for execution grouping
    });

    // Configure exporters based on environment
    const environment = process.env.NODE_ENV || 'development';

    // TRACE EXPORTER AND PROVIDER
    let tracerProvider: BasicTracerProvider | null = null;
    const traceEndpoint = process.env.OTEL_EXPORTER_OTLP_TRACES_ENDPOINT ||
                         process.env.OTEL_EXPORTER_OTLP_ENDPOINT ||
                         'http://localhost:4318/v1/traces';

    const traceExporter = new OTLPTraceExporter({
      url: traceEndpoint,
      headers: process.env.OTEL_EXPORTER_OTLP_HEADERS ?
        JSON.parse(process.env.OTEL_EXPORTER_OTLP_HEADERS) : {},
    });

    // Create BasicTracerProvider with BatchSpanProcessor
    tracerProvider = new BasicTracerProvider({
      resource
    });
    tracerProvider.addSpanProcessor(new BatchSpanProcessor(traceExporter));

    // Set global tracer provider
    trace.setGlobalTracerProvider(tracerProvider);
    console.log('🔍 OTLP Trace exporter configured for:', traceEndpoint);

    // LOG EXPORTER (NEW - IMPROVED)
    let loggerProvider: LoggerProvider | null = null;
    const logEndpoint = process.env.OTEL_EXPORTER_OTLP_LOGS_ENDPOINT;
    
    if (logEndpoint || environment === 'development') {
      const logExporter = new OTLPLogExporter({
        url: logEndpoint || 'http://localhost:4318/v1/logs',
        headers: process.env.OTEL_EXPORTER_OTLP_HEADERS ? 
          JSON.parse(process.env.OTEL_EXPORTER_OTLP_HEADERS) : {},
      });
      
      const logRecordProcessor = new BatchLogRecordProcessor(logExporter);
      loggerProvider = new LoggerProvider({
        resource
      });
      loggerProvider.addLogRecordProcessor(logRecordProcessor);
      console.log('📡 OTLP Log exporter configured for:', logEndpoint || 'http://localhost:4318/v1/logs');
      console.log('📡 BatchLogRecordProcessor added to LoggerProvider');
    }

    // NODE SDK CONFIGURATION (optional auto-instrumentation)
    const sdk = new NodeSDK({
      resource,
      instrumentations: [
        getNodeAutoInstrumentations({
          // Enable Winston instrumentation for automatic trace context injection
          '@opentelemetry/instrumentation-winston': { enabled: true },
          // Disable verbose instrumentations for development
          '@opentelemetry/instrumentation-fs': { enabled: false },
          '@opentelemetry/instrumentation-dns': { enabled: false },
        }),
      ],
    });

    console.log('🔗 OpenTelemetry SDK initialized for', serviceName);
    console.log('🔍 Auto-instrumentation includes Winston integration');

    return { sdk, loggerProvider, tracerProvider };

  } catch (error) {
    console.warn('⚠️  OpenTelemetry SDK configuration failed:', error);
    return { sdk: null, loggerProvider: null, tracerProvider: null as BasicTracerProvider | null };
  }
}

// =============================================================================
// GLOBAL LOGGER INSTANCE MANAGEMENT
// =============================================================================

/**
 * Global logger instance - initialized once per application
 */
let globalLogger: InternalSovdevLogger | null = null;

/**
 * Global OpenTelemetry SDK instance
 */
let otelSDK: NodeSDK | null = null;

/**
 * Global OpenTelemetry LoggerProvider instance for flushing
 */
let globalLoggerProvider: LoggerProvider | null = null;

/**
 * Initialize the Sovdev logger with system identifier and OpenTelemetry SDK
 * Must be called once at application startup
 *
 * @param serviceName Service name (e.g., "company-lookup-integration")
 * @param serviceVersion Service version (optional, auto-detected from package.json)
 * @param peerServices Mapping of peer service names to system IDs (use PEER_SERVICES.mappings)
 */
function initializeSovdevLogger(
  serviceName: string,
  serviceVersion?: string,
  peerServices: Record<string, string> = {}
): void {
  const effectiveServiceName = serviceName;
  const effectiveServiceVersion = serviceVersion || getServiceVersion();

  // Automatically add INTERNAL peer service pointing to this service
  const effectiveSystemIds = {
    INTERNAL: serviceName,  // Always auto-generated
    ...peerServices
  };

  if (!effectiveServiceName || effectiveServiceName.trim() === '') {
    throw new Error(
      'Sovdev Logger: serviceName is required. ' +
      'Example: initializeSovdevLogger("company-lookup-integration", "1.2.3", {...})'
    );
  }

  // Generate session ID once for this execution (OTEL semantic convention)
  // This automatically groups all logs, metrics, and traces from this run
  const sessionId = uuidv4();
  console.log(`🔑 Session ID: ${sessionId}`);

  // Initialize OpenTelemetry Metrics FIRST (before SDK)
  if (!globalMeterProvider) {
    globalMeterProvider = configureMetrics(effectiveServiceName, effectiveServiceVersion, sessionId);
  }

  // Initialize OpenTelemetry SDK with full configuration
  if (!otelSDK) {
    const { sdk, loggerProvider, tracerProvider } = configureOpenTelemetry(effectiveServiceName, effectiveServiceVersion, sessionId);
    otelSDK = sdk;
    globalLoggerProvider = loggerProvider;
    globalTracerProvider = tracerProvider;

    // CRITICAL: Set global logs provider BEFORE starting SDK and creating Winston logger
    // This ensures Winston's OpenTelemetryTransport gets the correct LoggerProvider
    if (loggerProvider) {
      logs.setGlobalLoggerProvider(loggerProvider);
      console.log('✅ Global LoggerProvider set');
    }

    if (otelSDK) {
      try {
        otelSDK.start();
        console.log('✅ OpenTelemetry SDK started successfully');
      } catch (error) {
        console.warn('⚠️  OpenTelemetry SDK start failed:', error);
        // Continue - logging should work without OTEL
      }
    }
  }

  // Initialize Winston logger with serviceName for OpenTelemetry transport
  // This must happen AFTER global LoggerProvider is set
  initializeWinstonLogger(effectiveServiceName.trim());

  globalLogger = new InternalSovdevLogger(
    effectiveServiceName.trim(),
    effectiveServiceVersion,
    effectiveSystemIds
  );

  const isDevelopment = process.env.NODE_ENV !== 'production';
  const hasOtlpEndpoint = !!process.env.OTEL_EXPORTER_OTLP_LOGS_ENDPOINT;
  const logToConsole = process.env.LOG_TO_CONSOLE !== undefined
    ? process.env.LOG_TO_CONSOLE === 'true'
    : !hasOtlpEndpoint;
  const logToFile = process.env.LOG_TO_FILE !== undefined
    ? process.env.LOG_TO_FILE === 'true'
    : true;

  console.log('🚀 Sovdev Logger initialized:');
  console.log(`   ├── Service: ${effectiveServiceName}`);
  console.log(`   ├── Version: ${effectiveServiceVersion}`);
  console.log(`   ├── Systems: ${Object.keys(effectiveSystemIds).join(', ') || 'None configured'}`);
  console.log(`   ├── Console: ${logToConsole ? (isDevelopment ? 'Colored (dev)' : 'JSON (prod)') : 'Disabled'}`);
  console.log(`   ├── File: ${logToFile ? 'Enabled' : 'Disabled'}`);
  console.log(`   └── OTLP: ${hasOtlpEndpoint ? 'Configured' : '⚠️  Not configured (using localhost:4318)'}`);

  if (!hasOtlpEndpoint && !logToConsole && !logToFile) {
    console.warn('⚠️  WARNING: All logging outputs are disabled!');
    console.warn('   Set OTEL_EXPORTER_OTLP_LOGS_ENDPOINT, LOG_TO_CONSOLE=true, or LOG_TO_FILE=true');
  }
}

/**
 * Ensure logger is initialized before use
 */
function ensureLogger(): InternalSovdevLogger {
  if (!globalLogger) {
    throw new Error(
      'Sovdev Logger not initialized. Call initializeSovdevLogger(systemId) at application startup.'
    );
  }
  return globalLogger;
}

// =============================================================================
// PUBLIC API - IDENTICAL ACROSS ALL LANGUAGES
// =============================================================================

/**
 * General purpose logging function
 *
 * @param level Log level from SOVDEV_LOGLEVELS constants
 * @param functionName Name of the function where logging occurs
 * @param message Human-readable description of what happened
 * @param peerService Peer service identifier (use PEER_SERVICE_INTERNAL for internal operations)
 * @param inputJSON Valid JSON object containing function input parameters (optional)
 * @param responseJSON Valid JSON object containing function output/response data (optional)
 * @param exceptionObject Exception/error object (optional, null if no exception)
 * @param traceId OpenTelemetry trace ID for correlating related logs (optional, auto-generated if not provided)
 */
export function sovdevLog(
  level: SovdevLogLevel,
  functionName: string,
  message: string,
  peerService: string,
  inputJSON?: any,
  responseJSON?: any,
  exceptionObject?: any,
  traceId?: string
): void {
  ensureLogger().log(level, functionName, message, peerService, inputJSON, responseJSON, exceptionObject, traceId);
}

/**
 * Log job lifecycle events (start, completion, failure)
 *
 * @param level Log level from SOVDEV_LOGLEVELS constants
 * @param functionName Name of the function managing the job
 * @param jobName Name of the job being tracked
 * @param status Job status (e.g., "Started", "Completed", "Failed")
 * @param inputJSON Additional job context variables (optional)
 * @param traceId OpenTelemetry trace ID for correlating related logs (optional, auto-generated if not provided)
 */
export function sovdevLogJobStatus(
  level: SovdevLogLevel,
  functionName: string,
  jobName: string,
  status: string,
  peerService: string,
  inputJSON?: any,
  traceId?: string
): void {
  ensureLogger().logJobStatus(level, functionName, jobName, status, peerService, inputJSON, traceId);
}

/**
 * Log processing progress for batch operations
 *
 * @param level Log level from SOVDEV_LOGLEVELS constants
 * @param functionName Name of the function doing the processing
 * @param itemId Identifier for the item being processed
 * @param current Current item number (1-based)
 * @param total Total number of items to process
 * @param inputJSON Additional context variables for this item (optional)
 * @param traceId OpenTelemetry trace ID for correlating related logs (optional, auto-generated if not provided)
 */
export function sovdevLogJobProgress(
  level: SovdevLogLevel,
  functionName: string,
  itemId: string,
  current: number,
  total: number,
  peerService: string,
  inputJSON?: any,
  traceId?: string
): void {
  ensureLogger().logJobProgress(level, functionName, "BatchProcessing", itemId, current, total, peerService, inputJSON, traceId);
}

// Export types for TypeScript consumers
export type { SovdevLogLevel, StructuredLogEntry };

/**
 * ARCHITECTURE SUMMARY:
 *
 * 1. Multiple Simultaneous Transports:
 *    ├── Console: Smart default (auto if no OTLP) or explicit via LOG_TO_CONSOLE
 *    ├── File: Smart default (on) or explicit via LOG_TO_FILE
 *    └── Error File: Separate file for errors only (when file enabled)
 *
 * 2. OpenTelemetry Full Integration:
 *    ├── Traces: OTLPTraceExporter → OTLP Endpoint
 *    ├── Logs: OTLPLogExporter → OTLP Endpoint
 *    └── Auto-Instrumentation: Winston integration
 *
 * 3. No Manual Trace Injection:
 *    ├── Removed manual trace.getActiveSpan() logic
 *    └── OpenTelemetry auto-instrumentation handles everything
 *
 * 4. Best Practices Implementation:
 *    ├── Winston native features (no custom file I/O)
 *    ├── Proper transport separation and formatting
 *    ├── Error handling and graceful degradation
 *    └── Environment-based configuration
 *
 * Usage:
 *    initializeSovdevLogger("your-system-id");
 *    sovdevLog(SOVDEV_LOGLEVELS.INFO, "MyFunction", "Message", null, input, response);
 */

// =============================================================================
// OPENTELEMETRY LOG FLUSHING
// =============================================================================

/**
 * Flush OpenTelemetry logs, metrics, and traces to ensure they are sent to OTLP collector
 * Call this before application exit to ensure all telemetry is exported
 */
async function flushSovdevLogs(): Promise<void> {
  try {
    if (globalTracerProvider) {
      console.log('🔄 Flushing OpenTelemetry traces...');
      await globalTracerProvider.forceFlush();
      console.log('✅ OpenTelemetry traces flushed successfully');
    }

    if (globalMeterProvider) {
      console.log('🔄 Flushing OpenTelemetry metrics...');
      await globalMeterProvider.forceFlush();
      console.log('✅ OpenTelemetry metrics flushed successfully');
    }

    if (globalLoggerProvider) {
      console.log('🔄 Flushing OpenTelemetry logs...');
      await globalLoggerProvider.forceFlush();
      console.log('✅ OpenTelemetry logs flushed successfully');
    }

    if (otelSDK) {
      console.log('🔄 Shutting down OpenTelemetry SDK...');
      await otelSDK.shutdown();
      console.log('✅ OpenTelemetry SDK shutdown complete');
    }

    if (globalTracerProvider) {
      console.log('🔄 Shutting down TracerProvider...');
      await globalTracerProvider.shutdown();
      console.log('✅ TracerProvider shutdown complete');
    }

    if (globalMeterProvider) {
      console.log('🔄 Shutting down MeterProvider...');
      await globalMeterProvider.shutdown();
      console.log('✅ MeterProvider shutdown complete');
    }
  } catch (error) {
    console.warn('⚠️  OpenTelemetry flush/shutdown failed:', error);
  }
}

// =============================================================================
// CONSISTENT NAMING ALIASES (sovdev* prefix for all functions)
// =============================================================================

/**
 * Initialize the Sovdev logger with service name, version, and system ID mappings
 * Must be called once at application startup
 *
 * @param serviceName Service name (e.g., "company-lookup-integration")
 * @param serviceVersion Service version (optional, auto-detected from package.json)
 * @param systemIds Mapping of friendly names to CMDB IDs (optional)
 *
 * @example
 * ```typescript
 * import { sovdevInitialize } from '@sovdev/logger';
 *
 * sovdevInitialize('company-lookup', '1.0.0', {
 *   'BRREG': process.env.BRREG_SYSTEM_ID,
 *   'CRM': process.env.CRM_SYSTEM_ID
 * });
 * ```
 */
export const sovdevInitialize = initializeSovdevLogger;

/**
 * Flush all OpenTelemetry telemetry (logs, metrics, traces) before app exit
 * Call this to ensure all buffered telemetry is sent to OTLP endpoints
 *
 * @example
 * ```typescript
 * import { sovdevFlush } from '@sovdev/logger';
 *
 * async function main() {
 *   // ... your application code ...
 *   await sovdevFlush();
 * }
 * ```
 */
export const sovdevFlush = flushSovdevLogs;

/**
 * Generate a unique trace ID for grouping related operations
 * Use this to link multiple log entries that belong to the same transaction/workflow
 *
 * @returns A unique UUID v4 string to use as traceId parameter in sovdevLog calls
 *
 * @example
 * ```typescript
 * // Generate one traceId for related operations
 * const companyTraceId = sovdevGenerateTraceId();
 *
 * // All these operations share the same traceId
 * sovdevLog(INFO, 'lookupCompany', 'Found', 'BRREG', null, input, output, companyTraceId);
 * sovdevLog(INFO, 'validateCompany', 'Valid', null, null, data, result, companyTraceId);
 * sovdevLog(INFO, 'saveCompany', 'Saved', 'Database', null, data, success, companyTraceId);
 *
 * // In Grafana: {traceId="<uuid>"} shows all 3 operations together
 * ```
 */
export function sovdevGenerateTraceId(): string {
  // Note: Future enhancement could add a prefix for easier trace identification
  // (e.g., `trace-${uuidv4()}` or `sovdev-${uuidv4()}`)
  // Decision: Keep plain UUID for now to maintain OpenTelemetry compatibility
  return uuidv4();
}