"""
Sovdev Logger - Configuration Module

Handles environment variable parsing and smart defaults for transport configuration.
"""

import os
from pathlib import Path
from typing import Any


def _parse_bool_env(var_name: str, default: bool = False) -> bool:
    """
    Parse boolean environment variable.

    Accepts: 'true', 'false', '1', '0', 'yes', 'no' (case-insensitive)

    Args:
        var_name: Environment variable name
        default: Default value if not set

    Returns:
        Boolean value
    """
    value = os.environ.get(var_name, '').strip().lower()

    if not value:
        return default

    if value in ('true', '1', 'yes'):
        return True
    elif value in ('false', '0', 'no'):
        return False
    else:
        # Invalid value, use default and warn
        import sys
        print(f"⚠️  Warning: Invalid value '{value}' for {var_name}, using default: {default}", file=sys.stderr)
        return default


def _has_otlp_endpoint() -> bool:
    """
    Check if any OTLP endpoint is configured.

    Returns:
        True if at least one OTLP endpoint is set
    """
    endpoints = [
        'OTEL_EXPORTER_OTLP_ENDPOINT',
        'OTEL_EXPORTER_OTLP_LOGS_ENDPOINT',
        'OTEL_EXPORTER_OTLP_METRICS_ENDPOINT',
        'OTEL_EXPORTER_OTLP_TRACES_ENDPOINT',
    ]

    for endpoint in endpoints:
        value = os.environ.get(endpoint, '').strip()
        if value:
            return True

    return False


def get_config() -> dict[str, Any]:
    """
    Get logger configuration from environment variables with smart defaults.

    Environment Variables:
        LOG_TO_CONSOLE: Enable console logging (true/false/auto, default: auto)
        LOG_TO_FILE: Enable file logging (true/false, default: false)
        LOG_FILE_PATH: Directory for log files (default: ./logs/)
        LOG_FILE_MAX_BYTES: Max size per log file (default: 52428800 = 50MB)
        LOG_FILE_BACKUP_COUNT: Number of backup files (default: 5)
        OTEL_EXPORTER_OTLP_*: OTLP endpoint configuration

    Smart Defaults:
        - If LOG_TO_CONSOLE not set and no OTLP endpoint: auto-enable console
        - If LOG_TO_CONSOLE='auto': enable if no OTLP endpoint
        - If all transports disabled: warn user

    Returns:
        Configuration dictionary with keys:
        - console_enabled: bool
        - file_enabled: bool
        - log_file_path: Path
        - log_file_max_bytes: int
        - log_file_backup_count: int
        - has_otlp: bool
    """
    # Check if OTLP is configured
    has_otlp = _has_otlp_endpoint()

    # Parse LOG_TO_CONSOLE with smart defaults
    console_env = os.environ.get('LOG_TO_CONSOLE', 'auto').strip().lower()

    if console_env == 'auto':
        # Auto-enable console if no OTLP endpoint
        console_enabled = not has_otlp
    elif console_env in ('true', '1', 'yes'):
        console_enabled = True
    elif console_env in ('false', '0', 'no'):
        console_enabled = False
    else:
        # Invalid value, use smart default
        import sys
        print(f"⚠️  Warning: Invalid LOG_TO_CONSOLE value '{console_env}', using auto", file=sys.stderr)
        console_enabled = not has_otlp

    # Parse LOG_TO_FILE
    file_enabled = _parse_bool_env('LOG_TO_FILE', default=False)

    # Parse log file path
    log_file_path_str = os.environ.get('LOG_FILE_PATH', './logs/').strip()
    log_file_path = Path(log_file_path_str)

    # Parse log file rotation settings
    try:
        log_file_max_bytes = int(os.environ.get('LOG_FILE_MAX_BYTES', '52428800'))
    except ValueError:
        log_file_max_bytes = 52428800  # 50MB default

    try:
        log_file_backup_count = int(os.environ.get('LOG_FILE_BACKUP_COUNT', '5'))
    except ValueError:
        log_file_backup_count = 5

    # Warn if all transports disabled
    if not console_enabled and not file_enabled and not has_otlp:
        import sys
        print("⚠️  Warning: All log transports disabled (console, file, and OTLP)", file=sys.stderr)

    return {
        'console_enabled': console_enabled,
        'file_enabled': file_enabled,
        'log_file_path': log_file_path,
        'log_file_max_bytes': log_file_max_bytes,
        'log_file_backup_count': log_file_backup_count,
        'has_otlp': has_otlp,
    }


def get_console_enabled() -> bool:
    """Get whether console logging is enabled (convenience function)."""
    return get_config()['console_enabled']


def get_file_enabled() -> bool:
    """Get whether file logging is enabled (convenience function)."""
    return get_config()['file_enabled']


def get_log_file_path() -> Path:
    """Get log file directory path (convenience function)."""
    return get_config()['log_file_path']
