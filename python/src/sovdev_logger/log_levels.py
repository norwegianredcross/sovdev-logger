"""
Sovdev Logger - Log Levels

Standard log levels following "Loggeloven av 2025" requirements
ERROR and FATAL levels trigger ServiceNow incidents
"""

from enum import Enum


class SOVDEV_LOGLEVELS(str, Enum):
    """
    Log levels matching OpenTelemetry severity numbers.

    Subclasses str to allow use as string literals.
    """
    TRACE = "trace"   # Severity: 1  (OpenTelemetry)
    DEBUG = "debug"   # Severity: 5  (OpenTelemetry)
    INFO = "info"     # Severity: 9  (OpenTelemetry)
    WARN = "warn"     # Severity: 13 (OpenTelemetry)
    ERROR = "error"   # Severity: 17 (OpenTelemetry)
    FATAL = "fatal"   # Severity: 21 (OpenTelemetry)
