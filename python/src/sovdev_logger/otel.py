"""
OpenTelemetry Integration Module

Provides full OTEL SDK integration for logs, metrics, and traces.
Matches TypeScript implementation pattern.
"""

import os
import json
from typing import Optional
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry import trace, metrics, _logs
import sys


# =============================================================================
# GLOBAL OTEL PROVIDERS AND METRICS
# =============================================================================

_logger_provider: Optional[LoggerProvider] = None
_tracer_provider: Optional[TracerProvider] = None
_meter_provider: Optional[MeterProvider] = None

# Global metrics instruments (created once, reused for all operations)
_operation_counter = None
_error_counter = None
_operation_duration_histogram = None
_active_operations = None


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _get_otlp_headers() -> dict[str, str]:
    """
    Parse OTEL_EXPORTER_OTLP_HEADERS environment variable.

    Returns:
        Dictionary of headers
    """
    headers_env = os.environ.get('OTEL_EXPORTER_OTLP_HEADERS', '{}')
    try:
        return json.loads(headers_env)
    except json.JSONDecodeError:
        print(f"⚠️  Warning: Could not parse OTEL_EXPORTER_OTLP_HEADERS: {headers_env}", file=sys.stderr)
        return {}


def _get_trace_endpoint() -> str:
    """Get OTLP trace endpoint from environment."""
    return (
        os.environ.get('OTEL_EXPORTER_OTLP_TRACES_ENDPOINT') or
        os.environ.get('OTEL_EXPORTER_OTLP_ENDPOINT', 'http://localhost:4318') + '/v1/traces'
    )


def _get_log_endpoint() -> Optional[str]:
    """Get OTLP log endpoint from environment."""
    if 'OTEL_EXPORTER_OTLP_LOGS_ENDPOINT' in os.environ:
        return os.environ['OTEL_EXPORTER_OTLP_LOGS_ENDPOINT']
    if 'OTEL_EXPORTER_OTLP_ENDPOINT' in os.environ:
        base = os.environ['OTEL_EXPORTER_OTLP_ENDPOINT']
        return f"{base}/v1/logs" if not base.endswith('/v1/logs') else base
    return None


def _get_metric_endpoint() -> str:
    """Get OTLP metric endpoint from environment."""
    return (
        os.environ.get('OTEL_EXPORTER_OTLP_METRICS_ENDPOINT') or
        os.environ.get('OTEL_EXPORTER_OTLP_ENDPOINT', 'http://localhost:4318') + '/v1/metrics'
    )


# =============================================================================
# OTEL INITIALIZATION
# =============================================================================

def initialize_otel(
    service_name: str,
    service_version: str,
    session_id: str,
    verbose: bool = False
) -> tuple[Optional[LoggerProvider], Optional[TracerProvider], Optional[MeterProvider]]:
    """
    Initialize OpenTelemetry SDK with Logs, Traces, and Metrics.

    Matches TypeScript implementation pattern:
    - Creates Resource with service.name, service.version, session.id
    - Sets up LoggerProvider with OTLPLogExporter
    - Sets up TracerProvider with OTLPSpanExporter
    - Sets up MeterProvider with OTLPMetricExporter

    Args:
        service_name: Service name
        service_version: Service version
        session_id: Session ID for grouping logs
        verbose: Enable verbose diagnostic output (default: False)

    Returns:
        Tuple of (LoggerProvider, TracerProvider, MeterProvider)
    """
    global _logger_provider, _tracer_provider, _meter_provider

    try:
        # Create Resource with semantic conventions
        resource = Resource.create({
            SERVICE_NAME: service_name,
            SERVICE_VERSION: service_version,
            'deployment.environment': os.environ.get('DEPLOYMENT_ENVIRONMENT', 'development'),
            'session.id': session_id  # Custom attribute for execution grouping
        })

        headers = _get_otlp_headers()

        # =============================================================================
        # TRACER PROVIDER SETUP
        # =============================================================================
        trace_endpoint = _get_trace_endpoint()

        try:
            trace_exporter = OTLPSpanExporter(
                endpoint=trace_endpoint,
                headers=headers
            )

            _tracer_provider = TracerProvider(resource=resource)
            _tracer_provider.add_span_processor(BatchSpanProcessor(trace_exporter))

            # Set as global tracer provider
            trace.set_tracer_provider(_tracer_provider)

            if verbose:
                print(f'🔍 OTLP Trace exporter configured for: {trace_endpoint}', file=sys.stderr)
        except Exception as e:
            if verbose:
                print(f'⚠️  Failed to configure trace exporter: {e}', file=sys.stderr)
            _tracer_provider = None

        # =============================================================================
        # LOGGER PROVIDER SETUP
        # =============================================================================
        log_endpoint = _get_log_endpoint()

        if log_endpoint:
            try:
                log_exporter = OTLPLogExporter(
                    endpoint=log_endpoint,
                    headers=headers
                )

                _logger_provider = LoggerProvider(resource=resource)
                _logger_provider.add_log_record_processor(BatchLogRecordProcessor(log_exporter))

                # Set as global logger provider
                _logs.set_logger_provider(_logger_provider)

                if verbose:
                    print(f'📡 OTLP Log exporter configured for: {log_endpoint}', file=sys.stderr)
                    print('📡 BatchLogRecordProcessor added to LoggerProvider', file=sys.stderr)
            except Exception as e:
                if verbose:
                    print(f'⚠️  Failed to configure log exporter: {e}', file=sys.stderr)
                _logger_provider = None
        else:
            if verbose:
                print('📡 OTLP Log exporter not configured (no endpoint)', file=sys.stderr)
            _logger_provider = None

        # =============================================================================
        # METER PROVIDER SETUP
        # =============================================================================
        metric_endpoint = _get_metric_endpoint()

        try:
            # Configure metric exporter with CUMULATIVE temporality (Prometheus compatible)
            # Python OTEL SDK defaults to DELTA, but Prometheus Remote Write requires CUMULATIVE
            from opentelemetry.sdk.metrics.export import AggregationTemporality, ConsoleMetricExporter
            from opentelemetry.sdk.metrics._internal.instrument import Counter, Histogram

            # Create custom metric exporter that uses CUMULATIVE temporality
            class CumulativeOTLPMetricExporter(OTLPMetricExporter):
                """OTLP Metric Exporter configured for Prometheus (CUMULATIVE temporality)"""
                def __init__(self, *args, **kwargs):
                    super().__init__(*args, **kwargs)
                    # Override temporality preference for all instrument types
                    self._preferred_temporality = {
                        Counter: AggregationTemporality.CUMULATIVE,
                        Histogram: AggregationTemporality.CUMULATIVE,
                    }

            metric_exporter = CumulativeOTLPMetricExporter(
                endpoint=metric_endpoint,
                headers=headers
            )

            metric_reader = PeriodicExportingMetricReader(
                exporter=metric_exporter,
                export_interval_millis=10000  # Export every 10 seconds (matches TypeScript)
            )

            _meter_provider = MeterProvider(
                resource=resource,
                metric_readers=[metric_reader]
            )

            # Set as global meter provider
            metrics.set_meter_provider(_meter_provider)

            # Create global metric instruments (create once, reuse for all operations)
            global _operation_counter, _error_counter, _operation_duration_histogram, _active_operations
            meter = metrics.get_meter(__name__, meter_provider=_meter_provider)

            _operation_counter = meter.create_counter(
                name='sovdev_operations_total',
                description='Total number of sovdev operations',
                unit='1'
            )

            _error_counter = meter.create_counter(
                name='sovdev_errors_total',
                description='Total number of errors by service, peer service, and exception type',
                unit='1'
            )

            _operation_duration_histogram = meter.create_histogram(
                name='sovdev_operation_duration',
                description='Duration of sovdev operations in milliseconds',
                unit='ms'
            )

            _active_operations = meter.create_up_down_counter(
                name='sovdev_operations_active',
                description='Number of currently active operations',
                unit='1'
            )

            if verbose:
                print(f'📊 OTLP Metric exporter configured for: {metric_endpoint}', file=sys.stderr)
        except Exception as e:
            if verbose:
                print(f'⚠️  Failed to configure metric exporter: {e}', file=sys.stderr)
            _meter_provider = None

        if verbose:
            print(f'🔗 OpenTelemetry SDK initialized for {service_name}', file=sys.stderr)

        return _logger_provider, _tracer_provider, _meter_provider

    except Exception as error:
        if verbose:
            print(f'⚠️  OpenTelemetry SDK configuration failed: {error}', file=sys.stderr)
        return None, None, None


def get_logger_provider() -> Optional[LoggerProvider]:
    """Get the global LoggerProvider instance."""
    return _logger_provider


def get_tracer_provider() -> Optional[TracerProvider]:
    """Get the global TracerProvider instance."""
    return _tracer_provider


def get_meter_provider() -> Optional[MeterProvider]:
    """Get the global MeterProvider instance."""
    return _meter_provider


def get_metrics():
    """Get the global metrics instruments."""
    return {
        'operation_counter': _operation_counter,
        'error_counter': _error_counter,
        'operation_duration_histogram': _operation_duration_histogram,
        'active_operations': _active_operations
    }


def shutdown_otel() -> None:
    """
    Shutdown all OTEL providers and flush remaining telemetry.

    Should be called at application shutdown.
    """
    global _logger_provider, _tracer_provider, _meter_provider

    if _logger_provider:
        try:
            _logger_provider.shutdown()
            print('📡 LoggerProvider shutdown complete', file=sys.stderr)
        except Exception as e:
            print(f'⚠️  LoggerProvider shutdown error: {e}', file=sys.stderr)

    if _tracer_provider:
        try:
            _tracer_provider.shutdown()
            print('🔍 TracerProvider shutdown complete', file=sys.stderr)
        except Exception as e:
            print(f'⚠️  TracerProvider shutdown error: {e}', file=sys.stderr)

    if _meter_provider:
        try:
            _meter_provider.shutdown()
            print('📊 MeterProvider shutdown complete', file=sys.stderr)
        except Exception as e:
            print(f'⚠️  MeterProvider shutdown error: {e}', file=sys.stderr)

    _logger_provider = None
    _tracer_provider = None
    _meter_provider = None


def force_flush_otel(timeout_millis: int = 30000) -> bool:
    """
    Force flush all OTEL providers.

    Args:
        timeout_millis: Timeout in milliseconds

    Returns:
        True if all providers flushed successfully
    """
    timeout_seconds = timeout_millis / 1000.0
    success = True

    if _logger_provider:
        try:
            _logger_provider.force_flush(timeout_millis=int(timeout_seconds * 1000))
        except Exception as e:
            print(f'⚠️  LoggerProvider flush error: {e}', file=sys.stderr)
            success = False

    if _tracer_provider:
        try:
            _tracer_provider.force_flush(timeout_millis=int(timeout_seconds * 1000))
        except Exception as e:
            print(f'⚠️  TracerProvider flush error: {e}', file=sys.stderr)
            success = False

    if _meter_provider:
        try:
            _meter_provider.force_flush(timeout_millis=int(timeout_seconds * 1000))
        except Exception as e:
            print(f'⚠️  MeterProvider flush error: {e}', file=sys.stderr)
            success = False

    return success
