"""
Sovdev Logger - Main Export File

Structured logging library for OpenTelemetry with "Loggeloven av 2025" compliance

Example:
    >>> from sovdev_logger import sovdev_initialize, sovdev_log, SOVDEV_LOGLEVELS, create_peer_services
    >>>
    >>> PEER_SERVICES = create_peer_services({'BRREG': 'SYS1234567'})
    >>> sovdev_initialize('my-service', '1.0.0', PEER_SERVICES.mappings)
    >>>
    >>> sovdev_log(SOVDEV_LOGLEVELS.INFO, 'test', 'Hello', PEER_SERVICES.INTERNAL)
"""

# Export main logging functions
from .logger import (
    sovdev_initialize,
    sovdev_log,
    sovdev_log_job_status,
    sovdev_log_job_progress,
    sovdev_flush,
    sovdev_generate_trace_id
)

# Export log levels
from .log_levels import SOVDEV_LOGLEVELS

# Export peer service helper
from .peer_services import create_peer_services

__all__ = [
    'sovdev_initialize',
    'sovdev_log',
    'sovdev_log_job_status',
    'sovdev_log_job_progress',
    'sovdev_flush',
    'sovdev_generate_trace_id',
    'SOVDEV_LOGLEVELS',
    'create_peer_services'
]

__version__ = '1.0.0'
