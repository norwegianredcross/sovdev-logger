"""
Sovdev Logger - File Handler Module

Provides file logging with rotation for main logs and error-only logs.
"""

import json
import logging
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional


def _ensure_log_directory(log_path: Path) -> None:
    """
    Ensure log directory exists, create if needed.

    Args:
        log_path: Path to log directory
    """
    if not log_path.exists():
        log_path.mkdir(parents=True, exist_ok=True)


def create_file_handler(
    log_file_path: Path,
    max_bytes: int = 52428800,  # 50MB
    backup_count: int = 5,
    level: int = logging.NOTSET
) -> RotatingFileHandler:
    """
    Create a RotatingFileHandler for file logging.

    Args:
        log_file_path: Full path to log file
        max_bytes: Maximum bytes per file before rotation (default: 50MB)
        backup_count: Number of backup files to keep (default: 5)
        level: Logging level filter (default: NOTSET = all levels)

    Returns:
        Configured RotatingFileHandler
    """
    # Ensure directory exists
    _ensure_log_directory(log_file_path.parent)

    # Create rotating file handler
    handler = RotatingFileHandler(
        filename=str(log_file_path),
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )

    # Set level filter
    handler.setLevel(level)

    # Use JSON formatter
    handler.setFormatter(JsonFormatter())

    return handler


def create_main_log_handler(
    log_dir: Path,
    max_bytes: int = 52428800,
    backup_count: int = 5
) -> RotatingFileHandler:
    """
    Create main log file handler (all log levels).

    Args:
        log_dir: Directory for log files
        max_bytes: Maximum bytes per file before rotation (default: 50MB)
        backup_count: Number of backup files to keep (default: 5)

    Returns:
        Configured handler for dev.log
    """
    log_file = log_dir / 'dev.log'
    return create_file_handler(log_file, max_bytes, backup_count, logging.NOTSET)


def create_error_log_handler(
    log_dir: Path,
    max_bytes: int = 52428800,
    backup_count: int = 5
) -> RotatingFileHandler:
    """
    Create error log file handler (ERROR and FATAL only).

    Args:
        log_dir: Directory for log files
        max_bytes: Maximum bytes per file before rotation (default: 50MB)
        backup_count: Number of backup files to keep (default: 5)

    Returns:
        Configured handler for error.log (ERROR level and above)
    """
    log_file = log_dir / 'error.log'
    return create_file_handler(log_file, max_bytes, backup_count, logging.ERROR)


class JsonFormatter(logging.Formatter):
    """
    JSON formatter for structured log output to files.

    Formats log records as single-line JSON for easy parsing.
    """

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON string.

        Args:
            record: Log record to format

        Returns:
            JSON string representation
        """
        # Get the message (already a dict from sovdev_log)
        if hasattr(record, 'sovdev_data'):
            # Use the structured data directly
            log_data = record.sovdev_data
        else:
            # Fallback for standard logging
            log_data = {
                'timestamp': self.formatTime(record, self.datefmt),
                'level': record.levelname,
                'message': record.getMessage(),
                'logger': record.name,
            }

            if record.exc_info:
                log_data['exception'] = self.formatException(record.exc_info)

        return json.dumps(log_data, ensure_ascii=False)


def write_log_to_file(
    log_entry: dict,
    log_dir: Path,
    max_bytes: int = 52428800,
    backup_count: int = 5
) -> None:
    """
    Write a log entry to file(s) directly.

    This is a convenience function for writing structured log entries
    without using the full logging infrastructure.

    Args:
        log_entry: Structured log entry dictionary
        log_dir: Directory for log files
        max_bytes: Maximum bytes per file before rotation
        backup_count: Number of backup files to keep
    """
    # Ensure directory exists
    _ensure_log_directory(log_dir)

    # Write to main log
    main_log_file = log_dir / 'dev.log'
    _append_json_to_file(log_entry, main_log_file)

    # Write to error log if ERROR or FATAL
    level = log_entry.get('level', '')
    if level in ('ERROR', 'FATAL'):
        error_log_file = log_dir / 'error.log'
        _append_json_to_file(log_entry, error_log_file)


def _append_json_to_file(data: dict, file_path: Path) -> None:
    """
    Append JSON data as a single line to file.

    Args:
        data: Dictionary to write as JSON
        file_path: Path to file
    """
    with open(file_path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(data, ensure_ascii=False))
        f.write('\n')


# Logging level mapping from sovdev levels to Python logging levels
LEVEL_MAP = {
    'TRACE': logging.DEBUG,      # Python has no TRACE, map to DEBUG
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARN': logging.WARNING,
    'ERROR': logging.ERROR,
    'FATAL': logging.CRITICAL,
}


def get_python_log_level(sovdev_level: str) -> int:
    """
    Convert sovdev log level to Python logging level.

    Args:
        sovdev_level: Sovdev log level (TRACE, DEBUG, INFO, WARN, ERROR, FATAL)

    Returns:
        Python logging level constant
    """
    return LEVEL_MAP.get(sovdev_level, logging.INFO)
