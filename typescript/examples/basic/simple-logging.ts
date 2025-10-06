/**
 * Basic Example - Simple Logging with Sovdev Logger
 *
 * This example demonstrates the basic usage of the sovdev-logger library
 * with minimal configuration.
 */

import {
  sovdevInitialize,
  sovdevLog,
  sovdevFlush,
  SOVDEV_LOGLEVELS,
  createPeerServices
} from '../../dist/index.js';

// Define peer services - INTERNAL is auto-generated (no external systems in this simple example)
const PEER_SERVICES = createPeerServices({});

async function main() {
  const FUNCTIONNAME = 'main';

  // Step 1: Initialize the logger with your system ID
  sovdevInitialize('basic-example');

  // Step 2: Log at different levels
  sovdevLog(
    SOVDEV_LOGLEVELS.INFO,
    FUNCTIONNAME,
    'Application started',
    PEER_SERVICES.INTERNAL
  );

  const debugInput = { debugData: 'some debug context' };
  sovdevLog(
    SOVDEV_LOGLEVELS.DEBUG,
    FUNCTIONNAME,
    'Debug information',
    PEER_SERVICES.INTERNAL,
    debugInput
  );

  const warnInput = { warningReason: 'demonstration' };
  sovdevLog(
    SOVDEV_LOGLEVELS.WARN,
    FUNCTIONNAME,
    'This is a warning',
    PEER_SERVICES.INTERNAL,
    warnInput
  );

  // Step 3: Log with input and response
  const input = { userId: '12345', action: 'getData' };
  const response = { status: 'success', data: ['item1', 'item2'] };

  sovdevLog(
    SOVDEV_LOGLEVELS.INFO,
    'processRequest',
    'Request processed successfully',
    PEER_SERVICES.INTERNAL,
    input,
    response
  );

  // Step 4: Log an error with exception
  try {
    throw new Error('Demonstration error');
  } catch (error) {
    const errorInput = { context: 'error handling demo' };
    sovdevLog(
      SOVDEV_LOGLEVELS.ERROR,
      FUNCTIONNAME,
      'An error occurred',
      PEER_SERVICES.INTERNAL,
      errorInput,
      null,
      error
    );
  }

  sovdevLog(
    SOVDEV_LOGLEVELS.INFO,
    FUNCTIONNAME,
    'Application finished',
    PEER_SERVICES.INTERNAL
  );

  // Step 5: Flush logs before exit
  // CRITICAL: OpenTelemetry batches logs for performance.
  // Without flushing, logs still in the batch buffer will be lost when the app exits.
  // This ensures all logs (especially the last ones) reach the OTLP collector.
  await sovdevFlush();
}

main().catch(console.error);
