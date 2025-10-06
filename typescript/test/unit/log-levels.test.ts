/**
 * Unit Tests: Log Level Constants
 *
 * Tests the SOVDEV_LOGLEVELS constants to ensure they match
 * OpenTelemetry severity levels and Winston log levels.
 */

import { describe, it } from 'node:test';
import assert from 'node:assert';
import { SOVDEV_LOGLEVELS } from '../../dist/index.js';

describe('SOVDEV_LOGLEVELS', () => {
  it('should have all required log levels', () => {
    assert.ok(SOVDEV_LOGLEVELS.DEBUG, 'DEBUG level should exist');
    assert.ok(SOVDEV_LOGLEVELS.INFO, 'INFO level should exist');
    assert.ok(SOVDEV_LOGLEVELS.WARN, 'WARN level should exist');
    assert.ok(SOVDEV_LOGLEVELS.ERROR, 'ERROR level should exist');
  });

  it('should use correct Winston level names', () => {
    assert.strictEqual(SOVDEV_LOGLEVELS.DEBUG, 'debug');
    assert.strictEqual(SOVDEV_LOGLEVELS.INFO, 'info');
    assert.strictEqual(SOVDEV_LOGLEVELS.WARN, 'warn');
    assert.strictEqual(SOVDEV_LOGLEVELS.ERROR, 'error');
  });

  it('should be lowercase strings', () => {
    assert.strictEqual(SOVDEV_LOGLEVELS.DEBUG, SOVDEV_LOGLEVELS.DEBUG.toLowerCase());
    assert.strictEqual(SOVDEV_LOGLEVELS.INFO, SOVDEV_LOGLEVELS.INFO.toLowerCase());
    assert.strictEqual(SOVDEV_LOGLEVELS.WARN, SOVDEV_LOGLEVELS.WARN.toLowerCase());
    assert.strictEqual(SOVDEV_LOGLEVELS.ERROR, SOVDEV_LOGLEVELS.ERROR.toLowerCase());
  });

  it('should have exactly 6 log levels', () => {
    const levels = Object.keys(SOVDEV_LOGLEVELS);
    assert.strictEqual(levels.length, 6, 'Should have exactly 6 log levels (TRACE, DEBUG, INFO, WARN, ERROR, FATAL)');
  });

  it('should have all 6 standard levels', () => {
    assert.ok(SOVDEV_LOGLEVELS.TRACE, 'TRACE level should exist');
    assert.ok(SOVDEV_LOGLEVELS.FATAL, 'FATAL level should exist');
  });

  it('should have unique values', () => {
    const values = Object.values(SOVDEV_LOGLEVELS);
    const uniqueValues = new Set(values);
    assert.strictEqual(values.length, uniqueValues.size, 'All log level values should be unique');
  });
});
