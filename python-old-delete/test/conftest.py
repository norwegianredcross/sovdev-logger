"""Shared pytest fixtures for all tests"""
import pytest
import os


@pytest.fixture(scope="session")
def session_id():
    """Generate session ID for test run"""
    import uuid
    return str(uuid.uuid4())


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    """Clean environment before each test"""
    # Remove OTLP endpoints by default
    monkeypatch.delenv('OTEL_EXPORTER_OTLP_LOGS_ENDPOINT', raising=False)
    monkeypatch.delenv('OTEL_EXPORTER_OTLP_METRICS_ENDPOINT', raising=False)
    monkeypatch.delenv('OTEL_EXPORTER_OTLP_TRACES_ENDPOINT', raising=False)

    # Set safe defaults
    monkeypatch.setenv('LOG_TO_CONSOLE', 'false')
    monkeypatch.setenv('LOG_TO_FILE', 'false')

    yield

    # Cleanup after test
    try:
        # Import will fail until Stage 8 (flush implementation)
        # from sovdev_logger import sovdev_flush
        # sovdev_flush()
        pass
    except:
        pass


@pytest.fixture
def enable_console(monkeypatch):
    """Enable console logging for test"""
    monkeypatch.setenv('LOG_TO_CONSOLE', 'true')


@pytest.fixture
def enable_file_logging(tmp_path, monkeypatch):
    """Enable file logging to temp directory"""
    log_file = tmp_path / "test.log"
    monkeypatch.setenv('LOG_TO_FILE', 'true')
    monkeypatch.setenv('LOG_FILE_PATH', str(log_file))
    return log_file


@pytest.fixture
def mock_kubernetes_otlp(monkeypatch):
    """Configure for Kubernetes testing"""
    monkeypatch.setenv('OTEL_EXPORTER_OTLP_LOGS_ENDPOINT', 'http://host.docker.internal/v1/logs')
    monkeypatch.setenv('OTEL_EXPORTER_OTLP_HEADERS', '{"Host": "otel.localhost"}')
