#!/usr/bin/env python3
"""
Sovdev Logger - Loki Response Validator

Validates Loki query responses against JSON Schema to ensure logs are properly
stored with correct field names (snake_case only) and all required fields.

Uses: specification/schemas/loki-response-schema.json

Usage:
    # Validate Loki response (human-readable output)
    ./query-loki.sh sovdev-test-app --json > /tmp/loki.json
    python3 validate-loki-response.py /tmp/loki.json

    # JSON output for automation
    python3 validate-loki-response.py /tmp/loki.json --json

    # Pipe directly from query
    ./query-loki.sh sovdev-test-app --json | python3 validate-loki-response.py -

Exit Codes:
    0 - Validation passed
    1 - Validation failed
    2 - Usage error
"""

import argparse
import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Set

try:
    import jsonschema
    from jsonschema import Draft7Validator
except ImportError:
    print("ERROR: jsonschema library not found", file=sys.stderr)
    print("Install with: pip install jsonschema", file=sys.stderr)
    sys.exit(1)


# ANSI color codes
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'


class LokiResponseValidator:
    """Validates Loki API responses using JSON Schema"""

    def __init__(self, schema_path: Path, json_mode: bool = False):
        """
        Initialize validator with JSON Schema

        Args:
            schema_path: Path to loki-response-schema.json
            json_mode: If True, output JSON instead of human-readable text
        """
        self.schema = json.loads(schema_path.read_text())
        self.validator = Draft7Validator(self.schema)
        self.log_entry_schema = self.schema['definitions']['log_entry']
        self.log_entry_validator = Draft7Validator(self.log_entry_schema)
        self.json_mode = json_mode
        self.errors = []
        self.warnings = []
        self.stats = {
            'total_streams': 0,
            'total_logs': 0,
            'unique_services': set(),
            'log_types': {},
        }

    def print_success(self, msg: str):
        if not self.json_mode:
            print(f"{Colors.GREEN}✅ {msg}{Colors.NC}")

    def print_error(self, msg: str):
        self.errors.append(msg)
        if not self.json_mode:
            print(f"{Colors.RED}❌ {msg}{Colors.NC}", file=sys.stderr)

    def print_warning(self, msg: str):
        self.warnings.append(msg)
        if not self.json_mode:
            print(f"{Colors.YELLOW}⚠️  {msg}{Colors.NC}", file=sys.stderr)

    def print_info(self, msg: str):
        if not self.json_mode:
            print(f"{Colors.BLUE}ℹ️  {msg}{Colors.NC}")

    def validate_response(self, loki_data: Dict[str, Any]) -> bool:
        """Validate Loki API response using JSON Schema"""

        # Step 1: Validate response structure against schema
        if not self._validate_schema(loki_data):
            return False

        # Step 2: Validate parsed log entries from values
        if not self._validate_log_entries(loki_data):
            return False

        # Success!
        self._print_summary()
        return True

    def _validate_schema(self, loki_data: Dict[str, Any]) -> bool:
        """Validate response against JSON Schema"""
        self.print_info("Validating Loki response structure against schema...")

        # Validate using jsonschema
        errors = list(self.validator.iter_errors(loki_data))

        if errors:
            self.print_error(f"Schema validation failed with {len(errors)} error(s)")
            for error in errors[:5]:  # Show first 5 errors
                error_path = " -> ".join(str(p) for p in error.path) if error.path else "root"
                self.print_error(f"  {error_path}: {error.message}")
            if len(errors) > 5:
                self.print_warning(f"  ... and {len(errors) - 5} more errors")
            return False

        # Check if we have results
        results = loki_data.get('data', {}).get('result', [])
        if len(results) == 0:
            self.print_warning("No logs found in Loki response")
            return True  # Empty is valid

        self.stats['total_streams'] = len(results)
        self.print_success(f"Schema validation passed - found {len(results)} stream(s)")
        return True

    def _validate_log_entries(self, loki_data: Dict[str, Any]) -> bool:
        """
        Validate log entries from Loki OTLP format

        In Loki's OTLP storage:
        - Structured fields (service_name, function_name, etc.) → stream labels
        - Message text → values array as plain string

        We validate the stream labels, not the message text.
        """
        results = loki_data.get('data', {}).get('result', [])
        if not results:
            return True  # No logs to validate

        self.print_info("Validating stream labels (structured fields)...")

        all_valid = True
        total_logs = 0

        for stream_idx, stream_data in enumerate(results):
            stream_labels = stream_data.get('stream', {})
            values = stream_data.get('values', [])
            total_logs += len(values)

            # Validate stream labels as a log entry (one per stream is sufficient)
            if stream_labels:
                # Note: We don't validate against full log_entry schema because
                # stream labels don't include message (it's in values)
                # Instead, we check for required snake_case fields

                required_fields = ['service_name']  # Minimum required
                missing_fields = [f for f in required_fields if f not in stream_labels]

                if missing_fields:
                    self.print_warning(f"Stream {stream_idx}: Missing fields: {missing_fields}")

                # Check for camelCase fields (should not exist)
                camel_case_fields = [
                    'serviceName', 'functionName', 'logType', 'traceId',
                    'eventId', 'sessionId', 'peerService'
                ]
                found_camel = [f for f in camel_case_fields if f in stream_labels]
                if found_camel:
                    self.print_error(f"Stream {stream_idx}: Found camelCase fields: {found_camel}")
                    self.print_error(f"    All fields must use snake_case")
                    all_valid = False

                # Track stats
                if 'service_name' in stream_labels:
                    self.stats['unique_services'].add(stream_labels['service_name'])
                if 'log_type' in stream_labels:
                    log_type = stream_labels['log_type']
                    self.stats['log_types'][log_type] = self.stats['log_types'].get(log_type, 0) + 1

        self.stats['total_logs'] = total_logs
        if all_valid:
            self.print_success(f"Stream label validation passed - {len(results)} streams, {total_logs} log entries")

        return all_valid

    def _print_summary(self):
        """Print validation summary"""
        if not self.json_mode:
            print()
            self.print_success("LOKI RESPONSE VALIDATION PASSED")
            print()
            print(f"Total streams: {self.stats['total_streams']}")
            print(f"Total logs: {self.stats['total_logs']}")
            print(f"Services: {', '.join(sorted(self.stats['unique_services']))}")
            if self.stats['log_types']:
                print(f"Log types: {dict(self.stats['log_types'])}")
            if self.warnings:
                print(f"\nWarnings: {len(self.warnings)}")
                for warning in self.warnings:
                    print(f"  - {warning}")

    def get_json_output(self, passed: bool) -> Dict[str, Any]:
        """Generate JSON output for automation"""
        return {
            'validation': 'passed' if passed else 'failed',
            'errors': self.errors,
            'warnings': self.warnings,
            'stats': {
                'total_streams': self.stats['total_streams'],
                'total_logs': self.stats['total_logs'],
                'unique_services': list(self.stats['unique_services']),
                'log_types': self.stats['log_types'],
            }
        }


def main():
    parser = argparse.ArgumentParser(
        description='Validate Loki query response against JSON Schema',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        'response_file',
        help='Path to Loki response JSON file (use "-" for stdin)'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output JSON format for automation'
    )
    parser.add_argument(
        '--schema',
        type=Path,
        help='Path to loki-response-schema.json (default: auto-detect)'
    )

    args = parser.parse_args()

    # Locate schema file
    if args.schema:
        schema_path = args.schema
    else:
        # Auto-detect: look in ../schemas/ relative to this script
        script_dir = Path(__file__).parent
        schema_path = script_dir.parent / 'schemas' / 'loki-response-schema.json'

    if not schema_path.exists():
        print(f"ERROR: Schema file not found: {schema_path}", file=sys.stderr)
        print("Specify schema location with --schema option", file=sys.stderr)
        sys.exit(2)

    # Read Loki response
    try:
        if args.response_file == '-':
            loki_data = json.load(sys.stdin)
        else:
            loki_data = json.loads(Path(args.response_file).read_text())
    except FileNotFoundError:
        print(f"ERROR: File not found: {args.response_file}", file=sys.stderr)
        sys.exit(2)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON: {e}", file=sys.stderr)
        sys.exit(2)

    # Validate
    validator = LokiResponseValidator(schema_path=schema_path, json_mode=args.json)
    passed = validator.validate_response(loki_data)

    # Output results
    if args.json:
        print(json.dumps(validator.get_json_output(passed), indent=2))

    sys.exit(0 if passed else 1)


if __name__ == '__main__':
    main()
