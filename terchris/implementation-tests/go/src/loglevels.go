package sovdevlogger

// SovdevLogLevel represents valid log levels
type SovdevLogLevel string

// SOVDEV_LOGLEVELS defines the standard log levels
// These match OpenTelemetry severity numbers:
// TRACE=1, DEBUG=5, INFO=9, WARN=13, ERROR=17, FATAL=21
var SOVDEV_LOGLEVELS = struct {
	TRACE SovdevLogLevel
	DEBUG SovdevLogLevel
	INFO  SovdevLogLevel
	WARN  SovdevLogLevel
	ERROR SovdevLogLevel
	FATAL SovdevLogLevel
}{
	TRACE: "trace",
	DEBUG: "debug",
	INFO:  "info",
	WARN:  "warn",
	ERROR: "error",
	FATAL: "fatal",
}

// mapToSeverityNumber maps log levels to OpenTelemetry severity numbers
func mapToSeverityNumber(level SovdevLogLevel) int {
	switch level {
	case SOVDEV_LOGLEVELS.TRACE:
		return 1
	case SOVDEV_LOGLEVELS.DEBUG:
		return 5
	case SOVDEV_LOGLEVELS.INFO:
		return 9
	case SOVDEV_LOGLEVELS.WARN:
		return 13
	case SOVDEV_LOGLEVELS.ERROR:
		return 17
	case SOVDEV_LOGLEVELS.FATAL:
		return 21
	default:
		return 9 // Default to INFO
	}
}

// mapToSeverityText converts log level to uppercase for OpenTelemetry
func mapToSeverityText(level SovdevLogLevel) string {
	switch level {
	case SOVDEV_LOGLEVELS.TRACE:
		return "TRACE"
	case SOVDEV_LOGLEVELS.DEBUG:
		return "DEBUG"
	case SOVDEV_LOGLEVELS.INFO:
		return "INFO"
	case SOVDEV_LOGLEVELS.WARN:
		return "WARN"
	case SOVDEV_LOGLEVELS.ERROR:
		return "ERROR"
	case SOVDEV_LOGLEVELS.FATAL:
		return "FATAL"
	default:
		return "INFO"
	}
}
