"""
Sovdev Logger - Python Implementation

Structured logging library implementing Python stdlib logging best practices:
- Multiple simultaneous handlers (console + file + OTLP)
- OpenTelemetry auto-instrumentation (no manual trace injection)
- Proper handler separation and formatting
- Enhanced OTLP log exporter configuration

Implements "Loggeloven av 2025" requirements with the standardized API
that is consistent across all programming languages (TypeScript, C#, PHP, Python).

Features:
- Structured JSON logging with required fields
- Full OpenTelemetry integration (traces AND logs)
- Security-aware error handling (removes auth credentials)
- Consistent field naming (snake_case)
- Simple function-based API identical across languages
- Python stdlib logging best practices
"""

import json
import logging
import logging.handlers
import os
import re
import sys
import time
import traceback
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from opentelemetry import trace, metrics as otel_metrics
from opentelemetry._logs import set_logger_provider, get_logger, LogRecord, SeverityNumber
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.semconv.resource import ResourceAttributes

from .log_levels import SOVDEV_LOGLEVELS

# =============================================================================
# GLOBAL STATE
# =============================================================================

_global_logger: Optional['InternalSovdevLogger'] = None
_global_stdlib_logger: Optional[logging.Logger] = None
_global_tracer_provider: Optional[TracerProvider] = None
_global_meter_provider: Optional[MeterProvider] = None
_global_logger_provider: Optional[LoggerProvider] = None
_global_session_id: Optional[str] = None
_global_metrics: Optional[Dict[str, Any]] = None


# =============================================================================
# SEVERITY MAPPING
# =============================================================================

SEVERITY_MAP = {
    'trace': SeverityNumber.DEBUG,
    'debug': SeverityNumber.DEBUG,
    'info': SeverityNumber.INFO,
    'warn': SeverityNumber.WARN,
    'error': SeverityNumber.ERROR,
    'fatal': SeverityNumber.FATAL
}

STDLIB_LEVEL_MAP = {
    'trace': logging.DEBUG,
    'debug': logging.DEBUG,
    'info': logging.INFO,
    'warn': logging.WARNING,
    'error': logging.ERROR,
    'fatal': logging.CRITICAL
}


# =============================================================================
# CUSTOM LOGGING HANDLER FOR OTLP
# =============================================================================

class OTLPLoggingHandler(logging.Handler):
    """Custom logging handler that sends logs to OpenTelemetry OTLP"""

    def __init__(self, service_name: str):
        super().__init__()
        self.otel_logger = get_logger(service_name, '1.0.0')

    def emit(self, record: logging.LogRecord):
        """Emit a log record to OpenTelemetry"""
        try:
            # Get log level
            log_level = getattr(record, 'level', 'info').lower()

            # Build attributes from record
            attributes = {}

            # Standard fields
            for field in ['service_name', 'service_version', 'peer_service', 'function_name',
                          'timestamp', 'trace_id', 'span_id', 'event_id', 'log_type', 'session_id']:
                if hasattr(record, field):
                    attributes[field] = getattr(record, field)

            # Serialize input_json and response_json as JSON strings for OTLP
            if hasattr(record, 'input_json'):
                attributes['input_json'] = json.dumps(record.input_json) if record.input_json is not None else 'null'

            if hasattr(record, 'response_json'):
                attributes['response_json'] = json.dumps(record.response_json) if record.response_json is not None else 'null'

            # Exception fields (flat structure for OTLP)
            for field in ['exception_type', 'exception_message', 'exception_stack']:
                if hasattr(record, field):
                    attributes[field] = getattr(record, field)

            # Emit to OTLP
            self.otel_logger.emit(
                LogRecord(
                    timestamp=int(datetime.now(timezone.utc).timestamp() * 1_000_000_000),
                    observed_timestamp=int(datetime.now(timezone.utc).timestamp() * 1_000_000_000),
                    severity_number=SEVERITY_MAP.get(log_level, SeverityNumber.INFO),
                    severity_text=log_level.upper(),
                    body=record.getMessage(),
                    attributes=attributes
                )
            )
        except Exception as e:
            # Don't fail if OTLP fails
            print(f'❌ OpenTelemetry OTLP handler failed: {e}', file=sys.stderr)


# =============================================================================
# JSON FORMATTER
# =============================================================================

class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for file output"""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        log_entry = {
            'timestamp': getattr(record, 'timestamp', datetime.now(timezone.utc).isoformat()),
            'level': getattr(record, 'level', 'info'),
            'service_name': getattr(record, 'service_name', 'unknown'),
            'service_version': getattr(record, 'service_version', '1.0.0'),
            'session_id': getattr(record, 'session_id', ''),
            'peer_service': getattr(record, 'peer_service', ''),
            'function_name': getattr(record, 'function_name', ''),
            'log_type': getattr(record, 'log_type', 'transaction'),
            'message': record.getMessage(),
            'trace_id': getattr(record, 'trace_id', ''),
            'event_id': getattr(record, 'event_id', ''),
        }

        # Add span_id if present
        if hasattr(record, 'span_id') and record.span_id:
            log_entry['span_id'] = record.span_id

        # Add input_json and response_json
        if hasattr(record, 'input_json'):
            log_entry['input_json'] = record.input_json

        if hasattr(record, 'response_json'):
            log_entry['response_json'] = record.response_json

        # Add exception fields (flat structure for file output - matches OTLP)
        if hasattr(record, 'exception_type') and record.exception_type:
            log_entry['exception_type'] = record.exception_type
            log_entry['exception_message'] = getattr(record, 'exception_message', '')
            log_entry['exception_stacktrace'] = getattr(record, 'exception_stack', '')

        return json.dumps(log_entry, ensure_ascii=False)


# =============================================================================
# CONSOLE FORMATTER
# =============================================================================

class ConsoleFormatter(logging.Formatter):
    """Custom console formatter for human-readable output"""

    # ANSI color codes
    COLORS = {
        'trace': '\033[90m',     # Gray
        'debug': '\033[36m',     # Cyan
        'info': '\033[32m',      # Green
        'warn': '\033[33m',      # Yellow
        'error': '\033[31m',     # Red
        'fatal': '\033[35m',     # Magenta
        'reset': '\033[0m'
    }

    def format(self, record: logging.LogRecord) -> str:
        """Format log record for console output"""
        level = getattr(record, 'level', 'info')
        color = self.COLORS.get(level, self.COLORS['info'])
        reset = self.COLORS['reset']

        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        service_name = getattr(record, 'service_name', 'unknown')
        function_name = getattr(record, 'function_name', '')
        message = record.getMessage()

        # Build the log line
        log_line = f"{timestamp} {color}[{level.upper()}]{reset} {service_name}\n"
        log_line += f"  Function: {function_name}\n"
        log_line += f"  Message: {message}"

        # Add trace context if available
        if hasattr(record, 'trace_id') and record.trace_id:
            log_line += f"\n  Trace ID: {record.trace_id}"

        if hasattr(record, 'span_id') and record.span_id:
            log_line += f"\n  Span ID: {record.span_id}"

        if hasattr(record, 'session_id') and record.session_id:
            log_line += f"\n  Session ID: {record.session_id}"

        # Add exception details if present
        if hasattr(record, 'exception_message') and record.exception_message:
            log_line += f"\n  Error: {record.exception_message}"

        if hasattr(record, 'exception_stack') and record.exception_stack:
            log_line += f"\n  Stack: {record.exception_stack}"

        return log_line


# =============================================================================
# LOGGER INITIALIZATION
# =============================================================================

def _initialize_stdlib_logger(service_name: str) -> logging.Logger:
    """Initialize Python stdlib logger with handlers"""
    logger = logging.getLogger(service_name)
    logger.setLevel(logging.DEBUG)
    logger.handlers = []  # Clear any existing handlers

    # Get configuration
    is_development = os.environ.get('NODE_ENV', 'development') != 'production'
    has_otlp_endpoint = bool(os.environ.get('OTEL_EXPORTER_OTLP_LOGS_ENDPOINT'))
    log_to_console = os.environ.get('LOG_TO_CONSOLE', 'true' if not has_otlp_endpoint else 'false').lower() == 'true'
    log_to_file = os.environ.get('LOG_TO_FILE', 'true').lower() == 'true'

    # 1. CONSOLE HANDLER
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)

        if is_development:
            # Colored output for development
            console_handler.setFormatter(ConsoleFormatter())
        else:
            # JSON output for production
            console_handler.setFormatter(JSONFormatter())

        logger.addHandler(console_handler)

    # 2. FILE HANDLER
    if log_to_file:
        log_file_path = os.environ.get('LOG_FILE_PATH', './logs/dev.log')
        os.makedirs(os.path.dirname(log_file_path) or '.', exist_ok=True)

        file_handler = logging.handlers.RotatingFileHandler(
            log_file_path,
            maxBytes=50 * 1024 * 1024,  # 50MB
            backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(JSONFormatter())
        logger.addHandler(file_handler)

        print(f'📝 File logging enabled: {log_file_path}')

    # 3. ERROR FILE HANDLER
    if log_to_file:
        error_log_path = os.environ.get('ERROR_LOG_PATH', './logs/error.log')

        error_handler = logging.handlers.RotatingFileHandler(
            error_log_path,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=3
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(JSONFormatter())
        logger.addHandler(error_handler)

    # 4. OTLP HANDLER
    if service_name:
        otlp_handler = OTLPLoggingHandler(service_name)
        otlp_handler.setLevel(logging.DEBUG)
        logger.addHandler(otlp_handler)
        print('📡 OpenTelemetry OTLP handler configured')

    return logger


# =============================================================================
# OPENTELEMETRY CONFIGURATION
# =============================================================================

def _configure_metrics(service_name: str, service_version: str, session_id: str) -> Optional[MeterProvider]:
    """Configure OpenTelemetry metrics"""
    try:
        resource = Resource.create({
            ResourceAttributes.SERVICE_NAME: service_name,
            ResourceAttributes.SERVICE_VERSION: service_version,
            ResourceAttributes.DEPLOYMENT_ENVIRONMENT: os.environ.get('NODE_ENV', 'development'),
            'session_id': session_id
        })

        # Parse OTLP headers if present
        headers = {}
        if os.environ.get('OTEL_EXPORTER_OTLP_HEADERS'):
            try:
                headers = json.loads(os.environ['OTEL_EXPORTER_OTLP_HEADERS'])
            except json.JSONDecodeError:
                pass

        metric_exporter = OTLPMetricExporter(
            endpoint=os.environ.get('OTEL_EXPORTER_OTLP_METRICS_ENDPOINT', 'http://localhost:4318/v1/metrics'),
            headers=headers
        )

        metric_reader = PeriodicExportingMetricReader(
            exporter=metric_exporter,
            export_interval_millis=10000  # 10 seconds
        )

        meter_provider = MeterProvider(
            resource=resource,
            metric_readers=[metric_reader]
        )

        otel_metrics.set_meter_provider(meter_provider)

        # Create metrics
        meter = meter_provider.get_meter(service_name, service_version)

        global _global_metrics
        _global_metrics = {
            'operation_counter': meter.create_counter(
                'sovdev.operations.total',
                description='Total number of operations by service, peer service, and log level',
                unit='1'
            ),
            'error_counter': meter.create_counter(
                'sovdev.errors.total',
                description='Total number of errors by service, peer service, and exception type',
                unit='1'
            ),
            'operation_duration': meter.create_histogram(
                'sovdev.operation.duration',
                description='Duration of operations in milliseconds',
                unit='ms'
            ),
            'active_operations': meter.create_up_down_counter(
                'sovdev.operations.active',
                description='Number of currently active operations',
                unit='1'
            )
        }

        print(f'📊 OTLP Metrics configured for: {os.environ.get("OTEL_EXPORTER_OTLP_METRICS_ENDPOINT", "http://localhost:4318/v1/metrics")}')

        return meter_provider

    except Exception as error:
        print(f'⚠️  Metrics configuration failed: {error}', file=sys.stderr)
        return None


def _configure_opentelemetry(service_name: str, service_version: str, session_id: str) -> tuple:
    """Configure OpenTelemetry with trace and log exporters"""
    try:
        resource = Resource.create({
            ResourceAttributes.SERVICE_NAME: service_name,
            ResourceAttributes.SERVICE_VERSION: service_version,
            ResourceAttributes.DEPLOYMENT_ENVIRONMENT: os.environ.get('NODE_ENV', 'development'),
            'session_id': session_id
        })

        # Parse OTLP headers if present
        headers = {}
        if os.environ.get('OTEL_EXPORTER_OTLP_HEADERS'):
            try:
                headers = json.loads(os.environ['OTEL_EXPORTER_OTLP_HEADERS'])
            except json.JSONDecodeError:
                pass

        # TRACE EXPORTER AND PROVIDER
        trace_endpoint = os.environ.get('OTEL_EXPORTER_OTLP_TRACES_ENDPOINT', 'http://localhost:4318/v1/traces')

        trace_exporter = OTLPSpanExporter(
            endpoint=trace_endpoint,
            headers=headers
        )

        tracer_provider = TracerProvider(resource=resource)
        tracer_provider.add_span_processor(BatchSpanProcessor(trace_exporter))

        trace.set_tracer_provider(tracer_provider)

        print(f'🔍 OTLP Trace exporter configured for: {trace_endpoint}')

        # LOG EXPORTER AND PROVIDER
        log_endpoint = os.environ.get('OTEL_EXPORTER_OTLP_LOGS_ENDPOINT', 'http://localhost:4318/v1/logs')

        log_exporter = OTLPLogExporter(
            endpoint=log_endpoint,
            headers=headers
        )

        logger_provider = LoggerProvider(resource=resource)
        logger_provider.add_log_record_processor(BatchLogRecordProcessor(log_exporter))

        set_logger_provider(logger_provider)

        print(f'📡 OTLP Log exporter configured for: {log_endpoint}')

        return tracer_provider, logger_provider

    except Exception as error:
        print(f'⚠️  OpenTelemetry configuration failed: {error}', file=sys.stderr)
        return None, None


# =============================================================================
# INTERNAL LOGGER CLASS
# =============================================================================

class InternalSovdevLogger:
    """Internal logger class - handles all complexity, hidden from developers"""

    def __init__(self, service_name: str, service_version: str, system_ids: Dict[str, str]):
        self.service_name = service_name
        self.service_version = service_version
        self.system_ids_mapping = system_ids
        self.session_id = _global_session_id

    def _resolve_peer_service(self, friendly_name: Optional[str]) -> str:
        """Resolve friendly name to CMDB ID or service name for internal operations"""
        effective_name = friendly_name or "INTERNAL"

        # If INTERNAL, use the service's own name
        if effective_name == "INTERNAL":
            return self.service_name

        # Try to resolve from mapping
        resolved_id = self.system_ids_mapping.get(effective_name)
        if not resolved_id:
            print(f'⚠️ Unknown peer service: {effective_name}. Available: {", ".join(self.system_ids_mapping.keys())} or INTERNAL', file=sys.stderr)
            return effective_name

        return resolved_id

    def _process_exception(self, exception_object: Optional[BaseException]) -> Optional[Dict[str, str]]:
        """Process exception objects with security cleanup and standardization"""
        if not exception_object:
            return None

        # Get exception details
        exception_type = 'Error'  # Always use "Error" across all languages
        exception_message = str(exception_object)

        # Get stack trace
        stack_trace = ''.join(traceback.format_exception(type(exception_object), exception_object, exception_object.__traceback__))

        # Security: Remove credentials from stack trace
        stack_trace = re.sub(r'Authorization[:\s]+[^\s,}]+', 'Authorization: [REDACTED]', stack_trace, flags=re.IGNORECASE)
        stack_trace = re.sub(r'password[:\s=]+[^\s,}]+', 'password=[REDACTED]', stack_trace, flags=re.IGNORECASE)
        stack_trace = re.sub(r'api[-_]?key[:\s=]+[^\s,}]+', 'api_key=[REDACTED]', stack_trace, flags=re.IGNORECASE)
        stack_trace = re.sub(r'Bearer\s+[A-Za-z0-9\-._~+/]+=*', 'Bearer [REDACTED]', stack_trace, flags=re.IGNORECASE)

        # Limit to 350 characters
        if len(stack_trace) > 350:
            stack_trace = stack_trace[:350]

        return {
            'exception_type': exception_type,
            'exception_message': exception_message,
            'exception_stack': stack_trace
        }

    def _create_log_entry(
        self,
        level: str,
        function_name: str,
        message: str,
        peer_service: Optional[str],
        exception_object: Optional[BaseException],
        input_json: Optional[Any],
        response_json: Optional[Any],
        trace_id: Optional[str],
        log_type: str
    ) -> Dict[str, Any]:
        """Create a complete structured log entry with all required fields"""
        # Generate unique event ID
        event_id = str(uuid.uuid4())

        # Use provided trace_id or generate new one in OpenTelemetry format (32 hex chars, no dashes)
        final_trace_id = trace_id or str(uuid.uuid4()).replace('-', '')

        # Resolve peer service
        resolved_peer_service = self._resolve_peer_service(peer_service)

        # Process exception
        processed_exception = self._process_exception(exception_object)

        # Create log entry
        log_entry = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'level': level,
            'service_name': self.service_name,
            'service_version': self.service_version,
            'session_id': self.session_id,
            'peer_service': resolved_peer_service,
            'function_name': function_name,
            'message': message,
            'trace_id': final_trace_id,
            'event_id': event_id,
            'log_type': log_type,
            'input_json': input_json,
            'response_json': response_json
        }

        # Add exception fields if present
        if processed_exception:
            log_entry.update(processed_exception)

        return log_entry

    def _write_log(self, level: str, log_entry: Dict[str, Any]) -> None:
        """Write log entry using stdlib logger"""
        start_time = time.time()  # Record start time for duration tracking

        try:
            # Get active span for trace/span context
            active_span = trace.get_current_span()
            if active_span and active_span.is_recording():
                span_context = active_span.get_span_context()
                if span_context.trace_id:
                    log_entry['trace_id'] = format(span_context.trace_id, '032x')
                if span_context.span_id:
                    log_entry['span_id'] = format(span_context.span_id, '016x')

            # Create log record
            record = _global_stdlib_logger.makeRecord(
                _global_stdlib_logger.name,
                STDLIB_LEVEL_MAP.get(level, logging.INFO),
                '',
                0,
                log_entry['message'],
                (),
                None
            )

            # Add custom fields to record
            for key, value in log_entry.items():
                setattr(record, key, value)

            # Log it
            _global_stdlib_logger.handle(record)

            # Emit metrics AFTER logging (to include logging time in duration)
            if _global_metrics:
                # Calculate duration in milliseconds
                duration = (time.time() - start_time) * 1000

                attributes = {
                    'service_name': log_entry['service_name'],
                    'service_version': log_entry['service_version'],
                    'peer_service': log_entry['peer_service'],
                    'log_level': level,
                    'log_type': log_entry['log_type']
                }

                # Record operation counter
                _global_metrics['operation_counter'].add(1, attributes)

                # Record duration histogram
                _global_metrics['operation_duration'].record(duration, attributes)

                # Record error counter if applicable
                if level in ['error', 'fatal'] or log_entry.get('exception_type'):
                    error_attributes = {
                        **attributes,
                        'exception_type': log_entry.get('exception_type', 'Unknown')
                    }
                    _global_metrics['error_counter'].add(1, error_attributes)

        except Exception as err:
            print(f'Sovdev Logger failed: {err}', file=sys.stderr)
            print(json.dumps(log_entry), file=sys.stderr)

    def log(
        self,
        level: str,
        function_name: str,
        message: str,
        peer_service: str,
        input_json: Optional[Any] = None,
        response_json: Optional[Any] = None,
        exception_object: Optional[BaseException] = None,
        trace_id: Optional[str] = None
    ) -> None:
        """Main logging method - for transaction/request-response logs"""
        log_entry = self._create_log_entry(
            level, function_name, message, peer_service,
            exception_object, input_json, response_json, trace_id, 'transaction'
        )
        self._write_log(level, log_entry)

    def log_job_status(
        self,
        level: str,
        function_name: str,
        job_name: str,
        status: str,
        peer_service: str,
        input_json: Optional[Any] = None,
        trace_id: Optional[str] = None
    ) -> None:
        """Job status logging - for batch job start/complete/failed events"""
        message = f"Job {status}: {job_name}"
        context_input = {
            'job_name': job_name,
            'job_status': status,
            **(input_json or {})
        }

        log_entry = self._create_log_entry(
            level, function_name, message, peer_service,
            None, context_input, None, trace_id, 'job.status'
        )
        self._write_log(level, log_entry)

    def log_job_progress(
        self,
        level: str,
        function_name: str,
        item_id: str,
        current: int,
        total: int,
        peer_service: str,
        input_json: Optional[Any] = None,
        trace_id: Optional[str] = None
    ) -> None:
        """Job progress logging - for tracking batch processing progress"""
        message = f"Processing {item_id} ({current}/{total})"
        context_input = {
            'item_id': item_id,
            'current_item': current,
            'total_items': total,
            'progress_percentage': round((current / total) * 100),
            **(input_json or {})
        }

        log_entry = self._create_log_entry(
            level, function_name, message, peer_service,
            None, context_input, None, trace_id, 'job.progress'
        )
        self._write_log(level, log_entry)


# =============================================================================
# PUBLIC API FUNCTIONS
# =============================================================================

def sovdev_initialize(
    service_name: str,
    service_version: str = "1.0.0",
    peer_services: Optional[Dict[str, str]] = None
) -> None:
    """
    Initialize the Sovdev logger with service information and peer service mappings.

    Args:
        service_name: Service identifier (from SYSTEM_ID env var)
        service_version: Service version (defaults to "1.0.0")
        peer_services: Peer service mapping from create_peer_services()

    Raises:
        ValueError: If service_name is empty
    """
    global _global_logger, _global_stdlib_logger, _global_tracer_provider
    global _global_meter_provider, _global_logger_provider, _global_session_id

    if not service_name or not service_name.strip():
        raise ValueError('service_name is required')

    # Generate session ID
    _global_session_id = str(uuid.uuid4())
    print(f'🔑 Session ID: {_global_session_id}')

    # Automatically add INTERNAL peer service
    effective_system_ids = {
        'INTERNAL': service_name,
        **(peer_services or {})
    }

    # Configure OpenTelemetry metrics
    _global_meter_provider = _configure_metrics(service_name, service_version, _global_session_id)

    # Configure OpenTelemetry traces and logs
    _global_tracer_provider, _global_logger_provider = _configure_opentelemetry(
        service_name, service_version, _global_session_id
    )

    # Initialize stdlib logger
    _global_stdlib_logger = _initialize_stdlib_logger(service_name)

    # Create internal logger
    _global_logger = InternalSovdevLogger(service_name, service_version, effective_system_ids)

    # Print configuration summary
    is_development = os.environ.get('NODE_ENV', 'development') != 'production'
    has_otlp_endpoint = bool(os.environ.get('OTEL_EXPORTER_OTLP_LOGS_ENDPOINT'))
    log_to_console = os.environ.get('LOG_TO_CONSOLE', 'true' if not has_otlp_endpoint else 'false').lower() == 'true'
    log_to_file = os.environ.get('LOG_TO_FILE', 'true').lower() == 'true'

    print('🚀 Sovdev Logger initialized:')
    print(f'   ├── Service: {service_name}')
    print(f'   ├── Version: {service_version}')
    print(f'   ├── Systems: {", ".join(effective_system_ids.keys()) or "None configured"}')
    print(f'   ├── Console: {"Colored (dev)" if log_to_console and is_development else "JSON (prod)" if log_to_console else "Disabled"}')
    print(f'   ├── File: {"Enabled" if log_to_file else "Disabled"}')
    print(f'   └── OTLP: {"Configured" if has_otlp_endpoint else "⚠️  Not configured (using localhost:4318)"}')


def _ensure_logger() -> InternalSovdevLogger:
    """Ensure logger is initialized before use"""
    if _global_logger is None:
        raise RuntimeError(
            'Sovdev Logger not initialized. Call sovdev_initialize(service_name) at application startup.'
        )
    return _global_logger


def sovdev_log(
    level: str,
    function_name: str,
    message: str,
    peer_service: str,
    input_json: Optional[Any] = None,
    response_json: Optional[Any] = None,
    exception: Optional[BaseException] = None,
    trace_id: Optional[str] = None
) -> None:
    """
    Log a transaction with optional input/output and exception.

    Args:
        level: Log level (use SOVDEV_LOGLEVELS enum or string)
        function_name: Name of the function being logged
        message: Human-readable message
        peer_service: Target system identifier
        input_json: Request data (any JSON-serializable type)
        response_json: Response data (any JSON-serializable type)
        exception: Exception object (if logging error)
        trace_id: UUID for transaction correlation (auto-generated if None)
    """
    _ensure_logger().log(level, function_name, message, peer_service, input_json, response_json, exception, trace_id)


def sovdev_log_job_status(
    level: str,
    function_name: str,
    job_name: str,
    status: str,
    peer_service: str,
    input_json: Optional[Any] = None,
    trace_id: Optional[str] = None
) -> None:
    """
    Log batch job status (Started, Completed, Failed).

    Args:
        level: Log level (typically INFO or ERROR)
        function_name: Function name managing the job
        job_name: Human-readable job name
        status: Job status ("Started", "Completed", "Failed", etc.)
        peer_service: Target system or INTERNAL for internal jobs
        input_json: Job metadata (total items, success count, etc.)
        trace_id: Job correlation ID (same for all logs in this job)
    """
    _ensure_logger().log_job_status(level, function_name, job_name, status, peer_service, input_json, trace_id)


def sovdev_log_job_progress(
    level: str,
    function_name: str,
    item_id: str,
    current: int,
    total: int,
    peer_service: str,
    input_json: Optional[Any] = None,
    trace_id: Optional[str] = None
) -> None:
    """
    Log progress for individual items in a batch job.

    Args:
        level: Log level (typically INFO)
        function_name: Function name processing items
        item_id: Identifier for current item being processed
        current: Current item number (1-based)
        total: Total number of items
        peer_service: Target system for this item
        input_json: Item-specific data
        trace_id: Job correlation ID (same as job status logs)
    """
    _ensure_logger().log_job_progress(level, function_name, item_id, current, total, peer_service, input_json, trace_id)


def sovdev_generate_trace_id() -> str:
    """
    Generate UUID v4 for trace correlation.

    Returns:
        Lowercase UUID string with hyphens (36 characters)

    Example:
        >>> sovdev_generate_trace_id()
        '50ba0e1d-c46d-4dee-98d3-a0d3913f74ee'
    """
    return str(uuid.uuid4()).replace('-', '')


def sovdev_flush() -> None:
    """
    Flush all pending logs, metrics, and traces.

    Blocks until all data is exported or 30-second timeout occurs.
    Safe to call from signal handlers and atexit hooks.
    """
    try:
        if _global_tracer_provider:
            print('🔄 Flushing OpenTelemetry traces...')
            _global_tracer_provider.force_flush()
            print('✅ OpenTelemetry traces flushed successfully')

        if _global_meter_provider:
            print('🔄 Flushing OpenTelemetry metrics...')
            _global_meter_provider.force_flush()
            print('✅ OpenTelemetry metrics flushed successfully')

        if _global_logger_provider:
            print('🔄 Flushing OpenTelemetry logs...')
            _global_logger_provider.force_flush()
            print('✅ OpenTelemetry logs flushed successfully')

        # Shutdown providers
        if _global_tracer_provider:
            print('🔄 Shutting down TracerProvider...')
            _global_tracer_provider.shutdown()
            print('✅ TracerProvider shutdown complete')

        if _global_meter_provider:
            print('🔄 Shutting down MeterProvider...')
            _global_meter_provider.shutdown()
            print('✅ MeterProvider shutdown complete')

        if _global_logger_provider:
            print('🔄 Shutting down LoggerProvider...')
            _global_logger_provider.shutdown()
            print('✅ LoggerProvider shutdown complete')

    except Exception as error:
        print(f'⚠️  OpenTelemetry flush/shutdown failed: {error}', file=sys.stderr)
