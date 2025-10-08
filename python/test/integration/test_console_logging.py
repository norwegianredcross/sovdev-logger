"""
Integration Tests: Console Logging

Tests console logging with config-based enabling and smart defaults.
"""

import pytest
import json
from sovdev_logger import sovdev_initialize, sovdev_log, SOVDEV_LOGLEVELS, create_peer_services
from sovdev_logger.logger import _global_state


class TestConsoleLogging:
    """Test console logging functionality"""

    def setup_method(self):
        """Reset state before each test"""
        _global_state.reset()

    def teardown_method(self):
        """Reset state after each test"""
        _global_state.reset()

    def test_console_logging_when_enabled(self, capsys, monkeypatch):
        """Should output to console when LOG_TO_CONSOLE=true"""
        monkeypatch.setenv('LOG_TO_CONSOLE', 'true')
        monkeypatch.setenv('LOG_TO_FILE', 'false')

        PEER_SERVICES = create_peer_services({})
        sovdev_initialize('test-service', '1.0.0')

        sovdev_log(
            SOVDEV_LOGLEVELS.INFO,
            'test_function',
            'Test message',
            PEER_SERVICES.INTERNAL
        )

        captured = capsys.readouterr()
        log_entry = json.loads(captured.err.strip())
        assert log_entry['level'] == 'INFO'
        assert log_entry['message'] == 'Test message'

    def test_console_disabled_when_explicit_false(self, capsys, monkeypatch):
        """Should NOT output to console when LOG_TO_CONSOLE=false"""
        monkeypatch.setenv('LOG_TO_CONSOLE', 'false')
        monkeypatch.setenv('LOG_TO_FILE', 'false')

        PEER_SERVICES = create_peer_services({})
        sovdev_initialize('test', '1.0.0')

        sovdev_log(SOVDEV_LOGLEVELS.INFO, 'test', 'Message', PEER_SERVICES.INTERNAL)

        captured = capsys.readouterr()
        assert captured.err == '' or 'Warning: All log transports disabled' in captured.err

    def test_console_auto_enabled_without_otlp(self, capsys, monkeypatch):
        """Should auto-enable console when no OTLP endpoint (smart default)"""
        # No LOG_TO_CONSOLE set, no OTLP endpoint
        monkeypatch.delenv('LOG_TO_CONSOLE', raising=False)
        monkeypatch.delenv('OTEL_EXPORTER_OTLP_ENDPOINT', raising=False)
        monkeypatch.delenv('OTEL_EXPORTER_OTLP_LOGS_ENDPOINT', raising=False)
        monkeypatch.setenv('LOG_TO_FILE', 'false')

        PEER_SERVICES = create_peer_services({})
        sovdev_initialize('test', '1.0.0')

        sovdev_log(SOVDEV_LOGLEVELS.INFO, 'test', 'Auto-enabled', PEER_SERVICES.INTERNAL)

        captured = capsys.readouterr()
        log_entry = json.loads(captured.err.strip())
        assert log_entry['message'] == 'Auto-enabled'

    def test_console_auto_disabled_with_otlp(self, capsys, monkeypatch):
        """Should auto-disable console when OTLP endpoint configured (smart default)"""
        monkeypatch.delenv('LOG_TO_CONSOLE', raising=False)
        monkeypatch.setenv('OTEL_EXPORTER_OTLP_LOGS_ENDPOINT', 'http://localhost:4318/v1/logs')
        monkeypatch.setenv('LOG_TO_FILE', 'false')

        PEER_SERVICES = create_peer_services({})
        sovdev_initialize('test', '1.0.0')

        sovdev_log(SOVDEV_LOGLEVELS.INFO, 'test', 'Should not appear', PEER_SERVICES.INTERNAL)

        captured = capsys.readouterr()
        # Should NOT have log output (console disabled due to OTLP)
        # Warning about all transports disabled is expected (no file, console auto-disabled, OTLP not implemented yet)
        assert '"message":"Should not appear"' not in captured.err

    def test_explicit_console_overrides_otlp_smart_default(self, capsys, monkeypatch):
        """Explicit LOG_TO_CONSOLE=true should override OTLP smart default"""
        monkeypatch.setenv('LOG_TO_CONSOLE', 'true')  # Explicit
        monkeypatch.setenv('OTEL_EXPORTER_OTLP_LOGS_ENDPOINT', 'http://localhost:4318/v1/logs')
        monkeypatch.setenv('LOG_TO_FILE', 'false')

        PEER_SERVICES = create_peer_services({})
        sovdev_initialize('test', '1.0.0')

        sovdev_log(SOVDEV_LOGLEVELS.INFO, 'test', 'Explicit wins', PEER_SERVICES.INTERNAL)

        captured = capsys.readouterr()
        log_entry = json.loads(captured.err.strip())
        assert log_entry['message'] == 'Explicit wins'

    def test_all_log_levels_to_console(self, capsys, monkeypatch):
        """Should output all 6 log levels to console"""
        monkeypatch.setenv('LOG_TO_CONSOLE', 'true')
        monkeypatch.setenv('LOG_TO_FILE', 'false')

        PEER_SERVICES = create_peer_services({})
        sovdev_initialize('test', '1.0.0')

        levels = [
            SOVDEV_LOGLEVELS.TRACE,
            SOVDEV_LOGLEVELS.DEBUG,
            SOVDEV_LOGLEVELS.INFO,
            SOVDEV_LOGLEVELS.WARN,
            SOVDEV_LOGLEVELS.ERROR,
            SOVDEV_LOGLEVELS.FATAL
        ]

        for level in levels:
            sovdev_log(level, 'test', f'{level} message', PEER_SERVICES.INTERNAL)

        captured = capsys.readouterr()
        log_lines = captured.err.strip().split('\n')
        assert len(log_lines) == 6

        for i, level in enumerate(levels):
            log_entry = json.loads(log_lines[i])
            assert log_entry['level'] == level

    def test_json_structure_in_console_output(self, capsys, monkeypatch):
        """Should output proper JSON structure to console"""
        monkeypatch.setenv('LOG_TO_CONSOLE', 'true')
        monkeypatch.setenv('LOG_TO_FILE', 'false')

        PEER_SERVICES = create_peer_services({'API': 'SYS123'})
        sovdev_initialize('my-service', '2.0.0', PEER_SERVICES.mappings)

        sovdev_log(
            SOVDEV_LOGLEVELS.INFO,
            'process_data',
            'Processing complete',
            PEER_SERVICES.API,
            input_json={'id': 123},
            response_json={'status': 'ok'}
        )

        captured = capsys.readouterr()
        log_entry = json.loads(captured.err.strip())

        # Verify structure
        assert log_entry['service']['name'] == 'my-service'
        assert log_entry['service']['version'] == '2.0.0'
        assert log_entry['function']['name'] == 'process_data'
        assert log_entry['input'] == {'id': 123}
        assert log_entry['response'] == {'status': 'ok'}
        assert log_entry['peer']['service'] == 'SYS123'

    def test_unicode_in_console_output(self, capsys, monkeypatch):
        """Should handle Unicode characters in console output"""
        monkeypatch.setenv('LOG_TO_CONSOLE', 'true')
        monkeypatch.setenv('LOG_TO_FILE', 'false')

        PEER_SERVICES = create_peer_services({})
        sovdev_initialize('test', '1.0.0')

        sovdev_log(
            SOVDEV_LOGLEVELS.INFO,
            'test',
            'Test with emoji 🚀 and Norwegian æøå',
            PEER_SERVICES.INTERNAL
        )

        captured = capsys.readouterr()
        log_entry = json.loads(captured.err.strip())
        assert '🚀' in log_entry['message']
        assert 'æøå' in log_entry['message']

    def test_exception_in_console_output(self, capsys, monkeypatch):
        """Should include exception details in console output"""
        monkeypatch.setenv('LOG_TO_CONSOLE', 'true')
        monkeypatch.setenv('LOG_TO_FILE', 'false')

        PEER_SERVICES = create_peer_services({})
        sovdev_initialize('test', '1.0.0')

        try:
            raise ValueError("Test error")
        except ValueError as e:
            sovdev_log(
                SOVDEV_LOGLEVELS.ERROR,
                'test',
                'Error occurred',
                PEER_SERVICES.INTERNAL,
                exception_object=e
            )

        captured = capsys.readouterr()
        log_entry = json.loads(captured.err.strip())

        assert 'exception' in log_entry
        assert log_entry['exception']['type'] == 'ValueError'
        assert log_entry['exception']['message'] == 'Test error'


class TestConsoleOutputFormat:
    """Test console output formatting"""

    def setup_method(self):
        """Reset state before each test"""
        _global_state.reset()

    def teardown_method(self):
        """Reset state after each test"""
        _global_state.reset()

    def test_output_is_valid_json(self, capsys, monkeypatch):
        """Console output should be valid JSON"""
        monkeypatch.setenv('LOG_TO_CONSOLE', 'true')
        monkeypatch.setenv('LOG_TO_FILE', 'false')

        PEER_SERVICES = create_peer_services({})
        sovdev_initialize('test', '1.0.0')

        sovdev_log(SOVDEV_LOGLEVELS.INFO, 'test', 'Message', PEER_SERVICES.INTERNAL)

        captured = capsys.readouterr()
        # Should not raise exception
        log_entry = json.loads(captured.err.strip())
        assert log_entry is not None

    def test_output_goes_to_stderr(self, capsys, monkeypatch):
        """Console output should go to stderr, not stdout"""
        monkeypatch.setenv('LOG_TO_CONSOLE', 'true')
        monkeypatch.setenv('LOG_TO_FILE', 'false')

        PEER_SERVICES = create_peer_services({})
        sovdev_initialize('test', '1.0.0')

        sovdev_log(SOVDEV_LOGLEVELS.INFO, 'test', 'Message', PEER_SERVICES.INTERNAL)

        captured = capsys.readouterr()
        # Stderr should have content
        assert len(captured.err) > 0
        # Stdout should be empty
        assert captured.out == ''

    def test_single_line_per_log_entry(self, capsys, monkeypatch):
        """Each log entry should be a single line"""
        monkeypatch.setenv('LOG_TO_CONSOLE', 'true')
        monkeypatch.setenv('LOG_TO_FILE', 'false')

        PEER_SERVICES = create_peer_services({})
        sovdev_initialize('test', '1.0.0')

        sovdev_log(SOVDEV_LOGLEVELS.INFO, 'test', 'Message 1', PEER_SERVICES.INTERNAL)
        sovdev_log(SOVDEV_LOGLEVELS.INFO, 'test', 'Message 2', PEER_SERVICES.INTERNAL)

        captured = capsys.readouterr()
        lines = captured.err.strip().split('\n')
        assert len(lines) == 2

        # Each line should be valid JSON
        for line in lines:
            json.loads(line)


class TestSmartDefaults:
    """Test smart default behavior"""

    def setup_method(self):
        """Reset state before each test"""
        _global_state.reset()

    def teardown_method(self):
        """Reset state after each test"""
        _global_state.reset()

    def test_smart_default_without_config(self, capsys, monkeypatch):
        """Should auto-enable console when no config provided"""
        # Clear all env vars
        for var in ['LOG_TO_CONSOLE', 'LOG_TO_FILE', 'OTEL_EXPORTER_OTLP_ENDPOINT',
                    'OTEL_EXPORTER_OTLP_LOGS_ENDPOINT']:
            monkeypatch.delenv(var, raising=False)

        PEER_SERVICES = create_peer_services({})
        sovdev_initialize('test', '1.0.0')

        sovdev_log(SOVDEV_LOGLEVELS.INFO, 'test', 'Default behavior', PEER_SERVICES.INTERNAL)

        captured = capsys.readouterr()
        # Should have console output (smart default)
        log_entry = json.loads(captured.err.strip())
        assert log_entry['message'] == 'Default behavior'
