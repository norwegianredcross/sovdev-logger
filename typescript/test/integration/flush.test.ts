/**
 * Integration Tests: Flush Behavior
 *
 * Tests the sovdevFlush() function to ensure logs are properly
 * flushed to all configured outputs (console, file, OTLP).
 */

import { describe, it, beforeEach, afterEach } from 'node:test';
import assert from 'node:assert';
import * as fs from 'node:fs';
import * as path from 'node:path';
import { sovdevInitialize, sovdevLog, sovdevFlush, SOVDEV_LOGLEVELS, createPeerServices } from '../../dist/index.js';

describe('Flush Behavior Integration', () => {
  const originalEnv = process.env.NODE_ENV;
  const testLogsDir = path.join(process.cwd(), 'logs-test-flush');
  let consoleOutput: string[] = [];
  let originalStdoutWrite: typeof process.stdout.write;

  beforeEach(() => {
    process.env.NODE_ENV = 'test';
    process.env.LOG_TO_CONSOLE = 'true';
    process.env.LOG_TO_FILE = 'true';
    process.env.LOG_FILE_PATH = path.join(testLogsDir, 'test.log');
    delete process.env.OTEL_EXPORTER_OTLP_LOGS_ENDPOINT;

    // Clean up test logs directory
    if (fs.existsSync(testLogsDir)) {
      fs.rmSync(testLogsDir, { recursive: true, force: true });
    }

    // Capture console output
    consoleOutput = [];
    originalStdoutWrite = process.stdout.write;
    process.stdout.write = ((chunk: any) => {
      consoleOutput.push(chunk.toString());
      return true;
    }) as any;
  });

  afterEach(async () => {
    process.env.NODE_ENV = originalEnv;
    delete process.env.LOG_FILE_PATH;
    process.stdout.write = originalStdoutWrite;
    await sovdevFlush();

    // Clean up test logs
    if (fs.existsSync(testLogsDir)) {
      fs.rmSync(testLogsDir, { recursive: true, force: true });
    }
  });

  it('should flush logs to console immediately', async () => {
    const PEER_SERVICES = createPeerServices({});

    sovdevInitialize('test-flush-console');

    sovdevLog(
      SOVDEV_LOGLEVELS.INFO,
      'testFunction',
      'Before flush',
      PEER_SERVICES.INTERNAL,
      null,
      null
    );

    // Flush and wait
    await sovdevFlush();
    await new Promise(resolve => setTimeout(resolve, 100));

    const output = consoleOutput.join('');
    assert.ok(output.includes('Before flush'), 'Logs should be flushed to console');
  });

  it('should flush logs to file', async () => {
    const PEER_SERVICES = createPeerServices({});

    sovdevInitialize('test-flush-file');

    sovdevLog(
      SOVDEV_LOGLEVELS.INFO,
      'testFunction',
      'File flush test',
      PEER_SERVICES.INTERNAL,
      { data: 'test' },
      null
    );

    await sovdevFlush();
    await new Promise(resolve => setTimeout(resolve, 200));

    // Check file was created and contains log
    const logFilePath = path.join(testLogsDir, 'test.log');
    assert.ok(fs.existsSync(logFilePath), 'Log file should exist');

    const content = fs.readFileSync(logFilePath, 'utf-8');
    assert.ok(content.includes('File flush test'), 'Flushed log should be in file');
  });

  it('should flush multiple logs in batch', async () => {
    const PEER_SERVICES = createPeerServices({});

    sovdevInitialize('test-batch-flush');

    // Log multiple entries rapidly
    for (let i = 0; i < 10; i++) {
      sovdevLog(
        SOVDEV_LOGLEVELS.INFO,
        'batchFunction',
        `Batch log ${i}`,
        PEER_SERVICES.INTERNAL,
        null,
        null
      );
    }

    await sovdevFlush();
    await new Promise(resolve => setTimeout(resolve, 200));

    const output = consoleOutput.join('');
    // Verify at least first and last
    assert.ok(output.includes('Batch log 0'), 'Should flush first log');
    assert.ok(output.includes('Batch log 9'), 'Should flush last log');
  });

  it('should handle flush with no pending logs', async () => {
    sovdevInitialize('test-empty-flush');

    // Flush without any logs
    await sovdevFlush();
    await new Promise(resolve => setTimeout(resolve, 100));

    // Should not crash or error
    assert.ok(true, 'Empty flush should succeed gracefully');
  });

  it('should flush different log levels correctly', async () => {
    const PEER_SERVICES = createPeerServices({});

    sovdevInitialize('test-levels-flush');

    sovdevLog(SOVDEV_LOGLEVELS.DEBUG, 'fn', 'Debug log', PEER_SERVICES.INTERNAL, null, null);
    sovdevLog(SOVDEV_LOGLEVELS.INFO, 'fn', 'Info log', PEER_SERVICES.INTERNAL, null, null);
    sovdevLog(SOVDEV_LOGLEVELS.WARN, 'fn', 'Warn log', PEER_SERVICES.INTERNAL, null, null);
    sovdevLog(SOVDEV_LOGLEVELS.ERROR, 'fn', 'Error log', PEER_SERVICES.INTERNAL, null, null);

    await sovdevFlush();
    await new Promise(resolve => setTimeout(resolve, 200));

    const output = consoleOutput.join('');
    assert.ok(output.includes('Debug log'), 'Should flush DEBUG');
    assert.ok(output.includes('Info log'), 'Should flush INFO');
    assert.ok(output.includes('Warn log'), 'Should flush WARN');
    assert.ok(output.includes('Error log'), 'Should flush ERROR');
  });

  it('should handle sequential flush calls', async () => {
    const PEER_SERVICES = createPeerServices({});

    sovdevInitialize('test-sequential-flush');

    // First batch
    sovdevLog(SOVDEV_LOGLEVELS.INFO, 'fn', 'First batch', PEER_SERVICES.INTERNAL, null, null);
    await sovdevFlush();
    await new Promise(resolve => setTimeout(resolve, 100));

    // Second batch
    sovdevLog(SOVDEV_LOGLEVELS.INFO, 'fn', 'Second batch', PEER_SERVICES.INTERNAL, null, null);
    await sovdevFlush();
    await new Promise(resolve => setTimeout(resolve, 100));

    const output = consoleOutput.join('');
    assert.ok(output.includes('First batch'), 'Should flush first batch');
    assert.ok(output.includes('Second batch'), 'Should flush second batch');
  });
});
