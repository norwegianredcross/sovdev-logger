/**
 * Sovdev Logger - Main Export File
 *
 * Structured logging library for OpenTelemetry with "Loggeloven av 2025" compliance
 *
 * @packageDocumentation
 */

// Export main logging functions (with sovdev_ prefix for consistency with Python implementation)
export {
  sovdev_initialize,
  sovdev_flush,
  sovdev_log,
  sovdev_log_job_status,
  sovdev_log_job_progress
} from './logger';

// Export log levels
export { SOVDEV_LOGLEVELS } from './logLevels';

// Export peer service helper
export { create_peer_services } from './peerServices';

// Export TypeScript types
export type { SovdevLogLevel } from './logLevels';
export type { StructuredLogEntry } from './logger';
