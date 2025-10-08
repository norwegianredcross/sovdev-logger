"""
Unit Tests: Log Level Constants

Tests the SOVDEV_LOGLEVELS constants to ensure they match
the TypeScript implementation and follow the standard.
"""

import pytest
from sovdev_logger.log_levels import SOVDEV_LOGLEVELS


class TestSovdevLogLevels:
    """Test SOVDEV_LOGLEVELS constants"""

    def test_has_all_required_levels(self):
        """Should have all 6 required log levels"""
        assert SOVDEV_LOGLEVELS.TRACE is not None
        assert SOVDEV_LOGLEVELS.DEBUG is not None
        assert SOVDEV_LOGLEVELS.INFO is not None
        assert SOVDEV_LOGLEVELS.WARN is not None
        assert SOVDEV_LOGLEVELS.ERROR is not None
        assert SOVDEV_LOGLEVELS.FATAL is not None

    def test_level_values(self):
        """Should use correct uppercase level names"""
        assert SOVDEV_LOGLEVELS.TRACE == 'TRACE'
        assert SOVDEV_LOGLEVELS.DEBUG == 'DEBUG'
        assert SOVDEV_LOGLEVELS.INFO == 'INFO'
        assert SOVDEV_LOGLEVELS.WARN == 'WARN'
        assert SOVDEV_LOGLEVELS.ERROR == 'ERROR'
        assert SOVDEV_LOGLEVELS.FATAL == 'FATAL'

    def test_levels_are_uppercase(self):
        """All level values should be uppercase strings"""
        levels = [
            SOVDEV_LOGLEVELS.TRACE,
            SOVDEV_LOGLEVELS.DEBUG,
            SOVDEV_LOGLEVELS.INFO,
            SOVDEV_LOGLEVELS.WARN,
            SOVDEV_LOGLEVELS.ERROR,
            SOVDEV_LOGLEVELS.FATAL
        ]
        for level in levels:
            assert isinstance(level, str), f"Level {level} should be a string"
            assert level == level.upper(), f"Level {level} should be uppercase"

    def test_has_exactly_six_levels(self):
        """Should have exactly 6 log levels"""
        # Count public attributes (excluding private/magic methods)
        public_attrs = [attr for attr in dir(SOVDEV_LOGLEVELS)
                       if not attr.startswith('_')]
        assert len(public_attrs) == 6, f"Should have exactly 6 log levels, got {len(public_attrs)}"

    def test_all_levels_unique(self):
        """All log level values should be unique"""
        levels = [
            SOVDEV_LOGLEVELS.TRACE,
            SOVDEV_LOGLEVELS.DEBUG,
            SOVDEV_LOGLEVELS.INFO,
            SOVDEV_LOGLEVELS.WARN,
            SOVDEV_LOGLEVELS.ERROR,
            SOVDEV_LOGLEVELS.FATAL
        ]
        assert len(levels) == len(set(levels)), "All log level values should be unique"

    @pytest.mark.parametrize("level_name,expected_value", [
        ('TRACE', 'TRACE'),
        ('DEBUG', 'DEBUG'),
        ('INFO', 'INFO'),
        ('WARN', 'WARN'),
        ('ERROR', 'ERROR'),
        ('FATAL', 'FATAL'),
    ])
    def test_level_mapping(self, level_name, expected_value):
        """Parametrized test for level name to value mapping"""
        actual_value = getattr(SOVDEV_LOGLEVELS, level_name)
        assert actual_value == expected_value

    def test_levels_are_immutable(self):
        """Log level constants should not be modifiable"""
        # Try to modify a level (should not affect the constant)
        original_value = SOVDEV_LOGLEVELS.INFO
        try:
            SOVDEV_LOGLEVELS.INFO = 'MODIFIED'
        except AttributeError:
            # This is good - attribute is read-only
            pass

        # Verify value unchanged (even if assignment was allowed)
        assert SOVDEV_LOGLEVELS.INFO == original_value
