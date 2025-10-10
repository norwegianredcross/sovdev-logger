/**
 * Advanced Example - Company Lookup Service
 *
 * This example demonstrates advanced features of sovdev-logger including:
 * - Job status tracking
 * - Progress logging for batch operations
 * - Error handling with retry logic
 * - Real API integration (Norwegian company registry)
 */

import {
  sovdev_initialize,
  sovdev_log,
  sovdev_log_job_status,
  sovdev_log_job_progress,
  sovdev_flush,
  SOVDEV_LOGLEVELS,
  create_peer_services
} from '../../../dist/index.js';

import https from 'https';

// Define peer services - INTERNAL is auto-generated
const PEER_SERVICES = create_peer_services({
  BRREG: 'SYS1234567'  // External system (Norwegian company registry)
});

interface CompanyData {
  organisasjonsnummer: string;
  navn: string;
  organisasjonsform?: { kode: string; beskrivelse: string };
}

/**
 * Fetch company data from Brønnøysund Registry
 */
async function fetchCompanyData(orgNumber: string): Promise<CompanyData> {
  return new Promise((resolve, reject) => {
    const url = `https://data.brreg.no/enhetsregisteret/api/enheter/${orgNumber}`;

    https
      .get(url, (res) => {
        let data = '';
        res.on('data', (chunk) => (data += chunk));
        res.on('end', () => {
          if (res.statusCode === 200) {
            resolve(JSON.parse(data));
          } else {
            reject(new Error(`HTTP ${res.statusCode}: ${data}`));
          }
        });
      })
      .on('error', reject);
  });
}

/**
 * Process a single company lookup with logging
 */
async function lookupCompany(orgNumber: string): Promise<void> {
  const FUNCTIONNAME = 'lookupCompany';
  const input = { organisasjonsnummer: orgNumber };

  sovdev_log(
    SOVDEV_LOGLEVELS.INFO,
    FUNCTIONNAME,
    `Looking up company ${orgNumber}`,
    PEER_SERVICES.BRREG,
    input
  );

  try {
    const companyData = await fetchCompanyData(orgNumber);
    const response = {
      navn: companyData.navn,
      organisasjonsform: companyData.organisasjonsform?.beskrivelse
    };

    sovdev_log(
      SOVDEV_LOGLEVELS.INFO,
      FUNCTIONNAME,
      `Company found: ${companyData.navn}`,
      PEER_SERVICES.BRREG,
      input,
      response
    );
  } catch (error) {
    sovdev_log(
      SOVDEV_LOGLEVELS.ERROR,
      FUNCTIONNAME,
      `Failed to lookup company ${orgNumber}`,
      PEER_SERVICES.BRREG,
      input,
      null,
      error
    );
  }
}

/**
 * Batch process multiple companies with progress tracking
 */
async function batchLookup(orgNumbers: string[]): Promise<void> {
  const jobName = 'CompanyLookupBatch';
  const FUNCTIONNAME = 'batchLookup';
  const jobStartInput = { totalCompanies: orgNumbers.length };

  // Log job start - internal job
  sovdev_log_job_status(
    SOVDEV_LOGLEVELS.INFO,
    FUNCTIONNAME,
    jobName,
    'Started',
    PEER_SERVICES.INTERNAL,
    jobStartInput
  );

  let successful = 0;
  let failed = 0;

  // Process each company
  for (let i = 0; i < orgNumbers.length; i++) {
    const orgNumber = orgNumbers[i];
    const progressInput = { organisasjonsnummer: orgNumber };

    // Log progress - tracking BRREG processing
    sovdev_log_job_progress(
      SOVDEV_LOGLEVELS.INFO,
      FUNCTIONNAME,
      orgNumber,
      i + 1,
      orgNumbers.length,
      PEER_SERVICES.BRREG,
      progressInput
    );

    try {
      await lookupCompany(orgNumber);
      successful++;
    } catch (error) {
      failed++;
      const errorInput = { organisasjonsnummer: orgNumber, itemNumber: i + 1 };
      sovdev_log(
        SOVDEV_LOGLEVELS.ERROR,
        FUNCTIONNAME,
        `Batch item ${i + 1} failed`,
        PEER_SERVICES.BRREG,
        errorInput,
        null,
        error
      );
    }

    // Small delay to avoid rate limiting
    await new Promise((resolve) => setTimeout(resolve, 100));
  }

  // Log job completion - internal job
  const jobCompleteInput = {
    totalCompanies: orgNumbers.length,
    successful: successful,
    failed: failed,
    successRate: `${Math.round((successful / orgNumbers.length) * 100)}%`
  };
  sovdev_log_job_status(
    SOVDEV_LOGLEVELS.INFO,
    FUNCTIONNAME,
    jobName,
    'Completed',
    PEER_SERVICES.INTERNAL,
    jobCompleteInput
  );
}

async function main() {
  const FUNCTIONNAME = 'main';

  // Initialize logger with service info and system mapping
  // Use OTEL_SERVICE_NAME env var (OpenTelemetry standard) or default
  const systemId = process.env.OTEL_SERVICE_NAME || "company-lookup-service";

  sovdev_initialize(
    systemId,
    "1.0.0",
    PEER_SERVICES.mappings
  );

  sovdev_log(
    SOVDEV_LOGLEVELS.INFO,
    FUNCTIONNAME,
    'Company Lookup Service started',
    PEER_SERVICES.INTERNAL
  );

  //TODO: create a file that all language implementations can use. This way we know that each implementation is tested with the same data.
  // Example: Norwegian Red Cross and related organizations
  const companies = [
    '971277882', // Norges Røde Kors (Norwegian Red Cross)
    '915933149', // Røde Kors Hjelpekorps
    '974652846', // Invalid number (will cause error for demonstration)
    '916201478'  // Norsk Folkehjelp
  ];

  await batchLookup(companies);

  sovdev_log(
    SOVDEV_LOGLEVELS.INFO,
    FUNCTIONNAME,
    'Company Lookup Service finished',
    PEER_SERVICES.INTERNAL
  );

  // Flush logs before exit
  // CRITICAL: OpenTelemetry batches logs for performance. Without flushing,
  // the final batch of logs (including job completion status) will be lost
  // when the application exits. This ensures all logs reach the OTLP collector.
  await sovdev_flush();
}

main().catch(async (error) => {
  console.error('Fatal error:', error);
  // IMPORTANT: Flush logs even on error to ensure error logs are sent!
  await sovdev_flush();
  process.exit(1);
});
