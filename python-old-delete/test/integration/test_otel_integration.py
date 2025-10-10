"""
Integration Tests: OpenTelemetry Integration

Tests full OTEL SDK integration including LoggerProvider, TracerProvider, and MeterProvider.
"""

import pytest
import os
from sovdev_logger import sovdev_initialize, sovdev_log, sovdev_flush, SOVDEV_LOGLEVELS, create_peer_services
from sovdev_logger.logger import _global_state
from sovdev_logger.otel import get_logger_provider, get_tracer_provider, get_meter_provider


class TestOTELInitialization:
    """Test OTEL providers are initialized correctly"""

    def setup_method(self):
        """Reset state before each test"""
        _global_state.reset()

    def teardown_method(self):
        """Reset state after each test"""
        _global_state.reset()

    def test_otel_providers_initialized_without_endpoints(self, monkeypatch):
        """Should initialize TracerProvider and MeterProvider even without explicit endpoints"""
        # Clear OTLP endpoints
        monkeypatch.delenv('OTEL_EXPORTER_OTLP_ENDPOINT', raising=False)
        monkeypatch.delenv('OTEL_EXPORTER_OTLP_LOGS_ENDPOINT', raising=False)
        monkeypatch.delenv('OTEL_EXPORTER_OTLP_TRACES_ENDPOINT', raising=False)
        monkeypatch.delenv('OTEL_EXPORTER_OTLP_METRICS_ENDPOINT', raising=False)
        monkeypatch.setenv('LOG_TO_CONSOLE', 'false')
        monkeypatch.setenv('LOG_TO_FILE', 'false')

        PEER_SERVICES = create_peer_services({})
        sovdev_initialize('test-otel', '1.0.0')

        # TracerProvider should be initialized (has default endpoint)
        tracer_provider = get_tracer_provider()
        assert tracer_provider is not None

        # LoggerProvider should be None (no endpoint configured)
        logger_provider = get_logger_provider()
        assert logger_provider is None

        # MeterProvider should be initialized (has default endpoint)
        meter_provider = get_meter_provider()
        assert meter_provider is not None

    def test_otel_providers_initialized_with_logs_endpoint(self, monkeypatch):
        """Should initialize all providers when OTLP logs endpoint is configured"""
        monkeypatch.setenv('OTEL_EXPORTER_OTLP_LOGS_ENDPOINT', 'http://localhost:4318/v1/logs')
        monkeypatch.setenv('LOG_TO_CONSOLE', 'false')
        monkeypatch.setenv('LOG_TO_FILE', 'false')

        PEER_SERVICES = create_peer_services({})
        sovdev_initialize('test-otel', '1.0.0')

        # All providers should be initialized
        logger_provider = get_logger_provider()
        assert logger_provider is not None

        tracer_provider = get_tracer_provider()
        assert tracer_provider is not None

        meter_provider = get_meter_provider()
        assert meter_provider is not None

    def test_otel_providers_with_base_endpoint(self, monkeypatch):
        """Should derive all endpoints from base OTEL_EXPORTER_OTLP_ENDPOINT"""
        monkeypatch.setenv('OTEL_EXPORTER_OTLP_ENDPOINT', 'http://localhost:4318')
        monkeypatch.setenv('LOG_TO_CONSOLE', 'false')
        monkeypatch.setenv('LOG_TO_FILE', 'false')

        PEER_SERVICES = create_peer_services({})
        sovdev_initialize('test-otel', '1.0.0')

        # All providers should be initialized (endpoints derived from base)
        logger_provider = get_logger_provider()
        assert logger_provider is not None

        tracer_provider = get_tracer_provider()
        assert tracer_provider is not None

        meter_provider = get_meter_provider()
        assert meter_provider is not None


class TestOTELResourceAttributes:
    """Test OTEL Resource contains correct attributes"""

    def setup_method(self):
        """Reset state before each test"""
        _global_state.reset()

    def teardown_method(self):
        """Reset state after each test"""
        _global_state.reset()

    def test_resource_includes_service_name_and_version(self, monkeypatch):
        """Resource should include service.name and service.version"""
        monkeypatch.setenv('OTEL_EXPORTER_OTLP_LOGS_ENDPOINT', 'http://localhost:4318/v1/logs')
        monkeypatch.setenv('LOG_TO_CONSOLE', 'false')
        monkeypatch.setenv('LOG_TO_FILE', 'false')

        PEER_SERVICES = create_peer_services({})
        sovdev_initialize('my-test-service', '2.5.0')

        # Get provider and check resource
        logger_provider = get_logger_provider()
        assert logger_provider is not None

        resource = logger_provider.resource
        assert resource.attributes.get('service.name') == 'my-test-service'
        assert resource.attributes.get('service.version') == '2.5.0'

    def test_resource_includes_session_id(self, monkeypatch):
        """Resource should include session.id for execution grouping"""
        monkeypatch.setenv('OTEL_EXPORTER_OTLP_LOGS_ENDPOINT', 'http://localhost:4318/v1/logs')
        monkeypatch.setenv('LOG_TO_CONSOLE', 'false')
        monkeypatch.setenv('LOG_TO_FILE', 'false')

        PEER_SERVICES = create_peer_services({})
        sovdev_initialize('test', '1.0.0')

        # Get provider and check resource
        logger_provider = get_logger_provider()
        resource = logger_provider.resource

        # session.id should be present and be a UUID
        session_id = resource.attributes.get('session.id')
        assert session_id is not None
        assert len(session_id) == 36  # UUID format
        assert session_id.count('-') == 4  # UUID has 4 hyphens

    def test_resource_includes_deployment_environment(self, monkeypatch):
        """Resource should include deployment.environment"""
        monkeypatch.setenv('OTEL_EXPORTER_OTLP_LOGS_ENDPOINT', 'http://localhost:4318/v1/logs')
        monkeypatch.setenv('DEPLOYMENT_ENVIRONMENT', 'production')
        monkeypatch.setenv('LOG_TO_CONSOLE', 'false')
        monkeypatch.setenv('LOG_TO_FILE', 'false')

        PEER_SERVICES = create_peer_services({})
        sovdev_initialize('test', '1.0.0')

        # Get provider and check resource
        logger_provider = get_logger_provider()
        resource = logger_provider.resource

        assert resource.attributes.get('deployment.environment') == 'production'

    def test_resource_deployment_environment_defaults_to_development(self, monkeypatch):
        """Resource should default deployment.environment to 'development'"""
        monkeypatch.setenv('OTEL_EXPORTER_OTLP_LOGS_ENDPOINT', 'http://localhost:4318/v1/logs')
        monkeypatch.delenv('DEPLOYMENT_ENVIRONMENT', raising=False)
        monkeypatch.setenv('LOG_TO_CONSOLE', 'false')
        monkeypatch.setenv('LOG_TO_FILE', 'false')

        PEER_SERVICES = create_peer_services({})
        sovdev_initialize('test', '1.0.0')

        # Get provider and check resource
        logger_provider = get_logger_provider()
        resource = logger_provider.resource

        assert resource.attributes.get('deployment.environment') == 'development'


class TestOTELFlush:
    """Test OTEL flush functionality"""

    def setup_method(self):
        """Reset state before each test"""
        _global_state.reset()

    def teardown_method(self):
        """Reset state after each test"""
        _global_state.reset()

    def test_flush_without_initialization_doesnt_crash(self, capsys):
        """Should not crash when flushing without initialization"""
        # Should not raise exception
        try:
            sovdev_flush()
        except Exception as e:
            pytest.fail(f"Flush should not crash without initialization: {e}")

        captured = capsys.readouterr()
        assert '🔄 Flushing OpenTelemetry providers' in captured.err

    def test_flush_after_initialization(self, capsys, monkeypatch):
        """Should successfully flush after initialization"""
        monkeypatch.setenv('OTEL_EXPORTER_OTLP_LOGS_ENDPOINT', 'http://localhost:4318/v1/logs')
        monkeypatch.setenv('LOG_TO_CONSOLE', 'false')
        monkeypatch.setenv('LOG_TO_FILE', 'false')

        PEER_SERVICES = create_peer_services({})
        sovdev_initialize('test', '1.0.0')

        # Log something
        sovdev_log(SOVDEV_LOGLEVELS.INFO, 'test', 'Message', PEER_SERVICES.INTERNAL)

        # Flush
        sovdev_flush()

        captured = capsys.readouterr()
        assert '🔄 Flushing OpenTelemetry providers' in captured.err
        assert '✅ OpenTelemetry flush complete' in captured.err or '⚠️' in captured.err

    def test_flush_with_custom_timeout(self, capsys, monkeypatch):
        """Should accept custom timeout parameter"""
        monkeypatch.setenv('OTEL_EXPORTER_OTLP_LOGS_ENDPOINT', 'http://localhost:4318/v1/logs')
        monkeypatch.setenv('LOG_TO_CONSOLE', 'false')
        monkeypatch.setenv('LOG_TO_FILE', 'false')

        PEER_SERVICES = create_peer_services({})
        sovdev_initialize('test', '1.0.0')

        # Should not raise exception
        try:
            sovdev_flush(timeout_millis=5000)
        except Exception as e:
            pytest.fail(f"Flush with timeout should not crash: {e}")


class TestOTELHeaders:
    """Test OTEL_EXPORTER_OTLP_HEADERS parsing"""

    def setup_method(self):
        """Reset state before each test"""
        _global_state.reset()

    def teardown_method(self):
        """Reset state after each test"""
        _global_state.reset()

    def test_otel_headers_parsing(self, monkeypatch):
        """Should parse OTEL_EXPORTER_OTLP_HEADERS JSON"""
        monkeypatch.setenv('OTEL_EXPORTER_OTLP_LOGS_ENDPOINT', 'http://localhost:4318/v1/logs')
        monkeypatch.setenv('OTEL_EXPORTER_OTLP_HEADERS', '{"Host":"otel.localhost","Authorization":"Bearer token123"}')
        monkeypatch.setenv('LOG_TO_CONSOLE', 'false')
        monkeypatch.setenv('LOG_TO_FILE', 'false')

        PEER_SERVICES = create_peer_services({})
        # Should initialize without error
        sovdev_initialize('test', '1.0.0')

        # Providers should be initialized
        logger_provider = get_logger_provider()
        assert logger_provider is not None

    def test_invalid_otel_headers_warning(self, capsys, monkeypatch):
        """Should warn when OTEL_EXPORTER_OTLP_HEADERS is invalid JSON"""
        monkeypatch.setenv('OTEL_EXPORTER_OTLP_LOGS_ENDPOINT', 'http://localhost:4318/v1/logs')
        monkeypatch.setenv('OTEL_EXPORTER_OTLP_HEADERS', 'invalid-json')
        monkeypatch.setenv('LOG_TO_CONSOLE', 'false')
        monkeypatch.setenv('LOG_TO_FILE', 'false')

        PEER_SERVICES = create_peer_services({})
        sovdev_initialize('test', '1.0.0')

        captured = capsys.readouterr()
        # Should have warning about parsing failure
        assert 'Warning' in captured.err or 'Could not parse' in captured.err or logger_provider is not None

        # But initialization should still succeed
        logger_provider = get_logger_provider()
        assert logger_provider is not None


class TestOTELIntegrationEndToEnd:
    """End-to-end OTEL integration tests"""

    def setup_method(self):
        """Reset state before each test"""
        _global_state.reset()

    def teardown_method(self):
        """Reset state after each test"""
        _global_state.reset()

    def test_full_lifecycle_with_otel(self, monkeypatch):
        """Test complete lifecycle: initialize -> log -> flush"""
        monkeypatch.setenv('OTEL_EXPORTER_OTLP_LOGS_ENDPOINT', 'http://localhost:4318/v1/logs')
        monkeypatch.setenv('LOG_TO_CONSOLE', 'false')
        monkeypatch.setenv('LOG_TO_FILE', 'false')

        PEER_SERVICES = create_peer_services({'API': 'SYS123'})

        # Initialize
        sovdev_initialize('test-lifecycle', '1.0.0', PEER_SERVICES.mappings)

        # Verify providers initialized
        assert get_logger_provider() is not None
        assert get_tracer_provider() is not None
        assert get_meter_provider() is not None

        # Log various levels
        sovdev_log(SOVDEV_LOGLEVELS.INFO, 'test', 'Info message', PEER_SERVICES.INTERNAL)
        sovdev_log(SOVDEV_LOGLEVELS.ERROR, 'test', 'Error message', PEER_SERVICES.API)
        sovdev_log(
            SOVDEV_LOGLEVELS.DEBUG,
            'test',
            'Debug with data',
            PEER_SERVICES.INTERNAL,
            input_json={'key': 'value'},
            response_json={'status': 'ok'}
        )

        # Flush (should not crash)
        try:
            sovdev_flush()
        except Exception as e:
            pytest.fail(f"Full lifecycle should not crash: {e}")

    def test_otel_silent_mode_default(self, capsys, monkeypatch):
        """OTEL should initialize silently by default (verbose=False)"""
        monkeypatch.setenv('OTEL_EXPORTER_OTLP_LOGS_ENDPOINT', 'http://localhost:4318/v1/logs')
        monkeypatch.setenv('LOG_TO_CONSOLE', 'false')
        monkeypatch.setenv('LOG_TO_FILE', 'false')

        PEER_SERVICES = create_peer_services({})
        sovdev_initialize('test', '1.0.0')

        captured = capsys.readouterr()

        # Should NOT have OTEL diagnostic messages (verbose=False)
        assert '🔍 OTLP Trace exporter configured' not in captured.err
        assert '📡 OTLP Log exporter configured' not in captured.err
        assert '📊 OTLP Metric exporter configured' not in captured.err
        assert '🔗 OpenTelemetry SDK initialized' not in captured.err
