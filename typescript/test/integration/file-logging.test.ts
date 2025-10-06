/**
 * Integration Tests: File Logging
 *
 * Tests the integration between sovdevLog and file output.
 * Verifies that logs are properly written to JSON files in ./logs/ directory.
 */

import { describe, it, beforeEach, afterEach } from 'node:test';
import assert from 'node:assert';
import * as fs from 'node:fs';
import * as path from 'node:path';
import { sovdevInitialize, sovdevLog, sovdevFlush, SOVDEV_LOGLEVELS, createPeerServices } from '../../dist/index.js';

describe('File Logging Integration', () => {
  const originalEnv = process.env.NODE_ENV;
  const testLogsDir = path.join(process.cwd(), 'logs-test-integration');

  beforeEach(() => {
    // Setup test environment
    process.env.NODE_ENV = 'test';
    process.env.LOG_TO_FILE = 'true';
    process.env.LOG_TO_CONSOLE = 'false';
    process.env.LOG_FILE_PATH = path.join(testLogsDir, 'test.log');
    delete process.env.OTEL_EXPORTER_OTLP_LOGS_ENDPOINT;

    // Clean up test logs directory
    if (fs.existsSync(testLogsDir)) {
      fs.rmSync(testLogsDir, { recursive: true, force: true });
    }
  });

  afterEach(async () => {
    // Cleanup
    process.env.NODE_ENV = originalEnv;
    delete process.env.LOG_FILE_PATH;
    await sovdevFlush();

    // Clean up test logs
    if (fs.existsSync(testLogsDir)) {
      fs.rmSync(testLogsDir, { recursive: true, force: true });
    }
  });

  it('should create logs directory if it does not exist', async () => {
    const PEER_SERVICES = createPeerServices({});

    sovdevInitialize('test-file-service');

    sovdevLog(
      SOVDEV_LOGLEVELS.INFO,
      'testFunction',
      'Test file logging',
      PEER_SERVICES.INTERNAL,
      null,
      null
    );

    await sovdevFlush();
    await new Promise(resolve => setTimeout(resolve, 200));

    assert.ok(fs.existsSync(testLogsDir), 'Logs directory should be created');
  });

  it('should write log entries to log file', async () => {
    const PEER_SERVICES = createPeerServices({});

    sovdevInitialize('test-json-file-service');

    sovdevLog(
      SOVDEV_LOGLEVELS.INFO,
      'testFunction',
      'JSON log entry',
      PEER_SERVICES.INTERNAL,
      { test: 'input' },
      { test: 'output' }
    );

    await sovdevFlush();
    await new Promise(resolve => setTimeout(resolve, 200));

    // Check log file exists and has content
    const logFilePath = path.join(testLogsDir, 'test.log');
    assert.ok(fs.existsSync(logFilePath), 'Log file should exist');

    const content = fs.readFileSync(logFilePath, 'utf-8');
    assert.ok(content.includes('JSON log entry'), 'Log file should contain message');
    assert.ok(content.includes('test-json-file-service'), 'Log file should contain service name');
  });

  it('should write multiple log levels to file', async () => {
    const PEER_SERVICES = createPeerServices({});

    sovdevInitialize('test-multiLevel-service');

    sovdevLog(SOVDEV_LOGLEVELS.INFO, 'fn1', 'Info message', PEER_SERVICES.INTERNAL, null, null);
    sovdevLog(SOVDEV_LOGLEVELS.WARN, 'fn2', 'Warn message', PEER_SERVICES.INTERNAL, null, null);
    sovdevLog(SOVDEV_LOGLEVELS.ERROR, 'fn3', 'Error message', PEER_SERVICES.INTERNAL, null, null);

    await sovdevFlush();
    await new Promise(resolve => setTimeout(resolve, 200));

    const logFilePath = path.join(testLogsDir, 'test.log');
    assert.ok(fs.existsSync(logFilePath), 'Log file should exist');

    const content = fs.readFileSync(logFilePath, 'utf-8');
    assert.ok(content.includes('Info message'), 'Should log INFO');
    assert.ok(content.includes('Warn message'), 'Should log WARN');
    assert.ok(content.includes('Error message'), 'Should log ERROR');
  });
});
