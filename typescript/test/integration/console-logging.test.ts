/**
 * Integration Tests: Console Logging
 *
 * Tests the integration between sovdevInitialize, sovdevLog, and console output.
 * Verifies that logs are properly formatted and written to stdout/stderr.
 */

import { describe, it, beforeEach, afterEach } from 'node:test';
import assert from 'node:assert';
import { sovdevInitialize, sovdevLog, sovdevFlush, SOVDEV_LOGLEVELS, createPeerServices } from '../../dist/index.js';

describe('Console Logging Integration', () => {
  const originalEnv = process.env.NODE_ENV;
  let consoleOutput: string[] = [];
  let originalStdoutWrite: typeof process.stdout.write;

  beforeEach(() => {
    // Reset environment
    process.env.NODE_ENV = 'test';
    process.env.LOG_TO_CONSOLE = 'true';
    process.env.LOG_TO_FILE = 'false';
    delete process.env.OTEL_EXPORTER_OTLP_LOGS_ENDPOINT;

    // Capture console output
    consoleOutput = [];
    originalStdoutWrite = process.stdout.write;
    process.stdout.write = ((chunk: any) => {
      consoleOutput.push(chunk.toString());
      return true;
    }) as any;
  });

  afterEach(async () => {
    // Restore
    process.env.NODE_ENV = originalEnv;
    process.stdout.write = originalStdoutWrite;
    await sovdevFlush();
  });

  it('should initialize and log to console', async () => {
    const PEER_SERVICES = createPeerServices({});

    sovdevInitialize('test-console-service');

    sovdevLog(
      SOVDEV_LOGLEVELS.INFO,
      'testFunction',
      'Test message',
      PEER_SERVICES.INTERNAL,
      { input: 'data' },
      { output: 'result' }
    );

    await sovdevFlush();

    // Wait for Winston to flush
    await new Promise(resolve => setTimeout(resolve, 100));

    const output = consoleOutput.join('');
    assert.ok(output.includes('Test message'), 'Console should contain log message');
    assert.ok(output.includes('test-console-service'), 'Console should contain service name');
  });

  it('should log all log levels to console', async () => {
    const PEER_SERVICES = createPeerServices({});

    sovdevInitialize('test-levels-service');

    sovdevLog(SOVDEV_LOGLEVELS.DEBUG, 'testFn', 'Debug message', PEER_SERVICES.INTERNAL, null, null);
    sovdevLog(SOVDEV_LOGLEVELS.INFO, 'testFn', 'Info message', PEER_SERVICES.INTERNAL, null, null);
    sovdevLog(SOVDEV_LOGLEVELS.WARN, 'testFn', 'Warn message', PEER_SERVICES.INTERNAL, null, null);
    sovdevLog(SOVDEV_LOGLEVELS.ERROR, 'testFn', 'Error message', PEER_SERVICES.INTERNAL, null, null);

    await sovdevFlush();
    await new Promise(resolve => setTimeout(resolve, 100));

    const output = consoleOutput.join('');
    assert.ok(output.includes('Debug message'), 'Should log DEBUG');
    assert.ok(output.includes('Info message'), 'Should log INFO');
    assert.ok(output.includes('Warn message'), 'Should log WARN');
    assert.ok(output.includes('Error message'), 'Should log ERROR');
  });

  it('should include peer service in console output', async () => {
    const PEER_SERVICES = createPeerServices({
      EXTERNAL_API: 'SYS1234567'
    });

    sovdevInitialize('test-peer-service', '1.0.0', PEER_SERVICES.mappings);

    sovdevLog(
      SOVDEV_LOGLEVELS.INFO,
      'apiCall',
      'Called external API',
      PEER_SERVICES.EXTERNAL_API,
      { request: 'data' },
      { response: 'success' }
    );

    await sovdevFlush();
    await new Promise(resolve => setTimeout(resolve, 100));

    const output = consoleOutput.join('');
    assert.ok(output.includes('EXTERNAL_API') || output.includes('SYS1234567'), 'Should include peer service');
  });
});
