"""
Unit Tests: Peer Services Utility

Tests the create_peer_services function and PeerServices class
to ensure they match the TypeScript implementation behavior.
"""

import pytest
from sovdev_logger.peer_services import create_peer_services, PeerServices


class TestPeerServices:
    """Test peer services utility"""

    def test_create_peer_services_returns_peer_services_object(self):
        """Should return a PeerServices instance"""
        result = create_peer_services({'BRREG': 'SYS1234567'})
        assert isinstance(result, PeerServices)

    def test_creates_constants_from_definitions(self):
        """Should create constants where each key maps to itself"""
        peer_services = create_peer_services({
            'BRREG': 'SYS1234567',
            'ALTINN': 'SYS1005678'
        })

        assert peer_services.BRREG == 'BRREG'
        assert peer_services.ALTINN == 'ALTINN'

    def test_always_includes_internal_constant(self):
        """Should always include INTERNAL constant"""
        peer_services = create_peer_services({'BRREG': 'SYS1234567'})
        assert peer_services.INTERNAL == 'INTERNAL'

    def test_mappings_property_returns_original_definitions(self):
        """mappings property should return the original definitions"""
        from types import MappingProxyType

        definitions = {
            'BRREG': 'SYS1234567',
            'ALTINN': 'SYS1005678'
        }
        peer_services = create_peer_services(definitions)

        assert peer_services.mappings == definitions
        assert isinstance(peer_services.mappings, MappingProxyType)  # Immutable view

    def test_empty_definitions(self):
        """Should handle empty definitions"""
        peer_services = create_peer_services({})

        # Should still have INTERNAL
        assert peer_services.INTERNAL == 'INTERNAL'
        # Mappings should be empty
        assert peer_services.mappings == {}

    def test_constants_are_immutable(self):
        """Should not allow modification of constants"""
        peer_services = create_peer_services({'BRREG': 'SYS1234567'})

        with pytest.raises(AttributeError, match="Cannot modify peer service constant"):
            peer_services.BRREG = 'MODIFIED'

        # Verify value unchanged
        assert peer_services.BRREG == 'BRREG'

    def test_internal_constant_immutable(self):
        """INTERNAL constant should also be immutable"""
        peer_services = create_peer_services({'BRREG': 'SYS1234567'})

        with pytest.raises(AttributeError, match="Cannot modify peer service constant"):
            peer_services.INTERNAL = 'MODIFIED'

        assert peer_services.INTERNAL == 'INTERNAL'

    def test_cannot_add_new_attributes(self):
        """Should not allow adding new attributes"""
        peer_services = create_peer_services({'BRREG': 'SYS1234567'})

        with pytest.raises(AttributeError, match="Cannot modify peer service constant"):
            peer_services.NEW_SERVICE = 'NEW'

    def test_multiple_services(self):
        """Should handle multiple service definitions"""
        peer_services = create_peer_services({
            'PAYMENT_GATEWAY': 'SYS2034567',
            'DATABASE': 'SYS2012345',
            'EMAIL_SERVICE': 'SYS2056789',
            'CACHE': 'SYS2067890'
        })

        assert peer_services.PAYMENT_GATEWAY == 'PAYMENT_GATEWAY'
        assert peer_services.DATABASE == 'DATABASE'
        assert peer_services.EMAIL_SERVICE == 'EMAIL_SERVICE'
        assert peer_services.CACHE == 'CACHE'
        assert peer_services.INTERNAL == 'INTERNAL'

        assert len(peer_services.mappings) == 4

    def test_mappings_not_modifiable(self):
        """mappings property should return consistent object"""
        peer_services = create_peer_services({
            'BRREG': 'SYS1234567',
            'ALTINN': 'SYS1005678'
        })

        mappings1 = peer_services.mappings
        mappings2 = peer_services.mappings

        assert mappings1 == mappings2

    @pytest.mark.parametrize("key,system_id", [
        ('BRREG', 'SYS1234567'),
        ('ALTINN', 'SYS1005678'),
        ('SKATTEETATEN', 'SYS1009999'),
    ])
    def test_individual_service_mapping(self, key, system_id):
        """Parametrized test for individual service mappings"""
        peer_services = create_peer_services({key: system_id})

        # Constant should be the key name
        assert getattr(peer_services, key) == key
        # Mapping should have the system ID
        assert peer_services.mappings[key] == system_id

    def test_uppercase_key_names(self):
        """Service names should typically be uppercase (convention)"""
        peer_services = create_peer_services({
            'PAYMENT_API': 'SYS1111111',
            'USER_SERVICE': 'SYS2222222'
        })

        # Keys should be uppercase strings
        assert peer_services.PAYMENT_API.isupper()
        assert peer_services.USER_SERVICE.isupper()

    def test_realistic_usage_example(self):
        """Test realistic usage matching documentation example"""
        # Define peer services
        PEER_SERVICES = create_peer_services({
            'BRREG': 'SYS1234567',
            'ALTINN': 'SYS1005678'
        })

        # Verify constants exist
        assert PEER_SERVICES.INTERNAL == 'INTERNAL'
        assert PEER_SERVICES.BRREG == 'BRREG'
        assert PEER_SERVICES.ALTINN == 'ALTINN'

        # Verify mappings for sovdev_initialize
        assert PEER_SERVICES.mappings == {
            'BRREG': 'SYS1234567',
            'ALTINN': 'SYS1005678'
        }

        # INTERNAL is NOT in mappings (auto-added during sovdev_initialize)
        assert 'INTERNAL' not in PEER_SERVICES.mappings

    def test_repr(self):
        """__repr__ should show all constants for debugging"""
        peer_services = create_peer_services({
            'BRREG': 'SYS1234567',
            'CACHE': 'SYS9999999'
        })

        repr_str = repr(peer_services)
        # Should be alphabetically sorted
        assert repr_str == "PeerServices(BRREG, CACHE, INTERNAL)"
