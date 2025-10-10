#!/bin/bash

# Load .env file if it exists (but exclude OTEL_EXPORTER_OTLP_HEADERS which needs special handling)
if [ -f .env ]; then
  echo "Loading environment variables from .env file..."
  # Export variables from .env (exclude comments, blank lines, and OTEL_EXPORTER_OTLP_HEADERS)
  export $(grep -v '^#' .env | grep -v '^$' | grep -v '^OTEL_EXPORTER_OTLP_HEADERS=' | xargs)
fi

# Run the company lookup example with OTLP configuration
# OTEL_EXPORTER_OTLP_HEADERS must be set directly because JSON in .env files gets mangled by export
OTEL_EXPORTER_OTLP_HEADERS='{"Host":"otel.localhost"}' \
python3 company-lookup.py
