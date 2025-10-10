"""
Integration Tests: Multi-Transport Logging

Tests simultaneous logging to multiple transports (console + file).
"""

import pytest
import json
from pathlib import Path
from sovdev_logger import sovdev_initialize, sovdev_log, SOVDEV_LOGLEVELS, create_peer_services
from sovdev_logger.logger import _global_state


class TestMultiTransport:
    """Test logging to multiple transports simultaneously"""

    def setup_method(self):
        """Reset state before each test"""
        _global_state.reset()

    def teardown_method(self):
        """Reset state after each test"""
        _global_state.reset()

    def test_console_and_file_simultaneously(self, capsys, tmp_path, monkeypatch):
        """Should output to both console and file when both enabled"""
        monkeypatch.setenv('LOG_TO_CONSOLE', 'true')
        monkeypatch.setenv('LOG_TO_FILE', 'true')
        monkeypatch.setenv('LOG_FILE_PATH', str(tmp_path))

        PEER_SERVICES = create_peer_services({})
        sovdev_initialize('test-service', '1.0.0')

        sovdev_log(
            SOVDEV_LOGLEVELS.INFO,
            'test_function',
            'Multi-transport message',
            PEER_SERVICES.INTERNAL
        )

        # Check console output
        captured = capsys.readouterr()
        console_log = json.loads(captured.err.strip())
        assert console_log['message'] == 'Multi-transport message'

        # Check file output
        dev_log = tmp_path / 'dev.log'
        assert dev_log.exists()
        with open(dev_log) as f:
            file_log = json.loads(f.readline())
            assert file_log['message'] == 'Multi-transport message'

        # Both should be identical
        assert console_log == file_log

    def test_error_goes_to_all_transports(self, capsys, tmp_path, monkeypatch):
        """ERROR should go to console, dev.log, and error.log"""
        monkeypatch.setenv('LOG_TO_CONSOLE', 'true')
        monkeypatch.setenv('LOG_TO_FILE', 'true')
        monkeypatch.setenv('LOG_FILE_PATH', str(tmp_path))

        PEER_SERVICES = create_peer_services({})
        sovdev_initialize('test', '1.0.0')

        sovdev_log(
            SOVDEV_LOGLEVELS.ERROR,
            'test',
            'Error message',
            PEER_SERVICES.INTERNAL
        )

        # Check console
        captured = capsys.readouterr()
        console_log = json.loads(captured.err.strip())
        assert console_log['level'] == 'ERROR'

        # Check dev.log
        dev_log = tmp_path / 'dev.log'
        assert dev_log.exists()
        with open(dev_log) as f:
            assert json.loads(f.readline())['level'] == 'ERROR'

        # Check error.log
        error_log = tmp_path / 'error.log'
        assert error_log.exists()
        with open(error_log) as f:
            assert json.loads(f.readline())['level'] == 'ERROR'

    def test_info_not_in_error_log_multi_transport(self, capsys, tmp_path, monkeypatch):
        """INFO should go to console and dev.log but NOT error.log"""
        monkeypatch.setenv('LOG_TO_CONSOLE', 'true')
        monkeypatch.setenv('LOG_TO_FILE', 'true')
        monkeypatch.setenv('LOG_FILE_PATH', str(tmp_path))

        PEER_SERVICES = create_peer_services({})
        sovdev_initialize('test', '1.0.0')

        sovdev_log(SOVDEV_LOGLEVELS.INFO, 'test', 'Info message', PEER_SERVICES.INTERNAL)

        # Console should have it
        captured = capsys.readouterr()
        assert len(captured.err) > 0

        # dev.log should have it
        assert (tmp_path / 'dev.log').exists()

        # error.log should NOT exist
        assert not (tmp_path / 'error.log').exists()

    def test_multiple_entries_to_all_transports(self, capsys, tmp_path, monkeypatch):
        """Multiple log entries should appear in all enabled transports"""
        monkeypatch.setenv('LOG_TO_CONSOLE', 'true')
        monkeypatch.setenv('LOG_TO_FILE', 'true')
        monkeypatch.setenv('LOG_FILE_PATH', str(tmp_path))

        PEER_SERVICES = create_peer_services({})
        sovdev_initialize('test', '1.0.0')

        # Log 3 entries
        sovdev_log(SOVDEV_LOGLEVELS.INFO, 'test', 'Message 1', PEER_SERVICES.INTERNAL)
        sovdev_log(SOVDEV_LOGLEVELS.DEBUG, 'test', 'Message 2', PEER_SERVICES.INTERNAL)
        sovdev_log(SOVDEV_LOGLEVELS.ERROR, 'test', 'Message 3', PEER_SERVICES.INTERNAL)

        # Check console has 3 lines
        captured = capsys.readouterr()
        console_lines = captured.err.strip().split('\n')
        assert len(console_lines) == 3

        # Check dev.log has 3 lines
        with open(tmp_path / 'dev.log') as f:
            file_lines = f.readlines()
            assert len(file_lines) == 3

        # Check error.log has only 1 (ERROR)
        with open(tmp_path / 'error.log') as f:
            error_lines = f.readlines()
            assert len(error_lines) == 1

    def test_console_only_no_file_created(self, capsys, tmp_path, monkeypatch):
        """When only console enabled, should not create files"""
        monkeypatch.setenv('LOG_TO_CONSOLE', 'true')
        monkeypatch.setenv('LOG_TO_FILE', 'false')
        monkeypatch.setenv('LOG_FILE_PATH', str(tmp_path))

        PEER_SERVICES = create_peer_services({})
        sovdev_initialize('test', '1.0.0')

        sovdev_log(SOVDEV_LOGLEVELS.INFO, 'test', 'Console only', PEER_SERVICES.INTERNAL)

        # Console should have output
        captured = capsys.readouterr()
        assert len(captured.err) > 0

        # No log files should be created
        assert not (tmp_path / 'dev.log').exists()
        assert not (tmp_path / 'error.log').exists()

    def test_file_only_no_console_output(self, capsys, tmp_path, monkeypatch):
        """When only file enabled, should not output to console"""
        monkeypatch.setenv('LOG_TO_CONSOLE', 'false')
        monkeypatch.setenv('LOG_TO_FILE', 'true')
        monkeypatch.setenv('LOG_FILE_PATH', str(tmp_path))

        PEER_SERVICES = create_peer_services({})
        sovdev_initialize('test', '1.0.0')

        sovdev_log(SOVDEV_LOGLEVELS.INFO, 'test', 'File only', PEER_SERVICES.INTERNAL)

        # Console should be empty (or only warning)
        captured = capsys.readouterr()
        # Filter out warnings
        non_warning_output = [line for line in captured.err.split('\n') if line and not line.startswith('⚠️')]
        assert len(non_warning_output) == 0

        # File should have content
        assert (tmp_path / 'dev.log').exists()
        with open(tmp_path / 'dev.log') as f:
            log = json.loads(f.readline())
            assert log['message'] == 'File only'


class TestAllTransportsDisabled:
    """Test edge case when all transports are disabled"""

    def setup_method(self):
        """Reset state before each test"""
        _global_state.reset()

    def teardown_method(self):
        """Reset state after each test"""
        _global_state.reset()

    def test_all_disabled_shows_warning(self, capsys, tmp_path, monkeypatch):
        """Should warn user when all transports disabled"""
        monkeypatch.setenv('LOG_TO_CONSOLE', 'false')
        monkeypatch.setenv('LOG_TO_FILE', 'false')
        monkeypatch.delenv('OTEL_EXPORTER_OTLP_ENDPOINT', raising=False)

        PEER_SERVICES = create_peer_services({})
        sovdev_initialize('test', '1.0.0')

        sovdev_log(SOVDEV_LOGLEVELS.INFO, 'test', 'Lost message', PEER_SERVICES.INTERNAL)

        captured = capsys.readouterr()
        # Should have warning about all transports disabled
        assert 'Warning: All log transports disabled' in captured.err

    def test_all_disabled_no_crash(self, capsys, tmp_path, monkeypatch):
        """Should not crash when all transports disabled"""
        monkeypatch.setenv('LOG_TO_CONSOLE', 'false')
        monkeypatch.setenv('LOG_TO_FILE', 'false')
        monkeypatch.delenv('OTEL_EXPORTER_OTLP_ENDPOINT', raising=False)

        PEER_SERVICES = create_peer_services({})
        sovdev_initialize('test', '1.0.0')

        # Should not raise exception
        try:
            sovdev_log(SOVDEV_LOGLEVELS.INFO, 'test', 'Message', PEER_SERVICES.INTERNAL)
        except Exception as e:
            pytest.fail(f"Logging should not crash when all transports disabled: {e}")


class TestTransportConsistency:
    """Test that log entries are consistent across transports"""

    def setup_method(self):
        """Reset state before each test"""
        _global_state.reset()

    def teardown_method(self):
        """Reset state after each test"""
        _global_state.reset()

    def test_same_content_all_transports(self, capsys, tmp_path, monkeypatch):
        """Console and file should have identical log entries"""
        monkeypatch.setenv('LOG_TO_CONSOLE', 'true')
        monkeypatch.setenv('LOG_TO_FILE', 'true')
        monkeypatch.setenv('LOG_FILE_PATH', str(tmp_path))

        PEER_SERVICES = create_peer_services({'API': 'SYS123'})
        sovdev_initialize('my-service', '2.0.0', PEER_SERVICES.mappings)

        sovdev_log(
            SOVDEV_LOGLEVELS.INFO,
            'process',
            'Test message',
            PEER_SERVICES.API,
            input_json={'id': 123},
            response_json={'status': 'ok'}
        )

        # Get console output
        captured = capsys.readouterr()
        console_log = json.loads(captured.err.strip())

        # Get file output
        with open(tmp_path / 'dev.log') as f:
            file_log = json.loads(f.readline())

        # Should be identical
        assert console_log == file_log
        assert console_log['service']['name'] == 'my-service'
        assert console_log['input'] == {'id': 123}
        assert console_log['response'] == {'status': 'ok'}

    def test_same_timestamp_all_transports(self, capsys, tmp_path, monkeypatch):
        """Timestamp should be identical across all transports"""
        monkeypatch.setenv('LOG_TO_CONSOLE', 'true')
        monkeypatch.setenv('LOG_TO_FILE', 'true')
        monkeypatch.setenv('LOG_FILE_PATH', str(tmp_path))

        PEER_SERVICES = create_peer_services({})
        sovdev_initialize('test', '1.0.0')

        sovdev_log(SOVDEV_LOGLEVELS.INFO, 'test', 'Message', PEER_SERVICES.INTERNAL)

        # Get timestamps
        captured = capsys.readouterr()
        console_log = json.loads(captured.err.strip())

        with open(tmp_path / 'dev.log') as f:
            file_log = json.loads(f.readline())

        # Timestamps should be identical (same log entry object)
        assert console_log['timestamp'] == file_log['timestamp']
        assert console_log['event']['id'] == file_log['event']['id']
        assert console_log['trace']['id'] == file_log['trace']['id']


class TestConfigurationReload:
    """Test that configuration changes are respected"""

    def setup_method(self):
        """Reset state before each test"""
        _global_state.reset()

    def teardown_method(self):
        """Reset state after each test"""
        _global_state.reset()

    def test_config_read_per_log_call(self, capsys, tmp_path, monkeypatch):
        """Configuration should be read on each log call (for dynamic changes)"""
        # Note: This test documents current behavior
        # In production, config is typically set once at startup
        monkeypatch.setenv('LOG_TO_CONSOLE', 'true')
        monkeypatch.setenv('LOG_TO_FILE', 'false')

        PEER_SERVICES = create_peer_services({})
        sovdev_initialize('test', '1.0.0')

        sovdev_log(SOVDEV_LOGLEVELS.INFO, 'test', 'First', PEER_SERVICES.INTERNAL)

        # First call should go to console
        captured = capsys.readouterr()
        log1 = json.loads(captured.err.strip())
        assert log1['message'] == 'First'

        # Change config and log again
        # (In real usage, config changes would require app restart)
        # This test just verifies the behavior
        monkeypatch.setenv('LOG_TO_CONSOLE', 'false')
        sovdev_log(SOVDEV_LOGLEVELS.INFO, 'test', 'Second', PEER_SERVICES.INTERNAL)

        captured = capsys.readouterr()
        # Second call should not go to console (config was re-read)
        assert captured.err == '' or 'Warning' in captured.err
