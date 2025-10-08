"""
Peer Service Constants Helper

This module provides a type-safe way to define peer service names.
Use this to create constants for external systems your service integrates with.

Example:
    >>> # Define your peer services with CMDB mappings
    >>> PEER_SERVICES = create_peer_services({
    ...     'PAYMENT_GATEWAY': 'SYS2034567',
    ...     'DATABASE': 'SYS2012345',
    ...     'EMAIL_SERVICE': 'SYS2056789'
    ... })
    >>>
    >>> # Initialize with the mappings
    >>> sovdev_initialize('my-service', '1.0.0', PEER_SERVICES.mappings)
    >>>
    >>> # Use type-safe constants in logging
    >>> sovdev_log(INFO, FUNCTIONNAME, 'Payment processed', PEER_SERVICES.PAYMENT_GATEWAY, ...)
    >>> sovdev_log(INFO, FUNCTIONNAME, 'Internal operation', PEER_SERVICES.INTERNAL, ...)
"""

from types import MappingProxyType
from typing import Any


class PeerServices:
    """
    Container for peer service constants and mappings.

    Provides both uppercase constants for use in logging and
    the original mappings for initialization.

    Note: __slots__ not used because we need dynamic attribute creation.
    """

    def __init__(self, definitions: dict[str, str]):
        """
        Initialize peer services with definitions.

        Args:
            definitions: Dictionary mapping peer service names to system IDs
        """
        # Store the mappings for sovdev_initialize (immutable)
        object.__setattr__(self, '_mappings', MappingProxyType(definitions))

        # Store which constants were defined (for __repr__)
        object.__setattr__(self, '_constants', set(definitions.keys()) | {'INTERNAL'})

        # Create constants where each key maps to itself
        for key in definitions:
            object.__setattr__(self, key, key)

        # Always include INTERNAL constant
        object.__setattr__(self, 'INTERNAL', 'INTERNAL')

    @property
    def mappings(self) -> MappingProxyType[str, str]:
        """Get the peer service mappings for sovdev_initialize (immutable view)."""
        return self._mappings

    def __setattr__(self, name: str, value: Any) -> None:
        """Prevent attribute modification to ensure immutability."""
        raise AttributeError(f"Cannot modify peer service constant '{name}'")

    def __repr__(self) -> str:
        """Return string representation for debugging."""
        constants = sorted(self._constants)
        return f"PeerServices({', '.join(constants)})"


def create_peer_services(definitions: dict[str, str]) -> PeerServices:
    """
    Create type-safe peer service constants.

    Args:
        definitions: Dictionary mapping peer service names to system IDs

    Returns:
        PeerServices object with constants and mappings

    Example:
        >>> PEER_SERVICES = create_peer_services({
        ...     'BRREG': 'SYS1234567',
        ...     'ALTINN': 'SYS1005678'
        ... })
        >>>
        >>> # PEER_SERVICES.INTERNAL == 'INTERNAL' (auto-generated, always available)
        >>> # PEER_SERVICES.BRREG == 'BRREG' (constant for logging)
        >>> # PEER_SERVICES.mappings == {'BRREG': 'SYS1234567', 'ALTINN': 'SYS1005678'}
        >>> # (INTERNAL is auto-added during sovdev_initialize)
    """
    return PeerServices(definitions)
