"""
Sovdev Logger - Core Implementation

Multi-language structured logging library implementing Norwegian Red Cross standards.
Provides initialization and state management for the logging system.
"""

import os
import uuid
from typing import Optional
from types import MappingProxyType


# =============================================================================
# GLOBAL STATE MANAGEMENT
# =============================================================================

class _LoggerState:
    """
    Global state container for the logger.

    Stores service metadata, system IDs mapping, and session information.
    """

    __slots__ = ('_service_name', '_service_version', '_system_ids', '_session_id', '_initialized')

    def __init__(self):
        """Initialize empty state."""
        self._service_name: Optional[str] = None
        self._service_version: Optional[str] = None
        self._system_ids: dict[str, str] = {}
        self._session_id: Optional[str] = None
        self._initialized: bool = False

    @property
    def service_name(self) -> Optional[str]:
        """Get the service name."""
        return self._service_name

    @property
    def service_version(self) -> Optional[str]:
        """Get the service version."""
        return self._service_version

    @property
    def system_ids(self) -> MappingProxyType[str, str]:
        """Get immutable view of system IDs mapping."""
        return MappingProxyType(self._system_ids)

    @property
    def session_id(self) -> Optional[str]:
        """Get the session ID."""
        return self._session_id

    @property
    def initialized(self) -> bool:
        """Check if logger has been initialized."""
        return self._initialized

    def initialize(
        self,
        service_name: str,
        service_version: str,
        system_ids: dict[str, str],
        session_id: str
    ) -> None:
        """
        Initialize the logger state.

        Args:
            service_name: Name of the service
            service_version: Version of the service
            system_ids: Mapping of peer service names to CMDB system IDs
            session_id: Unique session identifier for grouping logs
        """
        self._service_name = service_name
        self._service_version = service_version
        self._system_ids = system_ids.copy()  # Make a copy to prevent external modification
        self._session_id = session_id
        self._initialized = True

    def reset(self) -> None:
        """Reset state (primarily for testing)."""
        self._service_name = None
        self._service_version = None
        self._system_ids = {}
        self._session_id = None
        self._initialized = False


# Global logger state instance
_global_state = _LoggerState()


# =============================================================================
# VERSION AUTO-DETECTION
# =============================================================================

def _get_service_version() -> str:
    """
    Auto-detect service version from environment or package metadata.

    Checks in order:
    1. SERVICE_VERSION environment variable (deployment/CI)
    2. PYTHON_VERSION environment variable (alternative)
    3. package metadata (if available)

    Returns:
        Service version string or 'unknown' if not detected
    """
    # Try environment variables first (from CI/deployment)
    if 'SERVICE_VERSION' in os.environ:
        return os.environ['SERVICE_VERSION']

    if 'PYTHON_VERSION' in os.environ:
        return os.environ['PYTHON_VERSION']

    # Try reading package metadata
    try:
        from importlib.metadata import version
        return version('sovdev-logger')
    except Exception:
        pass

    return 'unknown'


# =============================================================================
# PUBLIC API - INITIALIZATION
# =============================================================================

def sovdev_initialize(
    service_name: str,
    service_version: Optional[str] = None,
    system_ids: Optional[dict[str, str]] = None
) -> None:
    """
    Initialize the Sovdev Logger with service metadata.

    Must be called once at application startup before any logging.

    Args:
        service_name: Name of the service (e.g., 'my-api-service')
        service_version: Version of the service (optional, auto-detected if not provided)
        system_ids: Mapping of peer service names to CMDB system IDs (optional)
                   Example: {'BRREG': 'SYS1234567', 'ALTINN': 'SYS1005678'}

    Example:
        >>> from sovdev_logger import sovdev_initialize, create_peer_services
        >>>
        >>> # Define peer services
        >>> PEER_SERVICES = create_peer_services({
        ...     'BRREG': 'SYS1234567',
        ...     'ALTINN': 'SYS1005678'
        ... })
        >>>
        >>> # Initialize logger
        >>> sovdev_initialize('my-service', '1.0.0', PEER_SERVICES.mappings)
    """
    # Validate service name
    if not service_name or not service_name.strip():
        raise ValueError("service_name cannot be empty")

    # Auto-detect version if not provided
    effective_version = service_version if service_version else _get_service_version()

    # Use provided system_ids or empty dict
    effective_system_ids = system_ids if system_ids else {}

    # Always add INTERNAL mapping (maps to service's own name)
    effective_system_ids_with_internal = effective_system_ids.copy()
    effective_system_ids_with_internal['INTERNAL'] = service_name.strip()

    # Generate session ID for this execution
    session_id = str(uuid.uuid4())

    # Initialize global state
    _global_state.initialize(
        service_name=service_name.strip(),
        service_version=effective_version,
        system_ids=effective_system_ids_with_internal,
        session_id=session_id
    )

    # Initialize OpenTelemetry SDK (logs, traces, metrics)
    from .otel import initialize_otel
    # verbose=False by default to avoid interfering with structured logging output
    initialize_otel(service_name.strip(), effective_version, session_id, verbose=False)


def get_logger_state() -> dict[str, any]:
    """
    Get current logger state (primarily for testing and verification).

    Returns:
        Dictionary containing current state:
        - service_name: str
        - service_version: str
        - system_ids: dict[str, str]
        - session_id: str
        - initialized: bool
    """
    return {
        'service_name': _global_state.service_name,
        'service_version': _global_state.service_version,
        'system_ids': dict(_global_state.system_ids),
        'session_id': _global_state.session_id,
        'initialized': _global_state.initialized
    }


def _ensure_initialized() -> _LoggerState:
    """
    Ensure logger is initialized before use.

    Returns:
        The global logger state

    Raises:
        RuntimeError: If logger not initialized
    """
    if not _global_state.initialized:
        raise RuntimeError(
            'Sovdev Logger not initialized. Call sovdev_initialize(service_name) '
            'at application startup before logging.'
        )
    return _global_state


# =============================================================================
# LOG ENTRY CREATION
# =============================================================================

def _resolve_peer_service(peer_service: str) -> str:
    """
    Resolve friendly peer service name to CMDB ID or service name.

    Args:
        peer_service: Friendly peer service name (e.g., 'BRREG', 'INTERNAL')

    Returns:
        Resolved system ID from mapping, or original name if not found
    """
    state = _ensure_initialized()

    # Try to resolve from mapping
    if peer_service in state.system_ids:
        return state.system_ids[peer_service]

    # Warn if not found (but don't fail - use as-is)
    import sys
    available = ', '.join(state.system_ids.keys())
    print(f"⚠️  Warning: Unknown peer service '{peer_service}'. Available: {available}", file=sys.stderr)
    return peer_service


def _process_exception(exception_object: any) -> dict[str, any]:
    """
    Process exception object into structured format.

    Security-aware: Removes authentication credentials from error messages.

    Args:
        exception_object: Exception or error object

    Returns:
        Dictionary with exception details
    """
    import traceback

    if exception_object is None:
        return None

    # Extract basic exception info
    # Use "Error" for consistency across languages (matching TypeScript)
    exception_data = {
        'type': 'Error',
        'message': str(exception_object)
    }

    # Add stack trace if available
    if hasattr(exception_object, '__traceback__'):
        exception_data['stack'] = ''.join(
            traceback.format_exception(
                type(exception_object),
                exception_object,
                exception_object.__traceback__
            )
        )

    # Security: Remove sensitive patterns from message
    # (passwords, tokens, api keys, etc.)
    sensitive_patterns = [
        'password=', 'token=', 'apikey=', 'api_key=',
        'secret=', 'authorization:', 'bearer '
    ]

    message_lower = exception_data['message'].lower()
    for pattern in sensitive_patterns:
        if pattern in message_lower:
            exception_data['message'] = '[REDACTED - Contains sensitive data]'
            break

    return exception_data


def _create_log_entry(
    level: str,
    function_name: str,
    message: str,
    peer_service: str,
    input_json: Optional[any] = None,
    response_json: Optional[any] = None,
    exception_object: Optional[any] = None,
    trace_id: Optional[str] = None,
    log_type: Optional[str] = None
) -> dict[str, any]:
    """
    Create structured log entry following "Loggeloven av 2025" standard.

    Uses OpenTelemetry/ECS field naming conventions.

    Args:
        level: Log level (TRACE, DEBUG, INFO, WARN, ERROR, FATAL)
        function_name: Name of the function/operation
        message: Human-readable message
        peer_service: Peer service identifier
        input_json: Input data (optional)
        response_json: Response data (optional)
        exception_object: Exception object (optional)
        trace_id: Trace ID for correlation (optional, auto-generated if not provided)

    Returns:
        Structured log entry dictionary
    """
    from datetime import datetime, timezone

    state = _ensure_initialized()

    # Generate event ID
    event_id = str(uuid.uuid4())

    # Use provided trace_id or generate new one
    final_trace_id = trace_id if trace_id else str(uuid.uuid4())

    # Resolve peer service to CMDB ID
    resolved_peer_service = _resolve_peer_service(peer_service)

    # Process exception if provided
    processed_exception = _process_exception(exception_object) if exception_object else None

    # Build structured log entry
    log_entry = {
        # Timestamp
        'timestamp': datetime.now(timezone.utc).isoformat(),

        # Log level
        'level': level,

        # Service metadata (OTEL semantic conventions)
        'service': {
            'name': state.service_name,
            'version': state.service_version
        },

        # Session ID for grouping logs from same execution
        'session': {
            'id': state.session_id
        },

        # Trace ID for correlation
        'trace': {
            'id': final_trace_id
        },

        # Event ID (unique per log entry)
        'event': {
            'id': event_id
        },

        # Function/operation name
        'function': {
            'name': function_name
        },

        # Message
        'message': message,

        # Peer service (resolved to CMDB ID)
        'peer': {
            'service': resolved_peer_service
        },

        # Log type classification (matches TypeScript)
        'log_type': log_type or 'transaction'  # Default to transaction if not specified
    }

    # Add optional fields
    if input_json is not None:
        log_entry['input'] = input_json

    if response_json is not None:
        log_entry['response'] = response_json

    if processed_exception is not None:
        log_entry['exception'] = processed_exception

    return log_entry


# =============================================================================
# PUBLIC API - LOGGING
# =============================================================================

def sovdev_flush(timeout_millis: int = 30000) -> None:
    """
    Flush all OTEL providers to ensure telemetry is sent.

    Should be called before application exit to ensure all logs, metrics,
    and traces are exported to the OTLP collector.

    Args:
        timeout_millis: Timeout in milliseconds (default: 30000)

    Example:
        >>> from sovdev_logger import sovdev_initialize, sovdev_log, sovdev_flush, SOVDEV_LOGLEVELS, create_peer_services
        >>>
        >>> PEER_SERVICES = create_peer_services({})
        >>> sovdev_initialize('my-service', '1.0.0')
        >>> sovdev_log(SOVDEV_LOGLEVELS.INFO, 'main', 'Application started', PEER_SERVICES.INTERNAL)
        >>> sovdev_flush()  # Ensure all telemetry is sent before exit
    """
    import sys
    from .otel import force_flush_otel, shutdown_otel

    print('🔄 Flushing OpenTelemetry providers...', file=sys.stderr)
    success = force_flush_otel(timeout_millis)

    if success:
        print('✅ OpenTelemetry flush complete', file=sys.stderr)
    else:
        print('⚠️  OpenTelemetry flush completed with errors', file=sys.stderr)

    # Shutdown providers (optional, but recommended for clean exit)
    shutdown_otel()


def sovdev_log(
    level: str,
    function_name: str,
    message: str,
    peer_service: str,
    input_json: Optional[any] = None,
    response_json: Optional[any] = None,
    exception_object: Optional[any] = None,
    trace_id: Optional[str] = None,
    log_type: Optional[str] = None
) -> None:
    """
    Log a structured message.

    Main logging function following "Loggeloven av 2025" requirements.

    Args:
        level: Log level from SOVDEV_LOGLEVELS
        function_name: Name of the function where logging occurs
        message: Human-readable message
        peer_service: Peer service identifier (use create_peer_services constants)
        input_json: Input data as JSON-serializable object (optional)
        response_json: Response data as JSON-serializable object (optional)
        exception_object: Exception object (optional)
        trace_id: Trace ID for correlation (optional, auto-generated)

    Example:
        >>> from sovdev_logger import sovdev_initialize, sovdev_log, SOVDEV_LOGLEVELS, create_peer_services
        >>>
        >>> PEER_SERVICES = create_peer_services({'BRREG': 'SYS1234567'})
        >>> sovdev_initialize('my-service', '1.0.0', PEER_SERVICES.mappings)
        >>>
        >>> sovdev_log(
        ...     SOVDEV_LOGLEVELS.INFO,
        ...     'get_company_info',
        ...     'Retrieved company information',
        ...     PEER_SERVICES.BRREG,
        ...     input_json={'org_number': '123456789'},
        ...     response_json={'name': 'Test Company AS'}
        ... )
    """
    import json
    import sys
    import time
    from .config import get_config
    from .file_handler import write_log_to_file
    from .otel import get_logger_provider, get_tracer_provider, get_meter_provider

    # Start timing for metrics
    start_time = time.time()

    # Create span for tracing (if tracer available)
    span = None
    tracer_provider = get_tracer_provider()
    if tracer_provider:
        from opentelemetry import trace
        from opentelemetry.trace import SpanKind, Status, StatusCode

        tracer = trace.get_tracer(__name__, tracer_provider=tracer_provider)
        span = tracer.start_span(
            name=function_name,
            kind=SpanKind.INTERNAL
        )

        # Add span attributes
        state = _ensure_initialized()
        resolved_peer = _resolve_peer_service(peer_service)

        # Create log entry first to get log_type
        temp_log_entry = {'log_type': log_type or 'transaction'}

        span.set_attributes({
            'service.name': state.service_name,
            'service.version': state.service_version,
            'peer.service': resolved_peer,
            'function.name': function_name,
            'log.level': level,
            'log.type': temp_log_entry['log_type']
        })

    # Create structured log entry
    log_entry = _create_log_entry(
        level=level,
        function_name=function_name,
        message=message,
        peer_service=peer_service,
        input_json=input_json,
        response_json=response_json,
        exception_object=exception_object,
        trace_id=trace_id,
        log_type=log_type
    )

    # Add events to span
    if span:
        if input_json:
            span.add_event('input', {'input.data': json.dumps(input_json)})
        if response_json:
            span.add_event('response', {'response.data': json.dumps(response_json)})

        # Mark span status
        if exception_object:
            span.set_status(Status(StatusCode.ERROR, str(exception_object)))
            span.record_exception(exception_object)
        elif level in ('ERROR', 'FATAL'):
            span.set_status(Status(StatusCode.ERROR, message))
        else:
            span.set_status(Status(StatusCode.OK))

    # Emit metrics (if meter available)
    from .otel import get_metrics
    global_metrics = get_metrics()
    if global_metrics['operation_counter']:
        state = _ensure_initialized()
        resolved_peer = _resolve_peer_service(peer_service)

        attributes = {
            'service.name': state.service_name,
            'service.version': state.service_version,
            'peer.service': resolved_peer,
            'log.level': level,
            'log.type': log_entry['log_type']  # Add log_type to match TypeScript
        }

        # Increment active operations
        if global_metrics['active_operations']:
            try:
                global_metrics['active_operations'].add(1, attributes)
            except Exception as e:
                print(f"⚠️ Active operations increment failed: {e}", file=sys.stderr)

        # Increment operation counter (using pre-created global instrument)
        try:
            global_metrics['operation_counter'].add(1, attributes)
            # DEBUG: Print to confirm metrics are being recorded
            import os
            if os.environ.get('DEBUG_METRICS'):
                print(f"DEBUG: Metric recorded - {attributes}", file=sys.stderr)
        except Exception as e:
            print(f"⚠️ Metric recording failed: {e}", file=sys.stderr)

        # Track errors separately
        if level in ('ERROR', 'FATAL') or exception_object:
            error_attributes = {
                **attributes,
                'exception.type': log_entry.get('exception', {}).get('type', 'Unknown')
            }
            if global_metrics['error_counter']:
                try:
                    global_metrics['error_counter'].add(1, error_attributes)
                except Exception as e:
                    print(f"⚠️ Error counter failed: {e}", file=sys.stderr)

    # Get configuration for transport selection
    config = get_config()

    # Output to console if enabled (smart defaults applied in config)
    if config['console_enabled']:
        print(json.dumps(log_entry, ensure_ascii=False), file=sys.stderr)

    # Output to file if enabled
    if config['file_enabled']:
        write_log_to_file(
            log_entry,
            config['log_file_path'],
            config['log_file_max_bytes'],
            config['log_file_backup_count']
        )

    # Send to OTEL if LoggerProvider is configured
    logger_provider = get_logger_provider()
    if logger_provider:
        from opentelemetry import _logs
        from opentelemetry.sdk._logs import LogRecord
        from opentelemetry._logs import SeverityNumber

        # Map sovdev log levels to OTEL severity
        severity_map = {
            'TRACE': SeverityNumber.TRACE,
            'DEBUG': SeverityNumber.DEBUG,
            'INFO': SeverityNumber.INFO,
            'WARN': SeverityNumber.WARN,
            'ERROR': SeverityNumber.ERROR,
            'FATAL': SeverityNumber.FATAL
        }

        # Get OTEL logger with service name as scope (matching TypeScript pattern)
        # Use service name instead of __name__ for consistency across languages
        logger = _logs.get_logger(log_entry["service"]["name"], "1.0.0", logger_provider=logger_provider)

        # Build attributes object with OTEL standard fields (matching TypeScript pattern)
        otel_attributes = {
            "service.name": log_entry["service"]["name"],
            "service.version": log_entry["service"]["version"],
            "peer.service": log_entry["peer"]["service"],
            "functionName": log_entry["function"]["name"],
            "timestamp": log_entry.get("timestamp"),
            "observed_timestamp": str(int(time.time() * 1_000_000_000))  # Nanosecond timestamp (matching TypeScript)
        }

        # Add correlation fields (OpenTelemetry/ECS standard)
        if log_entry.get("trace"):
            otel_attributes["traceId"] = log_entry["trace"]["id"]
        if log_entry.get("event"):
            otel_attributes["eventId"] = log_entry["event"]["id"]

        # Add log classification
        if log_entry.get("log_type"):
            otel_attributes["logType"] = log_entry["log_type"]

        # Serialize inputJSON and responseJSON as JSON strings for OTLP (matching TypeScript)
        if log_entry.get("input") is not None:
            otel_attributes["inputJSON"] = json.dumps(log_entry["input"])

        # Always add responseJSON (matching TypeScript pattern - sends "null" when no response)
        otel_attributes["responseJSON"] = json.dumps(log_entry.get("response"))

        # Add exception details if present (matching TypeScript pattern)
        if log_entry.get("exception"):
            otel_attributes["exceptionType"] = log_entry["exception"]["type"]
            otel_attributes["exceptionMessage"] = log_entry["exception"]["message"]
            if log_entry["exception"].get("stack"):
                otel_attributes["exceptionStack"] = log_entry["exception"]["stack"]

        # DEBUG: Print attributes being sent
        if os.environ.get('DEBUG_OTEL_LOGS'):
            print(f"🐛 OTEL Attributes: {otel_attributes}", file=sys.stderr)

        # Emit log record with message as body and all other fields as attributes
        # This matches TypeScript pattern: body=message, attributes=everything else
        logger.emit(
            LogRecord(
                timestamp=None,  # Will be set automatically
                severity_number=severity_map.get(level, SeverityNumber.INFO),
                severity_text=level,
                body=log_entry.get("message", ""),  # Just the message string
                resource=logger_provider.resource,
                attributes=otel_attributes  # All other fields as attributes
            )
        )

    # Record operation duration and decrement active operations
    if global_metrics['operation_duration_histogram']:
        duration_ms = (time.time() - start_time) * 1000
        global_metrics['operation_duration_histogram'].record(duration_ms, attributes)

    # Decrement active operations
    if global_metrics['active_operations']:
        try:
            global_metrics['active_operations'].add(-1, attributes)
        except Exception as e:
            print(f"⚠️ Active operations decrement failed: {e}", file=sys.stderr)

    # End span
    if span:
        span.end()


def sovdev_generate_trace_id() -> str:
    """
    Generate a unique trace ID (UUID v4).

    Returns:
        str: A unique UUID v4 string for trace correlation

    Example:
        >>> from sovdev_logger import sovdev_generate_trace_id
        >>> trace_id = sovdev_generate_trace_id()
        >>> print(trace_id)
        '550e8400-e29b-41d4-a716-446655440000'
    """
    return str(uuid.uuid4())


def sovdev_log_job_status(
    level: str,
    function_name: str,
    job_name: str,
    status: str,
    peer_service: str,
    input_json: Optional[any] = None,
    trace_id: Optional[str] = None
) -> None:
    """
    Log job status (Started/Completed/Failed).

    Convenience function for logging batch job lifecycle events.

    Args:
        level: Log level from SOVDEV_LOGLEVELS
        function_name: Name of the function managing the job
        job_name: Name of the job being tracked
        status: Job status (e.g., 'Started', 'Completed', 'Failed')
        peer_service: Peer service identifier (typically INTERNAL for jobs)
        input_json: Job metadata (e.g., total items, start time) (optional)
        trace_id: Trace ID for correlation (optional, auto-generated)

    Example:
        >>> from sovdev_logger import sovdev_log_job_status, SOVDEV_LOGLEVELS, create_peer_services
        >>>
        >>> PEER_SERVICES = create_peer_services({})
        >>> sovdev_log_job_status(
        ...     SOVDEV_LOGLEVELS.INFO,
        ...     'batch_processor',
        ...     'DataImportBatch',
        ...     'Started',
        ...     PEER_SERVICES.INTERNAL,
        ...     {'total_items': 1000}
        ... )
    """
    message = f"Job {status}: {job_name}"
    sovdev_log(
        level=level,
        function_name=function_name,
        message=message,
        peer_service=peer_service,
        input_json=input_json,
        response_json=None,
        exception_object=None,
        trace_id=trace_id,
        log_type='job.status'
    )


def sovdev_log_job_progress(
    level: str,
    function_name: str,
    item_id: str,
    current: int,
    total: int,
    peer_service: str,
    input_json: Optional[any] = None,
    trace_id: Optional[str] = None
) -> None:
    """
    Log processing progress for batch operations.

    Convenience function for logging progress during batch/job processing.

    Args:
        level: Log level from SOVDEV_LOGLEVELS
        function_name: Name of the function doing the processing
        item_id: Identifier for the item being processed
        current: Current item number (1-based)
        total: Total number of items to process
        peer_service: Peer service being called
        input_json: Additional context for this item (optional)
        trace_id: Trace ID for correlation (optional, auto-generated)

    Example:
        >>> from sovdev_logger import sovdev_log_job_progress, SOVDEV_LOGLEVELS, create_peer_services
        >>>
        >>> PEER_SERVICES = create_peer_services({'DATABASE': 'SYS9876543'})
        >>> for i, record_id in enumerate(records, 1):
        ...     sovdev_log_job_progress(
        ...         SOVDEV_LOGLEVELS.INFO,
        ...         'process_records',
        ...         record_id,
        ...         i,
        ...         len(records),
        ...         PEER_SERVICES.DATABASE,
        ...         {'record_id': record_id}
        ...     )
    """
    message = f"Processing {item_id} ({current}/{total})"
    sovdev_log(
        level=level,
        function_name=function_name,
        message=message,
        peer_service=peer_service,
        input_json=input_json,
        response_json=None,
        exception_object=None,
        trace_id=trace_id,
        log_type='job.progress'
    )
