/**
 * Test script for DevContainer environment
 * Tests logging from devcontainer to host Kubernetes cluster
 */

import { sovdevInitialize, sovdevLog, sovdevFlush, SOVDEV_LOGLEVELS, createPeerServices } from './src/index';

// Set environment variables for host.docker.internal networking
process.env.OTEL_EXPORTER_OTLP_LOGS_ENDPOINT = 'http://host.docker.internal/v1/logs';
process.env.OTEL_EXPORTER_OTLP_METRICS_ENDPOINT = 'http://host.docker.internal/v1/metrics';
process.env.OTEL_EXPORTER_OTLP_TRACES_ENDPOINT = 'http://host.docker.internal/v1/traces';
process.env.OTEL_EXPORTER_OTLP_HEADERS = JSON.stringify({ Host: 'otel.localhost' });

const PEER_SERVICES = createPeerServices({});

async function main() {
  console.log('🚀 Starting DevContainer logging test...');
  console.log('📍 Environment: DevContainer');
  console.log('🌐 Host: host.docker.internal');
  console.log('🎯 Target: Kubernetes cluster on host (via Traefik)');
  console.log('');

  // Initialize logger
  sovdevInitialize('sovdev-test-devcontainer');

  // Test different log levels
  sovdevLog(
    SOVDEV_LOGLEVELS.DEBUG,
    'main',
    'Debug message from devcontainer',
    PEER_SERVICES.INTERNAL,
    { test: 'debug' }
  );

  sovdevLog(
    SOVDEV_LOGLEVELS.INFO,
    'main',
    'Info message from devcontainer',
    PEER_SERVICES.INTERNAL,
    { test: 'info', timestamp: new Date().toISOString() }
  );

  sovdevLog(
    SOVDEV_LOGLEVELS.WARN,
    'main',
    'Warning message from devcontainer',
    PEER_SERVICES.INTERNAL,
    { test: 'warn' }
  );

  sovdevLog(
    SOVDEV_LOGLEVELS.ERROR,
    'main',
    'Error message from devcontainer',
    PEER_SERVICES.INTERNAL,
    { test: 'error', code: 'TEST_ERROR' }
  );

  // Test with structured data
  sovdevLog(
    SOVDEV_LOGLEVELS.INFO,
    'main',
    'Structured log from devcontainer',
    PEER_SERVICES.INTERNAL,
    {
      user: 'devcontainer-tester',
      action: 'test_logging',
      environment: 'devcontainer',
      host_gateway: 'host.docker.internal',
      metadata: {
        nodeVersion: process.version,
        platform: process.platform,
        architecture: process.arch
      }
    }
  );

  console.log('');
  console.log('✅ Test complete! Check Grafana for logs:');
  console.log('   http://grafana.localhost');
  console.log('   Filter: service_name="sovdev-test-devcontainer"');

  // Give time for logs to flush
  await new Promise(resolve => setTimeout(resolve, 2000));

  await sovdevFlush();
  console.log('🛑 Logger flushed and shutdown complete');
}

main().catch(error => {
  console.error('❌ Test failed:', error);
  process.exit(1);
});
