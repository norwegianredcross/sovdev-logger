"""
Sovdev Logger - Python Implementation

Structured logging library implementing best practices:
- Multiple simultaneous transports (console + file + OTLP)
- OpenTelemetry auto-instrumentation
- Proper transport separation and formatting
- Enhanced OTLP log exporter configuration

Implements "Loggeloven av 2025" requirements with standardized API
consistent across all programming languages (TypeScript, Python, C#, PHP).

Features:
- Structured JSON logging with required fields
- Full OpenTelemetry integration (traces AND logs)
- Security-aware error handling (removes auth credentials)
- Consistent field naming (snake_case)
- Simple function-based API identical across languages
"""

import os
import sys
import json
import logging
import logging.handlers
import re
import time
import traceback as tb
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple
from contextvars import ContextVar

# OpenTelemetry imports
from opentelemetry import trace, metrics as otel_metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.semconv.resource import ResourceAttributes
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.trace import Span, SpanContext, Status, StatusCode
from opentelemetry._logs import SeverityNumber

# Import log levels
try:
    from .log_levels import SOVDEV_LOGLEVELS, SovdevLogLevel
except ImportError:
    from log_levels import SOVDEV_LOGLEVELS, SovdevLogLevel

# =============================================================================
# SPAN CONTEXT STORAGE
# =============================================================================

# ContextVar for maintaining active span across async operations
span_storage: ContextVar[Optional[Span]] = ContextVar('active_span', default=None)

# =============================================================================
# TYPE DEFINITIONS
# =============================================================================

class SovdevMetrics:
    """Container for OpenTelemetry metrics instances."""
    def __init__(self, meter):
        # Create metric instruments
        self.operation_counter = meter.create_counter(
            name='sovdev_operations_total',
            description='Total number of operations by service, peer service, and log level',
            unit='1'
        )

        self.error_counter = meter.create_counter(
            name='sovdev_errors_total',
            description='Total number of errors by service, peer service, and exception type',
            unit='1'
        )

        self.operation_duration = meter.create_histogram(
            name='sovdev_operation_duration',
            description='Duration of operations in milliseconds',
            unit='ms'
        )

        self.active_operations = meter.create_up_down_counter(
            name='sovdev_operations_active',
            description='Number of currently active operations',
            unit='1'
        )

# Global metrics instance
global_metrics: Optional[SovdevMetrics] = None
global_meter_provider: Optional[MeterProvider] = None
global_tracer_provider: Optional[TracerProvider] = None
global_logger_provider: Optional[LoggerProvider] = None

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_service_version() -> str:
    """Auto-detect service version from environment or default."""
    return os.environ.get('SERVICE_VERSION', os.environ.get('PYTHON_VERSION', '1.0.0'))


def remove_undefined_fields(obj: Dict[str, Any]) -> Dict[str, Any]:
    """Remove None fields for cleaner JSON output."""
    return {k: v for k, v in obj.items() if v is not None}


# =============================================================================
# CUSTOM LOGGING HANDLER FOR JSON FILE OUTPUT
# =============================================================================

class JSONFileHandler(logging.handlers.RotatingFileHandler):
    """Custom handler that writes JSON lines to file with rotation."""

    def emit(self, record: logging.LogRecord) -> None:
        """Emit a log record as JSON line."""
        try:
            # Get the formatted message (already JSON from our formatter)
            msg = self.format(record)
            # Write as single line
            if self.stream is None:
                self.stream = self._open()
            self.stream.write(msg + '\n')
            self.flush()

            # Check if we should rotate
            if self.shouldRollover(record):
                self.doRollover()
        except Exception:
            self.handleError(record)


class JSONFormatter(logging.Formatter):
    """Formatter that outputs structured JSON log entries."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        # Extract our custom fields
        log_entry = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'level': record.levelname.lower(),
            'service_name': getattr(record, 'service_name', 'unknown'),
            'service_version': getattr(record, 'service_version', '1.0.0'),
            'peer_service': getattr(record, 'peer_service', 'unknown'),
            'function_name': getattr(record, 'function_name', 'unknown'),
            'log_type': getattr(record, 'log_type', 'transaction'),
            'message': record.getMessage(),
            'trace_id': getattr(record, 'trace_id', ''),
            'event_id': getattr(record, 'event_id', ''),
        }

        # Add optional fields
        if hasattr(record, 'span_id'):
            log_entry['span_id'] = record.span_id

        if hasattr(record, 'input_json'):
            log_entry['input_json'] = record.input_json

        if hasattr(record, 'response_json'):
            log_entry['response_json'] = record.response_json

        if hasattr(record, 'exception_type'):
            log_entry['exception_type'] = record.exception_type
            log_entry['exception_message'] = getattr(record, 'exception_message', '')
            log_entry['exception_stacktrace'] = getattr(record, 'exception_stacktrace', '')

        # Remove None values
        log_entry = remove_undefined_fields(log_entry)

        return json.dumps(log_entry, ensure_ascii=False)


# =============================================================================
# PYTHON LOGGING CONFIGURATION
# =============================================================================

def create_transports(service_name: str) -> Tuple[logging.Logger, list]:
    """
    Create Python logging handlers following best practices.
    Returns (logger, otel_handlers) tuple
    """
    logger = logging.getLogger(service_name)
    logger.setLevel(logging.DEBUG)  # Capture all levels
    logger.propagate = False  # Don't propagate to root logger

    # Clear any existing handlers
    logger.handlers = []

    # Track OTEL handlers separately for proper shutdown
    otel_handlers = []

    # 1. CONSOLE HANDLER: Optional, controlled by LOG_TO_CONSOLE
    is_development = os.environ.get('NODE_ENV', 'development') != 'production'
    has_otlp_endpoint = bool(os.environ.get('OTEL_EXPORTER_OTLP_LOGS_ENDPOINT'))
    log_to_console = os.environ.get('LOG_TO_CONSOLE', str(not has_otlp_endpoint)).lower() == 'true'

    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        if is_development:
            # Colored output for development
            console_formatter = logging.Formatter(
                '%(asctime)s [%(levelname)s] %(service_name)s:%(function_name)s - %(message)s',
                datefmt='%H:%M:%S'
            )
        else:
            # JSON output for production
            console_formatter = JSONFormatter()
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

    # 2. FILE HANDLER: Smart default (enabled unless explicitly disabled)
    log_to_file = os.environ.get('LOG_TO_FILE', 'true').lower() == 'true'

    if log_to_file:
        log_file_path = os.environ.get('LOG_FILE_PATH', './logs/dev.log')
        # Ensure directory exists
        os.makedirs(os.path.dirname(log_file_path), exist_ok=True)

        file_handler = JSONFileHandler(
            filename=log_file_path,
            maxBytes=50 * 1024 * 1024,  # 50MB max file size
            backupCount=5,  # Keep 5 rotated files
            encoding='utf-8'
        )
        file_handler.setFormatter(JSONFormatter())
        logger.addHandler(file_handler)
        print(f'📝 File logging enabled: {log_file_path}')

    # 3. ERROR FILE HANDLER: Separate file for errors only
    if log_to_file:
        error_log_path = os.environ.get('ERROR_LOG_PATH', './logs/error.log')
        # Ensure directory exists
        os.makedirs(os.path.dirname(error_log_path), exist_ok=True)

        error_handler = JSONFileHandler(
            filename=error_log_path,
            maxBytes=10 * 1024 * 1024,  # 10MB max file size
            backupCount=3,  # Keep 3 rotated error files
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(JSONFormatter())
        logger.addHandler(error_handler)

    # 4. OPENTELEMETRY HANDLER: Always enabled for centralized logging
    if service_name and global_logger_provider:
        otel_handler = LoggingHandler(
            level=logging.NOTSET,  # Capture all levels
            logger_provider=global_logger_provider
        )
        # Store reference for shutdown
        otel_handlers.append(otel_handler)
        logger.addHandler(otel_handler)
        print('📡 OpenTelemetry logging handler configured')

    return logger, otel_handlers


# Global logger instance
base_logger: Optional[logging.Logger] = None
otel_logging_handlers = []


# =============================================================================
# SECURITY FUNCTIONS
# =============================================================================

def limit_stack_trace(stack: str, max_length: int = 350) -> str:
    """Limit stack trace to maximum length."""
    if not stack:
        return ''
    if len(stack) <= max_length:
        return stack
    return stack[:max_length]


def remove_credentials_from_stack(stack: str) -> str:
    """Remove sensitive credentials from exception stack traces."""
    if not stack:
        return ''

    clean_stack = stack

    # Remove Authorization headers
    clean_stack = re.sub(
        r'Authorization[:\s]+[^\s,}]+',
        'Authorization: [REDACTED]',
        clean_stack,
        flags=re.IGNORECASE
    )

    # Remove Bearer tokens
    clean_stack = re.sub(
        r'Bearer\s+[A-Za-z0-9\-._~+/]+=*',
        'Bearer [REDACTED]',
        clean_stack,
        flags=re.IGNORECASE
    )

    # Remove API keys
    clean_stack = re.sub(
        r'api[-_]?key[:\s=]+[^\s,}]+',
        'api-key: [REDACTED]',
        clean_stack,
        flags=re.IGNORECASE
    )

    # Remove passwords
    clean_stack = re.sub(
        r'password[:\s=]+[^\s,}]+',
        'password: [REDACTED]',
        clean_stack,
        flags=re.IGNORECASE
    )

    # Remove JWT tokens
    clean_stack = re.sub(
        r'[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+',
        '[REDACTED-JWT]',
        clean_stack
    )

    # Remove session IDs
    clean_stack = re.sub(
        r'session[-_]?id[:\s=]+[^\s,}]+',
        'session-id: [REDACTED]',
        clean_stack,
        flags=re.IGNORECASE
    )

    # Remove cookie values
    clean_stack = re.sub(
        r'Cookie[:\s]+[^\r\n]+',
        'Cookie: [REDACTED]',
        clean_stack,
        flags=re.IGNORECASE
    )

    return clean_stack


# =============================================================================
# INTERNAL LOGGER IMPLEMENTATION
# =============================================================================

class InternalSovdevLogger:
    """Internal logger class - handles all complexity, hidden from developers."""

    def __init__(self, service_name: str, service_version: str, system_ids: Dict[str, str] = None):
        self.service_name = service_name
        self.service_version = service_version
        self.system_ids_mapping = system_ids or {}

    def resolve_peer_service(self, friendly_name: Optional[str]) -> str:
        """Resolve friendly name to CMDB ID or service name for internal operations."""
        # Default to INTERNAL if no peer service provided
        effective_name = friendly_name or "INTERNAL"

        # If INTERNAL, use the service's own name
        if effective_name == "INTERNAL":
            return self.service_name

        # Try to resolve from mapping
        resolved_id = self.system_ids_mapping.get(effective_name)
        if not resolved_id:
            print(f'⚠️ Unknown peer service: {effective_name}. Available: {", ".join(self.system_ids_mapping.keys())} or INTERNAL')
            return effective_name
        return resolved_id

    def process_exception(self, exception_object: Optional[BaseException]) -> Optional[Dict[str, str]]:
        """
        Process exception objects with security cleanup and standardization.
        Returns flat fields using snake_case (exception_type, exception_message, exception_stacktrace).
        """
        if not exception_object:
            return None

        # Extract raw stack trace
        raw_stack = ''.join(tb.format_exception(type(exception_object), exception_object, exception_object.__traceback__))

        # Remove credentials
        clean_stack = remove_credentials_from_stack(raw_stack)

        # Limit stack trace length
        limited_stack = limit_stack_trace(clean_stack, 350)

        # Standardize exception type to "Error" for cross-language consistency
        return {
            'exception_type': 'Error',  # Always "Error" regardless of actual Python type
            'exception_message': str(exception_object),
            'exception_stacktrace': limited_stack
        }

    def create_log_entry(
        self,
        level: str,
        function_name: str,
        message: str,
        peer_service: Optional[str],
        exception_object: Optional[BaseException],
        input_json: Any,
        response_json: Any,
        log_type: str
    ) -> Dict[str, Any]:
        """
        Create a complete structured log entry with all required fields.
        Uses snake_case field names for consistency across all languages.
        """
        # Generate unique event ID for this log entry
        event_id = str(uuid.uuid4())

        # Generate temporary trace_id - will be overridden by write_log if active span exists
        temp_trace_id = uuid.uuid4().hex

        # Resolve friendly name to CMDB ID (defaults to service_name for INTERNAL)
        resolved_peer_service = self.resolve_peer_service(peer_service)

        # Process exception object if provided
        processed_exception = self.process_exception(exception_object)

        # Create the complete log entry with snake_case fields
        log_entry = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'level': level.lower(),
            'service_name': self.service_name,
            'service_version': self.service_version,
            'peer_service': resolved_peer_service,
            'function_name': function_name,
            'message': message,
            'trace_id': temp_trace_id,
            'event_id': event_id,
            'log_type': log_type,
            'input_json': input_json,
            'response_json': response_json,
        }

        # Spread exception fields at top level if present
        if processed_exception:
            log_entry.update(processed_exception)

        return log_entry

    def map_to_python_level(self, level: str) -> int:
        """Map custom log levels to Python logging levels."""
        level_map = {
            'trace': logging.DEBUG,  # Python doesn't have TRACE, map to DEBUG
            'debug': logging.DEBUG,
            'info': logging.INFO,
            'warn': logging.WARNING,
            'error': logging.ERROR,
            'fatal': logging.CRITICAL,
        }
        return level_map.get(level.lower(), logging.INFO)

    def write_log(self, level: str, log_entry: Dict[str, Any]) -> None:
        """
        Write log entry using Python logging (multiple handlers including OTLP).
        Automatically emit metrics for complete observability.
        """
        start_time = time.time()

        try:
            # Extract trace ID and span ID from active span (stored in ContextVar)
            active_span = span_storage.get()
            if active_span:
                span_context = active_span.get_span_context()
                if span_context and span_context.trace_id:
                    # Override log trace_id with the active span's trace ID
                    log_entry['trace_id'] = format(span_context.trace_id, '032x')
                if span_context and span_context.span_id:
                    # Extract span ID for operation-level correlation
                    log_entry['span_id'] = format(span_context.span_id, '016x')

            # Emit metrics automatically
            if global_metrics:
                attributes = {
                    'service_name': log_entry['service_name'],
                    'service_version': log_entry['service_version'],
                    'peer_service': log_entry['peer_service'],
                    'log_level': level.lower(),
                    'log_type': log_entry['log_type']
                }

                # Increment active operations
                global_metrics.active_operations.add(1, attributes)

                # Increment operation counter
                global_metrics.operation_counter.add(1, attributes)

                # Track errors separately
                if level.upper() in ['ERROR', 'FATAL'] or log_entry.get('exception_type'):
                    error_attributes = {
                        **attributes,
                        'exception_type': log_entry.get('exception_type', 'Unknown')
                    }
                    global_metrics.error_counter.add(1, error_attributes)

            # Send to Python logging (all handlers including OTLP)
            python_level = self.map_to_python_level(level)

            # Create LogRecord with extra fields
            extra = {
                'service_name': log_entry['service_name'],
                'service_version': log_entry['service_version'],
                'peer_service': log_entry['peer_service'],
                'function_name': log_entry['function_name'],
                'log_type': log_entry['log_type'],
                'trace_id': log_entry['trace_id'],
                'event_id': log_entry['event_id'],
                'timestamp': log_entry['timestamp'],  # Add timestamp for Loki
            }

            # Add optional fields
            if 'span_id' in log_entry:
                extra['span_id'] = log_entry['span_id']
            if 'input_json' in log_entry:
                extra['input_json'] = log_entry['input_json']
            if 'response_json' in log_entry:
                extra['response_json'] = log_entry['response_json']
            if 'exception_type' in log_entry:
                extra['exception_type'] = log_entry['exception_type']
                extra['exception_message'] = log_entry['exception_message']
                extra['exception_stacktrace'] = log_entry['exception_stacktrace']

            base_logger.log(python_level, log_entry['message'], extra=extra)

            # Record operation duration and decrement active operations
            if global_metrics:
                duration = (time.time() - start_time) * 1000  # Convert to milliseconds
                attributes = {
                    'service_name': log_entry['service_name'],
                    'service_version': log_entry['service_version'],
                    'peer_service': log_entry['peer_service'],
                    'log_level': level.lower(),
                    'log_type': log_entry['log_type']
                }
                global_metrics.operation_duration.record(duration, attributes)
                global_metrics.active_operations.add(-1, attributes)

        except Exception as err:
            # Fallback - logging should never break the application
            print(f'Sovdev Logger failed: {err}')
            print(json.dumps(log_entry))

            # Decrement active operations on error
            if global_metrics:
                attributes = {
                    'service_name': log_entry['service_name'],
                    'service_version': log_entry['service_version'],
                    'peer_service': log_entry['peer_service'],
                    'log_level': level.lower(),
                    'log_type': log_entry['log_type']
                }
                global_metrics.active_operations.add(-1, attributes)

    def log(
        self,
        level: str,
        function_name: str,
        message: str,
        peer_service: str,
        input_json: Any = None,
        response_json: Any = None,
        exception_object: Optional[BaseException] = None
    ) -> None:
        """Main logging method - for transaction/request-response logs."""
        log_entry = self.create_log_entry(
            level, function_name, message, peer_service,
            exception_object, input_json, response_json, 'transaction'
        )
        self.write_log(level, log_entry)

    def log_job_status(
        self,
        level: str,
        function_name: str,
        job_name: str,
        status: str,
        peer_service: str,
        input_json: Any = None
    ) -> None:
        """Job status logging - for batch job start/complete/failed events."""
        message = f'Job {status}: {job_name}'
        context_input = {
            'job_name': job_name,
            'job_status': status,
            **(input_json or {})
        }

        log_entry = self.create_log_entry(
            level, function_name, message, peer_service,
            None, context_input, None, 'job.status'
        )
        self.write_log(level, log_entry)

    def log_job_progress(
        self,
        level: str,
        function_name: str,
        job_name: str,
        item_id: str,
        current: int,
        total: int,
        peer_service: str,
        input_json: Any = None
    ) -> None:
        """Job progress logging - for tracking batch processing progress (X of Y)."""
        message = f'Processing {item_id} ({current}/{total})'
        context_input = {
            'job_name': job_name,
            'item_id': item_id,
            'current_item': current,
            'total_items': total,
            'progress_percentage': round((current / total) * 100),
            **(input_json or {})
        }

        log_entry = self.create_log_entry(
            level, function_name, message, peer_service,
            None, context_input, None, 'job.progress'
        )
        self.write_log(level, log_entry)


# =============================================================================
# OPENTELEMETRY CONFIGURATION
# =============================================================================

def configure_metrics(service_name: str, service_version: str, session_id: str) -> Optional[MeterProvider]:
    """
    Configure OpenTelemetry Metrics.
    Creates automatic metrics for operations, errors, duration, and active operations.
    """
    try:
        resource = Resource(attributes={
            ResourceAttributes.SERVICE_NAME: service_name,
            ResourceAttributes.SERVICE_VERSION: service_version,
            ResourceAttributes.DEPLOYMENT_ENVIRONMENT: os.environ.get('NODE_ENV', 'development'),
            'session_id': session_id
        })

        # Configure metric exporter
        metric_endpoint = os.environ.get('OTEL_EXPORTER_OTLP_METRICS_ENDPOINT', 'http://localhost:4318/v1/metrics')
        headers_str = os.environ.get('OTEL_EXPORTER_OTLP_HEADERS', '{}')
        headers = json.loads(headers_str) if headers_str else {}

        metric_exporter = OTLPMetricExporter(
            endpoint=metric_endpoint,
            headers=headers
        )

        # Create periodic metric reader (export every 10 seconds)
        metric_reader = PeriodicExportingMetricReader(
            exporter=metric_exporter,
            export_interval_millis=10000  # 10 seconds
        )

        # Create MeterProvider
        meter_provider = MeterProvider(
            resource=resource,
            metric_readers=[metric_reader]
        )

        # Set global meter provider
        otel_metrics.set_meter_provider(meter_provider)

        print(f'📊 OTLP Metrics configured for: {metric_endpoint}')
        print('📊 Metrics: operations.total, errors.total, operation.duration, operations.active')

        return meter_provider

    except Exception as error:
        print(f'⚠️  Metrics configuration failed: {error}')
        return None


def configure_opentelemetry(service_name: str, service_version: str, session_id: str) -> Tuple[Optional[TracerProvider], Optional[LoggerProvider]]:
    """
    Configure OpenTelemetry with both trace AND log exporters.
    Full OTLP integration for complete observability.
    """
    try:
        resource = Resource(attributes={
            ResourceAttributes.SERVICE_NAME: service_name,
            ResourceAttributes.SERVICE_VERSION: service_version,
            ResourceAttributes.DEPLOYMENT_ENVIRONMENT: os.environ.get('NODE_ENV', 'development'),
            'session_id': session_id
        })

        # Parse OTLP headers
        headers_str = os.environ.get('OTEL_EXPORTER_OTLP_HEADERS', '{}')
        headers = json.loads(headers_str) if headers_str else {}

        # TRACE EXPORTER AND PROVIDER
        trace_endpoint = os.environ.get(
            'OTEL_EXPORTER_OTLP_TRACES_ENDPOINT',
            os.environ.get('OTEL_EXPORTER_OTLP_ENDPOINT', 'http://localhost:4318/v1/traces')
        )

        trace_exporter = OTLPSpanExporter(
            endpoint=trace_endpoint,
            headers=headers
        )

        tracer_provider = TracerProvider(resource=resource)
        # Configure BatchSpanProcessor with shorter delay for short-lived apps
        tracer_provider.add_span_processor(BatchSpanProcessor(
            trace_exporter,
            schedule_delay_millis=1000,  # Export every 1s (vs default 5s)
            max_queue_size=2048,
            max_export_batch_size=512,
            export_timeout_millis=30000
        ))

        # Set global BEFORE SDK initialization
        trace.set_tracer_provider(tracer_provider)

        print(f'🔍 OTLP Trace exporter configured for: {trace_endpoint}')
        print('✅ Global TracerProvider set')

        # LOG EXPORTER
        log_endpoint = os.environ.get('OTEL_EXPORTER_OTLP_LOGS_ENDPOINT')
        logger_provider = None

        if log_endpoint or os.environ.get('NODE_ENV', 'development') == 'development':
            log_exporter = OTLPLogExporter(
                endpoint=log_endpoint or 'http://localhost:4318/v1/logs',
                headers=headers
            )

            logger_provider = LoggerProvider(resource=resource)
            logger_provider.add_log_record_processor(BatchLogRecordProcessor(log_exporter))
            print(f'📡 OTLP Log exporter configured for: {log_endpoint or "http://localhost:4318/v1/logs"}')

        return tracer_provider, logger_provider

    except Exception as error:
        print(f'⚠️  OpenTelemetry SDK configuration failed: {error}')
        return None, None


# =============================================================================
# GLOBAL LOGGER INSTANCE MANAGEMENT
# =============================================================================

# Global logger instance - initialized once per application
global_logger: Optional[InternalSovdevLogger] = None

# Global session ID - generated once per application execution
global_session_id: Optional[str] = None


def initialize_sovdev_logger(
    service_name: str,
    service_version: Optional[str] = None,
    peer_services: Optional[Dict[str, str]] = None
) -> None:
    """
    Initialize the Sovdev logger with system identifier and OpenTelemetry SDK.
    Must be called once at application startup.
    """
    global global_logger, base_logger, otel_logging_handlers, global_metrics
    global global_meter_provider, global_tracer_provider, global_logger_provider
    global global_session_id

    effective_service_name = service_name
    effective_service_version = service_version or get_service_version()

    # Automatically add INTERNAL peer service pointing to this service
    effective_system_ids = {
        'INTERNAL': service_name,
        **(peer_services or {})
    }

    if not effective_service_name or effective_service_name.strip() == '':
        raise ValueError(
            'Sovdev Logger: service_name is required. '
            'Example: initialize_sovdev_logger("company-lookup-integration", "1.2.3", {...})'
        )

    # Generate session ID once for this execution
    session_id = str(uuid.uuid4())
    global_session_id = session_id
    print(f'🔑 Session ID: {session_id}')

    # Initialize OpenTelemetry Metrics FIRST (before SDK)
    if not global_meter_provider:
        global_meter_provider = configure_metrics(effective_service_name, effective_service_version, session_id)
        if global_meter_provider:
            # Create metrics instances
            meter = global_meter_provider.get_meter(effective_service_name, effective_service_version)
            global_metrics = SovdevMetrics(meter)

    # Initialize OpenTelemetry SDK with full configuration
    if not global_tracer_provider:
        tracer_provider, logger_provider = configure_opentelemetry(
            effective_service_name, effective_service_version, session_id
        )
        global_tracer_provider = tracer_provider
        global_logger_provider = logger_provider

    # Initialize Python logger with service_name
    base_logger, otel_logging_handlers = create_transports(effective_service_name.strip())

    global_logger = InternalSovdevLogger(
        effective_service_name.strip(),
        effective_service_version,
        effective_system_ids
    )

    is_development = os.environ.get('NODE_ENV', 'development') != 'production'
    has_otlp_endpoint = bool(os.environ.get('OTEL_EXPORTER_OTLP_LOGS_ENDPOINT'))
    log_to_console = os.environ.get('LOG_TO_CONSOLE', str(not has_otlp_endpoint)).lower() == 'true'
    log_to_file = os.environ.get('LOG_TO_FILE', 'true').lower() == 'true'

    print('🚀 Sovdev Logger initialized:')
    print(f'   ├── Service: {effective_service_name}')
    print(f'   ├── Version: {effective_service_version}')
    print(f'   ├── Systems: {", ".join(effective_system_ids.keys()) or "None configured"}')
    print(f'   ├── Console: {"Colored (dev)" if log_to_console and is_development else "JSON (prod)" if log_to_console else "Disabled"}')
    print(f'   ├── File: {"Enabled" if log_to_file else "Disabled"}')
    print(f'   └── OTLP: {"Configured" if has_otlp_endpoint else "⚠️  Not configured (using localhost:4318)"}')

    if not has_otlp_endpoint and not log_to_console and not log_to_file:
        print('⚠️  WARNING: All logging outputs are disabled!')
        print('   Set OTEL_EXPORTER_OTLP_LOGS_ENDPOINT, LOG_TO_CONSOLE=true, or LOG_TO_FILE=true')


def ensure_logger() -> InternalSovdevLogger:
    """Ensure logger is initialized before use."""
    if not global_logger:
        raise RuntimeError(
            'Sovdev Logger not initialized. Call sovdev_initialize(service_name) at application startup.'
        )
    return global_logger


# =============================================================================
# PUBLIC API - IDENTICAL ACROSS ALL LANGUAGES
# =============================================================================

def sovdev_log(
    level: SovdevLogLevel,
    function_name: str,
    message: str,
    peer_service: str,
    input_json: Any = None,
    response_json: Any = None,
    exception: Optional[BaseException] = None
) -> None:
    """
    General purpose logging function.

    Args:
        level: Log level from SOVDEV_LOGLEVELS constants
        function_name: Name of the function where logging occurs
        message: Human-readable description of what happened
        peer_service: Peer service identifier (use PEER_SERVICES.INTERNAL for internal operations)
        input_json: Valid JSON object containing function input parameters (optional)
        response_json: Valid JSON object containing function output/response data (optional)
        exception: Exception/error object (optional, None if no exception)
    """
    # Extract string value from enum
    level_str = level.value if isinstance(level, SOVDEV_LOGLEVELS) else str(level)
    ensure_logger().log(
        level_str, function_name, message, peer_service,
        input_json, response_json, exception
    )


def sovdev_log_job_status(
    level: SovdevLogLevel,
    function_name: str,
    job_name: str,
    status: str,
    peer_service: str,
    input_json: Any = None
) -> None:
    """
    Log job lifecycle events (start, completion, failure).

    Args:
        level: Log level from SOVDEV_LOGLEVELS constants
        function_name: Name of the function managing the job
        job_name: Name of the job being tracked
        status: Job status (e.g., "Started", "Completed", "Failed")
        peer_service: Target system or INTERNAL for internal jobs
        input_json: Additional job context variables (optional)
    """
    # Extract string value from enum
    level_str = level.value if isinstance(level, SOVDEV_LOGLEVELS) else str(level)
    ensure_logger().log_job_status(
        level_str, function_name, job_name, status, peer_service, input_json
    )


def sovdev_log_job_progress(
    level: SovdevLogLevel,
    function_name: str,
    item_id: str,
    current: int,
    total: int,
    peer_service: str,
    input_json: Any = None
) -> None:
    """
    Log processing progress for batch operations.

    Args:
        level: Log level from SOVDEV_LOGLEVELS constants
        function_name: Name of the function doing the processing
        item_id: Identifier for the item being processed
        current: Current item number (1-based)
        total: Total number of items to process
        peer_service: Target system for this item
        input_json: Additional context variables for this item (optional)
    """
    # Extract string value from enum
    level_str = level.value if isinstance(level, SOVDEV_LOGLEVELS) else str(level)
    ensure_logger().log_job_progress(
        level_str, function_name, "BatchProcessing", item_id, current, total,
        peer_service, input_json
    )


def sovdev_start_span(
    operation_name: str,
    attributes: Optional[Dict[str, Any]] = None
) -> Span:
    """
    Start a new span to track an operation's timing and hierarchy.

    Args:
        operation_name: Name of the operation (e.g., "lookupCompany", "processPayment")
        attributes: Optional metadata to make traces searchable in Grafana

    Returns:
        Span: Opaque handle that must be passed to sovdev_end_span()
    """
    if not global_tracer_provider:
        raise RuntimeError(
            'Sovdev Logger: TracerProvider not initialized. Call sovdev_initialize() first.'
        )

    tracer = global_tracer_provider.get_tracer('sovdev-logger', '1.0.0')

    # Create span
    span = tracer.start_span(operation_name)

    # Set attributes on span if provided
    if attributes:
        for key, value in attributes.items():
            if value is not None:
                if isinstance(value, (dict, list)):
                    span.set_attribute(key, json.dumps(value))
                else:
                    span.set_attribute(key, str(value))

    # Store span in ContextVar so logs can access it
    span_storage.set(span)

    return span


def sovdev_end_span(span: Span, error: Optional[BaseException] = None) -> None:
    """
    End a span, recording completion and calculating duration.

    Args:
        span: The span handle returned from sovdev_start_span()
        error: Optional error if operation failed (marks span as failed)
    """
    if not span:
        print('⚠️  sovdev_end_span called with None span')
        return

    try:
        if error:
            # Set span status to ERROR and record exception
            span.set_status(Status(StatusCode.ERROR, str(error)))
            span.record_exception(error)
        else:
            # Set span status to OK
            span.set_status(Status(StatusCode.OK))

        # End the span
        span.end()

        # Clear the span from ContextVar
        current_span = span_storage.get()
        if current_span == span:
            span_storage.set(None)

    except Exception as err:
        print(f'❌ sovdev_end_span failed: {err}')
        try:
            span.end()
        except:
            pass


def sovdev_flush() -> None:
    """
    Flush all pending logs, metrics, and traces.

    Blocks until all data is exported or 30-second timeout occurs.
    Safe to call from signal handlers and atexit hooks.
    """
    try:
        # Flush all providers
        if global_tracer_provider:
            print('🔄 Flushing OpenTelemetry traces...')
            global_tracer_provider.force_flush()
            print('✅ OpenTelemetry traces flushed successfully')

        if global_meter_provider:
            print('🔄 Flushing OpenTelemetry metrics...')
            global_meter_provider.force_flush()
            print('✅ OpenTelemetry metrics flushed successfully')

        if global_logger_provider:
            print('🔄 Flushing OpenTelemetry logs...')
            global_logger_provider.force_flush()
            print('✅ OpenTelemetry logs flushed successfully')

        # Flush OTEL logging handlers
        for handler in otel_logging_handlers:
            handler.flush()

    except Exception as error:
        print(f'⚠️  OpenTelemetry flush failed: {error}')


def create_peer_services(definitions: Dict[str, str]) -> 'PeerServices':
    """
    Create peer service mapping with INTERNAL auto-generation.

    Args:
        definitions: Dictionary mapping service names to system IDs

    Returns:
        PeerServices object with attribute access and mappings
    """
    class PeerServices:
        def __init__(self, defs: Dict[str, str]):
            self.mappings = defs
            self.INTERNAL = 'INTERNAL'
            # Add each definition as an attribute
            for key in defs.keys():
                setattr(self, key, key)

    return PeerServices(definitions)


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    'SOVDEV_LOGLEVELS',
    'sovdev_initialize',
    'sovdev_log',
    'sovdev_log_job_status',
    'sovdev_log_job_progress',
    'sovdev_start_span',
    'sovdev_end_span',
    'sovdev_flush',
    'create_peer_services',
]

# Alias for consistency
sovdev_initialize = initialize_sovdev_logger
