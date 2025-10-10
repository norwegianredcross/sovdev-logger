"""
Integration Tests: File Logging

Tests file logging handlers and rotation configuration.
"""

import pytest
import json
from pathlib import Path
from sovdev_logger.file_handler import (
    create_main_log_handler,
    create_error_log_handler,
    write_log_to_file,
    _ensure_log_directory,
)


class TestFileHandlerCreation:
    """Test file handler creation and configuration"""

    def test_create_main_log_handler(self, tmp_path):
        """Should create main log handler for all levels"""
        handler = create_main_log_handler(tmp_path)

        assert handler is not None
        assert handler.level == 0  # NOTSET = all levels
        assert handler.maxBytes == 52428800  # 50MB
        assert handler.backupCount == 5
        assert str(tmp_path / 'dev.log') in handler.baseFilename

    def test_create_error_log_handler(self, tmp_path):
        """Should create error log handler for ERROR+ only"""
        import logging
        handler = create_error_log_handler(tmp_path)

        assert handler is not None
        assert handler.level == logging.ERROR
        assert handler.maxBytes == 52428800
        assert handler.backupCount == 5
        assert str(tmp_path / 'error.log') in handler.baseFilename

    def test_custom_max_bytes(self, tmp_path):
        """Should accept custom max bytes"""
        handler = create_main_log_handler(tmp_path, max_bytes=104857600)  # 100MB

        assert handler.maxBytes == 104857600

    def test_custom_backup_count(self, tmp_path):
        """Should accept custom backup count"""
        handler = create_main_log_handler(tmp_path, backup_count=10)

        assert handler.backupCount == 10

    def test_creates_log_directory(self, tmp_path):
        """Should create log directory if it doesn't exist"""
        nested_dir = tmp_path / 'logs' / 'nested'
        assert not nested_dir.exists()

        handler = create_main_log_handler(nested_dir)

        assert nested_dir.exists()
        assert (nested_dir / 'dev.log').exists()


class TestDirectFileWriting:
    """Test direct file writing functionality"""

    def test_write_log_to_file_creates_main_log(self, tmp_path):
        """Should write to dev.log"""
        log_entry = {
            'timestamp': '2025-01-01T12:00:00Z',
            'level': 'INFO',
            'message': 'Test message',
            'service': {'name': 'test-service'}
        }

        write_log_to_file(log_entry, tmp_path)

        main_log = tmp_path / 'dev.log'
        assert main_log.exists()

        with open(main_log) as f:
            line = f.readline()
            logged = json.loads(line)
            assert logged['message'] == 'Test message'
            assert logged['level'] == 'INFO'

    def test_write_error_to_both_files(self, tmp_path):
        """Should write ERROR to both dev.log and error.log"""
        log_entry = {
            'timestamp': '2025-01-01T12:00:00Z',
            'level': 'ERROR',
            'message': 'Error message',
            'service': {'name': 'test-service'}
        }

        write_log_to_file(log_entry, tmp_path)

        # Check dev.log
        main_log = tmp_path / 'dev.log'
        assert main_log.exists()
        with open(main_log) as f:
            logged = json.loads(f.readline())
            assert logged['level'] == 'ERROR'

        # Check error.log
        error_log = tmp_path / 'error.log'
        assert error_log.exists()
        with open(error_log) as f:
            logged = json.loads(f.readline())
            assert logged['level'] == 'ERROR'

    def test_write_fatal_to_both_files(self, tmp_path):
        """Should write FATAL to both dev.log and error.log"""
        log_entry = {
            'timestamp': '2025-01-01T12:00:00Z',
            'level': 'FATAL',
            'message': 'Fatal error',
            'service': {'name': 'test-service'}
        }

        write_log_to_file(log_entry, tmp_path)

        # Check both files exist and contain the entry
        assert (tmp_path / 'dev.log').exists()
        assert (tmp_path / 'error.log').exists()

        with open(tmp_path / 'error.log') as f:
            logged = json.loads(f.readline())
            assert logged['level'] == 'FATAL'

    def test_write_info_only_to_main_log(self, tmp_path):
        """Should write INFO only to dev.log, not error.log"""
        log_entry = {
            'timestamp': '2025-01-01T12:00:00Z',
            'level': 'INFO',
            'message': 'Info message',
        }

        write_log_to_file(log_entry, tmp_path)

        assert (tmp_path / 'dev.log').exists()
        assert not (tmp_path / 'error.log').exists()

    def test_write_multiple_entries(self, tmp_path):
        """Should append multiple entries to same file"""
        entries = [
            {'level': 'INFO', 'message': 'Message 1'},
            {'level': 'DEBUG', 'message': 'Message 2'},
            {'level': 'INFO', 'message': 'Message 3'},
        ]

        for entry in entries:
            write_log_to_file(entry, tmp_path)

        main_log = tmp_path / 'dev.log'
        with open(main_log) as f:
            lines = f.readlines()
            assert len(lines) == 3
            assert json.loads(lines[0])['message'] == 'Message 1'
            assert json.loads(lines[1])['message'] == 'Message 2'
            assert json.loads(lines[2])['message'] == 'Message 3'

    def test_json_formatting_preserves_structure(self, tmp_path):
        """Should preserve complex nested JSON structure"""
        log_entry = {
            'timestamp': '2025-01-01T12:00:00Z',
            'level': 'INFO',
            'message': 'Complex entry',
            'service': {
                'name': 'test-service',
                'version': '1.0.0'
            },
            'input': {
                'user': {'id': 123, 'roles': ['admin', 'user']},
                'request': {'method': 'POST'}
            }
        }

        write_log_to_file(log_entry, tmp_path)

        with open(tmp_path / 'dev.log') as f:
            logged = json.loads(f.readline())
            assert logged['input']['user']['roles'] == ['admin', 'user']
            assert logged['service']['version'] == '1.0.0'


class TestDirectoryCreation:
    """Test automatic directory creation"""

    def test_ensure_log_directory_creates_nested(self, tmp_path):
        """Should create nested directory structure"""
        nested = tmp_path / 'a' / 'b' / 'c'
        assert not nested.exists()

        _ensure_log_directory(nested)

        assert nested.exists()
        assert nested.is_dir()

    def test_ensure_log_directory_idempotent(self, tmp_path):
        """Should be safe to call multiple times"""
        log_dir = tmp_path / 'logs'

        _ensure_log_directory(log_dir)
        assert log_dir.exists()

        # Call again - should not error
        _ensure_log_directory(log_dir)
        assert log_dir.exists()


class TestErrorLogFiltering:
    """Test that error.log only contains ERROR and FATAL"""

    def test_error_log_filters_levels(self, tmp_path):
        """Should only write ERROR and FATAL to error.log"""
        entries = [
            {'level': 'TRACE', 'message': 'Trace'},
            {'level': 'DEBUG', 'message': 'Debug'},
            {'level': 'INFO', 'message': 'Info'},
            {'level': 'WARN', 'message': 'Warn'},
            {'level': 'ERROR', 'message': 'Error'},
            {'level': 'FATAL', 'message': 'Fatal'},
        ]

        for entry in entries:
            write_log_to_file(entry, tmp_path)

        # dev.log should have all 6
        with open(tmp_path / 'dev.log') as f:
            lines = f.readlines()
            assert len(lines) == 6

        # error.log should only have 2 (ERROR and FATAL)
        with open(tmp_path / 'error.log') as f:
            lines = f.readlines()
            assert len(lines) == 2
            assert json.loads(lines[0])['level'] == 'ERROR'
            assert json.loads(lines[1])['level'] == 'FATAL'


class TestUnicodeSupport:
    """Test Unicode character support in logs"""

    def test_unicode_characters_in_message(self, tmp_path):
        """Should handle Unicode characters properly"""
        log_entry = {
            'level': 'INFO',
            'message': 'Test with emoji 🚀 and Norwegian æøå',
            'service': {'name': 'test'}
        }

        write_log_to_file(log_entry, tmp_path)

        with open(tmp_path / 'dev.log', encoding='utf-8') as f:
            logged = json.loads(f.readline())
            assert '🚀' in logged['message']
            assert 'æøå' in logged['message']

    def test_unicode_in_nested_objects(self, tmp_path):
        """Should handle Unicode in nested structures"""
        log_entry = {
            'level': 'INFO',
            'message': 'Test',
            'user': {'name': 'Børge Åse', 'city': 'Tromsø'}
        }

        write_log_to_file(log_entry, tmp_path)

        with open(tmp_path / 'dev.log', encoding='utf-8') as f:
            logged = json.loads(f.readline())
            assert logged['user']['name'] == 'Børge Åse'
            assert logged['user']['city'] == 'Tromsø'


class TestFilePermissions:
    """Test file creation permissions and accessibility"""

    def test_log_files_are_writable(self, tmp_path):
        """Created log files should be writable"""
        write_log_to_file({'level': 'INFO', 'message': 'Test'}, tmp_path)

        main_log = tmp_path / 'dev.log'
        assert main_log.exists()
        assert main_log.is_file()

        # Should be able to append
        write_log_to_file({'level': 'INFO', 'message': 'Test 2'}, tmp_path)

        with open(main_log) as f:
            lines = f.readlines()
            assert len(lines) == 2
