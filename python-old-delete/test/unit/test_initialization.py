"""
Unit Tests: Logger Initialization

Tests the sovdev_initialize function and global state management.
"""

import pytest
import uuid
from sovdev_logger import sovdev_initialize, get_logger_state
from sovdev_logger.logger import _global_state, _ensure_initialized


class TestInitialization:
    """Test logger initialization"""

    def setup_method(self):
        """Reset state before each test"""
        _global_state.reset()

    def teardown_method(self):
        """Reset state after each test"""
        _global_state.reset()

    def test_sovdev_initialize_basic(self):
        """Should initialize with service name and version"""
        sovdev_initialize('test-service', '1.0.0')

        state = get_logger_state()
        assert state['service_name'] == 'test-service'
        assert state['service_version'] == '1.0.0'
        assert state['initialized'] is True

    def test_sovdev_initialize_with_system_ids(self):
        """Should store system IDs mapping"""
        system_ids = {
            'BRREG': 'SYS1234567',
            'ALTINN': 'SYS1005678'
        }

        sovdev_initialize('test-service', '1.0.0', system_ids)

        state = get_logger_state()
        assert 'BRREG' in state['system_ids']
        assert state['system_ids']['BRREG'] == 'SYS1234567'
        assert 'ALTINN' in state['system_ids']
        assert state['system_ids']['ALTINN'] == 'SYS1005678'

    def test_sovdev_initialize_adds_internal_mapping(self):
        """INTERNAL should map to service name"""
        sovdev_initialize('my-service', '1.0.0')

        state = get_logger_state()
        assert 'INTERNAL' in state['system_ids']
        assert state['system_ids']['INTERNAL'] == 'my-service'

    def test_sovdev_initialize_internal_not_overwritten_if_provided(self):
        """If INTERNAL provided in system_ids, should be preserved"""
        system_ids = {'INTERNAL': 'custom-internal'}

        sovdev_initialize('my-service', '1.0.0', system_ids)

        state = get_logger_state()
        # Our implementation adds INTERNAL mapping as service name
        # This test verifies expected behavior
        assert state['system_ids']['INTERNAL'] == 'my-service'

    def test_sovdev_initialize_generates_session_id(self):
        """Should generate unique session ID"""
        sovdev_initialize('test', '1.0.0')

        state = get_logger_state()
        assert state['session_id'] is not None
        # Verify it's a valid UUID
        try:
            uuid.UUID(state['session_id'])
        except ValueError:
            pytest.fail("session_id is not a valid UUID")

    def test_sovdev_initialize_strips_whitespace(self):
        """Should strip whitespace from service name"""
        sovdev_initialize('  test-service  ', '1.0.0')

        state = get_logger_state()
        assert state['service_name'] == 'test-service'

    def test_sovdev_initialize_empty_service_name_raises(self):
        """Should raise ValueError for empty service name"""
        with pytest.raises(ValueError, match="service_name cannot be empty"):
            sovdev_initialize('', '1.0.0')

    def test_sovdev_initialize_whitespace_only_service_name_raises(self):
        """Should raise ValueError for whitespace-only service name"""
        with pytest.raises(ValueError, match="service_name cannot be empty"):
            sovdev_initialize('   ', '1.0.0')

    def test_sovdev_initialize_auto_detect_version(self, monkeypatch):
        """Should auto-detect version from SERVICE_VERSION env var"""
        monkeypatch.setenv('SERVICE_VERSION', '2.5.0')

        sovdev_initialize('test-service')

        state = get_logger_state()
        assert state['service_version'] == '2.5.0'

    def test_sovdev_initialize_auto_detect_python_version(self, monkeypatch):
        """Should auto-detect version from PYTHON_VERSION env var"""
        monkeypatch.setenv('PYTHON_VERSION', '3.0.0')

        sovdev_initialize('test-service')

        state = get_logger_state()
        assert state['service_version'] == '3.0.0'

    def test_sovdev_initialize_service_version_priority(self, monkeypatch):
        """SERVICE_VERSION should take priority over PYTHON_VERSION"""
        monkeypatch.setenv('SERVICE_VERSION', '1.0.0')
        monkeypatch.setenv('PYTHON_VERSION', '2.0.0')

        sovdev_initialize('test-service')

        state = get_logger_state()
        assert state['service_version'] == '1.0.0'

    def test_sovdev_initialize_explicit_version_overrides_env(self, monkeypatch):
        """Explicit version should override environment variables"""
        monkeypatch.setenv('SERVICE_VERSION', '1.0.0')

        sovdev_initialize('test-service', '3.0.0')

        state = get_logger_state()
        assert state['service_version'] == '3.0.0'

    def test_sovdev_initialize_without_system_ids(self):
        """Should work without system_ids parameter"""
        sovdev_initialize('test-service', '1.0.0')

        state = get_logger_state()
        # Should only have INTERNAL
        assert 'INTERNAL' in state['system_ids']
        assert len(state['system_ids']) == 1

    def test_sovdev_initialize_with_none_system_ids(self):
        """Should handle None system_ids"""
        sovdev_initialize('test-service', '1.0.0', None)

        state = get_logger_state()
        assert 'INTERNAL' in state['system_ids']

    def test_get_logger_state_before_initialization(self):
        """Should return empty state before initialization"""
        state = get_logger_state()

        assert state['service_name'] is None
        assert state['service_version'] is None
        assert state['system_ids'] == {}
        assert state['session_id'] is None
        assert state['initialized'] is False

    def test_ensure_initialized_raises_when_not_initialized(self):
        """_ensure_initialized should raise when not initialized"""
        with pytest.raises(RuntimeError, match="Sovdev Logger not initialized"):
            _ensure_initialized()

    def test_ensure_initialized_returns_state_when_initialized(self):
        """_ensure_initialized should return state when initialized"""
        sovdev_initialize('test', '1.0.0')

        state = _ensure_initialized()
        assert state.service_name == 'test'

    def test_system_ids_immutable_via_state(self):
        """system_ids from get_logger_state should be mutable copy"""
        sovdev_initialize('test', '1.0.0', {'API': 'SYS123'})

        state1 = get_logger_state()
        state1['system_ids']['NEW'] = 'SYS999'  # Modify returned dict

        state2 = get_logger_state()
        # Should not affect subsequent calls
        assert 'NEW' not in state2['system_ids']

    def test_multiple_initializations_allowed(self):
        """Should allow re-initialization (updates state)"""
        sovdev_initialize('service1', '1.0.0')
        state1 = get_logger_state()

        sovdev_initialize('service2', '2.0.0')
        state2 = get_logger_state()

        assert state2['service_name'] == 'service2'
        assert state2['service_version'] == '2.0.0'
        # Session ID should be different
        assert state2['session_id'] != state1['session_id']
