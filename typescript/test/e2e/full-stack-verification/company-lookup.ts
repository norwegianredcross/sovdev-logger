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
  sovdevInitialize,
  sovdevLog,
  sovdevLogJobStatus,
  sovdevLogJobProgress,
  sovdevFlush,
  sovdevGenerateTraceId,
  SOVDEV_LOGLEVELS,
  createPeerServices
} from '../../../dist/index.js';

import https from 'https';

// Define peer services - INTERNAL is auto-generated
const PEER_SERVICES = createPeerServices({
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
async function lookupCompany(orgNumber: string, traceId?: string): Promise<void> {
  const FUNCTIONNAME = 'lookupCompany';
  const txnTraceId = traceId || sovdevGenerateTraceId();  // Use provided or generate new
  const input = { organisasjonsnummer: orgNumber };

  sovdevLog(
    SOVDEV_LOGLEVELS.INFO,
    FUNCTIONNAME,
    `Looking up company ${orgNumber}`,
    PEER_SERVICES.BRREG,
    input,
    null,
    null,
    txnTraceId  // Same traceId for related logs
  );

  try {
    const companyData = await fetchCompanyData(orgNumber);
    const response = {
      navn: companyData.navn,
      organisasjonsform: companyData.organisasjonsform?.beskrivelse
    };

    sovdevLog(
      SOVDEV_LOGLEVELS.INFO,
      FUNCTIONNAME,
      `Company found: ${companyData.navn}`,
      PEER_SERVICES.BRREG,
      input,
      response,
      null,
      txnTraceId  // SAME traceId links request and response
    );
  } catch (error) {
    sovdevLog(
      SOVDEV_LOGLEVELS.ERROR,
      FUNCTIONNAME,
      `Failed to lookup company ${orgNumber}`,
      PEER_SERVICES.BRREG,
      input,
      null,
      error,
      txnTraceId  // SAME traceId for error
    );
  }
}

/**
 * Batch process multiple companies with progress tracking
 */
async function batchLookup(orgNumbers: string[]): Promise<void> {
  const jobName = 'CompanyLookupBatch';
  const FUNCTIONNAME = 'batchLookup';
  const batchTraceId = sovdevGenerateTraceId();  // Generate ONE traceId for entire batch job
  const jobStartInput = { totalCompanies: orgNumbers.length };

  // Log job start - internal job
  sovdevLogJobStatus(
    SOVDEV_LOGLEVELS.INFO,
    FUNCTIONNAME,
    jobName,
    'Started',
    PEER_SERVICES.INTERNAL,
    jobStartInput,
    batchTraceId  // All job logs share this traceId
  );

  let successful = 0;
  let failed = 0;

  // Process each company
  for (let i = 0; i < orgNumbers.length; i++) {
    const orgNumber = orgNumbers[i];
    const itemTraceId = sovdevGenerateTraceId();  // Generate unique traceId for each company lookup
    const progressInput = { organisasjonsnummer: orgNumber };

    // Log progress - tracking BRREG processing
    sovdevLogJobProgress(
      SOVDEV_LOGLEVELS.INFO,
      FUNCTIONNAME,
      orgNumber,
      i + 1,
      orgNumbers.length,
      PEER_SERVICES.BRREG,
      progressInput,
      batchTraceId  // Progress logs use batch traceId
    );

    try {
      await lookupCompany(orgNumber, itemTraceId);  // Pass itemTraceId to link request/response
      successful++;
    } catch (error) {
      failed++;
      const errorInput = { organisasjonsnummer: orgNumber, itemNumber: i + 1 };
      sovdevLog(
        SOVDEV_LOGLEVELS.ERROR,
        FUNCTIONNAME,
        `Batch item ${i + 1} failed`,
        PEER_SERVICES.BRREG,
        errorInput,
        null,
        error,
        itemTraceId  // Error uses same itemTraceId
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
  sovdevLogJobStatus(
    SOVDEV_LOGLEVELS.INFO,
    FUNCTIONNAME,
    jobName,
    'Completed',
    PEER_SERVICES.INTERNAL,
    jobCompleteInput,
    batchTraceId  // Completion uses batch traceId
  );
}

async function main() {
  const FUNCTIONNAME = 'main';

  // Initialize logger with service info and system mapping
  // Use SYSTEM_ID env var (e.g., "sovdev-test-company-lookup-typescript") or default
  const systemId = process.env.SYSTEM_ID || "company-lookup-service";

  sovdevInitialize(
    systemId,
    "1.0.0",
    PEER_SERVICES.mappings
  );

  sovdevLog(
    SOVDEV_LOGLEVELS.INFO,
    FUNCTIONNAME,
    'Company Lookup Service started',
    PEER_SERVICES.INTERNAL
  );

  // Example: Norwegian Red Cross and related organizations
  const companies = [
    '971277882', // Norges Røde Kors (Norwegian Red Cross)
    '915933149', // Røde Kors Hjelpekorps
    '974652846', // Invalid number (will cause error for demonstration)
    '916201478'  // Norsk Folkehjelp
  ];

  await batchLookup(companies);

  sovdevLog(
    SOVDEV_LOGLEVELS.INFO,
    FUNCTIONNAME,
    'Company Lookup Service finished',
    PEER_SERVICES.INTERNAL
  );

  // Flush logs before exit
  // CRITICAL: OpenTelemetry batches logs for performance. Without flushing,
  // the final batch of logs (including job completion status) will be lost
  // when the application exits. This ensures all logs reach the OTLP collector.
  await sovdevFlush();
}

main().catch(async (error) => {
  console.error('Fatal error:', error);
  // IMPORTANT: Flush logs even on error to ensure error logs are sent!
  await sovdevFlush();
  process.exit(1);
});
