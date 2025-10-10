"""
Integration Tests: Basic Logging

End-to-end tests for initialization and basic logging functionality.
"""

import pytest
import json
import sys
from io import StringIO
from sovdev_logger import sovdev_initialize, sovdev_log, SOVDEV_LOGLEVELS, create_peer_services
from sovdev_logger.logger import _global_state


class TestBasicLogging:
    """Integration tests for basic logging functionality"""

    def setup_method(self):
        """Reset state before each test"""
        _global_state.reset()

    def teardown_method(self):
        """Reset state after each test"""
        _global_state.reset()

    def test_end_to_end_basic_logging(self, capsys, monkeypatch):
        """Complete flow: initialize -> log -> verify output"""
        # Enable console output for testing
        monkeypatch.setenv('LOG_TO_CONSOLE', 'true')
        monkeypatch.setenv('LOG_TO_FILE', 'false')

        # Initialize
        PEER_SERVICES = create_peer_services({'API': 'SYS123'})
        sovdev_initialize('test-service', '1.0.0', PEER_SERVICES.mappings)

        # Log
        sovdev_log(
            SOVDEV_LOGLEVELS.INFO,
            'test_function',
            'Test message',
            PEER_SERVICES.INTERNAL
        )

        # Capture stderr output
        captured = capsys.readouterr()
        log_output = captured.err.strip()

        # Parse JSON
        log_entry = json.loads(log_output)

        # Verify structure
        assert log_entry['level'] == 'INFO'
        assert log_entry['message'] == 'Test message'
        assert log_entry['service']['name'] == 'test-service'
        assert log_entry['service']['version'] == '1.0.0'
        assert log_entry['function']['name'] == 'test_function'
        assert log_entry['peer']['service'] == 'test-service'  # INTERNAL resolves to service name

    def test_all_log_levels(self, capsys, monkeypatch):
        """Test all six log levels"""
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

        # Capture output
        captured = capsys.readouterr()
        log_lines = captured.err.strip().split('\n')

        assert len(log_lines) == 6

        # Verify each level
        for i, level in enumerate(levels):
            log_entry = json.loads(log_lines[i])
            assert log_entry['level'] == level
            assert level in log_entry['message']

    def test_peer_service_resolution(self, capsys, monkeypatch):
        """Test peer service name resolution to CMDB ID"""
        monkeypatch.setenv('LOG_TO_CONSOLE', 'true')
        monkeypatch.setenv('LOG_TO_FILE', 'false')

        PEER_SERVICES = create_peer_services({
            'BRREG': 'SYS1234567',
            'ALTINN': 'SYS1005678'
        })
        sovdev_initialize('my-service', '1.0.0', PEER_SERVICES.mappings)

        # Log to external service
        sovdev_log(
            SOVDEV_LOGLEVELS.INFO,
            'fetch_data',
            'Fetched company info',
            PEER_SERVICES.BRREG
        )

        captured = capsys.readouterr()
        log_entry = json.loads(captured.err.strip())

        # Should resolve to CMDB ID
        assert log_entry['peer']['service'] == 'SYS1234567'

    def test_input_and_response_json(self, capsys, monkeypatch):
        """Test logging with input and response data"""
        monkeypatch.setenv('LOG_TO_CONSOLE', 'true')
        monkeypatch.setenv('LOG_TO_FILE', 'false')

        PEER_SERVICES = create_peer_services({})
        sovdev_initialize('test', '1.0.0')

        input_data = {'org_number': '123456789'}
        response_data = {'name': 'Test Company AS', 'status': 'active'}

        sovdev_log(
            SOVDEV_LOGLEVELS.INFO,
            'get_company',
            'Retrieved company',
            PEER_SERVICES.INTERNAL,
            input_json=input_data,
            response_json=response_data
        )

        captured = capsys.readouterr()
        log_entry = json.loads(captured.err.strip())

        assert log_entry['input'] == input_data
        assert log_entry['response'] == response_data

    def test_exception_logging(self, capsys, monkeypatch):
        """Test logging with exception object"""
        monkeypatch.setenv('LOG_TO_CONSOLE', 'true')
        monkeypatch.setenv('LOG_TO_FILE', 'false')

        PEER_SERVICES = create_peer_services({})
        sovdev_initialize('test', '1.0.0')

        try:
            raise ValueError("Test error message")
        except ValueError as e:
            sovdev_log(
                SOVDEV_LOGLEVELS.ERROR,
                'process_data',
                'Processing failed',
                PEER_SERVICES.INTERNAL,
                exception_object=e
            )

        captured = capsys.readouterr()
        log_entry = json.loads(captured.err.strip())

        assert 'exception' in log_entry
        assert log_entry['exception']['type'] == 'ValueError'
        assert log_entry['exception']['message'] == 'Test error message'
        assert 'stackTrace' in log_entry['exception']

    def test_exception_with_sensitive_data_redacted(self, capsys, monkeypatch):
        """Test that sensitive data in exceptions is redacted"""
        monkeypatch.setenv('LOG_TO_CONSOLE', 'true')
        monkeypatch.setenv('LOG_TO_FILE', 'false')

        PEER_SERVICES = create_peer_services({})
        sovdev_initialize('test', '1.0.0')

        try:
            raise ValueError("Authentication failed: password=secret123")
        except ValueError as e:
            sovdev_log(
                SOVDEV_LOGLEVELS.ERROR,
                'authenticate',
                'Auth failed',
                PEER_SERVICES.INTERNAL,
                exception_object=e
            )

        captured = capsys.readouterr()
        log_entry = json.loads(captured.err.strip())

        # Should be redacted
        assert log_entry['exception']['message'] == '[REDACTED - Contains sensitive data]'

    def test_custom_trace_id(self, capsys, monkeypatch):
        """Test providing custom trace ID"""
        monkeypatch.setenv('LOG_TO_CONSOLE', 'true')
        monkeypatch.setenv('LOG_TO_FILE', 'false')

        PEER_SERVICES = create_peer_services({})
        sovdev_initialize('test', '1.0.0')

        custom_trace_id = 'custom-trace-12345'

        sovdev_log(
            SOVDEV_LOGLEVELS.INFO,
            'test',
            'Message',
            PEER_SERVICES.INTERNAL,
            trace_id=custom_trace_id
        )

        captured = capsys.readouterr()
        log_entry = json.loads(captured.err.strip())

        assert log_entry['trace']['id'] == custom_trace_id

    def test_session_id_consistent_across_logs(self, capsys, monkeypatch):
        """Test that session ID remains constant across multiple logs"""
        monkeypatch.setenv('LOG_TO_CONSOLE', 'true')
        monkeypatch.setenv('LOG_TO_FILE', 'false')

        PEER_SERVICES = create_peer_services({})
        sovdev_initialize('test', '1.0.0')

        # Log twice
        sovdev_log(SOVDEV_LOGLEVELS.INFO, 'test', 'Message 1', PEER_SERVICES.INTERNAL)
        sovdev_log(SOVDEV_LOGLEVELS.INFO, 'test', 'Message 2', PEER_SERVICES.INTERNAL)

        captured = capsys.readouterr()
        log_lines = captured.err.strip().split('\n')

        log1 = json.loads(log_lines[0])
        log2 = json.loads(log_lines[1])

        # Session ID should be same
        assert log1['session']['id'] == log2['session']['id']

    def test_event_id_unique_per_log(self, capsys, monkeypatch):
        """Test that event ID is unique for each log entry"""
        monkeypatch.setenv('LOG_TO_CONSOLE', 'true')
        monkeypatch.setenv('LOG_TO_FILE', 'false')

        PEER_SERVICES = create_peer_services({})
        sovdev_initialize('test', '1.0.0')

        # Log twice
        sovdev_log(SOVDEV_LOGLEVELS.INFO, 'test', 'Message 1', PEER_SERVICES.INTERNAL)
        sovdev_log(SOVDEV_LOGLEVELS.INFO, 'test', 'Message 2', PEER_SERVICES.INTERNAL)

        captured = capsys.readouterr()
        log_lines = captured.err.strip().split('\n')

        log1 = json.loads(log_lines[0])
        log2 = json.loads(log_lines[1])

        # Event IDs should be different
        assert log1['event']['id'] != log2['event']['id']

    def test_logging_without_initialization_raises(self):
        """Test that logging without initialization raises error"""
        PEER_SERVICES = create_peer_services({})

        with pytest.raises(RuntimeError, match="Sovdev Logger not initialized"):
            sovdev_log(
                SOVDEV_LOGLEVELS.INFO,
                'test',
                'Message',
                PEER_SERVICES.INTERNAL
            )

    def test_unknown_peer_service_warning(self, capsys, monkeypatch):
        """Test warning when using unknown peer service"""
        monkeypatch.setenv('LOG_TO_CONSOLE', 'true')
        monkeypatch.setenv('LOG_TO_FILE', 'false')

        PEER_SERVICES = create_peer_services({'API': 'SYS123'})
        sovdev_initialize('test', '1.0.0', PEER_SERVICES.mappings)

        # Use unknown peer service
        sovdev_log(
            SOVDEV_LOGLEVELS.INFO,
            'test',
            'Message',
            'UNKNOWN_SERVICE'
        )

        captured = capsys.readouterr()

        # Should have warning in stderr
        assert 'Warning: Unknown peer service' in captured.err
        assert 'UNKNOWN_SERVICE' in captured.err

        # But logging should still work (use as-is)
        log_lines = [line for line in captured.err.split('\n') if line.startswith('{')]
        log_entry = json.loads(log_lines[0])
        assert log_entry['peer']['service'] == 'UNKNOWN_SERVICE'

    def test_timestamp_format(self, capsys, monkeypatch):
        """Test that timestamp is in ISO 8601 format with timezone"""
        monkeypatch.setenv('LOG_TO_CONSOLE', 'true')
        monkeypatch.setenv('LOG_TO_FILE', 'false')

        PEER_SERVICES = create_peer_services({})
        sovdev_initialize('test', '1.0.0')

        sovdev_log(SOVDEV_LOGLEVELS.INFO, 'test', 'Message', PEER_SERVICES.INTERNAL)

        captured = capsys.readouterr()
        log_entry = json.loads(captured.err.strip())

        # Verify ISO 8601 format with timezone
        timestamp = log_entry['timestamp']
        assert '+' in timestamp or 'Z' in timestamp  # Has timezone
        assert 'T' in timestamp  # ISO 8601 separator

        # Verify parseable
        from datetime import datetime
        parsed = datetime.fromisoformat(timestamp)
        assert parsed is not None

    def test_complex_input_json(self, capsys, monkeypatch):
        """Test logging with complex nested JSON structures"""
        monkeypatch.setenv('LOG_TO_CONSOLE', 'true')
        monkeypatch.setenv('LOG_TO_FILE', 'false')

        PEER_SERVICES = create_peer_services({})
        sovdev_initialize('test', '1.0.0')

        complex_input = {
            'user': {
                'id': 123,
                'name': 'Test User',
                'roles': ['admin', 'user']
            },
            'request': {
                'method': 'POST',
                'params': {'filter': 'active', 'limit': 100}
            }
        }

        sovdev_log(
            SOVDEV_LOGLEVELS.INFO,
            'test',
            'Message',
            PEER_SERVICES.INTERNAL,
            input_json=complex_input
        )

        captured = capsys.readouterr()
        log_entry = json.loads(captured.err.strip())

        assert log_entry['input'] == complex_input
        assert log_entry['input']['user']['roles'] == ['admin', 'user']
