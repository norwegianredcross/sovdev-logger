/**
 * Test using SYSTEM_ID environment variable instead of parameter
 */

import {
  initializeSovdevLogger,
  sovdevLog,
  flushSovdevLogs,
  SOVDEV_LOGLEVELS,
  createPeerServices
} from '../../dist/index.js';

// Define peer services - INTERNAL is auto-generated (no external systems in this simple example)
const PEER_SERVICES = createPeerServices({});

async function main() {
  const FUNCTIONNAME = 'main';

  // No parameter - will use SYSTEM_ID env var
  initializeSovdevLogger();

  sovdevLog(
    SOVDEV_LOGLEVELS.INFO,
    FUNCTIONNAME,
    'Using SYSTEM_ID from environment variable',
    PEER_SERVICES.INTERNAL
  );

  await flushSovdevLogs();
}

main().catch(async (error) => {
  console.error('Error:', error.message);
  await flushSovdevLogs();
  process.exit(1);
});
