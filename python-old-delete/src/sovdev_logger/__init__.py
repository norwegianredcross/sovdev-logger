"""
sovdev-logger: Structured logging library for OpenTelemetry

Multi-language structured logging library implementing Norwegian Red Cross standards.
"""

__version__ = "1.0.0"
__author__ = "Terje Christensen"
__license__ = "MIT"

# Public API exports
from .log_levels import SOVDEV_LOGLEVELS
from .peer_services import create_peer_services
from .logger import (
    sovdev_initialize,
    sovdev_log,
    sovdev_flush,
    sovdev_generate_trace_id,
    sovdev_log_job_status,
    sovdev_log_job_progress,
    get_logger_state
)

__all__ = [
    'SOVDEV_LOGLEVELS',
    'create_peer_services',
    'sovdev_initialize',
    'sovdev_log',
    'sovdev_flush',
    'sovdev_generate_trace_id',
    'sovdev_log_job_status',
    'sovdev_log_job_progress',
    'get_logger_state',
]
