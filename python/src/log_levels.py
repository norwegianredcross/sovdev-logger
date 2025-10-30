"""
Sovdev Logger - Log Levels

Defines log levels matching OpenTelemetry severity numbers.
"""

from enum import Enum
from typing import Union


class SOVDEV_LOGLEVELS(str, Enum):
    """
    Log levels matching OpenTelemetry severity numbers.

    Subclasses str to allow use as string literals.
    """

    TRACE = "trace"  # Severity: 1  (OpenTelemetry)
    DEBUG = "debug"  # Severity: 5  (OpenTelemetry)
    INFO = "info"  # Severity: 9  (OpenTelemetry)
    WARN = "warn"  # Severity: 13 (OpenTelemetry)
    ERROR = "error"  # Severity: 17 (OpenTelemetry)
    FATAL = "fatal"  # Severity: 21 (OpenTelemetry)


# Type alias for log levels (accepts both enum and string)
SovdevLogLevel = Union[SOVDEV_LOGLEVELS, str]
