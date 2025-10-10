"""
Sovdev Logger - Log Levels

Standard log levels following "Loggeloven av 2025" requirements.
ERROR and FATAL levels trigger ServiceNow incidents.
"""

from typing import Any, Final


class _LogLevels:
    """Log level constants for sovdev-logger"""

    __slots__ = ()

    TRACE: Final[str] = 'TRACE'    # Detailed trace information (very verbose)
    DEBUG: Final[str] = 'DEBUG'    # Debug information for development
    INFO: Final[str] = 'INFO'      # Informational messages
    WARN: Final[str] = 'WARN'      # Warning messages (potential issues)
    ERROR: Final[str] = 'ERROR'    # Error messages (triggers ServiceNow incident)
    FATAL: Final[str] = 'FATAL'    # Fatal errors (triggers ServiceNow incident)

    def __setattr__(self, name: str, value: Any) -> None:
        """Prevent attribute modification to ensure immutability."""
        raise AttributeError(f"Cannot modify log level constant '{name}'")

    def __repr__(self) -> str:
        """Return string representation for debugging."""
        return "SOVDEV_LOGLEVELS(TRACE, DEBUG, INFO, WARN, ERROR, FATAL)"


# Singleton instance - matches TypeScript const object pattern
SOVDEV_LOGLEVELS = _LogLevels()
