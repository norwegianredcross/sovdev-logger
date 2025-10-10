/**
 * Peer Service Constants Helper
 *
 * This module provides a type-safe way to define peer service names.
 * Use this to create constants for external systems your service integrates with.
 *
 * @example
 * ```typescript
 * // Define your peer services with CMDB mappings (always include INTERNAL)
 * export const PEER_SERVICES = create_peer_services({
 *   INTERNAL: 'INTERNAL',  // For internal operations
 *   PAYMENT_GATEWAY: 'SYS2034567',
 *   DATABASE: 'SYS2012345',
 *   EMAIL_SERVICE: 'SYS2056789'
 * });
 *
 * // Initialize with the mappings
 * sovdev_initialize('my-service', '1.0.0', PEER_SERVICES.mappings);
 *
 * // Use type-safe constants in logging
 * sovdev_log(INFO, FUNCTIONNAME, 'Payment processed', PEER_SERVICES.PAYMENT_GATEWAY, ...);
 * sovdev_log(INFO, FUNCTIONNAME, 'Internal operation', PEER_SERVICES.INTERNAL, ...);
 * ```
 */

/**
 * Create type-safe peer service constants
 *
 * @param definitions - Object mapping peer service names to system IDs (INTERNAL is auto-generated)
 * @returns Object with both constants (including INTERNAL) and mappings for sovdev_initialize
 *
 * @example
 * ```typescript
 * const PEER_SERVICES = create_peer_services({
 *   BRREG: 'SYS1234567',
 *   ALTINN: 'SYS1005678'
 * });
 *
 * // PEER_SERVICES.INTERNAL === 'INTERNAL' (auto-generated, always available)
 * // PEER_SERVICES.BRREG === 'BRREG' (constant for logging)
 * // PEER_SERVICES.mappings === { BRREG: 'SYS1234567', ALTINN: 'SYS1005678' }
 * // (INTERNAL is auto-added during sovdev_initialize)
 * ```
 */
export function create_peer_services<T extends Record<string, string>>(
  definitions: T
): { [K in keyof T]: K } & { INTERNAL: 'INTERNAL' } & { mappings: T } {
  const constants = {} as { [K in keyof T]: K };

  // Create constants where each key maps to itself (the string name)
  for (const key in definitions) {
    constants[key] = key;
  }

  return {
    ...constants,
    INTERNAL: 'INTERNAL' as const,  // Always include INTERNAL constant
    mappings: definitions
  };
}
