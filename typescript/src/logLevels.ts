/**
 * Sovdev Logger - Log Levels
 *
 * Standard log levels following "Loggeloven av 2025" requirements
 * ERROR and FATAL levels trigger ServiceNow incidents
 */

export const SOVDEV_LOGLEVELS = {
  TRACE: 'trace', // Detailed trace information (very verbose)
  DEBUG: 'debug', // Debug information for development
  INFO: 'info', // Informational messages
  WARN: 'warn', // Warning messages (potential issues)
  ERROR: 'error', // Error messages (triggers ServiceNow incident)
  FATAL: 'fatal', // Fatal errors (triggers ServiceNow incident)
} as const;

export type sovdev_log_level = (typeof SOVDEV_LOGLEVELS)[keyof typeof SOVDEV_LOGLEVELS];
