package sovdevlogger

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"regexp"
	"strings"
	"sync"
	"time"

	"github.com/google/uuid"
	"gopkg.in/natefinch/lumberjack.v2"
	"go.opentelemetry.io/otel"
	"go.opentelemetry.io/otel/exporters/otlp/otlplog/otlploghttp"
	"go.opentelemetry.io/otel/exporters/otlp/otlpmetric/otlpmetrichttp"
	"go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracehttp"
	sdklog "go.opentelemetry.io/otel/sdk/log"
	sdkmetric "go.opentelemetry.io/otel/sdk/metric"
	"go.opentelemetry.io/otel/sdk/resource"
	sdktrace "go.opentelemetry.io/otel/sdk/trace"
	semconv "go.opentelemetry.io/otel/semconv/v1.24.0"
	"go.opentelemetry.io/otel/trace"
	"go.opentelemetry.io/otel/attribute"
	otlog "go.opentelemetry.io/otel/log"
	"go.opentelemetry.io/otel/metric"
	apitrace "go.opentelemetry.io/otel/trace"
)

// StructuredLogEntry represents a complete log entry compliant with "Loggeloven av 2025"
type StructuredLogEntry struct {
	Timestamp          string                 `json:"timestamp"`
	Level              string                 `json:"level,omitempty"`
	ServiceName        string                 `json:"service_name"`
	ServiceVersion     string                 `json:"service_version"`
	SessionID          string                 `json:"session_id"`
	PeerService        string                 `json:"peer_service"`
	FunctionName       string                 `json:"function_name"`
	Message            string                 `json:"message"`
	TraceID            string                 `json:"trace_id"`
	SpanID             string                 `json:"span_id,omitempty"`
	EventID            string                 `json:"event_id"`
	LogType            string                 `json:"log_type"`
	InputJSON          interface{}            `json:"input_json,omitempty"`
	ResponseJSON       interface{}            `json:"response_json,omitempty"`
	ExceptionType      string                 `json:"exception_type,omitempty"`
	ExceptionMessage   string                 `json:"exception_message,omitempty"`
	ExceptionStacktrace string                `json:"exception_stacktrace,omitempty"`
}

// Global logger instance
var (
	globalLogger       *sovdevLogger
	globalMutex        sync.RWMutex
	globalSessionID    string
	globalTracer       trace.Tracer
	globalMeter        metric.Meter
	globalLogProvider  *sdklog.LoggerProvider
	globalTraceProvider *sdktrace.TracerProvider
	globalMeterProvider *sdkmetric.MeterProvider

	// Metrics
	operationCounter   metric.Int64Counter
	errorCounter       metric.Int64Counter
	operationDuration  metric.Float64Histogram
	activeOperations   metric.Int64UpDownCounter
)

// sovdevLogger is the internal logger implementation
type sovdevLogger struct {
	serviceName       string
	serviceVersion    string
	sessionID         string
	peerServiceMap    map[string]string
	fileLogger        *log.Logger
	errorLogger       *log.Logger
	consoleLogger     *log.Logger
	otlpLogger        otlog.Logger
	logToConsole      bool
	logToFile         bool
}

// SovdevInitialize initializes the sovdev-logger with service information
func SovdevInitialize(serviceName string, serviceVersion string, peerServices map[string]string) error {
	globalMutex.Lock()
	defer globalMutex.Unlock()

	if serviceName == "" {
		return fmt.Errorf("service_name is required")
	}

	if serviceVersion == "" {
		serviceVersion = "1.0.0"
	}

	// Generate session ID
	globalSessionID = uuid.New().String()
	fmt.Printf("🔑 Session ID: %s\n", globalSessionID)

	// Add INTERNAL peer service
	effectivePeerServices := make(map[string]string)
	for k, v := range peerServices {
		effectivePeerServices[k] = v
	}
	effectivePeerServices["INTERNAL"] = serviceName

	// Initialize OpenTelemetry
	if err := initializeOpenTelemetry(serviceName, serviceVersion, globalSessionID); err != nil {
		fmt.Printf("⚠️  OpenTelemetry initialization warning: %v\n", err)
	}

	// Create file loggers
	logToFile := os.Getenv("LOG_TO_FILE") != "false"
	logToConsole := os.Getenv("LOG_TO_CONSOLE") != "false"

	var fileLogger, errorLogger, consoleLogger *log.Logger

	if logToFile {
		logPath := os.Getenv("LOG_FILE_PATH")
		if logPath == "" {
			logPath = "./logs/dev.log"
		}
		errorLogPath := os.Getenv("ERROR_LOG_PATH")
		if errorLogPath == "" {
			errorLogPath = "./logs/error.log"
		}

		// Ensure log directory exists
		os.MkdirAll("./logs", 0755)

		// Main log file with rotation
		fileWriter := &lumberjack.Logger{
			Filename:   logPath,
			MaxSize:    50, // megabytes
			MaxBackups: 5,
			MaxAge:     0, // days (0 = don't delete old files)
		}
		fileLogger = log.New(fileWriter, "", 0)

		// Error log file with rotation
		errorWriter := &lumberjack.Logger{
			Filename:   errorLogPath,
			MaxSize:    10, // megabytes
			MaxBackups: 3,
			MaxAge:     0,
		}
		errorLogger = log.New(errorWriter, "", 0)

		fmt.Printf("📝 File logging enabled: %s\n", logPath)
	}

	if logToConsole {
		consoleLogger = log.New(os.Stdout, "", 0)
	}

	var otlpLogger otlog.Logger
	if globalLogProvider != nil {
		otlpLogger = globalLogProvider.Logger(serviceName)
	}

	globalLogger = &sovdevLogger{
		serviceName:    serviceName,
		serviceVersion: serviceVersion,
		sessionID:      globalSessionID,
		peerServiceMap: effectivePeerServices,
		fileLogger:     fileLogger,
		errorLogger:    errorLogger,
		consoleLogger:  consoleLogger,
		otlpLogger:     otlpLogger,
		logToConsole:   logToConsole,
		logToFile:      logToFile,
	}

	fmt.Printf("🚀 Sovdev Logger initialized:\n")
	fmt.Printf("   ├── Service: %s\n", serviceName)
	fmt.Printf("   ├── Version: %s\n", serviceVersion)
	fmt.Printf("   ├── Session: %s\n", globalSessionID)
	fmt.Printf("   ├── Console: %v\n", logToConsole)
	fmt.Printf("   └── File: %v\n", logToFile)

	return nil
}

// hostOverrideTransport is an HTTP RoundTripper that overrides the Host header
type hostOverrideTransport struct {
	base http.RoundTripper
	host string
}

func (t *hostOverrideTransport) RoundTrip(req *http.Request) (*http.Response, error) {
	if t.host != "" {
		req.Host = t.host
		req.Header.Set("Host", t.host)
	}
	return t.base.RoundTrip(req)
}

// createHTTPClientWithHost creates an HTTP client that forces a specific Host header
func createHTTPClientWithHost(hostHeader string) *http.Client {
	return &http.Client{
		Transport: &hostOverrideTransport{
			base: http.DefaultTransport,
			host: hostHeader,
		},
		Timeout: 30 * time.Second,
	}
}

// parseEndpoint extracts host and path from a full URL
// Example: "http://host.docker.internal/v1/logs" -> ("host.docker.internal:80", "/v1/logs")
func parseEndpoint(endpoint string) (host string, path string) {
	// Determine if using HTTPS
	isHTTPS := strings.HasPrefix(endpoint, "https://")

	// Remove scheme
	endpoint = strings.TrimPrefix(endpoint, "http://")
	endpoint = strings.TrimPrefix(endpoint, "https://")

	// Split by first slash
	if idx := strings.Index(endpoint, "/"); idx != -1 {
		host = endpoint[:idx]
		path = endpoint[idx:]
	} else {
		host = endpoint
		path = "/"
	}

	// Add default port if not specified
	if !strings.Contains(host, ":") {
		if isHTTPS {
			host = host + ":443"
		} else {
			host = host + ":80"
		}
	}

	return host, path
}

// parseOTLPHeaders parses OTEL_EXPORTER_OTLP_HEADERS in key=value format
// Format: "key1=value1,key2=value2" (OpenTelemetry standard for Go)
func parseOTLPHeaders() map[string]string {
	headersStr := os.Getenv("OTEL_EXPORTER_OTLP_HEADERS")
	if headersStr == "" {
		return nil
	}

	headers := make(map[string]string)

	// Try JSON format first (for compatibility with TypeScript)
	if strings.HasPrefix(headersStr, "{") {
		if err := json.Unmarshal([]byte(headersStr), &headers); err == nil {
			return headers
		}
	}

	// Parse key=value,key=value format (OpenTelemetry standard for Go)
	pairs := strings.Split(headersStr, ",")
	for _, pair := range pairs {
		parts := strings.SplitN(strings.TrimSpace(pair), "=", 2)
		if len(parts) == 2 {
			headers[parts[0]] = parts[1]
		}
	}

	if len(headers) == 0 {
		return nil
	}
	return headers
}

// initializeOpenTelemetry sets up OTLP exporters and providers
func initializeOpenTelemetry(serviceName, serviceVersion, sessionID string) error {
	ctx := context.Background()

	// Create resource
	res, err := resource.New(ctx,
		resource.WithAttributes(
			semconv.ServiceName(serviceName),
			semconv.ServiceVersion(serviceVersion),
			semconv.DeploymentEnvironment(getEnv("NODE_ENV", "development")),
		),
	)
	if err != nil {
		return fmt.Errorf("failed to create resource: %w", err)
	}

	// Parse headers from environment
	headers := parseOTLPHeaders()
	if headers != nil {
		fmt.Printf("📋 OTLP headers configured: %v\n", headers)
	}

	// Trace exporter
	traceEndpoint := getEnv("OTEL_EXPORTER_OTLP_TRACES_ENDPOINT", "http://localhost:4318/v1/traces")
	traceEndpointHost, traceEndpointPath := parseEndpoint(traceEndpoint)
	fmt.Printf("🔗 Trace endpoint: %s (path: %s)\n", traceEndpointHost, traceEndpointPath)

	traceExporterOpts := []otlptracehttp.Option{
		otlptracehttp.WithEndpoint(traceEndpointHost),
		otlptracehttp.WithInsecure(),
		otlptracehttp.WithURLPath(traceEndpointPath),
	}
	if headers != nil && headers["Host"] != "" {
		// Use custom HTTP client that forces the Host header
		httpClient := createHTTPClientWithHost(headers["Host"])
		traceExporterOpts = append(traceExporterOpts, otlptracehttp.WithHTTPClient(httpClient))
		fmt.Printf("   ├── Using custom Host header: %s\n", headers["Host"])
	}
	traceExporter, err := otlptracehttp.New(ctx, traceExporterOpts...)
	if err != nil {
		fmt.Printf("⚠️  Trace exporter initialization failed: %v\n", err)
		// Create a basic tracer provider even if exporter fails
		tracerProvider := sdktrace.NewTracerProvider(sdktrace.WithResource(res))
		otel.SetTracerProvider(tracerProvider)
		globalTracer = tracerProvider.Tracer(serviceName)
		globalTraceProvider = tracerProvider
	} else {
		tracerProvider := sdktrace.NewTracerProvider(
			sdktrace.WithBatcher(traceExporter),
			sdktrace.WithResource(res),
		)
		otel.SetTracerProvider(tracerProvider)
		globalTracer = tracerProvider.Tracer(serviceName)
		globalTraceProvider = tracerProvider
	}

	// Log exporter
	logEndpoint := getEnv("OTEL_EXPORTER_OTLP_LOGS_ENDPOINT", "http://localhost:4318/v1/logs")
	logEndpointHost, logEndpointPath := parseEndpoint(logEndpoint)
	fmt.Printf("🔗 Log endpoint: %s (path: %s)\n", logEndpointHost, logEndpointPath)

	logExporterOpts := []otlploghttp.Option{
		otlploghttp.WithEndpoint(logEndpointHost),
		otlploghttp.WithInsecure(),
		otlploghttp.WithURLPath(logEndpointPath),
	}
	if headers != nil && headers["Host"] != "" {
		// Use custom HTTP client that forces the Host header
		httpClient := createHTTPClientWithHost(headers["Host"])
		logExporterOpts = append(logExporterOpts, otlploghttp.WithHTTPClient(httpClient))
		fmt.Printf("   ├── Using custom Host header: %s\n", headers["Host"])
	}
	logExporter, err := otlploghttp.New(ctx, logExporterOpts...)
	if err != nil {
		fmt.Printf("⚠️  Log exporter initialization failed: %v\n", err)
		// Create a minimal log provider even if exporter fails
		globalLogProvider = sdklog.NewLoggerProvider(sdklog.WithResource(res))
	} else {
		logProvider := sdklog.NewLoggerProvider(
			sdklog.WithProcessor(sdklog.NewBatchProcessor(logExporter)),
			sdklog.WithResource(res),
		)
		globalLogProvider = logProvider
	}

	// Metric exporter
	metricEndpoint := getEnv("OTEL_EXPORTER_OTLP_METRICS_ENDPOINT", "http://localhost:4318/v1/metrics")
	metricEndpointHost, metricEndpointPath := parseEndpoint(metricEndpoint)
	fmt.Printf("🔗 Metric endpoint: %s (path: %s)\n", metricEndpointHost, metricEndpointPath)

	metricExporterOpts := []otlpmetrichttp.Option{
		otlpmetrichttp.WithEndpoint(metricEndpointHost),
		otlpmetrichttp.WithInsecure(),
		otlpmetrichttp.WithURLPath(metricEndpointPath),
	}
	if headers != nil && headers["Host"] != "" {
		// Use custom HTTP client that forces the Host header
		httpClient := createHTTPClientWithHost(headers["Host"])
		metricExporterOpts = append(metricExporterOpts, otlpmetrichttp.WithHTTPClient(httpClient))
		fmt.Printf("   ├── Using custom Host header: %s\n", headers["Host"])
	}
	metricExporter, err := otlpmetrichttp.New(ctx, metricExporterOpts...)
	if err != nil {
		fmt.Printf("⚠️  Metric exporter initialization failed: %v\n", err)
		// Create a basic meter provider even if exporter fails
		meterProvider := sdkmetric.NewMeterProvider(sdkmetric.WithResource(res))
		otel.SetMeterProvider(meterProvider)
		globalMeter = meterProvider.Meter(serviceName)
		globalMeterProvider = meterProvider
	} else {
		// Create periodic reader with CUMULATIVE temporality (Prometheus compatible)
		// Use manual reader with temporality preference, then wrap in periodic
		reader := sdkmetric.NewPeriodicReader(
			metricExporter,
			sdkmetric.WithInterval(10*time.Second), // Export every 10 seconds
		)

		// Set cumulative temporality using the exporter's temporality selector
		meterProvider := sdkmetric.NewMeterProvider(
			sdkmetric.WithReader(reader),
			sdkmetric.WithResource(res),
		)
		otel.SetMeterProvider(meterProvider)
		globalMeter = meterProvider.Meter(serviceName)
		globalMeterProvider = meterProvider
		fmt.Printf("   ├── Metric export interval: 10s\n")
	}

	// Initialize metrics (matching TypeScript implementation)
	operationCounter, _ = globalMeter.Int64Counter("sovdev.operations.total",
		metric.WithDescription("Total number of operations"))
	errorCounter, _ = globalMeter.Int64Counter("sovdev.errors.total",
		metric.WithDescription("Total number of errors"))
	operationDuration, _ = globalMeter.Float64Histogram("sovdev.operation.duration",
		metric.WithDescription("Duration of operations in milliseconds"),
		metric.WithUnit("ms"))
	activeOperations, _ = globalMeter.Int64UpDownCounter("sovdev.operations.active",
		metric.WithDescription("Number of active operations"))

	fmt.Printf("📡 OpenTelemetry configured\n")
	return nil
}

// SovdevLog logs a general transaction with optional input/output and exception
func SovdevLog(level SovdevLogLevel, functionName, message, peerService string, inputJSON, responseJSON interface{}, exception error, traceID string) {
	if globalLogger == nil {
		fmt.Println("⚠️  Logger not initialized. Call SovdevInitialize first.")
		return
	}

	globalLogger.log(level, functionName, message, peerService, inputJSON, responseJSON, exception, traceID, "transaction")
}

// SovdevLogJobStatus logs job status events (Started, Completed, Failed)
func SovdevLogJobStatus(level SovdevLogLevel, functionName, jobName, status, peerService string, inputJSON interface{}, traceID string) {
	if globalLogger == nil {
		fmt.Println("⚠️  Logger not initialized. Call SovdevInitialize first.")
		return
	}

	// Add job metadata to input
	enrichedInput := map[string]interface{}{
		"job_name":   jobName,
		"job_status": status,
	}
	if inputJSON != nil {
		if inputMap, ok := inputJSON.(map[string]interface{}); ok {
			for k, v := range inputMap {
				enrichedInput[k] = v
			}
		}
	}

	message := fmt.Sprintf("Job %s: %s", status, jobName)
	globalLogger.log(level, functionName, message, peerService, enrichedInput, nil, nil, traceID, "job.status")
}

// SovdevLogJobProgress logs progress for batch operations
func SovdevLogJobProgress(level SovdevLogLevel, functionName, itemID string, current, total int, peerService string, inputJSON interface{}, traceID string) {
	if globalLogger == nil {
		fmt.Println("⚠️  Logger not initialized. Call SovdevInitialize first.")
		return
	}

	progressPercentage := int((float64(current) / float64(total)) * 100)

	// Add progress metadata to input
	enrichedInput := map[string]interface{}{
		"item_id":             itemID,
		"current_item":        current,
		"total_items":         total,
		"progress_percentage": progressPercentage,
		"job_name":            "BatchProcessing",
	}
	if inputJSON != nil {
		if inputMap, ok := inputJSON.(map[string]interface{}); ok {
			for k, v := range inputMap {
				enrichedInput[k] = v
			}
		}
	}

	message := fmt.Sprintf("Processing %s (%d/%d)", itemID, current, total)
	globalLogger.log(level, functionName, message, peerService, enrichedInput, nil, nil, traceID, "job.progress")
}

// SovdevGenerateTraceID generates a UUID for transaction correlation
func SovdevGenerateTraceID() string {
	return strings.ReplaceAll(uuid.New().String(), "-", "")
}

// SovdevFlush flushes all pending telemetry
func SovdevFlush() error {
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	var errs []error

	if globalTraceProvider != nil {
		fmt.Println("🔄 Flushing OpenTelemetry traces...")
		if err := globalTraceProvider.ForceFlush(ctx); err != nil {
			errs = append(errs, fmt.Errorf("trace flush: %w", err))
		} else {
			fmt.Println("✅ OpenTelemetry traces flushed")
		}
	}

	if globalMeterProvider != nil {
		fmt.Println("🔄 Flushing OpenTelemetry metrics...")
		if err := globalMeterProvider.ForceFlush(ctx); err != nil {
			errs = append(errs, fmt.Errorf("metric flush: %w", err))
		} else {
			fmt.Println("✅ OpenTelemetry metrics flushed")
		}
	}

	if globalLogProvider != nil {
		fmt.Println("🔄 Flushing OpenTelemetry logs...")
		if err := globalLogProvider.ForceFlush(ctx); err != nil {
			errs = append(errs, fmt.Errorf("log flush: %w", err))
		} else {
			fmt.Println("✅ OpenTelemetry logs flushed")
		}
	}

	if len(errs) > 0 {
		return fmt.Errorf("flush errors: %v", errs)
	}

	return nil
}

// Internal log method
func (l *sovdevLogger) log(level SovdevLogLevel, functionName, message, peerService string, inputJSON, responseJSON interface{}, exception error, traceID, logType string) {
	startTime := time.Now()

	// Generate IDs
	eventID := uuid.New().String()
	if traceID == "" {
		traceID = SovdevGenerateTraceID()
	}

	// Resolve peer service
	resolvedPeerService := l.resolvePeerService(peerService)

	// Process exception
	var exceptionType, exceptionMessage, exceptionStacktrace string
	if exception != nil {
		exceptionType = "Error"
		exceptionMessage = exception.Error()
		exceptionStacktrace = limitStackTrace(removeCredentials(fmt.Sprintf("%+v", exception)), 350)
	}

	// Get span context if available
	spanID := ""
	ctx := context.Background()
	span := apitrace.SpanFromContext(ctx)
	if span.SpanContext().IsValid() {
		traceID = span.SpanContext().TraceID().String()
		spanID = span.SpanContext().SpanID().String()
	}

	// Create log entry
	entry := StructuredLogEntry{
		Timestamp:           time.Now().UTC().Format(time.RFC3339Nano),
		Level:               string(level),
		ServiceName:         l.serviceName,
		ServiceVersion:      l.serviceVersion,
		SessionID:           l.sessionID,
		PeerService:         resolvedPeerService,
		FunctionName:        functionName,
		Message:             message,
		TraceID:             traceID,
		SpanID:              spanID,
		EventID:             eventID,
		LogType:             logType,
		InputJSON:           inputJSON,
		ResponseJSON:        responseJSON,
		ExceptionType:       exceptionType,
		ExceptionMessage:    exceptionMessage,
		ExceptionStacktrace: exceptionStacktrace,
	}

	// Write to outputs
	l.writeToOutputs(level, entry)

	// Record metrics with proper attributes (matching TypeScript labels)
	if operationCounter != nil {
		// Create metric attributes matching TypeScript implementation
		attrs := metric.WithAttributes(
			semconv.ServiceName(l.serviceName),
			semconv.ServiceVersion(l.serviceVersion),
			attribute.String("peer_service", resolvedPeerService),
			attribute.String("log_type", logType),
			attribute.String("log_level", string(level)),
		)

		operationCounter.Add(ctx, 1, attrs)
		if level == SOVDEV_LOGLEVELS.ERROR || level == SOVDEV_LOGLEVELS.FATAL {
			errorCounter.Add(ctx, 1, attrs)
		}
		// Record duration in milliseconds (matching TypeScript)
		duration := float64(time.Since(startTime).Milliseconds())
		operationDuration.Record(ctx, duration, attrs)
	}
}

func (l *sovdevLogger) writeToOutputs(level SovdevLogLevel, entry StructuredLogEntry) {
	// Marshal to JSON
	jsonBytes, err := json.Marshal(entry)
	if err != nil {
		fmt.Printf("❌ Failed to marshal log entry: %v\n", err)
		return
	}

	// File output
	if l.logToFile && l.fileLogger != nil {
		l.fileLogger.Println(string(jsonBytes))

		// Error file
		if (level == SOVDEV_LOGLEVELS.ERROR || level == SOVDEV_LOGLEVELS.FATAL) && l.errorLogger != nil {
			l.errorLogger.Println(string(jsonBytes))
		}
	}

	// Console output
	if l.logToConsole && l.consoleLogger != nil {
		l.consoleLogger.Println(string(jsonBytes))
	}

	// OTLP output
	if l.otlpLogger != nil {
		l.writeToOTLP(level, entry)
	}
}

func (l *sovdevLogger) writeToOTLP(level SovdevLogLevel, entry StructuredLogEntry) {
	ctx := context.Background()

	var logLevel otlog.Severity
	switch level {
	case SOVDEV_LOGLEVELS.TRACE:
		logLevel = otlog.SeverityTrace
	case SOVDEV_LOGLEVELS.DEBUG:
		logLevel = otlog.SeverityDebug
	case SOVDEV_LOGLEVELS.INFO:
		logLevel = otlog.SeverityInfo
	case SOVDEV_LOGLEVELS.WARN:
		logLevel = otlog.SeverityWarn
	case SOVDEV_LOGLEVELS.ERROR:
		logLevel = otlog.SeverityError
	case SOVDEV_LOGLEVELS.FATAL:
		logLevel = otlog.SeverityFatal
	default:
		logLevel = otlog.SeverityInfo
	}

	record := otlog.Record{}
	record.SetTimestamp(time.Now())
	record.SetSeverity(logLevel)
	record.SetSeverityText(mapToSeverityText(level))
	record.SetBody(otlog.StringValue(entry.Message))

	// Add attributes
	record.AddAttributes(
		otlog.String("service_name", entry.ServiceName),
		otlog.String("service_version", entry.ServiceVersion),
		otlog.String("session_id", entry.SessionID),
		otlog.String("peer_service", entry.PeerService),
		otlog.String("function_name", entry.FunctionName),
		otlog.String("trace_id", entry.TraceID),
		otlog.String("event_id", entry.EventID),
		otlog.String("log_type", entry.LogType),
	)

	if entry.SpanID != "" {
		record.AddAttributes(otlog.String("span_id", entry.SpanID))
	}

	if entry.InputJSON != nil {
		if jsonBytes, err := json.Marshal(entry.InputJSON); err == nil {
			record.AddAttributes(otlog.String("input_json", string(jsonBytes)))
		}
	}

	if entry.ResponseJSON != nil {
		if jsonBytes, err := json.Marshal(entry.ResponseJSON); err == nil {
			record.AddAttributes(otlog.String("response_json", string(jsonBytes)))
		}
	}

	if entry.ExceptionType != "" {
		record.AddAttributes(
			otlog.String("exception_type", entry.ExceptionType),
			otlog.String("exception_message", entry.ExceptionMessage),
			otlog.String("exception_stacktrace", entry.ExceptionStacktrace),
		)
	}

	l.otlpLogger.Emit(ctx, record)
}

func (l *sovdevLogger) resolvePeerService(friendlyName string) string {
	if friendlyName == "" || friendlyName == "INTERNAL" {
		return l.serviceName
	}

	if systemID, ok := l.peerServiceMap[friendlyName]; ok {
		return systemID
	}

	return friendlyName
}

// Utility functions
func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}

func removeCredentials(stack string) string {
	patterns := []struct {
		regex       *regexp.Regexp
		replacement string
	}{
		{regexp.MustCompile(`(?i)Authorization[:\s]+[^\s,}]+`), "Authorization: [REDACTED]"},
		{regexp.MustCompile(`(?i)Bearer\s+[A-Za-z0-9\-._~+/]+=*`), "Bearer [REDACTED]"},
		{regexp.MustCompile(`(?i)api[-_]?key[:\s=]+[^\s,}]+`), "api-key: [REDACTED]"},
		{regexp.MustCompile(`(?i)password[:\s=]+[^\s,}]+`), "password: [REDACTED]"},
		{regexp.MustCompile(`[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+`), "[REDACTED-JWT]"},
		{regexp.MustCompile(`(?i)session[-_]?id[:\s=]+[^\s,}]+`), "session-id: [REDACTED]"},
		{regexp.MustCompile(`(?i)Cookie[:\s]+[^\r\n]+`), "Cookie: [REDACTED]"},
	}

	result := stack
	for _, p := range patterns {
		result = p.regex.ReplaceAllString(result, p.replacement)
	}
	return result
}

func limitStackTrace(stack string, maxLength int) string {
	if len(stack) <= maxLength {
		return stack
	}
	return stack[:maxLength] + "... (truncated)"
}
