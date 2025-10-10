"""
Advanced Example - Company Lookup Service

This example demonstrates advanced features of sovdev-logger including:
- Job status tracking
- Progress logging for batch operations
- Error handling with retry logic
- Real API integration (Norwegian company registry)
"""

import os
import sys
import time
import urllib.request
import json as json_module
from typing import Optional, Dict, Any

from sovdev_logger import (
    sovdev_initialize,
    sovdev_log,
    sovdev_flush,
    sovdev_generate_trace_id,
    sovdev_log_job_status,
    sovdev_log_job_progress,
    SOVDEV_LOGLEVELS,
    create_peer_services
)

# Define peer services - INTERNAL is auto-generated
PEER_SERVICES = create_peer_services({
    'BRREG': 'SYS1234567'  # External system (Norwegian company registry)
})


def fetch_company_data(org_number: str) -> Dict[str, Any]:
    """
    Fetch company data from Brønnøysund Registry
    """
    url = f"https://data.brreg.no/enhetsregisteret/api/enheter/{org_number}"

    try:
        with urllib.request.urlopen(url) as response:
            if response.status == 200:
                data = response.read().decode('utf-8')
                return json_module.loads(data)
            else:
                raise Exception(f"HTTP {response.status}:")
    except urllib.error.HTTPError as e:
        # Match TypeScript error format: "HTTP {status_code}:"
        raise Exception(f"HTTP {e.code}:")
    except Exception as e:
        raise


def lookup_company(org_number: str, trace_id: Optional[str] = None) -> None:
    """
    Process a single company lookup with logging
    """
    FUNCTIONNAME = 'lookupCompany'
    txn_trace_id = trace_id or sovdev_generate_trace_id()  # Use provided or generate new
    input_data = {'organisasjonsnummer': org_number}

    sovdev_log(
        SOVDEV_LOGLEVELS.INFO,
        FUNCTIONNAME,
        f'Looking up company {org_number}',
        PEER_SERVICES.BRREG,
        input_json=input_data,
        trace_id=txn_trace_id  # Same traceId for related logs
    )

    try:
        company_data = fetch_company_data(org_number)
        response = {
            'navn': company_data['navn'],
            'organisasjonsform': company_data.get('organisasjonsform', {}).get('beskrivelse')
        }

        sovdev_log(
            SOVDEV_LOGLEVELS.INFO,
            FUNCTIONNAME,
            f"Company found: {company_data['navn']}",
            PEER_SERVICES.BRREG,
            input_json=input_data,
            response_json=response,
            trace_id=txn_trace_id  # SAME traceId links request and response
        )
    except Exception as error:
        sovdev_log(
            SOVDEV_LOGLEVELS.ERROR,
            FUNCTIONNAME,
            f'Failed to lookup company {org_number}',
            PEER_SERVICES.BRREG,
            input_json=input_data,
            exception_object=error,
            trace_id=txn_trace_id  # SAME traceId for error
        )


def batch_lookup(org_numbers: list[str]) -> None:
    """
    Batch process multiple companies with progress tracking
    """
    job_name = 'CompanyLookupBatch'
    FUNCTIONNAME = 'batchLookup'
    batch_trace_id = sovdev_generate_trace_id()  # Generate ONE traceId for entire batch job
    job_start_input = {'totalCompanies': len(org_numbers)}

    # Log job start - internal job
    sovdev_log_job_status(
        SOVDEV_LOGLEVELS.INFO,
        FUNCTIONNAME,
        job_name,
        'Started',
        PEER_SERVICES.INTERNAL,
        job_start_input,
        batch_trace_id  # All job logs share this traceId
    )

    successful = 0
    failed = 0

    # Process each company
    for i, org_number in enumerate(org_numbers):
        item_trace_id = sovdev_generate_trace_id()  # Generate unique traceId for each company lookup
        progress_input = {'organisasjonsnummer': org_number}

        # Log progress - tracking BRREG processing
        sovdev_log_job_progress(
            SOVDEV_LOGLEVELS.INFO,
            FUNCTIONNAME,
            org_number,
            i + 1,
            len(org_numbers),
            PEER_SERVICES.BRREG,
            progress_input,
            batch_trace_id  # Progress logs use batch traceId
        )

        try:
            lookup_company(org_number, item_trace_id)  # Pass itemTraceId to link request/response
            successful += 1
        except Exception as error:
            failed += 1
            error_input = {'organisasjonsnummer': org_number, 'itemNumber': i + 1}
            sovdev_log(
                SOVDEV_LOGLEVELS.ERROR,
                FUNCTIONNAME,
                f'Batch item {i + 1} failed',
                PEER_SERVICES.BRREG,
                input_json=error_input,
                exception_object=error,
                trace_id=item_trace_id  # Error uses same itemTraceId
            )

        # Small delay to avoid rate limiting
        time.sleep(0.1)

    # Log job completion - internal job
    job_complete_input = {
        'totalCompanies': len(org_numbers),
        'successful': successful,
        'failed': failed,
        'successRate': f"{round((successful / len(org_numbers)) * 100)}%"
    }
    sovdev_log_job_status(
        SOVDEV_LOGLEVELS.INFO,
        FUNCTIONNAME,
        job_name,
        'Completed',
        PEER_SERVICES.INTERNAL,
        job_complete_input,
        batch_trace_id  # Completion uses batch traceId
    )


def main():
    FUNCTIONNAME = 'main'

    # Initialize logger with service info and system mapping
    # Use SYSTEM_ID env var (e.g., "sovdev-test-company-lookup-python") or default
    system_id = os.environ.get('SYSTEM_ID', 'company-lookup-service')

    sovdev_initialize(
        system_id,
        "1.0.0",
        PEER_SERVICES.mappings
    )

    sovdev_log(
        SOVDEV_LOGLEVELS.INFO,
        FUNCTIONNAME,
        'Company Lookup Service started',
        PEER_SERVICES.INTERNAL
    )

    # Example: Norwegian Red Cross and related organizations
    companies = [
        '971277882',  # Norges Røde Kors (Norwegian Red Cross)
        '915933149',  # Røde Kors Hjelpekorps
        '974652846',  # Invalid number (will cause error for demonstration)
        '916201478'   # Norsk Folkehjelp
    ]

    batch_lookup(companies)

    sovdev_log(
        SOVDEV_LOGLEVELS.INFO,
        FUNCTIONNAME,
        'Company Lookup Service finished',
        PEER_SERVICES.INTERNAL
    )

    # Flush logs before exit
    # CRITICAL: OpenTelemetry batches logs for performance. Without flushing,
    # the final batch of logs (including job completion status) will be lost
    # when the application exits. This ensures all logs reach the OTLP collector.
    sovdev_flush()


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print(f'Fatal error: {error}', file=sys.stderr)
        # IMPORTANT: Flush logs even on error to ensure error logs are sent!
        sovdev_flush()
        sys.exit(1)
