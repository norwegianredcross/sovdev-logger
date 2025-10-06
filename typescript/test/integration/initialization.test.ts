/**
 * Integration Tests: Initialization Flow
 *
 * Tests the sovdevInitialize() function with different configurations
 * and environment variables. Verifies proper setup of service context.
 */

import { describe, it, beforeEach, afterEach } from 'node:test';
import assert from 'node:assert';
import { sovdevInitialize, sovdevLog, sovdevFlush, SOVDEV_LOGLEVELS, createPeerServices } from '../../dist/index.js';

describe('Initialization Flow Integration', () => {
  const originalEnv = process.env.NODE_ENV;
  let consoleOutput: string[] = [];
  let originalStdoutWrite: typeof process.stdout.write;

  beforeEach(() => {
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
    process.env.NODE_ENV = originalEnv;
    process.stdout.write = originalStdoutWrite;
    await sovdevFlush();
  });

  it('should initialize with only service name', async () => {
    const PEER_SERVICES = createPeerServices({});

    sovdevInitialize('test-minimal-service');

    sovdevLog(
      SOVDEV_LOGLEVELS.INFO,
      'testFunction',
      'Minimal initialization',
      PEER_SERVICES.INTERNAL,
      null,
      null
    );

    await sovdevFlush();
    await new Promise(resolve => setTimeout(resolve, 100));

    const output = consoleOutput.join('');
    assert.ok(output.includes('test-minimal-service'), 'Should include service name');
  });

  it('should initialize with service name and version', async () => {
    const PEER_SERVICES = createPeerServices({});

    sovdevInitialize('test-versioned-service', '2.5.3');

    sovdevLog(
      SOVDEV_LOGLEVELS.INFO,
      'testFunction',
      'Version test',
      PEER_SERVICES.INTERNAL,
      null,
      null
    );

    await sovdevFlush();
    await new Promise(resolve => setTimeout(resolve, 100));

    const output = consoleOutput.join('');
    assert.ok(output.includes('test-versioned-service'), 'Should include service name');
    assert.ok(output.includes('2.5.3'), 'Should include version');
  });

  it('should initialize with peer service mappings', async () => {
    const PEER_SERVICES = createPeerServices({
      EXTERNAL_API: 'SYS1234567',
      DATABASE: 'INT0000001'
    });

    sovdevInitialize('test-peer-service', '1.0.0', PEER_SERVICES.mappings);

    sovdevLog(
      SOVDEV_LOGLEVELS.INFO,
      'dbQuery',
      'Database operation',
      PEER_SERVICES.DATABASE,
      { query: 'SELECT * FROM users' },
      { rows: 42 }
    );

    await sovdevFlush();
    await new Promise(resolve => setTimeout(resolve, 100));

    const output = consoleOutput.join('');
    assert.ok(output.includes('Database operation'), 'Should include log message');
  });

  it('should handle multiple initializations gracefully', async () => {
    const PEER_SERVICES = createPeerServices({});

    // Initialize multiple times (should use latest)
    sovdevInitialize('service-v1', '1.0.0');
    sovdevInitialize('service-v2', '2.0.0');
    sovdevInitialize('service-v3', '3.0.0');

    sovdevLog(
      SOVDEV_LOGLEVELS.INFO,
      'testFunction',
      'After multiple inits',
      PEER_SERVICES.INTERNAL,
      null,
      null
    );

    await sovdevFlush();
    await new Promise(resolve => setTimeout(resolve, 100));

    const output = consoleOutput.join('');
    // Should use the last initialization
    assert.ok(output.includes('After multiple inits'), 'Should log successfully');
  });

  it('should work with environment-based OTLP endpoint', async () => {
    const PEER_SERVICES = createPeerServices({});

    // Set OTLP endpoint (will try to connect but that's ok for test)
    process.env.OTEL_EXPORTER_OTLP_LOGS_ENDPOINT = 'http://localhost:4318/v1/logs';

    sovdevInitialize('test-otlp-service');

    sovdevLog(
      SOVDEV_LOGLEVELS.INFO,
      'testFunction',
      'OTLP endpoint test',
      PEER_SERVICES.INTERNAL,
      null,
      null
    );

    await sovdevFlush();
    await new Promise(resolve => setTimeout(resolve, 100));

    // Should still log to console even with OTLP configured
    const output = consoleOutput.join('');
    assert.ok(output.includes('OTLP endpoint test'), 'Should still log to console');

    delete process.env.OTEL_EXPORTER_OTLP_LOGS_ENDPOINT;
  });
});
