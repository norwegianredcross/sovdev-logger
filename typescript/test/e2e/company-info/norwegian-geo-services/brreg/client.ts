/**
 * 🏢 BRREG API Client
 * 
 * Client for Norwegian Business Registry (Brønnøysundregistrene)
 * Official API: https://data.brreg.no/enhetsregisteret/api
 */

import https from 'https';
import { URL } from 'url';
import { ApiClientConfig } from '../shared/types.js';
import { BrregError } from '../shared/errors.js';
import {
  CompanyBasicInfo,
  CompanyDetailedInfo,
  CompanySearchResult,
  CompanySearchParams,
  BrregUpdatesResponse,
  BrregUpdate
} from './types.js';

export class BrregApiClient {
  private readonly config: ApiClientConfig;

  constructor(config?: Partial<ApiClientConfig>) {
    this.config = {
      baseUrl: 'https://data.brreg.no/enhetsregisteret/api',
      timeout: 10000,
      retryAttempts: 3,
      retryDelay: 1000,
      userAgent: 'Norwegian-Geo-Services-Library/1.0.0',
      ...config
    };
  }

  /**
   * Fetch a single company by organization number
   */
  async getCompany(organisasjonsnummer: string): Promise<CompanyDetailedInfo> {
    const url = `${this.config.baseUrl}/enheter/${organisasjonsnummer}`;
    
    try {
      const data = await this.httpGet<CompanyDetailedInfo>(url);
      return data;
    } catch (error) {
      throw new BrregError(
        `Failed to fetch company ${organisasjonsnummer}`,
        'BRREG_FETCH_ERROR',
        error instanceof Error && 'statusCode' in error ? (error as any).statusCode : undefined,
        { organisasjonsnummer },
        error instanceof Error ? error : undefined
      );
    }
  }

  /**
   * Search for companies based on various criteria
   */
  async searchCompanies(params: CompanySearchParams): Promise<CompanySearchResult> {
    const url = new URL(`${this.config.baseUrl}/enheter`);
    
    // Add search parameters
    if (params.navn) url.searchParams.set('navn', params.navn);
    if (params.organisasjonsnummer) url.searchParams.set('organisasjonsnummer', params.organisasjonsnummer);
    if (params.postnummer) url.searchParams.set('forretningsadresse.postnummer', params.postnummer);
    if (params.kommune) url.searchParams.set('forretningsadresse.kommune', params.kommune);
    if (params.naeringskode) url.searchParams.set('naeringskode', params.naeringskode);
    if (params.size) url.searchParams.set('size', params.size.toString());
    if (params.page) url.searchParams.set('page', params.page.toString());

    try {
      const data = await this.httpGet<CompanySearchResult>(url.toString());
      return data;
    } catch (error) {
      throw new BrregError(
        'Failed to search companies',
        'BRREG_SEARCH_ERROR',
        error instanceof Error && 'statusCode' in error ? (error as any).statusCode : undefined,
        { searchParams: params },
        error instanceof Error ? error : undefined
      );
    }
  }

  /**
   * Check if a company exists and is active
   */
  async companyExists(organisasjonsnummer: string): Promise<boolean> {
    try {
      await this.getCompany(organisasjonsnummer);
      return true;
    } catch (error) {
      if (error instanceof BrregError && error.statusCode === 404) {
        return false;
      }
      throw error; // Re-throw other errors
    }
  }

  /**
   * Get multiple companies in a batch
   */
  async getCompaniesBatch(organisasjonsnummer: string[]): Promise<Map<string, CompanyDetailedInfo | Error>> {
    const results = new Map<string, CompanyDetailedInfo | Error>();
    
    // Process in parallel but with reasonable concurrency
    const batchSize = 5;
    for (let i = 0; i < organisasjonsnummer.length; i += batchSize) {
      const batch = organisasjonsnummer.slice(i, i + batchSize);
      const promises = batch.map(async (orgNr) => {
        try {
          const company = await this.getCompany(orgNr);
          return { orgNr, result: company };
        } catch (error) {
          return { orgNr, result: error instanceof Error ? error : new Error(String(error)) };
        }
      });

      const batchResults = await Promise.all(promises);
      batchResults.forEach(({ orgNr, result }) => {
        results.set(orgNr, result);
      });

      // Small delay between batches to be nice to the API
      if (i + batchSize < organisasjonsnummer.length) {
        await this.delay(200);
      }
    }

    return results;
  }

  /**
   * Fetch BRREG updates (oppdateringer) since a given ISO date string
   * Mirrors: GET /oppdateringer/enheter?dato=YYYY-MM-DDTHH:mm:ss&page={n}&size={m}
   * Returns a flat list of updates across pages, up to maxPages if provided.
   */
  async getUpdatesSince(
    sinceIsoDate: string,
    options?: { pageSize?: number; maxPages?: number }
  ): Promise<BrregUpdate[]> {
    const pageSize = options?.pageSize ?? 100;
    const maxPages = options?.maxPages ?? 10;

    // Normalize input date to the exact format BRREG expects: yyyy-MM-dd'T'HH:mm:ss.SSS'Z'
    const normalizedSince = this.normalizeBrregIsoDate(sinceIsoDate);

    const updates: BrregUpdate[] = [];
    let page = 0;
    let totalPages = 1;

    while (page < totalPages && page < maxPages) {
      const url = `${this.config.baseUrl}/oppdateringer/enheter?dato=${encodeURIComponent(normalizedSince)}&page=${page}&size=${pageSize}`;
      const resp = await this.httpGet<BrregUpdatesResponse>(url);
      const batch = resp?._embedded?.oppdaterteEnheter || [];
      for (const u of batch) updates.push(u);
      totalPages = resp?.page?.totalPages ?? totalPages;
      page += 1;
    }

    return updates;
  }

  /**
   * Normalize various input date shapes into BRREG's required ISO format with milliseconds and Z suffix
   * Examples in -> out:
   *  - '2024-01-01' -> '2024-01-01T00:00:00.000Z'
   *  - '2024-01-01T00:00:00' -> '2024-01-01T00:00:00.000Z'
   *  - '2024-01-01T00:00:00Z' -> '2024-01-01T00:00:00.000Z'
   */
  private normalizeBrregIsoDate(input: string): string {
    if (!input || typeof input !== 'string') {
      return new Date(0).toISOString();
    }

    const hasTime = /T\d{2}:\d{2}:\d{2}/.test(input);
    const hasTimezone = /Z|[+-]\d{2}:?\d{2}$/.test(input);

    let candidate = input.trim();
    if (!hasTime) {
      candidate = `${candidate}T00:00:00`;
    }
    if (!hasTimezone) {
      candidate = `${candidate}Z`;
    }

    const date = new Date(candidate);
    if (isNaN(date.getTime())) {
      // Fallback to epoch if parsing fails
      return new Date(0).toISOString();
    }
    return date.toISOString();
  }

  /**
   * HTTP GET implementation with retry logic
   */
  private async httpGet<T>(url: string): Promise<T> {
    let lastError: Error | undefined;

    for (let attempt = 1; attempt <= this.config.retryAttempts!; attempt++) {
      try {
        return await this.performHttpGet<T>(url);
      } catch (error) {
        lastError = error instanceof Error ? error : new Error(String(error));
        
        // Don't retry on 4xx errors (client errors)
        if ('statusCode' in lastError && typeof (lastError as any).statusCode === 'number' && (lastError as any).statusCode >= 400 && (lastError as any).statusCode < 500) {
          throw lastError;
        }

        // Wait before retrying (exponential backoff)
        if (attempt < this.config.retryAttempts!) {
          await this.delay(this.config.retryDelay! * Math.pow(2, attempt - 1));
        }
      }
    }

    throw lastError || new Error('Max retry attempts reached');
  }

  /**
   * Perform a single HTTP GET request
   */
  private performHttpGet<T>(url: string): Promise<T> {
    return new Promise((resolve, reject) => {
      const request = https.get(url, {
        timeout: this.config.timeout,
        headers: {
          'User-Agent': this.config.userAgent!,
          'Accept': 'application/json',
          ...this.config.headers
        }
      }, (response) => {
        let data = '';
        
        response.on('data', (chunk) => {
          data += chunk;
        });

        response.on('end', () => {
          try {
            if (response.statusCode! >= 200 && response.statusCode! < 300) {
              const parsed = JSON.parse(data);
              resolve(parsed);
            } else {
              const error = new Error(`HTTP ${response.statusCode}: ${data}`) as any;
              error.statusCode = response.statusCode;
              error.responseBody = data;
              reject(error);
            }
          } catch (parseError) {
            const error = new Error(`Failed to parse JSON response: ${parseError}`) as any;
            error.statusCode = response.statusCode;
            error.responseBody = data;
            reject(error);
          }
        });
      });

      request.on('error', (error) => {
        reject(error);
      });

      request.on('timeout', () => {
        request.destroy();
        reject(new Error(`Request timeout after ${this.config.timeout}ms`));
      });
    });
  }

  /**
   * Utility function for delays
   */
  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

// Export a default instance for convenience
export const brregApi = new BrregApiClient();

