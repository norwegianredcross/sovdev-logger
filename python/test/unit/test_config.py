"""
Unit Tests: Configuration Module

Tests environment variable parsing and smart defaults logic.
"""

import pytest
from pathlib import Path
from sovdev_logger.config import get_config, get_console_enabled, get_file_enabled, get_log_file_path


class TestConfigParsing:
    """Test configuration environment variable parsing"""

    def test_default_config_no_env_vars(self, monkeypatch):
        """Should use smart defaults when no env vars set"""
        # Clear all relevant env vars
        monkeypatch.delenv('LOG_TO_CONSOLE', raising=False)
        monkeypatch.delenv('LOG_TO_FILE', raising=False)
        monkeypatch.delenv('LOG_FILE_PATH', raising=False)
        monkeypatch.delenv('OTEL_EXPORTER_OTLP_ENDPOINT', raising=False)
        monkeypatch.delenv('OTEL_EXPORTER_OTLP_LOGS_ENDPOINT', raising=False)

        config = get_config()

        # No OTLP = console auto-enabled
        assert config['console_enabled'] is True
        assert config['file_enabled'] is False
        assert config['log_file_path'] == Path('./logs/')
        assert config['log_file_max_bytes'] == 52428800  # 50MB
        assert config['log_file_backup_count'] == 5
        assert config['has_otlp'] is False

    def test_explicit_console_true(self, monkeypatch):
        """Should enable console when LOG_TO_CONSOLE=true"""
        monkeypatch.setenv('LOG_TO_CONSOLE', 'true')
        monkeypatch.delenv('OTEL_EXPORTER_OTLP_ENDPOINT', raising=False)

        config = get_config()
        assert config['console_enabled'] is True

    def test_explicit_console_false(self, monkeypatch):
        """Should disable console when LOG_TO_CONSOLE=false"""
        monkeypatch.setenv('LOG_TO_CONSOLE', 'false')

        config = get_config()
        assert config['console_enabled'] is False

    def test_console_true_variations(self, monkeypatch):
        """Should accept various true values"""
        true_values = ['true', 'True', 'TRUE', '1', 'yes', 'Yes', 'YES']

        for value in true_values:
            monkeypatch.setenv('LOG_TO_CONSOLE', value)
            config = get_config()
            assert config['console_enabled'] is True, f"Failed for value: {value}"

    def test_console_false_variations(self, monkeypatch):
        """Should accept various false values"""
        false_values = ['false', 'False', 'FALSE', '0', 'no', 'No', 'NO']

        for value in false_values:
            monkeypatch.setenv('LOG_TO_CONSOLE', value)
            config = get_config()
            assert config['console_enabled'] is False, f"Failed for value: {value}"

    def test_file_logging_enabled(self, monkeypatch):
        """Should enable file logging when LOG_TO_FILE=true"""
        monkeypatch.setenv('LOG_TO_FILE', 'true')

        config = get_config()
        assert config['file_enabled'] is True

    def test_file_logging_disabled(self, monkeypatch):
        """Should disable file logging when LOG_TO_FILE=false"""
        monkeypatch.setenv('LOG_TO_FILE', 'false')

        config = get_config()
        assert config['file_enabled'] is False

    def test_custom_log_file_path(self, monkeypatch, tmp_path):
        """Should use custom LOG_FILE_PATH"""
        custom_path = str(tmp_path / 'custom-logs')
        monkeypatch.setenv('LOG_FILE_PATH', custom_path)

        config = get_config()
        assert config['log_file_path'] == Path(custom_path)

    def test_custom_file_max_bytes(self, monkeypatch):
        """Should parse LOG_FILE_MAX_BYTES"""
        monkeypatch.setenv('LOG_FILE_MAX_BYTES', '104857600')  # 100MB

        config = get_config()
        assert config['log_file_max_bytes'] == 104857600

    def test_custom_backup_count(self, monkeypatch):
        """Should parse LOG_FILE_BACKUP_COUNT"""
        monkeypatch.setenv('LOG_FILE_BACKUP_COUNT', '10')

        config = get_config()
        assert config['log_file_backup_count'] == 10

    def test_invalid_max_bytes_uses_default(self, monkeypatch):
        """Should use default for invalid LOG_FILE_MAX_BYTES"""
        monkeypatch.setenv('LOG_FILE_MAX_BYTES', 'invalid')

        config = get_config()
        assert config['log_file_max_bytes'] == 52428800  # Default

    def test_invalid_backup_count_uses_default(self, monkeypatch):
        """Should use default for invalid LOG_FILE_BACKUP_COUNT"""
        monkeypatch.setenv('LOG_FILE_BACKUP_COUNT', 'invalid')

        config = get_config()
        assert config['log_file_backup_count'] == 5  # Default

    def test_invalid_console_value_warns(self, monkeypatch, capsys):
        """Should warn on invalid LOG_TO_CONSOLE value and use smart default"""
        monkeypatch.setenv('LOG_TO_CONSOLE', 'invalid')
        monkeypatch.delenv('OTEL_EXPORTER_OTLP_ENDPOINT', raising=False)

        config = get_config()

        captured = capsys.readouterr()
        assert 'Warning' in captured.err
        assert 'invalid' in captured.err
        # Should use smart default (no OTLP = console enabled)
        assert config['console_enabled'] is True

    def test_invalid_file_value_warns(self, monkeypatch, capsys):
        """Should warn on invalid LOG_TO_FILE value and use default"""
        monkeypatch.setenv('LOG_TO_FILE', 'invalid')

        config = get_config()

        captured = capsys.readouterr()
        assert 'Warning' in captured.err
        # Should use default (false)
        assert config['file_enabled'] is False


class TestSmartDefaults:
    """Test smart defaults logic"""

    def test_console_auto_with_otlp_endpoint(self, monkeypatch):
        """Should disable console when OTLP endpoint configured (auto mode)"""
        monkeypatch.setenv('LOG_TO_CONSOLE', 'auto')
        monkeypatch.setenv('OTEL_EXPORTER_OTLP_ENDPOINT', 'http://localhost:4318')

        config = get_config()
        assert config['console_enabled'] is False
        assert config['has_otlp'] is True

    def test_console_auto_without_otlp(self, monkeypatch):
        """Should enable console when no OTLP endpoint (auto mode)"""
        monkeypatch.setenv('LOG_TO_CONSOLE', 'auto')
        monkeypatch.delenv('OTEL_EXPORTER_OTLP_ENDPOINT', raising=False)
        monkeypatch.delenv('OTEL_EXPORTER_OTLP_LOGS_ENDPOINT', raising=False)

        config = get_config()
        assert config['console_enabled'] is True
        assert config['has_otlp'] is False

    def test_console_default_auto_with_otlp(self, monkeypatch):
        """Should default to auto mode and disable console with OTLP"""
        monkeypatch.delenv('LOG_TO_CONSOLE', raising=False)
        monkeypatch.setenv('OTEL_EXPORTER_OTLP_LOGS_ENDPOINT', 'http://localhost:4318/v1/logs')

        config = get_config()
        assert config['console_enabled'] is False
        assert config['has_otlp'] is True

    def test_console_default_auto_without_otlp(self, monkeypatch):
        """Should default to auto mode and enable console without OTLP"""
        monkeypatch.delenv('LOG_TO_CONSOLE', raising=False)
        monkeypatch.delenv('OTEL_EXPORTER_OTLP_ENDPOINT', raising=False)

        config = get_config()
        assert config['console_enabled'] is True
        assert config['has_otlp'] is False

    def test_has_otlp_with_logs_endpoint(self, monkeypatch):
        """Should detect OTEL_EXPORTER_OTLP_LOGS_ENDPOINT"""
        monkeypatch.setenv('OTEL_EXPORTER_OTLP_LOGS_ENDPOINT', 'http://localhost:4318/v1/logs')

        config = get_config()
        assert config['has_otlp'] is True

    def test_has_otlp_with_metrics_endpoint(self, monkeypatch):
        """Should detect OTEL_EXPORTER_OTLP_METRICS_ENDPOINT"""
        monkeypatch.setenv('OTEL_EXPORTER_OTLP_METRICS_ENDPOINT', 'http://localhost:4318/v1/metrics')

        config = get_config()
        assert config['has_otlp'] is True

    def test_has_otlp_with_traces_endpoint(self, monkeypatch):
        """Should detect OTEL_EXPORTER_OTLP_TRACES_ENDPOINT"""
        monkeypatch.setenv('OTEL_EXPORTER_OTLP_TRACES_ENDPOINT', 'http://localhost:4318/v1/traces')

        config = get_config()
        assert config['has_otlp'] is True

    def test_has_otlp_with_generic_endpoint(self, monkeypatch):
        """Should detect OTEL_EXPORTER_OTLP_ENDPOINT"""
        monkeypatch.setenv('OTEL_EXPORTER_OTLP_ENDPOINT', 'http://localhost:4318')

        config = get_config()
        assert config['has_otlp'] is True

    def test_has_otlp_ignores_empty_string(self, monkeypatch):
        """Should ignore empty string OTLP endpoints"""
        monkeypatch.setenv('OTEL_EXPORTER_OTLP_ENDPOINT', '')
        monkeypatch.setenv('OTEL_EXPORTER_OTLP_LOGS_ENDPOINT', '  ')

        config = get_config()
        assert config['has_otlp'] is False

    def test_all_transports_disabled_warning(self, monkeypatch, capsys):
        """Should warn when all transports disabled"""
        monkeypatch.setenv('LOG_TO_CONSOLE', 'false')
        monkeypatch.setenv('LOG_TO_FILE', 'false')
        monkeypatch.delenv('OTEL_EXPORTER_OTLP_ENDPOINT', raising=False)

        config = get_config()

        captured = capsys.readouterr()
        assert 'Warning' in captured.err
        assert 'All log transports disabled' in captured.err

    def test_explicit_console_overrides_otlp(self, monkeypatch):
        """Explicit LOG_TO_CONSOLE=true should override OTLP smart default"""
        monkeypatch.setenv('LOG_TO_CONSOLE', 'true')
        monkeypatch.setenv('OTEL_EXPORTER_OTLP_ENDPOINT', 'http://localhost:4318')

        config = get_config()
        assert config['console_enabled'] is True  # Explicit wins
        assert config['has_otlp'] is True


class TestConvenienceFunctions:
    """Test convenience getter functions"""

    def test_get_console_enabled(self, monkeypatch):
        """Should return console_enabled from config"""
        monkeypatch.setenv('LOG_TO_CONSOLE', 'true')

        assert get_console_enabled() is True

    def test_get_file_enabled(self, monkeypatch):
        """Should return file_enabled from config"""
        monkeypatch.setenv('LOG_TO_FILE', 'true')

        assert get_file_enabled() is True

    def test_get_log_file_path(self, monkeypatch, tmp_path):
        """Should return log_file_path from config"""
        custom_path = str(tmp_path / 'logs')
        monkeypatch.setenv('LOG_FILE_PATH', custom_path)

        assert get_log_file_path() == Path(custom_path)


class TestEdgeCases:
    """Test edge cases and boundary conditions"""

    def test_whitespace_in_env_vars(self, monkeypatch):
        """Should handle whitespace in environment variables"""
        monkeypatch.setenv('LOG_TO_CONSOLE', '  true  ')
        monkeypatch.setenv('LOG_FILE_PATH', '  ./logs/  ')

        config = get_config()
        assert config['console_enabled'] is True
        assert config['log_file_path'] == Path('./logs/')

    def test_multiple_config_calls_consistent(self, monkeypatch):
        """Should return consistent config across multiple calls"""
        monkeypatch.setenv('LOG_TO_CONSOLE', 'true')
        monkeypatch.setenv('LOG_TO_FILE', 'true')

        config1 = get_config()
        config2 = get_config()

        assert config1 == config2

    def test_zero_max_bytes(self, monkeypatch):
        """Should handle edge case of 0 max bytes"""
        monkeypatch.setenv('LOG_FILE_MAX_BYTES', '0')

        config = get_config()
        assert config['log_file_max_bytes'] == 0

    def test_zero_backup_count(self, monkeypatch):
        """Should handle edge case of 0 backup count"""
        monkeypatch.setenv('LOG_FILE_BACKUP_COUNT', '0')

        config = get_config()
        assert config['log_file_backup_count'] == 0

    def test_negative_values_accepted(self, monkeypatch):
        """Negative values should be accepted (Python may use defaults internally)"""
        monkeypatch.setenv('LOG_FILE_MAX_BYTES', '-1')
        monkeypatch.setenv('LOG_FILE_BACKUP_COUNT', '-1')

        config = get_config()
        # Should parse as negative numbers (even if nonsensical)
        assert config['log_file_max_bytes'] == -1
        assert config['log_file_backup_count'] == -1
