/**
 * Sovdev Logger - Main Export File
 *
 * Structured logging library for OpenTelemetry with "Loggeloven av 2025" compliance
 *
 * @packageDocumentation
 */

// Export main logging functions (with sovdev* prefix for consistency)
export {
  sovdevInitialize,
  sovdevFlush,
  sovdevGenerateTraceId,
  sovdevLog,
  sovdevLogJobStatus,
  sovdevLogJobProgress
} from './logger';

// Export log levels
export { SOVDEV_LOGLEVELS } from './logLevels';

// Export peer service helper
export { createPeerServices } from './peerServices';

// Export TypeScript types
export type { SovdevLogLevel } from './logLevels';
export type { StructuredLogEntry } from './logger';
