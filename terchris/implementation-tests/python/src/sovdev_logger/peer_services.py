"""
Peer Service Constants Helper

This module provides a type-safe way to define peer service names.
Use this to create constants for external systems your service integrates with.

Example:
    >>> PEER_SERVICES = create_peer_services({
    ...     'BRREG': 'SYS1234567',
    ...     'ALTINN': 'SYS7654321'
    ... })
    >>> PEER_SERVICES.BRREG  # Returns 'BRREG' (constant name)
    'BRREG'
    >>> PEER_SERVICES.INTERNAL  # Auto-generated
    'INTERNAL'
    >>> PEER_SERVICES.mappings  # Returns full mapping
    {'BRREG': 'SYS1234567', 'ALTINN': 'SYS7654321'}
"""

from typing import Dict


class PeerServices:
    """Type-safe peer service constants."""

    def __init__(self, definitions: Dict[str, str]):
        """
        Create peer service mapping with INTERNAL auto-generation.

        Args:
            definitions: Dictionary mapping service names to system IDs

        Returns:
            PeerServices object with:
            - Attribute access (PEER_SERVICES.BRREG returns 'BRREG')
            - Mapping access (PEER_SERVICES.mappings returns full dict)
            - Auto-generated INTERNAL constant
        """
        self.mappings = definitions.copy()
        self.INTERNAL = 'INTERNAL'

        # Create attributes for each defined service
        for key in definitions.keys():
            setattr(self, key, key)


def create_peer_services(definitions: Dict[str, str]) -> PeerServices:
    """
    Create type-safe peer service constants

    Args:
        definitions: Dictionary mapping peer service names to system IDs

    Returns:
        PeerServices object with constants and mappings

    Example:
        >>> PEER_SERVICES = create_peer_services({
        ...     'BRREG': 'SYS1234567',
        ...     'ALTINN': 'SYS7654321'
        ... })
        >>> PEER_SERVICES.BRREG  # Type-safe constant
        'BRREG'
        >>> PEER_SERVICES.mappings
        {'BRREG': 'SYS1234567', 'ALTINN': 'SYS7654321'}
    """
    return PeerServices(definitions)
