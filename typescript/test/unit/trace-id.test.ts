/**
 * Unit Tests: Trace ID Generation
 *
 * Tests the sovdevGenerateTraceId() function to ensure it generates
 * valid UUID v4 trace IDs for distributed tracing.
 */

import { describe, it } from 'node:test';
import assert from 'node:assert';
import { sovdevGenerateTraceId } from '../../dist/index.js';

describe('sovdevGenerateTraceId', () => {
  it('should generate a valid UUID v4 format', () => {
    const traceId = sovdevGenerateTraceId();

    // UUID v4 format: xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx
    const uuidV4Regex = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

    assert.match(traceId, uuidV4Regex, 'Trace ID should match UUID v4 format');
  });

  it('should generate unique trace IDs', () => {
    const traceId1 = sovdevGenerateTraceId();
    const traceId2 = sovdevGenerateTraceId();
    const traceId3 = sovdevGenerateTraceId();

    assert.notStrictEqual(traceId1, traceId2, 'Trace IDs should be unique');
    assert.notStrictEqual(traceId2, traceId3, 'Trace IDs should be unique');
    assert.notStrictEqual(traceId1, traceId3, 'Trace IDs should be unique');
  });

  it('should generate trace IDs with correct length', () => {
    const traceId = sovdevGenerateTraceId();

    // UUID format with dashes: 36 characters
    assert.strictEqual(traceId.length, 36, 'Trace ID should be 36 characters long');
  });

  it('should generate lowercase trace IDs', () => {
    const traceId = sovdevGenerateTraceId();

    assert.strictEqual(traceId, traceId.toLowerCase(), 'Trace ID should be lowercase');
  });

  it('should generate 100 unique trace IDs rapidly', () => {
    const traceIds = new Set<string>();

    for (let i = 0; i < 100; i++) {
      traceIds.add(sovdevGenerateTraceId());
    }

    assert.strictEqual(traceIds.size, 100, 'All 100 trace IDs should be unique');
  });
});
