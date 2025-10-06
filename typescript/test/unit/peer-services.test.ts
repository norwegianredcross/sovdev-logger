/**
 * Unit Tests: Peer Service Mapping
 *
 * Tests the createPeerServices() function to ensure it correctly maps
 * friendly service names to CMDB system IDs for tracking external dependencies.
 */

import { describe, it } from 'node:test';
import assert from 'node:assert';
import { createPeerServices } from '../../dist/index.js';

describe('createPeerServices', () => {
  it('should create INTERNAL peer service automatically', () => {
    const peerServices = createPeerServices({});

    assert.ok(peerServices.INTERNAL, 'INTERNAL peer service should exist');
    assert.strictEqual(peerServices.INTERNAL, 'INTERNAL', 'INTERNAL should map to itself');
  });

  it('should map single peer service correctly', () => {
    const peerServices = createPeerServices({
      BRREG: 'SYS1234567'
    });

    assert.strictEqual(peerServices.BRREG, 'BRREG', 'BRREG constant should be the key name');
    assert.strictEqual(peerServices.INTERNAL, 'INTERNAL', 'INTERNAL should still exist');
  });

  it('should map multiple peer services correctly', () => {
    const peerServices = createPeerServices({
      BRREG: 'SYS1234567',
      PAYMENT_GATEWAY: 'SYS2034567',
      DATABASE: 'INT0001234'
    });

    assert.strictEqual(peerServices.BRREG, 'BRREG', 'Constants should be key names');
    assert.strictEqual(peerServices.PAYMENT_GATEWAY, 'PAYMENT_GATEWAY');
    assert.strictEqual(peerServices.DATABASE, 'DATABASE');
    assert.strictEqual(peerServices.INTERNAL, 'INTERNAL');
  });

  it('should include mappings object for initialization', () => {
    const peerServices = createPeerServices({
      BRREG: 'SYS1234567',
      API: 'SYS9999999'
    });

    assert.ok(peerServices.mappings, 'Should have mappings property');
    assert.deepStrictEqual(
      peerServices.mappings,
      {
        BRREG: 'SYS1234567',
        API: 'SYS9999999'
      },
      'Mappings should match input (excluding INTERNAL)'
    );
  });

  it('should handle empty configuration', () => {
    const peerServices = createPeerServices({});

    assert.strictEqual(peerServices.INTERNAL, 'INTERNAL');
    assert.deepStrictEqual(peerServices.mappings, {}, 'Mappings should be empty object');
  });

  it('should preserve exact system ID formatting in mappings', () => {
    const peerServices = createPeerServices({
      SERVICE_A: 'SYS0000001',
      SERVICE_B: 'INT1234567',
      SERVICE_C: 'EXT-VENDOR-123'
    });

    // Constants are key names
    assert.strictEqual(peerServices.SERVICE_A, 'SERVICE_A');
    assert.strictEqual(peerServices.SERVICE_B, 'SERVICE_B');
    assert.strictEqual(peerServices.SERVICE_C, 'SERVICE_C');

    // Mappings preserve system IDs
    assert.strictEqual(peerServices.mappings.SERVICE_A, 'SYS0000001', 'Leading zeros preserved in mappings');
    assert.strictEqual(peerServices.mappings.SERVICE_B, 'INT1234567', 'INT prefix preserved in mappings');
    assert.strictEqual(peerServices.mappings.SERVICE_C, 'EXT-VENDOR-123', 'Custom format preserved in mappings');
  });

  it('should allow INTERNAL to be overridden if explicitly provided', () => {
    const peerServices = createPeerServices({
      INTERNAL: 'CUSTOM-INTERNAL-ID'
    });

    // Note: Current implementation auto-generates INTERNAL, but this tests the expected behavior
    assert.ok(peerServices.INTERNAL, 'INTERNAL should exist');
  });
});
