"""
============================================================================
Company-Lookup E2E Test Application - Python Implementation
============================================================================

PURPOSE:
This is the **Python implementation** of the reference E2E test for sovdev-logger.
It demonstrates ALL 8 core API functions and matches the TypeScript reference implementation.

TEST SCENARIO:
Simulates a real-world batch processing service that:
1. Looks up Norwegian companies from the Brønnøysund Registry (BRREG)
2. Processes multiple companies in a batch
3. Tracks job progress and handles errors
4. Demonstrates transaction correlation via explicit trace IDs

CROSS-LANGUAGE REQUIREMENTS:
This Python implementation MUST produce identical output to TypeScript version.
============================================================================
"""

import asyncio
import os
import sys
import time
from typing import Dict, Any

import requests
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

# Import sovdev-logger API functions
from src.sovdev_logger import (
    sovdev_initialize,         # Function 1: Initialize logger with service info
    sovdev_log,                # Function 2: General logging (transactions, errors, etc.)
    sovdev_log_job_status,     # Function 3: Job lifecycle (started/completed)
    sovdev_log_job_progress,   # Function 4: Progress tracking (items in batch)
    sovdev_flush,              # Function 5: Flush OTLP batches before exit
    sovdev_generate_trace_id,  # Function 6: Generate trace ID for correlation
    SOVDEV_LOGLEVELS,          # Function 7: Log level constants (INFO, ERROR, etc.)
    create_peer_services       # Function 8: Create peer service mappings
)

# Load environment variables from .env file
load_dotenv()

# ============================================================================
# PEER SERVICES - External System Mapping (CMDB Integration)
# ============================================================================
PEER_SERVICES = create_peer_services({
    'BRREG': 'SYS1234567'  # Norwegian company registry (Brønnøysundregistrene)
    # INTERNAL is auto-generated
})


# ============================================================================
# HELPER FUNCTION - Fetch Company Data from External API
# ============================================================================
def fetch_company_data(org_number: str) -> Dict[str, Any]:
    """
    Make HTTP call to Norwegian company registry.
    This is a helper function, NOT a sovdev-logger demonstration.
    """
    url = f'https://data.brreg.no/enhetsregisteret/api/enheter/{org_number}'

    response = requests.get(url, timeout=10)

    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f'HTTP {response.status_code}: {response.text}')


# ============================================================================
# FUNCTION: lookup_company - Single Company Lookup with Transaction Correlation
# ============================================================================
def lookup_company(org_number: str) -> None:
    """
    DEMONSTRATES: sovdev_log() with explicit trace_id correlation

    LOG ENTRIES GENERATED:
    - 1x INFO log: "Looking up company..." (transaction start, input only)
    - 1x INFO log: "Company found..." (transaction success, input + response)
    OR
    - 1x ERROR log: "Failed to lookup..." (transaction failure, input + exception)
    """
    # PATTERN: Define FUNCTIONNAME constant to avoid typos in log calls
    FUNCTIONNAME = 'lookup_company'

    # PATTERN: Define input object once, reuse in all log calls
    input_data = {'organisasjonsnummer': org_number}

    # ============================================================================
    # TRANSACTION CORRELATION - Generate Trace ID
    # ============================================================================
    trace_id = sovdev_generate_trace_id()

    try:
        # ========================================================================
        # LOG #1: Transaction Start - Before External API Call
        # ========================================================================
        sovdev_log(
            SOVDEV_LOGLEVELS.INFO,
            FUNCTIONNAME,
            f'Looking up company {org_number}',
            PEER_SERVICES.BRREG,
            input_data,
            None,      # No response yet
            None,      # No exception
            trace_id   # CRITICAL: Same trace_id for correlation
        )

        # Call external API (not logged - helper function)
        company_data = fetch_company_data(org_number)

        # Prepare response object for logging
        response = {
            'navn': company_data.get('navn'),
            'organisasjonsform': company_data.get('organisasjonsform', {}).get('beskrivelse')
        }

        # ========================================================================
        # LOG #2: Transaction Success - After External API Call
        # ========================================================================
        sovdev_log(
            SOVDEV_LOGLEVELS.INFO,
            FUNCTIONNAME,
            f'Company found: {company_data.get("navn")}',
            PEER_SERVICES.BRREG,
            input_data,
            response,
            None,      # No exception
            trace_id   # CRITICAL: SAME trace_id links this log to start log
        )

    except Exception as error:
        # ========================================================================
        # LOG #3: Transaction Error - API Call Failed
        # ========================================================================
        sovdev_log(
            SOVDEV_LOGLEVELS.ERROR,
            FUNCTIONNAME,
            f'Failed to lookup company {org_number}',
            PEER_SERVICES.BRREG,
            input_data,
            None,
            error,
            trace_id   # CRITICAL: SAME trace_id shows this error belongs to this transaction
        )

        # Re-raise to propagate error to caller
        raise


# ============================================================================
# FUNCTION: batch_lookup - Batch Processing with Job Tracking
# ============================================================================
def batch_lookup(org_numbers: list) -> None:
    """
    DEMONSTRATES: sovdev_log_job_status() and sovdev_log_job_progress()

    LOG ENTRIES GENERATED (for 4 companies):
    - 1x job.status log: "Started" (log_type: job.status)
    - 4x job.progress logs: One per company (log_type: job.progress)
    - 2x transaction logs per company (from lookup_company): start + success/error
    - 1x error log: For the invalid company number (974652846)
    - 1x job.status log: "Completed" with summary statistics
    """
    job_name = 'CompanyLookupBatch'
    FUNCTIONNAME = 'batch_lookup'
    job_start_input = {'totalCompanies': len(org_numbers)}

    # ============================================================================
    # LOG #1: Job Started - Batch Operation Begins
    # ============================================================================
    sovdev_log_job_status(
        SOVDEV_LOGLEVELS.INFO,
        FUNCTIONNAME,
        job_name,
        'Started',
        PEER_SERVICES.INTERNAL,
        job_start_input
    )

    # Track batch results
    successful = 0
    failed = 0

    # ============================================================================
    # BATCH PROCESSING LOOP - Process Each Company
    # ============================================================================
    for i, org_number in enumerate(org_numbers):
        progress_input = {'organisasjonsnummer': org_number}

        # ==========================================================================
        # LOG #2-5: Progress Tracking - One Log Per Item in Batch
        # ==========================================================================
        sovdev_log_job_progress(
            SOVDEV_LOGLEVELS.INFO,
            FUNCTIONNAME,
            org_number,          # Item name (what we're processing)
            i + 1,               # Item number (current position, 1-based)
            len(org_numbers),    # Total items (batch size)
            PEER_SERVICES.BRREG,
            progress_input
        )

        try:
            # Call lookup_company (generates 2 transaction logs per company)
            lookup_company(org_number)
            successful += 1

        except Exception as error:
            # =======================================================================
            # ERROR HANDLING - Log Batch Item Failure Without Stopping
            # =======================================================================
            failed += 1
            error_input = {'organisasjonsnummer': org_number, 'itemNumber': i + 1}

            sovdev_log(
                SOVDEV_LOGLEVELS.ERROR,
                FUNCTIONNAME,
                f'Batch item {i + 1} failed',
                PEER_SERVICES.BRREG,
                error_input,
                None,
                error
            )

        # Small delay to avoid hitting BRREG API rate limits
        time.sleep(0.1)

    # ============================================================================
    # LOG #6: Job Completed - Batch Operation Ends with Summary
    # ============================================================================
    job_complete_input = {
        'totalCompanies': len(org_numbers),
        'successful': successful,
        'failed': failed,
        'successRate': f'{round((successful / len(org_numbers)) * 100)}%'
    }

    sovdev_log_job_status(
        SOVDEV_LOGLEVELS.INFO,
        FUNCTIONNAME,
        job_name,
        'Completed',
        PEER_SERVICES.INTERNAL,
        job_complete_input
    )


# ============================================================================
# FUNCTION: main - Application Entry Point
# ============================================================================
def main() -> None:
    """
    DEMONSTRATES: sovdev_initialize(), sovdev_log(), and sovdev_flush()

    LOG ENTRIES GENERATED:
    - 1x INFO log: "Company Lookup Service started" (application start)
    - ~15-17 logs from batch_lookup (job status, progress, transactions, errors)
    - 1x INFO log: "Company Lookup Service finished" (application finish)
    """
    FUNCTIONNAME = 'main'

    # ============================================================================
    # INITIALIZATION - Configure sovdev-logger (ONE TIME at startup)
    # ============================================================================
    system_id = os.environ.get('OTEL_SERVICE_NAME', 'company-lookup-service')

    sovdev_initialize(
        system_id,                    # Service name (from env or default)
        '1.0.0',                      # Service version
        PEER_SERVICES.mappings        # Peer service validation mappings
    )

    # ============================================================================
    # LOG #1: Application Start - Service Lifecycle
    # ============================================================================
    sovdev_log(
        SOVDEV_LOGLEVELS.INFO,
        FUNCTIONNAME,
        'Company Lookup Service started',
        PEER_SERVICES.INTERNAL
    )

    # ============================================================================
    # TEST DATA - Company Organization Numbers
    # ============================================================================
    # CRITICAL: All language implementations MUST use these exact numbers
    companies = [
        '971277882',  # Company 1: DIREKTORATET FOR UTVIKLINGSSAMARBEID (NORAD) - Valid
        '915933149',  # Company 2: DIREKTORATET FOR E-HELSE MELDT TIL OPPHØR - Valid
        '974652846',  # Company 3: INVALID - Will fail with HTTP 404 (intentional)
        '916201478'   # Company 4: KVISTADMANNEN AS - Valid
    ]

    # ============================================================================
    # BATCH PROCESSING - Process All Companies
    # ============================================================================
    batch_lookup(companies)

    # ============================================================================
    # LOG #2: Application Finish - Service Lifecycle
    # ============================================================================
    sovdev_log(
        SOVDEV_LOGLEVELS.INFO,
        FUNCTIONNAME,
        'Company Lookup Service finished',
        PEER_SERVICES.INTERNAL
    )

    # ============================================================================
    # FLUSH - CRITICAL for Short-Lived Applications
    # ============================================================================
    sovdev_flush()


# ============================================================================
# APPLICATION ENTRY POINT - Error Handling
# ============================================================================
if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print(f'Fatal error: {error}', file=sys.stderr)

        # CRITICAL: Flush logs even on fatal error
        sovdev_flush()

        sys.exit(1)
